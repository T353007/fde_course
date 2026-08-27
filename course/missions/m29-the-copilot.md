---
id: M29
slug: the-copilot
title: The Copilot
subtitle: "Human in the loop means the human still decides. It also means the clicks have to be worth it."
phase: 6
order: 29
duration: 300
difficulty: 4
lab: true
status: complete
objectives:
  - Build a hitl copilot that proposes underwriting actions without committing them
  - Produce explanation text Doug can put near an adverse action letter
  - Hear Wendy's click complaint and record it as a real adoption risk
  - Ship a vertical slice reviewers will try twice, not once
concepts: [human in the loop, explainability, adverse action, adoption seeds]
competencies: [agent-design, adoption, fintech-judgment]
prereqs: [M28]
---

## Where you are

The assistant answers questions on a workflow for most volume. Hank still wants help on
the decision itself: a drafted recommendation the underwriter accepts or rejects.

It is Thursday, July 16. You are building the copilot panel in the reviewer portal. Wendy
Kaur watches the first prototype for eleven minutes without speaking. That is not a good
sign.

## The request

:::evidence{type=email label="Marcus Webb, subject: Copilot MVP scope"}
```text
Need the underwriting copilot in pilot by end of month.

- AI reads the file and recommends Approve / Decline / Pending info
- Shows reasons and the numbers it used
- Underwriter confirms in one click
- Logs for Doug

Jordan already told Dale we are "putting a copilot in the underwriter's hands."
Please make that sentence true.
```
:::

## The conversation

:::dialogue{title="Wendy's monitor, Thursday 2:10 PM"}
**Wendy:** Count with me.

**You:** Okay.

**Wendy:** Open app. Open copilot. Wait. Expand reasons. Open policy cite. Open
transactions. Accept. Confirm accept. Close toast.

**You:** That is eight.

**Wendy:** I said six last month about the portal alone. You added two. Reviewers will
try this while they are already late on the queue. Then they will stop.

**You:** We can trim.

**Wendy:** Trim before Hank measures adoption by logins. Logins will look fine while
people open it once and never accept a suggestion.
:::

:::dialogue{title="Doug, Friday 9:30 AM"}
**Doug:** Can you explain that decision to the applicant in writing?

**You:** The copilot explains to the underwriter.

**Doug:** If they accept a decline recommendation, something has to land in the adverse
action path that a human can stand behind. Model prose is not a reason code.

**You:** So the copilot picks from your list.

**Doug:** The copilot proposes from my list. The underwriter selects. The letter uses
the selected codes. Free text stays internal.
:::

## What you know about the system

Kafka topic `ai.extraction.requested` already exists for document work. For the copilot
you add a synchronous endpoint the portal calls when the reviewer opens the panel:

`POST /v1/memo/draft` with application context, returning a structured proposal.

Human in the loop (HITL) here means: the model never sets `applications.status`. It
returns a proposal. The existing decision UI commits.

## Evidence

:::evidence{type=http label="Copilot draft response, application 45301"}
```text
POST /v1/memo/draft
X-Tenant-Id: NSC_DIRECT
X-Trace-Id: 55c0d2e1

{
  "applicationId": 45301,
  "include": ["transactions", "policy", "fraud"]
}
```

```text
200 OK
{
  "proposalId": "prop_45301_02",
  "recommendation": "DECLINE",
  "reasonCodes": ["INSUFFICIENT_REVENUE", "HIGH_EXISTING_DEBT"],
  "internalRationale": "Operating revenue after excluding transfer and Fastcapital loan proceeds does not support requested 250000 at policy DSCR floor.",
  "numbersUsed": {
    "amountRequested": 250000.00,
    "operatingRevenueMonthly": 49133.33,
    "naiveCreditAverage": 84133.33
  },
  "citations": [
    {"documentId": "credit-policy-2025", "section": "4.2 DSCR", "effectiveFrom": "2025-01-01"}
  ],
  "adverseActionDraft": {
    "reasonCodes": ["INSUFFICIENT_REVENUE", "HIGH_EXISTING_DEBT"],
    "applicantFacingText": null
  },
  "model": "qwen3:8b",
  "promptVersion": "memo-draft-v1"
}
```
:::

:::evidence{type=slack label="Renee, after three pilot files"}
```text
Renee:  the numbersUsed panel is the only part I trust at a glance
Renee:  if naive and operating disagree, show both like you did
Renee:  we don't use that number - meaning the naive one - but I need to see
        that the machine also knows we don't use it
```
:::

## What you do not know

- Whether one-click accept is compatible with Doug's selection requirement.
- How often proposals will be wrong on the loan-proceeds slice.
- Whether Wendy's eight-click path will still be eight after you "simplify."
- How hard Marcus will push to count panel opens as adoption.

## Your task

