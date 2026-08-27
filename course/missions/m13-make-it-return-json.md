---
id: M13
slug: make-it-return-json
title: Make It Return JSON
subtitle: It returns clean JSON every time you test it, and 3.1% of the time in a batch of four hundred.
phase: 3
order: 13
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Measure a structured output failure rate instead of estimating it
  - Apply the four rungs of structured output in the right order
  - Build a typed failure taxonomy that separates schema errors from timeouts
  - Recognize when a retry makes a failure worse instead of better
concepts: [structured output, json schema, response format, parsing, pydantic validation, failure taxonomy, retries]
competencies: [coding, ai-fundamentals, production-reliability]
prereqs: [M12]
---

## Where you are

Classification works. You showed Marcus on Thursday, he was happy, and Wendy asked
when she could call it from the portal.

Which means it stops being a curl command and becomes a thing another service depends
on. Tomás is writing the Java side that reads your response, and he asked you a
reasonable question this morning that you answered too confidently.

## The request

:::evidence{type=slack label="DM from Tomás Ferreira, Monday 9:41 AM"}
```text
Tomás:  hey, wiring underwriting-service to your classify endpoint
Tomás:  what does it return when the model messes up

You:    it returns the same shape every time, results array with txn_id
        and classification

Tomás:  no I mean when the model returns something weird. does the JSON
        ever come back broken

You:    haven't seen it. I've run it maybe thirty times

Tomás:  ok cool, I'll just parse it then

You:    yeah should be fine
```
:::

Read your last message again. "Haven't seen it" and "should be fine" are the two
phrases that appear right before every LLM parsing incident, and you just said both in
one conversation.

## The conversation

:::dialogue{title="Nadia, Slack DM, Monday 10:05 AM"}
**Nadia:** thirty times.

**You:** you're reading my DMs?

**Nadia:** you pasted the thread in the channel. thirty times is not a
measurement, it's a vibe.

**You:** the prompt says return a JSON array. it returns a JSON array.

**Nadia:** how many of your thirty were the messy statements. the faxed ones.

*A pause.*

**You:** ...they were the clean batch.

**Nadia:** run four hundred. real ones. count the failures. then tell Tomás a number
instead of a feeling.

**You:** and if the number is small?

**Nadia:** small numbers are the dangerous ones. a failure at 30 percent gets fixed
in week one. a failure at 3 percent ships, and then you find out what your caller does
with it.
:::

## Your task

:::task{time="60 min"}
Before you fix anything, measure it.

1. Pull 400 statement pages from the seed data, spread across all three tenants and
   both OCR quality levels. Do not filter for clean ones.
2. Call `/v1/classify/transactions` for each one with the prompt exactly as it is
   today.
3. Count how many responses cannot be parsed into your expected shape, and record
   the raw text of every failure.
4. Group the failures by what is actually wrong with them. Do not group them by
   "parse error."
5. Write the rate in `customers/northstar/notes/m13-json-rate.md` with the date, the
   prompt version, and the model alias. All three matter.
:::

Here is the runner.

```python
# lab/ai-service/scripts/m13_batch.py
import json, pathlib, collections
import httpx

BASE = "http://localhost:8000"
PAGES = sorted(pathlib.Path("data/bank-statements/ocr").glob("*.json"))[:400]

failures = []
ok = 0

with httpx.Client(timeout=120) as client:
    for i, page in enumerate(PAGES):
        payload = json.loads(page.read_text())
        r = client.post(
            f"{BASE}/v1/classify/transactions",
            json={"transactions": payload["credits"],
                  "options": {"alias": "hosted-mid", "temperature": 0.0,
                              "max_output_tokens": 800}},
            headers={"X-Tenant-Id": payload["tenant_id"],
                     "X-Trace-Id": f"m13-{i:04d}"},
        )
        raw = r.json()["raw_completion"]
        try:
            parsed = json.loads(raw)
            assert isinstance(parsed, list)
            ok += 1
        except Exception as exc:
            failures.append({"page": page.name, "error": str(exc),
                             "finish_reason": r.json()["usage"]["finish_reason"],
                             "raw": raw})

print(f"ok {ok}  failed {len(failures)}  rate {len(failures) / len(PAGES):.2%}")
pathlib.Path("out/m13-failures.json").write_text(json.dumps(failures, indent=2))
```

