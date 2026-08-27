---
id: M14
slug: it-made-up-a-number
title: It Made Up a Number
subtitle: "The EIN field was blank in the document. The model returned an EIN. It is well formed and it belongs to nobody."
phase: 3
order: 14
duration: 210
difficulty: 3
lab: true
status: complete
objectives:
  - Reproduce a hallucinated field with the stub scenario and prove the source text never contained it
  - Separate prompt instructions from system guarantees for missing fields
  - Add null paths, provenance, and source validation so a blank EIN stays blank
  - Explain to fraud and compliance why a well formed wrong EIN is worse than a null
concepts: [hallucination, abstention, provenance, missing data, null paths, field validation]
competencies: [ai-fundamentals, coding, fintech-judgment]
prereqs: [M13]
---

## Where you are

Mission 13 got you real JSON. Schema mode and typed failures are in. Tomás stopped
retrying 422s. Wendy wired the classify endpoint into a rough reviewer screen.

Marcus wants the next demo to pull fields off a statement page: account holder, period,
and EIN when it is there. Extraction already exists. You have not looked hard at what
it does when a field is missing.

Today that is the whole problem.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:08 AM"}
```text
Marcus:  can we show extraction tomorrow. business name + EIN + a few lines
Marcus:  Dale likes concrete fields

You:    same endpoint we already have. I'll run a clean statement through it.

Ada:     if you are putting EINs in a model response I want to see the cases
         where the page does not have one
Ada:     assume the applicant is hostile
```
:::

Ada runs fraud. She did not ask for a demo. She asked for the blank case.

## The conversation

:::dialogue{title="Ada Nwosu, fraud bay, Wednesday 9:40 AM"}
**Ada:** Show me a statement with no EIN on it.

**You:** Most of the seed set has one. I can find a blank.

**Ada:** Find a blank. Run extraction. Tell me what comes back.

**You:** If it is blank it should come back null. The prompt says that.

**Ada:** The prompt says that.

*She waits.*

**Ada:** Assume the applicant is hostile. Assume the model is helpful. Helpful is the
failure mode.
:::

## What you know about the system

`POST /v1/extract/bank-statement` takes OCR text and returns a
`BankStatementExtraction`. The schema already allows `ein` to be null.

```python
# lab/ai-service/ai_service/schemas.py  (excerpt)
class BankStatementExtraction(ApiModel):
    account_holder: str | None = None
    statement_period: StatementPeriod = Field(default_factory=StatementPeriod)
    # Blank in the source more often than not. A model that fills this in from
    # nowhere is the Mission 14 problem.
    ein: str | None = None
    transactions: list[ExtractedTransaction] = Field(default_factory=list)
    ocr_confidence: float | None = None
    notes: str | None = None
```

The prompt already tells the model not to invent fields.

```text
# lab/ai-service/ai_service/prompts/bank_extract_v2.txt  (rules 1-2)
1. Copy values exactly as they appear. Do not round and do not reformat numbers
   beyond removing commas and currency symbols.
2. If a field is not on the page, use null. Do not guess an EIN, a business
   name, or a date. A blank EIN is a correct answer.
```

The stub provider has a scenario built for this mission. You flip it with a header.

| Scenario | Behavior |
|---|---|
| `default` | recorded good path |
| `hallucinated-ein` | invents an EIN that was blank in the source |

Mission 13 already warned you: under strict schema mode, a model that wants to refuse
has no clean way to refuse. It fills something in. That something can look perfect.

## Evidence

Here is a short statement page from the seed set. Search it yourself. There is no EIN.

:::evidence{type=http label="OCR text for APP-10442, page 1"}
```text
NORTHSTAR BUSINESS CHECKING
Statement Period: 04/01/2026 - 04/30/2026
Account Holder: Harbor Pine Supply LLC
Account Number: ****4419

Date        Description                         Amount
04/03       STRIPE PAYOUT                       12,440.00
04/11       STRIPE PAYOUT                       11,890.00
04/18       TRANSFER FROM SAVINGS ****1221      8,000.00
04/22       STRIPE PAYOUT                       13,210.00

Ending balance                                  47,882.11
```
:::

No `EIN`, no `Tax ID`, no `Federal ID`. Harbor Pine's applicant row in the database also
has `ein` null. That is intentional in the seed.

Now call extract with the stub scenario Ada cares about.

