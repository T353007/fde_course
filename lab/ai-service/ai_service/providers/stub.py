"""The stub provider. A model simulator, not a mock.

Read this file before you write a mission that uses it.

Why it exists
-------------
The lab has to fail the same way on every machine. If Mission 32's outage only
happens sometimes, the debugging walkthrough is fiction. So the answers here are
real recorded model output, frozen on disk, replayed by key.

The key is (prompt_version, sha256(normalized_input), scenario).

If no fixture matches, this raises FixtureMissing. It does not guess, and it
does not fall back to a nearby answer. A missing fixture is a red test in CI
instead of a quiet wrong number in a credit memo.

Scenarios
---------
Set with the X-Stub-Scenario header or the STUB_SCENARIO environment variable.
Each one reproduces a real failure that a mission investigates. See SCENARIOS
below for the list.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_service.config import get_settings
from ai_service.providers.base import (
    STUB_COST_BASIS,
    CompletionRequest,
    CompletionResponse,
    FixtureMissing,
    ProviderError,
    ToolCall,
    estimate_tokens,
    input_sha256,
)

# Scenario name -> what it does and who uses it. Kept next to the code that
# reads it so the two cannot drift apart.
SCENARIOS: dict[str, str] = {
    "default": "The recorded good path. Used everywhere.",
    "revenue-as-string": (
        'Returns "$78,231 approximately" where a number belongs. Mission 32.'
    ),
    "slow-p99": "Sleeps 9 to 40 seconds, same input gives the same delay. Missions 31 and 34.",
    "truncated-json": "Output stops at the token limit mid object. Mission 13.",
    "hallucinated-ein": "Fills in an EIN that was blank in the source. Mission 14.",
    "injected-instructions": "Obeys instructions written in the document. Mission 26.",
    "overconfident-ocr": "High confidence, wrong values. Mission 19.",
    "tool-overreach": "Calls declineApplication on a read-only question. Mission 27.",
}

# slow-p99 picks a delay in this window. The floor is 9 seconds because that is
# what the Corveil bureau call actually does at p99, and the ceiling is the
# 40 second number in CANON.
SLOW_P99_FLOOR_SECONDS = 9.0
SLOW_P99_CEILING_SECONDS = 40.0


@dataclass(frozen=True)
class Fixture:
    """One recorded model answer, loaded from a JSON file."""

    fixture_id: str
    prompt_version: str
    scenario: str
    match_mode: str  # "sha256" or "any_input"
    input_sha256: str | None
    model: str
    text: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: int
    finish_reason: str
    tool_calls: list[dict[str, Any]]
    delegate_to_scenario: str | None
    sleep_seconds_range: tuple[float, float] | None
    source_path: Path
    recorded_from: str
    notes: str


class ScenarioUnknown(ProviderError):
    """Someone asked for a scenario that does not exist.

    Failing here catches the typo. A silent fall back to default would let a
    mission claim it tested a failure path when it tested the happy path.
    """

    def __init__(self, scenario: str) -> None:
        known = ", ".join(sorted(SCENARIOS))
        super().__init__(
            f"Unknown stub scenario {scenario!r}. Known scenarios: {known}."
        )


def _as_range(value: Any) -> tuple[float, float] | None:
    if not value:
        return None
    low, high = value
    return (float(low), float(high))


def load_fixtures(fixture_dir: Path) -> list[Fixture]:
    """Read every *.json under fixture_dir into a Fixture."""
    fixtures: list[Fixture] = []
    if not fixture_dir.exists():
        return fixtures

    for path in sorted(fixture_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw if isinstance(raw, list) else [raw]
        for entry in entries:
            match = entry.get("match", {})
            response = entry.get("response", {})
            sha = match.get("input_sha256")
            # A fixture may store the input text it was recorded from instead of
            # a hash. That way you can read the file and see what question
            # produced the answer, and nobody has to hand maintain a hash.
            if sha is None and match.get("input_text") is not None:
                sha = input_sha256(match["input_text"])
            fixtures.append(
                Fixture(
                    fixture_id=entry["fixture_id"],
                    prompt_version=entry["prompt_version"],
                    scenario=entry["scenario"],
                    match_mode=match.get("mode", "sha256"),
                    input_sha256=sha,
                    model=entry.get("model", "qwen3:8b"),
                    text=response.get("text"),
                    prompt_tokens=response.get("prompt_tokens"),
                    completion_tokens=response.get("completion_tokens"),
                    latency_ms=int(response.get("latency_ms", 0)),
                    finish_reason=response.get("finish_reason", "stop"),
                    tool_calls=response.get("tool_calls", []) or [],
                    delegate_to_scenario=response.get("delegate_to_scenario"),
                    sleep_seconds_range=_as_range(entry.get("sleep_seconds_range")),
                    source_path=path,
                    recorded_from=entry.get("recorded", {}).get("from", "unknown"),
                    notes=entry.get("notes", ""),
                )
            )
    return fixtures


class StubProvider:
    """Replays recorded model output. Deterministic by construction."""

    name = "stub"

    def __init__(
        self,
        fixture_dir: Path | None = None,
        default_scenario: str | None = None,
        slow_scale: float | None = None,
    ) -> None:
        settings = get_settings()
        self.fixture_dir = Path(fixture_dir or settings.fixture_path)
        self.default_scenario = default_scenario or settings.stub_scenario
        self.slow_scale = settings.stub_slow_scale if slow_scale is None else slow_scale
        self._by_sha: dict[tuple[str, str, str], Fixture] = {}
        self._by_any: dict[tuple[str, str], Fixture] = {}
        self._all: list[Fixture] = []
        self.reload()

    # -- loading -----------------------------------------------------------

    def reload(self) -> None:
        self._all = load_fixtures(self.fixture_dir)
        self._by_sha.clear()
        self._by_any.clear()
        for fixture in self._all:
            if fixture.match_mode == "any_input":
                self._by_any[(fixture.prompt_version, fixture.scenario)] = fixture
            else:
                if not fixture.input_sha256:
                    raise ProviderError(
                        f"Fixture {fixture.fixture_id} in {fixture.source_path.name} "
                        "uses sha256 matching but has no input_sha256."
                    )
                key = (
                    fixture.prompt_version,
                    fixture.input_sha256,
                    fixture.scenario,
                )
                self._by_sha[key] = fixture

    @property
    def fixture_count(self) -> int:
        return len(self._all)

    def known_prompt_versions(self) -> list[str]:
        return sorted({f.prompt_version for f in self._all})

    # -- lookup ------------------------------------------------------------

    def _lookup(
        self, prompt_version: str, sha: str, scenario: str
    ) -> Fixture:
        """Exact input match wins. A scenario wide fixture is the fallback.

        There is no third level. If neither matches we raise, on purpose.
        """
        exact = self._by_sha.get((prompt_version, sha, scenario))
        if exact is not None:
            return exact
        wide = self._by_any.get((prompt_version, scenario))
        if wide is not None:
            return wide
        raise FixtureMissing(prompt_version, sha, scenario)

    def resolve_scenario(self, req: CompletionRequest) -> str:
        scenario = req.scenario or self.default_scenario
        if scenario not in SCENARIOS:
            raise ScenarioUnknown(scenario)
        return scenario

    def slow_p99_delay_seconds(self, sha: str, low: float, high: float) -> float:
        """Pick a delay from the input hash so the same input always waits the same.

        A random sleep would make Mission 31's trace screenshots useless.
        """
        span_ms = int(round((high - low) * 1000))
        offset_ms = int(sha[:16], 16) % (span_ms + 1)
        return round(low + offset_ms / 1000.0, 3)

    # -- the provider contract --------------------------------------------

    def supports_json_schema(self) -> bool:
        """False on purpose.

        The recorded output includes the markdown fences and stray prose that a
        real model produced. If the stub claimed schema support, the parse
        repair ladder in parsing.py would never run and Mission 13 would have
        nothing to teach.
        """
        return False

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        scenario = self.resolve_scenario(req)
        sha = input_sha256(req.key_material())
        fixture = self._lookup(req.prompt_version, sha, scenario)

        started = time.perf_counter()
        planned_delay = 0.0

        if fixture.sleep_seconds_range is not None:
            low, high = fixture.sleep_seconds_range
            planned_delay = self.slow_p99_delay_seconds(sha, low, high)
            # stub_slow_scale exists so the test suite does not take nine
            # minutes. The delay above is still calculated from the input and
            # still reported in latency_ms, so the scenario does not lie.
            actual = planned_delay * self.slow_scale
            if actual > 0:
                time.sleep(actual)

        body = fixture
        if fixture.delegate_to_scenario:
            # Scenarios like slow-p99 change timing, not content. Rather than
            # copy the good answer into every scenario file, they point at it.
            body = self._lookup(
                req.prompt_version, sha, fixture.delegate_to_scenario
            )

        text = body.text or ""
        measured_ms = int((time.perf_counter() - started) * 1000)
        if planned_delay:
            latency_ms = int(planned_delay * 1000)
        else:
            latency_ms = body.latency_ms or measured_ms

        tool_calls = [ToolCall(**tc) for tc in (fixture.tool_calls or body.tool_calls)]

        return CompletionResponse(
            text=text,
            model=fixture.model or body.model,
            prompt_version=req.prompt_version,
            prompt_tokens=body.prompt_tokens
            if body.prompt_tokens is not None
            else estimate_tokens(req.prompt),
            completion_tokens=body.completion_tokens
            if body.completion_tokens is not None
            else estimate_tokens(text),
            latency_ms=latency_ms,
            cost_usd=0.0,
            cost_basis=STUB_COST_BASIS,
            finish_reason=fixture.finish_reason or body.finish_reason,
            tool_calls=tool_calls,
            provider=self.name,
            raw={
                "scenario": scenario,
                "fixture_id": fixture.fixture_id,
                "fixture_file": fixture.source_path.name,
                "input_sha256": sha,
                "recorded_from": body.recorded_from,
                "planned_delay_seconds": planned_delay,
                "slow_scale_applied": self.slow_scale,
            },
        )