`raw_completion` is the model's exact output before any handling, which the service
returns because a mission needs it. In production you log it and do not return it.

:::evidence{type=log label="scripts/m13_batch.py, three runs"}
```text
run 1   ok 388  failed 12  rate 3.00%
run 2   ok 386  failed 14  rate 3.50%
run 3   ok 389  failed 11  rate 2.75%

37 failures across 1,200 calls   3.1%
```
:::

Three runs of the same 400 pages give three different numbers. Temperature is 0. You
already know why from Mission 12.

## Evidence

Here is what the 12 failures from run 1 actually look like. This is the most useful
page in the mission.

:::evidence{type=log label="out/m13-failures.json, grouped by hand"}
```text
5 x  markdown code fence
       ```json
       [{"txn_id": "TX-10021", "classification": "OPERATING_REVENUE"}]
       ```

3 x  prose wrapper
       Here are the classifications for the transactions you provided:
       [{"txn_id": "TX-10021", "classification": "OPERATING_REVENUE"}]
       Let me know if you need any of these explained.

2 x  cut off at the token limit    (finish_reason: length)
       [{"txn_id": "TX-10021", "classification": "OPERATING_REVENUE"},
        {"txn_id": "TX-10022", "classification": "INTERNAL_TRAN

1 x  python literal instead of JSON
       [{'txn_id': 'TX-10021', 'classification': 'OPERATING_REVENUE'},]

1 x  refusal
       I don't have enough information to classify these transactions.
       The descriptions are heavily garbled and I would be guessing.
```
:::

Look at the last one. That is not a bug. The page was a fax of a fax, the OCR output
was `SIRIPE PAV0UI SI-44/1QK`, and the model declined to guess. Your prompt told it
not to guess. It obeyed, and your parser treats obedience as a crash.

Those five groups need five different responses. A parser that only knows "valid" and
"invalid" cannot give them.

:::stopandthink
Before the solution:

1. You are about to add "Return only valid JSON. No markdown, no explanation." to the
   prompt. Which of the five failure groups does that fix, and which does it not
   touch? Go group by group.
2. The two truncated responses came back with HTTP 200 and `finish_reason: length`.
   Should your service retry those? Should it retry the refusal? Are those the same
   decision?
3. Tomás is writing a retry in the Java worker. If your service returns HTTP 500 for
   all five groups, what does his worker do to the refusal case?
4. 3.1 percent of 3,680 monthly calls is 114 calls. Each call covers roughly 30
   transactions on one statement page. Estimate how many applications a month are
   affected, and say what "affected" means to Renee.

Write answers to all four. Question 1 is the one people skip, and it is the whole
mission.
:::

## Working through it

Structured output is a ladder with four rungs. People try rung one, it mostly works,
and they stop. Every rung above it fixes a class of failure the one below cannot.

### Rung 1: ask nicely in the prompt

Add the instruction. It is free and it helps.

```python
# lab/ai-service/ai_service/prompts/txn_classify_v2.py
PROMPT_VERSION = "txn-classify-v2"

SYSTEM = """...same as v1...

Output format:
  Return only a JSON array. No markdown fences. No explanation before or after.
  Each element has exactly two keys: txn_id and classification.
"""
```

Re-run the 400.

:::evidence{type=log label="prompt v2, three runs"}
```text
run 1   failed 6   rate 1.50%
run 2   failed 8   rate 2.00%
run 3   failed 5   rate 1.25%

19 failures across 1,200 calls   1.6%
```
:::

