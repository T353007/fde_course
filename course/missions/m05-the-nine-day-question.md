---
id: M05
slug: the-nine-day-question
title: The Nine Day Question
subtitle: You measure where the time goes and the answer disqualifies the project you were hired to build.
phase: 1
order: 5
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - Measure cycle time from the event history instead of from a column that looks right
  - Break a nine day clock into waits, rework, and hands-on work
  - Prove that automating underwriter time cannot reach a seventy percent target
  - Resolve two measurements that disagree without picking the flattering one
concepts: [cycle time, event sourcing, bottleneck analysis, measurement traps, workflow mapping]
competencies: [discovery, debugging, fintech-judgment]
prereqs: [M04]
---

## Where you are

March 18. The interviews are done. Your stakeholder map has eleven rows and too many
empty artifact cells for comfort. Dale wants a number on the twenty first. The board
meeting is on the twenty fourth.

Nadia's rule still holds. Measure where the time goes, all of it, before you say a
number out loud.

## The request

:::evidence{type=slack label="DM from Nadia Ferrante, Tuesday 7:14 AM"}
```text
Nadia:  readout is friday
Nadia:  what is your number

You:    don't have it yet. querying today

Nadia:  which table

You:    applications. submitted_at to decided_at

Nadia:  what would have to be true for that to be the answer

You:    that those columns mean what the names say

Nadia:  go find out whether they do
```
:::

## The conversation

:::dialogue{title="Sam's desk, Tuesday 9:40 AM"}
**You:** I need median days from submit to decision.

**Sam:** Finance pulls that. Ask Mei.

**You:** I want to pull it myself.

**Sam:** Fine. `applications.submitted_at` and `applications.decided_at`.

**You:** That is what I was going to use.

*He looks at you for a second. Then he looks at his monitor.*

**Sam:** Run it. Then come back.
:::

## What you know about the system

Lab is up. Seed has 1,200 applications. About 1,840 a month if you annualize the
window. Status values you care about right now:

```text
SUBMITTED  DOCS_REQUESTED  DOCS_RECEIVED  IN_REVIEW
PENDING_INFO  DECISIONED
```

`PENDING_INFO` is the rework loop. An application can enter it more than once.

Hank's SLA starts at complete file. Dale's clock starts at application. Those are
different clocks. Today you measure Dale's clock, then you break it into pieces.

## Evidence

### First query, the wrong one

You do the obvious thing.

:::evidence{type=sql label="psql, first attempt, applications.submitted_at"}
```sql
-- Wrong. Looks right. Defect lives in the column, not in the math.
SELECT
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (decided_at - submitted_at)) / 86400.0
  ) AS median_cycle_days,
  count(*) AS rows_used
FROM northstar.applications
WHERE submitted_at IS NOT NULL
  AND decided_at IS NOT NULL;
```
:::

:::evidence{type=sql label="Result"}
```text
 median_cycle_days | rows_used
-------------------+-----------
              9.85 |       867
```
:::

Nine point eight five. Close to the nine to ten days Hank quoted Dale. You feel a
little proud for about twelve minutes.

Then you notice the row count. 867. Seed has 1,004 decisioned applications. You are
missing 137 rows because `submitted_at` is null on some of them, and you do not know
why yet.

:::dialogue{title="Back at Sam's desk, 10:22 AM"}
**You:** I get 9.85 days. 867 rows.

**Sam:** ...Ah.

**You:** Ah what.

**Sam:** So you found that.

**You:** Found what?

**Sam:** Portal writes `submitted_at` on the client. Backend records a `SUBMITTED`
event when it actually accepts the application. Those are not the same time.

**You:** How far apart?

**Sam:** Median gap is about forty minutes. Sometimes days. Nightly job backfills the
failures. Some stay null.

**You:** So the column is lying.

**Sam:** The column is doing what it was told. You asked it the wrong question.

**You:** Where is the right question?

**Sam:** `application_events`. Append only. That is the real clock.
:::

## What you do not know

- How much of the 9.4 days (if that is the real number) is underwriter hands-on time
- How much is waiting on documents
- How often a file goes back out as `PENDING_INFO`
- Whether Finance's nine to ten days uses the same broken column
- Whether Marcus's "underwriting is the bottleneck" survives contact with minutes

:::task{time="150 min"}
With the lab running (`make up` then `make seed` if you have not), produce a one page
workflow map with numbers on it.

Required measurements, all from `application_events` unless a note says otherwise:

