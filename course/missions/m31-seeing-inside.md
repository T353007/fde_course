---
id: M31
slug: seeing-inside
title: Seeing Inside
subtitle: "A green health check is not a trace. You need spans that explain what the model did."
phase: 7
order: 31
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Add AI observability spans that carry model, prompt version, tokens, and validation
  - Persist invocation metadata so an on-call engineer can debug without replaying guesses
  - Prove that endpoint health is not workflow health
  - Use a slow stub scenario to practice reading latency in the right span
concepts: [tracing, spans, AI observability, audit logs, SLOs]
competencies: [production-reliability, coding, architecture]
prereqs: [M30]
---

## Where you are

The copilot is behind a flag. Prompts are versioned. Janet accepted the rollback drill.

Now Priya asks a question that sounds simple and is not: "When this is wrong at 2 a.m.,
how do we see inside it?"

## The request

:::evidence{type=slack label="#northstar-ai, Tuesday 9:00 AM"}
```text
Priya:  show me the blast radius
Priya:  also show me the trace for one real memo draft

Janet:  who is on call for that
Janet:  if the pager fires, what do they open first

Marcus: can we just look at CloudWatch

Sam:    CloudWatch will tell you it was slow. not why.
```
:::

Normal HTTP metrics will tell you ai-service returned 200 in 11 seconds. They will not
tell you which prompt version ran, which chunks were retrieved, or that JSON repair
ran twice before validation passed.

## The conversation

:::dialogue{title="Observability design, 9:30 AM"}
**You:** Every model call needs a span. Nested under retrieve, complete, validate.

**Janet:** What fields?

**You:** Model name, prompt version, prompt tokens, completion tokens, latency,
cost, finish reason, tenant, application id, validation result.

**Doug:** And enough to explain a decision later without inventing a story.

**Yuki:** Full bank transaction text in a trace store is also a data handling choice.
Say where it lives and who can read it.
:::

:::dialogue{title="Nadia, DM"}
**Nadia:** what would have to be true for "we logged the request" to be enough?

**You:** that the failure mode is always visible in status codes

**Nadia:** and is it?

**You:** no. the model can return 200 with garbage

**Nadia:** then log the shape of the garbage, not only the status
:::

## What you know about the system

`ai-service` already threads `X-Trace-Id`. There is an in-memory trace buffer and a
`GET /v1/traces/{traceId}` route sketched for this phase.

`ai_invocations` is the Postgres table you add in this mission. LAB_SPEC says it is
added by the learner here.

Health checks currently prove the process is up. They do not prove a classify then
parse then decide workflow works.

## Evidence

:::evidence{type=http label="A successful call that is still opaque"}
```bash
curl -s http://localhost:8000/v1/classify/transactions \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m31-opaque' \
  -H 'X-Stub-Scenario: slow-p99' \
  -d @fixtures/coastal-five.json | jq '{model: .meta.model, latencyMs: .meta.latency_ms}'
```
```json
{
  "model": "stub:qwen3:8b",
  "latencyMs": 11240
}
```
:::

Useful. Not enough. You still cannot answer: which prompt version, how many tokens,
did validation rewrite the payload, which application id was this for.

:::evidence{type=metrics label="Current dashboard, underwriting AI panel"}
```text
ai-service up                        yes
p50 latency                          1.9s
p99 latency                          11.2s
error rate                           0.2%
workflow success                     (not measured)
```
:::

:::evidence{type=slack label="Bill Tran, ops"}
```text
Bill:  if your new table needs a nightly patch I want to know now
Bill:  I already run fix_stuff.sh by hand when the other mismatch fails
You:   invocations table is append-only. no nightly rewrite
Bill:  It's fine, I run it by hand if it fails.
You:   this one should not need that
```
:::

## What you do not know

- How long Northstar will retain prompts that contain transaction text
- Whether reviewer portal will show span summaries to underwriters or only to eng
- What sampling rate finance will tolerate once cost fields are real

:::task{time="150 min"}
1. Create `ai_invocations` (migration) with at least: trace_id, tenant_id,
   application_id, route, model, prompt_version, prompt_tokens, completion_tokens,
   latency_ms, cost_usd, finish_reason, validation_status, created_at.
2. Emit nested spans for retrieve (if any), complete, and validate on classify and
   policy answer paths.
3. Expose `GET /v1/traces/{traceId}` with the span list for that request.
4. Add a red dashboard row or query that measures workflow success, not only HTTP 200.
5. Run `X-Stub-Scenario: slow-p99` and show the latency living on the complete span.

Lab: full stack. `LLM_PROVIDER=stub` is fine.
:::

:::stopandthink
Before you log everything:

1. Which fields must be always on for on-call, and which fields are PII-heavy?
2. If validation fails and you retry, is that one invocation or two?
3. What will look green during Mission 32 if you only monitor `/health`?
4. What is the wrong turn when leadership asks for "full prompt logging"?

Two minutes.
:::

## Working through it

### The wrong turn

The wrong turn is dumping full prompts and full completions into a shared debug bucket
with no access control because "we need visibility."

