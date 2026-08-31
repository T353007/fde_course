---
id: M40
slug: what-belongs-in-the-product
title: What Belongs in the Product
subtitle: >-
  Two customers is the earliest you can responsibly abstract. It is also early
  enough to abstract the wrong thing for eight imaginary ones.
phase: 9
order: 40
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Sort capabilities into platform, adapter, config, and customer-specific
    forever
  - Resist designing for eight customers when you have two
  - >-
    Extract a thin platform seam from Northstar and Redwood without a framework
    fantasy
  - >-
    Explain the product boundary to Halyard and to both customers in plain
    language
concepts:
  - productization
  - platform vs adapter
  - configuration
  - premature abstraction
competencies:
  - architecture
  - productization
prereqs:
  - M39
condensed: true
durationCondensed: 108
---
## Where you are

Redwood's Monday packet path works without `customer.equals` in the revenue guts. Halyard's product lead wants "the platform." A slide has appeared with eight verticals on it. You have two real deployments and a rumor named Meridian.

## The request

:::evidence{type=email label="Halyard product, Thursday 9:20 AM"}
```text
Subject: platform extraction workshop

We want a shared underwriting AI platform based on Northstar + Redwood.
Target architecture should support ~8 FIs without per-customer forks.

Please propose:
- core platform modules
- extension points
- what stays professional services

Workshop Friday. Deck appreciated.

Thanks,
Gina Cole
Product
```
:::

:::evidence{type=slack label="Nadia Ferrante"}
```text
Nadia:  what would have to be true for an eight customer abstraction to be cheap
Nadia:  if you cannot name the eight, do not design their interfaces yet
```
:::

## Your task

:::task{time="150 min"}
1. Produce a four-column inventory of every major capability in the lab AI path:
   platform / adapter / config / customer-specific.
2. Extract or confirm thin interfaces for `BankDataAdapter` and `DecisionProcess` that
   both customers bind without customer-name branches in domain services.
3. Deliberately reject one abstraction Gina wants (document it). Explain the cost of
   building it now.
4. Write `customers/_platform/BOUNDARY.md` describing what Halyard sells as product vs
   services.
5. Add a test that fails if underwriting domain code references the string literals
   `NORTHSTAR` or `REDWOOD`.
:::

## Stop and think

:::stopandthink
Before you invent a plugin SDK:

1. Which shared function has been wrong in the same way for both customers?
2. Which difference is data (config) rather than behavior (adapter)?
3. If Meridian breaks your interface next quarter, who pays the rewrite?
4. What is the honest professional services boundary?

Two minutes.
:::

## One line to remember

:::judgment
**Productization is the art of sharing meaning, not the art of sharing nouns.**

Two customers teach you which behaviors are stable. They also tempt you to design a
platform for a sales narrative. Put stable meaning in platform code, variance in
adapters, values in config, and leave some weirdness customer-specific on purpose. The
expensive wrong turn is a workflow engine or plugin SDK that forces fake commonality.
The third customer will not fit your fantasy either, and then you will rewrite the
abstraction instead of the adapter. An FDE who can say "not yet" to their own product
org is doing the job.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You built AI returns sorting for an online retailer (async agents in a web tool). A
second customer is a chain of outlet stores where returns are decided at the register
in under 90 seconds. Leadership wants a "returns OS platform for retail." An architect
proposes a plugin SDK with twenty hooks. You have two implementations.

**Your task**

1. Fill platform / adapter / config / forever-specific for five capabilities.
2. Name one abstraction you refuse.
3. What do you tell sales when they say customer three is "just config"?

---

**Notes, after you have written yours**

Platform candidates: receipt line classification, refund eligibility rules engine with
evals, reason codes. Adapters: web tool vs register UI, e-commerce order API vs POS.
Config: refund windows, category blocks. Forever-specific: outlet printed slip layout,
retailer's gift-card folklore. Refuse the twenty-hook SDK. Tell sales customer three
needs discovery; config-only is a claim you earn after seeing their workflow, not a
promise from a deck.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
