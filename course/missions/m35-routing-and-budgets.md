---
id: M35
slug: routing-and-budgets
title: Routing and Budgets
subtitle: "Eighty four percent of volume is easy. Pay hosted rates for the part that is not."
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
concepts: [model routing, local inference, caching, token budgets, cost controls]
competencies: [coding, ai-fundamentals]
prereqs: [M17, M34]
---

## Where you are

Mission 34 named the bill. The full-corpus flag is off. Classify is pinned to a smaller
hosted model for now. Dale is calmer. Priya wants the steady-state design, not another
afternoon of flags.

You already installed Ollama and `qwen3:8b` back in Mission 17 because Doug and Yuki
did not want raw bank text leaving the building on every call. That decision is about
to become an engineering asset instead of a compliance compromise.

## The request

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

Marcus's question is accidentally useful. "The AI picks" is how you get loops. A
router you design is how you get a bill you can explain.

Nadia follows up privately.

:::evidence{type=slack label="Nadia, 9:18 AM"}
```text
Nadia:  Mission 17 already paid for this decision
Nadia:  do not re-litigate local vs hosted as religion
Nadia:  use the slice table. what would have to be true for local on hard cases

You:    hard slice within ~2 points of hosted. it is not.

Nadia:  then do not pretend. route.
```
:::

## The conversation

:::dialogue{title="Whiteboard with Sam and Tomás, Monday 10:15 AM"}
**Sam:** Mission 16 said card settlements are 84 percent of volume and 99 percent
accuracy.

**You:** Local qwen on that slice was within a point of hosted in Mission 17.

**Tomás:** Loan proceeds was fourteen points worse locally.

**You:** So we route. Easy local. Hard hosted. Unknown goes hosted or review.

**Sam:** Who decides easy?

**You:** Heuristics first. Description patterns, amount bands, prior labels. Not an
open-ended agent choosing models for fun.

**Tomás:** And cache?

**You:** Same sha256, same prompt version, same model. Redis. No second bill.

**Sam:** Budgets?

**You:** Per request tokens, per application dollars. Exceed means review, not a half
parsed JSON that Tomás has to unstick again.

**Tomás:** Appreciate that.
:::

Doug joins for five minutes because privacy is why local exists at all.

:::dialogue{title="Doug, doorway"}
**Doug:** If easy path is local, does hard path still leave the building?

**You:** Yes, until the A10G pair is ready. We log model and destination on every call.

**Doug:** Can you explain that decision to the applicant in writing if the hosted path
was used?

**You:** The decision reasons stay in reason codes. The model destination is an ops
fact, not an adverse action reason.

**Doug:** Keep it that way.
:::

## What you know about the system

From Mission 17 and the canon:

| Fact | Value |
|---|---|
| Local main model | `qwen3:8b` via Ollama |
| Small router / classifier assist | `qwen3:1.7b` |
| Hosted latency, same task | about 1.9 seconds |
| Local 8b latency, 400 token out | 6 to 11 seconds |
| Easy slice local vs hosted | within 1 point |
| Loan proceeds local vs hosted | 14 points worse |
| Easy volume share | 84 percent |

Every path must still run with `LLM_PROVIDER=stub` so a small laptop is never blocked.

Tomás asks the practical question nobody puts in architecture decks.

:::dialogue{title="After the whiteboard"}
**Tomás:** What if Ollama dies at 2 a.m. on easy volume?

**You:** Fail over to hosted for that request. Metric on failover. Do not wedge apps.

**Tomás:** And if hosted is also down?

**You:** Budget path already fails to review. Same destination. Humans keep working.

**Sam:** Write that in the runbook before Janet asks who is on call for Ollama.
:::

## Evidence

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

Overall looks fine. The money-moving slices do not. That is why routing exists.

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

Same file. Three pays.

:::evidence{type=schema label="CompletionResponse fields you already emit"}
```text
model, prompt_version, prompt_tokens, completion_tokens,
latency_ms, cost_usd, finish_reason, cost_basis
```
:::

## What you do not know

- Whether Northstar's eventual A10G pair will beat your laptop enough to change the cut
  line
- How reviewers will react to 6 to 11 second local latency on the easy path
- Whether a tiny local router model invents confidence it should not have
- What the per-application dollar budget should be for SBA vs term loans

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

:::stopandthink
Before you code the router:

1. If the router itself is a model call, what stops it from costing more than it saves?
2. What should happen when local is down but hosted is up?
3. Is latency a product problem for underwriters on the easy path?
4. Which wrong turn are you most likely to take: over-routing to local, or leaving
   everything hosted "to be safe"?

Write answers first.
:::

## Working through it

### The wrong turn

You build a clever router. A `qwen3:1.7b` call classifies difficulty in natural
language: "HARD" or "EASY". It works in the demo. In the eval set it marks 30 percent
of loan-proceeds cases EASY because the description looks like a normal credit.

:::evidence{type=test label="Router v0, model-decides-difficulty"}
```text
loan_proceeds routed_local: 29%
loan_proceeds accuracy when wrongly local: 49%
cost: down 22%
Hank's reaction after three bad files: not printable
```
:::

Natural language difficulty is not a control. Prefer boring rules:

```python
def route_txn(description: str, amount: Decimal, ocr_quality: str) -> str:
    if ocr_quality == "poor":
        return "hosted_strong"
    if looks_like_loan_proceeds(description):
        return "hosted_strong"
    if looks_like_internal_transfer(description):
        return "hosted_strong"
    if amount >= Decimal("25000") and looks_like_lump_credit(description):
        return "hosted_strong"
    return "local_qwen_8b"
```

