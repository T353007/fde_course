---
id: M33
slug: the-vendor-said-200
title: The Vendor Said 200
subtitle: "HTTP 200 with an empty account list is not success. Your code treated it like zero revenue and declined people."
phase: 7
order: 33
duration: 210
difficulty: 4
lab: true
status: complete
objectives:
  - Separate transport success from semantic success in a third-party response
  - Trace a silent vendor failure from a declined application back to the wire
  - Design a check that fails closed when a bank connection has gone stale
  - Explain the failure to ops and underwriting without blaming the vendor alone
concepts: [vendor integration, transport vs semantic success, fail closed, stale connections]
competencies: [debugging, production-reliability]
prereqs: [M32]
---

## Where you are

Mission 32 is closed. The 214 stuck applications are recovered. Tomás's retry worker
no longer treats a schema error like a timeout. Your writeup is in the shared drive.
Carla's ticket volume is back to normal.

It is Thursday morning. Hank Slack-messages you a list of seven applications that were
declined overnight for "insufficient revenue." He wants to know if the AI is broken
again.

## The request

:::evidence{type=slack label="#underwriting-ops, Thursday 8:14 AM"}
```text
Hank:    seven declines overnight on "insufficient revenue"
Hank:    Renee looked at two. Both have real bank accounts. Real deposits.
Hank:    What does that do to my queue if this is a pattern

Renee:   APP-44891. I pulled the Ledgerlink raw. accounts array is empty.
Renee:   We don't use that number.

You:     empty how. error page empty, or 200 empty

Renee:   I do not know what that means. The UI said connected.
```
:::

Hank's question is not about accuracy. It is about whether his people should trust the
system this morning. After Mission 32, that trust is thin. A quiet wrong decline is worse
than a loud outage, because nobody pages on a green dashboard.

## The conversation

:::dialogue{title="Hank's office, Thursday 8:40 AM"}
**Hank:** Walk me through APP-44891.

**You:** Declined at 02:11. Reason code INSUFFICIENT_REVENUE. Average monthly revenue
recorded as 0.00.

**Hank:** Renee says they cleared 40k last month on Stripe alone.

**You:** The bank link shows connected in the portal.

**Hank:** So the AI decided they make nothing.

**You:** Something decided they make nothing. I do not know which layer yet.

**Hank:** What does that do to my queue?

**You:** If it is a vendor stale connection, every auto decline on revenue tonight is
suspect. I need two hours before we let those go out.

**Hank:** Do it. And tell me when I can release the holds.

**You:** I need Renee on the first two while I pull the vendor raw for all seven.

**Hank:** She is already on them. She does not trust the revenue field. Never has.
:::

On the walk back to your desk, Carla catches you.

:::dialogue{title="Hallway, 8:52 AM"}
**Carla:** Three of those seven called support before they got the decline letter. They
said the bank badge was green. We told them to reconnect. That is the wrong script if
the token is stale in a way the badge cannot see.

**You:** What do you tell them now?

**Carla:** Oh, that. Yeah, we just tell them to resubmit. Which is also wrong if we
already declined them.

**You:** Hold language until I confirm. I will give you a sentence by 10.
:::

## What you know about the system

Ledgerlink is the bank aggregation vendor. Application flow calls it when an applicant
connects a bank, and again when underwriting refreshes balances before a decision.

The happy path looks like this:

```text
POST /v1/connections/{id}/accounts
Authorization: Bearer ...
→ HTTP 200
{
  "connectionStatus": "ACTIVE",
  "accounts": [
    {"accountId": "...", "name": "Business Checking", "balance": 41200.11}
  ]
}
```

Your client treats HTTP 200 as success. It maps `accounts` into the revenue path. An
empty list becomes "no deposits," which becomes average revenue 0.00, which becomes a
decline when the policy floor is anything above zero.

That chain is the whole mission.

## Evidence

Inject the failure and watch it live.

```bash
make inject SCENARIO=ledgerlink-empty-200
```

Then open APP-44891 in the lab seed set and refresh the bank connection.

