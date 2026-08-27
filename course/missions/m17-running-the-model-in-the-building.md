---
id: M17
slug: running-the-model-in-the-building
title: Running the Model in the Building
subtitle: "Compliance asks why account numbers are leaving the building. It is a fair question and it changes your architecture."
phase: 3
order: 17
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Explain the data residency objection in words Doug and Yuki accept
  - Run the txn-classification suite against Ollama with qwen3:8b, and against stub
  - Compare hosted and local results using canon deltas on easy versus loan proceeds
  - Sketch a routing direction for Mission 35 without pretending local wins everywhere
concepts: [local models, ollama, data residency, tco, latency, model routing]
competencies: [ai-fundamentals, architecture, security]
prereqs: [M16]
---

## Where you are

You have a classifier, an eval, and a slice report that made Marcus less cheerful. The
design doc for the next phase still says "call the hosted mid alias from ai-service."

Doug read that sentence. Yuki read the sentence after it, the one about sending statement
text that includes account numbers.

They asked for a meeting. They did not ask for a slide about innovation.

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

## The conversation

:::dialogue{title="Compliance and security, Tuesday 10:00 AM"}
**Doug:** Why are account numbers leaving the building?

**You:** Because the hosted model is what we eval'd first. It was the fast path.

**Yuki:** Fast for who.

**You:** For iteration. Not for production egress.

**Doug:** Can you explain that decision to an applicant in writing if their statement
text is retained by a vendor we do not control?

**You:** Not today.

**Yuki:** Then we are not deciding today to keep it that way.

**Priya:** Show me the blast radius of switching.

**You:** Local model on our hardware for sensitive spans. Hosted only where we can
justify it. I need a day to measure quality and latency.

**Janet:** Who is on call for the local box?

**You:** That is part of what I will write down.
:::

:::dialogue{title="Nadia, Slack DM, Tuesday 10:40 AM"}
**Nadia:** they are right

**You:** I know

**Nadia:** local will be slower and worse on the hard slice. measure it. do not sell
local as free quality.

**You:** and if local loses on loan proceeds?

**Nadia:** then you have a routing problem, not a morality play. that is a later
mission. today you prove you can run in the building.
:::

## What you know about the system

Provider switch is an environment variable. Mission 12 already showed the table.

| `LLM_PROVIDER` | What it does |
|---|---|
| `stub` | Recorded fixtures. Always available. Required fallback for this mission. |
| `ollama` | Model on your machine. |
| `openai` / `anthropic` | Hosted. Needs a key. |

Canon local setup:

| Fact | Value |
|---|---|
| Runner | Ollama on the learner laptop |
| Main model | `qwen3:8b` |
| Small model for routing | `qwen3:1.7b` |
| Backup comparison model | `llama3.1:8b` |
| Minimum practical hardware | 16 GB RAM (8 GB can run the 1.7b) |
| Northstar production plan | Two A10G instances in their own VPC |
| Laptop latency, 8b, ~400 token output | 6 to 11 seconds |
| Hosted latency, same task | 1.9 seconds |
| Local vs hosted, easy slice | Within 1 point |
| Local vs hosted, loan proceeds | 14 points worse |

Every path in this mission must also pass with `LLM_PROVIDER=stub`. A classmate on an 8
GB machine is not blocked from finishing the course.

## Evidence

### Install and health

```bash
# macOS / Linux, from lab/
make ollama-check
# pulls qwen3:8b if missing, fails loud if the daemon is down

curl -s localhost:11434/api/tags | jq '.models[].name'
```

:::evidence{type=log label="make ollama-check, healthy laptop"}
```text
ollama ok
models: qwen3:8b, qwen3:1.7b
RAM: 32 GB
```
:::

If you have 8 GB RAM, pull the small model and run the stub path for the graded work.
Still try one live local call on a tiny prompt so you have felt the latency.

```bash
ollama pull qwen3:1.7b
```

### Point ai-service at Ollama

```bash
export LLM_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
# model alias local-qwen8b is already in /v1/models

curl -s localhost:8000/v1/models \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m17-0001' | jq '.aliases["local-qwen8b"]'
```

### Run the eval both ways

```bash
cd lab

# always works
python -m northstar_evals run --suite txn-classification --provider stub \
  --json out/m17-stub.json

# local path (skip if hardware cannot hold 8b; use notes from canon below)
python -m northstar_evals run --suite txn-classification --provider ollama \
  --model qwen3:8b --json out/m17-ollama.json

python -m northstar_evals compare --suite txn-classification \
  --a stub --b ollama --model-b qwen3:8b
```

:::evidence{type=metrics label="compare report, canon numbers"}
```text
a=hosted-or-stub reference    b=qwen3:8b local

OVERALL                 delta ~ small
card_settlement         within 1 point of hosted/easy reference
loan_proceeds           14 points worse on local
internal_transfer       local trails
poor_ocr                local trails

latency p50
  hosted-ish reference  ~1.9s
  local 8b              6 to 11s
```
:::

Write those deltas into `customers/northstar/notes/m17-local-vs-hosted.md` even if your
laptop only ran stub. The canon numbers are the ones Northstar leadership will hear.

## What you do not know

- Final VPC sizing and who patches Ollama in production.
- Whether Doug will allow hosted calls with redaction instead of a full local path.
- Exact unit cost of two A10G under Northstar's cloud agreement.
- How routing will choose easy versus hard cases. That is Mission 35.

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

:::stopandthink
1. Doug's question is not anti-AI. What requirement is he actually stating?
2. If local matches within 1 point on the easy slice and loses 14 points on loan
   proceeds, is "we go all local" a complete architecture?
3. Latency moves from 1.9s to 6 to 11s. Who feels that, Hank or the batch job?
4. Why does this course insist the stub path keeps working?

