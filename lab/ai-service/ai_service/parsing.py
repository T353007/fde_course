"""Getting structured data out of a model, in four layers.

There are four ways to make a model return usable JSON. They are not
alternatives. You stack them, weakest first, and each one catches what the one
above it missed.

    Level 1  Ask for JSON in the prompt.
             Weak. The model agrees and then adds "Here you go:" anyway.
    Level 2  Use the provider's json_schema or response_format.
             Strong, when the provider has it. Ollama and Anthropic do not
             give the same guarantee, so you cannot stop here.
    Level 3  Parse with repair. Strip fences, cut trailing prose, fix quotes
             and commas, close a truncated object.
    Level 4  Validate with pydantic. On failure raise a typed ParseFailure.

Level 4 is the one that matters most, and it is the smallest.

The reason is Mission 32. The model returned "$78,231 approximately" where a
number belonged. The Java parser threw. The retry worker could not tell a schema
error from a timeout, so it retried five times with backoff. 214 applications
got stuck. A timeout is worth retrying because the next attempt might work. A
schema error is not, because the model will hand you the same string again.

So ParseFailure carries a kind, and the kind drives the retry decision. That is
the whole lesson in one field.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from ai_service.config import get_settings

__all__ = [
    "ParseFailure",
    "ParseFailureKind",
    "ParsedResult",
    "RETRY_POLICY_LEGACY",
    "RETRY_POLICY_TYPED",
    "build_json_instruction",
    "call_with_retry",
    "close_truncated_json",
    "extract_json_text",
    "looks_like_refusal",
    "normalize_keys_to_camel",
    "parse_structured",
    "repair_json_text",
    "retry_delay_seconds",
    "schema_for",
    "should_retry",
    "strip_markdown_fences",
    "strip_trailing_prose",
]


class ParseFailureKind(str, Enum):
    """Why we could not get a valid object out of the model.

    Keep these separate. Collapsing them into one "model error" is exactly the
    bug behind the Mission 32 incident.
    """

    # The model answered, the shape is wrong. Retrying gets the same answer.
    SCHEMA_ERROR = "SCHEMA_ERROR"
    # The call did not finish in time. Retrying is reasonable.
    TIMEOUT = "TIMEOUT"
    # The model declined to answer. Retrying is rude and pointless.
    REFUSAL = "REFUSAL"
    # Output stopped at the token limit. Retrying with a bigger limit can work.
    TRUNCATED = "TRUNCATED"
    # Nothing came back at all.
    EMPTY = "EMPTY"
    # The network or the provider broke. Retrying is reasonable.
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    # We do not know. Treat it as not retryable until someone works it out.
    UNKNOWN = "UNKNOWN"


class ParseFailure(Exception):
    """A typed parse failure. The `kind` field is the point of this class."""

    def __init__(
        self,
        kind: ParseFailureKind,
        message: str,
        *,
        raw_text: str | None = None,
        detail: Any = None,
        repairs_applied: list[str] | None = None,
        prompt_version: str | None = None,
    ) -> None:
        self.kind = kind
        self.message = message
        self.raw_text = raw_text
        self.detail = detail
        self.repairs_applied = repairs_applied or []
        self.prompt_version = prompt_version
        super().__init__(f"{kind.value}: {message}")

    def to_dict(self) -> dict[str, Any]:
        preview = (self.raw_text or "")[:400]
        return {
            "kind": self.kind.value,
            "message": self.message,
            "promptVersion": self.prompt_version,
            "repairsApplied": self.repairs_applied,
            "detail": self.detail,
            "rawTextPreview": preview,
        }


@dataclass
class ParsedResult:
    """A validated object, plus a record of what we had to do to get it.

    repairs_applied belongs in the trace. If a prompt needs three repairs on
    every call, the prompt is the problem, not the parser.
    """

    value: Any
    data: dict[str, Any]
    repairs_applied: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Level 1: ask nicely
# ---------------------------------------------------------------------------

_JSON_INSTRUCTION = """Return only JSON. No explanation, no markdown fences.
The JSON must match this schema:
{schema}
"""


def build_json_instruction(schema: dict[str, Any]) -> str:
    """Level 1. Put the schema in the prompt and ask for JSON only.

    This is the weakest layer and it is worth measuring how weak. In the
    recorded qwen3:8b output under fixtures/recorded/, this instruction is
    present in every prompt and the model still wrapped the answer in markdown
    fences and added a closing sentence. Asking is not enforcing.

    Keep it anyway. It costs a few tokens and it moves the failure rate.
    """
    return _JSON_INSTRUCTION.format(schema=json.dumps(schema, indent=2))


def schema_for(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Level 2 input. The JSON schema a provider can enforce."""
    return model_cls.model_json_schema()


