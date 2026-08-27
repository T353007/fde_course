"""Compare two runs: model against model, or prompt against prompt.

The question is never "is this model good." It is "is this one better than
what we have, on the cases we care about, for a price we can pay." That is a
three column table, not a single number.

    from northstar_evals import compare

    cmp = compare(hosted_result, local_result, name_a="gpt-4o", name_b="qwen3:8b")
    cmp.report()

The flips list is the part people miss. Two runs can score the same overall
while swapping 30 cases in each direction. If those 30 cases are loan
deposits, the score did not change and your risk did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from .metrics import percent
from .result import Result


@dataclass
class SliceDelta:
    """One slice, scored under both runs."""

    name: str
    support_a: int
    support_b: int
    accuracy_a: float
    accuracy_b: float

    @property
    def delta(self) -> float:
        return self.accuracy_b - self.accuracy_a

    @property
    def points(self) -> float:
        return self.delta * 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "supportA": self.support_a,
            "supportB": self.support_b,
            "accuracyA": round(self.accuracy_a, 6),
            "accuracyB": round(self.accuracy_b, 6),
            "deltaPoints": round(self.points, 2),
        }


@dataclass
class Flip:
    """A case whose outcome changed between the two runs."""

    case_id: str
    direction: str  # "fixed" or "broken"
    expected: Any
    predicted_a: Any
    predicted_b: Any
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "caseId": self.case_id,
            "direction": self.direction,
            "expected": self.expected,
            "predictedA": self.predicted_a,
            "predictedB": self.predicted_b,
            "tags": self.tags,
        }


class Comparison:
    """The result of comparing two runs."""

    def __init__(
        self,
        result_a: Result,
        result_b: Result,
        name_a: str,
        name_b: str,
        slice_deltas: Sequence[SliceDelta],
        flips: Sequence[Flip],
        shared_cases: int,
    ) -> None:
        self.result_a = result_a
        self.result_b = result_b
        self.name_a = name_a
        self.name_b = name_b
        self.slice_deltas = list(slice_deltas)
        self.flips = list(flips)
        self.shared_cases = shared_cases

    @property
    def overall_delta(self) -> float:
        return self.result_b.accuracy - self.result_a.accuracy

    @property
    def fixed(self) -> list[Flip]:
        return [f for f in self.flips if f.direction == "fixed"]

    @property
    def broken(self) -> list[Flip]:
        return [f for f in self.flips if f.direction == "broken"]

    @property
    def cost_delta(self) -> float:
        return self.result_b.cost.total_usd - self.result_a.cost.total_usd

    @property
    def latency_delta_ms(self) -> float:
        return self.result_b.cost.p50_ms - self.result_a.cost.p50_ms

    def worst_slices(self, n: int = 3) -> list[SliceDelta]:
        return sorted(self.slice_deltas, key=lambda d: d.delta)[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "a": {
                "name": self.name_a,
                "provider": self.result_a.run.provider,
                "model": self.result_a.run.model,
                "accuracy": round(self.result_a.accuracy, 6),
                "cost": self.result_a.cost.to_dict(),
            },
            "b": {
                "name": self.name_b,
                "provider": self.result_b.run.provider,
                "model": self.result_b.run.model,
                "accuracy": round(self.result_b.accuracy, 6),
                "cost": self.result_b.cost.to_dict(),
            },
            "sharedCases": self.shared_cases,
            "overallDeltaPoints": round(self.overall_delta * 100, 2),
            "slices": [d.to_dict() for d in self.slice_deltas],
            "fixed": len(self.fixed),
            "broken": len(self.broken),
            "flips": [f.to_dict() for f in self.flips[:200]],
        }

    def report(self, stream: Any = None, max_flips: int = 10) -> str:
        text = render_comparison(self, max_flips=max_flips)
        import sys

        print(text, file=stream or sys.stdout)
        return text


def compare(
    result_a: Result,
    result_b: Result,
    name_a: str | None = None,
    name_b: str | None = None,
) -> Comparison:
    """Compare two runs over the same dataset.

    If the two runs used different dataset files, you get a warning in the
    report rather than an error. Sometimes comparing across dataset versions
    is what you meant.
    """
    label_a = name_a or _describe(result_a)
    label_b = name_b or _describe(result_b)

    slice_names = [s.name for s in result_a.slices]
    for s in result_b.slices:
        if s.name not in slice_names:
            slice_names.append(s.name)

    deltas: list[SliceDelta] = []
    for name in slice_names:
        sa = result_a.slice(name)
        sb = result_b.slice(name)
        deltas.append(
            SliceDelta(
                name=name,
                support_a=sa.support if sa else 0,
                support_b=sb.support if sb else 0,
                accuracy_a=sa.accuracy if sa else 0.0,
                accuracy_b=sb.accuracy if sb else 0.0,
            )
        )

    by_id_a = {cr.case_id: cr for cr in result_a.case_results}
    by_id_b = {cr.case_id: cr for cr in result_b.case_results}
    shared = sorted(set(by_id_a) & set(by_id_b))

    flips: list[Flip] = []
    for cid in shared:
        ca, cb = by_id_a[cid], by_id_b[cid]
        if ca.matched == cb.matched:
            continue
        flips.append(
            Flip(
                case_id=cid,
                direction="fixed" if cb.matched else "broken",
                expected=ca.expected_label,
                predicted_a=ca.predicted_label,
                predicted_b=cb.predicted_label,
                tags=dict(ca.case.tags),
            )
        )

    return Comparison(
        result_a=result_a,
        result_b=result_b,
        name_a=label_a,
        name_b=label_b,
        slice_deltas=deltas,
        flips=flips,
        shared_cases=len(shared),
    )


def _describe(result: Result) -> str:
    model = result.run.model or result.run.provider
    if result.run.prompt_version:
        return f"{model}@{result.run.prompt_version}"
    return str(model)


def _signed(points: float) -> str:
    return f"{points:+.1f}"


def render_comparison(cmp: Comparison, max_flips: int = 10, width: int = 92) -> str:
    rule = "-" * width
    a, b = cmp.name_a, cmp.name_b
    lines = ["", f"COMPARE  A = {a}   B = {b}", rule]

    if cmp.result_a.provenance.sha256 != cmp.result_b.provenance.sha256:
        lines.append(
            "WARNING: the two runs used different dataset files. "
            "Some of this difference is the data, not the model."
        )
        lines.append("")

    lines.append(
        f"{'SLICE':<22}{'SUPPORT':>8}{'A':>10}{'B':>10}{'CHANGE':>10}"
    )
    lines.append(rule)
    lines.append(
        f"{'OVERALL':<22}{cmp.result_a.total:>8}"
        f"{percent(cmp.result_a.accuracy):>10}"
        f"{percent(cmp.result_b.accuracy):>10}"
        f"{_signed(cmp.overall_delta * 100):>9} pt"
    )
    lines.append(rule)
    for d in sorted(cmp.slice_deltas, key=lambda x: -x.support_a):
        flag = ""
        if d.points <= -5:
            flag = "  <-- worse"
        elif d.points >= 5:
            flag = "  <-- better"
        lines.append(
            f"{d.name:<22}{d.support_a:>8}"
            f"{percent(d.accuracy_a):>10}{percent(d.accuracy_b):>10}"
            f"{_signed(d.points):>9} pt{flag}"
        )
    lines.append(rule)

    lines.append(
        f"cases that B fixed: {len(cmp.fixed)}    "
        f"cases that B broke: {len(cmp.broken)}    "
        f"shared cases: {cmp.shared_cases}"
    )
    if cmp.fixed and cmp.broken:
        lines.append(
            "Both runs changed cases in both directions. A flat overall score "
            "can still be a different product."
        )

    ca, cb = cmp.result_a.cost, cmp.result_b.cost
    lines.append("")
    lines.append(
        f"cost per case   A ${ca.usd_per_case:.6f}   B ${cb.usd_per_case:.6f}   "
        f"change ${cmp.cost_delta:+.4f} over the run"
    )
    lines.append(
        f"latency p50     A {ca.p50_ms:.0f} ms   B {cb.p50_ms:.0f} ms   "
        f"change {cmp.latency_delta_ms:+.0f} ms"
    )

    broken = cmp.broken[:max_flips]
    if broken:
        lines.append("")
        lines.append(f"CASES B BROKE (showing {len(broken)} of {len(cmp.broken)})")
        lines.append(rule)
        for f in broken:
            kind = f.tags.get("kind", "")
            ocr = f.tags.get("ocr_quality", "")
            lines.append(
                f"{f.case_id:<12} expected {f.expected}   "
                f"A said {f.predicted_a}   B said {f.predicted_b}"
            )
            if kind or ocr:
                lines.append(f"{'':<12} kind={kind} ocr={ocr}")

    lines.append("")
    return "\n".join(lines)


def compare_many(
    results: dict[str, Result],
    slice_names: Sequence[str] | None = None,
    width: int = 92,
) -> str:
    """A grid of several runs at once. Rows are slices, columns are runs.

    Use this for a model bake off, where four options and five slices do not
    fit into a stack of pairwise reports.
    """
    if not results:
        return "(nothing to compare)"
    names = list(results)
    first = results[names[0]]
    slices = list(slice_names or [s.name for s in first.slices])

    col = max(12, max(len(n) for n in names) + 2)
    rule = "-" * width
    lines = ["", "MODEL COMPARISON", rule]
    lines.append(f"{'SLICE':<22}{'SUPPORT':>8}" + "".join(n.rjust(col) for n in names))
    lines.append(rule)

    lines.append(
        f"{'OVERALL':<22}{first.total:>8}"
        + "".join(percent(results[n].accuracy).rjust(col) for n in names)
    )
    lines.append(rule)
    for sname in slices:
        support = 0
        cells = []
        for n in names:
            s = results[n].slice(sname)
            support = max(support, s.support if s else 0)
            cells.append(percent(s.accuracy) if s else "n/a")
        lines.append(
            f"{sname:<22}{support:>8}" + "".join(c.rjust(col) for c in cells)
        )
    lines.append(rule)
    lines.append(
        f"{'cost / case':<22}{'':>8}"
        + "".join(f"${results[n].cost.usd_per_case:.5f}".rjust(col) for n in names)
    )
    lines.append(
        f"{'latency p50 ms':<22}{'':>8}"
        + "".join(f"{results[n].cost.p50_ms:.0f}".rjust(col) for n in names)
    )
    lines.append("")
    return "\n".join(lines)
