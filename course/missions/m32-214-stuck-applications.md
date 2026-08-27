---
id: M32
slug: 214-stuck-applications
title: 214 Stuck Applications
subtitle: "Expected a number. Got \"$78,231 approximately\". Monitoring stayed green."
phase: 7
order: 32
duration: 300
difficulty: 5
lab: true
status: complete
objectives:
  - Run an incident from detection through containment, fix, recovery, and writeup
  - Separate schema failures from timeouts in retry policy
  - Explain why process health stayed green while 214 applications stuck
  - Recover work without double-decisioning applications
concepts: [incident response, structured output, retries, poison messages, workflow health]
competencies: [debugging, production-reliability, customer-communication]
prereqs: [M31]
---

## Where you are

Tuesday. Spans exist. Flags are on for a slice of `NSC_DIRECT` volume. You are in a
normal afternoon meeting when Carla's queue turns into a siren.

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

## The conversation

:::dialogue{title="Bridge call, 16:52 ET"}
**You:** When did it start?

**Sam:** Looking. First parser error at 14:02.

**Tomás:** Retry worker should have cleared transient failures.

**Sam:** ...Ah. So you found that.

**You:** Found what?

**Sam:** Retries that cannot tell a bad payload from a timeout.
:::

:::dialogue{title="Carla, still on the bridge"}
**Carla:** Do I keep telling people to resubmit?

**You:** No. Resubmit will hit the same path. We will put a banner up and take the
flag off if needed.

**Hank:** How many are stuck?

**You:** Counting now. Do not decision anything by hand until we have the list.
:::

## What you know about the system

From canon and earlier missions:

- Java expects `averageRevenue` as a number
- Stub scenario `revenue-as-string` returns `"$78,231 approximately"`
- Tomás wrote a retry worker for flaky timeouts
- Health checks test the process, not the workflow
- Spans from Mission 31 should show validation or parse failure if you look

## Evidence

:::evidence{type=log label="underwriting-service, 14:03 ET"}
```text
ERROR c.n.uw.RevenueParser - Cannot deserialize value of type java.math.BigDecimal
 from String value '$78,231 approximately'
ERROR c.n.uw.RevenueParseWorker - parse failed app=90112; scheduling retry 1/5
ERROR c.n.uw.RevenueParseWorker - parse failed app=90112; scheduling retry 2/5
...
ERROR c.n.uw.RevenueParseWorker - parse failed app=90112; scheduling retry 5/5
WARN  c.n.uw.RevenueParseWorker - moving app=90112 to RETRY_EXHAUSTED
```
:::

:::evidence{type=http label="Model payload that started it"}
```json
{
  "averageRevenue": "$78,231 approximately",
  "currency": "USD",
  "meta": {
    "model": "stub:hosted-v2",
    "prompt_version": "txn-v3",
    "finish_reason": "stop"
  }
}
```
:::

:::evidence{type=metrics label="Dashboards at 16:50"}
```text
ai-service /health                         green
underwriting-service /health               green
HTTP 5xx rate                              0.1%
parser error count (not on dashboard)      rising since 14:02
applications status=IN_REVIEW older 2h     214
```
:::

:::evidence{type=sql label="Stuck set"}
```sql
SELECT count(*) AS stuck
FROM northstar.applications
WHERE status = 'IN_REVIEW'
  AND updated_at < now() - interval '2 hours'
  AND application_id IN (
    SELECT application_id FROM northstar.application_events
    WHERE event_type = 'AI_REVENUE_RETRY_EXHAUSTED'
      AND created_at >= '2026-07-28 14:00:00-04'
  );
```
```text
 stuck
-------
   214
```
:::

:::evidence{type=trace label="trace for app 90112"}
```text
span model.complete        ok   latency=2104ms
span output.validate       fail status=schema_error
                           expected=number got=string
span underwriting.parse    fail BigDecimal deserialize
span retry.schedule        delay=30s attempt=3 reason=TIMEOUT   <-- wrong reason
```
:::

The last line is the heart of the incident. Validation already knew it was a schema
error. The retry worker labeled it TIMEOUT and paid for five completions.

## What you do not know

- Whether the provider change that introduced stringy revenue was a flag flip or a
  prompt edit
- How many of the 214 already have partial downstream side effects
- Whether applicants received SMS status messages that now lie

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

:::stopandthink
Before you dig into prompt archaeology:

1. What is the fastest containment that protects applicants right now?
2. Why did health checks stay green?
3. If you fix the parser to accept currency strings, what new bug do you create?
4. Who needs a status sentence in the next fifteen minutes: Hank, Carla, Dale?