Yuki will block that, correctly. Transaction text and SSNs do not become free to browse
because your spans are pretty.

Do this instead:

- Always store metadata fields listed in the task
- Store hash of input, not raw statement text, in the default table
- Put raw prompt bodies in a restricted store or behind an explicit debug flag for a
  short retention window
- Document who can run the debug flag

### Span shape

```text
trace m31-opaque
  span classify.transactions            11240ms
    span model.complete                 11010ms  model=stub:qwen3:8b prompt=txn-v3
    span output.validate                  180ms  status=ok repairs=0
```

For policy answers:

```text
trace m31-policy
  span policy.answer
    span policy.retrieve
    span model.complete
    span output.validate
```

Each span gets attributes. The parent gets the rollup latency. On-call should be able
to open one trace id from a log line and see the story.

### Persist invocations

```sql
CREATE TABLE ai_invocations (
    invocation_id      BIGSERIAL PRIMARY KEY,
    trace_id           TEXT NOT NULL,
    tenant_id          TEXT NOT NULL,
    application_id     BIGINT,
    route              TEXT NOT NULL,
    model              TEXT NOT NULL,
    prompt_version     TEXT NOT NULL,
    prompt_tokens      INT,
    completion_tokens  INT,
    latency_ms         INT,
    cost_usd           NUMERIC(12,6),
    finish_reason      TEXT,
    validation_status  TEXT,
    input_sha256       TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Write the row after the call completes, including failures. A missing row on error is
how incidents stay mysterious.

### Workflow success

Add a definition Janet accepts:

```text
workflow_success =
  classify HTTP 200
  AND validation_status = ok
  AND underwriting parser accepted the payload
```

Until that last clause exists as a metric, you only know the model spoke. You do not
know the business moved.

## Tests

```python
def test_trace_includes_complete_and_validate_spans(client):
    response = client.post(
        "/v1/classify/transactions",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Trace-Id": "m31-spans",
            "X-Stub-Scenario": "slow-p99",
        },
        json=coastal_payload,
    )
    assert response.status_code == 200
    trace = client.get("/v1/traces/m31-spans").json()
    names = [s["name"] for s in trace["spans"]]
    assert "model.complete" in names
    assert "output.validate" in names
    complete = next(s for s in trace["spans"] if s["name"] == "model.complete")
    assert complete["latency_ms"] >= 9000


def test_ai_invocation_row_written(db, client):
    client.post("/v1/classify/transactions", headers=..., json=...)
    row = db.fetch_one("select * from ai_invocations where trace_id=%s", "m31-spans")
    assert row["prompt_version"]
    assert row["validation_status"] == "ok"
```

## Then this happens

Marcus wants a live "AI thinking" panel in the portal that streams token counts to
underwriters.

:::dialogue{title="Wendy and Marcus"}
**Marcus:** It would build trust.

**Wendy:** It would add clicks and noise. They need the revenue number and the flags.

**You:** Eng can have the trace link. Reviewers get the result and the reason codes.

**Marcus:** Fine. But I want the link in the support tool for Carla.

**You:** Agreed, with role checks.
:::

That compromise is the product judgment. Observability is not the same as exposing
every span to every user.

## Tracking it down

Run one slow call and one fast call. Confirm the p99 pain sits on `model.complete`,
not on Postgres. If someone "optimizes" the API gateway while the model is slow, you
will waste a week. Spans stop that argument.

## The better version

- Traces answer on-call questions in minutes
- Invocations are queryable by application id
- PII policy for prompt bodies is written down
- Health checks remain, and workflow success sits beside them
- You are ready for Tuesday in Mission 32, when green health will lie

:::judgment
**If you cannot see model, prompt version, tokens, and validation on one trace, you do
not have AI observability. You have hosting metrics.**

Ship spans before you need them. The night you need them, you will not have time to
design a schema. And when someone asks for full prompt dumps, separate debug power from
default logging so security does not have to choose between blindness and leakage.
:::

:::commslab
#### To Janet

> On-call opens GET /v1/traces/{id} from the log line. Invocation rows land in
> Postgres. Workflow success is a separate panel from process health.

#### To Yuki

> Default table stores metadata and input hash. Raw prompt bodies are flag-gated with
> short retention. Need your sign-off on the flag role list.

#### To Priya

> Blast radius of missing spans: slow incidents and silent schema failures. This mission
> closes the first. Mission 32 will test the second.

#### To Bill

> No new cron. Append-only table. If inserts fail, pager eng, do not patch by hand.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A support-copilot team only monitors API Gateway 5xx and CPU. Users report "answers
feel weird." The model returns 200 with confident wrong citations. Leadership asks for
complete prompt logging into a shared Slack channel for a week.

**Your task**

1. What spans and fields do you add first?
2. Why is Slack the wrong turn?
3. What metric would have caught weird-but-200 answers?

---

**Notes, after you have written yours**

Add complete and validate spans with model, prompt version, tokens, citation ids,
validation status. Slack is wrong because prompts contain customer text and because
chat is not an audit store. A validation or groundedness failure rate next to HTTP
success would catch weird-but-200. Same lesson as Northstar with different furniture.
:::
