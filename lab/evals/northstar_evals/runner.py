"""The Runner: point a task at a dataset, get a Result.

    from northstar_evals import Dataset, Runner, Slice

    ds = Dataset.load("data/golden/txn-classification-v3.jsonl")

    result = Runner(
        task=classify_transactions,
        dataset=ds,
        slices=[
            Slice("loan_proceeds", lambda c: c.tags.get("kind") == "loan"),
        ],
    ).run()

Your task is a plain function. It gets a Case and returns an answer. The
answer can be:

    a dict          {"classification": "LOAN_PROCEEDS"}
    a bare value    "LOAN_PROCEEDS", wrapped into the expected field for you
    a Prediction    when you want to report tokens, cost, and latency

If the task raises, the Runner records the exception, counts the case wrong,
and keeps going. One bad case should not cost you a 400 case run.
"""

from __future__ import annotations

import inspect
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from .case import Case
from .cost import CostSummary, Usage
from .dataset import Dataset
from .matchers import Matcher, auto, by_field
from .result import CaseResult, Result, RunInfo, build_result
from .slicing import Slice, assign


@dataclass
class Prediction:
    """An answer plus what it cost to get it.

    Return one of these from your task when you know the token counts. The
    Runner will use your latency instead of wall clock, which matters when
    you run cases in parallel.
    """

    output: Any
    cost_usd: float = 0.0
    latency_ms: float | None = None
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_basis: str = ""
    prompt_version: str | None = None
    raw: Any = None


Task = Callable[..., Any]


