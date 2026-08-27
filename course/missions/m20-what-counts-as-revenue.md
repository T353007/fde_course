---
id: M20
slug: what-counts-as-revenue
title: What Counts as Revenue
subtitle: "Five transactions. A naive sum of 252,400. The real number is 147,400. Renee saw it in two seconds."
phase: 4
order: 20
duration: 300
difficulty: 4
lab: true
status: complete
objectives:
  - Build a hybrid pipeline where the model classifies and code adds
  - Reproduce the CANON statement end to end and land on 147,400
  - Show why overall accuracy of 96 percent still fails the cases that move money
  - Defend the boundary to a stakeholder who wants the model to "just do the math"
concepts: [hybrid pipelines, operating revenue, classification, deterministic arithmetic, eval slices]
competencies: [coding, evals, fintech-judgment, ai-fundamentals]
prereqs: [M19]
---

## Where you are

Intake no longer clones documents. OCR no longer ships confident garbage as done.
Now you have to answer the question the whole engagement was scoped around.

How much money does this business actually make.

## The request

:::evidence{type=email label="Marcus Webb, subject: revenue demo Friday?"}
```text
Can we show Dale the AI pulling revenue off a real statement Friday?

I told him we were close. I may have set expectations a little. Just need the
number to look right on one clean example.

Marcus
```
:::

One clean example is how this always starts. The clean example is also where the
course has been pointing since Mission 01.

## The conversation

:::dialogue{title="Renee's desk, Thursday 10:20 AM"}
**You:** I brought the May statement for Coastal Supply.

**Renee:** Put it up.

*You put the five lines on the shared screen.*

**Renee:** 252,400.

**You:** That is what the system says.

**Renee:** We don't use that number.

**You:** What do you use?

**Renee:** 147,400. The transfer and the Fastcapital loan are not revenue.

*Two seconds. She did not open a calculator.*
:::

:::dialogue{title="Same desk, thirty seconds later"}
**You:** How do you know the Fastcapital line is a loan?

**Renee:** Because it says Fastcapital Loan. Also because every merchant who is
shopping us is shopping them. Also because loan proceeds are not earned from
customers.

**You:** And the transfer?

**Renee:** TRANSFER FROM SAVINGS. Same owner. Money moved rooms. It did not get
earned.

**You:** Where is that written down?

**Renee:** In the spreadsheet. And in my head. Not in the Java.
:::

She is right. You already saw the TODO in `RevenueCalculator` back in Mission 09.
Jan Kowalski left in 2021. The decision from credit policy never came. The function
still sums every credit.

## What you know about the system

The bank statement, the signature example of the course, is exactly these five lines:

```text
05/04  STRIPE PAYOUT                    +48,230
05/06  TRANSFER FROM SAVINGS            +30,000
05/11  STRIPE PAYOUT                    +51,340
05/18  FASTCAPITAL LOAN                 +75,000
05/22  STRIPE PAYOUT                    +47,830
```

Naive total of credits: **252,400**

Correct operating revenue: **147,400**

Exclude the internal transfer of 30,000 and the loan proceeds of 75,000.

`ai-service` already has the endpoint shape. `POST /v1/classify/transactions` asks the
model for a label per line. Python adds the ones labeled `OPERATING_REVENUE`. The
model never sees a total field in the schema on purpose.

The eval slice table from Mission 16 still holds:

```text
Overall accuracy ............................... 96.0%
  loan proceeds ................................ 68%
  poor OCR quality ............................. 61%
  internal transfers ........................... 73%
  standard card settlements .................... 99%
```

Ninety six percent is real. It is also mostly the easy 84 percent of volume. The
failing slices are the ones that move an approval by five figures.

## The code

Read this file. The comment at the top is the mission.

```python
"""POST /v1/classify/transactions

This is the endpoint the whole course points at, so read the boundary rule first.

    The model classifies. Python does the arithmetic.

Not "mostly". Not "except for the easy sums". The model is given a list of
transactions and asked for one label per transaction. It is never asked for a
total, an average, or a difference. Then compute_totals() below, which is plain
Python with Decimal, adds up the ones labeled OPERATING_REVENUE.
"""
```