:::task{time="180 min"}
1. Implement the copilot panel against `POST /v1/memo/draft` with structured proposals
   only (recommendation, reason codes from the approved enum, numbers used, citations).
2. Wire Accept so it opens the existing decision panel with fields prefilled, actor =
   the reviewer. No silent status change from ai-service.
3. Generate applicant-facing adverse action text only from selected reason codes via
   Doug's templates, never from `internalRationale`.
4. Instrument clicks: panel open, proposal shown, accept, modify, reject. You will need
   this in Mission 37.
5. Write down Wendy's complaint in the mission notes you hand Marcus. Do not sand it off.
:::

## Stop and think

:::stopandthink
1. If Accept commits in one click with no reason code screen, what does Doug lose?
2. If Accept only prefills and still needs four more clicks, what does Wendy lose?
3. Which number on the proposal would Renee refuse to show the applicant?

Write answers before you scroll. Two minutes.
:::

## Working through it

### First panel review with Renee and Wendy in the room

You drive three live files. Renee ignores the recommendation chip until she sees
`numbersUsed`. Wendy times every click on her phone stopwatch.

:::evidence{type=metrics label="Wendy's stopwatch, first prototype"}
```text
open application ................ 0:00
open copilot .................... 0:08
spinner ......................... 0:08 to 0:14
expand reasons .................. 0:16
open policy cite modal .......... 0:21
close cite, open txns ........... 0:29
accept .......................... 0:41
confirm accept dialog ........... 0:44
toast + dismiss ................. 0:48
total ........................... 48 seconds of ceremony before decision panel work
```
:::

**Wendy:** Forty eight seconds and they have not underwritten anything yet.

**Renee:** The naive versus operating split is correct on file two. Keep that. Lose the
toast.

### Build the proposal contract

```python
# lab/ai-service/ai_service/memo/draft.py
from pydantic import BaseModel, Field
from typing import Literal

ReasonCode = Literal[
    "INSUFFICIENT_REVENUE",
    "HIGH_EXISTING_DEBT",
    "INCOMPLETE_DOCS",
    "FAILED_FRAUD_REVIEW",
    "OUTSIDE_POLICY_PRODUCT",
]


class CopilotProposal(BaseModel):
    proposal_id: str
    recommendation: Literal["APPROVE", "DECLINE", "PENDING_INFO"]
    reason_codes: list[ReasonCode] = Field(min_length=1)
    internal_rationale: str
    numbers_used: dict
    citations: list[dict]
    prompt_version: str


def draft_memo(ctx: ApplicationContext) -> CopilotProposal:
    facts = gather_facts(ctx)  # workflow style, not open agent
    raw = provider.complete_structured(
        prompt_version="memo-draft-v1",
        schema=CopilotProposal.model_json_schema(),
        facts=facts,
    )
    proposal = CopilotProposal.model_validate(raw)
    # Never let the model invent a reason code.
    proposal.reason_codes = [c for c in proposal.reason_codes if c in ReasonCode.__args__]
    return proposal
```

### Adverse action text

```python
# lab/ai-service/ai_service/memo/adverse.py
TEMPLATES = {
    "INSUFFICIENT_REVENUE": (
        "The monthly operating revenue shown in the file did not meet "
        "Northstar's requirements for the amount requested."
    ),
    "HIGH_EXISTING_DEBT": (
        "Existing debt obligations were too high relative to operating revenue "
        "for the requested credit."
    ),
}


def applicant_facing_text(codes: list[str]) -> str:
    parts = [TEMPLATES[c] for c in codes if c in TEMPLATES]
    if not parts:
        raise ValueError("no approved templates for codes")
    return " ".join(parts)
```

`internalRationale` can say "Fastcapital loan proceeds." The letter cannot invent facts
the reason codes do not carry. If Doug needs more detail later, he expands templates,
not model prose.

:::dialogue{title="Doug reviews a sample letter"}
**Doug:** Read the applicant sentence out loud.

**You:** "The monthly operating revenue shown in the file did not meet Northstar's
requirements for the amount requested."

**Doug:** Good. Now read the internal rationale.

**You:** It mentions Fastcapital and the transfer exclusion.

**Doug:** That stays internal. If we need Fastcapital on the letter someday, we add a
reason code and a template. We do not paste model text into Reg B correspondence.
:::

### The wrong turn: one-click accept

Marcus wants the literal one-click from his email. You try it.

```tsx
// wrong turn
async function onAccept(proposal) {
  await api.decision.commit({
    applicationId: proposal.applicationId,
    status: proposal.recommendation,
    reasonCodes: proposal.reasonCodes,
    source: "copilot_one_click",
  });
}
```

Doug blocks the deploy. Hank likes the speed. You are stuck until you change the meaning
of Accept.

Better Accept:

