---
slug: capstone-meridian
title: "Capstone: Meridian Financial"
subtitle: A new lender, a folder of messy artifacts, and nobody to tell you where the real problem is.
kind: capstone
order: 10
duration: 2400
competencies: [discovery, customer-communication, architecture, coding, debugging, ai-fundamentals, evals, rag, agent-design, security, fintech-judgment, production-reliability, adoption, productization, executive-communication]
---

Everything before this had guidance in it. Missions told you what to look at. Stop and
think blocks pointed at the questions worth asking. Even when the obvious answer was
wrong, the mission was built so you would find the right one.

This has none of that.

You get a customer package and a request. There is no answer key, no hint about where
the real bottleneck is, and no mission text telling you that your first hypothesis is
incomplete. It probably is. Finding that out is the exam.

Budget forty hours. Doing it in ten means you skipped discovery, which is the specific
failure this capstone is designed to catch.

## The request

:::evidence{type=email label="Received Monday, 6:14 AM"}
```text
From: Alicia Ferreira-Boyd <aferreiraboyd@meridianfinancial.com>
To: engagements@halyard.ai
Subject: AI agent for commercial loan processing

We were referred to you by a contact at Northstar.

Meridian Financial is a commercial lender. We do owner-occupied CRE,
equipment, and working capital lines, mostly in the 250k to 4M range.
Roughly 90 loans a month across three regions.

Our processing time is not competitive. We want to build an AI agent
that reduces commercial loan processing time by 70%.

I have budget approved for a pilot and I need something demonstrable
before our October board meeting. Our head of credit is skeptical, which
I would like you to treat as a challenge rather than an obstacle.

Can you start in two weeks?

Alicia Ferreira-Boyd
COO, Meridian Financial
```
:::

Yes, the number is 70 percent again. No, that does not mean the answer is the same.

Meridian is not Northstar. Different product mix, different regulatory posture,
different failure modes, different people. If you pattern match your way through this
and hand back the Northstar solution with the names changed, you will fail on
`discovery` and `fintech-judgment`, and the graders are specifically watching for it.

Some of what you learned does transfer. Working out which parts is the point.

## The package

Everything is in `customers/meridian/`. It is deliberately disorganized, because
customer material always is.

:::files
```text
customers/meridian/
  00-inbox/
    customer-email.md
    referral-note-from-northstar.md
    nda-and-sow-draft.pdf.md
  01-meetings/
    kickoff-transcript.md
    credit-committee-observation.md
    regional-manager-calls/          three calls, three different processes
    ops-walkthrough-notes.md
    it-security-intake-call.md
  02-architecture/
    system-overview-2023.pptx.md     out of date, and it says so nowhere
    integration-inventory.xlsx.md
    network-diagram.png.md
    whiteboard-photo-transcription.md
  03-api-docs/
    core-banking-api-v2.md           describes v2. they run v1.4 in two regions.
    loan-origination-swagger.json
    partner-portal-api.md
  04-code/
    lending-core/                    Java 8, Spring 4, no tests worth the name
    doc-intake/                      Python 2 to 3 migration, unfinished
    scripts/                         eleven shell scripts, four in use
  05-database/
    schema-dump.sql
    sample-rows.csv
    the-report-query.sql             1,400 lines, runs nightly, nobody owns it
  06-applications/                   40 real-shaped applications
  07-bank-statements/                mixed quality, including six that are unusable
  08-policies/                       nine documents, two contradict each other
  09-security/
    prior-pentest-findings.md
    vendor-risk-questionnaire.md
    data-classification-policy.md
  10-production/
    logs/                            three days, two services, one bad night
    metrics-export.csv
    trace-samples.json
  11-support/
    ticket-export.csv                fourteen months of tickets
    top-complaints-summary.md        written by someone with an agenda
  12-history/
    prior-vendor-postmortem.md       they tried this before. read this one.
```
:::

:::warning{title="Read 12-history first"}
Meridian has attempted this before. The prior attempt failed, and the postmortem in
`12-history/` was written by the person who inherited the mess rather than the person
who caused it, so it is unusually honest.

Most candidates read it in week three. The ones who read it on day one save themselves
about fifteen hours.
:::

## What you have to produce