3.1 percent to 1.6 percent. Half the problem gone for two lines of text.

That result is also the trap. It is a real improvement, it is easy, and it feels like
a fix. It is not a fix, because the mechanism is wrong: you asked a probabilistic
system to please always do something. It will comply most of the time. "Most" is not a
property you can build a bank on.

The remaining failures are the truncations, the refusals, and one stubborn markdown
fence.

### Rung 2: make the provider enforce the shape

Good providers accept a JSON schema and constrain generation so the output cannot be
malformed. The model is only allowed to emit tokens that keep the output valid against
your schema. That is enforcement in the serving layer, not a request in English.

The provider interface already tells you who supports it.

```python
class LLMProvider(Protocol):
    name: str

    def complete(self, req: CompletionRequest) -> CompletionResponse: ...
    def supports_json_schema(self) -> bool: ...
```

```python
# lab/ai-service/ai_service/schemas/classification.py
from typing import Literal
from pydantic import BaseModel, Field

Classification = Literal[
    "OPERATING_REVENUE", "INTERNAL_TRANSFER", "LOAN_PROCEEDS",
    "OWNER_CONTRIBUTION", "REFUND_OR_REVERSAL", "OTHER_CREDIT",
]


class TxnResult(BaseModel):
    txn_id: str = Field(min_length=1)
    classification: Classification


class ClassifyBatch(BaseModel):
    results: list[TxnResult]
```

```python
# lab/ai-service/ai_service/routers/classify.py  (excerpt)
req = CompletionRequest(
    system=SYSTEM,
    user=USER_TEMPLATE.format(transactions_json=txn_json),
    temperature=0.0,
    max_output_tokens=800,
)

if provider.supports_json_schema():
    req.response_format = {
        "type": "json_schema",
        "json_schema": {"name": "classify_batch",
                        "schema": ClassifyBatch.model_json_schema(),
                        "strict": True},
    }
```

Re-run.

:::evidence{type=log label="prompt v2 plus json_schema, three runs"}
```text
run 1   failed 2   rate 0.50%
run 2   failed 2   rate 0.50%
run 3   failed 1   rate 0.25%

5 failures across 1,200 calls   0.4%
```
:::

Every fence, every prose wrapper, and the Python literal are gone. Constrained
decoding cannot emit them.

What is left is the two things enforcement cannot touch.

A truncated response is still a schema violation, because the constraint only
guarantees that valid tokens are chosen, not that the model finishes before it hits
your output limit. You get a syntactically doomed prefix.

A refusal is worse: under strict schema mode, a model that wants to say "I cannot do
this" has no way to say it. It is forced to emit a valid array. So it fills one in.
You just converted a visible refusal into an invisible guess, which is Mission 14's
entire subject.

That is the honest cost of rung 2. Write it down.

### Rung 3: parse with repair

You still need a tolerant parser, for three reasons. Not every provider supports
schema mode, the local model in Mission 17 enforces it more loosely, and truncation
happens regardless.

