---
id: M31
slug: seeing-inside
title: Seeing Inside
subtitle: >-
  A green health check is not a trace. You need spans that explain what the
  model did.
phase: 7
order: 31
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - >-
    Add AI observability spans that carry model, prompt version, tokens, and
    validation
  - >-
    Persist invocation metadata so an on-call engineer can debug without
    replaying guesses
  - Prove that endpoint health is not workflow health
  - Use a slow stub scenario to practice reading latency in the right span
concepts:
  - tracing
  - spans
  - AI observability
  - audit logs
  - SLOs
competencies:
  - production-reliability
  - coding
  - architecture
prereqs:
  - M30
condensed: true
durationCondensed: 96
---
## Where you are

The copilot is behind a flag. Prompts are versioned. Janet accepted the rollback drill.

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

## Your task

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

## Stop and think

:::stopandthink
Before you log everything:

1. Which fields must be always on for on-call, and which fields are PII-heavy?
2. If validation fails and you retry, is that one invocation or two?
3. What will look green during Mission 32 if you only monitor `/health`?
4. What is the wrong turn when leadership asks for "full prompt logging"?

Two minutes.
:::

## One line to remember

:::judgment
**If you cannot see model, prompt version, tokens, and validation on one trace, you do
not have AI observability. You have hosting metrics.**

Ship spans before you need them. The night you need them, you will not have time to
design a schema. And when someone asks for full prompt dumps, separate debug power from
default logging so security does not have to choose between blindness and leakage.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
