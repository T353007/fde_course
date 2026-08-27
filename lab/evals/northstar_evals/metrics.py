"""The metric math.

Everything here works on a list of (expected, predicted) pairs. Nothing here
knows about datasets, runners, or slices. That is on purpose. It makes the
math testable by hand, which is the only way anyone believes a metric.

Definitions used, for one class C:

    true positive   predicted C, and C was right
    false positive  predicted C, but something else was right
    false negative  did not predict C, but C was right

    precision = TP / (TP + FP)      of the times it said C, how often was it C
    recall    = TP / (TP + FN)      of the real C cases, how many did it find
    f1        = 2 * P * R / (P + R)

Precision and recall answer different questions and one of them is usually
the one you care about. For loan proceeds, recall matters: a missed loan
deposit inflates revenue and moves an approval.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

Pair = tuple[Any, Any]


def accuracy(correct: int, total: int) -> float:
    """Share of cases that matched, from 0.0 to 1.0. Empty set scores 0.0."""
    if total <= 0:
        return 0.0
    return correct / total


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True)
class ClassMetrics:
    """Precision, recall, and F1 for one class, with the raw counts."""

    label: str
    support: int
    predicted: int
    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        return _safe_div(self.true_positives, self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        return _safe_div(self.true_positives, self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return _safe_div(2 * p * r, p + r)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "support": self.support,
            "predicted": self.predicted,
            "truePositives": self.true_positives,
            "falsePositives": self.false_positives,
            "falseNegatives": self.false_negatives,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
        }


@dataclass
class ConfusionMatrix:
    """Counts of expected label against predicted label.

    `counts[(expected, predicted)]` is how many times that swap happened. The
    off diagonal cells are the interesting part. In the Northstar transaction
    set, `(LOAN_PROCEEDS, OPERATING_REVENUE)` is the cell that costs money.
    """

    counts: Counter = field(default_factory=Counter)
    labels: list[str] = field(default_factory=list)

    def add(self, expected: Any, predicted: Any) -> None:
        e, p = _norm_label(expected), _norm_label(predicted)
        self.counts[(e, p)] += 1
        for lbl in (e, p):
            if lbl not in self.labels:
                self.labels.append(lbl)

    def get(self, expected: str, predicted: str) -> int:
        return self.counts.get((expected, predicted), 0)

    def support(self, label: str) -> int:
        return sum(n for (e, _p), n in self.counts.items() if e == label)

    def predicted_count(self, label: str) -> int:
        return sum(n for (_e, p), n in self.counts.items() if p == label)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def sorted_labels(self) -> list[str]:
        return sorted(self.labels, key=lambda l: (-self.support(l), l))

    def top_confusions(self, n: int = 5) -> list[tuple[str, str, int]]:
        """The most common wrong swaps, biggest first."""
        wrong = [(e, p, c) for (e, p), c in self.counts.items() if e != p]
        wrong.sort(key=lambda row: (-row[2], row[0], row[1]))
        return wrong[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "labels": self.sorted_labels(),
            "cells": [
                {"expected": e, "predicted": p, "count": c}
                for (e, p), c in sorted(self.counts.items())
            ],
        }

    @classmethod
    def from_pairs(cls, pairs: Iterable[Pair]) -> "ConfusionMatrix":
        cm = cls()
        for expected, predicted in pairs:
            cm.add(expected, predicted)
        return cm

    def render(self, max_labels: int = 12) -> str:
        """A plain text grid. Rows are expected, columns are predicted."""
        labels = self.sorted_labels()[:max_labels]
        if not labels:
            return "(no data)"
        short = {l: _abbrev(l) for l in labels}
        width = max(len(l) for l in labels) + 2
        cell = max(6, max(len(short[l]) for l in labels) + 2)

        header = " " * width + "".join(short[l].rjust(cell) for l in labels)
        lines = [header, " " * width + "-" * (cell * len(labels))]
        for e in labels:
            row = e.ljust(width)
            for p in labels:
                n = self.get(e, p)
                row += (str(n) if n else ".").rjust(cell)
            lines.append(row)
        lines.append("")
        lines.append("rows are the correct label, columns are what the model said")
        return "\n".join(lines)


def _norm_label(value: Any) -> str:
    if value is None:
        return "<none>"
    if isinstance(value, (list, tuple, set, frozenset)):
        return ",".join(sorted(str(v) for v in value))
    if isinstance(value, Mapping):
        return ",".join(f"{k}={v}" for k, v in sorted(value.items()))
    return str(value)


def _abbrev(label: str) -> str:
    """Shorten LOAN_PROCEEDS to LOAN_P so the grid fits on a terminal."""
    if len(label) <= 6:
        return label
    parts = label.replace("-", "_").split("_")
    if len(parts) > 1:
        return (parts[0][:4] + "_" + parts[1][:1]).upper()
    return label[:6]


def class_metrics(cm: ConfusionMatrix, label: str) -> ClassMetrics:
    """Pull precision and recall for one class out of a confusion matrix."""
    tp = cm.get(label, label)
    support = cm.support(label)
    predicted = cm.predicted_count(label)
    return ClassMetrics(
        label=label,
        support=support,
        predicted=predicted,
        true_positives=tp,
        false_positives=predicted - tp,
        false_negatives=support - tp,
    )


def confusion_matrix(pairs: Iterable[Pair]) -> ConfusionMatrix:
    """Build a confusion matrix from (expected, predicted) pairs."""
    return ConfusionMatrix.from_pairs(pairs)


def precision_recall_f1(pairs: Iterable[Pair]) -> dict[str, ClassMetrics]:
    """Per class metrics for every label that appears on either side."""
    cm = ConfusionMatrix.from_pairs(pairs)
    return {label: class_metrics(cm, label) for label in cm.sorted_labels()}


@dataclass(frozen=True)
class AverageMetrics:
    """Precision, recall, and F1 rolled up across classes."""

    kind: str
    precision: float
    recall: float
    f1: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
        }


def macro_average(per_class: Mapping[str, ClassMetrics]) -> AverageMetrics:
    """Plain average across classes. Every class counts the same.

    Use this when a rare class matters as much as a common one, which is the
    whole reason the Northstar slice table exists.
    """
    if not per_class:
        return AverageMetrics("macro", 0.0, 0.0, 0.0)
    n = len(per_class)
    return AverageMetrics(
        "macro",
        sum(m.precision for m in per_class.values()) / n,
        sum(m.recall for m in per_class.values()) / n,
        sum(m.f1 for m in per_class.values()) / n,
    )


def weighted_average(per_class: Mapping[str, ClassMetrics]) -> AverageMetrics:
    """Average across classes weighted by how common each one is.

    This tracks overall accuracy closely, which is exactly why it hides the
    problem in a set where 84 percent of cases are one easy class.
    """
    total = sum(m.support for m in per_class.values())
    if not total:
        return AverageMetrics("weighted", 0.0, 0.0, 0.0)
    return AverageMetrics(
        "weighted",
        sum(m.precision * m.support for m in per_class.values()) / total,
        sum(m.recall * m.support for m in per_class.values()) / total,
        sum(m.f1 * m.support for m in per_class.values()) / total,
    )


def micro_average(per_class: Mapping[str, ClassMetrics]) -> AverageMetrics:
    """Pool every true positive and false positive, then divide once.

    For single label classification this equals accuracy.
    """
    tp = sum(m.true_positives for m in per_class.values())
    fp = sum(m.false_positives for m in per_class.values())
    fn = sum(m.false_negatives for m in per_class.values())
    p = _safe_div(tp, tp + fp)
    r = _safe_div(tp, tp + fn)
    return AverageMetrics("micro", p, r, _safe_div(2 * p * r, p + r))


@dataclass
class SliceMetrics:
    """Everything scored for one slice, including the support count.

    `support` and `share` are printed next to accuracy on purpose. An accuracy
    number without a support count next to it has started more bad arguments
    than any other number in machine learning.
    """

    name: str
    support: int
    correct: int
    total_cases: int = 0
    errors: int = 0
    mean_score: float = 0.0
    per_class: dict[str, ClassMetrics] = field(default_factory=dict)
    confusion: ConfusionMatrix = field(default_factory=ConfusionMatrix)
    description: str = ""

    @property
    def wrong(self) -> int:
        return self.support - self.correct

    @property
    def accuracy(self) -> float:
        return accuracy(self.correct, self.support)

    @property
    def share(self) -> float:
        """This slice's size as a fraction of the whole dataset."""
        return _safe_div(self.support, self.total_cases)

    @property
    def macro(self) -> AverageMetrics:
        return macro_average(self.per_class)

    @property
    def weighted(self) -> AverageMetrics:
        return weighted_average(self.per_class)

    def to_dict(self, include_confusion: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "support": self.support,
            "correct": self.correct,
            "wrong": self.wrong,
            "accuracy": round(self.accuracy, 6),
            "share": round(self.share, 6),
            "meanScore": round(self.mean_score, 6),
            "errors": self.errors,
            "macro": self.macro.to_dict(),
            "weighted": self.weighted.to_dict(),
            "perClass": {k: v.to_dict() for k, v in self.per_class.items()},
        }
        if include_confusion:
            out["confusion"] = self.confusion.to_dict()
        if self.description:
            out["description"] = self.description
        return out


def build_slice_metrics(
    name: str,
    outcomes: Sequence[tuple[bool, float, Any, Any, bool]],
    total_cases: int,
    description: str = "",
) -> SliceMetrics:
    """Turn raw per case outcomes into one SliceMetrics.

    Each outcome is (matched, score, expected_label, predicted_label, errored).
    `errored` means the task itself blew up, which counts as wrong.
    """
    support = len(outcomes)
    correct = sum(1 for matched, *_ in outcomes if matched)
    error_count = sum(1 for *_rest, errored in outcomes if errored)
    mean_score = _safe_div(sum(score for _m, score, *_ in outcomes), support)
    cm = ConfusionMatrix()
    for _matched, _score, expected, predicted, _errored in outcomes:
        cm.add(expected, predicted)
    per_class = {label: class_metrics(cm, label) for label in cm.sorted_labels()}
    return SliceMetrics(
        name=name,
        support=support,
        correct=correct,
        total_cases=total_cases,
        errors=error_count,
        mean_score=mean_score,
        per_class=per_class,
        confusion=cm,
        description=description,
    )


def percent(value: float, places: int = 1) -> str:
    """Format 0.9607 as '96.1%'. One place is enough for a console table."""
    return f"{value * 100:.{places}f}%"