```bash
# from lab/
export LLM_PROVIDER=stub

curl -s localhost:8000/v1/extract/bank-statement \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m14-0001' \
  -H 'X-Stub-Scenario: hallucinated-ein' \
  -d @- <<'EOF' | jq '{ein: .extraction.ein, holder: .extraction.account_holder, meta: .meta}'
{
  "document_text": "NORTHSTAR BUSINESS CHECKING\nStatement Period: 04/01/2026 - 04/30/2026\nAccount Holder: Harbor Pine Supply LLC\nAccount Number: ****4419\n\nDate        Description                         Amount\n04/03       STRIPE PAYOUT                       12,440.00\n04/11       STRIPE PAYOUT                       11,890.00\n04/18       TRANSFER FROM SAVINGS ****1221      8,000.00\n04/22       STRIPE PAYOUT                       13,210.00\n\nEnding balance                                  47,882.11",
  "document_id": "DOC-10442-1",
  "application_id": "APP-10442"
}
EOF
```

:::evidence{type=http label="response under hallucinated-ein"}
```json
{
  "ein": "82-4719385",
  "holder": "Harbor Pine Supply LLC",
  "meta": {
    "model": "stub-recorded",
    "prompt_version": "bank_extract_v2",
    "finish_reason": "stop",
    "prompt_tokens": 412,
    "completion_tokens": 186,
    "latency_ms": 840,
    "cost_usd": 0.0
  }
}
```
:::

HTTP 200. Valid JSON. Schema happy. EIN looks like an EIN. `82-4719385` is well formed
and it belongs to nobody in this lab, and it is not on the page.

:::dialogue{title="Ada, looking at your screen"}
**Ada:** So it invented a tax ID.

**You:** The prompt says not to.

**Ada:** And yet.

**You:** I can strengthen the wording.

**Ada:** Can you.

*She points at rule 2 on the prompt file you already have open.*

**Ada:** That sentence is already there. Adding another sentence that says the same
thing is not a control. It is a wish.
:::

## What you do not know

- How often blank EINs appear in real Northstar volume.
- Whether downstream code treats a present EIN as verified identity.
- Whether Doug will accept "the model usually leaves it blank" as a control.
- Whether the invented number collides with a real business somewhere outside the lab.

## Your task

:::task{time="90 min"}
1. Reproduce the Harbor Pine case with `X-Stub-Scenario: hallucinated-ein`. Save the
   raw response under `customers/northstar/notes/m14-hallucinated-ein.json`.
2. Write a check that proves the returned EIN string does not appear anywhere in the
   source document text. Fail loud when it does not.
3. Open `routes/extract.py`. Find the comment that says there is no check that a
   returned EIN appears in the source. That gap is the work.
4. Do **not** start by editing the prompt. You will try that path later on purpose, and
   it will fail for a reason you need to feel.
5. Design a response shape where a missing field is an explicit abstention, not a
   lucky null. Write the design in `customers/northstar/notes/m14-null-path.md`
   before you code.
:::

:::stopandthink
1. The prompt already forbids guessing. The model still returned an EIN. What does that
   tell you about prompt text as a safety control?
2. Which is worse for Northstar: `ein: null`, or `ein: "82-4719385"` when the page is
   blank? Say why in one sentence Ada would accept.
3. Mission 13 forced valid JSON with a schema. How does that change the model's options
   when the honest answer is "I do not know"?
4. If you only add "Do not make up values" to the prompt, which failure mode stays
   open?

Write the four answers before you scroll. Ada will ask question 2 out loud.
:::

## Working through it

### The wrong turn: ask nicer

You do it anyway, because it is the first thing every engineer does.

```python
# lab/ai-service/ai_service/prompts/bank_extract_v2.py   # the edit you almost ship
EXTRA_RULE = """
5. Do not make up values. If a field is absent, return null. Never invent an EIN.
"""
```

Re-run with the same scenario.

:::evidence{type=http label="after the prompt tweak, same stub scenario"}
```json
{
  "ein": "82-4719385",
  "notes": "EIN taken from business records when not printed on statement."
}
```
:::

The stub scenario does not care about your new sentence. That is the point of the
fixture. A real model also does not treat English prohibitions as hard gates. You spent
twenty minutes proving a control that was never a control.

Revert the prompt change. Keep rule 2 as it is. Move the guarantee into code.

### Null paths and abstention

