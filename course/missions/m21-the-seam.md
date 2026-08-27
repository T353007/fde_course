---
id: M21
slug: the-seam
title: The Seam
subtitle: "Marcus wants more AI. Doug wants a sentence he can put in a letter. You have to draw the line."
phase: 4
order: 21
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Apply a decision framework for model versus code versus human on a real underwriting step
  - Remove a legacy path that asks the model to do arithmetic
  - Make an AI assisted decision auditable without replaying a prompt
  - Push back on a product request that puts a policy threshold in a prompt
concepts: [AI boundaries, auditability, policy as code, human in the loop, productization]
competencies: [architecture, fintech-judgment, productization, ai-fundamentals]
prereqs: [M20]
---

## Where you are

Mission 20 works. Coastal Supply shows 147,400. Renee signed off on the excluded
lines. Dale called it "directionally correct," which from Dale is a standing ovation.

Marcus wants to go further. He always does.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 9:05 AM"}
```text
Marcus:  love the revenue panel. next step: can the AI just decide if they
         clear the 300k minimum?

Marcus:  like, policy says 300k annual operating revenue for term loans.
         model already has the number. Can't the AI just do that?

Sam:     the model has a classification. python has the number.

Marcus:  right. so the AI can finish the thought.
```
:::

"Can't the AI just do that?" is Marcus's catchphrase. Sometimes he is pointing at a
real product gap. Sometimes he is pointing at a seam you must not erase.

## The conversation

:::dialogue{title="Whiteboard, Monday 10:15 AM"}
**You:** Three buckets. Model, code, human. We put each step in one.

**Marcus:** Feels like overthinking.

**You:** Walk through what Doug asks when a decline goes out.

**Doug:** *from the doorway* Can you explain that decision to the applicant in
writing?

**Marcus:** We can have the model write the letter.

**Doug:** I need the reason to be true before it is eloquent.
:::

:::dialogue{title="Same whiteboard, Marcus pushes"}
**Marcus:** Fine. But the threshold check is trivial. Why is that not the model?

**You:** Because the threshold changes with product, tenant, and effective date. And
because a prompt that says "decline under 300000" becomes a second policy store
nobody diffs.

**Priya:** Show me the blast radius if the prompt is wrong.

**You:** Every term loan decisioned while that prompt is live.
:::

## What you know about the system

After Mission 20 the happy path is:

1. Extract lines.
2. Classify lines with the model.
3. Sum operating revenue in Python.
4. Hand the number to underwriting.

Underwriting already has policy hooks. They are incomplete and partly wrong, but they
are code. They can be tested. They show up in `decisions.reason_codes`.

There is still a landmine in `ai-service`. `LEGACY_REVENUE_SUMMARY` defaults on.
`_legacy_revenue_summary()` asks the model for `averageRevenue`. Mission 32 will turn
that into an incident. Mission 21 is where you kill the path on purpose, while you
still have time.

The seam is the boundary between probabilistic judgment and deterministic consequence.

## The code

```python
class LegacyRevenueSummary(ApiModel):
    """The old prompt asked the model to do the arithmetic. This is that shape.

    Kept because underwriting-service still reads it. Mission 21 removes it.
    """

    average_revenue: Decimal
    method: str | None = None
```

And the config knob:

```python
    # Also return the model's own revenue average on the classify response.
    # underwriting-service still reads that field.
    legacy_revenue_summary: bool = True
```

Marcus's new request would add a second knob. Something like "ask the model whether
policy clears." That is the wrong turn. Write the framework first.

## Evidence

:::evidence{type=policy label="credit-policy-2025.pdf, Section 3 excerpt"}
```text
Minimum annual operating revenue for a term loan is 300,000 dollars.

Do not count these as operating revenue:
- transfers between accounts held by the same business or owner
- proceeds from any loan, line of credit, or merchant cash advance
- owner capital contributions
- refunds and chargeback reversals
- one time asset sales
```
:::