class Runner:
    """Runs a task over a dataset and scores the answers."""

    def __init__(
        self,
        task: Task,
        dataset: Dataset,
        slices: Sequence[Slice] = (),
        matcher: Matcher | Mapping[str, Matcher] | None = None,
        label_field: str | None = None,
        name: str | None = None,
        provider: str = "custom",
        model: str | None = None,
        prompt_version: str | None = None,
        max_workers: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not callable(task):
            raise TypeError("task has to be callable")
        self.task = task
        self.dataset = dataset
        self.slices = list(slices)
        self.label_field = label_field or _infer_label_field(dataset)
        self.matcher = _resolve_matcher(matcher)
        self.name = name or dataset.name
        self.provider = provider
        self.model = model
        self.prompt_version = prompt_version
        self.max_workers = max(1, int(max_workers))
        self.metadata = metadata or {}
        self._pass_case = _task_wants_case(task)

    # ---------------------------------------------------------------- public

    def run(self, limit: int | None = None, progress: bool = False) -> Result:
        """Run every case and score it. Returns a Result."""
        cases = self.dataset.cases
        if limit is not None:
            cases = cases[:limit]
        if not cases:
            raise ValueError("nothing to run, the dataset is empty")

        started = time.perf_counter()
        run_info = RunInfo.now(
            suite=self.name,
            provider=self.provider,
            model=self.model,
            prompt_version=self.prompt_version,
            matcher=getattr(self.matcher, "__name__", "custom"),
            label_field=self.label_field,
            metadata=self.metadata,
        )

        if self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                case_results = list(pool.map(self._run_one, cases))
        else:
            case_results = []
            for i, case in enumerate(cases, start=1):
                case_results.append(self._run_one(case))
                if progress and (i % 25 == 0 or i == len(cases)):
                    print(f"  {i}/{len(cases)} cases", flush=True)

        duration = time.perf_counter() - started
        run_info.duration_s = duration

        if self.model is None:
            models = {cr.usage.model for cr in case_results if cr.usage.model}
            if len(models) == 1:
                run_info.model = models.pop()

        assignment = assign(cases, self.slices)
        cost = CostSummary.from_usages(
            (cr.usage for cr in case_results), wall_clock_s=duration
        )

        return build_result(
            run=run_info,
            provenance=self.dataset.provenance,
            case_results=case_results,
            slice_members=assignment.members,
            slice_order=assignment.order,
            cost=cost,
            slice_descriptions={s.name: s.description for s in self.slices},
        )

    # --------------------------------------------------------------- internal

    def _run_one(self, case: Case) -> CaseResult:
        expected_label = _label_of(case.expected, self.label_field)
        started = time.perf_counter()
        try:
            raw = self.task(case) if self._pass_case else self.task(case.input)
        except Exception as exc:  # noqa: BLE001 - one bad case must not stop the run
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return CaseResult(
                case=case,
                predicted=None,
                matched=False,
                score=0.0,
                detail=f"task raised {type(exc).__name__}: {exc}",
                usage=Usage(latency_ms=elapsed_ms, model=self.model),
                error=f"{type(exc).__name__}: {exc}",
                expected_label=expected_label,
                predicted_label="<error>",
            )
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        if isinstance(raw, Prediction):
            output = raw.output
            usage = Usage(
                prompt_tokens=raw.prompt_tokens,
                completion_tokens=raw.completion_tokens,
                cost_usd=raw.cost_usd,
                latency_ms=raw.latency_ms if raw.latency_ms is not None else elapsed_ms,
                model=raw.model or self.model,
                cost_basis=raw.cost_basis,
            )
        else:
            output = raw
            usage = Usage(latency_ms=elapsed_ms, model=self.model)

        predicted = _as_answer(output, case.expected, self.label_field)
        match = self.matcher(case.expected, predicted)

        return CaseResult(
            case=case,
            predicted=predicted,
            matched=match.matched,
            score=match.score,
            detail=match.detail,
            usage=usage,
            expected_label=expected_label,
            predicted_label=_label_of(predicted, self.label_field),
        )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _resolve_matcher(matcher: Matcher | Mapping[str, Matcher] | None) -> Matcher:
    if matcher is None:
        return by_field({}, default=auto())
    if isinstance(matcher, Mapping):
        return by_field(matcher, default=auto())
    if callable(matcher):
        return matcher
    raise TypeError("matcher has to be a callable or a dict of field matchers")


def _infer_label_field(dataset: Dataset) -> str | None:
    """Pick the field to score per class metrics on.

    If every case has exactly one expected field, that is the one. Otherwise
    the caller has to say, and per class metrics fall back to the whole
    expected object.
    """
    fields: set[tuple[str, ...]] = set()
    for c in dataset:
        fields.add(tuple(sorted(c.expected)))
        if len(fields) > 1:
            break
    if len(fields) == 1:
        only = next(iter(fields))
        if len(only) == 1:
            return only[0]
    return None


def _label_of(answer: Any, label_field: str | None) -> Any:
    if isinstance(answer, Mapping):
        if label_field and label_field in answer:
            return answer[label_field]
        if len(answer) == 1:
            return next(iter(answer.values()))
        return {k: answer[k] for k in sorted(answer)}
    return answer


def _as_answer(
    output: Any,
    expected: Mapping[str, Any],
    label_field: str | None,
) -> Any:
    """Let a task return a bare value when the answer has one field."""
    if isinstance(output, Mapping):
        return output
    key = label_field
    if key is None and len(expected) == 1:
        key = next(iter(expected))
    if key is not None:
        return {key: output}
    return output


def _task_wants_case(task: Task) -> bool:
    """Decide whether to hand the task a Case or just `case.input`.

    Default is the Case, because tags and provenance are usually useful. A
    task whose only parameter is annotated as a dict or named `input` or
    `payload` gets `case.input` instead.
    """
    try:
        sig = inspect.signature(task)
    except (TypeError, ValueError):
        return True
    params = [
        p
        for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    if len(params) != 1:
        return True
    p = params[0]
    if p.name in {"input", "payload", "inputs", "data"}:
        return False
    annotation = p.annotation
    if annotation is inspect.Parameter.empty:
        return True
    if annotation in (dict, Mapping):
        return False
    text = str(annotation)
    if "Case" in text:
        return True
    if "dict" in text or "Mapping" in text:
        return False
    return True