1. Median cycle time, `SUBMITTED` event to `DECISIONED` event
2. Median document wait, first `DOCS_REQUESTED` to first `DOCS_RECEIVED`
3. Median underwriter hands-on minutes, sum of `REVIEW_OPENED` to matching
   `REVIEW_CLOSED` per application
4. Share of submitted applications with at least one `PENDING_INFO` event
5. Median cost of one rework loop, `PENDING_INFO` to the next `IN_REVIEW`

Also run the wrong query on `applications.submitted_at` and write one sentence about
why the row count differs.

Then answer, in writing, before the readout draft: if you automated every minute of
underwriter hands-on time, what percent of cycle time could you remove? Show the
arithmetic.

Save the map as `customers/northstar/cycle-time.md`.
:::

:::stopandthink
Before you scroll into the working queries:

1. You already have 9.85 days from `submitted_at`. What would make you throw that
   number out?
2. If hands-on time comes back under an hour, what happens to Dale's seventy percent?
3. Hank says his team hits SLA ninety one percent of the time. Can that be true at the
   same time as a nine day median from submit to decision?
4. What third measurement would Marcus wave at you to defend "underwriting is the
   bottleneck," and how would you check it?

Eight minutes. On paper.
:::

## Working through it

### Second query, the right one

:::evidence{type=sql label="psql, cycle time from application_events"}
```sql
WITH bounds AS (
  SELECT
    application_id,
    min(occurred_at) FILTER (WHERE event_type = 'SUBMITTED')  AS submitted_at,
    min(occurred_at) FILTER (WHERE event_type = 'DECISIONED') AS decided_at
  FROM northstar.application_events
  GROUP BY application_id
)
SELECT
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (decided_at - submitted_at)) / 86400.0
  ) AS median_cycle_days,
  count(*) AS decisioned_apps
FROM bounds
WHERE submitted_at IS NOT NULL
  AND decided_at IS NOT NULL;
```
:::

:::evidence{type=sql label="Result"}
```text
 median_cycle_days | decisioned_apps
-------------------+-----------------
              9.40 |            1004
```
:::

Nine point four days. Canon number. Full row count.

:::dialogue{title="Sam, still standing"}
**You:** 9.4. Thousand and four rows.

**Sam:** Yeah.

**You:** Finance's number was nine to ten. They were close and wrong in the same way.

**Sam:** Mei uses `submitted_at`. She knows it is messy. She rounds.
:::

### The rest of the clock

:::evidence{type=sql label="psql, document wait"}
```sql
WITH docs AS (
  SELECT
    application_id,
    min(occurred_at) FILTER (WHERE event_type = 'DOCS_REQUESTED') AS requested_at,
    min(occurred_at) FILTER (WHERE event_type = 'DOCS_RECEIVED')  AS received_at
  FROM northstar.application_events
  GROUP BY application_id
)
SELECT
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (received_at - requested_at)) / 86400.0
  ) AS median_doc_wait_days
FROM docs
WHERE requested_at IS NOT NULL
  AND received_at IS NOT NULL;
```
:::

:::evidence{type=sql label="Result"}
```text
 median_doc_wait_days
----------------------
                 5.10
```
:::

:::evidence{type=sql label="psql, hands-on minutes"}
```sql
WITH ordered AS (
  SELECT
    application_id,
    event_type,
    occurred_at,
    lead(event_type) OVER (
      PARTITION BY application_id ORDER BY occurred_at
    ) AS next_type,
    lead(occurred_at) OVER (
      PARTITION BY application_id ORDER BY occurred_at
    ) AS next_at
  FROM northstar.application_events
),
sessions AS (
  SELECT
    application_id,
    EXTRACT(EPOCH FROM (next_at - occurred_at)) / 60.0 AS minutes
  FROM ordered
  WHERE event_type = 'REVIEW_OPENED'
    AND next_type = 'REVIEW_CLOSED'
)
SELECT
  percentile_cont(0.5) WITHIN GROUP (ORDER BY minutes) AS median_hands_on_minutes
FROM (
  SELECT application_id, sum(minutes) AS minutes
  FROM sessions
  GROUP BY application_id
) per_app;
```
:::

:::evidence{type=sql label="Result"}
```text
 median_hands_on_minutes
-------------------------
                   41.00
```
:::

Forty one minutes. Not hours. Not days.

