"""Matchers decide whether one answer counts as the same as another.

This is the part people skip, and then they argue for a week about whether the
model was wrong. "78231.0" against "78231.00" is a formatting difference.
"INTERNAL_TRANSFER" against "OPERATING_REVENUE" is a five figure mistake. A
matcher is where you write down which is which.

A matcher is any callable that takes (expected, actual) and returns a
MatchResult. You can write your own in three lines.

    from northstar_evals import matchers

    m = matchers.numeric(tolerance=0.01)
    m(78231.00, 78231.004).matched   # True
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Callable, Iterable, Mapping

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s]")
_MONEY = re.compile(r"^\s*[-+]?[$\u20ac\u00a3]?\s*[\d,]*\.?\d+\s*$")


@dataclass(frozen=True)
class MatchResult:
    """Did it match, how close was it, and why."""

    matched: bool
    score: float = 0.0
    detail: str = ""

    def __bool__(self) -> bool:
        return self.matched


Matcher = Callable[[Any, Any], MatchResult]


def _hit(score: float = 1.0, detail: str = "") -> MatchResult:
    return MatchResult(True, score, detail)


def _miss(score: float = 0.0, detail: str = "") -> MatchResult:
    return MatchResult(False, score, detail)


def normalize_text(
    value: Any,
    casefold: bool = True,
    strip_punctuation: bool = False,
    collapse_whitespace: bool = True,
) -> str:
    """Clean up a string so two spellings of the same answer compare equal."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text)
    if casefold:
        text = text.casefold()
    if strip_punctuation:
        text = _PUNCTUATION.sub(" ", text)
    if collapse_whitespace:
        text = _WHITESPACE.sub(" ", text)
    return text.strip()


def parse_number(value: Any) -> float | None:
    """Turn a value into a float, or return None if it is not a number.

    Handles the shapes a model actually returns: 78231, "78231.00", "$78,231".
    It does not handle "$78,231 approximately". That one is supposed to fail.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not _MONEY.match(text):
            return None
        cleaned = text.replace(",", "").replace("$", "")
        cleaned = cleaned.replace("\u20ac", "").replace("\u00a3", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def exact() -> Matcher:
    """Values have to be equal, with no cleanup at all."""

    def match(expected: Any, actual: Any) -> MatchResult:
        if expected == actual:
            return _hit(detail="exact")
        return _miss(detail=f"expected {expected!r}, got {actual!r}")

    match.__name__ = "exact"
    return match


def normalized(
    casefold: bool = True,
    strip_punctuation: bool = False,
    collapse_whitespace: bool = True,
) -> Matcher:
    """Compare as text after cleanup. Good for labels and short answers."""

    def match(expected: Any, actual: Any) -> MatchResult:
        e = normalize_text(expected, casefold, strip_punctuation, collapse_whitespace)
        a = normalize_text(actual, casefold, strip_punctuation, collapse_whitespace)
        if e == a:
            return _hit(detail="normalized")
        return _miss(detail=f"expected {expected!r}, got {actual!r}")

    match.__name__ = "normalized"
    return match


def numeric(tolerance: float = 0.0, relative: bool = False) -> Matcher:
    """Compare numbers, allowing a gap.

    With `relative=True` the tolerance is a fraction of the expected value, so
    0.01 means one percent. Use that for revenue, where being off by a dollar
    on 78,231 does not matter and being off by 30,000 does.
    """
    if tolerance < 0:
        raise ValueError("tolerance cannot be negative")

    def match(expected: Any, actual: Any) -> MatchResult:
        e = parse_number(expected)
        a = parse_number(actual)
        if e is None:
            return _miss(detail=f"expected value {expected!r} is not a number")
        if a is None:
            return _miss(detail=f"got {actual!r}, which is not a number")
        gap = abs(e - a)
        limit = abs(e) * tolerance if relative else tolerance
        if gap <= limit + 1e-12:
            return _hit(score=1.0, detail=f"gap {gap:g}")
        return _miss(detail=f"expected {e:g}, got {a:g}, gap {gap:g} over limit {limit:g}")

    match.__name__ = "numeric"
    return match


def _as_set(value: Any) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in re.split(r"[,;|]", value)]
        return {p for p in parts if p}
    if isinstance(value, Mapping):
        return {str(k) for k in value}
    if isinstance(value, Iterable):
        return {str(v).strip() for v in value if str(v).strip()}
    return {str(value)}


def set_overlap(threshold: float = 1.0, casefold: bool = True) -> Matcher:
    """Compare two collections by how much they share.

    The score is the Jaccard overlap: shared items divided by all items seen.
    A threshold of 1.0 means the sets have to be identical. Use a lower number
    when an extra citation is acceptable but a missing one is not.
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold has to be above 0 and at most 1")

    def match(expected: Any, actual: Any) -> MatchResult:
        e = _as_set(expected)
        a = _as_set(actual)
        if e is None or a is None:
            return _miss(detail="one side is not a collection")
        if casefold:
            e = {x.casefold() for x in e}
            a = {x.casefold() for x in a}
        if not e and not a:
            return _hit(detail="both empty")
        union = e | a
        shared = e & a
        score = len(shared) / len(union) if union else 1.0
        if score >= threshold - 1e-12:
            return _hit(score=score, detail=f"overlap {score:.2f}")
        missing = sorted(e - a)
        extra = sorted(a - e)
        return _miss(
            score=score,
            detail=f"overlap {score:.2f}, missing {missing}, extra {extra}",
        )

    match.__name__ = "set_overlap"
    return match