:::evidence{type=policy label="California-overlay.pdf, CASCADE only"}
```text
Minimum annual operating revenue for a term loan is 400,000 dollars for
California borrowers. This is higher than base policy.
```
:::

:::evidence{type=slack label="Doug Feinberg, Monday 11:02 AM"}
```text
Doug:  if the model "decides" the threshold, what do I cite?
Doug:  the prompt version? the temperature?
Doug:  I need a rule id and a number.
```
:::

## What you do not know

- Whether Janet will accept a new `PolicyThresholdService` in underwriting this sprint.
- How many callers still read `model_revenue_summary` from the classify response.
- Whether Hank will accept a human step when operating revenue sits inside 10 percent
  of the threshold.
- Whether Bayline and Cascade need different near miss bands. Base policy is silent.

## A second conversation you need

:::dialogue{title="Hank, Monday 1:10 PM"}
**Hank:** What does that do to my queue?

**You:** Far below the floor can system decline with a rule id. Far above can pass the
threshold check. The band around the floor goes to review.

**Hank:** How wide is the band?

**You:** Ten percent. About one in twelve term loans in the last quarter sat there.

**Hank:** And those still need an underwriter.

**You:** Yes. The point of the seam is not zero humans. It is knowing why a human is
in the path.
:::

Hank cares about throughput. He will accept a REVIEW bucket if you can show him it is
smaller than the pile Renee already rekeys by hand. Bring the count.

## Your task

:::task{time="110 min"}
1. Write a one page decision framework with three columns: model, code, human. Place
   every step of bank statement revenue handling into exactly one column.
2. Turn off `LEGACY_REVENUE_SUMMARY` and remove or gate the callers that depended on
   `model_revenue_summary`.
3. Implement the 300,000 term loan threshold check in code, reading product and tenant
   overlays from policy metadata, not from a prompt.
4. When operating revenue is within 10 percent of the threshold, route to a human
   underwriter instead of auto passing or auto failing.
5. Decline Marcus's "put the threshold in the prompt" request in writing, with the
   blast radius attached.
:::

## Stop and think

:::stopandthink
1. If the threshold lives in a prompt, how do you diff a policy change?
2. What belongs to the model on this path, if not the threshold?
3. What is the cost of a confident automatic decline that cited the wrong floor?

Write before you scroll.
:::

## Working through it

### The framework

| Step | Owner | Why |
|---|---|---|
| Read text off a messy page | model | Judgment under noise |
| Parse amounts into decimals | code | Facts, testable parsers |
| Label a deposit as loan vs revenue | model | Judgment, needs examples |
| Sum operating revenue | code | Arithmetic, audit trail |
| Compare to product threshold | code | Policy as data |
| Apply CASCADE California floor | code | Tenant overlay |
| Borderline within 10 percent | human | Accountability |
| Draft a credit memo paragraph | model | Language, reviewed by human |
| Send adverse action notice | human + templates | Legal consequence |

The model is not banned from the workflow. It is banned from the consequences that
require a stable rule id.

### The wrong turn: policy threshold in the prompt

Marcus pastes this into a draft prompt file and asks you to "just try it."

```text
If annualized operating revenue is below 300000, set decision to DECLINE.
If the applicant is in California, use 400000.
Explain your decision briefly.
```

You try it on ten fixtures. Eight look fine. One CASCADE applicant gets the 300,000
floor because the prompt buried the overlay under a long revenue discussion and the
model missed it. One SBA application gets declined on the term loan floor even though
SBA overlays differ.

Cost of the wrong turn: two incorrect decision recommendations before lunch, and a
policy change process that is now "edit the prompt and hope retrieval surfaces the
right paragraph."

Revert the prompt. Keep the transcript. You will need it when Marcus asks again.

### Threshold in code

