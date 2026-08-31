---
id: M35
slug: routing-and-budgets
title: Routing and Budgets
subtitle: >-
  Eighty four percent of volume is easy. Pay hosted rates for the part that is
  not.
phase: 7
order: 35
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - Route easy volume to a local model and hard cases to a hosted model
  - Add extraction caching keyed by document hash and prompt version
  - Enforce token and cost budgets per request and per application
  - Prove with evals that routing does not quietly burn the hard slices
concepts:
  - model routing
  - local inference
  - caching
  - token budgets
  - cost controls
competencies:
  - coding
  - ai-fundamentals
prereqs:
  - M17
  - M34
condensed: true
durationCondensed: 108
---
## Where you are

Mission 34 named the bill. The full-corpus flag is off. Classify is pinned to a smaller hosted model for now. Dale is calmer. Priya wants the steady-state design, not another afternoon of flags.

## Key artifacts

:::evidence{type=slack label="#northstar-ai, Monday 9:05 AM"}
```text
Priya:   cost brief landed. thanks.
Priya:   show me the blast radius of a routing design before we flip prod
Priya:   and Doug still wants PII options that do not default to vendor

Nadia:   what would have to be true for local to handle most volume safely?

You:     easy slice within a point of hosted. hard slice allowed to go hosted.
You:     and a budget so one application cannot spend twenty dollars.

Marcus:  can't the AI just pick the right model?
```
:::

:::evidence{type=slack label="Nadia, 9:18 AM"}
```text
Nadia:  Mission 17 already paid for this decision
Nadia:  do not re-litigate local vs hosted as religion
Nadia:  use the slice table. what would have to be true for local on hard cases

You:    hard slice within ~2 points of hosted. it is not.

Nadia:  then do not pretend. route.
```
:::

:::evidence{type=metrics label="Mission 17 eval remnant, still in baselines/"}
```text
slice                 hosted   qwen3:8b   delta
card_settlement       99.1     98.4       -0.7
internal_transfer     73.0     66.2       -6.8
loan_proceeds         68.0     54.1      -13.9
poor_ocr              61.0     52.4       -8.6
overall               96.0     93.1       -2.9
```
:::

## Evidence to use

:::evidence{type=slack label="#northstar-ai, Monday 9:05 AM"}
```text
Priya:   cost brief landed. thanks.
Priya:   show me the blast radius of a routing design before we flip prod
Priya:   and Doug still wants PII options that do not default to vendor

Nadia:   what would have to be true for local to handle most volume safely?

You:     easy slice within a point of hosted. hard slice allowed to go hosted.
You:     and a budget so one application cannot spend twenty dollars.

Marcus:  can't the AI just pick the right model?
```
:::

:::evidence{type=slack label="Nadia, 9:18 AM"}
```text
Nadia:  Mission 17 already paid for this decision
Nadia:  do not re-litigate local vs hosted as religion
Nadia:  use the slice table. what would have to be true for local on hard cases

You:    hard slice within ~2 points of hosted. it is not.

Nadia:  then do not pretend. route.
```
:::

:::evidence{type=metrics label="Mission 17 eval remnant, still in baselines/"}
```text
slice                 hosted   qwen3:8b   delta
card_settlement       99.1     98.4       -0.7
internal_transfer     73.0     66.2       -6.8
loan_proceeds         68.0     54.1      -13.9
poor_ocr              61.0     52.4       -8.6
overall               96.0     93.1       -2.9
```
:::

:::evidence{type=log label="ai-service without cache, reviewer reopen"}
```text
INFO  extract - document_sha=3f2c... prompt=v17 model=hosted-strong
      cache=MISS cost_usd=0.084 latency_ms=1904
INFO  extract - document_sha=3f2c... prompt=v17 model=hosted-strong
      cache=MISS cost_usd=0.084 latency_ms=1877
INFO  extract - document_sha=3f2c... prompt=v17 model=hosted-strong
      cache=MISS cost_usd=0.084 latency_ms=2011
```
:::

:::evidence{type=schema label="CompletionResponse fields you already emit"}
```text
model, prompt_version, prompt_tokens, completion_tokens,
latency_ms, cost_usd, finish_reason, cost_basis
```
:::

:::evidence{type=test label="Router v0, model-decides-difficulty"}
```text
loan_proceeds routed_local: 29%
loan_proceeds accuracy when wrongly local: 49%
cost: down 22%
Hank's reaction after three bad files: not printable
```
:::

## Your task

:::task{time="150 min"}
1. Implement a router in `ai-service` that sends the easy classification slice to local
   `qwen3:8b` (or stub) and hard / unknown cases to the hosted strong model.
2. Add Redis caching for extraction keyed by `(tenant_id, sha256, prompt_version,
   model)`.
3. Enforce a per-request token budget and a per-application cost budget. Exceeding
   budget must fail closed to review, not silently truncate mid-JSON.
4. Run `make eval SUITE=txn-classification` for hosted-only, local-only, and routed.
   Record overall and slice metrics.
5. Document the routing rules in `customers/northstar/model-routing.md` so Janet's team
   can own them.
:::

## Stop and think

:::stopandthink
Before you code the router:

1. If the router itself is a model call, what stops it from costing more than it saves?
2. What should happen when local is down but hosted is up?
3. Is latency a product problem for underwriters on the easy path?
4. Which wrong turn are you most likely to take: over-routing to local, or leaving
   everything hosted "to be safe"?

Write answers first.
:::

## One line to remember

:::judgment
**Routing is an engineering decision about measured slices, not a belief about which
vendor is winning the week.**

Mission 17 gave you the awkward truth: local is good enough for most volume and not
good enough for the cases that move money. Mission 34 showed what happens when you
ignore that and pay premium rates for everything, or panic-switch to cheap everywhere.
The FDE synthesis is a boring router, a cache that respects prompt versions, and budgets
that fail closed. If your router needs a paragraph to explain, it is probably an agent
in disguise. Prefer rules you can test without vibes.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital coding assistant. Local model matches hosted within 1 point on routine
outpatient codes (78 percent of volume). It is 11 points worse on rare inpatient
comorbidity bundles. Last month they ran everything hosted and blew the budget. A
doctor asks why the UI sometimes waits eight seconds.

**Your task**

1. Sketch the routing table.
2. Name two cache keys you need.
3. What budget failure mode keeps patients safer than truncation?
4. One sentence to the CMIO about latency.

---

**Notes, after you have written yours**

Route routine outpatient local, rare inpatient and low-confidence cases hosted. Cache
on `(patient_doc_hash, codebook_version, model)`. On budget exceed, stop and send to
human coding review. Never truncate a partial code list into the chart. Tell the CMIO
local path is slower by design for privacy and cost, and the UI must show progress so
clinicians do not re-click and double-submit.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
