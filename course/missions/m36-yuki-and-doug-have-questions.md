---
id: M36
slug: yuki-and-doug-have-questions
title: Yuki and Doug Have Questions
subtitle: "Security and compliance are not a gate at the end. They are constraints you either designed for or you are about to retrofit under fluorescent lights."
phase: 8
order: 36
duration: 240
difficulty: 4
lab: false
status: complete
objectives:
  - Survive a security and compliance review with evidence, not vibes
  - Find PII in traces and decide what must be redacted or sealed
  - Show how an adverse action reason is produced in plain English
  - Separate "we can ship" from "we can defend this to a regulator"
concepts: [security review, audit trail, PII in observability, adverse action, model governance]
competencies: [security, fintech-judgment, customer-communication]
prereqs: [M31, M35]
---

## Where you are

Phase 7 is done. The system is live for a growing share of applications. Cost is under
control. Routing works. You have traces, budgets, and a postmortem from the Tuesday
incident in a shared folder.

Yuki Sato has booked two hours on your calendar titled "AI threat model walkthrough."
Doug Feinberg booked the hour after that titled "Adverse action and model governance."
Neither invite has an agenda attachment. That is not an oversight. They want to see
whether you bring evidence or a narrative.

Ada pings you five minutes before Yuki's review.

:::evidence{type=slack label="Adaeze Nwosu, 9:55 AM"}
```text
Ada:   Assume the applicant is hostile.
Ada:   that includes the PDF and the trace store.
Ada:   if contractors can read bank lines, say so early. Yuki already knows.
```
:::

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

## The conversation

:::dialogue{title="Conference room B, Monday 10:00 AM"}
**Yuki:** Start with trust boundaries. Where does untrusted document text enter the
system?

**You:** Upload to document-service, OCR, then ai-service extraction.

**Yuki:** Does any of that text land in traces in plaintext?

**You:** Span attributes include truncated input. I think we cap at two thousand
characters.

**Yuki:** You think.

*Silence.*

**Doug:** While we are on plaintext. If I pull application 44891, can I see the owner's
tax identifiers in the trace store?

**You:** I will verify during this meeting.

**Yuki:** Say "just" one more time.

**You:** I did not say just.

**Yuki:** You were about to.
:::

You pull the trace live on the projector. That is better than describing it. It is also
how the meeting gets hard fast.

:::dialogue{title="Still Monday 10:00 AM"}
**Yuki:** Who are the three contractors in this Okta group?

**You:** I do not have the offboarding list with me.

**Yuki:** Then access review is finding one.

**Doug:** Flip to a decline letter. Any decline from last week.

**You:** APP-44800. Reason codes insufficient revenue and DSCR below floor.

**Doug:** Read the letter the applicant got.

**You:** "Your application was not approved based on our assessment."

**Doug:** That is not specific. That is a shrug. Can you explain that decision to the
applicant in writing?

**You:** Not with this letter. The codes exist. The letter did not use them.
:::

## What you know about the system

You built observability in Mission 31. You handled prompt injection in Mission 26 and
tool authorization in Mission 27. Local routing in Mission 35 exists partly because
Doug and Yuki pushed back on sending bank text out by default.

None of that means the review is ceremonial. Reviews find the gap between the design
you described and the permissions that actually exist.

## Evidence

:::evidence{type=trace label="Sample span attributes on /v1/extract/bank-statement"}
```text
http.route=/v1/extract/bank-statement
tenant_id=NSC_DIRECT
application_id=44891
model=qwen3:8b
prompt_version=v17
input.preview=05/04 STRIPE PAYOUT +48,230\n05/06 TRANSFER FROM SAVINGS +30,000\n...
applicant.ein=12-3456789
owner.ssn_last4=4412
prompt_tokens=4210
completion_tokens=520
```
:::

EIN and last4 are in the trace. Bank lines are in the trace. The trace backend ACL is
currently "anyone in the engineering Okta group," which includes three contractors who
left last quarter and were never removed.

:::evidence{type=policy label="Adverse action excerpt, Doug's binder"}
```text
If credit is declined or offered on materially less favorable terms,
the applicant must receive a statement of specific principal reasons.
Reference to a statistical score or "automated system" without the
underlying reasons is not sufficient.
```
:::

:::evidence{type=slack label="Old thread, Mission 29 era"}
```text
Marcus:  the copilot can just say "policy concern" and the underwriter
         fills in the letter

Doug:    that is not how this works
Doug:    can you explain that decision to the applicant in writing?
```
:::

:::evidence{type=schema label="decisions.reason_codes today"}
```text
reason_codes TEXT  -- comma separated string, not an array
example: INSUFFICIENT_REVENUE,DSCR_BELOW_FLOOR
```
:::

Codes exist. Plain English letters mapped from those codes are inconsistent. Some
overrides in the portal clear the codes.

:::evidence{type=log label="Portal override last Thursday"}
```text
INFO  reviewer-portal - user=renee.blackwell app=44771
      override=true cleared_reason_codes=true free_text="see notes"
WARN  adverse_action - letter generated with empty reasons; fallback boilerplate used
```
:::

