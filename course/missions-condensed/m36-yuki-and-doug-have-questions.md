---
id: M36
slug: yuki-and-doug-have-questions
title: Yuki and Doug Have Questions
subtitle: >-
  Security and compliance are not a gate at the end. They are constraints you
  either designed for or you are about to retrofit under fluorescent lights.
phase: 8
order: 36
duration: 240
difficulty: 4
lab: false
status: complete
objectives:
  - 'Survive a security and compliance review with evidence, not vibes'
  - Find PII in traces and decide what must be redacted or sealed
  - Show how an adverse action reason is produced in plain English
  - Separate "we can ship" from "we can defend this to a regulator"
concepts:
  - security review
  - audit trail
  - PII in observability
  - adverse action
  - model governance
competencies:
  - security
  - fintech-judgment
  - customer-communication
prereqs:
  - M31
  - M35
condensed: true
durationCondensed: 96
---
## Where you are

Phase 7 is done. The system is live for a growing share of applications. Cost is under control. Routing works. You have traces, budgets, and a postmortem from the Tuesday incident in a shared folder.

## The request

:::evidence{type=email label="Yuki Sato, Monday 7:58 AM"}
```text
Subject: materials for today's review

Bring:

1. Architecture diagram that matches production (not the 18 month old one)
2. Data flow for bank statement text, SSN/EIN, and decision outputs
3. Who can read ai_invocations and trace payloads today
4. What happens when a document contains instructions (you know the one)
5. Audit events for approve, decline, override, and tool calls

If a box says "just logging," say "just" one more time and we will spend
the hour on that box.

Yuki
```
:::

:::evidence{type=email label="Doug Feinberg, Monday 8:03 AM"}
```text
Subject: after Yuki

I need to see whether we can explain a decline to an applicant in writing,
in plain English, with the specific reasons we relied on.

If the answer is "the model said so," we do not ship broader rollout.

Doug
```
:::

## Your task

:::task{time="120 min"}
Produce a review packet (markdown is fine) with five parts:

1. **Data flow.** Bank text, identifiers, decisions. Mark trust boundaries.
2. **Access control findings.** Who can read traces and `ai_invocations` now. Gaps.
3. **Injection and tools.** One page on Mission 26/27 controls and what is still open.
4. **Adverse action path.** From reason codes to applicant-facing language. Show one
   real decline end to end.
5. **Remediation list.** Ordered by severity, with owners and dates. Include at least
   one item you cannot finish this week and say so.

You will present this to Yuki and Doug. No slides required. Evidence required.
:::

## Stop and think

:::stopandthink
Before you promise fixes in the room:

1. What is the difference between an audit log and a debug trace?
2. If you redact PII from traces, what incident workflow gets harder?
3. Can you name a decline reason that is true, specific, and not fair-lending toxic?
4. What are you tempted to hide because it is embarrassing rather than unsafe?

Write it down. Yuki can smell hand waving.
:::

## One line to remember

:::judgment
**A feature that cannot be audited, access-scoped, and explained to an applicant is not
done, no matter how good the eval score is.**

Security and compliance reviews feel adversarial when you treat them as theater. They
feel useful when you bring current evidence and separate blockers from backlog. In
fintech, PII in traces is a common self-own: observability gets built fast during an
incident phase, and nobody revisits who can read the payloads. Adverse action is the
same class of problem on the business side. Codes without plain language, or letters
without codes, both fail. The FDE who survives these rooms does not perform certainty.
They show artifacts, admit gaps, and leave with dated owners.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You built an AI assistant for an auto lender's collections team. Traces store full SMS
bodies "for debugging quality." The compliance lead asks whether you can show why a
borrower's payment plan offer was denied. Your system says `MODEL_RISK_SCORE_LOW`. The
VP wants to double traffic next week.

**Your task**

1. Name two review findings that should be blockers.
2. Rewrite the denial reason into something an applicant (or examiner) can understand,
   or say what data you still need.
3. Write the message to the VP refusing the traffic increase in under 100 words.

---

**Notes, after you have written yours**

Blockers: SMS bodies in broadly readable traces, and a denial reason that names a score
instead of specific principal reasons. You still need the concrete factors behind the
score (past due amount, broken promise-to-pay, income unverified, etc.). Message to the
VP: traffic waits on redaction/ACL and explainable reasons; expanding now creates exam
risk that dwarfs the throughput gain; give dates.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