def fuzzy(threshold: float = 0.85, casefold: bool = True) -> Matcher:
    """Compare text by similarity. For free text answers, not for labels.

    Never use this on a classification. A fuzzy match between
    OPERATING_REVENUE and LOAN_PROCEEDS scores high and means nothing.
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold has to be above 0 and at most 1")

    def match(expected: Any, actual: Any) -> MatchResult:
        e = normalize_text(expected, casefold=casefold, strip_punctuation=True)
        a = normalize_text(actual, casefold=casefold, strip_punctuation=True)
        score = SequenceMatcher(None, e, a).ratio()
        if score >= threshold - 1e-12:
            return _hit(score=score, detail=f"similarity {score:.2f}")
        return _miss(score=score, detail=f"similarity {score:.2f} below {threshold:.2f}")

    match.__name__ = "fuzzy"
    return match


def contains(casefold: bool = True) -> Matcher:
    """Pass when the expected text appears somewhere inside the answer."""

    def match(expected: Any, actual: Any) -> MatchResult:
        e = normalize_text(expected, casefold=casefold)
        a = normalize_text(actual, casefold=casefold)
        if e and e in a:
            return _hit(detail="found")
        return _miss(detail=f"{expected!r} not found in answer")

    match.__name__ = "contains"
    return match


def any_of(*inner: Matcher) -> Matcher:
    """Pass when any of the given matchers passes."""

    def match(expected: Any, actual: Any) -> MatchResult:
        best = _miss(detail="no matcher passed")
        for m in inner:
            r = m(expected, actual)
            if r.matched:
                return r
            if r.score > best.score:
                best = r
        return best

    match.__name__ = "any_of"
    return match


def all_of(*inner: Matcher) -> Matcher:
    """Pass only when every given matcher passes."""

    def match(expected: Any, actual: Any) -> MatchResult:
        scores = []
        for m in inner:
            r = m(expected, actual)
            if not r.matched:
                return r
            scores.append(r.score)
        avg = sum(scores) / len(scores) if scores else 1.0
        return _hit(score=avg, detail="all passed")

    match.__name__ = "all_of"
    return match


def auto() -> Matcher:
    """Pick a sensible matcher from the shape of the expected value.

    Numbers compare exactly. Lists and sets compare as sets. Everything else
    compares as normalized text. This is the default so a new suite runs
    before you have thought hard about matching, but you should think hard
    about matching.
    """
    _num = numeric(tolerance=0.0)
    _set = set_overlap(1.0)
    _text = normalized()

    def match(expected: Any, actual: Any) -> MatchResult:
        if isinstance(expected, bool):
            return exact()(expected, actual)
        if isinstance(expected, (int, float)):
            return _num(expected, actual)
        if isinstance(expected, (list, tuple, set, frozenset)):
            return _set(expected, actual)
        return _text(expected, actual)

    match.__name__ = "auto"
    return match


def by_field(
    field_matchers: Mapping[str, Matcher],
    default: Matcher | None = None,
    require_all: bool = True,
) -> Matcher:
    """Match a whole answer object, one field at a time.

    The Runner uses this by default. `expected` and `actual` are both dicts.
    A field named in `field_matchers` uses that matcher. Anything else uses
    `default`, which is `auto()` unless you say otherwise.
    """
    fallback = default or auto()

    def match(expected: Any, actual: Any) -> MatchResult:
        if not isinstance(expected, Mapping):
            return fallback(expected, actual)
        if not isinstance(actual, Mapping):
            return _miss(detail=f"expected an object, got {type(actual).__name__}")

        failures: list[str] = []
        scores: list[float] = []
        for key, want in expected.items():
            m = field_matchers.get(key, fallback)
            got = actual.get(key)
            if key not in actual:
                failures.append(f"{key}: missing from the answer")
                scores.append(0.0)
                continue
            r = m(want, got)
            scores.append(r.score)
            if not r.matched:
                failures.append(f"{key}: {r.detail}")

        avg = sum(scores) / len(scores) if scores else 1.0
        if not failures:
            return _hit(score=avg, detail="all fields matched")
        if not require_all and len(failures) < len(expected):
            return _hit(score=avg, detail="; ".join(failures))
        return _miss(score=avg, detail="; ".join(failures))

    match.__name__ = "by_field"
    return match


REGISTRY: dict[str, Callable[..., Matcher]] = {
    "exact": exact,
    "normalized": normalized,
    "numeric": numeric,
    "set_overlap": set_overlap,
    "fuzzy": fuzzy,
    "contains": contains,
    "auto": auto,
}


def get(name: str, **kwargs: Any) -> Matcher:
    """Look up a matcher by name. Handy for config files and the CLI."""
    if name not in REGISTRY:
        known = ", ".join(sorted(REGISTRY))
        raise KeyError(f"no matcher named '{name}'. Known matchers: {known}")
    return REGISTRY[name](**kwargs)