```python
# lab/ai-service/ai_service/parsing.py
import json
import re

FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)
FIRST_ARRAY = re.compile(r"\[.*", re.DOTALL)
TRAILING_COMMA = re.compile(r",\s*([\]}])")


def strip_fence(text: str) -> str:
    m = FENCE.match(text)
    return m.group(1) if m else text


def strip_prose(text: str) -> str:
    """Drop anything before the first '[' and after the matching ']'."""
    m = FIRST_ARRAY.search(text)
    if not m:
        return text
    body = m.group(0)
    depth = 0
    for i, ch in enumerate(body):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return body[: i + 1]
    return body


def fix_quotes(text: str) -> str:
    """Only safe because our values never contain apostrophes."""
    if '"' in text:
        return text
    return text.replace("'", '"')


def drop_trailing_commas(text: str) -> str:
    return TRAILING_COMMA.sub(r"\1", text)


def close_truncated_array(text: str) -> str:
    """Keep whole objects, throw away the partial one at the end."""
    last = text.rfind("}")
    if last == -1:
        return "[]"
    return text[: last + 1] + "]"


REPAIRS = (strip_fence, strip_prose, fix_quotes, drop_trailing_commas)


def parse_json_array(text: str, allow_truncated: bool) -> tuple[list, list[str]]:
    """Returns (parsed, applied_repairs). Raises ValueError if unrecoverable."""
    applied: list[str] = []
    candidate = text
    for repair in REPAIRS:
        after = repair(candidate)
        if after != candidate:
            applied.append(repair.__name__)
            candidate = after
        try:
            return json.loads(candidate), applied
        except json.JSONDecodeError:
            continue

    if allow_truncated:
        candidate = close_truncated_array(candidate)
        applied.append("close_truncated_array")
        try:
            return json.loads(candidate), applied
        except json.JSONDecodeError:
            pass

    raise ValueError(f"unrecoverable after {applied}")
```

Two decisions in there are worth arguing about.

`fix_quotes` refuses to run when a double quote is present. Blind quote swapping
corrupts real data. Guard every repair with a condition that makes it safe on this
data, and say so in a comment.

`close_truncated_array` is behind a flag, because silently recovering 18 of 30
transactions and returning them as a complete answer is a wrong number, not a
recovered one. The caller has to opt in and has to be told what it got.

Force the case with the stub scenario and look at it directly.

```bash
curl -s localhost:8000/v1/classify/transactions \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m13-trunc' \
  -H 'X-Stub-Scenario: truncated-json' \
  -d @scripts/fixtures/m13-page-30.json | jq
```

:::evidence{type=http label="Response with truncated-json scenario"}
```json
{
  "results": [],
  "failure": {
    "kind": "TRUNCATED",
    "message": "finish_reason=length, recovered 18 of 30 items",
    "retryable": true,
    "retry_hint": "raise max_output_tokens or split the batch",
    "partial_count": 18
  },
  "usage": {
    "finish_reason": "length",
    "completion_tokens": 800,
    "prompt_version": "txn-classify-v2"
  }
}
```
:::

### Rung 4: validate, and give the failure a type

Parsing tells you the text was JSON. Validation tells you the JSON was your JSON. They
are different questions and the second one is where money hides.

A parse success with a bad payload looks like this: `classification` comes back as
`"Operating Revenue"` instead of `OPERATING_REVENUE`, or the array has 29 results for
30 transactions, or a `txn_id` appears that you never sent.

