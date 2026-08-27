---
id: M40
slug: what-belongs-in-the-product
title: What Belongs in the Product
subtitle: "Two customers is the earliest you can responsibly abstract. It is also early enough to abstract the wrong thing for eight imaginary ones."
phase: 9
order: 40
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - Sort capabilities into platform, adapter, config, and customer-specific forever
  - Resist designing for eight customers when you have two
  - Extract a thin platform seam from Northstar and Redwood without a framework fantasy
  - Explain the product boundary to Halyard and to both customers in plain language
concepts: [productization, platform vs adapter, configuration, premature abstraction]
competencies: [architecture, productization]
prereqs: [M39]
---

## Where you are

Redwood's Monday packet path works without `customer.equals` in the revenue guts.
Halyard's product lead wants "the platform." A slide has appeared with eight verticals
on it. You have two real deployments and a rumor named Meridian.

This mission is the extraction discipline. Not the brand launch.

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

## The conversation

:::dialogue{title="Workshop, Friday 10:00 AM"}
**Gina:** If we do this right, Redwood and Northstar both run on one codebase with
config.

**You:** Some of it. Not the committee packet PDF layout. Not Northstar's partner
tenant overlays.

**Gina:** Those can be themes.

**Sam:** *invited from Northstar, looks tired* Themes is how we got three tenant ID
conventions.

**Gina:** Can't we just have a plugin SDK?

**You:** We can. We should not, yet. Two examples give us seams. They do not give us a
stable SDK contract.
:::

Janet, dialed in from Northstar, draws a line.

:::dialogue{title="Still the workshop"}
**Janet:** Who is on call for a plugin SDK?

**Gina:** Platform team, eventually.

**Janet:** Eventually is not an on-call rotation. If you freeze an interface wrong, my
team pays in pages.

**You:** Then we freeze only what both deployments already share in meaning. Adapters
stay thin. No workflow meta-engine this quarter.

**Gina:** That will look small in the board deck.

**You:** Small and true beats large and fictional.
:::

## What you know about the system

You have two working shapes:

**Northstar:** online apps, Kafka, Ledgerlink, single reviewer portal, partner tenants,
policy overlays.

**Redwood:** branch packets, SFTP batch, core extracts, committee cadence, deposit-bank
compliance posture.

Shared useful pieces already proven twice:

- transaction classification with slice evals
- operating revenue rules that exclude transfers and loan proceeds
- policy answer with citations and effective dates
- reason codes that can drive adverse action language
- model routing, budgets, semantic vendor checks
- audit/ACL patterns for AI invocations

## Evidence

:::evidence{type=schema label="Draft platform map on the whiteboard"}
```text
PLATFORM (same meaning both places)
  - extract transactions from text
  - classify transactions
  - compute operating revenue with explicit exclusion rules
  - answer policy questions with citations + dates
  - emit reason codes + letter templates
  - model router + budgets + invocation audit

ADAPTER (swap implementation)
  - bank data source
  - document intake transport
  - event transport
  - decision process hooks
  - notification / packet delivery

CONFIG (data, not code)
  - policy document sets + effective dating
  - product floors and thresholds
  - routing thresholds
  - retention and ACL settings

CUSTOMER-SPECIFIC FOREVER (on purpose)
  - Redwood committee PDF layout and BranchOS filenames
  - Northstar Bayline/Cascade pricing display quirks
  - each FI's core banking field mappings that only they understand
```
:::

:::evidence{type=log label="Over-abstract spike that almost shipped"}
```text
INFO  PluginSDK - loading CustomerPlugin
ERROR PluginSDK - RedwoodPlugin does not implement AsyncReviewerPresence
ERROR PluginSDK - NorthstarPlugin missing CommitteeQuorumHint
WARN  PluginSDK - defaulting both to NoopStrategy
```
:::

The SDK demanded concepts each customer does not have. Both fell through to no-ops.
That is how premature platforms create dead code paths that still need tests.

## What you do not know

- Whether Meridian looks more like Northstar, Redwood, or neither
- How much Halyard will staff professional services for field mappings
- Whether Gina's "eight FIs" are real pipeline or a board narrative
- Which Northstar partner quirks are actually contractual obligations

Gina's deck lists "community banks, credit unions, specialty finance, insurance premium
finance" as year-one targets. That is four more shapes than you have evidence for.
Treat the list as sales aspiration until discovery says otherwise.

:::evidence{type=slack label="Private note to Nadia"}
```text
You:    eight-FI slide is fiction until we have eight workflows
Nadia:  say that in the workshop without saying fiction
You:    "two proven bindings, more when discovered"
Nadia:  good
```
:::

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

:::stopandthink
Before you invent a plugin SDK:

1. Which shared function has been wrong in the same way for both customers?
2. Which difference is data (config) rather than behavior (adapter)?
3. If Meridian breaks your interface next quarter, who pays the rewrite?
4. What is the honest professional services boundary?

Two minutes.
:::

## Working through it

### The wrong turn

Gina wants a `WorkflowEngine` that can express portal review and committee batch as
YAML state machines. You spend a day sketching states: `SUBMITTED`, `PACKET_READY`,
`IN_COMMITTEE`, `IN_REVIEWER_QUEUE`, and twelve more.

Redwood's defer-two-days path does not fit. Northstar's `PENDING_INFO` loops do not
fit cleanly either. You start adding escape hatches. By evening the "platform" is a
worse copy of each customer's existing process tools.

You delete the engine draft. Keep the adapters.

