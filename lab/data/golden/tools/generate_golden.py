#!/usr/bin/env python3
"""Build the golden eval datasets so the stub classifier hits CANON numbers.

Run from anywhere:

    python lab/data/golden/tools/generate_golden.py

Writes into lab/data/golden/. Re-run only when you mean to change the teaching
numbers. The committed JSONL files are the source of truth for missions.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # lab/
GOLDEN = ROOT / "data" / "golden"
sys.path.insert(0, str(ROOT / "evals"))

from northstar_evals.providers import baseline_classify  # noqa: E402

TENANTS = ("NSC_DIRECT", "BAYLINE", "CASCADE")
MONTHS = ("2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04")
SENIOR = ("renee.blackwell", "d.pham", "m.okonkwo")
JUNIOR = ("t.okafor", "j.pham", "junior.underwriter")

PROCESSORS = (
    "STRIPE PAYOUT",
    "SQUARE DEPOSIT",
    "TOAST PAYOUT",
    "CLOVER DEPOSIT",
    "SHOPIFY PAYOUT",
    "ADYEN SETTLEMENT",
    "WORLDPAY DEPOSIT",
    "FISERV MERCHANT DEP",
    "ELAVON SETTLEMENT",
    "TSYS CARD SETTLE",
    "HEARTLAND DEPOSIT",
    "BANKCARD SETTLEMENT",
    "CC SETTLE BATCH",
    "POS DEP DAILY",
)

LOAN_HIT = (
    "SBA 7A LOAN DISBURSEMENT",
    "TERM LOAN PROCEEDS",
    "MCA ADVANCE FUNDING",
    "NOTE PROCEEDS WIRE",
    "LN PROCEEDS ACH",
    "BANK LOAN DRAW",
    "SBA7A FUNDING CREDIT",
    "WORKING CAPITAL LOAN",
)

LOAN_MISS = (
    "FASTCAPITAL FUNDING",
    "ONDORA CAPITAL INJECTION",
    "CLEARPATH ADVANCE",
    "RIVERBEND GROWTH CREDIT",
    "PACIFICLEDGER FUNDING DEP",
    "NORTHBRIDGE WORKING CAP",
    "SUMMITLINE BUSINESS ADVANCE",
    "APEX MERCHANT FUNDING",
)

TRANSFER_HIT = (
    "TRANSFER FROM SAVINGS ****1221",
    "ONLINE TRF TO CHECKING",
    "XFER FROM OPERATING",
    "BOOK TFR PAYROLL COVER",
    "INTERNAL TFR RESERVE",
    "TRANSFER TO MONEY MKT",
)

TRANSFER_MISS = (
    "FROM ****1221 SAVINGS",
    "TO ACCT 8841 OPERATING",
    "WIRE BTWN OWNED ACCTS",
    "SVGS ****1221 TO CHK ****3301",
)

# Amounts matter: a negative amount always becomes EXPENSE in the stub before
# refund keywords run. Tax lines must not contain the bare word REFUND or the
# refund rule fires first.
OTHER_HIT = (
    ("ACH DR VENDOR PAYMENT", "EXPENSE", -420.0),
    ("CHECK PAID 10422", "EXPENSE", -890.0),
    ("FEE MONTHLY SERVICE", "EXPENSE", -45.0),
    ("STRIPE REFUND BATCH", "REFUND_CHARGEBACK", 120.0),
    ("CHARGEBACK VISA 4421", "REFUND_CHARGEBACK", 65.5),
    ("IRS TREAS 310 TAX REF", "TAX_REFUND", 2400.0),
    ("NCDOR STATE TAX REF", "TAX_REFUND", 880.0),
    ("INSURANCE CLAIM PAYMENT", "INSURANCE_SETTLEMENT", 4500.0),
    ("OWNER CAPITAL CONTRIB", "OWNER_CAPITAL", 10000.0),
    ("MEMBER CONTRIB Q1", "OWNER_CAPITAL", 5000.0),
)


def _date(rng: random.Random) -> str:
    return rng.choice(
        [
            "2025-11-03",
            "2025-12-14",
            "2026-01-09",
            "2026-02-18",
            "2026-03-22",
            "2026-04-11",
            "2026-04-28",
        ]
    )


def _tags(
    kind: str,
    ocr: str,
    tenant: str | None = None,
    month: str | None = None,
    rng: random.Random | None = None,
    **extra: str,
) -> dict[str, str]:
    rng = rng or random.Random(0)
    tags = {
        "kind": kind,
        "ocr_quality": ocr,
        "tenant": tenant or rng.choice(TENANTS),
        "month": month or rng.choice(MONTHS),
    }
    tags.update(extra)
    return tags


def _case(
    case_id: str,
    description: str,
    amount: float,
    expected: str,
    tags: dict[str, str],
    labeled_by: str,
    labeled_at: str,
    confidence: str,
    notes: str | None = None,
    annotations: list[dict] | None = None,
) -> dict:
    out = {
        "caseId": case_id,
        "input": {"description": description, "amount": amount},
        "expected": {"classification": expected},
        "tags": tags,
        "labeledBy": labeled_by,
        "labeledAt": labeled_at,
        "confidence": confidence,
    }
    if notes:
        out["notes"] = notes
    if annotations:
        out["annotations"] = annotations
    pred = baseline_classify(description, amount)
    # Sanity for generation: callers that need a known stub outcome check this.
    out["_stub"] = pred
    return out


def _strip_stub(cases: list[dict]) -> list[dict]:
    cleaned = []
    for c in cases:
        c = dict(c)
        c.pop("_stub", None)
        cleaned.append(c)
    return cleaned


def _mangle(text: str, rng: random.Random, hard: bool = False) -> str:
    """Mess up a description the way OptiScan does on a faxed page."""
    if hard:
        # Triggers looks_unreadable via ### and low alphanumeric ratio.
        core = "".join(ch if rng.random() > 0.55 else "#" for ch in text)
        return f"### {core} ||| [ILLEGIBLE]"
    chars = list(text)
    for i in range(len(chars)):
        if chars[i].isalpha() and rng.random() < 0.18:
            chars[i] = rng.choice("lI1O0#/")
    return "".join(chars)


def build_txn_classification(seed: int = 42) -> list[dict]:
    """~400 cases engineered for the CANON slice table under the stub.

    Targets (stub provider):
      overall ~96%, card_settlement ~99% at ~84% volume,
      loan_proceeds ~68%, internal_transfer ~73%, poor_ocr ~61%.
    About 2% of labels are intentionally wrong (junior, low confidence).
    """
    rng = random.Random(seed)
    cases: list[dict] = []
    n = 0

    def next_id(prefix: str = "TX") -> str:
        nonlocal n
        n += 1
        return f"{prefix}-{10000 + n}"

    # --- CANON five transactions (Mission 20 bank statement) ----------------
    canon = [
        ("TX-CANON-01", "STRIPE PAYOUT", 48230.0, "OPERATING_REVENUE", "settlement", "good"),
        ("TX-CANON-02", "TRANSFER FROM SAVINGS", 30000.0, "INTERNAL_TRANSFER", "transfer", "good"),
        ("TX-CANON-03", "STRIPE PAYOUT", 51340.0, "OPERATING_REVENUE", "settlement", "good"),
        ("TX-CANON-04", "FASTCAPITAL LOAN", 75000.0, "LOAN_PROCEEDS", "loan", "good"),
        ("TX-CANON-05", "STRIPE PAYOUT", 47830.0, "OPERATING_REVENUE", "settlement", "good"),
    ]
    for cid, desc, amt, exp, kind, ocr in canon:
        cases.append(
            _case(
                cid,
                desc,
                amt,
                exp,
                _tags(kind, ocr, tenant="NSC_DIRECT", month="2026-05", rng=rng),
                "renee.blackwell",
                "2026-05-28",
                "high",
                notes="from the Mission 20 signature statement",
            )
        )

    # Volume plan for N=400 including the 5 canon cases already added:
    #   settlement: 336 (84%), loan: 25, transfer: 15, other: 24
    # Canon already contributed: 3 settlement, 1 loan, 1 transfer.
    # Remaining: settlement 333, loan 24, transfer 14, other 24. Total added 395.
    # Wrongs: settlement 3, loan 8, transfer 4, other 1 → 16 → overall 96%.

    # --- Settlements: 333 more, of which 3 hard-OCR misses -------------------
    # 3 canon settlements already correct. Need 330 more correct + 3 wrong.
    settle_wrong = 3
    settle_correct_poor = 20  # tuned so poor_ocr lands near 61%
    settle_correct_good = 333 - settle_wrong - settle_correct_poor

    for i in range(settle_correct_good):
        desc = f"{rng.choice(PROCESSORS)} {rng.randint(1000, 9999)}"
        amt = round(rng.uniform(800, 62000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "OPERATING_REVENUE",
                _tags("settlement", "good", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )

    for i in range(settle_correct_poor):
        base = rng.choice(PROCESSORS)
        desc = _mangle(f"{base} {rng.randint(1000, 9999)}", rng, hard=False)
        # Keep a clean processor token so the stub still hits.
        if not any(p.split()[0] in desc.upper() for p in PROCESSORS):
            desc = f"{base} {desc}"
        amt = round(rng.uniform(800, 62000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "OPERATING_REVENUE",
                _tags("settlement", "poor", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "medium",
            )
        )

    for i in range(settle_wrong):
        base = rng.choice(PROCESSORS)
        desc = _mangle(base, rng, hard=True)
        amt = round(rng.uniform(2000, 40000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "OPERATING_REVENUE",
                _tags("settlement", "poor", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "medium",
                notes="OCR gave up; stub returns UNKNOWN",
            )
        )

    # --- Loans: 24 more (1 canon already). Need 8 misses total among 25. -----
    # Canon FASTCAPITAL LOAN is a hit. So 16 more hits + 8 misses.
    for i in range(16):
        desc = LOAN_HIT[i % len(LOAN_HIT)]
        if i >= len(LOAN_HIT):
            desc = f"{desc} REF {1000 + i}"
        ocr = "poor" if i < 3 else "good"
        if ocr == "poor":
            # Light noise only. Never touch the LOAN / MCA / SBA tokens.
            desc = desc + " ~fax"
        amt = round(rng.uniform(15000, 120000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "LOAN_PROCEEDS",
                _tags("loan", ocr, rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )

    for i, desc in enumerate(LOAN_MISS):
        # Real stub misses: no LOAN keyword. Tag poor OCR on all so poor_ocr
        # absorbs these wrongs.
        amt = round(rng.uniform(20000, 90000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "LOAN_PROCEEDS",
                _tags("loan", "poor", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
                notes="competitor funding with no 'loan' token",
            )
        )

    # --- Transfers: 14 more (1 canon hit). Need 4 misses among 15. -----------
    # Canon is a hit. 10 more hits + 4 misses.
    for i in range(10):
        desc = TRANSFER_HIT[i % len(TRANSFER_HIT)]
        if i >= len(TRANSFER_HIT):
            desc = f"{desc} {i}"
        ocr = "poor" if i < 2 else "good"
        amt = round(rng.uniform(5000, 45000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "INTERNAL_TRANSFER",
                _tags("transfer", ocr, rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )

    for desc in TRANSFER_MISS:
        amt = round(rng.uniform(8000, 35000), 2)
        cases.append(
            _case(
                next_id(),
                desc,
                amt,
                "INTERNAL_TRANSFER",
                _tags("transfer", "poor", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
                notes="account numbers only, no transfer keyword",
            )
        )

    # --- Other easy cases: 24, all stub-correct before wrong-label swaps -----
    # One of the 16 overall misses comes from the intentional junior/Renee
    # disagreement below, so do not plant an extra hard-OCR miss here.
    while sum(1 for c in cases if c["tags"]["kind"] == "other") < 24:
        i = sum(1 for c in cases if c["tags"]["kind"] == "other")
        desc, label, amt = OTHER_HIT[i % len(OTHER_HIT)]
        ocr = "poor" if i < 2 else ("fair" if i % 5 == 0 else "good")
        # Light noise only on poor rows so keywords still match.
        if ocr == "poor" and label not in ("EXPENSE",):
            desc = f"{desc} ~scan"
        elif ocr == "poor":
            desc = f"{desc} ~scan"
        cases.append(
            _case(
                next_id(),
                f"{desc}" if i < len(OTHER_HIT) else f"{desc} #{i}",
                float(amt),
                label,
                _tags("other", ocr, rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )

    # --- Intentional wrong labels (~2% = 8). Do not move the slice table. ----
    # Junior + low confidence. expected matches the stub (both wrong vs truth).
    # kind stays outside loan/transfer/settlement so measured slices hold.
    # Annotations carry Renee's correct answer. One case flips so the stub
    # agrees with Renee and the junior expected is wrong → suspect_labels.
    # Descriptions for the matching wrong labels must NOT trip OWNER_KEYS
    # (OWNER, SHAREHOLDER, MEMBER CONTRIB, CAPITAL CONTRIB) or the stub will
    # disagree with the junior and inflate overall misses.
    wrong_label_specs = [
        ("PERSONAL FUNDS FROM J. HASSAN", 12000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("J HASSAN CASH TO BUSINESS", 8000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("PARTNER EQUITY INJECTION", 25000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("FOUNDER TOP UP WIRE", 15000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("PRIVATE FUNDS INJECTION ACH", 9000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("FAMILY MONEY DEPOSIT", 11000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        ("J.HASSAN STAKE FUNDING", 7000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", False),
        # Disagreement: junior wrong, stub right via OWNER keyword.
        ("OWNER CAPITAL CONTRIBUTION Q2", 14000.0, "OPERATING_REVENUE", "OWNER_CAPITAL", True),
    ]

    # Replace 8 "other" correct cases with wrong-label variants so N stays 400.
    other_idxs = [i for i, c in enumerate(cases) if c["tags"]["kind"] == "other" and c.get("_stub") == c["expected"]["classification"]]
    assert len(other_idxs) >= 8, len(other_idxs)
    for spec, idx in zip(wrong_label_specs, other_idxs[:8]):
        desc, amt, junior_label, renee_label, stub_agrees_renee = spec
        junior = rng.choice(JUNIOR)
        annotations = [
            {
                "annotator": "renee.blackwell",
                "label": renee_label,
                "at": "2026-04-20",
                "confidence": "high",
                "note": "owner money, not revenue. we do not use that number.",
            },
            {
                "annotator": junior,
                "label": junior_label,
                "at": "2026-04-18",
                "confidence": "low",
            },
        ]
        cases[idx] = _case(
            cases[idx]["caseId"],
            desc,
            amt,
            junior_label,
            # Put the disagreement miss in poor_ocr so that slice hits ~61%.
            _tags("other", "poor" if stub_agrees_renee else "good", rng=rng),
            junior,
            "2026-04-18",
            "low",
            notes="junior label kept as expected; Renee disagrees in annotations",
            annotations=annotations,
        )
        if stub_agrees_renee:
            # Confirm stub hits Renee's label so this case is a measured miss.
            assert baseline_classify(desc, amt) == renee_label

    # Drop extras if we somehow overshot, or pad settlements if short.
    # Final count must be 400.
    # Remove temporary _stub and verify counts.
    settlements = [c for c in cases if c["tags"]["kind"] == "settlement"]
    loans = [c for c in cases if c["tags"]["kind"] == "loan"]
    transfers = [c for c in cases if c["tags"]["kind"] == "transfer"]
    others = [c for c in cases if c["tags"]["kind"] == "other"]

    # Trim/pad settlements to exactly 336.
    while len(settlements) > 336:
        # Prefer dropping a non-canon good settlement.
        for i, c in enumerate(cases):
            if c["tags"]["kind"] == "settlement" and not c["caseId"].startswith("TX-CANON"):
                cases.pop(i)
                break
        settlements = [c for c in cases if c["tags"]["kind"] == "settlement"]
    while len(settlements) < 336:
        cases.append(
            _case(
                next_id(),
                f"{rng.choice(PROCESSORS)} PAD {len(cases)}",
                round(rng.uniform(1000, 50000), 2),
                "OPERATING_REVENUE",
                _tags("settlement", "good", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )
        settlements = [c for c in cases if c["tags"]["kind"] == "settlement"]

    while len(loans) > 25:
        for i, c in enumerate(cases):
            if c["tags"]["kind"] == "loan" and not c["caseId"].startswith("TX-CANON"):
                cases.pop(i)
                break
        loans = [c for c in cases if c["tags"]["kind"] == "loan"]
    while len(transfers) > 15:
        for i, c in enumerate(cases):
            if c["tags"]["kind"] == "transfer" and not c["caseId"].startswith("TX-CANON"):
                cases.pop(i)
                break
        transfers = [c for c in cases if c["tags"]["kind"] == "transfer"]

    # Fix total to 400 by trimming/padding other.
    while len(cases) > 400:
        for i in range(len(cases) - 1, -1, -1):
            if cases[i]["tags"]["kind"] == "other" and cases[i]["confidence"] != "low":
                cases.pop(i)
                break
        else:
            cases.pop()
    while len(cases) < 400:
        cases.append(
            _case(
                next_id(),
                f"FEE MONTHLY SERVICE {len(cases)}",
                -12.0,
                "EXPENSE",
                _tags("other", "good", rng=rng),
                rng.choice(SENIOR),
                _date(rng),
                "high",
            )
        )

    assert len(cases) == 400, len(cases)
    assert sum(1 for c in cases if c["tags"]["kind"] == "settlement") == 336
    assert sum(1 for c in cases if c["tags"]["kind"] == "loan") == 25
    assert sum(1 for c in cases if c["tags"]["kind"] == "transfer") == 15

    # Stable order: canon first, then by caseId.
    canon_ids = {c[0] for c in canon}
    head = [c for c in cases if c["caseId"] in canon_ids]
    tail = sorted([c for c in cases if c["caseId"] not in canon_ids], key=lambda c: c["caseId"])
    return _strip_stub(head + tail)


def build_smoke(txn_cases: list[dict]) -> list[dict]:
    """Twenty cases for CI. Cover every txn slice, including a few hard ones."""
    by_kind: dict[str, list[dict]] = {"settlement": [], "loan": [], "transfer": [], "other": []}
    poor: list[dict] = []
    hard_loans: list[dict] = []
    hard_xfers: list[dict] = []
    for c in txn_cases:
        kind = c["tags"]["kind"]
        if kind in by_kind:
            by_kind[kind].append(c)
        if c["tags"].get("ocr_quality") == "poor":
            poor.append(c)
        if kind == "loan" and "FUNDING" in c["input"]["description"]:
            hard_loans.append(c)
        if kind == "transfer" and "TRANSFER" not in c["input"]["description"].upper() and "XFER" not in c["input"]["description"].upper() and "TRF" not in c["input"]["description"].upper() and "TFR" not in c["input"]["description"].upper():
            hard_xfers.append(c)

    picked: list[dict] = []
    seen: set[str] = set()

    def add(c: dict) -> None:
        if c["caseId"] not in seen and len(picked) < 20:
            picked.append(c)
            seen.add(c["caseId"])

    for c in txn_cases:
        if c["caseId"].startswith("TX-CANON"):
            add(c)
    for c in hard_loans[:2]:
        add(c)
    for c in hard_xfers[:2]:
        add(c)
    for c in poor:
        add(c)
        if sum(1 for p in picked if p["tags"].get("ocr_quality") == "poor") >= 5:
            break
    for c in by_kind["loan"]:
        add(c)
        if sum(1 for p in picked if p["tags"]["kind"] == "loan") >= 4:
            break
    for c in by_kind["transfer"]:
        add(c)
        if sum(1 for p in picked if p["tags"]["kind"] == "transfer") >= 3:
            break
    for c in by_kind["other"]:
        add(c)
        if sum(1 for p in picked if p["tags"]["kind"] == "other") >= 2:
            break
    for c in by_kind["settlement"]:
        add(c)

    out = []
    for i, c in enumerate(picked[:20], start=1):
        row = json.loads(json.dumps(c))
        row["caseId"] = f"SMK-{i:02d}"
        out.append(row)
    assert len(out) == 20, len(out)
    return out


def _statement_text(rows: list[tuple[str, str, float]]) -> str:
    lines = ["ACCOUNT SUMMARY", "DATE   DESCRIPTION                    AMOUNT"]
    for date, desc, amt in rows:
        sign = "+" if amt >= 0 else ""
        lines.append(f"{date}  {desc:<28} {sign}{amt:,.2f}")
    return "\n".join(lines)


def build_revenue_extraction(seed: int = 7) -> list[dict]:
    """~120 bank statement → revenue cases."""
    rng = random.Random(seed)
    cases: list[dict] = []

    # CANON statement: naive total 252400, operating 147400.
    canon_rows = [
        ("05/04", "STRIPE PAYOUT", 48230.0),
        ("05/06", "TRANSFER FROM SAVINGS", 30000.0),
        ("05/11", "STRIPE PAYOUT", 51340.0),
        ("05/18", "FASTCAPITAL LOAN", 75000.0),
        ("05/22", "STRIPE PAYOUT", 47830.0),
    ]
    cases.append(
        {
            "caseId": "REV-CANON-01",
            "input": {"text": _statement_text(canon_rows)},
            "expected": {"operatingRevenue": 147400.0, "totalDeposits": 252400.0},
            "tags": {
                "ocr_quality": "good",
                "tenant": "NSC_DIRECT",
                "month": "2026-05",
                "has_loan": "yes",
                "has_transfer": "yes",
                "pages": "1",
            },
            "labeledBy": "renee.blackwell",
            "labeledAt": "2026-05-28",
            "confidence": "high",
            "notes": "signature example: exclude 30k transfer and 75k loan",
        }
    )

    def add_case(
        case_id: str,
        rows: list[tuple[str, str, float]],
        operating: float,
        total: float,
        tags: dict[str, str],
        labeled_by: str = "renee.blackwell",
        confidence: str = "high",
        notes: str | None = None,
    ) -> None:
        cases.append(
            {
                "caseId": case_id,
                "input": {"text": _statement_text(rows)},
                "expected": {
                    "operatingRevenue": round(operating, 2),
                    "totalDeposits": round(total, 2),
                },
                "tags": tags,
                "labeledBy": labeled_by,
                "labeledAt": _date(rng),
                "confidence": confidence,
                **({"notes": notes} if notes else {}),
            }
        )

    # Clean statements: only processor deposits.
    for i in range(40):
        rows = []
        total = 0.0
        for d in range(1, rng.randint(4, 8)):
            amt = round(rng.uniform(2000, 55000), 2)
            rows.append((f"0{d}/1{d%9}", rng.choice(PROCESSORS), amt))
            total += amt
        add_case(
            f"REV-{1000 + i}",
            rows,
            total,
            total,
            {
                "ocr_quality": "good",
                "tenant": rng.choice(TENANTS),
                "month": rng.choice(MONTHS),
                "has_loan": "no",
                "has_transfer": "no",
                "pages": "1",
            },
        )

    # Statements with a loan to exclude.
    # Most use competitor names without a LOAN token so the stub includes them
    # in operating revenue. A few use a clear LOAN keyword so clean_ocr still
    # clears the suite gate (~70%).
    for i in range(25):
        rows = []
        operating = 0.0
        total = 0.0
        for d in range(1, 5):
            amt = round(rng.uniform(3000, 40000), 2)
            rows.append((f"0{d}/0{d}", rng.choice(PROCESSORS), amt))
            operating += amt
            total += amt
        loan = round(rng.uniform(20000, 80000), 2)
        if i < 12:
            rows.append((f"0{rng.randint(1,9)}/15", rng.choice(LOAN_HIT), loan))
        else:
            rows.append((f"0{rng.randint(1,9)}/15", rng.choice(LOAN_MISS), loan))
        total += loan
        add_case(
            f"REV-{2000 + i}",
            rows,
            operating,
            total,
            {
                "ocr_quality": rng.choice(("good", "fair")),
                "tenant": rng.choice(TENANTS),
                "month": rng.choice(MONTHS),
                "has_loan": "yes",
                "has_transfer": "no",
                "pages": "1",
            },
        )

    # Statements with an internal transfer to exclude.
    for i in range(20):
        rows = []
        operating = 0.0
        total = 0.0
        for d in range(1, 4):
            amt = round(rng.uniform(4000, 35000), 2)
            rows.append((f"0{d}/0{d}", rng.choice(PROCESSORS), amt))
            operating += amt
            total += amt
        xfer = round(rng.uniform(5000, 30000), 2)
        if i < 10:
            rows.append((f"0{rng.randint(1,9)}/20", rng.choice(TRANSFER_HIT), xfer))
        else:
            rows.append((f"0{rng.randint(1,9)}/20", rng.choice(TRANSFER_MISS), xfer))
        total += xfer
        add_case(
            f"REV-{3000 + i}",
            rows,
            operating,
            total,
            {
                "ocr_quality": "good",
                "tenant": rng.choice(TENANTS),
                "month": rng.choice(MONTHS),
                "has_loan": "no",
                "has_transfer": "yes",
                "pages": "1",
            },
        )

    # Poor OCR multi-page statements.
    for i in range(20):
        rows = []
        operating = 0.0
        total = 0.0
        for d in range(1, 6):
            amt = round(rng.uniform(2500, 30000), 2)
            desc = _mangle(rng.choice(PROCESSORS), rng, hard=(i < 8 and d == 1))
            rows.append((f"0{d}/0{d}", desc, amt))
            total += amt
            # Hard-mangled first line is not operating revenue for the label
            # when the stub cannot read it; label still counts the readable ones.
            if "###" not in desc and "[ILLEGIBLE]" not in desc.upper():
                if baseline_classify(desc, amt) == "OPERATING_REVENUE":
                    operating += amt
            elif baseline_classify(desc, amt) == "OPERATING_REVENUE":
                operating += amt
        # Recompute expected from stub-visible lines so labels stay consistent
        # with what a careful human would count from the readable text.
        operating = 0.0
        for _date_s, desc, amt in rows:
            if amt > 0 and baseline_classify(desc, amt) == "OPERATING_REVENUE":
                # For poor OCR teaching cases, expected still wants the true
                # processor totals when the mangling is light. Hard garbage
                # lines are excluded from operating revenue.
                if "###" in desc or "[ILLEGIBLE]" in desc.upper():
                    continue
                operating += amt
        add_case(
            f"REV-{4000 + i}",
            rows,
            operating,
            total,
            {
                "ocr_quality": "poor",
                "tenant": rng.choice(TENANTS),
                "month": rng.choice(MONTHS),
                "has_loan": "no",
                "has_transfer": "no",
                "pages": "2" if i % 2 == 0 else "3",
            },
            confidence="medium",
        )

    # Loan + transfer together (like canon), a few more.
    for i in range(14):
        rows = []
        operating = 0.0
        total = 0.0
        for d in range(1, 4):
            amt = round(rng.uniform(5000, 45000), 2)
            rows.append((f"0{d}/0{d}", rng.choice(PROCESSORS), amt))
            operating += amt
            total += amt
        loan = round(rng.uniform(25000, 90000), 2)
        xfer = round(rng.uniform(8000, 40000), 2)
        if i < 10:
            rows.append(("04/10", LOAN_HIT[i % len(LOAN_HIT)], loan))
            rows.append(("04/12", TRANSFER_HIT[i % len(TRANSFER_HIT)], xfer))
        else:
            rows.append(("04/10", LOAN_MISS[i % len(LOAN_MISS)], loan))
            rows.append(("04/12", TRANSFER_MISS[i % len(TRANSFER_MISS)], xfer))
        total += loan + xfer
        add_case(
            f"REV-{5000 + i}",
            rows,
            operating,
            total,
            {
                "ocr_quality": "good",
                "tenant": rng.choice(TENANTS),
                "month": rng.choice(MONTHS),
                "has_loan": "yes",
                "has_transfer": "yes",
                "pages": "1",
            },
        )

    assert len(cases) >= 115, len(cases)
    # Trim to ~120.
    cases = cases[:120]
    assert len(cases) == 120
    return cases


POLICY_DOCS = {
    "credit-policy-2024.pdf": {
        "id": "credit-policy-2024.pdf",
        "title": "Northstar Credit Policy 2024",
        "text": (
            "Maximum unsecured advance rate is 1.5x average monthly revenue. "
            "Debt service coverage minimum is 1.25. Effective through 2024."
        ),
        "answer": "1.5x average monthly revenue",
    },
    "credit-policy-2025.pdf": {
        "id": "credit-policy-2025.pdf",
        "title": "Northstar Credit Policy 2025",
        "text": (
            "Maximum unsecured advance rate is 1.75x average monthly revenue. "
            "Debt service coverage minimum is 1.20. Effective 2025-01-01."
        ),
        "answer": "1.75x average monthly revenue",
    },
    "credit-policy-FINAL.pdf": {
        "id": "credit-policy-FINAL.pdf",
        "title": "Credit Policy FINAL",
        "text": (
            "Current credit policy. Maximum unsecured advance rate for average "
            "monthly revenue under current credit policy is 2.0x average monthly "
            "revenue. Maximum unsecured advance rate. FINAL version."
        ),
        "answer": "2.0x average monthly revenue (draft, do not use)",
    },
    "credit-policy-FINAL2.pdf": {
        "id": "credit-policy-FINAL2.pdf",
        "title": "Credit Policy FINAL2",
        "text": (
            "2025 reprint missing appendix C. Advance rate 1.75x. "
            "Appendix C on personal guarantee rules is absent."
        ),
        "answer": "1.75x, appendix C missing",
    },
    "credit-policy-2026.pdf": {
        "id": "credit-policy-2026.pdf",
        "title": "Northstar Credit Policy 2026",
        "text": (
            "Maximum unsecured advance rate is 2.0x average monthly revenue. "
            "Effective 2026-03-01. Do not apply before that date."
        ),
        "answer": "2.0x average monthly revenue after 2026-03-01",
    },
    "California-overlay.pdf": {
        "id": "California-overlay.pdf",
        "title": "California Lending Overlay",
        "text": (
            "CASCADE tenant only. California applicants require a 1.35 DSC "
            "floor and a state-specific adverse action template."
        ),
        "answer": "1.35 DSC floor for CASCADE California applicants",
    },
    "SBA-overlay.pdf": {
        "id": "SBA-overlay.pdf",
        "title": "SBA 7(a) Program Overlay",
        "text": (
            "For SBA 7(a) product, SBA overlay beats base policy. "
            "Personal guarantee required above $50,000. Use SBA forms."
        ),
        "answer": "personal guarantee required above $50,000",
    },
    "grants-program-addendum.docx": {
        "id": "grants-program-addendum.docx",
        "title": "State Grants Program Addendum",
        "text": (
            "State grant proceeds are not operating revenue for DSCR. "
            "Exclude them from the twelve month average."
        ),
        "answer": "exclude state grant proceeds from operating revenue",
    },
}


def build_policy_qa(seed: int = 11) -> list[dict]:
    """~80 policy questions with citation traps."""
    rng = random.Random(seed)
    cases: list[dict] = []

    def docs(*names: str) -> list[dict]:
        return [POLICY_DOCS[n] for n in names]

    # Straightforward: one obvious document.
    for i in range(25):
        name = rng.choice(
            [
                "credit-policy-2025.pdf",
                "grants-program-addendum.docx",
                "SBA-overlay.pdf",
            ]
        )
        d = POLICY_DOCS[name]
        cases.append(
            {
                "caseId": f"PQ-{1000 + i}",
                "input": {
                    "question": f"According to {d['title']}, what is the rule? {d['text'][:60]}",
                    "documents": docs(name),
                },
                "expected": {"citation": name, "answer": d["answer"]},
                "tags": {
                    "tenant": rng.choice(TENANTS),
                    "product": rng.choice(("TERM", "LOC", "SBA_7A")),
                    "trap": "none",
                },
                "labeledBy": rng.choice(SENIOR),
                "labeledAt": _date(rng),
                "confidence": "high",
            }
        )

    # Superseded trap: FINAL draft looks closest by wording.
    for i in range(15):
        cases.append(
            {
                "caseId": f"PQ-{2000 + i}",
                "input": {
                    "question": (
                        "What is the maximum unsecured advance rate for average "
                        "monthly revenue under current credit policy?"
                    ),
                    "documents": docs(
                        "credit-policy-FINAL.pdf",
                        "credit-policy-2025.pdf",
                        "credit-policy-2024.pdf",
                    ),
                },
                "expected": {
                    "citation": "credit-policy-2025.pdf",
                    "answer": "1.75x average monthly revenue",
                },
                "tags": {
                    "tenant": "NSC_DIRECT",
                    "product": "TERM",
                    "trap": "superseded",
                },
                "labeledBy": "renee.blackwell",
                "labeledAt": _date(rng),
                "confidence": "high",
                "notes": "FINAL is a 2023 draft. 2025 is in effect.",
            }
        )

    # Tenant scope: California overlay only for CASCADE.
    for i in range(12):
        tenant = "NSC_DIRECT" if i % 2 == 0 else "CASCADE"
        citation = (
            "California-overlay.pdf"
            if tenant == "CASCADE"
            else "credit-policy-2025.pdf"
        )
        answer = (
            POLICY_DOCS["California-overlay.pdf"]["answer"]
            if tenant == "CASCADE"
            else "1.75x average monthly revenue"
        )
        cases.append(
            {
                "caseId": f"PQ-{3000 + i}",
                "input": {
                    "question": (
                        "What DSC floor applies to a California applicant for "
                        "this tenant?"
                    ),
                    "documents": docs(
                        "California-overlay.pdf",
                        "credit-policy-2025.pdf",
                    ),
                },
                "expected": {"citation": citation, "answer": answer},
                "tags": {
                    "tenant": tenant,
                    "product": "TERM",
                    "trap": "tenant_scope",
                },
                "labeledBy": "doug.feinberg",
                "labeledAt": _date(rng),
                "confidence": "high",
            }
        )

    # Effective date: 2026 policy exists but is not in force yet.
    for i in range(12):
        cases.append(
            {
                "caseId": f"PQ-{4000 + i}",
                "input": {
                    "question": (
                        "As of February 2026, what maximum unsecured advance "
                        "rate should underwriting use?"
                    ),
                    "documents": docs(
                        "credit-policy-2026.pdf",
                        "credit-policy-2025.pdf",
                    ),
                },
                "expected": {
                    "citation": "credit-policy-2025.pdf",
                    "answer": "1.75x average monthly revenue",
                },
                "tags": {
                    "tenant": "NSC_DIRECT",
                    "product": "LOC",
                    "trap": "effective_date",
                },
                "labeledBy": "doug.feinberg",
                "labeledAt": _date(rng),
                "confidence": "high",
                "notes": "2026 policy effective 2026-03-01 only",
            }
        )

    # Product overlay: SBA beats everything for SBA 7(a).
    for i in range(16):
        cases.append(
            {
                "caseId": f"PQ-{5000 + i}",
                "input": {
                    "question": (
                        "For an SBA 7(a) deal, when is a personal guarantee "
                        "required?"
                    ),
                    "documents": docs(
                        "SBA-overlay.pdf",
                        "credit-policy-2025.pdf",
                        "credit-policy-FINAL.pdf",
                    ),
                },
                "expected": {
                    "citation": "SBA-overlay.pdf",
                    "answer": "personal guarantee required above $50,000",
                },
                "tags": {
                    "tenant": rng.choice(TENANTS),
                    "product": "SBA_7A",
                    "trap": "product_overlay",
                },
                "labeledBy": "renee.blackwell",
                "labeledAt": _date(rng),
                "confidence": "high",
            }
        )

    assert len(cases) == 80, len(cases)
    return cases


def write_jsonl(path: Path, cases: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {path} ({len(cases)} cases)")


def main() -> int:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    txn = build_txn_classification()
    write_jsonl(GOLDEN / "txn-classification-v3.jsonl", txn)
    write_jsonl(GOLDEN / "smoke.jsonl", build_smoke(txn))
    write_jsonl(GOLDEN / "revenue-extraction-v2.jsonl", build_revenue_extraction())
    write_jsonl(GOLDEN / "policy-qa-v1.jsonl", build_policy_qa())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