```python
# lab/ai-service/ai_service/parsing.py  (continued)
from dataclasses import dataclass
from enum import Enum

import pydantic


class FailureKind(str, Enum):
    TRUNCATED = "TRUNCATED"          # we cut the model off
    SCHEMA_ERROR = "SCHEMA_ERROR"    # not our shape, and never will be
    VALIDATION_ERROR = "VALIDATION_ERROR"  # our shape, wrong contents
    REFUSAL = "REFUSAL"              # the model declined, on purpose
    TIMEOUT = "TIMEOUT"              # no answer arrived
    RATE_LIMIT = "RATE_LIMIT"        # provider said slow down
    TRANSPORT_ERROR = "TRANSPORT_ERROR"  # socket, DNS, TLS


RETRY_SAME_REQUEST = {FailureKind.TIMEOUT, FailureKind.RATE_LIMIT,
                      FailureKind.TRANSPORT_ERROR}
RETRY_DIFFERENT_REQUEST = {FailureKind.TRUNCATED}
DO_NOT_RETRY = {FailureKind.SCHEMA_ERROR, FailureKind.VALIDATION_ERROR,
                FailureKind.REFUSAL}

REFUSAL_MARKERS = ("i don't have enough information", "i cannot classify",
                   "i would be guessing", "unable to determine")


@dataclass
class Failure:
    kind: FailureKind
    message: str
    partial_count: int = 0

    @property
    def retryable(self) -> bool:
        return self.kind not in DO_NOT_RETRY


@dataclass
class ParseResult:
    value: ClassifyBatch | None
    failure: Failure | None
    repairs: list[str]

    @property
    def ok(self) -> bool:
        return self.failure is None


def parse_and_validate(raw: str, finish_reason: str,
                       expected_ids: list[str]) -> ParseResult:
    if any(m in raw.lower()[:200] for m in REFUSAL_MARKERS):
        return ParseResult(None, Failure(FailureKind.REFUSAL, raw[:200]), [])

    truncated = finish_reason == "length"
    try:
        items, repairs = parse_json_array(raw, allow_truncated=truncated)
    except ValueError as exc:
        kind = FailureKind.TRUNCATED if truncated else FailureKind.SCHEMA_ERROR
        return ParseResult(None, Failure(kind, str(exc)), [])

    try:
        batch = ClassifyBatch(results=items)
    except pydantic.ValidationError as exc:
        return ParseResult(None, Failure(FailureKind.VALIDATION_ERROR,
                                         exc.errors()[0]["msg"]), repairs)

    returned = [r.txn_id for r in batch.results]
    if truncated or set(returned) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(returned))
        return ParseResult(None, Failure(
            FailureKind.TRUNCATED if truncated else FailureKind.VALIDATION_ERROR,
            f"missing {len(missing)} txn_ids, first {missing[:3]}",
            partial_count=len(returned)), repairs)

    return ParseResult(batch, None, repairs)
```

The `expected_ids` check is the one people leave out, and it catches the quietest
failure of the five. A model handed 30 transactions sometimes returns 29 valid
objects. Every one of them parses. Every one of them validates. One transaction just
does not exist any more, and if that missing one was the Fastcapital loan, revenue is
overstated by $75,000 and nothing in your logs says a word.

### The result

```bash
python scripts/m13_batch.py --parser=v2
```

:::evidence{type=log label="all four rungs, three runs of 400"}
```text
                          run 1   run 2   run 3
unrecoverable                 1       1       0
recovered by repair           4       5       4
REFUSAL (correct behavior)    1       1       1
TRUNCATED (batch resent)      2       2       1

unrecoverable rate: 2 / 1,200 = 0.17%
```
:::

3.1 percent to 0.17 percent, and the remaining failures have names.

## Tests

```python
# lab/ai-service/tests/test_parsing.py
import pytest
from ai_service.parsing import parse_and_validate, FailureKind

IDS = ["TX-1", "TX-2"]
GOOD = '[{"txn_id":"TX-1","classification":"OPERATING_REVENUE"},' \
       '{"txn_id":"TX-2","classification":"LOAN_PROCEEDS"}]'


def test_clean_json():
    r = parse_and_validate(GOOD, "stop", IDS)
    assert r.ok and len(r.value.results) == 2


def test_markdown_fence():
    r = parse_and_validate(f"```json\n{GOOD}\n```", "stop", IDS)
    assert r.ok
    assert "strip_fence" in r.repairs


def test_prose_wrapper():
    raw = f"Here are the classifications:\n{GOOD}\nHope that helps."
    r = parse_and_validate(raw, "stop", IDS)
    assert r.ok and "strip_prose" in r.repairs


def test_python_literal_with_trailing_comma():
    raw = "[{'txn_id': 'TX-1', 'classification': 'OPERATING_REVENUE'}," \
          "{'txn_id': 'TX-2', 'classification': 'LOAN_PROCEEDS'},]"
    r = parse_and_validate(raw, "stop", IDS)
    assert r.ok


def test_refusal_is_not_a_schema_error():
    raw = "I don't have enough information to classify these transactions."
    r = parse_and_validate(raw, "stop", IDS)
    assert r.failure.kind is FailureKind.REFUSAL
    assert r.failure.retryable is False


def test_truncation_is_not_a_schema_error():
    raw = '[{"txn_id":"TX-1","classification":"OPERATING_REVENUE"},{"txn_id":"TX-2'
    r = parse_and_validate(raw, "length", IDS)
    assert r.failure.kind is FailureKind.TRUNCATED
    assert r.failure.retryable is True
    assert r.failure.partial_count == 1


def test_missing_id_is_caught_even_though_json_is_valid():
    raw = '[{"txn_id":"TX-1","classification":"OPERATING_REVENUE"}]'
    r = parse_and_validate(raw, "stop", IDS)
    assert r.failure.kind is FailureKind.VALIDATION_ERROR
    assert "TX-2" in r.failure.message


@pytest.mark.parametrize("bad", ["Operating Revenue", "revenue", "REVENUE"])
def test_wrong_enum_value(bad):
    raw = '[{"txn_id":"TX-1","classification":"%s"},' \
          '{"txn_id":"TX-2","classification":"LOAN_PROCEEDS"}]' % bad
    r = parse_and_validate(raw, "stop", IDS)
    assert r.failure.kind is FailureKind.VALIDATION_ERROR
```