A null that means "we looked and it was not there" is useful. A null that means "the
parser failed" is not the same thing. Make the absence explicit.

```python
# lab/ai-service/ai_service/schemas.py  (additions for M14)
from typing import Literal
from pydantic import BaseModel, Field


class FieldPresence(BaseModel):
    """How a scalar field was resolved."""

    value: str | None = None
    status: Literal["present", "absent", "unverified"] = "absent"
    # Character offsets into the source document_text. Empty when absent.
    source_spans: list[tuple[int, int]] = Field(default_factory=list)
    evidence: str | None = None


class BankStatementExtractionV3(BaseModel):
    account_holder: FieldPresence = Field(default_factory=FieldPresence)
    ein: FieldPresence = Field(default_factory=FieldPresence)
    statement_period: StatementPeriod = Field(default_factory=StatementPeriod)
    transactions: list[ExtractedTransaction] = Field(default_factory=list)
    ocr_confidence: float | None = None
    notes: str | None = None
```

You do not have to migrate the whole schema in this mission. You do have to stop
treating a bare string as proof.

### Provenance, then validation

Provenance means: show where in the source the value came from. Validation means: refuse
to keep a value that cannot be found.

```python
# lab/ai-service/ai_service/validation/fields.py
import re

EIN_RE = re.compile(r"\b\d{2}-\d{7}\b|\b\d{9}\b")


def ein_in_source(ein: str | None, document_text: str) -> tuple[bool, list[tuple[int, int]]]:
    if not ein:
        return True, []
    digits = re.sub(r"\D", "", ein)
    if len(digits) != 9:
        return False, []
    spans: list[tuple[int, int]] = []
    for match in EIN_RE.finditer(document_text):
        if re.sub(r"\D", "", match.group()) == digits:
            spans.append(match.span())
    return (len(spans) > 0), spans


def resolve_ein(model_ein: str | None, document_text: str) -> dict:
    ok, spans = ein_in_source(model_ein, document_text)
    if model_ein and not ok:
        # The model invented it. Do not forward the invention.
        return {
            "value": None,
            "status": "absent",
            "source_spans": [],
            "evidence": "model_returned_ein_not_in_source",
        }
    if not model_ein:
        return {"value": None, "status": "absent", "source_spans": [], "evidence": None}
    return {
        "value": model_ein,
        "status": "present",
        "source_spans": spans,
        "evidence": document_text[spans[0][0]:spans[0][1]],
    }
```

Wire it into the route after structured parse, before you return.

```python
# lab/ai-service/ai_service/routes/extract.py  (excerpt)
from ai_service.validation.fields import resolve_ein

extraction = result.value
resolved = resolve_ein(extraction.ein, payload.document_text)
extraction.ein = resolved["value"]
if resolved["evidence"] == "model_returned_ein_not_in_source":
    warnings.append(
        "Model returned an EIN that does not appear in the source text. "
        "Value cleared. status=absent."
    )
# Attach provenance on the response envelope for the reviewer UI.
```

Re-run the Harbor Pine call.

:::evidence{type=http label="after source validation"}
```json
{
  "extraction": {
    "account_holder": "Harbor Pine Supply LLC",
    "ein": null
  },
  "warnings": [
    "Model returned an EIN that does not appear in the source text. Value cleared. status=absent."
  ]
}
```
:::

The model still "wanted" to invent a number. Your service refused to ship it. That is
the difference between a prompt and a guarantee.

## Tests

```python
# lab/ai-service/tests/test_m14_ein_validation.py
from ai_service.validation.fields import resolve_ein

BLANK_PAGE = """NORTHSTAR BUSINESS CHECKING
Account Holder: Harbor Pine Supply LLC
Account Number: ****4419
"""

PAGE_WITH_EIN = BLANK_PAGE + "\nEIN 56-2288104\n"


def test_blank_page_clears_invented_ein():
    out = resolve_ein("82-4719385", BLANK_PAGE)
    assert out["value"] is None
    assert out["status"] == "absent"
    assert out["evidence"] == "model_returned_ein_not_in_source"


def test_real_ein_keeps_span():
    out = resolve_ein("56-2288104", PAGE_WITH_EIN)
    assert out["value"] == "56-2288104"
    assert out["status"] == "present"
    assert out["source_spans"]


def test_null_stays_absent():
    out = resolve_ein(None, BLANK_PAGE)
    assert out == {
        "value": None,
        "status": "absent",
        "source_spans": [],
        "evidence": None,
    }
```