:::evidence{type=http label="Ledgerlink stub, APP-44891 refresh, 02:09:44 ET"}
```http
POST /v1/connections/conn_9f2a/accounts HTTP/1.1
Host: vendors:8090
X-Tenant-Id: NSC_DIRECT
X-Trace-Id: trc_44891_0209

HTTP/1.1 200 OK
Content-Type: application/json

{
  "connectionStatus": "ACTIVE",
  "accounts": [],
  "asOf": "2026-06-18T06:09:44Z",
  "error": null
}
```
:::

:::evidence{type=log label="underwriting-service, 02:09:45 ET"}
```text
INFO  c.n.uw.vendor.LedgerlinkClient - Ledgerlink accounts ok status=200
      connectionId=conn_9f2a accountCount=0 latencyMs=118
INFO  c.n.uw.revenue.RevenueRefreshJob - revenue refresh complete
      applicationId=44891 averageMonthlyRevenue=0.00 source=LEDGERLINK
INFO  c.n.uw.decision.DecisionEngine - decision=DECLINED
      reason=INSUFFICIENT_REVENUE applicationId=44891
```
:::

:::evidence{type=sql label="decisions + bank_transactions for APP-44891"}
```sql
SELECT d.application_id, d.decision, d.reason_codes, d.decided_at
FROM decisions d
WHERE d.application_id = 44891;

-- 44891 | DECLINED | INSUFFICIENT_REVENUE | 2026-06-18 02:11:02-04

SELECT COUNT(*) AS txn_count, COALESCE(SUM(amount),0) AS credit_sum
FROM bank_transactions
WHERE application_id = 44891 AND amount > 0;

-- txn_count=0 | credit_sum=0
```
:::

The portal still shows the connection as green. Carla's ticket for this applicant says
the owner "reconnected three times and it still says connected."

:::evidence{type=ticket label="CS-22841, Carla Mendes"}
```text
Applicant says bank is linked. Portal badge is green. Underwriting says
revenue is zero. Told them to disconnect and reconnect. Same result.
Escalating.
```
:::

:::evidence{type=metrics label="Overnight declines tagged INSUFFICIENT_REVENUE"}
```text
02:00-06:00 ET
  declines with reason INSUFFICIENT_REVENUE ............... 11
  of those with Ledgerlink ACTIVE + accountCount=0 ........ 7
  of those with accounts present and true zero credits .... 4
  health.check.ledgerlink ................................. green (HTTP probe only)
```
:::

Seven of eleven is not noise. Four real zeros exist in the same window. Any fix that
treats every zero as stale will create a different lie.

:::evidence{type=slack label="Bill Tran, 9:05 AM"}
```text
Bill:  is this related to fix_stuff.sh
Bill:  that one patches a nightly mismatch, not Ledgerlink

You:   different failure. leave the cron alone

Bill:  It's fine, I run it by hand if it fails.
Bill:  just checking
```
:::

## What you do not know

- How many live connections are currently returning empty account lists
- Whether Ledgerlink marks stale links as ACTIVE on purpose
- Whether any underwriter override path catches this before the letter goes out
- Whether Bayline and Cascade use the same Ledgerlink client path
- What "connected" in the portal actually means in code

:::task{time="90 min"}
1. Reproduce APP-44891 with `make inject SCENARIO=ledgerlink-empty-200`.
2. Trace from the HTTP response to the decline. Name every function that treated
   empty accounts as a valid zero-revenue result.
3. Query how many applications in the last 48 hours have `averageMonthlyRevenue = 0`
   and a Ledgerlink connection that still reports `ACTIVE`.
4. Write a failing test that asserts: HTTP 200 with `accounts: []` is not a successful
   revenue refresh.
5. Propose the smallest code change that fails closed (hold for review, do not decline)
   when this shape appears.
:::

:::stopandthink
Before you change anything:

1. Is the bug in Ledgerlink, in your client, or in the decision policy?
2. If you "fix" it by declining only when revenue is below the floor *and* accounts
   is non-empty, what happens to a real business with a true empty account?
3. What is the blast radius if seven declines already went out overnight?
4. Would your health check have caught this? Why or why not?

Write the answers down. Two minutes.
:::

## Working through it

### The wrong turn

A reasonable first move is to page Ledgerlink and ask why they returned 200. You open a
vendor ticket. Their reply arrives in 40 minutes.