And the function that does the money:

```python
def compute_totals(
    transactions: list[TransactionInput],
    classifications: list[TransactionClassification],
    months: int | None = None,
) -> RevenueTotals:
    """Add up the money. No model involved, no network, fully unit testable.

    On the canonical May statement from CANON.md those two numbers are 252,400
    and 147,400. The 105,000 gap is one internal transfer of 30,000 and one
    Fastcapital loan deposit of 75,000. Renee spots it in two seconds and the
    system has never once caught it.
    """
    by_index = {c.index: c for c in classifications}

    naive_total = Decimal("0")
    operating = Decimal("0")
    excluded: list[ExcludedTransaction] = []

    for index, txn in enumerate(transactions):
        amount = Decimal(txn.amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        if amount <= 0:
            continue

        naive_total += amount

        classification = by_index.get(index)
        category = (
            classification.classification
            if classification is not None
            else TransactionCategory.UNKNOWN
        )

        if category in REVENUE_CATEGORIES:
            operating += amount
            continue

        excluded.append(
            ExcludedTransaction(
                index=index,
                description=txn.description,
                amount=amount,
                classification=category,
                reason=classification.reason if classification else "No classification returned.",
            )
        )

    # ... monthly average when months is set ...
    return RevenueTotals(
        naive_total_credits=naive_total,
        operating_revenue=operating,
        excluded_total=(naive_total - operating),
        excluded=excluded,
        months=months,
        monthly_operating_revenue=monthly,
        computed_by="python",
    )
```

Notice what the model is not allowed to touch. No amount field on
`TransactionClassification`. No total in `ClassificationModelOutput`. The model picks
a label. Code keeps the dollars.

## Evidence

:::evidence{type=spreadsheet label="revenue_check_v7_FINAL.xlsx, rows Renee uses on this statement"}
```text
rule_id  rule
R-02     Internal transfers between owner accounts are not operating revenue
R-04     Loan proceeds, MCA deposits, and line draws are not operating revenue
R-07     Card settlement payouts (Stripe, Square, PayPal) count as operating revenue
R-11     When description names a competitor lender, flag for existing debt review
```
:::

:::evidence{type=http label="POST /v1/classify/transactions, Coastal Supply May statement"}
```bash
curl -s http://localhost:8000/v1/classify/transactions \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m20-coastal' \
  -d '{
    "applicationId": "84412",
    "transactions": [
      {"date": "2026-05-04", "description": "STRIPE PAYOUT", "amount": "48230.00"},
      {"date": "2026-05-06", "description": "TRANSFER FROM SAVINGS", "amount": "30000.00"},
      {"date": "2026-05-11", "description": "STRIPE PAYOUT", "amount": "51340.00"},
      {"date": "2026-05-18", "description": "FASTCAPITAL LOAN", "amount": "75000.00"},
      {"date": "2026-05-22", "description": "STRIPE PAYOUT", "amount": "47830.00"}
    ]
  }'
```
```json
{
  "classifications": [
    {"index": 0, "classification": "OPERATING_REVENUE", "reason": "Card settlement payout"},
    {"index": 1, "classification": "INTERNAL_TRANSFER", "reason": "Transfer from savings"},
    {"index": 2, "classification": "OPERATING_REVENUE", "reason": "Card settlement payout"},
    {"index": 3, "classification": "LOAN_PROCEEDS", "reason": "Named loan deposit from Fastcapital"},
    {"index": 4, "classification": "OPERATING_REVENUE", "reason": "Card settlement payout"}
  ],
  "totals": {
    "naiveTotalCredits": "252400.00",
    "operatingRevenue": "147400.00",
    "excludedTotal": "105000.00",
    "excluded": [
      {"index": 1, "amount": "30000.00", "classification": "INTERNAL_TRANSFER"},
      {"index": 3, "amount": "75000.00", "classification": "LOAN_PROCEEDS"}
    ],
    "computedBy": "python"
  }
}
```
:::