Write it. Then move.
:::

## Working through it

### Contain first

Wrong order: spend forty minutes arguing about whether the model "should" have
returned a number while 214 files age.

Right order:

1. Flip `copilot.revenue.enabled` off for the affected tenants, or pause the retry
   consumer.
2. Tell Carla the banner text: do not ask applicants to resubmit.
3. Tell Hank his team should not manually force decision from partial AI state.
4. Snapshot the stuck application ids.

Only then dig.

### The wrong turn

A reasonable engineer "fixes" Java to parse currency strings and words like
approximately.

```java
// looks helpful, is not
cleaned = raw.replace("$", "").replace(",", "").replace("approximately", "").trim();
return new BigDecimal(cleaned);
```

That turns a loud failure into a quiet acceptance of fuzzy money. Doug will ask how you
explain "approximately" in an adverse action letter. You will not have a good answer.

Cost: you clear the queue today and invent a new class of unverifiable numbers for six
months.

### Real fix

1. Schema validation in ai-service fails closed on non-numeric `averageRevenue`.
2. Underwriting maps validation failure to `SCHEMA_ERROR`.
3. Retry worker retries timeouts and 503s only. Schema errors go to a dead letter and
   page.
4. Prompt or provider pin returns to a version that emits JSON numbers, as a
   separate change with an eval check.

```python
# retry policy sketch
if error_type == "SCHEMA_ERROR":
    dead_letter(app_id, payload, error_type)
    page("schema-error-non-retryable")
    return
if error_type in {"TIMEOUT", "PROVIDER_5XX"}:
    schedule_retry(app_id, attempt+1)
```

### Recover the 214

Replay from dead letter after the fix, idempotently.

:::evidence{type=sql label="Recovery guard"}
```sql
-- do not decision twice
SELECT application_id
FROM stuck_recovery_batch b
WHERE EXISTS (
  SELECT 1 FROM decisions d WHERE d.application_id = b.application_id
);
```
:::

Skip rows that somehow decisioned during the chaos. For the rest, rerun classify with
the good provider path and let the normal workflow continue. Watch spans while the
batch runs.

## Then this happens

Dale hears "two hundred fourteen" in a hallway and asks if the AI underwriter is down.

:::dialogue{title="Priya pulls you aside"}
**Priya:** Dale wants a sentence.

**You:** We had a bad model payload shape from 14:02 to when we flipped the flag. Two
hundred fourteen applications stalled in review. No incorrect approvals from this bug.
Support has banner text. We are replaying safely now.

**Priya:** Directionally correct enough. Do not say approximately.
:::

Humor is not welcome in that sentence. Precision is.

## Tracking it down

Timeline you should be able to reconstruct from evidence:

```text
14:02  first schema error
14:02-16:40 retries amplify cost and delay
16:47  Carla detects via tickets
16:52  bridge up
17:05  flag off / consumer paused
17:40  non-retryable schema errors shipped
18:30  recovery batch 1 running
```

Root cause chain:

1. Model returned a stringy money value
2. Parser threw
3. Retry treated it like a timeout
4. Health checks stayed green
5. Detection waited on support volume

Tomás is not the villain. His worker solved a real timeout problem. It needed an error
taxonomy.

## The better version

- Containment runbook exists and was used
- SCHEMA_ERROR is non-retryable
- Workflow success metric would have fired before 16:47
- Incident writeup names detection lag honestly
- No currency-string parser heroics

:::judgment
**Containment before diagnosis, and schema errors are not timeouts.**

Green hosting metrics during a workflow outage are normal. Design for that. When a
model returns the wrong shape, fail closed, page, and do not pay five times for the
same poison payload. When you recover, protect against double decisions first, pride
second.

The phrase "$78,231 approximately" is funny once. In production it is how you learn
whether your retries understand the failures they see.
:::

:::commslab
#### To Carla

> Do not tell applicants to resubmit. Banner text is live. We are clearing a stuck set
> from a bad AI payload shape. Status will move again after replay.

#### To Hank

> 214 IN_REVIEW files stalled after 14:02. No evidence of wrong approvals from this
> bug. Please hold manual force-decision until recovery marks a file ready.

#### To Janet

> On-call actions used: flag off, dead letter, non-retryable schema class, idempotent
> replay. Health checks were green the whole time. Follow-up is workflow success
> alerting.

#### To Dale (via Priya)

> We paused the AI revenue path after a bad payload format stalled 214 applications.
> Applicants were not auto-declined incorrectly. Replay is in progress. Full note after
> recovery.
:::

## Practice

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
