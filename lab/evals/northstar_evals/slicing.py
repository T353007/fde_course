"""Slices: named subsets of a dataset that you score on their own.

Overall accuracy is an average weighted by how common each kind of case is.
If 84 percent of your cases are easy, overall accuracy is a report on the easy
cases wearing a hat. A slice is how you get the number that actually matters.

A case can belong to several slices at once. A poor scan of a loan deposit is
in `poor_ocr` and in `loan_proceeds`. Slices are not buckets and they do not
have to add up to the whole set.

    from northstar_evals import Slice

    Slice("loan_proceeds", lambda c: c.tags.get("kind") == "loan")
    Slice.from_tag("poor_ocr", "ocr_quality", "poor")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from .case import Case

Predicate = Callable[[Case], bool]


class SliceError(ValueError):
    """Raised when a slice is defined badly or its predicate blows up."""


@dataclass(frozen=True)
class Slice:
    """One named subset.

    `name` shows up in the report and in the baseline file, so treat it as an
    identifier. Renaming a slice breaks the comparison to old runs.
    """

    name: str
    predicate: Predicate
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise SliceError("a slice needs a name")
        if not callable(self.predicate):
            raise SliceError(f"slice '{self.name}': predicate is not callable")

    def matches(self, case: Case) -> bool:
        """Run the predicate. A predicate that raises is treated as no match.

        A tag lookup on a case that is missing the tag should not kill a run
        of 400 cases. It should show up as a smaller slice, which the support
        column makes obvious.
        """
        try:
            return bool(self.predicate(case))
        except Exception:  # noqa: BLE001 - a bad predicate must not stop the run
            return False

    # ------------------------------------------------------------- shortcuts

    @classmethod
    def from_tag(
        cls,
        name: str,
        tag: str,
        value: str | Iterable[str],
        description: str = "",
    ) -> "Slice":
        """Slice on one tag value, or on any of several values."""
        if isinstance(value, str):
            wanted = {value}
        else:
            wanted = set(value)

        def predicate(case: Case) -> bool:
            return case.tags.get(tag) in wanted

        return cls(
            name=name,
            predicate=predicate,
            description=description or f"{tag} in {sorted(wanted)}",
        )

    @classmethod
    def from_label(
        cls,
        name: str,
        label: str,
        field_name: str | None = None,
        description: str = "",
    ) -> "Slice":
        """Slice on the expected answer. Useful for per class recall."""

        def predicate(case: Case) -> bool:
            try:
                return str(case.expected_label(field_name)) == label
            except Exception:  # noqa: BLE001
                return False

        return cls(
            name=name,
            predicate=predicate,
            description=description or f"expected label is {label}",
        )

    @classmethod
    def everything(cls, name: str = "overall") -> "Slice":
        return cls(name=name, predicate=lambda _c: True, description="every case")

    def __and__(self, other: "Slice") -> "Slice":
        """Combine two slices. `poor_ocr & loan_proceeds` is a real question."""
        return Slice(
            name=f"{self.name}+{other.name}",
            predicate=lambda c: self.matches(c) and other.matches(c),
            description=f"{self.description} and {other.description}".strip(),
        )

    def __repr__(self) -> str:
        return f"Slice({self.name!r})"


@dataclass
class SliceAssignment:
    """Which case indexes landed in which slice."""

    members: dict[str, list[int]] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)

    def support(self, name: str) -> int:
        return len(self.members.get(name, ()))

    def empty_slices(self) -> list[str]:
        return [n for n in self.order if not self.members.get(n)]


def assign(cases: Sequence[Case], slices: Sequence[Slice]) -> SliceAssignment:
    """Work out which cases belong to which slices.

    Returns index lists rather than cases so the Runner can line results up
    with the same positions.
    """
    names = [s.name for s in slices]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise SliceError(f"two slices share a name: {', '.join(sorted(duplicates))}")

    members: dict[str, list[int]] = {s.name: [] for s in slices}
    for i, case in enumerate(cases):
        for s in slices:
            if s.matches(case):
                members[s.name].append(i)
    return SliceAssignment(members=members, order=names)


def coverage(cases: Sequence[Case], slices: Sequence[Slice]) -> dict[str, Any]:
    """How much of the dataset the slices cover, and what they miss.

    A case in no slice is a case nobody is watching. Print this when you add
    a new kind of input and want to know if your slices kept up.
    """
    assignment = assign(cases, slices)
    covered = set()
    for idx_list in assignment.members.values():
        covered.update(idx_list)
    uncovered = [cases[i].case_id for i in range(len(cases)) if i not in covered]
    total = len(cases) or 1
    return {
        "total": len(cases),
        "covered": len(covered),
        "coveragePct": round(100.0 * len(covered) / total, 2),
        "uncoveredCaseIds": uncovered[:50],
        "uncoveredCount": len(uncovered),
        "emptySlices": assignment.empty_slices(),
    }