:::evidence{type=email label="Ledgerlink support, Thursday 9:22 AM"}
```text
Hi,

HTTP 200 with an empty accounts array is expected when the end-user
connection token is expired or the institution requires re-auth.
connectionStatus may still show ACTIVE until the next full sync.

Please check item.login_required in the connection metadata and prompt
the user to reconnect.

This is documented in section 4.2 of the Accounts API guide.

Regards,
Ledgerlink Support
```
:::

So the vendor is not down. Your monitoring is green. The API behaved as designed. Your
code assumed that transport success plus a parseable body meant semantic success.

That assumption is the defect. Blaming the vendor burns an hour and does not stop the
next decline.

### Tracking it down

Read the client. It probably looks like this shape in the lab:

```java
public AccountsResponse fetchAccounts(String connectionId) {
    ResponseEntity<AccountsResponse> resp = restTemplate.exchange(
        "/v1/connections/{id}/accounts",
        HttpMethod.POST,
        entity(connectionId),
        AccountsResponse.class,
        connectionId
    );
    if (!resp.getStatusCode().is2xxSuccessful()) {
        throw new VendorTransportException("ledgerlink", resp.getStatusCode());
    }
    return resp.getBody();
}
```

Then the revenue refresh:

```java
AccountsResponse accounts = ledgerlink.fetchAccounts(connectionId);
BigDecimal revenue = revenueFromAccounts(accounts.accounts());
application.setAverageMonthlyRevenue(revenue);
```

`revenueFromAccounts` on an empty list returns `BigDecimal.ZERO`. The decision engine
compares zero to the policy floor and declines. Every step is locally reasonable. The
chain is wrong.

Semantic checks belong next to the transport check:

```java
if (resp.getStatusCode().is2xxSuccessful()) {
    AccountsResponse body = resp.getBody();
    if (body == null || body.accounts() == null || body.accounts().isEmpty()) {
        throw new VendorSemanticException(
            "ledgerlink",
            "EMPTY_ACCOUNTS",
            "HTTP 200 with empty accounts; treat as stale connection"
        );
    }
    return body;
}
```

And the decision path must not map that exception to a decline. Map it to
`PENDING_INFO` or a human review reason like `BANK_LINK_STALE`.

### Then this happens

You ship the semantic check. Declines on empty accounts stop. An hour later Ada pings
you.

:::evidence{type=slack label="DM from Adaeze Nwosu, 11:05 AM"}
```text
Ada:   APP-44902 just went PENDING_INFO with BANK_LINK_STALE
Ada:   applicant has one account with a $12 balance and no credits in 90 days
Ada:   that one is actually empty. your new check is holding real zeros too?

You:   accounts array length?

Ada:   one account. empty of money, not empty of accounts.

You:   ok. different shape. leave that one in review. thanks.
```
:::

Empty *accounts list* is stale. Empty *balances* can be a real decline. You almost
collapsed those into one rule. That would have blocked legitimate zero-revenue cases
and trained Hank to ignore `BANK_LINK_STALE`.

### The better version

Fail closed on the stale shape only:

| Response shape | Meaning | System action |
|---|---|---|
| HTTP 5xx / timeout | Transport failure | Retry with budget, then hold |
| HTTP 200, `accounts: []` | Semantic failure, stale link | Hold, ask applicant to re-auth |
| HTTP 200, accounts present, all zero | Possible real zero revenue | Continue underwriting with reason codes |
| HTTP 200, accounts present, credits found | Normal path | Continue |

Add a metric: `vendor.ledgerlink.empty_accounts_total`. Alert when it rises. A green
HTTP status alone is not a health signal for this dependency.

Also fix the portal badge. "Connected" must mean "returned at least one account on the
last successful refresh," not "we once got a token."

### Saying it to the vendor without losing the morning

You still reply to Ledgerlink support. You need their metadata field names documented
for Janet's team. You do not wait on them to stop the declines.

:::evidence{type=email label="Your reply to Ledgerlink, 9:35 AM"}
```text
Thanks. We will treat HTTP 200 + empty accounts as login_required / stale
and hold underwriting instead of scoring revenue as zero.

Please confirm the exact metadata field we should read for re-auth on
API version we are pinned to (we are on Accounts API v3). We will add
that to our client this week.

We are not opening this as a vendor outage. We are fixing our semantic
handling.
```
:::