Twelve deliverables. They are graded together, because in real work they are one thing.

### Phase one, discovery, deliverables 1 to 4

**1. Engagement brief.** Same shape as Mission 01. The request, the problem as you
understand it, what you must learn, who you must talk to, what done looks like for week
three.

**2. Workflow map with measurements.** Not a diagram of the happy path. Where time
actually goes, with numbers pulled from the data you were given, including the exception
paths and the rework loops. State your measurement method and your confidence.

**3. Architecture map.** Built from evidence, not from `02-architecture/`. Include what
the documents get wrong and how you know.

**4. Findings memo, two pages maximum.** What the real problem is. If your answer is
"the thing they asked for," you need strong evidence, because it usually is not.

### Phase two, design, deliverables 5 to 7

**5. Slice proposal.** One vertical slice. Measurable value, reachable in six weeks,
a real user whose job changes, and it must produce evidence that informs the next
decision. Include what you are deliberately not doing and why.

**6. AI boundary document.** For every capability in your slice, state whether it is
deterministic code, a model, retrieval, a workflow, an agent, or a human, and defend it.
Marking something as a model without justifying it costs you points. So does refusing to
use one where it is clearly right.

**7. Architecture proposal.** Including multi-tenancy, data handling, audit,
observability, and a failure model. Say what happens when each dependency is down.

### Phase three, build, deliverables 8 to 10

**8. Working code.** Runs, has tests, integrates with at least one Meridian legacy
system as represented in the package. Handles the failure modes you documented.

**9. Eval suite.** Golden dataset with real provenance, slices that reflect actual
business risk, a baseline, and a regression gate. Report per-slice numbers and say
which slices you would block a release on.

**10. Security and compliance review response.** Meridian's security team will send you
questions. Answer them as an engineer, in writing, without hand waving.

### Phase four, production and impact, deliverables 11 to 12

**11. Incident response.** At a point you do not control, you will be given a production
incident with a live timeline. Produce the timeline, the containment steps, the fix, the
recovery of affected work, and an honest writeup.

**12. Executive readout.** Twenty minutes for Alicia and her board. Business result,
engineering result, remaining risk, what you recommend next, and what you would not do.

## How it is scored

Fifteen competencies, each 0 to 4. See the [competency matrix](/reference/competency-matrix).

To pass:

- Average of 3.0 or better
- No competency below 2
- No score below 3 in `discovery`, `customer-communication`, or `security`

Those three have a higher bar on purpose. Weak code gets caught in review. Weak
discovery does not get caught until the project is over, and weak security does not get
caught until it is in the news.

### What graders reward

- Changing your mind in writing when evidence contradicts you. Show the wrong turn.
- Saying "I do not know yet" with a plan to find out.
- Choosing not to use AI where it is not warranted, and defending it.
- Scoping something small that actually shipped over something large that did not.
- Reading the support tickets.

### What graders penalize

- Applying the Northstar solution without testing whether it fits.
- Accepting the 70 percent target without measuring the ceiling.
- An accuracy number with no slices under it.
- A design that cannot explain a decision to an applicant in writing.
- An agent where a workflow would do, with no justification.
- Any deliverable that assumes the customer's documentation is correct.

:::stopandthink
Before you open the package, write down two things and seal them.

1. Your prediction of what the real bottleneck will turn out to be.
2. Your confidence in that prediction, as a percentage.

At the end, compare. The gap between those two numbers is the most useful thing this
capstone will teach you about yourself.
:::

:::judgment
**The capstone is not testing whether you can build an AI system. It is testing whether
you can be trusted alone in a room with a customer who is confidently wrong.**

Every technical skill in this course is learnable from documentation in a few weeks. The
thing that is hard, and the thing that actually separates a Forward Deployed Engineer
from a very good backend engineer, is the willingness to keep a problem open while
everyone around you, including the person paying, is pushing to close it.

Alicia has budget, a board date, and a skeptical head of credit she wants you to win
over. All three of those push you toward building something demonstrable fast. That
pressure is the exam. Building something demonstrable fast is sometimes right. Doing it
before you know where the time goes is how the prior vendor ended up with a postmortem
in `12-history/`.

Read that file. Someone already ran this experiment for you.
:::