:::evidence{type=email label="Your note to Gina after deleting the engine"}
```text
Gina,

I killed the WorkflowEngine spike. It was optimizing for a slide.

What we can defend with two customers:
- shared credit/policy/eval/cost guts
- adapters for bank data, events, delivery, decision cadence
- config for thresholds and policy sets

What we cannot defend yet:
- a state machine that claims to express every FI process

If Meridian looks like a third shape, we will learn again. That is
cheaper than teaching eight imaginary banks wrong interfaces.

You,
```
:::

### Sorting rules that hold

**Platform** means the meaning is stable and tested the same way. Operating revenue
exclusions are platform. Slice evals are platform. Invocation audit shape is platform.

**Adapter** means the world talks differently. SFTP vs Kafka. Ledgerlink vs core
extract. Portal toast vs Monday PDF.

**Config** means values change without code. Floors, policy sets, routing cut lines,
retention days.

**Customer-specific forever** means the cost of abstracting exceeds the value, even at
customer five. BranchOS filename folklore. A partner brand's PDF disclaimer paragraph.
A committee's cover sheet that must match an internal template from 2014.

If you only have two examples, prefer a boring interface with two implementations over
a generic engine with imaginary hooks.

### Worked example: revenue

| Layer | Choice | Why |
|---|---|---|
| Platform | `OperatingRevenueCalculator` with exclusion rules | Same meaning both places |
| Adapter | `LedgerlinkAdapter` / `CoreExtractAdapter` | Different feeds |
| Config | months window, minimum credits required | Values differ |
| Forever-specific | Redwood core field `GL_CR_MEMO_TYP` mapping table | Only their core knows |

Do not put the GL mapping into platform. Do not put exclusion rules only in Redwood
services code. That is how you fork truth.

:::evidence{type=test label="Guardrail test sketch"}
```java
@Test
void operatingRevenueExcludesLoanProceedsForBothBindings() {
    for (BankDataAdapter adapter : List.of(ledgerlink, coreExtract)) {
        var txns = adapter.load(FIXTURE_WITH_FASTCAPITAL_LOAN);
        assertEquals(new BigDecimal("147400.00"),
            calculator.operatingRevenue(txns, 1));
    }
}
```
:::

### Then this happens

Meridian's name appears in a pipeline Slack. Someone pastes your boundary doc and asks
whether Meridian is "just config."

:::evidence{type=slack label="#halyard-deals"}
```text
Jordan:    meridian wants AI underwriting like northstar
Gina:    great, platform ready
You:     we have seams. we do not know meridian's workflow.
You:     if we tell them it is config-only we will lie them into a fork
Nadia:   discovery first. productization is not telepathy.
```
:::

Protect the boundary by refusing to classify the third customer before you have sat in
their process.

### The better version

Ship this to Gina as the workshop outcome:

```text
Sell now as product
  - classification + revenue engine + policy QA + reason/letter kit
  - routing/budgets/audit
  - adapter interfaces with two reference bindings

Sell as services / customer code
  - new bank adapters
  - packet or portal integration
  - policy corpus onboarding
  - workflow placement UX

Do not build yet
  - universal workflow engine
  - plugin SDK with payment-required interface methods
  - multi-vertical theming system
```

Add the guard test:

```java
@Test
void domainServicesDoNotBranchOnCustomerName() throws Exception {
    // scan underwriting-service main sources; fail on NORTHSTAR|REDWOOD literals
}
```

Exceptions allowed only in config modules and adapter packaging.

:::evidence{type=slack label="Sam after the guard test lands"}
```text
Sam:   failed CI on a helper named NorthstarDateFormats
Sam:   ...Ah. So you found that.
You:   moved to adapter packaging. thanks for not renaming it quietly.
Sam:   I have wanted that test for nine years.
```
:::

Write the boundary in language sales can repeat without lying:

```text
Halyard product: credit and policy AI guts, evals, cost controls, adapter interfaces
Halyard services: bind adapters, place the assist in the customer workflow, onboard policy
Not product yet: universal workflow engine, vertical theme packs, plugin marketplace
```

Phase 9 ends when both customers run on shared guts without customer-name branches in
domain services, and Halyard has a written boundary that sales cannot casually inflate
to eight verticals. Meridian, when it comes, starts with discovery. That is the point
of the word forward in the job title.

Before you close the laptop, skim Gina's deck one more time and remove any slide that
implies Redwood proved a universal FI workflow. Replace it with the four-column
inventory. If a slide cannot survive contact with Sam's on-call question, it does not
ship to the board.

Capstone will tempt you to abstract Meridian on day one. Re-read this mission first.
Two examples earned thin adapters. They did not earn a marketplace. If someone asks
for the eight-customer SDK in the first week of Meridian, send them the boundary doc
and schedule discovery, not a design review. The cheapest platform mistake is the one
you do not merge. Say no early while it is still cheap. Your future self will mean it.

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

:::commslab
#### To Gina

> We can productize classification, revenue, policy QA, reason letters, and the
> observability/cost controls. We should not ship a universal workflow engine from two
> examples. Here is the boundary doc and the list I am explicitly not building.

#### To Northstar Priya

> Shared library extraction will not change your runtime binding. You keep Kafka and
> Ledgerlink adapters. I want Janet's review on the interface freeze.

#### To Redwood CIO

> You are not being shoved into Northstar's portal product. Your packet delivery stays
> yours. Shared pieces are the credit math and policy assist underneath.
:::

## Practice

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