Priya asks for blast radius in one paragraph. Give her numbers, not feelings.

:::evidence{type=slack label="Reply to Priya, 9:50 AM"}
```text
You:  Blast radius: every auto revenue refresh that trusts Ledgerlink
      account lists without checking length. Overnight: 7 false zero
      declines, 4 true zeros in same bucket. Fix: semantic exception to
      PENDING_INFO/BANK_LINK_STALE. Portal badge meaning changes with it.
      Janet on call for the client. No vendor outage process needed.
```
:::

## Tests

```java
@Test
void emptyAccountsOnHttp200IsSemanticFailure() {
    stubLedgerlinkEmpty200("conn_9f2a");

    assertThrows(VendorSemanticException.class,
        () -> ledgerlinkClient.fetchAccounts("conn_9f2a"));
}

@Test
void emptyAccountsDoesNotAutoDecline() {
    seedApplication(44891);
    stubLedgerlinkEmpty200("conn_9f2a");

    Decision d = decisionEngine.evaluate(44891);

    assertEquals("PENDING_INFO", d.status());
    assertTrue(d.reasonCodes().contains("BANK_LINK_STALE"));
}
```

Run them with the injected scenario still on. Then clear it:

```bash
make clear-scenarios
```

:::judgment
**A 200 from a vendor is a claim about the HTTP layer, not a claim about the business
fact you needed.**

Transport success means the bytes arrived and parsed. Semantic success means the
payload is a trustworthy answer to the question you asked. Third-party APIs love to
put failure modes inside 200 bodies. Empty lists, null objects, `status: ACTIVE` with
`login_required: true`, reason codes in a side field. If your client only checks the
status code, you will manufacture confident wrong answers.

In lending, the wrong answer is not a display bug. Zero revenue declines a real
business. The FDE move is to invent explicit semantic predicates for every vendor call
that can fail while smiling, and to fail closed into human review when those predicates
trip. Monitoring that only watches latency and 5xx rates will stay green while you hurt
customers.
:::

:::commslab
#### To Hank

> Seven overnight declines on insufficient revenue look wrong. At least one is a stale
> bank link that returned an empty account list with HTTP 200. I am holding auto
> declines on that shape and reviewing the seven by hand. I will release your queue
> once the hold reason is live.

#### To Carla

> When the portal says connected but revenue is zero, ask whether Ledgerlink returned
> accounts. Reconnect alone may not clear a stale token. We are adding a clearer
> applicant prompt for re-auth.

#### To Priya

> Blast radius is every revenue decision that trusts Ledgerlink without checking account
> count. Fix is a semantic exception and a hold path, not a vendor outage process. I
> want Janet's team on call for the client change.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You are embedding at a property insurer. Their weather vendor returns:

```http
HTTP/1.1 200 OK

{"events": [], "coverageWindowHours": 72, "status": "OK"}
```

Your quoting service treats empty `events` as "no storm risk" and offers a discount.
Yesterday a coastal ZIP got discounted while a named storm was 40 miles offshore. The
vendor later said empty `events` means "feed unavailable for that ZIP," not "no
storms."

**Your task**

1. Name the transport claim and the semantic claim your code mixed up.
2. Write the hold condition in one sentence.
3. What metric would have caught this before a customer complaint?
4. Draft the Slack message to the pricing lead in under 80 words.

---

**Notes, after you have written yours**

Transport claim: HTTP 200, JSON parsed. Semantic claim: there are no relevant weather
events in the coverage window. Those are different. Empty `events` with `status: OK` is
still an untrusted answer if the vendor documents it as feed gap.

Hold condition: if `events` is empty, do not apply a no-storm discount; route to manual
review or a secondary feed.

Metric: count of quotes where `events` was empty, by ZIP. Spike equals feed gaps, not
calm weather.

Slack to pricing: say you are suspending the discount on empty feeds, name the ZIP
incident, and give a time for the secondary-feed check. Do not lead with "the vendor
screwed up." Lead with customer impact and the control you put in place.
:::