:::evidence{type=sql label="psql, rework share and cost"}
```sql
-- Share with at least one rework loop
SELECT
  round(
    100.0 * count(DISTINCT CASE WHEN event_type = 'PENDING_INFO'
                                THEN application_id END)
         / count(DISTINCT CASE WHEN event_type = 'SUBMITTED'
                                THEN application_id END)
  , 0) AS rework_share_pct
FROM northstar.application_events;

-- Median days from PENDING_INFO to next IN_REVIEW
WITH ordered AS (
  SELECT
    application_id,
    event_type,
    occurred_at,
    lead(event_type) OVER (
      PARTITION BY application_id ORDER BY occurred_at
    ) AS next_interesting,
    lead(occurred_at) OVER (
      PARTITION BY application_id ORDER BY occurred_at
    ) AS next_at
  FROM northstar.application_events
  WHERE event_type IN ('PENDING_INFO', 'IN_REVIEW')
)
SELECT
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (next_at - occurred_at)) / 86400.0
  ) AS median_rework_days
FROM ordered
WHERE event_type = 'PENDING_INFO'
  AND next_interesting = 'IN_REVIEW';
```
:::

:::evidence{type=sql label="Result"}
```text
 rework_share_pct
------------------
               63

 median_rework_days
--------------------
               2.80
```
:::

Write them down exactly. You will quote them for the rest of the engagement.

```text
Median time from application to decision ....... 9.4 days
Median underwriter hands-on time ............... 41 minutes
Median time waiting on documents ............... 5.1 days
Applications with at least one rework loop ..... 63%
Median cost of one rework loop ................. 2.8 days
Applications per month ......................... 1,840
Underwriters on staff .......................... 11
Dale's stated target ........................... 70% faster
```

### The arithmetic that kills the original plan

:::dialogue{title="Nadia, Slack, Tuesday 2:05 PM"}
**You:** 9.4 days. Hands-on is 41 minutes.

**Nadia:** say the percent out loud

**You:** 41 divided by 9.4 times 60. About 7 percent.

**Nadia:** and Dale wants

**You:** 70.

**Nadia:** so what did you get hired to build

**You:** an AI underwriter

**Nadia:** which automates which part

**You:** the 41 minutes

**Nadia:** week 3. say it friday. not week 9.
:::

Automating every minute of underwriter hands-on time caps out near 7 percent of cycle
time. Dale's 70 percent does not live in underwriting judgment. It lives in the 5.1
days of document wait and the rework loops that hit 63 percent of files at 2.8 days
each.

The project you were hired to build cannot produce the outcome you were hired to
produce. Not because AI is weak. Because the time is not where anyone pointed.

## Then this happens

Wednesday morning Marcus drops a screenshot in the channel.

:::evidence{type=slack label="#northstar-ai, Wednesday 8:41 AM"}
```text
Marcus:  wait I thought we measured this??
Marcus:  finance dashboard says median time IN_REVIEW to decision
         is 2.2 days
Marcus:  that is underwriting. that is the bottleneck.
Marcus:  your 41 minutes can't be right

You:     looking
```
:::

This is the third measurement. It contradicts your hands-on number if you let it.

:::evidence{type=sql label="psql, Marcus's clock"}
```sql
WITH bounds AS (
  SELECT
    application_id,
    min(occurred_at) FILTER (WHERE event_type = 'IN_REVIEW')   AS review_at,
    min(occurred_at) FILTER (WHERE event_type = 'DECISIONED') AS decided_at
  FROM northstar.application_events
  GROUP BY application_id
)
SELECT
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (decided_at - review_at)) / 86400.0
  ) AS median_underwriting_calendar_days
FROM bounds
WHERE review_at IS NOT NULL
  AND decided_at IS NOT NULL;
```
:::

:::evidence{type=sql label="Result"}
```text
 median_underwriting_calendar_days
-----------------------------------
                              2.24
```
:::

Two point two four calendar days from first `IN_REVIEW` to decision. Marcus is not
making it up. Finance is not lying. And 41 minutes is still true.

:::dialogue{title="Call with Marcus, Wednesday 9:10 AM"}
**You:** Your 2.2 days is real. My 41 minutes is real. They measure different things.

**Marcus:** How.

**You:** `IN_REVIEW` means the file is sitting in the underwriting queue. Waiting for
someone to open it. Waiting overnight. Waiting while they finish another file.

**Marcus:** And 41 minutes is...

**You:** `REVIEW_OPENED` to `REVIEW_CLOSED`. Actual screen time. Hands on the keyboard.

**Marcus:** So underwriting takes 2 days.

**You:** The queue takes 2 days. The person takes 41 minutes. An AI underwriter replaces
the person. It does not drain the queue by itself, and it does not fetch the bank
statements.

