"""northstar_evals: a small eval library for the Northstar lab.

The five things you need most:

    from northstar_evals import Dataset, Runner, Slice, metrics, Case

    ds = Dataset.load("data/golden/txn-classification-v3.jsonl")

    result = Runner(
        task=classify_transactions,
        dataset=ds,
        slices=[
            Slice("loan_proceeds",     lambda c: c.tags.get("kind") == "loan"),
            Slice("internal_transfer", lambda c: c.tags.get("kind") == "transfer"),
            Slice("poor_ocr",          lambda c: c.tags.get("ocr_quality") == "poor"),
            Slice("card_settlement",   lambda c: c.tags.get("kind") == "settlement"),
        ],
    ).run()

    result.report()
    result.assert_no_regression(baseline="baselines/txn-v3-qwen8b.json")

Nothing in here is specific to lending. The Northstar suites live in
suites.py, and a second customer registers their own without touching the
rest of the library.
"""

from __future__ import annotations

from . import cost, gates, labeling, matchers, metrics, providers, slicing, suites
from .case import Annotation, Case, CaseError
from .compare import Comparison, compare, compare_many
from .cost import CostSummary, Usage, estimate_cost
from .dataset import Dataset, DatasetError, Provenance, ValidationReport
from .gates import Gate, GateFinding, GateReport
from .labeling import (
    AgreementReport,
    Disagreement,
    agreement,
    cohens_kappa,
    label_audit,
    suspect_labels,
)
from .metrics import (
    ClassMetrics,
    ConfusionMatrix,
    SliceMetrics,
    accuracy,
    confusion_matrix,
    macro_average,
    precision_recall_f1,
    weighted_average,
)
from .providers import StubProvider, get_provider
from .result import (
    BaselineResult,
    CaseResult,
    RegressionError,
    Result,
    RunInfo,
    slice_report,
)
from .runner import Prediction, Runner
from .slicing import Slice, SliceError, coverage
from .suites import Suite, register

__version__ = "1.0.0"

__all__ = [
    # the five names LAB_SPEC section 8 names
    "Dataset",
    "Runner",
    "Slice",
    "metrics",
    "Case",
    # models
    "Annotation",
    "CaseResult",
    "Prediction",
    "Provenance",
    "Result",
    "RunInfo",
    "BaselineResult",
    "Suite",
    # metrics
    "ClassMetrics",
    "ConfusionMatrix",
    "SliceMetrics",
    "accuracy",
    "confusion_matrix",
    "macro_average",
    "precision_recall_f1",
    "weighted_average",
    # comparing and gating
    "Comparison",
    "compare",
    "compare_many",
    "Gate",
    "GateFinding",
    "GateReport",
    "slice_report",
    # labeling
    "AgreementReport",
    "Disagreement",
    "agreement",
    "cohens_kappa",
    "label_audit",
    "suspect_labels",
    # cost
    "CostSummary",
    "Usage",
    "estimate_cost",
    # providers and suites
    "StubProvider",
    "get_provider",
    "register",
    # modules
    "cost",
    "gates",
    "labeling",
    "matchers",
    "providers",
    "slicing",
    "suites",
    "coverage",
    # errors
    "CaseError",
    "DatasetError",
    "RegressionError",
    "SliceError",
    "ValidationReport",
]
