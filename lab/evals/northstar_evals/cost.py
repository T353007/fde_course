"""Cost and latency, per run and per case.

An eval that only reports accuracy will let you ship something correct and
unaffordable. Northstar's bill went from $22,000 to $91,000 in a month and
nobody could say which call did it. So every run records tokens, dollars, and
milliseconds next to the score.

Local and stub providers cost 0.0 dollars. That is a real number, not a
missing one, so `cost_basis` records why it is zero. Free per call still costs
hardware and it still costs seconds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

# Dollars per one million tokens. Rough public list prices, good enough to
# rank options. Update the number, not the code, when a vendor changes it.
PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-sonnet": (3.00, 15.00),
    "claude-haiku": (0.80, 4.00),
    "qwen3:8b": (0.0, 0.0),
    "qwen3:1.7b": (0.0, 0.0),
    "llama3.1:8b": (0.0, 0.0),
    "stub": (0.0, 0.0),
}

FREE_BASIS = {
    "stub": "stub provider, no model call was made",
    "ollama": "local model, no per token charge",
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Dollars for one call, from the price table. Unknown model costs 0.0."""
    rates = PRICING.get(model)
    if rates is None:
        return 0.0
    in_rate, out_rate = rates
    return (prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000


def percentile(values: Sequence[float], p: float) -> float:
    """Nearest rank percentile. p is 0 to 100. Empty input gives 0.0.

    Nearest rank, not interpolated, because for latency you want a number a
    real request actually took.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    rank = max(1, min(len(ordered), int(round(p / 100.0 * len(ordered) + 0.5))))
    return ordered[rank - 1]


@dataclass
class Usage:
    """What one call spent."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model: str | None = None
    cost_basis: str = ""

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "costUsd": round(self.cost_usd, 8),
            "latencyMs": round(self.latency_ms, 3),
            "model": self.model,
            "costBasis": self.cost_basis,
        }


@dataclass
class CostSummary:
    """Cost and latency rolled up over a run."""

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_usd: float = 0.0
    latencies_ms: list[float] = field(default_factory=list)
    cost_basis: str = ""
    wall_clock_s: float = 0.0

    @classmethod
    def from_usages(
        cls,
        usages: Iterable[Usage],
        wall_clock_s: float = 0.0,
    ) -> "CostSummary":
        summary = cls(wall_clock_s=wall_clock_s)
        bases: set[str] = set()
        for u in usages:
            summary.calls += 1
            summary.prompt_tokens += u.prompt_tokens
            summary.completion_tokens += u.completion_tokens
            summary.total_usd += u.cost_usd
            summary.latencies_ms.append(u.latency_ms)
            if u.cost_basis:
                bases.add(u.cost_basis)
        summary.cost_basis = "; ".join(sorted(bases))
        return summary

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def usd_per_case(self) -> float:
        return self.total_usd / self.calls if self.calls else 0.0

    @property
    def p50_ms(self) -> float:
        return percentile(self.latencies_ms, 50)

    @property
    def p95_ms(self) -> float:
        return percentile(self.latencies_ms, 95)

    @property
    def p99_ms(self) -> float:
        return percentile(self.latencies_ms, 99)

    @property
    def mean_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0

    def project_monthly(self, calls_per_month: int) -> float:
        """What this run's cost per case would come to at Northstar's volume.

        1,840 applications a month is the number from discovery. Multiply by
        how many model calls each application makes before you quote it.
        """
        return self.usd_per_case * calls_per_month

    def to_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "totalTokens": self.total_tokens,
            "totalUsd": round(self.total_usd, 8),
            "usdPerCase": round(self.usd_per_case, 8),
            "latencyMs": {
                "mean": round(self.mean_ms, 2),
                "p50": round(self.p50_ms, 2),
                "p95": round(self.p95_ms, 2),
                "p99": round(self.p99_ms, 2),
            },
            "wallClockSeconds": round(self.wall_clock_s, 3),
            "costBasis": self.cost_basis,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CostSummary":
        lat = raw.get("latencyMs") or {}
        summary = cls(
            calls=int(raw.get("calls", 0)),
            prompt_tokens=int(raw.get("promptTokens", 0)),
            completion_tokens=int(raw.get("completionTokens", 0)),
            total_usd=float(raw.get("totalUsd", 0.0)),
            cost_basis=raw.get("costBasis", ""),
            wall_clock_s=float(raw.get("wallClockSeconds", 0.0)),
        )
        # Rebuild just enough of the distribution to keep p50 and p95 readable.
        for key in ("p50", "p95", "p99"):
            if key in lat:
                summary.latencies_ms.append(float(lat[key]))
        return summary

    def line(self) -> str:
        """One line for the bottom of a report."""
        return (
            f"cost ${self.total_usd:.4f} over {self.calls} calls "
            f"(${self.usd_per_case:.6f} each), "
            f"latency p50 {self.p50_ms:.0f} ms, p95 {self.p95_ms:.0f} ms, "
            f"wall clock {self.wall_clock_s:.1f} s"
        )