# ---------------------------------------------------------------------------
# Level 3: repair
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:json|JSON)?\s*(.*?)\s*```", re.DOTALL)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
_SNAKE_PART = re.compile(r"_([a-z0-9])")

_REFUSAL_PATTERNS = (
    "i cannot",
    "i can't",
    "i am not able to",
    "i'm not able to",
    "i am unable",
    "i'm unable",
    "i won't",
    "i will not",
    "as an ai",
    "i do not have enough information",
    "i don't have enough information",
)


def looks_like_refusal(text: str) -> bool:
    """Cheap refusal check.

    Text matching is not a great way to detect a refusal and this function is
    honest about that. It is here because the alternative is calling a refusal a
    schema error, and then the retry worker hammers a model that already said no
    five times in a row. Mission 14 makes this precise.
    """
    head = text.strip().lower()[:300]
    if not head:
        return False
    if head.startswith("{") or head.startswith("["):
        return False
    return any(pattern in head for pattern in _REFUSAL_PATTERNS)


def strip_markdown_fences(text: str) -> str:
    """Repair 1. The single most common thing a model does to your JSON."""
    match = _FENCE.search(text)
    if match:
        return match.group(1)
    return text


def strip_trailing_prose(text: str) -> str:
    """Repair 2. Cut whatever the model said after the JSON ended.

    We walk the string and track bracket depth so we can find the real end of
    the first top level object. A regex cannot do this correctly because JSON
    nests and strings can contain braces.
    """
    stripped = text.strip()
    start = None
    for index, char in enumerate(stripped):
        if char in "{[":
            start = index
            break
    if start is None:
        return stripped

    opener = stripped[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return stripped[start : index + 1]
    return stripped[start:]


def fix_single_quotes(text: str) -> str:
    """Repair 3. A model that was thinking in Python hands you Python dict text.

    Only safe when there are no double quotes to confuse. If both are present we
    leave it alone rather than corrupt a value that contains an apostrophe.
    """
    if '"' in text:
        return text
    return text.replace("'", '"')


def remove_trailing_commas(text: str) -> str:
    """Repair 4. Valid in Python and JavaScript, not in JSON."""
    return _TRAILING_COMMA.sub(r"\1", text)


def close_truncated_json(text: str) -> str:
    """Repair 5. Rebuild a closing for output that stopped at the token limit.

    This is the repair to be most careful with. Closing the brackets makes the
    text parse, and the object is still incomplete. A statement that had eleven
    transactions and got cut after four will parse cleanly and be wrong by
    seven transactions. So callers must also look at finish_reason. Mission 13
    covers exactly this trap.
    """
    stack: list[str] = []
    in_string = False
    escaped = False
    last_safe = None  # index just past the last complete value

    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            if not in_string:
                last_safe = index + 1
            continue
        if in_string:
            continue
        if char in "{[":
            stack.append("}" if char == "{" else "]")
        elif char in "}]":
            if stack:
                stack.pop()
            last_safe = index + 1
        elif char in "0123456789truefalsn":
            last_safe = index + 1

    body = text
    if in_string and last_safe is not None:
        # We ended inside a string literal. Drop the partial value entirely.
        body = text[:last_safe]

    body = body.rstrip()
    # Drop a dangling comma or a key with no value, like  "ein":
    body = re.sub(r',\s*"[^"]*"\s*:\s*$', "", body)
    body = re.sub(r'"[^"]*"\s*:\s*$', "", body)
    body = body.rstrip().rstrip(",")

    return body + "".join(reversed(stack))


def _camel(key: str) -> str:
    if "_" in key:
        head, *rest = key.split("_")
        converted = head.lower() + "".join(part.title() for part in rest if part)
        return converted or key
    if key[:1].isupper():
        return key[:1].lower() + key[1:]
    return key


def normalize_keys_to_camel(data: Any) -> Any:
    """Repair 6. Make key casing consistent.

    One recorded fixture mixes "Description" with "classification" in the same
    object, because that is what the 8b model did on a batch with poor OCR text
    in it. The API contract is camelCase, so we only run this after validation
    has already failed, and we record that we ran it.
    """
    if isinstance(data, dict):
        return {_camel(str(k)): normalize_keys_to_camel(v) for k, v in data.items()}
    if isinstance(data, list):
        return [normalize_keys_to_camel(item) for item in data]
    return data


def extract_json_text(text: str) -> str:
    """Run the text repairs that do not need to know the schema."""
    return strip_trailing_prose(strip_markdown_fences(text))


def repair_json_text(
    text: str, *, finish_reason: str = "stop"
) -> tuple[Any, list[str]]:
    """Try increasingly aggressive repairs until json.loads succeeds.

    Returns the loaded object and the list of repairs that were needed. Raises
    ParseFailure if nothing works.
    """
    repairs: list[str] = []

    def attempt(candidate: str) -> Any | None:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            return None

    loaded = attempt(text)
    if loaded is not None:
        return loaded, repairs

    candidate = text
    steps: list[tuple[str, Callable[[str], str]]] = [
        ("strip_markdown_fences", strip_markdown_fences),
        ("strip_trailing_prose", strip_trailing_prose),
        ("remove_trailing_commas", remove_trailing_commas),
        ("fix_single_quotes", fix_single_quotes),
        ("close_truncated_json", close_truncated_json),
    ]
    for name, step in steps:
        updated = step(candidate)
        if updated != candidate:
            candidate = updated
            repairs.append(name)
        loaded = attempt(candidate)
        if loaded is not None:
            return loaded, repairs

    kind = (
        ParseFailureKind.TRUNCATED
        if finish_reason == "length"
        else ParseFailureKind.SCHEMA_ERROR
    )
    raise ParseFailure(
        kind,
        "Could not read JSON out of the model output, even after repair.",
        raw_text=text,
        repairs_applied=repairs,
    )


# ---------------------------------------------------------------------------
# Level 4: validate
# ---------------------------------------------------------------------------

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_structured(
    text: str,
    model_cls: type[ModelT],
    *,
    finish_reason: str = "stop",
    prompt_version: str | None = None,
) -> ParsedResult:
    """Levels 3 and 4 together. The one function routes should call.

    Raises ParseFailure with a kind that says what to do next.
    """
    if not text or not text.strip():
        raise ParseFailure(
            ParseFailureKind.EMPTY,
            "The model returned nothing.",
            raw_text=text,
            prompt_version=prompt_version,
        )

    if looks_like_refusal(text):
        raise ParseFailure(
            ParseFailureKind.REFUSAL,
            "The model declined to answer. Do not retry this. Route it to a human.",
            raw_text=text,
            prompt_version=prompt_version,
        )

    try:
        data, repairs = repair_json_text(text, finish_reason=finish_reason)
    except ParseFailure as failure:
        failure.prompt_version = prompt_version
        raise

    if not isinstance(data, (dict, list)):
        raise ParseFailure(
            ParseFailureKind.SCHEMA_ERROR,
            f"Expected a JSON object, got {type(data).__name__}.",
            raw_text=text,
            repairs_applied=repairs,
            prompt_version=prompt_version,
        )

    try:
        value = model_cls.model_validate(data)
    except ValidationError as first_error:
        # Last repair, and only now. Renaming keys before validation would hide
        # a real contract break behind a helpful guess.
        recased = normalize_keys_to_camel(data)
        try:
            value = model_cls.model_validate(recased)
        except ValidationError:
            kind = (
                ParseFailureKind.TRUNCATED
                if finish_reason == "length"
                else ParseFailureKind.SCHEMA_ERROR
            )
            raise ParseFailure(
                kind,
                "The model output is valid JSON but does not match the schema.",
                raw_text=text,
                detail=first_error.errors(include_url=False),
                repairs_applied=repairs,
                prompt_version=prompt_version,
            ) from first_error
        repairs.append("normalize_keys_to_camel")
        data = recased

    if finish_reason == "length" and "close_truncated_json" in repairs:
        # It parses. That does not mean it is complete.
        raise ParseFailure(
            ParseFailureKind.TRUNCATED,
            "Output hit the token limit. The object parsed only after we closed "
            "it by hand, so fields are missing. Raise max_tokens or split the "
            "batch. Do not use this result.",
            raw_text=text,
            repairs_applied=repairs,
            prompt_version=prompt_version,
        )

    return ParsedResult(
        value=value,
        data=data if isinstance(data, dict) else {"items": data},
        repairs_applied=repairs,
    )


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------

RETRY_POLICY_LEGACY = "legacy"
RETRY_POLICY_TYPED = "typed"

# The correct policy. Only retry things that a second attempt could fix.
TYPED_RETRYABLE_KINDS: frozenset[ParseFailureKind] = frozenset(
    {
        ParseFailureKind.TIMEOUT,
        ParseFailureKind.TRANSPORT_ERROR,
        ParseFailureKind.EMPTY,
    }
)


def should_retry(
    kind: ParseFailureKind,
    attempt: int,
    *,
    max_attempts: int,
    policy: str = RETRY_POLICY_LEGACY,
) -> bool:
    """Decide whether to try again.

    Two policies live here on purpose, and the default is the wrong one.

    "legacy" is what Tomás's retry worker in underwriting-service does. It sees a
    failure, it retries, five times, with backoff. It cannot tell a schema error
    from a timeout because the exception it catches does not say. This is the
    root cause of the Mission 32 incident, and it is the default here so the
    incident reproduces on every machine.

    "typed" is the fix. Read the kind first. A SCHEMA_ERROR means the model gave
    a well formed wrong answer, and it will give the same one again, so retrying
    burns money and delays the alert. A REFUSAL means stop and get a human.
    Set RETRY_POLICY=typed to turn it on.
    """
    if attempt >= max_attempts:
        return False
    if policy == RETRY_POLICY_TYPED:
        return kind in TYPED_RETRYABLE_KINDS
    # legacy: retry anything, which is the bug
    return True


def retry_delay_seconds(attempt: int, base: float) -> float:
    """Exponential backoff, no jitter.

    No jitter is also a defect. Five workers that fail at the same moment retry
    at the same moment. Mission 33 gets to that.
    """
    return base * (2 ** (attempt - 1))


def call_with_retry(
    operation: Callable[[], ParsedResult],
    *,
    policy: str | None = None,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    on_attempt: Callable[[int, ParseFailure | None], None] | None = None,
) -> ParsedResult:
    """Run a parse-and-validate operation under the configured retry policy."""
    settings = get_settings()
    policy = policy or settings.retry_policy
    max_attempts = max_attempts if max_attempts is not None else settings.retry_max_attempts
    base_delay = (
        base_delay if base_delay is not None else settings.retry_base_delay_seconds
    )

    attempt = 0
    last_failure: ParseFailure | None = None
    while True:
        attempt += 1
        try:
            result = operation()
        except ParseFailure as failure:
            last_failure = failure
            if on_attempt is not None:
                on_attempt(attempt, failure)
            if should_retry(
                failure.kind, attempt, max_attempts=max_attempts, policy=policy
            ):
                delay = retry_delay_seconds(attempt, base_delay)
                if delay > 0:
                    time.sleep(delay)
                continue
            raise
        if on_attempt is not None:
            on_attempt(attempt, None)
        return result
    # unreachable, kept so the type checker sees a return path
    raise last_failure  # pragma: no cover
