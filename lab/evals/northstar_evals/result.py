"""The Result object and the console report.

A Result is what a Runner hands back. It holds every case outcome, the rolled
up metrics for the whole set and for each slice, the cost, and enough
provenance to reproduce the run.

The report is the teaching artifact of this whole library. It puts overall
accuracy on top, then every slice below it with a support count and a bar
showing how much of the dataset that slice is. Once you see that the 99
percent slice is 84 percent of the volume, the 96 percent stops feeling like
good news.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, TextIO

from .case import Case
from .cost import CostSummary, Usage
from .dataset import Provenance
from .metrics import (
    ConfusionMatrix,
    SliceMetrics,
    build_slice_metrics,
    percent,
)

OVERALL = "OVERALL"


class RegressionError(AssertionError):
    """Raised by assert_no_regression when a run got worse than the baseline."""


@dataclass
class CaseResult:
    """What happened for one case."""

    case: Case
    predicted: Any = None
    matched: bool = False
    score: float = 0.0
    detail: str = ""
    usage: Usage = field(default_factory=Usage)
    error: str | None = None
    expected_label: Any = None
    predicted_label: Any = None

    @property
    def case_id(self) -> str:
        return self.case.case_id

    @property
    def errored(self) -> bool:
        return self.error is not None

    def to_dict(self, include_case: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {
            "caseId": self.case_id,
            "matched": self.matched,
            "score": round(self.score, 6),
            "expected": self.expected_label,
            "predicted": self.predicted_label,
            "usage": self.usage.to_dict(),
        }
        if self.detail:
            out["detail"] = self.detail
        if self.error:
            out["error"] = self.error
        if include_case:
            out["case"] = self.case.to_dict()
        return out


@dataclass
class RunInfo:
    """Everything you need to say what produced this number."""

    suite: str = "unnamed"
    provider: str = "unknown"
    model: str | None = None
    prompt_version: str | None = None
    started_at: str = ""
    duration_s: float = 0.0
    matcher: str = "by_field"
    label_field: str | None = None
    host: str = ""
    python: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, **kwargs: Any) -> "RunInfo":
        return cls(
            started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            host=platform.node(),
            python=platform.python_version(),
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "provider": self.provider,
            "model": self.model,
            "promptVersion": self.prompt_version,
            "startedAt": self.started_at,
            "durationSeconds": round(self.duration_s, 3),
            "matcher": self.matcher,
            "labelField": self.label_field,
            "host": self.host,
            "python": self.python,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RunInfo":
        return cls(
            suite=raw.get("suite", "unnamed"),
            provider=raw.get("provider", "unknown"),
            model=raw.get("model"),
            prompt_version=raw.get("promptVersion"),
            started_at=raw.get("startedAt", ""),
            duration_s=float(raw.get("durationSeconds", 0.0)),
            matcher=raw.get("matcher", "by_field"),
            label_field=raw.get("labelField"),
            host=raw.get("host", ""),
            python=raw.get("python", ""),
            metadata=raw.get("metadata") or {},
        )


class Result:
    """The output of a run. Print it, save it, or compare it to a baseline."""

    def __init__(
        self,
        run: RunInfo,
        provenance: Provenance,
        case_results: Sequence[CaseResult],
        overall: SliceMetrics,
        slices: Sequence[SliceMetrics] = (),
        cost: CostSummary | None = None,
        slice_descriptions: dict[str, str] | None = None,
    ) -> None:
        self.run = run
        self.provenance = provenance
        self.case_results = list(case_results)
        self.overall = overall
        self.slices = list(slices)
        self.cost = cost or CostSummary()
        self.slice_descriptions = slice_descriptions or {}
        self._slice_index: dict[str, list[int]] = {}

    # ------------------------------------------------------------- shortcuts

    @property
    def accuracy(self) -> float:
        return self.overall.accuracy

    @property
    def total(self) -> int:
        return self.overall.support

    @property
    def confusion(self) -> ConfusionMatrix:
        return self.overall.confusion

    def slice(self, name: str) -> SliceMetrics | None:
        for s in self.slices:
            if s.name == name:
                return s
        return None

    def slice_accuracy(self, name: str) -> float:
        s = self.slice(name)
        if s is None:
            raise KeyError(f"no slice named '{name}' in this result")
        return s.accuracy

    def failures(self, slice_name: str | None = None) -> list[CaseResult]:
        """Every case that did not match. Read these before touching a prompt."""
        rows = [cr for cr in self.case_results if not cr.matched]
        if slice_name:
            keep = {cr.case_id for cr in self._cases_in_slice(slice_name)}
            rows = [cr for cr in rows if cr.case_id in keep]
        return rows

    def errors(self) -> list[CaseResult]:
        """Cases where the task itself raised. Not the same as a wrong answer."""
        return [cr for cr in self.case_results if cr.errored]

    def _cases_in_slice(self, name: str) -> list[CaseResult]:
        idx = self._slice_index.get(name, [])
        return [self.case_results[i] for i in idx]

    # ------------------------------------------------------------ the report

    def report(
        self,
        detail: bool = False,
        stream: TextIO | None = None,
        max_failures: int = 8,
    ) -> str:
        """Print the slice table. Returns the same text so tests can read it."""
        text = slice_report(self, detail=detail, max_failures=max_failures)
        out = stream if stream is not None else sys.stdout
        print(text, file=out)
        return text

    # ------------------------------------------------------------ saving out

    def to_dict(self, include_cases: bool = True) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "run": self.run.to_dict(),
            "dataset": self.provenance.to_dict(),
            "overall": self.overall.to_dict(),
            "slices": [s.to_dict() for s in self.slices],
            "cost": self.cost.to_dict(),
            "cases": [cr.to_dict() for cr in self.case_results] if include_cases else [],
        }

    def to_json(self, include_cases: bool = True, indent: int = 2) -> str:
        return json.dumps(self.to_dict(include_cases), indent=indent, sort_keys=False)

    def save(
        self,
        path: str | os.PathLike[str],
        include_cases: bool = True,
    ) -> Path:
        """Write the result to disk. This is how you create a baseline."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(include_cases) + "\n", encoding="utf-8")
        return p

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> "BaselineResult":
        """Read a saved result back. Baselines load as BaselineResult."""
        return BaselineResult.load(path)

    # ------------------------------------------------------------ the gate

    def assert_no_regression(
        self,
        baseline: str | os.PathLike[str] | "BaselineResult",
        tolerance: float = 0.01,
        per_slice: dict[str, float] | None = None,
        require_all_slices: bool = True,
    ) -> "BaselineResult":
        """Fail if this run is worse than the baseline.

        `tolerance` is how far a number may drop before it counts as a
        regression, as a fraction. 0.01 means one accuracy point.

        `per_slice` lets you be stricter where it matters. Loan proceeds can
        get a tolerance of 0.0 while the easy slice gets the default.

        Returns the baseline so you can look at it. Raises RegressionError
        when something got worse.
        """
        base = (
            baseline
            if isinstance(baseline, BaselineResult)
            else BaselineResult.load(baseline)
        )
        per_slice = per_slice or {}
        problems: list[str] = []

        # Accuracies are rounded to 6 places when a baseline is saved, so a
        # zero tolerance still needs a little room for that round trip.
        eps = 1e-6
        drop = base.accuracy - self.accuracy
        if drop > tolerance + eps:
            problems.append(
                f"overall fell from {percent(base.accuracy)} to "
                f"{percent(self.accuracy)}, a drop of {drop * 100:.2f} points "
                f"(allowed {tolerance * 100:.2f})"
            )

        for name, base_acc in base.slice_accuracies.items():
            mine = self.slice(name)
            if mine is None:
                if require_all_slices:
                    problems.append(
                        f"slice '{name}' is in the baseline but not in this run"
                    )
                continue
            limit = per_slice.get(name, tolerance)
            slice_drop = base_acc - mine.accuracy
            if slice_drop > limit + eps:
                problems.append(
                    f"slice '{name}' fell from {percent(base_acc)} to "
                    f"{percent(mine.accuracy)}, a drop of "
                    f"{slice_drop * 100:.2f} points (allowed {limit * 100:.2f})"
                )

        if problems:
            header = (
                f"this run is worse than {base.source}\n"
                f"  baseline: {base.run.provider}/{base.run.model} "
                f"on {base.provenance.short_sha}\n"
                f"  this run: {self.run.provider}/{self.run.model} "
                f"on {self.provenance.short_sha}"
            )
            if base.provenance.sha256 != self.provenance.sha256:
                header += "\n  the dataset changed, so some of this may be the data"
            body = "\n".join(f"  - {p}" for p in problems)
            raise RegressionError(f"{header}\n{body}")
        return base

    def __repr__(self) -> str:
        return (
            f"Result(suite={self.run.suite!r}, provider={self.run.provider!r}, "
            f"n={self.total}, accuracy={percent(self.accuracy)})"
        )