:::evidence{type=policy label="Yuki's threat model prompt (on the whiteboard)"}
```text
1. Untrusted input: applicant PDFs, emails, portal fields
2. Privileged actions: decline, approve, tool calls, data export
3. Sensitive reads: traces, ai_invocations, raw documents
4. Cross-tenant: CASCADE must not see BAYLINE spans
5. Exit paths: hosted model, vendor APIs, support exports
```
:::

## What you do not know

- Whether production trace retention is 7 days or 90
- Who approved contractor access to the observability project
- Whether CASCADE and BAYLINE data is separable in the trace index
- What Renee actually pastes into adverse action free text today

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

:::stopandthink
Before you promise fixes in the room:

1. What is the difference between an audit log and a debug trace?
2. If you redact PII from traces, what incident workflow gets harder?
3. Can you name a decline reason that is true, specific, and not fair-lending toxic?
4. What are you tempted to hide because it is embarrassing rather than unsafe?

Write it down. Yuki can smell hand waving.
:::

## Working through it

### The wrong turn

You try to win the room by talking about everything you already built. Local models.
Tool allowlists. Prompt injection tests. It is all real. Yuki listens. Then she opens
the trace.

:::dialogue{title="Ten minutes later"}
**Yuki:** This span has an EIN.

**You:** We can redact that.

**Yuki:** Who could have seen it yesterday?

**You:** Engineering Okta.

**Yuki:** How many people is that?

**You:** I do not know the exact number.

**Doug:** Then you do not have access control. You have a hope.

**You:** Fair.
:::

Listing prior heroics does not pass a review. Current evidence does.

### Surviving the review

**On PII in traces.** Split debug and audit.

| Store | Purpose | PII policy |
|---|---|---|
| OpenTelemetry traces | Debug latency and failures | Redact identifiers and raw bank lines. Keep hashes, counts, model metadata. |
| `ai_invocations` | Model governance audit | Controlled access. Tenant scoped. Retention policy. No contractor default. |
| `application_events` / `decisions` | Business audit | Source of truth for what was decided and why. |

Incident response still needs a sealed break-glass path to raw inputs. That path must
be logged, time limited, and dual controlled. "We deleted everything sensitive" is how
you make the next outage un-debuggable.

**On injection.** Walk the PDF case from Mission 26 without swagger. Show the test that
still fails if someone reintroduces raw document text into a tool-selection prompt.
Yuki cares that the control is enforced in code, not in a wiki.

**On adverse action.** Pick APP-44800 from seed data (or a known decline). Show:

```text
reason_codes: INSUFFICIENT_REVENUE, DSCR_BELOW_FLOOR

Applicant letter draft:
We declined your application for a term loan because:
1. Average monthly operating revenue was below our minimum for this product.
2. Debt service coverage was below our floor for the requested amount.
```

If the model drafted the memo, the letter still has to be grounded in stored reason
codes a human accepts. Free text overrides that erase codes fail Doug's test.

### Then this happens

You agree to redact span previews by Friday. Marcus joins the last fifteen minutes.

:::dialogue{title="Marcus drops in"}
**Marcus:** Are we good to expand the flag to 50 percent traffic?

**Yuki:** Not until trace ACL and adverse action mapping are done.

**Marcus:** Can't we expand and fix in parallel? Speed matters.

**Doug:** Speed without explainability is how we earn a letter from a regulator.

**You:** We expand when the remediation items marked blocker are closed. I will put
dates on the non-blockers today.
:::

Your job is to keep Marcus from turning a review finding into a schedule fight in the
same room. Agree on blockers in writing before anyone leaves.

### The better version of your close

End with a short list Yuki can accept:

```text
BLOCKER-1  Remove EIN/SSN/bank lines from default traces          You+Sam   Fri
BLOCKER-2  Restrict trace+ai_invocations to named on-call group   Yuki      Fri
BLOCKER-3  Adverse action letter generator from reason_codes      You+Doug  Tue
NEXT-1     Break-glass raw access with dual control               Yuki      +2w
NEXT-2     Contractor offboarding audit of observability ACL      Priya     +1w
```

Do not argue that local routing already solved privacy. It reduced one path. It did not
fix who can read the path you still log.

:::dialogue{title="Close of Doug's hour"}
**Doug:** Blocker three is the letter path. Show me Tuesday.

**You:** Three declines, three letters, codes only, no boilerplate.

**Doug:** And overrides?

**You:** Override cannot clear codes without replacing them. Free text is notes, not
the letter source.

**Doug:** That I can defend. Ship it.

**Yuki:** Access review calendar invite is on your desk. Bring the contractor list
yourself next time.
:::

After they leave, you write the embarrassing line in the remediation doc: "We built
excellent AI controls and left bank lines in a trace store half the company could
read." That sentence is what keeps the next engagement from repeating it.

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

:::commslab
#### To Yuki

> Traces currently contain EIN and bank line previews. ACL is too broad. Blockers are
> redaction and named access by Friday. I want your break-glass design before I strip
> raw inputs everywhere.

#### To Doug

> Declines store reason codes. Applicant language is not consistently generated from
> those codes. I will ship a letter path that only uses accepted codes, and I will show
> you three examples Tuesday.

#### To Priya

> Review outcome: not a no, a conditional. Two blockers before wider rollout. Blast
> radius of ignoring them is regulatory and reputational, not just engineering debt.
:::

## Practice

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
