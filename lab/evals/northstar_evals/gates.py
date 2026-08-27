"""The CI gate.

A gate is a set of rules a run has to pass before a change can merge. Without
one, "the eval looked fine when I ran it" is your release process.

Two kinds of rule, and you want both:

    floors      absolute minimums. loan_proceeds must be at least 0.65.
                These stop slow decay that a relative check would allow.
    baselines   nothing may drop more than N points against a saved run.
                These catch a change that quietly trades one slice for another.

    from northstar_evals import Gate

    gate = Gate(
        min_overall=0.94,
        min_slices={"loan_proceeds": 0.65, "poor_ocr": 0.58},
        max_regression=0.01,
        per_slice_regression={"loan_proceeds": 0.0},
        baseline="baselines/txn-v3-stub.json",
    )
    report = gate.check(result)
    report.raise_if_failed()

Set the floors below where you are today, not at your best ever run. A gate
that fires on normal noise gets turned off in a week.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .metrics import percent
from .result import BaselineResult, RegressionError, Result


@dataclass
class GateFinding:
    """One rule that fired."""

    rule: str
    target: str
    message: str
    severity: str = "fail"  # "fail" or "warn"
    observed: float | None = None
    threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "target": self.target,
            "message": self.message,
            "severity": self.severity,
            "observed": None if self.observed is None else round(self.observed, 6),
            "threshold": None if self.threshold is None else round(self.threshold, 6),
        }


@dataclass
class GateReport:
    """What the gate decided, and why."""

    suite: str
    passed: bool
    findings: list[GateFinding] = field(default_factory=list)
    checks_run: int = 0
    baseline_path: str | None = None

    @property
    def failures(self) -> list[GateFinding]:
        return [f for f in self.findings if f.severity == "fail"]

    @property
    def warnings(self) -> list[GateFinding]:
        return [f for f in self.findings if f.severity == "warn"]

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "passed": self.passed,
            "checksRun": self.checks_run,
            "baseline": self.baseline_path,
            "findings": [f.to_dict() for f in self.findings],
        }

    def raise_if_failed(self) -> "GateReport":
        if not self.passed:
            raise RegressionError(self.render())
        return self

    def render(self, width: int = 92) -> str:
        rule = "-" * width
        status = "PASS" if self.passed else "FAIL"
        lines = ["", f"EVAL GATE  {self.suite}  [{status}]", rule]
        lines.append(f"checks run: {self.checks_run}")
        if self.baseline_path:
            lines.append(f"baseline:   {self.baseline_path}")
        lines.append("")
        if not self.findings:
            lines.append("every check passed")
        for f in self.failures:
            lines.append(f"FAIL  {f.target:<20} {f.message}")
        for f in self.warnings:
            lines.append(f"warn  {f.target:<20} {f.message}")
        lines.append("")
        return "\n".join(lines)

    def report(self, stream: Any = None) -> str:
        import sys

        text = self.render()
        print(text, file=stream or sys.stdout)
        return text


@dataclass
class Gate:
    """Rules a run has to pass.

    Every threshold is a fraction from 0.0 to 1.0, not a percentage.
    """

    min_overall: float | None = None
    min_slices: Mapping[str, float] = field(default_factory=dict)
    max_regression: float | None = 0.01
    per_slice_regression: Mapping[str, float] = field(default_factory=dict)
    baseline: str | os.PathLike[str] | BaselineResult | None = None
    required_slices: Sequence[str] = ()
    min_support: Mapping[str, int] = field(default_factory=dict)
    max_task_errors: int = 0
    max_cost_usd: float | None = None
    max_p95_ms: float | None = None
    warn_only: bool = False

    def check(self, result: Result) -> GateReport:
        findings: list[GateFinding] = []
        checks = 0
        severity = "warn" if self.warn_only else "fail"
        baseline_path: str | None = None

        # Slices the report must contain at all. A renamed slice should be a
        # loud failure, not a silently skipped check.
        for name in self.required_slices:
            checks += 1
            if result.slice(name) is None:
                findings.append(
                    GateFinding(
                        rule="required_slice",
                        target=name,
                        message=f"slice '{name}' is missing from this run",
                        severity=severity,
                    )
                )

        # A slice that shrank below a useful size gives a meaningless score.
        for name, floor in self.min_support.items():
            checks += 1
            s = result.slice(name)
            support = s.support if s else 0
            if support < floor:
                findings.append(
                    GateFinding(
                        rule="min_support",
                        target=name,
                        message=(
                            f"only {support} cases, which is under the "
                            f"minimum of {floor}. The accuracy on it is noise."
                        ),
                        severity=severity,
                        observed=float(support),
                        threshold=float(floor),
                    )
                )

        if self.min_overall is not None:
            checks += 1
            if result.accuracy < self.min_overall - 1e-12:
                findings.append(
                    GateFinding(
                        rule="min_overall",
                        target="OVERALL",
                        message=(
                            f"{percent(result.accuracy)} is below the floor of "
                            f"{percent(self.min_overall)}"
                        ),
                        severity=severity,
                        observed=result.accuracy,
                        threshold=self.min_overall,
                    )
                )

        for name, floor in self.min_slices.items():
            checks += 1
            s = result.slice(name)
            if s is None:
                findings.append(
                    GateFinding(
                        rule="min_slice",
                        target=name,
                        message=f"slice '{name}' has a floor but is not in this run",
                        severity=severity,
                    )
                )
                continue
            if s.accuracy < floor - 1e-12:
                findings.append(
                    GateFinding(
                        rule="min_slice",
                        target=name,
                        message=(
                            f"{percent(s.accuracy)} on {s.support} cases is below "
                            f"the floor of {percent(floor)}"
                        ),
                        severity=severity,
                        observed=s.accuracy,
                        threshold=floor,
                    )
                )

        if self.max_task_errors is not None:
            checks += 1
            n_errors = len(result.errors())
            if n_errors > self.max_task_errors:
                findings.append(
                    GateFinding(
                        rule="max_task_errors",
                        target="task",
                        message=(
                            f"{n_errors} cases raised an exception, "
                            f"limit is {self.max_task_errors}"
                        ),
                        severity=severity,
                        observed=float(n_errors),
                        threshold=float(self.max_task_errors),
                    )
                )

        if self.max_cost_usd is not None:
            checks += 1
            if result.cost.total_usd > self.max_cost_usd + 1e-12:
                findings.append(
                    GateFinding(
                        rule="max_cost",
                        target="cost",
                        message=(
                            f"the run cost ${result.cost.total_usd:.4f}, "
                            f"budget is ${self.max_cost_usd:.4f}"
                        ),
                        severity=severity,
                        observed=result.cost.total_usd,
                        threshold=self.max_cost_usd,
                    )
                )

        if self.max_p95_ms is not None:
            checks += 1
            if result.cost.p95_ms > self.max_p95_ms:
                findings.append(
                    GateFinding(
                        rule="max_p95_latency",
                        target="latency",
                        message=(
                            f"p95 latency {result.cost.p95_ms:.0f} ms is over the "
                            f"limit of {self.max_p95_ms:.0f} ms"
                        ),
                        severity=severity,
                        observed=result.cost.p95_ms,
                        threshold=self.max_p95_ms,
                    )
                )

        if self.baseline is not None and self.max_regression is not None:
            base = (
                self.baseline
                if isinstance(self.baseline, BaselineResult)
                else BaselineResult.load(self.baseline)
            )
            baseline_path = base.source
            checks += 1
            try:
                result.assert_no_regression(
                    baseline=base,
                    tolerance=self.max_regression,
                    per_slice=dict(self.per_slice_regression),
                    require_all_slices=False,
                )
            except RegressionError as exc:
                for line in str(exc).splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- "):
                        findings.append(
                            GateFinding(
                                rule="no_regression",
                                target=_target_from(stripped),
                                message=stripped[2:],
                                severity=severity,
                            )
                        )

        passed = not any(f.severity == "fail" for f in findings)
        return GateReport(
            suite=result.run.suite,
            passed=passed,
            findings=findings,
            checks_run=checks,
            baseline_path=baseline_path,
        )

    def assert_pass(self, result: Result) -> GateReport:
        """Run the gate and raise if it failed. Use this inside a pytest test."""
        return self.check(result).raise_if_failed()

    def to_dict(self) -> dict[str, Any]:
        return {
            "minOverall": self.min_overall,
            "minSlices": dict(self.min_slices),
            "maxRegression": self.max_regression,
            "perSliceRegression": dict(self.per_slice_regression),
            "baseline": str(self.baseline) if self.baseline is not None else None,
            "requiredSlices": list(self.required_slices),
            "minSupport": dict(self.min_support),
            "maxTaskErrors": self.max_task_errors,
            "maxCostUsd": self.max_cost_usd,
            "maxP95Ms": self.max_p95_ms,
            "warnOnly": self.warn_only,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Gate":
        return cls(
            min_overall=raw.get("minOverall"),
            min_slices=raw.get("minSlices") or {},
            max_regression=raw.get("maxRegression", 0.01),
            per_slice_regression=raw.get("perSliceRegression") or {},
            baseline=raw.get("baseline"),
            required_slices=raw.get("requiredSlices") or (),
            min_support=raw.get("minSupport") or {},
            max_task_errors=int(raw.get("maxTaskErrors", 0)),
            max_cost_usd=raw.get("maxCostUsd"),
            max_p95_ms=raw.get("maxP95Ms"),
            warn_only=bool(raw.get("warnOnly", False)),
        )


def _target_from(line: str) -> str:
    if "slice '" in line:
        return line.split("slice '", 1)[1].split("'", 1)[0]
    if line.startswith("- overall"):
        return "OVERALL"
    return "run"