class BaselineResult:
    """A result read back from disk.

    It carries the numbers but not the live case objects, which is all a
    regression check needs and keeps committed baselines small.
    """

    def __init__(self, raw: dict[str, Any], source: str = "<memory>") -> None:
        self.raw = raw
        self.source = source
        self.run = RunInfo.from_dict(raw.get("run") or {})
        self.provenance = Provenance.from_dict(raw.get("dataset") or {})
        overall = raw.get("overall") or {}
        self.accuracy: float = float(overall.get("accuracy", 0.0))
        self.support: int = int(overall.get("support", 0))
        self.correct: int = int(overall.get("correct", 0))
        self.cost = CostSummary.from_dict(raw.get("cost") or {})
        self.slice_accuracies: dict[str, float] = {}
        self.slice_supports: dict[str, int] = {}
        for s in raw.get("slices") or []:
            self.slice_accuracies[s["name"]] = float(s.get("accuracy", 0.0))
            self.slice_supports[s["name"]] = int(s.get("support", 0))

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> "BaselineResult":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(
                f"no baseline at {p}. Create one with "
                "`python -m northstar_evals run --suite <name> --save-baseline <path>`"
            )
        return cls(json.loads(p.read_text(encoding="utf-8")), source=str(p))

    def __repr__(self) -> str:
        return f"BaselineResult({self.source!r}, accuracy={percent(self.accuracy)})"