Use the 1.7b model only for narrow assistive checks if at all, with a hard allowlist of
labels. Default unknown to hosted.

### Unit tests for boring rules

```python
def test_stripe_payout_routes_local():
    assert route_txn("STRIPE PAYOUT", Decimal("48230"), "good") == "local_qwen_8b"

def test_fastcapital_loan_routes_hosted():
    assert route_txn("FASTCAPITAL LOAN", Decimal("75000"), "good") == "hosted_strong"

def test_poor_ocr_routes_hosted_even_if_settlement_shaped():
    assert route_txn("STRIPE PAYOUT", Decimal("1200"), "poor") == "hosted_strong"

def test_large_lump_unknown_description_routes_hosted():
    assert route_txn("WIRE IN COMERICA", Decimal("90000"), "good") == "hosted_strong"
```

If a rule is not in a test, it will rot the first time someone "simplifies" routing.

### Building the pieces

**Routing.** Keep the decision in code you can unit test without a model.

**Caching.**

```python
def cache_key(tenant_id: str, sha256: str, prompt_version: str, model: str) -> str:
    return f"extract:{tenant_id}:{sha256}:{prompt_version}:{model}"
```

On hit, still write an `ai_invocations` row with `cost_usd=0` and `cost_basis=cache_hit`
so Mission 34 style investigations stay honest.

**Budgets.**

```python
@dataclass
class Budgets:
    max_prompt_tokens: int = 8000
    max_completion_tokens: int = 1200
    max_application_cost_usd: Decimal = Decimal("1.50")
```

If a call would exceed the prompt budget, refuse before send. If cumulative application
cost would exceed the cap, stop and mark `BUDGET_EXCEEDED` for human review.

**Fallback.** Local timeout or Ollama down: fail over to hosted for that request, emit a
metric, do not wedge the application.

### Then this happens

Routing ships behind a flag. Cost drops. Wendy reports the classify badge sometimes
spins for nine seconds.

:::evidence{type=slack label="Wendy Kaur, Tuesday 2:11 PM"}
```text
Wendy:  easy path is slow enough that people click away
Wendy:  they think it hung
Wendy:  if local is the default, show a progress state. do not make them guess

You:    fair. adding "running on-prem model" copy and a 15s timeout to hosted

Wendy:  also this is six clicks before they even see the suggestion
Wendy:  but that is a different ticket I already filed
```
:::

She is right about clicks. That fight is Phase 8. Your job today is not to ignore
latency while celebrating cost.

:::evidence{type=metrics label="Staging soak, routed + cache, 24 hours"}
```text
local_share ................................ 81%
hosted_share ............................... 19%
cache_hit_rate on reopen ................... 84%
cost vs prior week same volume ............. -38%
loan_proceeds accuracy ..................... 67.1% (hosted baseline 68.0)
card_settlement accuracy ................... 98.6%
p95 local classify latency ................. 9.4s
p95 hosted classify latency ................ 2.1s
budget_exceeded count ...................... 3 (all poor OCR multi-doc packets)
```
:::

:::evidence{type=test label="Budget exceed fails closed"}
```text
APP-45012: 4 statements, poor OCR, routed hosted repeatedly
cumulative cost hit $1.50 cap
status -> PENDING_INFO reason BUDGET_EXCEEDED
no truncated JSON written to document_extractions
```
:::

### The better version

Publish the contract:

| Traffic | Model | Why |
|---|---|---|
| Standard settlements, clean OCR | local `qwen3:8b` | 84% volume, within 1 pt |
| Loan proceeds, transfers, poor OCR, large lumps | hosted strong | quality gap is real |
| Cache hit | none | pay zero, log the hit |
| Budget exceeded | no model | human review |

Eval gate for the flag flip:

```text
routed overall >= hosted overall - 1.0
routed loan_proceeds >= hosted loan_proceeds - 2.0
cache hit rate on reopen >= 80% in staging soak
p95 local path latency documented, UI shows progress
```

`make ollama-check` for machines with models. `LLM_PROVIDER=stub` for CI.

:::evidence{type=slack label="Priya after reading model-routing.md"}
```text
Priya:  blast radius if local share spikes and loan_proceeds drops
You:    auto rollback to hosted-only when slice eval nightly fails gate
Priya:  put that in the runbook, not only in your head
You:    done. Janet reviewed the rollback section.
```
:::

The runbook section is five lines on purpose:

```text
1. Set MODEL_ROUTING_V1=false
2. Confirm hosted-only in /v1/models
3. Re-run make eval SUITE=txn-classification
4. Page if loan_proceeds < baseline-2
5. Leave cache on; cache is not the incident
```

Document the laptop reality for learners in the routing doc too: 16 GB RAM preferred,
`qwen3:1.7b` if 8 GB, and stub provider always green in CI. Local is a production
design choice for Northstar's privacy story. It is not a homework tax.

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

:::commslab
#### To Priya

> Routing design: local for the easy 84 percent, hosted for hard slices, cache on
> identical extractions, hard budgets per application. Eval gate attached. Blast radius
> if wrong is the loan-proceeds slice, so unknown defaults hosted.

#### To Doug and Yuki

> Easy-path bank text can stay on-prem with Ollama. Hard-path still leaves the building
> until Northstar's A10G pair is ready. Cache keys include tenant id.

#### To Janet

> On call notes: flag `MODEL_ROUTING_V1`, rollback is hosted-only. Metric to watch is
> `routing.local_share` and `eval.loan_proceeds`.
:::

## Practice

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
