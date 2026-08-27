---
slug: exam-02-debugging
title: "Exam 02: Debugging"
subtitle: Source code, logs, metrics, and a wrong number. Nobody tells you the root cause.
kind: exam
order: 2
duration: 120
competencies: [debugging, architecture, production-reliability]
---

Timed practical. You get evidence only. Write your root cause hypothesis before the answer key.

## Situation

Northstar's underwriter review screen shows operating revenue of $0 for application `APP-88421`. The bank connection status is "Connected." The applicant is angry. Hank's queue is backing up.

## Evidence

:::evidence{type=http label="GET /ledgerlink/v1/connections/conn_991/accounts"}
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "accounts": [],
  "connectionId": "conn_991",
  "status": "READY"
}
```
:::

:::evidence{type=log label="underwriting-service 11:42:18 ET"}
```text
INFO  c.n.uw.BankRevenueService - fetched accounts for app=88421 count=0
INFO  c.n.uw.BankRevenueService - computed monthlyRevenue=0.00
INFO  c.n.uw.DecisionService - autoDecline candidate app=88421 reason=INSUFFICIENT_REVENUE
WARN  c.n.uw.DecisionService - autoDecline blocked by flag ENABLE_AUTO_DECLINE=false
```
:::

:::evidence{type=metrics label="ledgerlink client, last 24h"}
```text
http_client_requests_seconds{client="ledgerlink",status="2xx"}  count=412  p50=180ms  p99=2.1s
http_client_requests_seconds{client="ledgerlink",status="5xx"}  count=0
http_client_errors_total{client="ledgerlink"}  0
business_empty_account_list_total  37
```
:::

:::evidence{type=sql label="bank_connections for APP-88421"}
```text
 connection_id | applicant_id | status  | last_sync_at          | vendor_status
---------------+--------------+---------+-----------------------+---------------
 conn_991      | 44102        | ACTIVE  | 2026-03-02 09:11:00   | READY
```
:::

:::evidence{type=slack label="Bill Tran, ops"}
```text
Bill:  oh that. when ledgerlink goes stale it still says READY
Bill:  I re-auth them by hand when underwriters complain
Bill:  maybe twice a week?
```
:::

## Your deliverables

1. What is your root cause hypothesis?
2. What evidence supports it, and what would falsify it?
3. Why did monitoring stay green?
4. Immediate containment (next 30 minutes).
5. Durable fix (next sprint).
6. Who do you tell, and in what order?

:::stopandthink
Write all six answers before opening the key.
:::

:::spoiler{label="Answer key and rubric"}
**Root cause**

Ledgerlink returned HTTP 200 with an empty account list for a stale connection. The client treated transport success as business success and computed revenue as zero. Auto-decline was luckily behind a flag. Bill's manual re-auth is the undocumented load-bearing workaround.

**Why monitoring was green**

Health and HTTP metrics track status codes, not semantic emptiness. `business_empty_account_list_total` exists but nobody alerted on it.

**Containment**

1. Stop auto-decline if the flag is about to ship.
2. Queue applications with empty account lists for manual review.
3. Page Bill's re-auth path and do it for the current queue.
4. Tell Hank the queue will spike with review work, not silent declines.

**Durable fix**

Treat empty accounts with `status=READY` and stale `last_sync_at` as an error. Distinguish transport / schema / semantic / business success. Alert on empty-account rate. Replace Bill's manual path with a forced re-auth workflow.

**Comms order**

Hank (queue), Carla (applicant tickets), Priya (blast radius), then Dale only if declined apps already went out.

**Rubric**

| Score | Behavior |
|---|---|
| 4 | Names semantic vs transport success, containment before rewrite, uses Bill's tip |
| 3 | Finds empty-list bug, thin on monitoring lesson |
| 2 | Blames "Ledgerlink is down" despite 200s |
| 1 | Proposes retrying the same call harder |
:::