# ---------------------------------------------------------------------------
# The console renderer
# ---------------------------------------------------------------------------

_BAR_WIDTH = 22


def _bar(share: float, width: int = _BAR_WIDTH) -> str:
    filled = int(round(share * width))
    return "#" * filled + "." * (width - filled)


def slice_report(
    result: Result,
    detail: bool = False,
    max_failures: int = 8,
    width: int = 92,
) -> str:
    """Render the slice table as text.

    Layout on purpose: overall sits alone above a rule, then the slices sit
    below it sorted by how big they are. The share bar makes the size gap
    impossible to miss.
    """
    r = result
    lines: list[str] = []
    rule = "-" * width

    lines.append("")
    lines.append(f"EVAL  {r.run.suite}")
    lines.append(rule)
    model = r.run.model or "n/a"
    prompt = f"  prompt {r.run.prompt_version}" if r.run.prompt_version else ""
    lines.append(f"provider {r.run.provider}   model {model}{prompt}")
    lines.append(
        f"dataset  {r.provenance.path}   "
        f"{r.provenance.case_count} cases   sha256 {r.provenance.short_sha}"
    )
    lines.append(f"run      {r.run.started_at}   matcher {r.run.matcher}")
    lines.append("")

    header = (
        f"{'SLICE':<22}{'SUPPORT':>8}{'% OF SET':>10}"
        f"{'ACCURACY':>10}{'RIGHT':>7}{'WRONG':>7}   SHARE OF VOLUME"
    )
    lines.append(header)
    lines.append(rule)

    lines.append(
        f"{OVERALL:<22}{r.overall.support:>8}{100.0:>9.1f}%"
        f"{percent(r.overall.accuracy):>10}{r.overall.correct:>7}{r.overall.wrong:>7}"
        f"   {_bar(1.0)}"
    )
    lines.append(rule)

    ordered = sorted(r.slices, key=lambda s: (-s.support, s.name))
    for s in ordered:
        flag = "  <-- watch this one" if s.accuracy < 0.80 and s.support else ""
        lines.append(
            f"{s.name:<22}{s.support:>8}{s.share * 100:>9.1f}%"
            f"{percent(s.accuracy):>10}{s.correct:>7}{s.wrong:>7}"
            f"   {_bar(s.share)}{flag}"
        )

    if ordered:
        lines.append(rule)
        biggest = ordered[0]
        if biggest.share >= 0.5:
            lines.append(
                f"{biggest.share * 100:.1f}% of this dataset is the "
                f"'{biggest.name}' slice, which scores "
                f"{percent(biggest.accuracy)}."
            )
            lines.append(
                "Overall accuracy is mostly a report on that one slice. "
                "Read the rows, not the headline."
            )
        weak = [s for s in ordered if s.support and s.accuracy < 0.80]
        if weak:
            names = ", ".join(f"{s.name} at {percent(s.accuracy)}" for s in weak)
            lines.append(f"Below 80 percent: {names}.")

    lines.append("")
    lines.append(r.cost.line())
    if r.cost.cost_basis:
        lines.append(f"cost basis: {r.cost.cost_basis}")

    task_errors = r.errors()
    if task_errors:
        lines.append(
            f"{len(task_errors)} cases raised an exception and were counted wrong. "
            f"First one: {task_errors[0].case_id} {task_errors[0].error}"
        )

    if detail:
        lines.append("")
        lines.append("PER CLASS")
        lines.append(rule)
        lines.append(
            f"{'LABEL':<24}{'SUPPORT':>8}{'PRECISION':>11}"
            f"{'RECALL':>9}{'F1':>8}"
        )
        for label, m in sorted(
            r.overall.per_class.items(), key=lambda kv: -kv[1].support
        ):
            lines.append(
                f"{label:<24}{m.support:>8}{m.precision:>11.3f}"
                f"{m.recall:>9.3f}{m.f1:>8.3f}"
            )
        macro = r.overall.macro
        weighted = r.overall.weighted
        lines.append(rule)
        lines.append(
            f"{'macro average':<24}{'':>8}{macro.precision:>11.3f}"
            f"{macro.recall:>9.3f}{macro.f1:>8.3f}"
        )
        lines.append(
            f"{'weighted average':<24}{'':>8}{weighted.precision:>11.3f}"
            f"{weighted.recall:>9.3f}{weighted.f1:>8.3f}"
        )
        lines.append("")
        lines.append("Macro treats every class the same. Weighted follows volume.")
        lines.append("The gap between those two lines is the same lesson again.")

        top = r.overall.confusion.top_confusions(6)
        if top:
            lines.append("")
            lines.append("MOST COMMON MISTAKES")
            lines.append(rule)
            for expected, predicted, count in top:
                lines.append(f"{count:>5}  {expected}  ->  {predicted}")

        fails = r.failures()
        if fails:
            lines.append("")
            lines.append(f"FAILED CASES (showing {min(max_failures, len(fails))} of {len(fails)})")
            lines.append(rule)
            for cr in fails[:max_failures]:
                who = cr.case.labeled_by or "unlabeled"
                conf = cr.case.confidence or "n/a"
                lines.append(
                    f"{cr.case_id}  expected {cr.expected_label}  "
                    f"got {cr.predicted_label}"
                )
                lines.append(f"        labeled by {who} (confidence {conf})")
                snippet = _input_snippet(cr.case)
                if snippet:
                    lines.append(f"        input: {snippet}")

    lines.append("")
    return "\n".join(lines)