The two tests that earn their keep are `test_refusal_is_not_a_schema_error` and
`test_missing_id_is_caught_even_though_json_is_valid`. Both assert that a specific
kind of wrong is labeled as that kind of wrong.

## Then this happens

Back up to the moment after rung 1. This is the wrong turn, and it is the one almost
everyone takes.

You added two lines to the prompt, the rate dropped from 3.1 percent to 1.6 percent,
you ran the clean batch twenty times with no failures, and you told Tomás it was
handled.

:::evidence{type=slack label="#northstar-ai, Wednesday 3:12 PM"}
```text
You:    fixed the JSON thing, prompt now forces the format. we're clean

Tomás:  nice. my parser is straight jackson readValue then
Tomás:  no error branch, keeps it simple

You:    yep should be fine
```
:::

Then you run the pilot batch on Friday. 400 applications through the whole path,
ai-service to Kafka to `underwriting-service`.

:::evidence{type=log label="underwriting-service, Friday 4:02 PM"}
```text
ERROR c.n.uw.ai.ClassifyClient - com.fasterxml.jackson.databind.exc
      .MismatchedInputException: Cannot deserialize value of type
      `java.util.List<TxnResult>` from String value
      2026-06-12T16:02:11 app_id=41822 attempt=1
      2026-06-12T16:02:13 app_id=41822 attempt=2
      2026-06-12T16:02:17 app_id=41822 attempt=3
      2026-06-12T16:02:25 app_id=41822 attempt=4
      2026-06-12T16:02:41 app_id=41822 attempt=5
ERROR c.n.uw.ai.ClassifyClient - app_id=41822 exhausted, status left IN_REVIEW
```

```text
12 applications, 60 model calls, 0 succeeded on retry.
```
:::

Twelve applications sat in `IN_REVIEW` with no classification. Nobody was harmed,
because it was a dev batch on seed data. It cost you Friday evening and it cost Tomás
Monday morning.

## Tracking it down

Pull one of the twelve. `app_id=41822`, a faxed statement from a `CASCADE` applicant.

:::evidence{type=log label="ai-service, Friday 4:02:11 PM"}
```text
INFO  classify  app=41822 page=3 finish_reason=stop tokens=1102/291
DEBUG classify  raw_completion="I don't have enough information to classify
      these transactions. The descriptions are heavily garbled and I would
      be guessing."
```
:::

The model refused. Your prompt told it not to guess and the OCR was unreadable, so it
did the right thing.

Your service returned HTTP 500. Tomás's worker saw a 500, decided that meant "the
other side is having a bad moment," and retried five times with backoff.

Each retry sent the identical unreadable page to the identical model with the identical
prompt at temperature 0. All five got the same refusal. The 60 calls in that log line
are 12 real failures and 48 retries of a request that could never succeed.