```java
package com.northstar.underwriting.policy;

import java.math.BigDecimal;

import org.springframework.stereotype.Component;

@Component
public class RevenueThresholdPolicy {

    public record ThresholdResult(
            BigDecimal operatingRevenue,
            BigDecimal threshold,
            String ruleId,
            String outcome, // PASS, FAIL, REVIEW
            String detail) {}

    public ThresholdResult evaluate(String tenantId, String product,
                                    String state, BigDecimal operatingRevenue) {
        BigDecimal threshold = baseThreshold(product);

        if ("CASCADE".equals(tenantId) && "CA".equalsIgnoreCase(state)
                && "TERM_LOAN".equals(product)) {
            threshold = new BigDecimal("400000.00");
            return conclude(operatingRevenue, threshold, "POL-CA-REV-400K");
        }

        return conclude(operatingRevenue, threshold, "POL-BASE-REV-300K");
    }

    private BigDecimal baseThreshold(String product) {
        if ("TERM_LOAN".equals(product)) {
            return new BigDecimal("300000.00");
        }
        if ("LOC".equals(product)) {
            return new BigDecimal("200000.00");
        }
        return new BigDecimal("300000.00");
    }

    private ThresholdResult conclude(BigDecimal revenue, BigDecimal threshold,
                                     String ruleId) {
        BigDecimal band = threshold.multiply(new BigDecimal("0.10"));
        if (revenue.compareTo(threshold) >= 0) {
            if (revenue.subtract(threshold).compareTo(band) <= 0) {
                return new ThresholdResult(revenue, threshold, ruleId, "REVIEW",
                        "Within 10 percent above threshold. Human review required.");
            }
            return new ThresholdResult(revenue, threshold, ruleId, "PASS",
                        "Operating revenue meets " + ruleId);
        }
        if (threshold.subtract(revenue).compareTo(band) <= 0) {
            return new ThresholdResult(revenue, threshold, ruleId, "REVIEW",
                    "Within 10 percent below threshold. Human review required.");
        }
        return new ThresholdResult(revenue, threshold, ruleId, "FAIL",
                "Operating revenue below " + ruleId);
    }
}
```

Doug gets a rule id. Hank gets a REVIEW bucket for the edge. Marcus gets a decision
in the product without stuffing policy into prose.

### Kill the legacy summary

```python
# config.py
legacy_revenue_summary: bool = False
```

Find callers:

```bash
rg "model_revenue_summary|modelRevenueSummary|legacy_revenue_summary" lab/
```

Underwriting still deserializes the field. Make it optional and unused. Add a log line
when a caller asks for it with the flag off, so Mission 32 has a cleaner failure mode
if someone flips the flag back.

```java
// UnderwritingDecisionService: stop preferring the model average
BigDecimal operating = hybridTotals.operatingRevenue();
// Do not read aiResponse.modelRevenueSummary()
```

### Auditability

When a decision is written, persist:

```text
operating_revenue     147400.00
threshold             300000.00
rule_id               POL-BASE-REV-300K
classification_ids    [trace of classify call]
prompt_version        txn_classify_v3
computed_by           python
```

An auditor should rebuild the compare step with no model replay. They may need a model
replay to audit a disputed classification. That is fine. Classification is the judgment
layer. The compare is not.

## Tests

```java
@Test
void cascadeCaliforniaUsesHigherFloor() {
    var result = policy.evaluate("CASCADE", "TERM_LOAN", "CA",
            new BigDecimal("350000.00"));
    assertEquals(new BigDecimal("400000.00"), result.threshold());
    assertEquals("FAIL", result.outcome());
    assertEquals("POL-CA-REV-400K", result.ruleId());
}

@Test
void nearMissGoesToReview() {
    var result = policy.evaluate("NSC_DIRECT", "TERM_LOAN", "NC",
            new BigDecimal("285000.00"));
    assertEquals("REVIEW", result.outcome());
}
```

```python
def test_legacy_summary_off_by_default(monkeypatch):
    monkeypatch.setenv("LEGACY_REVENUE_SUMMARY", "false")
    reset_settings_cache()
    assert get_settings().legacy_revenue_summary is False
```

