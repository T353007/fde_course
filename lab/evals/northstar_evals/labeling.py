"""Human labeling helpers.

Ground truth is a person's opinion written down. People disagree, get tired,
and label 200 transactions on a Friday afternoon. About 2 percent of the
labels in the Northstar transaction set are wrong, and that is a normal number
for a hand labeled set, not a scandal.

This module gives you three things:

    agreement       how often two people gave the same answer, corrected for
                    the agreement you would get by guessing (Cohen's kappa)
    disagreements   the actual cases where they differ, so a human can look
    suspects        cases the model got "wrong" that are probably bad labels

The last one is the useful one. When a model misses a case that a junior
labeled with low confidence, check the label before you change the prompt.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .case import Case
from .dataset import Dataset

# How to read kappa. These bands are the common Landis and Koch reading.
# They are a convention, not a law.
KAPPA_BANDS = (
    (0.81, "almost perfect"),
    (0.61, "substantial"),
    (0.41, "moderate"),
    (0.21, "fair"),
    (0.01, "slight"),
    (-1.0, "worse than guessing"),
)


def interpret_kappa(kappa: float) -> str:
    for floor, label in KAPPA_BANDS:
        if kappa >= floor:
            return label
    return "worse than guessing"


def cohens_kappa(labels_a: Sequence[Any], labels_b: Sequence[Any]) -> float:
    """Agreement between two annotators, corrected for chance.

    Plain agreement is misleading when one answer is very common. If 84
    percent of cases are card settlements, two people who always guess
    "settlement" agree 84 percent of the time and know nothing.

        kappa = (observed - expected) / (1 - expected)

    1.0 is perfect agreement. 0.0 is what you would get by chance. Below zero
    means they disagree more than random guessing would.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("both annotators have to label the same number of cases")
    n = len(labels_a)
    if n == 0:
        raise ValueError("no labels to compare")

    a = [str(x) for x in labels_a]
    b = [str(x) for x in labels_b]

    observed = sum(1 for x, y in zip(a, b) if x == y) / n

    count_a = Counter(a)
    count_b = Counter(b)
    expected = sum(
        (count_a[label] / n) * (count_b[label] / n)
        for label in set(count_a) | set(count_b)
    )

    if abs(1.0 - expected) < 1e-12:
        # Both annotators used one label for everything. Kappa is undefined,
        # so report perfect agreement if they match and none if they do not.
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


@dataclass
class Disagreement:
    """One case where two people gave different answers."""

    case_id: str
    annotator_a: str
    label_a: Any
    annotator_b: str
    label_b: Any
    confidence_a: str | None = None
    confidence_b: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "caseId": self.case_id,
            "a": {
                "annotator": self.annotator_a,
                "label": self.label_a,
                "confidence": self.confidence_a,
            },
            "b": {
                "annotator": self.annotator_b,
                "label": self.label_b,
                "confidence": self.confidence_b,
            },
            "note": self.note,
        }


@dataclass
class AgreementReport:
    """Kappa plus the cases that produced it."""

    annotator_a: str
    annotator_b: str
    overlap: int
    agreed: int
    kappa: float
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def raw_agreement(self) -> float:
        return self.agreed / self.overlap if self.overlap else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "annotatorA": self.annotator_a,
            "annotatorB": self.annotator_b,
            "overlap": self.overlap,
            "agreed": self.agreed,
            "rawAgreement": round(self.raw_agreement, 6),
            "kappa": round(self.kappa, 6),
            "reading": interpret_kappa(self.kappa),
            "disagreements": [d.to_dict() for d in self.disagreements],
        }

    def report(self) -> str:
        lines = [
            "",
            f"AGREEMENT  {self.annotator_a} vs {self.annotator_b}",
            "-" * 72,
            f"cases both labeled ....... {self.overlap}",
            f"they agreed on ........... {self.agreed}",
            f"raw agreement ............ {self.raw_agreement * 100:.1f}%",
            f"Cohen's kappa ............ {self.kappa:.3f} ({interpret_kappa(self.kappa)})",
            "",
        ]
        if self.disagreements:
            lines.append(f"THEY DISAGREED ON {len(self.disagreements)} CASES")
            lines.append("-" * 72)
            for d in self.disagreements[:20]:
                lines.append(
                    f"{d.case_id:<12} {d.annotator_a} said {d.label_a} "
                    f"({d.confidence_a or 'n/a'})"
                )
                lines.append(
                    f"{'':<12} {d.annotator_b} said {d.label_b} "
                    f"({d.confidence_b or 'n/a'})"
                )
                if d.note:
                    lines.append(f"{'':<12} note: {d.note}")
            if len(self.disagreements) > 20:
                lines.append(f"...and {len(self.disagreements) - 20} more")
        else:
            lines.append("no disagreements in the overlap")
        lines.append("")
        lines.append(
            "Raw agreement looks good on any set where one label is common. "
            "Kappa is the honest number."
        )
        lines.append("")
        return "\n".join(lines)