Write answers. Question 2 is the bridge to Mission 35.
:::

## Working through it

### The wrong turn: privacy theater in the prompt

```text
# do not ship this as the control
System: Never send account numbers to an external service.
```

The model does not enforce network egress. Your HTTP client does. Yuki will say "say
just one more time" if you propose a prompt as the boundary.

The control is: which provider the service is allowed to call for which fields, enforced
in config and network policy.

### Run local for real

```python
# lab/evals/scripts/m17_local_smoke.py
import os
import httpx

os.environ["LLM_PROVIDER"] = "ollama"

payload = {
    "transactions": [
        {"txn_id": "TX-10001", "description": "STRIPE PAYOUT", "amount": 48230}
    ],
    "options": {"alias": "local-qwen8b", "temperature": 0.0, "max_output_tokens": 200},
}

r = httpx.post(
    "http://localhost:8000/v1/classify/transactions",
    json=payload,
    headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "m17-smoke"},
    timeout=120,
)
print(r.status_code, r.json()["meta"]["latency_ms"], r.json()["results"])
```

Expect multi-second latency. That is the laptop telling you the truth.

### TCO sketch (order of magnitude)

Use numbers you can defend in a room. Example arithmetic for the note:

```text
Hosted mid (from M12 aliases):
  $0.60 / 1M prompt tokens, $2.40 / 1M completion
  Rough classify+extract burden ~ 15k prompt + 1k completion tokens / app
  1,840 apps * 16k tokens ~= 29.4M tokens / month
  Blend ~ $1.00 / 1M average -> ~$30 / month for this slice alone
  (grows fast when you stuff policies into prompts later; see M34)

Local production plan: two A10G in VPC
  Assume ~$1.00 / GPU-hour on-demand style pricing for planning
  2 * 730 hours * $1.00 ~= $1,460 / month fixed
  Plus engineering time to keep it alive

Laptop latency 6-11s vs hosted 1.9s
  Interactive reviewer path feels it
  Overnight batch can hide it
```

Local is not cheaper at this volume for this narrow slice. Local is the answer to Doug's
egress question. Different objective functions. Say that plainly.

### Architecture that respects the measurement

```text
                    +------------------+
   statement text ->| classify router  |
                    +--------+---------+
                             |
              easy settlement |  hard / PII-heavy
                              |  (loan, transfer, SSN-ish)
                   +----------v----+   +------v-------+
                   | local qwen8b  |   | hosted mid*  |
                   +---------------+   +--------------+
                                         * only if Doug
                                           signs redaction
                                           or VPC hosted
```

You do not build the router today. You write the constraint that makes Mission 35 a
real design problem instead of a trick: local is good enough for the 84 percent easy
slice and not good enough for loan proceeds.

## Tests

```python
# lab/ai-service/tests/test_m17_provider_switch.py
import os
from fastapi.testclient import TestClient
from ai_service.main import app

client = TestClient(app)


def test_stub_path_still_classifies(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    r = client.post(
        "/v1/classify/transactions",
        json={
            "transactions": [
                {"txn_id": "TX-1", "description": "STRIPE PAYOUT", "amount": 100}
            ],
            "options": {"alias": "hosted-mid", "temperature": 0.0},
        },
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "m17-test"},
    )
    assert r.status_code == 200
    assert r.json()["results"]
```

```bash
cd lab/ai-service && pytest tests/test_m17_provider_switch.py -q
```

## Then this happens

:::dialogue{title="Follow-up with Doug and Yuki, Wednesday 9:30 AM"}
**You:** Local qwen3:8b runs. Easy slice within a point of hosted. Loan proceeds about
14 points worse. Latency 6 to 11 seconds on a laptop versus about 1.9 seconds hosted.
Stub path still passes for CI.

**Doug:** Will production keep statement text in our VPC for the default path?

**You:** That is the proposal. Hosted only with an explicit exception.

**Yuki:** Who can flip the provider env in prod?

**You:** Change control. Not the app process. I will put it in the runbook draft.

**Doug:** Can you explain that decision to the applicant in writing?

**You:** Yes. Their statement text for default classification stays on Northstar
infrastructure. If we ever send a redacted span outside, we will say so in the notice.
:::

Priya wants the blast radius in one paragraph. Give it to her.

:::evidence{type=slack label="#northstar-ai"}
```text
You:    Local path unblocks compliance review for Phase 4 docs work.
You:    Quality tradeoff is concentrated on loan proceeds (-14pts).
You:    That becomes a routing design, not a reason to abandon local.
Janet:  on call for the GPU box is still an open question
You:    agreed. parked under infra owners, not silent
```
:::

## The better version

- **Boundary in config and network**, not in prompt prose.
- **Measure local on the same golden set** you already trust, with slices on.
- **Keep stub green** so classwork and CI do not depend on GPUs.
- **Plan routing** where local handles easy volume and a stronger path handles money
  slices, once Doug agrees what may leave the building.

Mission 35 will turn that plan into code. This mission only makes the tradeoff
undeniable.

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

:::commslab
#### To Doug

> Default classification can run on in-network models so statement text does not go to a
> third party. We measured quality: easy traffic stays close, loan proceeds drop about 14
> points, so we will not claim local solves every case. Exceptions for hosted calls will
> be written, not implied.

#### To Yuki

> Provider selection is config under change control. Prompt text is not the egress
> control. Threat model draft will list who can flip `LLM_PROVIDER` and where secrets
> live.

#### To Priya

> Blast radius of the local path: new runtime dependency (Ollama or VPC GPUs), higher
> latency on interactive calls, and a known quality gap on loan proceeds that we will
> route around later. CI keeps using stub.
:::

## Practice

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
