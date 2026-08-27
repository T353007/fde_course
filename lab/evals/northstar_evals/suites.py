"""Suite definitions: dataset, slices, matchers, and gate in one place.

A suite is the thing you name on the command line:

    python -m northstar_evals run --suite txn-classification

Keeping the slices here instead of in a script is what makes this library
reusable. When Redwood Bank arrives in Phase 9, you add a suite. You do not
touch the Runner, the metrics, or the report.

To register your own suites without editing this file, point an environment
variable at a module that calls `register()`:

    export NORTHSTAR_EVALS_SUITES=redwood_evals.suites
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .dataset import Dataset
from .gates import Gate
from .matchers import Matcher, exact, normalized, numeric, set_overlap
from .providers import CATEGORIES
from .slicing import Slice


@dataclass
class Suite:
    """Everything needed to run one eval, named once."""

    name: str
    dataset_path: str
    slices: Sequence[Slice] = ()
    matchers: Mapping[str, Matcher] = field(default_factory=dict)
    label_field: str | None = None
    description: str = ""
    baseline: str | None = None
    gate: Gate | None = None
    required_tags: Sequence[str] = ()
    allowed_labels: Sequence[str] | None = None

    def load(self, data_root: str | os.PathLike[str] | None = None) -> Dataset:
        """Load this suite's dataset, resolving the path if needed."""
        return Dataset.load(resolve_data_path(self.dataset_path, data_root), name=self.name)

    def validate(self, data_root: str | os.PathLike[str] | None = None) -> Any:
        ds = self.load(data_root)
        return ds.validate(
            required_tags=self.required_tags,
            allowed_labels=self.allowed_labels,
            label_field=self.label_field,
        )


_REGISTRY: dict[str, Suite] = {}


def register(suite: Suite, replace: bool = False) -> Suite:
    """Add a suite to the registry."""
    if suite.name in _REGISTRY and not replace:
        raise ValueError(
            f"a suite named '{suite.name}' is already registered. "
            "Pass replace=True if you meant to override it."
        )
    _REGISTRY[suite.name] = suite
    return suite


def get(name: str) -> Suite:
    _load_external()
    if name in _REGISTRY:
        return _REGISTRY[name]
    # Let people say txn-classification-v3 when the suite is txn-classification.
    for key in _REGISTRY:
        if name.startswith(key):
            return _REGISTRY[key]
    known = ", ".join(sorted(_REGISTRY))
    raise KeyError(f"no suite named '{name}'. Known suites: {known}")


def all_suites() -> dict[str, Suite]:
    _load_external()
    return dict(_REGISTRY)


_external_loaded = False


def _load_external() -> None:
    global _external_loaded
    if _external_loaded:
        return
    _external_loaded = True
    modules = os.environ.get("NORTHSTAR_EVALS_SUITES", "")
    for mod in [m.strip() for m in modules.split(",") if m.strip()]:
        importlib.import_module(mod)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_data_path(
    path: str | os.PathLike[str],
    data_root: str | os.PathLike[str] | None = None,
) -> Path:
    """Find a dataset file without making the caller care about the cwd.

    Order: an absolute path wins. Then `data_root`, then the environment
    variable, then the current directory, then a walk up the tree looking for
    a `data/golden` folder. The last one is what makes `make eval` work from
    anywhere inside the lab.
    """
    p = Path(path)
    if p.is_absolute():
        return p

    roots: list[Path] = []
    if data_root:
        roots.append(Path(data_root))
    env_root = os.environ.get("NORTHSTAR_EVALS_DATA_ROOT")
    if env_root:
        roots.append(Path(env_root))
    roots.append(Path.cwd())

    for root in roots:
        candidate = root / p
        if candidate.exists():
            return candidate

    here = Path(__file__).resolve()
    for parent in [Path.cwd().resolve(), *Path.cwd().resolve().parents, *here.parents]:
        candidate = parent / p
        if candidate.exists():
            return candidate
        if (parent / "data" / "golden").is_dir():
            candidate = parent / p
            if candidate.exists():
                return candidate

    raise FileNotFoundError(
        f"could not find dataset '{path}'. Run from inside lab/ or set "
        "NORTHSTAR_EVALS_DATA_ROOT to the folder that holds data/golden."
    )


def baseline_path(name: str) -> Path:
    """Where a committed baseline lives, relative to the evals package."""
    return Path(__file__).resolve().parent.parent / "baselines" / name


# ---------------------------------------------------------------------------
# Northstar suites
# ---------------------------------------------------------------------------

# These four slice names are quoted in Missions 16 and 20. Renaming one breaks
# every committed baseline, so treat them as an interface.
TXN_SLICES = [
    Slice(
        "loan_proceeds",
        lambda c: c.tags.get("kind") == "loan",
        "money the business borrowed, which is not revenue",
    ),
    Slice(
        "internal_transfer",
        lambda c: c.tags.get("kind") == "transfer",
        "money moving between accounts the business already owns",
    ),
    Slice(
        "poor_ocr",
        lambda c: c.tags.get("ocr_quality") == "poor",
        "scanned or faxed pages the OCR vendor mangled",
    ),
    Slice(
        "card_settlement",
        lambda c: c.tags.get("kind") == "settlement",
        "daily payouts from a card processor, the easy majority",
    ),
]

