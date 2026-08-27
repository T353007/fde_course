#!/usr/bin/env python3
"""Run the stub classifier on txn-classification-v3 and print the slice table.

Proves the golden set lands near the CANON numbers:

    overall 96%, loan_proceeds 68%, poor_ocr 61%,
    internal_transfer 73%, card_settlement 99% at ~84% volume.

    python lab/evals/scripts/simulate_classifier.py
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB / "evals"))

from northstar_evals import Runner, get_provider  # noqa: E402
from northstar_evals.suites import get as get_suite  # noqa: E402

# Tolerances around CANON section 4. Close enough to teach the lesson.
TARGETS = {
    "overall": (0.96, 0.01),
    "loan_proceeds": (0.68, 0.02),
    "poor_ocr": (0.61, 0.02),
    "internal_transfer": (0.73, 0.02),
    "card_settlement": (0.99, 0.015),
    "card_settlement_share": (0.84, 0.02),
}


def main() -> int:
    suite = get_suite("txn-classification")
    dataset = suite.load(LAB)
    provider = get_provider("stub")
    result = Runner(
        task=provider.task_for(suite.name),
        dataset=dataset,
        slices=list(suite.slices),
        matcher=dict(suite.matchers),
        label_field=suite.label_field,
        name=suite.name,
        provider=provider.name,
        model=getattr(provider, "model", None),
    ).run()

    result.report()

    checks = {
        "overall": result.accuracy,
        "loan_proceeds": result.slice_accuracy("loan_proceeds"),
        "poor_ocr": result.slice_accuracy("poor_ocr"),
        "internal_transfer": result.slice_accuracy("internal_transfer"),
        "card_settlement": result.slice_accuracy("card_settlement"),
        "card_settlement_share": result.slice("card_settlement").share,
    }

    print("\nCANON CHECK")
    print("-" * 72)
    failed = 0
    for name, value in checks.items():
        target, tol = TARGETS[name]
        ok = abs(value - target) <= tol
        mark = "ok" if ok else "FAIL"
        print(
            f"{mark:<4} {name:<24} got {value * 100:5.1f}%  "
            f"target {target * 100:5.1f}%  ±{tol * 100:.1f}"
        )
        if not ok:
            failed += 1

    if failed:
        print(f"\n{failed} check(s) missed the CANON window")
        return 1
    print("\nAll slice numbers sit inside the CANON window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
