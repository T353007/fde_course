"""The Case model.

A case is one labeled example. It holds what goes into the model, what a human
said the right answer is, and enough provenance to argue about that answer later.

The wire format is one JSON object per line, exactly as written in LAB_SPEC
section 8:

    {
      "caseId": "TX-10021",
      "input": {"description": "TRANSFER FROM SAVINGS ****1221", "amount": 30000},
      "expected": {"classification": "INTERNAL_TRANSFER"},
      "tags": {"kind": "transfer", "ocr_quality": "good", "tenant": "NSC_DIRECT"},
      "labeledBy": "renee.blackwell",
      "labeledAt": "2026-04-11",
      "confidence": "high"
    }

Two optional fields are allowed on top of that. `notes` is free text from the
labeler. `annotations` holds extra labels from other people, which is what the
agreement math in labeling.py reads. Files that leave both out still load.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONFIDENCE_LEVELS = ("high", "medium", "low")

REQUIRED_KEYS = ("caseId", "input", "expected")

_KNOWN_KEYS = frozenset(
    {
        "caseId",
        "input",
        "expected",
        "tags",
        "labeledBy",
        "labeledAt",
        "confidence",
        "notes",
        "annotations",
    }
)


class CaseError(ValueError):
    """Raised when a line in a dataset file is not a usable case."""


@dataclass(frozen=True)
class Annotation:
    """One person's answer for one case.

    Used when more than one human labeled the same case. Cohen's kappa needs
    two of these per case to say anything.
    """

    annotator: str
    label: Any
    at: str | None = None
    confidence: str | None = None
    note: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Annotation":
        if "annotator" not in raw:
            raise CaseError("annotation is missing 'annotator'")
        if "label" not in raw:
            raise CaseError("annotation is missing 'label'")
        return cls(
            annotator=str(raw["annotator"]),
            label=raw["label"],
            at=raw.get("at"),
            confidence=raw.get("confidence"),
            note=raw.get("note"),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"annotator": self.annotator, "label": self.label}
        if self.at is not None:
            out["at"] = self.at
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.note is not None:
            out["note"] = self.note
        return out


@dataclass
class Case:
    """One labeled example.

    Attribute names stay close to the JSON. `case_id` is the Python name and
    `caseId` works too, so code copied out of a mission still runs.
    """

    case_id: str
    input: dict[str, Any]
    expected: dict[str, Any]
    tags: dict[str, str] = field(default_factory=dict)
    labeled_by: str | None = None
    labeled_at: str | None = None
    confidence: str | None = None
    notes: str | None = None
    annotations: list[Annotation] = field(default_factory=list)
    source: str | None = None
    line_no: int | None = None

    # Aliases so both spellings work. Missions quote the JSON spelling.
    @property
    def caseId(self) -> str:  # noqa: N802 - matches the wire format on purpose
        return self.case_id

    @property
    def labeledBy(self) -> str | None:  # noqa: N802
        return self.labeled_by

    @property
    def labeledAt(self) -> str | None:  # noqa: N802
        return self.labeled_at

    def tag(self, name: str, default: str | None = None) -> str | None:
        """Read one tag. Same as `case.tags.get(name)`, just shorter."""
        return self.tags.get(name, default)

    def expected_label(self, field_name: str | None = None) -> Any:
        """Return the single expected value.

        If `field_name` is given, return that field. If the expected block has
        exactly one field, return it without being told which one.
        """
        if field_name is not None:
            return self.expected.get(field_name)
        if len(self.expected) == 1:
            return next(iter(self.expected.values()))
        raise CaseError(
            f"case {self.case_id} has {len(self.expected)} expected fields, "
            "so you have to say which one you mean"
        )

    def is_low_confidence(self) -> bool:
        return (self.confidence or "").lower() == "low"

    @classmethod
    def from_dict(
        cls,
        raw: dict[str, Any],
        source: str | None = None,
        line_no: int | None = None,
    ) -> "Case":
        if not isinstance(raw, dict):
            raise CaseError("a case must be a JSON object")

        missing = [k for k in REQUIRED_KEYS if k not in raw]
        if missing:
            raise CaseError(f"case is missing required keys: {', '.join(missing)}")

        case_id = raw["caseId"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise CaseError("caseId must be a non empty string")

        inp = raw["input"]
        if not isinstance(inp, dict):
            raise CaseError(f"case {case_id}: 'input' must be an object")

        expected = raw["expected"]
        if not isinstance(expected, dict):
            raise CaseError(f"case {case_id}: 'expected' must be an object")
        if not expected:
            raise CaseError(f"case {case_id}: 'expected' cannot be empty")

        tags_raw = raw.get("tags") or {}
        if not isinstance(tags_raw, dict):
            raise CaseError(f"case {case_id}: 'tags' must be an object")
        tags = {str(k): ("" if v is None else str(v)) for k, v in tags_raw.items()}

        confidence = raw.get("confidence")
        if confidence is not None and confidence not in CONFIDENCE_LEVELS:
            raise CaseError(
                f"case {case_id}: confidence '{confidence}' is not one of "
                f"{', '.join(CONFIDENCE_LEVELS)}"
            )

        annotations_raw = raw.get("annotations") or []
        if not isinstance(annotations_raw, list):
            raise CaseError(f"case {case_id}: 'annotations' must be a list")
        annotations = [Annotation.from_dict(a) for a in annotations_raw]

        unknown = set(raw) - _KNOWN_KEYS
        if unknown:
            raise CaseError(
                f"case {case_id}: unknown keys {sorted(unknown)}. "
                "Add them under 'tags' or 'notes' instead."
            )

        return cls(
            case_id=case_id,
            input=inp,
            expected=expected,
            tags=tags,
            labeled_by=raw.get("labeledBy"),
            labeled_at=raw.get("labeledAt"),
            confidence=confidence,
            notes=raw.get("notes"),
            annotations=annotations,
            source=source,
            line_no=line_no,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON form. Key order matches the spec example."""
        out: dict[str, Any] = {
            "caseId": self.case_id,
            "input": self.input,
            "expected": self.expected,
            "tags": self.tags,
        }
        if self.labeled_by is not None:
            out["labeledBy"] = self.labeled_by
        if self.labeled_at is not None:
            out["labeledAt"] = self.labeled_at
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.notes is not None:
            out["notes"] = self.notes
        if self.annotations:
            out["annotations"] = [a.to_dict() for a in self.annotations]
        return out

    def __repr__(self) -> str:
        return f"Case({self.case_id!r}, tags={self.tags!r})"