:::dialogue{title="Tomás's desk, Monday 9:15 AM"}
**You:** Your worker retried a refusal five times.

**Tomás:** Yeah, it retries anything that isn't a 2xx.

**You:** The model was telling us the page is unreadable. That is a real answer. It
needs to go to a human, not back to the model.

**Tomás:** Right, but I can't tell. From my side it's a 500. A 500 is a 500.

*He pulls up another file.*

**Tomás:** Honestly, the retry worker for the whole document pipeline does the same
thing. `catch (Exception e)`, backoff, five attempts. It's been in there since I
started.

**You:** Has anyone looked at it?

**Tomás:** It was never reviewed. It works.
:::

Now write your own retry, before you know better. Here is what you actually wrote on
Friday night.

```python
# lab/ai-service/ai_service/retry.py     <-- the version that ships in M13
import time


def call_with_retry(fn, attempts: int = 5):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:      # every failure looks the same from here
            last = exc
            time.sleep(2 ** i)
    raise last
```

Same shape as his. `except Exception` cannot tell a timeout from a refusal, so it
treats both as "try again."

You fix the immediate problem by returning typed failures from your endpoint instead
of a bare 500.

```python
# lab/ai-service/ai_service/routers/classify.py  (excerpt)
HTTP_FOR_KIND = {
    FailureKind.TIMEOUT: 504,
    FailureKind.RATE_LIMIT: 429,
    FailureKind.TRANSPORT_ERROR: 502,
    FailureKind.TRUNCATED: 503,       # retry, but change the request
    FailureKind.SCHEMA_ERROR: 422,    # do not retry
    FailureKind.VALIDATION_ERROR: 422,
    FailureKind.REFUSAL: 422,         # send it to a human
}
```

Tomás changes his worker to stop retrying on 4xx. That takes ten minutes and it fixes
these twelve applications.

Neither of you touches the document pipeline retry worker. It is not in scope, it is
not your service, and it works today.

:::dialogue{title="Nadia, Slack DM, Monday 11:40 AM"}
**You:** fixed. typed failures, tomás stops retrying 422s

**Nadia:** good. what about the other retry worker he mentioned

**You:** the document one? not our service, and it's out of scope for the slice

**Nadia:** ok.

**Nadia:** write down where it lives.

**You:** why

**Nadia:** just write it down.
:::

You write it down.

`northstar/document-service/src/main/java/com/northstar/docs/worker/RetryWorker.java`

## The better version

The parser and taxonomy above are the better version of the parsing problem. The retry
is a different problem and you have only half fixed it.

What is right now: failures have types, types map to status codes, and the caller can
tell "ask again" from "a human needs to look at this."

What is still wrong: `call_with_retry` catches `Exception`. So does the Java worker in
`document-service`. Both retry on the assumption that failure is temporary, and both
are used on paths where it often is not.

Retrying an identical request at temperature 0 against a model that just refused it is
not a retry. It is the same call, five times, at five times the cost, arriving at the
same answer five minutes later. When you retry a model call, at least one of these has
to change or you are wasting money:

- the request (smaller batch, higher output limit, different prompt version)
- the model (fall back to a different alias)
- the destination (a human queue)

That is the whole idea and neither of you has implemented it yet.

:::judgment
**A structured output failure rate you have not measured is not low, it is unknown, and
the fix that feels sufficient is the one that only moves it halfway.**

The ladder has an order for a reason. Ask nicely, because it is free and it halves the
rate. Enforce the schema at the provider, because that removes whole categories rather
than reducing them. Parse with repair, because you will always meet a provider or a
truncation that enforcement does not cover. Validate with types, because valid JSON
that is missing a transaction is more dangerous than JSON that fails to parse.

