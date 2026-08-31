---
id: M32
slug: 214-stuck-applications
title: 214 Stuck Applications
subtitle: 'Expected a number. Got "$78,231 approximately". Monitoring stayed green.'
phase: 7
order: 32
duration: 300
difficulty: 5
lab: true
status: complete
objectives:
  - >-
    Run an incident from detection through containment, fix, recovery, and
    writeup
  - Separate schema failures from timeouts in retry policy
  - Explain why process health stayed green while 214 applications stuck
  - Recover work without double-decisioning applications
concepts:
  - incident response
  - structured output
  - retries
  - poison messages
  - workflow health
competencies:
  - debugging
  - production-reliability
  - customer-communication
prereqs:
  - M31
condensed: true
durationCondensed: 120
---
## Where you are

Tuesday. Spans exist. Flags are on for a slice of `NSC_DIRECT` volume. You are in a normal afternoon meeting when Carla's queue turns into a siren.

## The request

:::evidence{type=slack label="#northstar-ai, Tuesday 16:47 ET"}
```text
Carla:  ticket volume just spiked
Carla:  applicants saying status stuck in review
Carla:  Oh, that. Yeah, we just tell them to resubmit. except resubmit is
        also stuck?

Hank:   What does that do to my queue?
Hank:   I have people waiting on decisioned files

Janet:  who is on call for that

Priya:  show me the blast radius
```
:::

Detected at 16:47 because support volume moved. Not because monitoring caught it.
Monitoring was green.

## Your task

:::task{time="180 min"}
Run the incident in the lab with `X-Stub-Scenario: revenue-as-string` (or the inject
scenario wired for M32).

1. Contain: stop the bleeding (flag, consumer pause, or route to deterministic path).
2. Diagnose root cause with logs, traces, and one failing payload.
3. Fix: reject non-numeric revenue before Java parse, and make retries treat
   SCHEMA_ERROR as non-retryable.
4. Recover the 214 without double posting decisions.
5. Write an incident report: timeline, impact, root cause, fix, follow-ups.

Time pressure is part of the exercise. Contain before you craft the perfect patch.
:::

## Stop and think

:::stopandthink
Before you dig into prompt archaeology:

1. What is the fastest containment that protects applicants right now?
2. Why did health checks stay green?
3. If you fix the parser to accept currency strings, what new bug do you create?
4. Who needs a status sentence in the next fifteen minutes: Hank, Carla, Dale?

Write it. Then move.
:::

## One line to remember

:::judgment
**Containment before diagnosis, and schema errors are not timeouts.**

Green hosting metrics during a workflow outage are normal. Design for that. When a
model returns the wrong shape, fail closed, page, and do not pay five times for the
same poison payload. When you recover, protect against double decisions first, pride
second.

The phrase "$78,231 approximately" is funny once. In production it is how you learn
whether your retries understand the failures they see.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A payments company LLM returns `"twenty dollars"` for a fee field. The ledger parser
throws. A retry bus redelivers for 3 hours. Dashboards show API green. Support sees
settlement delays at minute 150. An engineer patches the ledger to parse English number
words.

**Your task**

1. What do you contain in the first 15 minutes?
2. Why is English-number parsing the wrong turn?
3. What retry rule do you ship?

---

**Notes, after you have written yours**

Contain by stopping the consumer or feature flag for the LLM fee path and freezing
manual settlement guesses. English parsing creates unverifiable money and invites more
creative strings. Retries should treat schema failures as non-retryable dead letters.
Same incident shape as Northstar.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
