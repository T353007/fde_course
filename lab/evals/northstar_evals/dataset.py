"""Loading golden datasets, with provenance.

A golden dataset is a file of labeled cases. It is the thing you argue with
when someone says the model got worse. That only works if you can say exactly
which file, which version, and who labeled what. So loading a dataset also
records a checksum and a summary of who did the labeling.

    from northstar_evals import Dataset

    ds = Dataset.load("data/golden/txn-classification-v3.jsonl")
    print(ds.provenance.sha256[:12], len(ds))
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Sequence

from .case import Case, CaseError


class DatasetError(ValueError):
    """Raised when a dataset file cannot be loaded or does not validate."""


@dataclass(frozen=True)
class Provenance:
    """Where a dataset came from, so a result can point back at it."""

    path: str
    sha256: str
    case_count: int
    loaded_at: str
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "caseCount": self.case_count,
            "loadedAt": self.loaded_at,
            "sizeBytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Provenance":
        return cls(
            path=raw.get("path", ""),
            sha256=raw.get("sha256", ""),
            case_count=int(raw.get("caseCount", 0)),
            loaded_at=raw.get("loadedAt", ""),
            size_bytes=int(raw.get("sizeBytes", 0)),
        )

    @property
    def short_sha(self) -> str:
        return self.sha256[:12]


@dataclass
class ValidationReport:
    """What validate() found. Errors block a run. Warnings do not."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_if_bad(self) -> "ValidationReport":
        if self.errors:
            joined = "\n  ".join(self.errors[:20])
            more = "" if len(self.errors) <= 20 else f"\n  ...and {len(self.errors) - 20} more"
            raise DatasetError(f"dataset did not validate:\n  {joined}{more}")
        return self

    def report(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"ERROR   {e}")
        for w in self.warnings:
            lines.append(f"WARN    {w}")
        if not lines:
            lines.append("dataset looks fine")
        return "\n".join(lines)