register(
    Suite(
        name="txn-classification",
        dataset_path="data/golden/txn-classification-v3.jsonl",
        slices=TXN_SLICES,
        matchers={"classification": exact()},
        label_field="classification",
        description="Bank transaction descriptions to categories.",
        baseline="baselines/txn-v3-stub.json",
        required_tags=("kind", "ocr_quality", "tenant", "month"),
        allowed_labels=CATEGORIES,
        gate=Gate(
            min_overall=0.94,
            min_slices={
                "card_settlement": 0.97,
                "loan_proceeds": 0.65,
                "internal_transfer": 0.70,
                "poor_ocr": 0.58,
            },
            required_slices=[s.name for s in TXN_SLICES],
            min_support={"loan_proceeds": 15, "internal_transfer": 12, "poor_ocr": 25},
            max_regression=0.01,
            per_slice_regression={"loan_proceeds": 0.0, "internal_transfer": 0.0},
            baseline="baselines/txn-v3-stub.json",
        ),
    )
)

register(
    Suite(
        name="revenue-extraction",
        dataset_path="data/golden/revenue-extraction-v2.jsonl",
        slices=[
            Slice.from_tag("poor_ocr", "ocr_quality", "poor"),
            Slice.from_tag("clean_ocr", "ocr_quality", ("good", "fair")),
            Slice(
                "has_loan_deposit",
                lambda c: c.tags.get("has_loan") == "yes",
                "statements with a loan deposit hiding in the credits",
            ),
            Slice(
                "has_transfer",
                lambda c: c.tags.get("has_transfer") == "yes",
                "statements with an internal transfer in the credits",
            ),
            Slice.from_tag("multi_page", "pages", ("2", "3")),
        ],
        # A dollar either way is fine. Thirty thousand is not.
        matchers={
            "operatingRevenue": numeric(tolerance=1.0),
            "totalDeposits": numeric(tolerance=1.0),
        },
        label_field="operatingRevenue",
        description="Bank statement text to structured monthly revenue.",
        baseline="baselines/revenue-v2-stub.json",
        required_tags=("ocr_quality", "tenant", "month"),
        gate=Gate(
            min_overall=0.55,
            min_slices={"clean_ocr": 0.70},
            max_regression=0.02,
            baseline="baselines/revenue-v2-stub.json",
        ),
    )
)

register(
    Suite(
        name="policy-qa",
        dataset_path="data/golden/policy-qa-v1.jsonl",
        slices=[
            Slice(
                "superseded_trap",
                lambda c: c.tags.get("trap") == "superseded",
                "the closest document by wording is the one that expired",
            ),
            Slice(
                "tenant_scoped",
                lambda c: c.tags.get("trap") == "tenant_scope",
                "the answer must not come from another tenant's overlay",
            ),
            Slice(
                "effective_date",
                lambda c: c.tags.get("trap") == "effective_date",
                "the 2026 policy is real but not in effect yet",
            ),
            Slice(
                "product_overlay",
                lambda c: c.tags.get("trap") == "product_overlay",
                "SBA overlay beats everything when the product is SBA 7(a)",
            ),
            Slice(
                "straightforward",
                lambda c: c.tags.get("trap") in (None, "", "none"),
                "one obvious document, no precedence question",
            ),
        ],
        matchers={
            "citation": exact(),
            "answer": normalized(strip_punctuation=True),
            "citations": set_overlap(1.0),
        },
        label_field="citation",
        description="Policy questions with a required citation.",
        baseline="baselines/policy-v1-stub.json",
        required_tags=("tenant", "product"),
        gate=Gate(
            min_overall=0.40,
            min_slices={"straightforward": 0.60},
            max_regression=0.02,
            baseline="baselines/policy-v1-stub.json",
        ),
    )
)

register(
    Suite(
        name="smoke",
        dataset_path="data/golden/smoke.jsonl",
        slices=TXN_SLICES,
        matchers={"classification": exact()},
        label_field="classification",
        description="Twenty cases for CI. Runs in under a second.",
        baseline="baselines/smoke-stub.json",
        required_tags=("kind", "ocr_quality", "tenant", "month"),
        allowed_labels=CATEGORIES,
        gate=Gate(
            min_overall=0.80,
            max_regression=0.0,
            max_task_errors=0,
            baseline="baselines/smoke-stub.json",
        ),
    )
)


def slice_factory(name: str) -> Callable[..., Slice]:
    """Small helper so config driven suites can build slices by tag."""
    if name == "from_tag":
        return Slice.from_tag
    if name == "from_label":
        return Slice.from_label
    raise KeyError(f"no slice factory called '{name}'")