Put that response next to Sam's Java path.

:::evidence{type=sql label="What underwriting stores today for the same application"}
```sql
SELECT application_id, average_monthly_revenue, calc_version
FROM northstar.decisions
WHERE application_id = 84412;
```
```text
 application_id | average_monthly_revenue | calc_version
----------------+-------------------------+--------------
          84412 |               252400.00 | java-v1-all-credits
```
:::

Same five lines. Two numbers. One of them funds the wrong story about the business.

:::evidence{type=metrics label="make eval SUITE=txn-classification"}
```text
slice                  n    accuracy
overall              500      0.960
loan_proceeds         48      0.680
internal_transfer     52      0.730
poor_ocr              61      0.610
card_settlement      420      0.990
```
:::

If you only report overall, Friday's demo looks like a win. If you report the loan
proceeds slice, Friday's demo is the beginning of the real work.

## What you do not know

- Whether Renee and the junior who labeled part of the golden set agree on every edge
  case. About 2 percent of labels are wrong on purpose in the set. At least one of
  those is a Renee-versus-junior disagreement where Renee is right.
- Whether Dale can hear "96 percent overall, 68 percent on loan proceeds" without
  hearing "the AI is broken."
- Whether Janet will let you call into underwriting-service from ai-service this week,
  or only expose a comparison panel in the reviewer portal.

## Your task

:::task{time="150 min"}
1. Run the five transaction statement through `/v1/classify/transactions` with
   `LLM_PROVIDER=stub`. Confirm `operatingRevenue` is 147400.00 and
   `naiveTotalCredits` is 252400.00.
2. Write or extend unit tests for `compute_totals` that lock those two numbers in.
3. Run `make eval SUITE=txn-classification` and paste the slice table into your notes.
4. Build a side by side view Renee can check in ninety seconds: Java number, hybrid
   number, excluded lines with reasons.
5. Do not ask the model for a total. If you find a code path that still does, flag it
   and leave it alone for Mission 21.
:::

## Stop and think

:::stopandthink
1. If the model mislabels the Fastcapital line as OPERATING_REVENUE, who can explain
   the approval to the applicant in writing?
2. Why is "the model added it up correctly this time" not good enough?
3. Which slice would you put on slide one for Dale, and which would you put on slide
   two?

Write before you scroll.
:::

## Working through it

### Lock the arithmetic

```python
def test_coastal_supply_may_statement():
    txns = [
        TransactionInput(date="2026-05-04", description="STRIPE PAYOUT", amount=Decimal("48230")),
        TransactionInput(date="2026-05-06", description="TRANSFER FROM SAVINGS", amount=Decimal("30000")),
        TransactionInput(date="2026-05-11", description="STRIPE PAYOUT", amount=Decimal("51340")),
        TransactionInput(date="2026-05-18", description="FASTCAPITAL LOAN", amount=Decimal("75000")),
        TransactionInput(date="2026-05-22", description="STRIPE PAYOUT", amount=Decimal("47830")),
    ]
    labels = [
        TransactionClassification(index=0, classification=TransactionCategory.OPERATING_REVENUE),
        TransactionClassification(index=1, classification=TransactionCategory.INTERNAL_TRANSFER),
        TransactionClassification(index=2, classification=TransactionCategory.OPERATING_REVENUE),
        TransactionClassification(index=3, classification=TransactionCategory.LOAN_PROCEEDS),
        TransactionClassification(index=4, classification=TransactionCategory.OPERATING_REVENUE),
    ]
    totals = compute_totals(txns, labels)
    assert totals.naive_total_credits == Decimal("252400.00")
    assert totals.operating_revenue == Decimal("147400.00")
    assert totals.excluded_total == Decimal("105000.00")
    assert totals.computed_by == "python"
```