def _annotator_labels(case: Case, label_field: str | None) -> dict[str, Any]:
    """Every label on this case, keyed by who gave it.

    The primary label counts as an annotation from `labeledBy`.
    """
    labels: dict[str, Any] = {}
    if case.labeled_by:
        try:
            labels[case.labeled_by] = case.expected_label(label_field)
        except Exception:  # noqa: BLE001
            pass
    for a in case.annotations:
        labels[a.annotator] = a.label
    return labels


def _annotator_confidence(case: Case, annotator: str) -> str | None:
    if case.labeled_by == annotator:
        return case.confidence
    for a in case.annotations:
        if a.annotator == annotator:
            return a.confidence
    return None


def _annotator_note(case: Case, annotator: str) -> str | None:
    if case.labeled_by == annotator:
        return case.notes
    for a in case.annotations:
        if a.annotator == annotator:
            return a.note
    return None


def annotators(dataset: Dataset) -> Counter:
    """Who labeled how many cases, counting the extra annotations too."""
    counts: Counter = Counter()
    for c in dataset:
        for name in _annotator_labels(c, None):
            counts[name] += 1
    return counts


def agreement(
    dataset: Dataset,
    annotator_a: str,
    annotator_b: str,
    label_field: str | None = None,
) -> AgreementReport:
    """Compare two people on the cases they both labeled."""
    labels_a: list[Any] = []
    labels_b: list[Any] = []
    disagreements: list[Disagreement] = []

    for case in dataset:
        found = _annotator_labels(case, label_field)
        if annotator_a not in found or annotator_b not in found:
            continue
        la, lb = found[annotator_a], found[annotator_b]
        labels_a.append(la)
        labels_b.append(lb)
        if str(la) != str(lb):
            disagreements.append(
                Disagreement(
                    case_id=case.case_id,
                    annotator_a=annotator_a,
                    label_a=la,
                    annotator_b=annotator_b,
                    label_b=lb,
                    confidence_a=_annotator_confidence(case, annotator_a),
                    confidence_b=_annotator_confidence(case, annotator_b),
                    note=_annotator_note(case, annotator_a)
                    or _annotator_note(case, annotator_b),
                )
            )

    overlap = len(labels_a)
    if overlap == 0:
        return AgreementReport(annotator_a, annotator_b, 0, 0, 0.0, [])

    agreed = sum(1 for x, y in zip(labels_a, labels_b) if str(x) == str(y))
    return AgreementReport(
        annotator_a=annotator_a,
        annotator_b=annotator_b,
        overlap=overlap,
        agreed=agreed,
        kappa=cohens_kappa(labels_a, labels_b),
        disagreements=disagreements,
    )


def all_disagreements(
    dataset: Dataset,
    label_field: str | None = None,
) -> list[Disagreement]:
    """Every case where any two annotators differ. Start a label review here."""
    out: list[Disagreement] = []
    for case in dataset:
        found = _annotator_labels(case, label_field)
        names = sorted(found)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if str(found[a]) != str(found[b]):
                    out.append(
                        Disagreement(
                            case_id=case.case_id,
                            annotator_a=a,
                            label_a=found[a],
                            annotator_b=b,
                            label_b=found[b],
                            confidence_a=_annotator_confidence(case, a),
                            confidence_b=_annotator_confidence(case, b),
                            note=_annotator_note(case, a) or _annotator_note(case, b),
                        )
                    )
    return out


@dataclass
class SuspectLabel:
    """A failing case that looks more like a bad label than a bad model."""

    case_id: str
    expected: Any
    predicted: Any
    labeled_by: str | None
    confidence: str | None
    reasons: list[str] = field(default_factory=list)
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "caseId": self.case_id,
            "expected": self.expected,
            "predicted": self.predicted,
            "labeledBy": self.labeled_by,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "input": self.snippet,
        }


