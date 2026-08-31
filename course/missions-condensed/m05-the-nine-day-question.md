---
id: M05
slug: the-nine-day-question
title: The Nine Day Question
subtitle: >-
  You measure where the time goes and the answer disqualifies the project you
  were hired to build.
phase: 1
order: 5
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Measure cycle time from the event history instead of from a column that
    looks right
  - 'Break a nine day clock into waits, rework, and hands-on work'
  - Prove that automating underwriter time cannot reach a seventy percent target
  - Resolve two measurements that disagree without picking the flattering one
concepts:
  - cycle time
  - event sourcing
  - bottleneck analysis
  - measurement traps
  - workflow mapping
competencies:
  - discovery
  - debugging
  - fintech-judgment
prereqs:
  - M04
condensed: true
durationCondensed: 108
---
## Where you are

March 18. The interviews are done. Your stakeholder map has eleven rows and too many empty artifact cells for comfort. Dale wants a number on the twenty first. The board meeting is on the twenty fourth.

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

## Your task

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

## Stop and think

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

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
