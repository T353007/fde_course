---
id: M33
slug: the-vendor-said-200
title: The Vendor Said 200
subtitle: >-
  HTTP 200 with an empty account list is not success. Your code treated it like
  zero revenue and declined people.
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
concepts:
  - vendor integration
  - transport vs semantic success
  - fail closed
  - stale connections
competencies:
  - debugging
  - production-reliability
prereqs:
  - M32
condensed: true
durationCondensed: 84
---
## Where you are

Mission 32 is closed. The 214 stuck applications are recovered. Tomás's retry worker no longer treats a schema error like a timeout. Your writeup is in the shared drive. Carla's ticket volume is back to normal.

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

## Your task

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

## Stop and think

:::stopandthink
Before you change anything:

1. Is the bug in Ledgerlink, in your client, or in the decision policy?
2. If you "fix" it by declining only when revenue is below the floor *and* accounts
   is non-empty, what happens to a real business with a true empty account?
3. What is the blast radius if seven declines already went out overnight?
4. Would your health check have caught this? Why or why not?

Write the answers down. Two minutes.
:::

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