def suspect_labels(
    result: Any,
    junior_labelers: Iterable[str] = (),
    limit: int = 50,
) -> list[SuspectLabel]:
    """Rank failing cases by how likely the label is the thing that is wrong.

    A case gets flagged when the human who labeled it said "low confidence",
    when the labeler is on the junior list, or when another annotator on the
    same case disagreed with the recorded answer.

    This does not tell you the label is wrong. It tells you which twenty cases
    a senior underwriter should look at first.
    """
    juniors = {j.lower() for j in junior_labelers}
    suspects: list[SuspectLabel] = []

    for cr in result.case_results:
        if cr.matched or cr.errored:
            continue
        case = cr.case
        reasons: list[str] = []
        if case.is_low_confidence():
            reasons.append("labeled with low confidence")
        if case.labeled_by and case.labeled_by.lower() in juniors:
            reasons.append(f"labeled by {case.labeled_by}, who is on the junior list")
        other = [
            a
            for a in case.annotations
            if str(a.label) != str(cr.expected_label)
        ]
        if other:
            who = ", ".join(a.annotator for a in other)
            reasons.append(f"another annotator disagreed ({who})")
        agreeing = [a for a in case.annotations if str(a.label) == str(cr.predicted_label)]
        if agreeing:
            who = ", ".join(a.annotator for a in agreeing)
            reasons.append(f"{who} gave the same answer the model gave")
        if not reasons:
            continue
        snippet = ""
        for key in ("description", "text", "question"):
            if key in case.input:
                snippet = str(case.input[key])[:80]
                break
        suspects.append(
            SuspectLabel(
                case_id=case.case_id,
                expected=cr.expected_label,
                predicted=cr.predicted_label,
                labeled_by=case.labeled_by,
                confidence=case.confidence,
                reasons=reasons,
                snippet=snippet,
            )
        )

    suspects.sort(key=lambda s: (-len(s.reasons), s.case_id))
    return suspects[:limit]


def label_audit(dataset: Dataset, label_field: str | None = None) -> dict[str, Any]:
    """Who labeled what, and where the low confidence labels are sitting.

    Run this before you trust a number. If one person labeled 300 of 400
    cases at low confidence, your ceiling is their Friday afternoon.
    """
    by_labeler: dict[str, Counter] = defaultdict(Counter)
    low_by_labeler: Counter = Counter()
    label_counts: Counter = Counter()
    multi_annotated = 0

    for case in dataset:
        who = case.labeled_by or "<unlabeled>"
        by_labeler[who][case.confidence or "<none>"] += 1
        if case.is_low_confidence():
            low_by_labeler[who] += 1
        try:
            label_counts[str(case.expected_label(label_field))] += 1
        except Exception:  # noqa: BLE001
            label_counts["<multi-field>"] += 1
        if case.annotations:
            multi_annotated += 1

    total = len(dataset)
    low_total = sum(low_by_labeler.values())
    return {
        "cases": total,
        "labelers": {k: dict(v) for k, v in sorted(by_labeler.items())},
        "lowConfidence": {
            "count": low_total,
            "pct": round(100.0 * low_total / total, 2) if total else 0.0,
            "byLabeler": dict(low_by_labeler),
        },
        "labelCounts": dict(label_counts.most_common()),
        "multiAnnotatedCases": multi_annotated,
        "annotators": dict(annotators(dataset)),
    }


def render_audit(audit: dict[str, Any]) -> str:
    """Print a label audit as text."""
    lines = ["", "LABEL AUDIT", "-" * 72, f"cases: {audit['cases']}", ""]
    lines.append(f"{'LABELED BY':<28}{'CASES':>7}{'LOW CONF':>10}")
    for who, conf in audit["labelers"].items():
        n = sum(conf.values())
        low = conf.get("low", 0)
        lines.append(f"{who:<28}{n:>7}{low:>10}")
    lines.append("")
    low = audit["lowConfidence"]
    lines.append(f"low confidence labels: {low['count']} ({low['pct']}% of the set)")
    lines.append(f"cases with a second annotator: {audit['multiAnnotatedCases']}")
    lines.append("")
    lines.append(f"{'LABEL':<28}{'COUNT':>7}")
    for label, n in audit["labelCounts"].items():
        lines.append(f"{label:<28}{n:>7}")
    lines.append("")
    return "\n".join(lines)


def sample_for_review(
    dataset: Dataset,
    n: int = 20,
    seed: int = 0,
    prefer_low_confidence: bool = True,
) -> list[Case]:
    """Pick cases for a human to re-check. Repeatable for the same seed.

    Low confidence cases come first, then the rest at random. Twenty cases is
    about forty minutes of an underwriter's time, which is what you can
    actually ask for.
    """
    import random

    rng = random.Random(seed)
    cases = dataset.cases
    if prefer_low_confidence:
        low = [c for c in cases if c.is_low_confidence()]
        rest = [c for c in cases if not c.is_low_confidence()]
        rng.shuffle(low)
        rng.shuffle(rest)
        picked = (low + rest)[:n]
    else:
        picked = rng.sample(cases, min(n, len(cases)))
    return sorted(picked, key=lambda c: c.case_id)