If this test fails, the course is wrong. If a future change makes the model emit a
total field, this test still protects the money path.

### The wrong turn: let the model do the sum

There is already a counterexample in the same file. `_legacy_revenue_summary()` asks
the model for `averageRevenue`. It exists because February's demo path asked for a
single number and Marcus liked how fast it looked.

You will be tempted to use it for Friday. One call, one number, Dale nods. Do not.

:::dialogue{title="Nadia, Slack, Thursday 3:40 PM"}
**Nadia:** What would have to be true for the model doing the arithmetic to be the
answer?

**You:** It would have to be right every time, and we would have to explain every
miss.

**Nadia:** And can you explain a miss when the only artifact is a number?

**You:** No. You get a number. You do not get the two lines that should have been
out.

**Nadia:** So what do you show Dale?

**You:** The three Stripe lines in. The transfer and the loan out. Then the sum in
Python.
:::

Friday's demo is a classification story with a calculator at the end. It is slower to
narrate. It is the only version Doug can defend in an adverse action letter.

### Show Renee the work

Build a small panel in the reviewer portal, or a local HTML fixture if Wendy is mid
sprint. Three columns:

| Line | Hybrid label | Counts? |
|---|---|---|
| STRIPE PAYOUT 48,230 | OPERATING_REVENUE | yes |
| TRANSFER FROM SAVINGS 30,000 | INTERNAL_TRANSFER | no |
| STRIPE PAYOUT 51,340 | OPERATING_REVENUE | yes |
| FASTCAPITAL LOAN 75,000 | LOAN_PROCEEDS | no |
| STRIPE PAYOUT 47,830 | OPERATING_REVENUE | yes |

Footer: Java 252,400. Hybrid 147,400. Excluded 105,000.

:::dialogue{title="Renee reviews the panel"}
**Renee:** That is the number.

**You:** And the Fastcapital flag?

**Renee:** Section 12. Existing debt. Even when it is not on the bureau yet. Your
label is right. The underwriter still has to pull the payoff.

**You:** So we should not auto decline on that label.

**Renee:** Correct. We should not auto approve on 252,400 either. We have been doing
that by accident for years.
:::

### What about the 96 percent

When you put the eval table next to the statement, the shape of the lie becomes clear.
Card settlements are 99 percent and most of the volume. Loan proceeds are 68 percent
and decide whether you are looking at a healthy merchant or a stacked borrower.

Your job on Friday is not to hide the 68. Your job is to put it where Dale can act on
it. Slide one: Coastal Supply, 252,400 versus 147,400, two excluded lines. Slide two:
slice table, and the sentence "we are measuring the hard cases on purpose."

## Tests

Besides the Coastal Supply unit test, add a property style check that the model cannot
change the dollars:

```python
def test_model_cannot_mutate_amounts(monkeypatch):
    txns = [TransactionInput(description="STRIPE PAYOUT", amount=Decimal("48230"))]
    # Even if a buggy classifier returns a mirrored amount in reason text,
    # operating revenue still comes from the input list.
    labels = [
        TransactionClassification(
            index=0,
            classification=TransactionCategory.OPERATING_REVENUE,
            reason="amount looks like 99999",
        )
    ]
    totals = compute_totals(txns, labels)
    assert totals.operating_revenue == Decimal("48230.00")
```

Run:

```bash
cd lab/ai-service && pytest tests/test_compute_totals.py -q
make eval SUITE=txn-classification
```

## Then this happens

After the demo, a junior underwriter pings you. Case TX-10088 in the golden set. The
junior labeled a "WIRE FROM OWNER" as OPERATING_REVENUE. Renee labeled it
OWNER_CONTRIBUTION. The eval currently scores the junior's label as expected.

:::evidence{type=test label="TX-10088"}
```json
{
  "caseId": "TX-10088",
  "input": {"description": "WIRE FROM OWNER ****2291", "amount": 25000},
  "expected": {"classification": "OPERATING_REVENUE"},
  "tags": {"kind": "transfer", "ocr_quality": "good"},
  "labeledBy": "jordan.lee",
  "confidence": "low"
}
```
:::

