---
slug: exam-04-incident
title: "Exam 04: Incident"
subtitle: Timed events. Contain first. Root cause second. Write it up like an adult.
kind: exam
order: 4
duration: 90
competencies: [production-reliability, debugging, executive-communication, customer-communication]
---

## Clock starts

You are on call for the Northstar AI slice.

:::evidence{type=timeline label="Incident clock"}
```text
14:02  Model responses for revenue_summary_v1 start returning
       averageRevenue as a string: "$78,231 approximately"
14:08  Java parser throws. Retry worker retries 5x with backoff.
14:40  Queue depth rising. Health checks still green.
15:10  Carla: ticket spike, applicants asking why status is stuck.
16:00  Hank: "my queue is frozen."
16:47  You are paged because of ticket volume, not because of an alert.
```
:::

## Deliverables

1. Impact statement at 16:50 (who/what/how many).
2. Containment actions in order, with who does each.
3. Root cause in two sentences.
4. Recovery plan for stuck applications.
5. Monitoring gap and the alert you will add.
6. Incident report outline (not a novel).
7. Three audience updates: engineer Slack, Hank, Dale.

:::stopandthink
Order matters. If your first step is "fix the prompt," you fail containment.
:::

:::spoiler{label="Answer key and rubric"}
**Containment order**

1. Disable legacy model revenue summary path / stop the retry worker for SCHEMA_ERROR.
2. Pause intake into the broken path if needed.
3. Count stuck apps (expect ~214).
4. Fail open to human review with naive-or-last-known handling, not silent zero.
5. Then fix schema boundary and typed retry.

**Root cause**

Model returned a non-numeric string for a field Java parses as BigDecimal. Retry logic treated every failure like a transient timeout, amplifying paid calls and leaving apps stuck. Health checks tested the process, not the workflow.

**Alert**

Workflow success rate and stuck-app age, plus parse failure kind counts. Not only HTTP 5xx.

**Dale update**

Deals are delayed, not wrongly declined (if true). ETA for recovery. What you will prevent next. No model jargon.

**Rubric**

| Score | Behavior |
|---|---|
| 4 | Containment before fix, typed failure lesson, honest exec update |
| 3 | Good fix, soft on containment order |
| 2 | Root cause right, recovery vague |
| 1 | Restarts pods and hopes |
:::
