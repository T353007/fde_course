---
id: M17
slug: running-the-model-in-the-building
title: Running the Model in the Building
subtitle: >-
  Compliance asks why account numbers are leaving the building. It is a fair
  question and it changes your architecture.
phase: 3
order: 17
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Explain the data residency objection in words Doug and Yuki accept
  - >-
    Run the txn-classification suite against Ollama with qwen3:8b, and against
    stub
  - >-
    Compare hosted and local results using canon deltas on easy versus loan
    proceeds
  - >-
    Sketch a routing direction for Mission 35 without pretending local wins
    everywhere
concepts:
  - local models
  - ollama
  - data residency
  - tco
  - latency
  - model routing
competencies:
  - ai-fundamentals
  - architecture
  - security
prereqs:
  - M16
condensed: true
durationCondensed: 108
---
## Where you are

You have a classifier, an eval, and a slice report that made Marcus less cheerful. The design doc for the next phase still says "call the hosted mid alias from ai-service."

## The request

:::evidence{type=email label="From Doug Feinberg, Tuesday 7:58 AM"}
```text
Subject: AI egress of account data

Copying Yuki.

The current design sends bank transaction text to a third party model provider.
That text includes account numbers, counterparties, and occasionally SSNs in memo
lines.

Please explain:
1) what leaves Northstar's network
2) what retention the vendor has
3) why this is acceptable for our compliance program

If we cannot answer those, we need an in-network option before expand.

Doug
```
:::

:::evidence{type=slack label="DM from Yuki Sato, same morning"}
```text
Yuki:  say "just send it to the API" one more time
Yuki:  I will end the meeting early
Yuki:  bring a local option or bring a threat model. not vibes
```
:::

## Your task

:::task{time="150 min"}
1. Answer Doug's three email questions in
   `customers/northstar/notes/m17-egress-response.md` before you touch Ollama.
2. Run `make ollama-check`. If it fails on RAM or missing daemon, complete the stub
   lane and still fill the canon comparison table by hand from this mission.
3. Run txn-classification on stub and, if possible, on `qwen3:8b`. Save JSON outputs
   under `out/m17-*.json`.
4. Produce a TCO sketch: monthly cost of two A10G always on, versus hosted mid alias at
   current volume, versus a mixed routing guess. Numbers can be approximate. Show the
   arithmetic.
5. List what must stay true so a classmate with `LLM_PROVIDER=stub` still passes the
   verify target.
:::

## Stop and think

:::stopandthink
1. Doug's question is not anti-AI. What requirement is he actually stating?
2. If local matches within 1 point on the easy slice and loses 14 points on loan
   proceeds, is "we go all local" a complete architecture?
3. Latency moves from 1.9s to 6 to 11s. Who feels that, Hank or the batch job?
4. Why does this course insist the stub path keeps working?

Write answers. Question 2 is the bridge to Mission 35.
:::

## One line to remember

:::judgment
**Data residency is an architecture constraint, not a prompt setting, and local models
trade latency and hard-slice quality for an answer Doug can defend.**

When compliance asks why account numbers leave the building, the honest responses are
redaction, VPC hosted, or in-building inference. You measured the third. It is close on
the easy majority and materially worse on loan proceeds, and it is several times slower
on a laptop. That mix is what makes routing a serious design later instead of a slogan.

The FDE move is to respect the objection, run the eval on both providers, and refuse to
claim local is free. Also refuse to strand classmates or CI behind a GPU requirement.
Stub remains a first class provider.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital wants a chart-summarization model. Legal says discharge notes cannot go to a
public API. Their engineer installed a 7B local model and reports "it works."

What you find:

- Easy discharge notes: local within 1 point of the hosted pilot.
- Complex oncology notes: local 12 to 16 points worse.
- Latency 8 seconds local vs 2 seconds hosted.
- Their demo laptop has 64 GB RAM. Half the clinicians have 8 GB corporate laptops.
- CI calls the local model and fails when the daemon is down.

**Your task**

1. Rewrite "it works" into two sentences Legal and Engineering both accept.
2. What do you do for developers without 16 GB RAM?
3. Is all-local the right end state? Why or why not?
4. Name the CI rule that prevents weekend outages of the build.

---

**Notes, after you have written yours**

**Rewrite.** Local meets residency for default traffic and matches easy notes closely.
Complex oncology quality and latency remain gaps, so we need routing or a stronger
in-network model before broad rollout.

**Low RAM.** Stub fixtures or a tiny model for dev, full model in a shared VPC endpoint.

**End state.** Probably mixed: local or VPC for sensitive default path, stronger model
for hard slices under the same residency rules.

**CI rule.** Default provider stub. Optional nightly job for live local. Build must not
require a GPU daemon.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