class Dataset:
    """A list of cases plus the paperwork that says where they came from."""

    def __init__(
        self,
        cases: Sequence[Case],
        provenance: Provenance,
        name: str | None = None,
    ) -> None:
        self._cases: list[Case] = list(cases)
        self.provenance = provenance
        self.name = name or Path(provenance.path).stem or "dataset"
        self._by_id: dict[str, Case] = {c.case_id: c for c in self._cases}

    # ---------------------------------------------------------------- loading

    @classmethod
    def load(
        cls,
        path: str | os.PathLike[str],
        name: str | None = None,
        strict: bool = True,
    ) -> "Dataset":
        """Read a JSONL file. One JSON object per line, blank lines skipped.

        With `strict=True` a bad line stops the load. That is the right
        default. A dataset you cannot fully parse is a dataset you cannot
        trust to compare two runs.
        """
        p = Path(path)
        if not p.exists():
            raise DatasetError(f"no dataset at {p}")

        raw_bytes = p.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()

        cases: list[Case] = []
        problems: list[str] = []
        text = raw_bytes.decode("utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                problems.append(f"{p.name}:{i}: not valid JSON ({exc.msg})")
                continue
            try:
                cases.append(Case.from_dict(raw, source=str(p), line_no=i))
            except CaseError as exc:
                problems.append(f"{p.name}:{i}: {exc}")

        if problems and strict:
            joined = "\n  ".join(problems[:20])
            more = "" if len(problems) <= 20 else f"\n  ...and {len(problems) - 20} more"
            raise DatasetError(f"could not load {p}:\n  {joined}{more}")

        if not cases:
            raise DatasetError(f"{p} has no cases in it")

        prov = Provenance(
            path=str(p),
            sha256=digest,
            case_count=len(cases),
            loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            size_bytes=len(raw_bytes),
        )
        ds = cls(cases, prov, name=name)
        dupes = ds.duplicate_ids()
        if dupes and strict:
            raise DatasetError(
                f"{p} has repeated caseIds: {', '.join(sorted(dupes)[:10])}"
            )
        return ds

    @classmethod
    def from_cases(
        cls,
        cases: Iterable[Case],
        name: str = "in-memory",
        path: str = "<memory>",
    ) -> "Dataset":
        """Build a dataset in code. Used by tests and by `filter()`."""
        case_list = list(cases)
        payload = "\n".join(
            json.dumps(c.to_dict(), sort_keys=True) for c in case_list
        ).encode("utf-8")
        prov = Provenance(
            path=path,
            sha256=hashlib.sha256(payload).hexdigest(),
            case_count=len(case_list),
            loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            size_bytes=len(payload),
        )
        return cls(case_list, prov, name=name)

    def save(self, path: str | os.PathLike[str]) -> Path:
        """Write the cases back out as JSONL."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for c in self._cases:
                fh.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        return p

    # ------------------------------------------------------------ collection

    @property
    def cases(self) -> list[Case]:
        return list(self._cases)

    def __len__(self) -> int:
        return len(self._cases)

    def __iter__(self) -> Iterator[Case]:
        return iter(self._cases)

    def __getitem__(self, index: int) -> Case:
        return self._cases[index]

    def get(self, case_id: str) -> Case | None:
        return self._by_id.get(case_id)

    def filter(self, predicate: Callable[[Case], bool], name: str | None = None) -> "Dataset":
        """Return a smaller dataset. Provenance points at the same file."""
        kept = [c for c in self._cases if predicate(c)]
        sub = Dataset(kept, self.provenance, name=name or f"{self.name}-filtered")
        return sub

    def sample(self, n: int, seed: int = 0) -> "Dataset":
        """Take a repeatable random sample. Same seed, same cases."""
        import random

        rng = random.Random(seed)
        picked = rng.sample(self._cases, min(n, len(self._cases)))
        picked.sort(key=lambda c: c.case_id)
        return Dataset(picked, self.provenance, name=f"{self.name}-sample{n}")

    def duplicate_ids(self) -> set[str]:
        counts = Counter(c.case_id for c in self._cases)
        return {cid for cid, n in counts.items() if n > 1}

    # -------------------------------------------------------------- summaries

    def tag_values(self, tag: str) -> Counter:
        """Count how many cases carry each value of one tag."""
        return Counter(c.tags.get(tag, "<missing>") for c in self._cases)

    def label_counts(self, field_name: str | None = None) -> Counter:
        counts: Counter = Counter()
        for c in self._cases:
            try:
                counts[str(c.expected_label(field_name))] += 1
            except CaseError:
                counts["<multi-field>"] += 1
        return counts

    def labeler_counts(self) -> Counter:
        return Counter(c.labeled_by or "<unlabeled>" for c in self._cases)

    def confidence_counts(self) -> Counter:
        return Counter(c.confidence or "<none>" for c in self._cases)

    def stats(self) -> dict[str, Any]:
        """A quick picture of the dataset. Printed by `validate` in the CLI."""
        tags = sorted({k for c in self._cases for k in c.tags})
        return {
            "name": self.name,
            "cases": len(self._cases),
            "provenance": self.provenance.to_dict(),
            "tags": {t: dict(self.tag_values(t)) for t in tags},
            "labeledBy": dict(self.labeler_counts()),
            "confidence": dict(self.confidence_counts()),
            "expectedFields": sorted({k for c in self._cases for k in c.expected}),
        }

    # ------------------------------------------------------------- validation

    def validate(
        self,
        required_tags: Sequence[str] = (),
        allowed_labels: Sequence[str] | None = None,
        label_field: str | None = None,
    ) -> ValidationReport:
        """Check the things that quietly ruin an eval.

        Missing tags mean a slice silently loses cases. An off list label
        means a typo becomes its own class in the confusion matrix. Both are
        cheap to catch here and expensive to catch later.
        """
        report = ValidationReport()

        dupes = self.duplicate_ids()
        for cid in sorted(dupes):
            report.errors.append(f"caseId '{cid}' appears more than once")

        allowed = set(allowed_labels) if allowed_labels else None
        expected_shapes = Counter(tuple(sorted(c.expected)) for c in self._cases)
        if len(expected_shapes) > 1:
            common = expected_shapes.most_common(1)[0][0]
            report.warnings.append(
                "cases do not all have the same expected fields. Most common is "
                f"{list(common)}. That is fine if you meant it."
            )

        for c in self._cases:
            where = f"{c.case_id}"
            for tag in required_tags:
                if not c.tags.get(tag):
                    report.errors.append(f"{where}: missing required tag '{tag}'")
            if allowed is not None:
                try:
                    label = c.expected_label(label_field)
                except CaseError as exc:
                    report.errors.append(f"{where}: {exc}")
                    continue
                if str(label) not in allowed:
                    report.errors.append(
                        f"{where}: label '{label}' is not in the allowed list"
                    )
            if c.labeled_by is None:
                report.warnings.append(f"{where}: no labeledBy, so nobody owns this label")
            if c.confidence is None:
                report.warnings.append(f"{where}: no confidence recorded")

        return report

    def __repr__(self) -> str:
        return (
            f"Dataset({self.name!r}, cases={len(self._cases)}, "
            f"sha256={self.provenance.short_sha})"
        )
