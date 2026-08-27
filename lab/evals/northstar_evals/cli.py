"""Command line entry point.

    python -m northstar_evals run --suite txn-classification
    python -m northstar_evals run --suite txn-classification --provider ollama
    python -m northstar_evals compare --suite txn-classification --a stub --b ollama
    python -m northstar_evals gate --suite smoke
    python -m northstar_evals labels --suite txn-classification
    python -m northstar_evals validate --suite txn-classification
    python -m northstar_evals suites

Exit codes: 0 means everything passed, 1 means a gate failed or a regression
was found, 2 means the command could not run at all. CI reads those.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from . import labeling
from .compare import compare, compare_many
from .dataset import DatasetError
from .gates import Gate
from .providers import ProviderError, get_provider
from .result import RegressionError, Result
from .runner import Runner
from .suites import Suite, all_suites, get as get_suite, resolve_data_path

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BROKEN = 2

JUNIOR_LABELERS = ("t.okafor", "j.pham", "junior.underwriter")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--suite", required=True, help="suite name, e.g. txn-classification")
    parser.add_argument(
        "--data-root",
        default=None,
        help="folder that holds data/golden. Defaults to a walk up from the cwd.",
    )
    parser.add_argument("--limit", type=int, default=None, help="run only the first N cases")


def _add_provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider",
        default="stub",
        help="stub, ollama, or hosted. Default is stub, which needs no network.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="model name for the provider, for example qwen3:8b",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m northstar_evals",
        description="Run and score evals for the Northstar lab.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a suite and print the slice table")
    _add_common(run)
    _add_provider_args(run)
    run.add_argument("--detail", action="store_true", help="add per class metrics and failures")
    run.add_argument("--json", dest="json_out", default=None, help="write the result to this file")
    run.add_argument("--save-baseline", default=None, help="write this run as a baseline")
    run.add_argument("--baseline", default=None, help="compare against this baseline file")
    run.add_argument("--gate", action="store_true", help="also run the suite's gate")
    run.add_argument("--workers", type=int, default=1, help="run cases in parallel")
    run.add_argument("--suspects", action="store_true", help="list cases that look mislabeled")

    cmp_p = sub.add_parser("compare", help="run two providers and diff them")
    _add_common(cmp_p)
    cmp_p.add_argument("--a", default="stub", help="first provider")
    cmp_p.add_argument("--b", default="ollama", help="second provider")
    cmp_p.add_argument("--a-model", default=None)
    cmp_p.add_argument("--b-model", default=None)
    cmp_p.add_argument("--json", dest="json_out", default=None)
    cmp_p.add_argument("--workers", type=int, default=1)

    gate_p = sub.add_parser("gate", help="run a suite and apply its CI gate")
    _add_common(gate_p)
    _add_provider_args(gate_p)
    gate_p.add_argument("--baseline", default=None, help="override the suite baseline")
    gate_p.add_argument("--min-overall", type=float, default=None)
    gate_p.add_argument("--workers", type=int, default=1)
    gate_p.add_argument("--warn-only", action="store_true", help="print but always exit 0")

    labels_p = sub.add_parser("labels", help="audit who labeled what, and agreement")
    _add_common(labels_p)
    labels_p.add_argument("--a", default=None, help="first annotator for kappa")
    labels_p.add_argument("--b", default=None, help="second annotator for kappa")
    labels_p.add_argument("--review", type=int, default=0, help="print N cases to re-check")

    val_p = sub.add_parser("validate", help="check a dataset without running a model")
    _add_common(val_p)
    val_p.add_argument("--stats", action="store_true", help="print the tag breakdown too")

    sub.add_parser("suites", help="list every registered suite")

    return parser


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def _run_suite(
    suite: Suite,
    provider_name: str,
    model: str | None,
    data_root: str | None,
    limit: int | None,
    workers: int,
) -> Result:
    dataset = suite.load(data_root)
    provider = get_provider(provider_name, model=model)
    task = provider.task_for(suite.name)
    runner = Runner(
        task=task,
        dataset=dataset,
        slices=list(suite.slices),
        matcher=dict(suite.matchers),
        label_field=suite.label_field,
        name=suite.name,
        provider=getattr(provider, "name", provider_name),
        model=getattr(provider, "model", model),
        prompt_version=getattr(provider, "prompt_version", None),
        max_workers=workers,
    )
    return runner.run(limit=limit)


def cmd_run(args: argparse.Namespace) -> int:
    suite = get_suite(args.suite)
    result = _run_suite(
        suite, args.provider, args.model, args.data_root, args.limit, args.workers
    )
    result.report(detail=args.detail)

    if args.suspects:
        suspects = labeling.suspect_labels(result, junior_labelers=JUNIOR_LABELERS)
        print("\nCASES THAT LOOK MISLABELED")
        print("-" * 92)
        if not suspects:
            print("none flagged")
        for s in suspects[:15]:
            print(f"{s.case_id:<12} expected {s.expected}, model said {s.predicted}")
            print(f"{'':<12} {'; '.join(s.reasons)}")
            if s.snippet:
                print(f"{'':<12} input: {s.snippet}")
        print(
            "\nCheck the label before you change the prompt. "
            "Roughly 2 percent of this set is mislabeled."
        )

    if args.json_out:
        path = result.save(args.json_out)
        print(f"wrote {path}")
    if args.save_baseline:
        path = result.save(args.save_baseline, include_cases=False)
        print(f"wrote baseline {path}")

    exit_code = EXIT_OK
    baseline = args.baseline or (suite.baseline if args.gate else None)
    if baseline and not args.save_baseline:
        try:
            result.assert_no_regression(_resolve_baseline(baseline, args.data_root))
            print("no regression against the baseline")
        except RegressionError as exc:
            print(f"\nREGRESSION\n{exc}")
            exit_code = EXIT_FAILED
        except FileNotFoundError as exc:
            print(f"\nskipping the baseline check: {exc}")

    if args.gate and suite.gate is not None:
        gate = suite.gate
        report = gate.check(result)
        report.report()
        exit_code = exit_code or report.exit_code
    return exit_code


def cmd_compare(args: argparse.Namespace) -> int:
    suite = get_suite(args.suite)
    result_a = _run_suite(
        suite, args.a, args.a_model, args.data_root, args.limit, args.workers
    )
    result_b = _run_suite(
        suite, args.b, args.b_model, args.data_root, args.limit, args.workers
    )
    comparison = compare(result_a, result_b)
    comparison.report()
    print(compare_many({comparison.name_a: result_a, comparison.name_b: result_b}))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(comparison.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"wrote {args.json_out}")
    return EXIT_OK


def cmd_gate(args: argparse.Namespace) -> int:
    suite = get_suite(args.suite)
    if suite.gate is None:
        print(f"suite '{suite.name}' has no gate defined")
        return EXIT_BROKEN
    result = _run_suite(
        suite, args.provider, args.model, args.data_root, args.limit, args.workers
    )
    result.report()

    gate = Gate.from_dict(suite.gate.to_dict())
    if args.baseline:
        gate.baseline = args.baseline
    if gate.baseline:
        try:
            gate.baseline = str(_resolve_baseline(str(gate.baseline), args.data_root))
        except FileNotFoundError as exc:
            print(f"skipping the baseline part of the gate: {exc}")
            gate.baseline = None
    if args.min_overall is not None:
        gate.min_overall = args.min_overall
    gate.warn_only = args.warn_only

    report = gate.check(result)
    report.report()
    return EXIT_OK if args.warn_only else report.exit_code


def cmd_labels(args: argparse.Namespace) -> int:
    suite = get_suite(args.suite)
    dataset = suite.load(args.data_root)
    audit = labeling.label_audit(dataset, label_field=suite.label_field)
    print(labeling.render_audit(audit))

    people = list(audit["annotators"])
    a = args.a
    b = args.b
    if a is None or b is None:
        overlapping = _pick_overlapping_pair(dataset, suite.label_field, people)
        a = a or (overlapping[0] if overlapping else None)
        b = b or (overlapping[1] if overlapping else None)
    if a and b and a != b:
        report = labeling.agreement(dataset, a, b, label_field=suite.label_field)
        print(report.report())
    else:
        print("not enough overlapping annotators to compute kappa\n")

    others = labeling.all_disagreements(dataset, label_field=suite.label_field)
    if others:
        print(f"{len(others)} annotator disagreements in this dataset")

    if args.review:
        print(f"\n{args.review} CASES TO RE-CHECK")
        print("-" * 92)
        for c in labeling.sample_for_review(dataset, n=args.review):
            desc = c.input.get("description") or c.input.get("question") or ""
            print(
                f"{c.case_id:<12} {str(desc)[:52]:<54} "
                f"label {c.expected_label(suite.label_field)}"
            )
            print(f"{'':<12} by {c.labeled_by} ({c.confidence})")
    return EXIT_OK


def _pick_overlapping_pair(
    dataset: Any, label_field: str | None, people: Sequence[str]
) -> tuple[str, str] | None:
    best: tuple[str, str] | None = None
    best_overlap = 0
    for i in range(len(people)):
        for j in range(i + 1, len(people)):
            a, b = people[i], people[j]
            n = sum(
                1
                for c in dataset
                if a in labeling._annotator_labels(c, label_field)
                and b in labeling._annotator_labels(c, label_field)
            )
            if n > best_overlap:
                best_overlap, best = n, (a, b)
    return best


def cmd_validate(args: argparse.Namespace) -> int:
    suite = get_suite(args.suite)
    try:
        dataset = suite.load(args.data_root)
    except DatasetError as exc:
        print(f"FAILED to load: {exc}")
        return EXIT_FAILED
    report = dataset.validate(
        required_tags=suite.required_tags,
        allowed_labels=suite.allowed_labels,
        label_field=suite.label_field,
    )
    print(f"\n{dataset!r}")
    print(report.report())
    if args.stats:
        print(json.dumps(dataset.stats(), indent=2))
    from .slicing import coverage

    cov = coverage(dataset.cases, list(suite.slices))
    print(
        f"\nslice coverage: {cov['covered']}/{cov['total']} cases "
        f"({cov['coveragePct']}%) land in at least one slice"
    )
    if cov["emptySlices"]:
        print(f"empty slices: {', '.join(cov['emptySlices'])}")
    return EXIT_OK if report.ok else EXIT_FAILED


def cmd_suites(_args: argparse.Namespace) -> int:
    print("")
    print(f"{'SUITE':<22}{'DATASET':<48}DESCRIPTION")
    print("-" * 110)
    for name, suite in sorted(all_suites().items()):
        print(f"{name:<22}{suite.dataset_path:<48}{suite.description}")
    print("")
    return EXIT_OK


def _resolve_baseline(path: str, data_root: str | None) -> Path:
    p = Path(path)
    if p.exists():
        return p
    here = Path(__file__).resolve().parent.parent
    candidate = here / path
    if candidate.exists():
        return candidate
    candidate = here / "baselines" / Path(path).name
    if candidate.exists():
        return candidate
    try:
        return resolve_data_path(path, data_root)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"no baseline file at {path}") from exc


COMMANDS = {
    "run": cmd_run,
    "compare": cmd_compare,
    "gate": cmd_gate,
    "labels": cmd_labels,
    "validate": cmd_validate,
    "suites": cmd_suites,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS[args.command]
    try:
        return handler(args)
    except (KeyError, ProviderError, DatasetError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BROKEN


if __name__ == "__main__":
    raise SystemExit(main())