## Tracking it down

This is the 2 percent. Low confidence junior label. Renee is right. Owner wires are
not earned revenue. If you "fix" the model to match the golden set here, you teach it
the wrong rule.

Open a label defect note. Do not silently flip the expected value in a hurry before
Friday. Bring Renee the row. Change the label with her initials in `labeledBy` after
she agrees. Evals are only as honest as the people who marked them.

## The better version

The hybrid pipeline is now the path you will defend for the rest of the course:

1. OCR and extraction produce lines with amounts from the document.
2. The model classifies each line.
3. Python sums `OPERATING_REVENUE`.
4. The response carries naive total, operating total, and the excluded rows with
   reasons.
5. Underwriting and Doug can read the reasons without asking the model to remember
   what it did.

Mission 21 is about the next pressure: Marcus will want more of that pipeline to be
"AI." Your job is to know which steps must stay code.

:::judgment
**The model should never do the arithmetic.**

Not because models cannot add. Sometimes they can. Because a lending decision needs a
trail that names the two deposits that did not count, and a sum you can unit test
without a GPU. Classification is judgment. Addition is a fact. Put judgment where the
model is strong. Put facts in code.

The signature statement is small on purpose. Five lines. Anyone can add them. The
point is not the difficulty of the math. The point is that 252,400 and 147,400 are
both defensible looking numbers until you force the system to show its work. Renee
already showed her work. The software is catching up.
:::

:::commslab
#### To Renee

> Coastal Supply comes out at 147,400 with the transfer and the Fastcapital loan
> excluded. I want you to break the next ten statements the same way before we call
> this done. Also TX-10088 looks mislabeled. Can I walk it with you for five minutes?

#### To Dale

> On the sample statement the old system reports 252,400. Operating revenue is
> 147,400 once we remove an internal transfer and a Fastcapital loan. That gap is the
> product. Overall model accuracy is 96 percent. On loan proceeds it is 68 percent,
> and that is the slice we are improving next.

#### To Marcus

> Friday works if we show the excluded lines, not only the final number. If we only
> show the number, we are back to a black box Dale cannot defend to the board.

#### To Doug

> Every excluded deposit carries a classification and a reason string. If you need
> that language in an adverse action notice, we can map reason codes to your letter
> templates next. The model does not invent the total.
:::

## Practice

Different domain, same skill.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

An auto insurer prices renewal premiums using "annual miles driven." The mobile app
estimates miles from GPS. A legacy batch job sums raw trip lengths. A new model reads
trip summaries in English ("short commute", "weekend road trip") and outputs a single
annual miles number.

What you learn:

- Raw GPS sum for one driver: 11,400 miles.
- After removing trips that were the driver's spouse on a shared phone: 9,100.
- The model, asked for annual miles, returns 9,000 "approximately" on most runs and
  11,200 on others.
- Actuaries need a reproducible number for rate filings.
- Fraud wants a list of excluded trips with reasons, not a vibes total.
- Leadership wants "AI powered mileage" on a launch slide.

**Your task**

1. Where does the model belong in this pipeline?
2. What does code compute?
3. What do you put on the launch slide so leadership gets the AI story without
   shipping a non reproducible rate input?
4. Name the wrong turn.

---

**Notes, after you have written yours**

The model classifies trips: driver, spouse, commercial use, unclear. Code sums the
miles on trips labeled driver. The filing packet includes the excluded trips and the
rule ids. The launch slide shows a sample driver with three excluded spouse trips and
a stable total of 9,100. The wrong turn is asking the model for the annual miles
number directly because it photographs better. That path cannot survive a rate filing
or a fraud review, and it will drift run to run.
:::

The lesson in one sentence: classify with the model, add with code, and put both
totals on screen so a human can see the 105,000 that used to hide inside one number.
