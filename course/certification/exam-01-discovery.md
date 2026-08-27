---
slug: exam-01-discovery
title: "Exam 01: Discovery"
subtitle: A payments company wants an AI chargeback agent. You have 90 minutes and no code to write.
kind: exam
order: 1
duration: 90
competencies: [discovery, customer-communication, fintech-judgment]
---

Timed practical. Write your answers before you open the spoiler.

## The brief

:::evidence{type=email label="COO, Clearsettle Payments"}
```text
We need an AI agent to handle chargebacks. Our dispute team is drowning
and we pay a vendor $40k a month for overflow. Every competitor has
automated this. Can you build us an agent by end of quarter?
```
:::

On the intro call you learn:

- The dispute team is four people.
- Chargebacks grew 3x in a year. Total payment volume grew 1.4x.
- The $40k vendor was hired eight months ago as a "stopgap."
- The COO's boss asked about AI in the last board meeting.
- Nobody offers a reason for the gap between 3x and 1.4x.

## Your deliverables

1. List every claim in the email. Mark each as problem, solution, or target.
2. Write the three discovery questions most likely to change the shape of the project.
3. Name the fact that should stop you cold, and what it suggests.
4. The COO wants a proposal by Friday. Reply in under 150 words.
5. Write what you would say to the Account Executive who already told the customer an agent ships by quarter end.

:::stopandthink
Answer all five in writing first. Time yourself. Then open the key.
:::

:::spoiler{label="Answer key and rubric"}
**1. Claims**

| Claim | Kind |
|---|---|
| Dispute team is drowning | Problem |
| We need an AI agent | Solution |
| Paying $40k/month for overflow | Problem (cost) |
| Competitors automated this | Business claim |
| By end of quarter | Target |

**2. Questions that change the project**

1. What changed in twelve months that explains 3x chargebacks vs 1.4x volume? Break it down by merchant, reason code, and product.
2. What does the $40k vendor actually do, and what happens if you stop paying tomorrow?
3. Walk the four people through their last full day. Time the work. How much is evidence gathering from internal systems vs real judgment?

**3. The fact that stops you**

Chargebacks grew faster than payments. Disputes should roughly track volume. A gap that size means something changed upstream: a new merchant category, fraud, a product change, a bad billing descriptor, or a broken refund flow. If that is true, automating response may make the flood cheaper to tolerate and remove pressure to fix the cause.

**4. Friday reply shape**

Decline to propose a solution. Commit to a date. Name the one number you will explain (the 3x vs 1.4x gap). Ask for two things: reason-code breakdown and a half day with the dispute team. Under 150 words. No feature list.

**5. AE conversation**

Protect the relationship without owning the promise. "We can still hit a board-ready milestone by quarter end. The milestone may be reducing dispute generation, not shipping an agent. I need until [date] to know which. Help me keep that door open with the COO."

**Rubric**

| Score | Behavior |
|---|---|
| 4 | Separates problem from solution, catches the volume gap, declines premature proposal without lecturing |
| 3 | Catches the gap and writes a solid reply, soft on the AE conversation |
| 2 | Good questions but still proposes an agent architecture |
| 1 | Accepts the agent ask and starts scoping tools |
:::