```bash
cd lab/ai-service && pytest tests/test_m14_ein_validation.py -q
```

## Then this happens

Ada is not done.

:::dialogue{title="Ada, Wednesday 2:10 PM"}
**Ada:** Good. You clear the fake ones. What do you store when it was present?

**You:** The value, and the span in the source text.

**Ada:** And when an underwriter edits it by hand?

**You:** Then the span is gone. Status becomes unverified until someone re-checks.

**Ada:** Write that down. Fraud reviews hand edits. If your system pretends a typed EIN
came from the PDF, that is a different kind of lie.
:::

Doug pings you five minutes later.

:::evidence{type=slack label="DM from Doug Feinberg"}
```text
Doug:  Ada forwarded the Harbor Pine case.
Doug:  Can you explain, in writing, why a fabricated EIN is worse than a blank
       for adverse action and KYC?

You:   working on the note now
```
:::

## The better version

Three layers, in this order:

1. **Abstention in the schema.** Missing is a first class status, not an omitted key.
2. **Provenance.** If the value is present, point at the bytes that justify it.
3. **Validation.** If the value cannot be found in the source, drop it and warn.

Prompt text stays. It reduces how often the model tries. It does not get to be the
control you cite to compliance.

The same pattern applies to account numbers, SSNs, and any identifier that looks
correct when invented. Well formed is not verified. Verified means "found on the page"
or "confirmed by a human," and those are different states.

:::judgment
**A well formed invented number is worse than a blank, because every system downstream
treats presence as information.**

Prompt instructions are requests. Validation is a gate. When a field is optional in the
real world, your service needs an explicit absent path, a way to prove presence from
source text, and a refusal to forward values that fail that proof. Schema mode makes
this sharper, not softer: once the model must emit valid JSON, "I do not know" stops
being easy, and confident garbage fills the slot.

The FDE move is to stop arguing with the model in English and start deciding which
outputs are allowed to leave your process. Ada's line stands: assume the applicant is
hostile, and assume helpfulness will invent a tidy answer when the page is quiet.
:::

:::commslab
#### To Ada

> Harbor Pine came back with EIN 82-4719385 under the failure scenario. That string is
> not on the page. We now clear any EIN that cannot be located in the source text and
> mark the field absent. Hand edits will show as unverified, not as document-sourced.

#### To Doug

> A blank EIN means we do not claim to know the tax ID. A fabricated EIN means we
> assert an identity we cannot support in writing. For KYC and adverse action, the
> second case creates a false record. We will not emit an EIN unless it appears in the
> source document or a human enters it under an unverified status.

#### To Marcus

> Extraction demo is fine if we show a blank EIN staying blank. Please do not put a
> filled EIN on a slide unless we can highlight the source span on the page. Invented
> fields look like product and they are fraud risk.
:::

## Practice

Different domain. Same reasoning.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A claims shop extracts a patient's member ID from faxed insurance cards. The prompt
says: "If the member ID is unreadable, return null."

Out of 2,000 faxes last week:

```text
1,720  member ID present on card, extracted correctly
 190  member ID unreadable, model returned null
  70  member ID unreadable, model returned a plausible 12 character ID
  20  member ID present, model returned a different plausible ID
```

Their engineer added "Never invent a member ID" to the prompt on Friday. Monday's rate
for invented IDs on blank cards fell from 70 to 55.

**Your task**

1. Rank the four rows by damage. Justify the worst one.
2. Why did the prompt change only move 70 to 55?
3. Write the validation rule that removes the invented IDs without blocking the 1,720.
4. What status should the 190 honest nulls carry into the claims system?

---

**Notes, after you have written yours**

**Worst row.** The 20 wrong IDs on cards that had a real number. Those attach the claim
to the wrong member. The 70 invented IDs on blank cards are close behind: they create
members that do not exist and pass format checks.

**Prompt change.** English reduced the rate. It did not create a guarantee. Residual
invention is expected.

**Validation.** Keep an ID only if its normalized form appears in the OCR text (or in a
barcode payload you trust). Otherwise set value null and status absent, with a warning
code like `model_returned_id_not_in_source`.

**Honest nulls.** Status `absent` (or `unreadable`), not a silent null and not a
guess. Downstream should route those to a human, not to auto-adjudication.
:::
