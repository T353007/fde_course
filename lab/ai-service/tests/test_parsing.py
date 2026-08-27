"""ParseFailure taxonomy and repair ladder."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from ai_service.parsing import (
    ParseFailure,
    ParseFailureKind,
    close_truncated_json,
    parse_structured,
    should_retry,
    strip_markdown_fences,
)


class Tiny(BaseModel):
    average_revenue: float


def test_schema_error_kind_for_string_number():
    with pytest.raises(ParseFailure) as raised:
        parse_structured(
            '{"averageRevenue": "$78,231 approximately"}',
            Tiny,
            prompt_version="revenue_summary_v1",
        )
    assert raised.value.kind == ParseFailureKind.SCHEMA_ERROR


def test_truncated_kind_when_finish_reason_length():
    raw = '{"averageRevenue": 10, "method": "partial'
    with pytest.raises(ParseFailure) as raised:
        parse_structured(raw, Tiny, finish_reason="length")
    assert raised.value.kind in {
        ParseFailureKind.TRUNCATED,
        ParseFailureKind.SCHEMA_ERROR,
    }


def test_refusal_kind():
    with pytest.raises(ParseFailure) as raised:
        parse_structured("I cannot help with that request.", Tiny)
    assert raised.value.kind == ParseFailureKind.REFUSAL


def test_empty_kind():
    with pytest.raises(ParseFailure) as raised:
        parse_structured("   ", Tiny)
    assert raised.value.kind == ParseFailureKind.EMPTY


def test_legacy_retries_schema_error_typed_does_not():
    assert should_retry(
        ParseFailureKind.SCHEMA_ERROR, 1, max_attempts=5, policy="legacy"
    )
    assert not should_retry(
        ParseFailureKind.SCHEMA_ERROR, 1, max_attempts=5, policy="typed"
    )
    assert should_retry(
        ParseFailureKind.TIMEOUT, 1, max_attempts=5, policy="typed"
    )


def test_strip_fences_and_close_truncated():
    fenced = "```json\n{\"a\": 1}\n```\nThanks!"
    assert '"a"' in strip_markdown_fences(fenced)
    closed = close_truncated_json('{"a": 1, "b": [1, 2')
    assert closed.endswith("]}")
