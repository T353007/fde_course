---
id: M21
slug: the-seam
title: The Seam
subtitle: >-
  Marcus wants more AI. Doug wants a sentence he can put in a letter. You have
  to draw the line.
phase: 4
order: 21
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Apply a decision framework for model versus code versus human on a real
    underwriting step
  - Remove a legacy path that asks the model to do arithmetic
  - Make an AI assisted decision auditable without replaying a prompt
  - Push back on a product request that puts a policy threshold in a prompt
concepts:
  - AI boundaries
  - auditability
  - policy as code
  - human in the loop
  - productization
competencies:
  - architecture
  - fintech-judgment
  - productization
  - ai-fundamentals
prereqs:
  - M20
condensed: true
durationCondensed: 96
---
## Where you are

Mission 20 works. Coastal Supply shows 147,400. Renee signed off on the excluded lines. Dale called it "directionally correct," which from Dale is a standing ovation.

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

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