**Marcus:** ...Okay. That is annoying.

**You:** Yeah.

**Marcus:** Do not put "Marcus was wrong" on the slide.

**You:** I will put "calendar time in review is mostly queue." Your name stays off it.
:::

### The wrong turn: trusting the first column that matched Dale

Your first query felt done because 9.85 was close to the story everyone already told.
Close is the danger. A number that confirms the brief gets less scrutiny than a number
that threatens it.

The cost was not the morning. The cost was almost walking into Friday with a column
that drops 137 decisioned apps, drifts by a median of 40 minutes, and occasionally by
days, and calling it measured. Sam's pause is the whole quality bar for this week: if a
senior engineer says "run it, then come back," assume the first answer is a trap.

### The map you bring on Friday

```text
SUBMITTED
    |
    v
DOCS_REQUESTED  ---- 5.1 days median ---->  DOCS_RECEIVED
    |
    |   (Bill's missing-file loop and Carla's resubmits live here)
    v
IN_REVIEW  (queue: part of the 2.2 calendar days)
    |
    +-- REVIEW_OPENED .. 41 min hands-on .. REVIEW_CLOSED
    |
    +-- 63% enter PENDING_INFO ---- 2.8 days median ----> back to IN_REVIEW
    |
    v
DECISIONED

Total SUBMITTED to DECISIONED: 9.4 days median
```

The AI underwriter sits on the 41 minute box. Dale's seventy percent sits on the 5.1
and the 2.8.

:::judgment
**A clock that confirms the brief is the one you have to distrust first.**

`submitted_at` is accurate and wrong. Accurate as a record of what the portal wrote.
Wrong as a definition of when the company accepted the application. Most measurement
bugs in legacy systems look like that. The column name matches the question. The write
path does not.

The second trap is mixing calendar time with hands-on time. Marcus's 2.2 days and
Renee's forty one minutes can both be true, and only one of them is the thing an AI
underwriter replaces. If you automate judgment without measuring wait, you ship a demo
that looks smart and moves the nine days by minutes.

Your job on Friday is not to humiliate anyone. It is to put the five numbers on one
page so Dale can see that his target is real and his plan cannot reach it. The plan
changes. The target stays. That distinction is the whole mission.
:::

:::commslab
#### To Sam

> `application_events` is the clock. I will not quote `submitted_at` again without a
> footnote. If Mei asks why her number moved, I will walk her through the gap query
> with you on the call.

#### To Marcus

> Your 2.2 days is queue time, not keyboard time. I am going to say that on Friday
> without naming you. If Dale asks who found it, I will say product and discovery
> together.

#### To Hank

> Your SLA can stay green while Dale's nine days stay bad. Different start times. I
> need one slide that shows both clocks so nobody thinks your team is the delay.

#### To Dale (draft line for Friday, not sent yet)

> You are losing deals on speed. The nine days are real. Almost none of them are
> underwriter hands-on time. I want twenty minutes on Friday to show you where they
> are, before the board deck freezes.
:::

## Practice

Same skill, different industry.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A regional auto insurer wants "AI claims adjusters" to cut cycle time 60 percent. You
pull three numbers in a day:

```text
Query A, claims.opened_at to claims.closed_at:
  median 11.2 days, 4,102 rows (opened_at is set by the agent app offline)

Query B, claim_events OPENED to CLOSED:
  median 10.1 days, 4,880 rows

Query C, ADJUSTING status start to close:
  median 3.6 days

Desk observation, six adjusters:
  median hands-on per claim: 52 minutes
```

The VP says Query C proves adjusting is the bottleneck.

**Your task**

1. Which query do you take to the exec readout, and why not the others?
2. What percent of cycle time can automating hands-on adjuster work move, using the
   same board arithmetic as Northstar (minutes over days × 60)?
3. Write the one sentence that separates the VP's 3.6 days from the 52 minutes.
4. Name one wait you still have not measured.

---

**Notes, after you have written yours**

Take Query B. Event history, full population. Query A drops rows and uses a client
timestamp. Query C is real and is mostly queue.

52 / (10.1 × 60) ≈ 9 percent. That is the ceiling on "AI adjuster" if all it replaces
is desk time.

One sentence: 3.6 days is how long a claim sits in adjusting, and 52 minutes is how
long a person touches it.

Unmeasured wait: evidence from the shop, rental car authorizations, or medical records.
If those dominate, you have Northstar's document problem in a different jacket.
:::