def _input_snippet(case: Case, limit: int = 70) -> str:
    for key in ("description", "text", "question", "prompt"):
        if key in case.input:
            value = str(case.input[key]).replace("\n", " ")
            return value[:limit] + ("..." if len(value) > limit else "")
    return ""


def build_result(
    run: RunInfo,
    provenance: Provenance,
    case_results: Sequence[CaseResult],
    slice_members: dict[str, list[int]],
    slice_order: Sequence[str],
    cost: CostSummary,
    slice_descriptions: dict[str, str] | None = None,
) -> Result:
    """Assemble a Result from raw case outcomes. Called by the Runner."""
    outcomes = [
        (cr.matched, cr.score, cr.expected_label, cr.predicted_label, cr.errored)
        for cr in case_results
    ]
    total = len(case_results)
    overall = build_slice_metrics(OVERALL, outcomes, total, "every case in the set")

    descriptions = slice_descriptions or {}
    slice_metrics: list[SliceMetrics] = []
    for name in slice_order:
        idx = slice_members.get(name, [])
        slice_metrics.append(
            build_slice_metrics(
                name,
                [outcomes[i] for i in idx],
                total,
                descriptions.get(name, ""),
            )
        )

    result = Result(
        run=run,
        provenance=provenance,
        case_results=case_results,
        overall=overall,
        slices=slice_metrics,
        cost=cost,
        slice_descriptions=descriptions,
    )
    result._slice_index = dict(slice_members)
    return result