The rung most people never build is the fourth one, and it is the one that pays. Not
the pydantic model itself, but the failure taxonomy next to it. The moment a failure
has a name, three things become possible: the caller can decide what to do, your
metrics can show you which kind is growing, and a retry can be a decision instead of a
reflex. Without names, every failure is `Exception`, and the only available response to
`Exception` is "do it again," which is correct for timeouts and actively harmful for
everything else.

Two things happened in this mission that you should not feel finished about. You said
"should be fine" to a downstream engineer based on thirty runs on clean data, and the
person consuming your API wrote a parser with no error branch because of it. And you
found a retry worker in someone else's service that cannot tell a schema error from a
timeout, correctly judged it out of scope, and moved on. Both decisions were
reasonable. Write down the second one anyway.
:::

## Practice

Different domain. Same reasoning.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A freight brokerage uses a model to read shipping manifests emailed by carriers and
turn them into structured records. The output feeds their billing system directly.

Their schema:

```json
{
  "bol_number": "string",
  "shipper": "string",
  "consignee": "string",
  "pieces": "integer",
  "weight_lbs": "number",
  "accessorials": ["string"],
  "total_charges": "number"
}
```

What you find in a week of production logs, out of 9,400 manifests:

```text
211  parse failure, caught, retried, eventually manual
 38  valid JSON, weight_lbs came back as "12,400 lbs"
 17  valid JSON, accessorials was a comma separated string, not an array
  9  valid JSON, total_charges was 0.00 and the manifest showed $2,180
  4  valid JSON, bol_number was a plausible number that is not on the manifest
```

Their engineer is proud that the 211 parse failures all get caught and retried, and
says the system is "99.997 percent reliable" because only the 4 bad BOL numbers made
it to billing uncaught.

**Your task**

1. Rank those five rows by how much damage they do, worst first. Justify the top one.
2. Which rows would a provider level JSON schema eliminate? Which would it not?
3. `weight_lbs: "12,400 lbs"` parses fine as JSON. Where should this be caught, and
   what type of failure is it?
4. The engineer's reliability number is wrong. Explain why in two sentences you could
   say to their VP.
5. `total_charges: 0.00` when the manifest says $2,180 is the one to be frightened of.
   Say why, and describe the check that catches it.

---

**Notes, after you have written yours**

**Ranking.** Worst is `total_charges: 0.00`, then the fabricated BOL number, then the
comma separated accessorials, then the weight string, then the 211 parse failures.

That ordering surprises people, and the principle behind it is the one to carry: the
failures ranked by damage are almost exactly the inverse of the failures ranked by
visibility. A parse failure is loud, cheap, and already handled. A zero that should
have been $2,180 is silent, passes every type check, and goes straight onto an invoice.

**What schema enforcement fixes.** It removes most of the 211 parse failures, and it
fixes the accessorials type error by forcing an array. It does nothing about the
weight string if the schema types that field as a string, and nothing at all about the
zero charge or the invented BOL number, because both are well formed values of the
right type. Enforcement guarantees shape. It has no opinion about truth.

**Where the weight string is caught.** Validation, as a `VALIDATION_ERROR`, not a
parse error. Then fix it properly by typing the field as a number in the schema and
normalizing in the prompt. Do not write a coercion that strips commas and the word
"lbs" and silently continues, because the same coercion will happily turn "12,400 kg"
into 12400 pounds.

**Why 99.997 percent is wrong.** He is counting only the failures his parser noticed.
The 64 rows that produced valid JSON with wrong contents are failures that reached
billing, so the real uncaught rate is at least 68 in 9,400, which is 0.72 percent, and
that is a floor because nobody has audited the manifests that produced no error at all.

**The zero charge check.** Cross-validate the extracted value against something
outside the model. Sum the line items and compare to `total_charges`. Compare against
the carrier's contracted rate for that lane and weight. Reject any invoice where
charges are zero but pieces and weight are not, because that combination cannot exist
in their business. The general rule is the one Mission 14 is built on: a value the
model produced is a claim, and a claim about money gets checked against a source that
is not the model.
:::