## Then this happens

Jordan forwards a note from Dale.

:::evidence{type=email label="Dale to Jordan, forwarded to you"}
```text
Liked the demo. When does the AI start declining the obvious ones on its own?
Board keeps asking if we are actually automating underwriting or just making
fancy calculators.

Is that directionally the plan?
```
:::

## Tracking it down

Dale is asking a productization question while using automation language. The honest
answer is: classification is automated, thresholds are automated in code, declines
that sit far below the floor can be system declined with a rule id, and borderline
cases stay human. That is automation. It is not "the AI declines."

Write the sentence you will reuse in Phase 8:

```text
We automate judgment where the model is measured, and we automate rules where
the rule has an id. We do not hide rules inside prompts.
```

## The better version

Ship a tiny design note in the repo, not a slide.

```text
docs/seam-revenue-v1.md

Model: classify transactions, draft memo language
Code: parse, sum, threshold, tenant overlays, reason codes
Human: within 10 percent of threshold, existing competitor debt, fraud flags

Never: policy thresholds in prompts, model-computed totals used for decisions
```

This note is the seed of productization. When Redwood Bank shows up in Phase 9, you
will not invent the seam again. You will ask which of their steps are judgment, which
are rules, and which are accountability.

:::judgment
**The seam is a product decision dressed up as an engineering preference.**

People argue about models versus code when they are really arguing about who owns the
rule when it is wrong. If the rule lives in a prompt, ownership is fuzzy and diffs are
chat transcripts. If the rule lives in code with a rule id, Doug can cite it and Janet
can page the owner.

Marcus is not the villain here. He is paid to push scope into the model because that
is what got sold. Your job is to keep the parts that must stay boring in the boring
layer, and to say that out loud before the prompt becomes the policy store.
:::

:::commslab
#### To Marcus

> The threshold check ships. It lives in underwriting code with rule ids, including
> the Cascade California 400k floor. Putting it in the prompt looked faster and failed
> two of ten fixtures on overlays. Same outcome you wanted, safer path.

#### To Doug

> Declines and near misses now carry rule ids and the operating revenue number. The
> model does not pick the floor. If you want the letter templates mapped to those ids,
> send me the current set.

#### To Dale

> We are automating classification and the hard threshold checks. Borderline files
> still go to an underwriter. That is intentional. Fancy calculator is the wrong
> frame. Measured judgment plus coded policy is the plan.

#### To Priya

> Blast radius of the rejected prompt approach: every term loan decisioned while the
> prompt was live, with no reliable overlay handling. Blast radius of the code path:
> RevenueThresholdPolicy and its tests. On call stays with underwriting-service.
:::

## Practice

Different domain, same skill.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A benefits platform decides whether an employee is eligible for parental leave top up.
A model reads free text HR notes and classifies leave type. Policy says full time
employees with 12 months tenure get top up. Managers want the model to "just approve
the obvious ones."

What you learn:

- Leave type classification from notes is messy and benefits from a model.
- Tenure and employment type live in the HRIS as structured fields.
- One business unit has a 6 month tenure exception in a side PDF.
- Legal needs a reason code on every denial.
- A prompt was drafted that says "approve if they seem full time and about a year in."

**Your task**

1. Fill model / code / human for: note classification, tenure check, business unit
   exception, final approve or deny, appeal letter.
2. What is wrong with the drafted prompt?
3. What do you productize for the next customer?

---

**Notes, after you have written yours**

Model classifies leave type from notes. Code checks tenure and employment type from
HRIS. Code loads business unit exceptions from a versioned config. Human handles
missing HRIS data and appeals. The drafted prompt hides a tenure rule in adjectives
like "about a year," which cannot be cited. Productize the seam document and the
exception config format, not the parental leave wording.
:::

The lesson in one sentence: put judgment in the model, put rules in code with ids, and
put accountability on a human when the file sits on the edge.