```tsx
async function onAccept(proposal) {
  // Prefill only. Reviewer still lands on the decision panel.
  openDecisionPanel({
    prefill: {
      recommendation: proposal.recommendation,
      reasonCodes: proposal.reasonCodes,
      proposalId: proposal.proposalId,
      numbersSnapshot: proposal.numbersUsed,
    },
  });
  track("copilot_accept_prefill", { proposalId: proposal.proposalId });
}
```

Clicks drop from eight to five if you also kill the toast and the nested cite modal
(cites inline). Not one. Wendy says five is "borderline livable" and asks you to write
that down.

:::evidence{type=slack label="Wendy, after the revision"}
```text
Wendy:  five clicks if the panel opens with codes already selected and cites inline
Wendy:  still too many. seed this for later. people will bounce by week three
Wendy:  do not let Marcus call five clicks one click in the deck
```
:::

That message is a Mission 37 fuse. Leave it lit.

### Instrumentation you will need later

```text
copilot_panel_open
copilot_proposal_shown
copilot_accept_prefill
copilot_codes_modified
copilot_proposal_rejected
copilot_decision_committed_with_proposal
```

If Marcus reports only `copilot_panel_open`, correct him in the meeting with the other
five. Adoption collapse in Mission 37 is already visible in the gap between open and
commit. You are planting the metric now on purpose.

## Tests

```python
def test_proposal_reason_codes_are_enum_only():
    raw = {
        "proposal_id": "p1",
        "recommendation": "DECLINE",
        "reason_codes": ["INSUFFICIENT_REVENUE", "FEELS_RISKY"],
        "internal_rationale": "x",
        "numbers_used": {},
        "citations": [],
        "prompt_version": "memo-draft-v1",
    }
    # FEELS_RISKY must not survive validation / filtering
    proposal = normalize_proposal(raw)
    assert proposal.reason_codes == ["INSUFFICIENT_REVENUE"]


def test_applicant_text_does_not_include_internal_rationale():
    text = applicant_facing_text(["INSUFFICIENT_REVENUE"])
    assert "Fastcapital" not in text
    assert "operating revenue" in text.lower()
```

```tsx
// reviewer-portal test
it("accept prefills but does not commit", async () => {
  const commit = vi.spyOn(api.decision, "commit");
  await user.click(screen.getByRole("button", { name: "Accept proposal" }));
  expect(commit).not.toHaveBeenCalled();
  expect(screen.getByRole("heading", { name: "Decision" })).toBeVisible();
});
```

## Then this happens

Pilot week one: 67 percent of reviewers open the panel. Accept-prefill rate is lower.
Marcus still wants to report 67 percent to Dale as adoption.

:::dialogue{title="Standing meeting"}
**Marcus:** Adoption is strong.

**You:** Opens are strong. Accepts are okay. Completes through decision are the number.

**Wendy:** And the completes will fall when the novelty wears off.

**Hank:** What does that do to my queue?

**You:** If the proposal is right, hands-on time drops a few minutes. If the panel is
slow, they ignore it and you gain nothing. We measure accepts, not opens.
:::

:::judgment
**A copilot that cannot explain a decline in approved language is not ready for lending.
A copilot that takes eight clicks is not ready for reviewers.**

HITL is not a checkbox. It is a specific split: model proposes structure, human commits
state, letters use templates a compliance officer already owns. The adoption risk shows
up as friction long before it shows up as accuracy. Wendy named the failure mode while
everyone else celebrated the panel existing. Write that down. You will need it when week
three usage falls off a cliff and someone blames the model.
:::

:::commslab
#### To Doug

> Copilot proposals use your reason code enum only. Applicant-facing text is rendered
> from templates keyed by those codes. Internal rationale never enters the letter.
> Commit actor is always the reviewer. Proposal id is stored on the decision for audit.

#### To Wendy

> Accept is prefill into the decision panel, cites are inline, toast is gone. We are at
> five clicks. I logged your week-three bounce warning in the adoption notes Marcus has
> to read before he reports numbers to Dale.

#### To Marcus

> Do not report panel opens as adoption. Report proposals accepted into a decision, and
> decisions that keep the proposed codes. Wendy expects a drop by week three if we do
> not cut more friction. Plan for that measurement now.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A mortgage shop wants a "one-click AI underwriter." Compliance requires adverse action
reasons from a fixed list. Loan officers say the current tools already take too many
clicks.

**Your task**

1. Split proposal vs commit responsibilities in five bullets.
2. What text is allowed in the applicant letter?
3. Which metric do you refuse to put in the exec deck?
4. Write Wendy's warning in one sentence for the project risk register.

---

**Notes, after you have written yours**

Proposal: recommendation, enum reason codes, numbers, citations, internal notes.
Commit: human in existing decision UI, human as actor. Letter: templates from codes
only. Refuse "panel open rate" as adoption. Risk register: reviewers will abandon a
high-click copilot by week three even if quality is fine.
:::
