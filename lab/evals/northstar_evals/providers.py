"""Where the answers come from.

A provider turns a suite name into a task function the Runner can call. The
same suite runs against three of them:

    stub    a deterministic baseline that runs offline and costs nothing.
            This is the keyword classifier Northstar already had. It is not a
            straw man. It is what most teams ship first, and it scores 96
            percent overall, which is the whole problem.
    ollama  a local model on your laptop, through the Ollama HTTP API.
    hosted  ai-service on port 8000, or any OpenAI compatible endpoint.

Every provider reports cost and latency. Stub and ollama cost 0.0 dollars and
say why in `cost_basis`, because free per call is not the same as free.

Nothing here imports a third party package. urllib is enough, and a library
that a learner can install with no network is worth more than a nicer client.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .case import Case
from .cost import estimate_cost
from .runner import Prediction

CATEGORIES = (
    "OPERATING_REVENUE",
    "INTERNAL_TRANSFER",
    "LOAN_PROCEEDS",
    "OWNER_CAPITAL",
    "REFUND_CHARGEBACK",
    "TAX_REFUND",
    "INSURANCE_SETTLEMENT",
    "EXPENSE",
    "UNKNOWN",
)


class Provider(Protocol):
    """Anything that can turn a suite name into a task."""

    name: str

    def task_for(self, suite: str) -> Callable[[Case], Prediction]: ...


class ProviderError(RuntimeError):
    """Raised when a provider is asked for something it cannot do."""


# ---------------------------------------------------------------------------
# The baseline classifier
# ---------------------------------------------------------------------------
#
# This is a keyword rule list, in priority order. It is the thing Northstar
# wrote in 2019 and never revisited. Read it once and you can predict every
# mistake it makes:
#
#   - it never sees a competitor loan that does not say "loan"
#   - it never sees a transfer that is labeled with only an account number
#   - when OCR mangles the one keyword that mattered, it falls through to the
#     last rule and calls the deposit revenue
#
# The last rule is the same assumption as RevenueCalculator.java: money in is
# revenue. That is the bug the entire course is built on.

EXPENSE_KEYS = ("DEBIT", "WITHDRAWAL", "ACH DR", "PAYMENT SENT", "CHECK PAID", "FEE ")
REFUND_KEYS = ("REFUND", "CHARGEBACK", "CHGBK", "REVERSAL", "RETURNED ITEM", "DISPUTE")
TAX_KEYS = ("IRS TREAS", "TAX REF", "TAXREF", "STATE TAX", "NCDOR", "DEPT OF REVENUE")
INSURANCE_KEYS = ("INSURANCE", "CLAIM PAYMENT", "CLM PMT", "SETTLEMENT CLAIM", "ADJUSTER")
LOAN_KEYS = ("LOAN", "SBA 7A", "SBA7A", "LN PROCEEDS", "NOTE PROCEEDS", "MCA ADVANCE")
TRANSFER_KEYS = ("TRANSFER", "XFER", "BOOK TFR", "INTERNAL TFR", "ONLINE TRF")
OWNER_KEYS = ("OWNER", "MEMBER CONTRIB", "CAPITAL CONTRIB", "SHAREHOLDER")
PROCESSOR_KEYS = (
    "STRIPE",
    "SQUARE",
    "TOAST",
    "CLOVER",
    "SHOPIFY",
    "ADYEN",
    "WORLDPAY",
    "FISERV",
    "ELAVON",
    "TSYS",
    "HEARTLAND",
    "BANKCARD",
    "MERCHANT DEP",
    "CARD SETTLE",
    "CC SETTLE",
    "POS DEP",
)

_ALNUM = re.compile(r"[A-Za-z0-9]")


def looks_unreadable(text: str) -> bool:
    """Did OCR give us something no reader could act on.

    Three or more block characters in a row is what OptiScan returns when it
    gives up on a faxed page. A model that answers anyway is guessing.
    """
    if "###" in text or "|||" in text or "[ILLEGIBLE]" in text.upper():
        return True
    if not text.strip():
        return True
    readable = len(_ALNUM.findall(text))
    return readable / max(len(text), 1) < 0.45


def baseline_classify(description: str, amount: float | None = None) -> str:
    """The 2019 keyword classifier, unchanged.

    Priority order matters. The last line is the one that costs money.
    """
    text = (description or "").upper()

    if looks_unreadable(text):
        return "UNKNOWN"
    if amount is not None and amount < 0:
        return "EXPENSE"
    if any(k in text for k in EXPENSE_KEYS):
        return "EXPENSE"
    if any(k in text for k in REFUND_KEYS):
        return "REFUND_CHARGEBACK"
    if any(k in text for k in TAX_KEYS):
        return "TAX_REFUND"
    if any(k in text for k in INSURANCE_KEYS):
        return "INSURANCE_SETTLEMENT"
    if any(k in text for k in LOAN_KEYS):
        return "LOAN_PROCEEDS"
    if any(k in text for k in TRANSFER_KEYS):
        return "INTERNAL_TRANSFER"
    if any(k in text for k in OWNER_KEYS):
        return "OWNER_CAPITAL"
    if any(k in text for k in PROCESSOR_KEYS):
        return "OPERATING_REVENUE"
    if amount is not None and amount > 0:
        # Money came in and nothing matched. Call it revenue and move on.
        return "OPERATING_REVENUE"
    return "UNKNOWN"


_TXN_LINE = re.compile(
    r"^\s*(\d{2}/\d{2})\s+(.+?)\s+([-+]?[\d,]+(?:\.\d{2})?)\s*$",
)


def parse_statement_lines(text: str) -> list[dict[str, Any]]:
    """Pull transactions out of a plain text bank statement.

    Handles the shape the OCR vendor produces: date, description, amount, one
    per line. Lines it cannot parse are skipped, which is itself a source of
    error the eval will catch.
    """
    rows: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        m = _TXN_LINE.match(line)
        if not m:
            continue
        date, description, raw_amount = m.groups()
        try:
            amount = float(raw_amount.replace(",", "").replace("+", ""))
        except ValueError:
            continue
        rows.append({"date": date, "description": description.strip(), "amount": amount})
    return rows


def baseline_revenue(text: str) -> dict[str, Any]:
    """Extract monthly revenue from statement text, the way the baseline does.

    It classifies each line and adds up the credits it thinks are operating
    revenue. It also reports total deposits, because the portal widget wants
    that number and the two are not the same.
    """
    rows = parse_statement_lines(text)
    total_deposits = sum(r["amount"] for r in rows if r["amount"] > 0)
    operating = 0.0
    for r in rows:
        if r["amount"] <= 0:
            continue
        if baseline_classify(r["description"], r["amount"]) == "OPERATING_REVENUE":
            operating += r["amount"]
    return {
        "operatingRevenue": round(operating, 2),
        "totalDeposits": round(total_deposits, 2),
        "transactionCount": len(rows),
    }


_STOPWORDS = {
    "the", "a", "an", "of", "for", "to", "in", "on", "is", "are", "what",
    "which", "does", "do", "and", "or", "we", "our", "can", "with", "at",
}


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def baseline_policy_answer(
    question: str,
    documents: list[dict[str, Any]],
    tenant: str | None = None,
) -> dict[str, Any]:
    """Answer a policy question by picking the closest document.

    Closest by word overlap, which is what a plain embedding search does when
    nobody has thought about effective dates or tenant scoping. It has no idea
    that credit-policy-FINAL.pdf is a 2023 draft. It just knows the words line
    up, and the words line up beautifully.
    """
    best_doc: dict[str, Any] | None = None
    best_score = -1.0
    q = _keywords(question)
    for doc in documents or []:
        d = _keywords(doc.get("text", "") + " " + doc.get("title", ""))
        if not d:
            continue
        overlap = len(q & d) / max(len(q | d), 1)
        # A small nudge for a longer document, which is how naive chunk
        # scoring behaves in practice.
        overlap += 0.001 * min(len(d), 50)
        if overlap > best_score:
            best_score = overlap
            best_doc = doc
    if best_doc is None:
        return {"answer": "I do not know.", "citation": "none"}
    return {
        "answer": best_doc.get("answer", best_doc.get("text", ""))[:400],
        "citation": best_doc.get("id", "unknown"),
    }


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


@dataclass
class StubProvider:
    """Offline, deterministic, free. The default everywhere.

    Latency is simulated so the report has a shape, but it is not a
    measurement of anything. `cost_basis` says so.
    """

    name: str = "stub"
    model: str = "baseline-keyword-v3"
    prompt_version: str = "stub-1"
    simulated_latency_ms: float = 12.0

    def task_for(self, suite: str) -> Callable[[Case], Prediction]:
        handler = _STUB_HANDLERS.get(_suite_kind(suite))
        if handler is None:
            raise ProviderError(
                f"the stub provider has no baseline for suite '{suite}'. "
                "Add one in northstar_evals/providers.py."
            )

        def task(case: Case) -> Prediction:
            output = handler(case)
            return Prediction(
                output=output,
                cost_usd=0.0,
                latency_ms=self.simulated_latency_ms,
                model=self.model,
                prompt_tokens=0,
                completion_tokens=0,
                cost_basis="stub provider, no model call was made",
                prompt_version=self.prompt_version,
            )

        return task


def _stub_classification(case: Case) -> dict[str, Any]:
    return {
        "classification": baseline_classify(
            str(case.input.get("description", "")),
            _maybe_float(case.input.get("amount")),
        )
    }


def _stub_revenue(case: Case) -> dict[str, Any]:
    extracted = baseline_revenue(str(case.input.get("text", "")))
    wanted = set(case.expected)
    return {k: v for k, v in extracted.items() if k in wanted} or extracted


def _stub_policy(case: Case) -> dict[str, Any]:
    out = baseline_policy_answer(
        str(case.input.get("question", "")),
        list(case.input.get("documents") or []),
        case.tags.get("tenant"),
    )
    wanted = set(case.expected)
    return {k: v for k, v in out.items() if k in wanted} or out


_STUB_HANDLERS: dict[str, Callable[[Case], dict[str, Any]]] = {
    "txn-classification": _stub_classification,
    "revenue-extraction": _stub_revenue,
    "policy-qa": _stub_policy,
}


def _suite_kind(suite: str) -> str:
    """Map 'txn-classification-v3' or 'smoke' onto a handler name."""
    base = suite.lower()
    for key in _STUB_HANDLERS:
        if base.startswith(key):
            return key
    if "smoke" in base:
        return "txn-classification"
    return base


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class OllamaProvider:
    """A local model over the Ollama HTTP API.

    Costs 0.0 dollars per call and 6 to 11 seconds of your laptop. Both of
    those show up in the report, which is the point of Mission 17.
    """

    model: str = "qwen3:8b"
    host: str = ""
    name: str = "ollama"
    timeout_s: float = 120.0
    prompt_version: str = "txn-classify-v2"

    def __post_init__(self) -> None:
        self.host = self.host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def task_for(self, suite: str) -> Callable[[Case], Prediction]:
        kind = _suite_kind(suite)
        build_prompt = _PROMPTS.get(kind)
        if build_prompt is None:
            raise ProviderError(f"no prompt for suite '{suite}'")

        def task(case: Case) -> Prediction:
            prompt = build_prompt(case)
            started = time.perf_counter()
            body = json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.0},
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host.rstrip('/')}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.URLError as exc:
                raise ProviderError(
                    f"could not reach Ollama at {self.host}. "
                    f"Run `make ollama-check`. ({exc})"
                ) from exc
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return Prediction(
                output=_coerce_json(payload.get("response", ""), case),
                cost_usd=0.0,
                latency_ms=elapsed_ms,
                model=self.model,
                prompt_tokens=int(payload.get("prompt_eval_count") or 0),
                completion_tokens=int(payload.get("eval_count") or 0),
                cost_basis="local model, no per token charge",
                prompt_version=self.prompt_version,
                raw=payload,
            )

        return task


@dataclass
class HostedProvider:
    """A hosted model, reached through ai-service on port 8000.

    ai-service already carries the tenant header, the trace id, and the
    provider switch. Going through it means the eval measures the thing you
    ship instead of a second code path that only the eval uses.
    """

    model: str = "gpt-4o-mini"
    base_url: str = ""
    name: str = "hosted"
    tenant: str = "NSC_DIRECT"
    timeout_s: float = 60.0
    prompt_version: str = "txn-classify-v2"

    _ENDPOINTS = {
        "txn-classification": "/v1/classify/transactions",
        "revenue-extraction": "/v1/extract/bank-statement",
        "policy-qa": "/v1/policy/answer",
    }

    def __post_init__(self) -> None:
        self.base_url = self.base_url or os.environ.get(
            "AI_SERVICE_URL", "http://localhost:8000"
        )

    def task_for(self, suite: str) -> Callable[[Case], Prediction]:
        kind = _suite_kind(suite)
        endpoint = self._ENDPOINTS.get(kind)
        if endpoint is None:
            raise ProviderError(f"no ai-service endpoint for suite '{suite}'")
        url = self.base_url.rstrip("/") + endpoint

        def task(case: Case) -> Prediction:
            started = time.perf_counter()
            body = json.dumps({"model": self.model, **case.input}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Tenant-Id": case.tags.get("tenant") or self.tenant,
                    "X-Trace-Id": f"eval-{case.case_id}",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.URLError as exc:
                raise ProviderError(
                    f"could not reach ai-service at {url}. Is `make up` running? ({exc})"
                ) from exc
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            usage = payload.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens") or 0)
            completion_tokens = int(usage.get("completion_tokens") or 0)
            cost = payload.get("cost_usd")
            if cost is None:
                cost = estimate_cost(self.model, prompt_tokens, completion_tokens)
            return Prediction(
                output=payload.get("result", payload),
                cost_usd=float(cost),
                latency_ms=float(payload.get("latency_ms") or elapsed_ms),
                model=payload.get("model") or self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_basis="hosted model, billed per token",
                prompt_version=payload.get("prompt_version") or self.prompt_version,
                raw=payload,
            )

        return task


def _classification_prompt(case: Case) -> str:
    return (
        "You classify one bank transaction for a small business lender.\n"
        f"Allowed categories: {', '.join(CATEGORIES)}.\n"
        "Answer with JSON only, shaped {\"classification\": \"<CATEGORY>\"}.\n"
        "A deposit from a lender is LOAN_PROCEEDS even when the lender name "
        "looks like a customer name.\n"
        "A movement between two accounts the business owns is "
        "INTERNAL_TRANSFER even when only an account number is shown.\n"
        "If the text cannot be read, answer UNKNOWN. Do not guess.\n\n"
        f"Description: {case.input.get('description', '')}\n"
        f"Amount: {case.input.get('amount', '')}\n"
    )


def _revenue_prompt(case: Case) -> str:
    return (
        "Read this bank statement text and return monthly revenue as JSON.\n"
        "Shape: {\"operatingRevenue\": <number>, \"totalDeposits\": <number>}.\n"
        "Numbers only. No currency symbols and no words.\n"
        "Operating revenue excludes internal transfers and loan proceeds.\n\n"
        f"{case.input.get('text', '')}\n"
    )


def _policy_prompt(case: Case) -> str:
    docs = case.input.get("documents") or []
    rendered = "\n\n".join(
        f"[{d.get('id')}] {d.get('title', '')}\n{d.get('text', '')}" for d in docs
    )
    return (
        "Answer the policy question using only the documents below.\n"
        "Return JSON shaped {\"answer\": \"...\", \"citation\": \"<document id>\"}.\n"
        "Cite the document that is in effect today for this tenant and product.\n"
        "A document titled FINAL is not automatically the current one.\n\n"
        f"Tenant: {case.tags.get('tenant', 'unknown')}\n"
        f"Question: {case.input.get('question', '')}\n\n{rendered}\n"
    )


_PROMPTS: dict[str, Callable[[Case], str]] = {
    "txn-classification": _classification_prompt,
    "revenue-extraction": _revenue_prompt,
    "policy-qa": _policy_prompt,
}


def _coerce_json(text: str, case: Case) -> Any:
    """Models return JSON with extra words around it. Dig it out."""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    # Give the matcher the raw string. A parse failure is a real result and
    # should show up as a wrong answer, not as a crash.
    if len(case.expected) == 1:
        return {next(iter(case.expected)): text}
    return {"raw": text}


PROVIDERS: dict[str, Callable[..., Provider]] = {
    "stub": StubProvider,
    "ollama": OllamaProvider,
    "hosted": HostedProvider,
}


def get_provider(name: str, model: str | None = None, **kwargs: Any) -> Provider:
    """Build a provider by name. Used by the CLI's --provider flag."""
    key = (name or "stub").lower()
    if key not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise ProviderError(f"no provider named '{name}'. Known providers: {known}")
    if model:
        kwargs["model"] = model
    return PROVIDERS[key](**kwargs)
