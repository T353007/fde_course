---
id: M39
slug: redwood-bank
title: Redwood Bank
subtitle: >-
  The second customer wants what Northstar has. Almost none of their workflow
  matches. You will feel pressure to write the customer name into an
  if-statement.
phase: 9
order: 39
duration: 300
difficulty: 5
lab: true
status: complete
objectives:
  - Map a second customer's workflow without forcing Northstar's shape onto it
  - 'Spot assumptions in your design that were accidents, not principles'
  - Live with a customer-name branch long enough to feel the failure mode
  - Recover toward seams that do not hardcode NORTHSTAR vs REDWOOD
concepts:
  - second customer
  - workflow mismatch
  - accidental architecture
  - customer branches
competencies:
  - discovery
  - coding
  - productization
prereqs:
  - M38
condensed: true
durationCondensed: 120
---
## Where you are

Northstar is stable enough that Halyard sold a second deal. Redwood Bank does equipment financing through branch officers. They saw a demo. They want "the Northstar AI." Jordan scheduled kickoff before you finished reading their architecture packet.

## The request

:::evidence{type=email label="Jordan Hale, Monday 8:02 AM"}
```text
Subject: Redwood kickoff materials

They loved the demo. Equipment loans, branch-led. Compliance is tighter because
they take deposits. Their CIO asked if we can be live in nine weeks.

I may have said our Northstar playbook transfers.

Packet attached. Kickoff at 11.

Jordan
```
:::

:::evidence{type=email label="Redwood CIO packet, excerpt"}
```text
Origination: branch officer submits packet in BranchOS (vendor, 2009)
Credit decision: two-person committee, Tue/Thu 90 minute sessions
Core banking: nightly SFTP batch, no Kafka
Documents: scanned PDFs couriered from branches, not applicant self-upload
Banking data: core extract, not Ledgerlink-style live aggregation
Applicants: commercial equipment buyers, often existing deposit customers
```
:::

## Your task

:::task{time="180 min"}
1. Write a one page Redwood vs Northstar assumption table. Mark each Northstar
   dependency as reuse, adapt, or replace.
2. Ingest a sample Redwood nightly batch from the lab fixtures and produce a packet
   summary the committee could read Monday night.
3. Implement the smallest path that scores revenue on core-extract transactions without
   calling Ledgerlink.
4. You will be asked for a quick demo Friday. You may temporarily introduce a
   customer-name branch to ship that demo. Then complete the "live with it" section.
5. After living with the branch, refactor the seam so behavior is selected by capability
   flags / adapter binding, not `NORTHSTAR` vs `REDWOOD` string compares in business
   logic.
:::

## Stop and think

:::stopandthink
Before the Friday demo panic:

1. Which Northstar component is actually product, and which is costume?
2. If you write `if (customer.equals("NORTHSTAR"))`, what breaks when Meridian arrives?
3. Where must the AI output land to change a Tuesday vote?
4. What will you refuse to promise in nine weeks?

Write it.
:::

## One line to remember

:::judgment
**The second customer is the test that reveals which of your decisions were principles
and which were souvenirs from the first engagement.**

Pressure to write `if (customer.equals("NORTHSTAR"))` is real, social, and sometimes
rational for a 48 hour demo. The cost shows up when the third condition arrives and
every shared fix forks. An FDE's job is to feel that pain early, on purpose if needed,
then move the variance into adapters and config. Also: do not transplant UI. Transplant
capabilities. Redwood's committee does not want Northstar's portal. They want a better
Monday packet. Believe the workflow you are standing in.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You built AI prior-auth helpers for a telehealth clinic (async nurse review). A hospital
system buys the same product. Their prior auth is decided in a 7am specialty huddle with
paper printouts. Sales demoed your nurse chat UI. An engineer proposes
`if (customer.equals("CLINIC")) ... else ...`.

**Your task**

1. Name three assumptions that just died.
2. What delivery surface fits the hospital?
3. Why is the customer if-statement going to hurt by customer three?
4. Write eight sentences of discovery questions for the huddle lead.

---

**Notes, after you have written yours**

Assumptions that died: async review, chat UI, nurse-as-single-decider. Delivery surface:
a printed or PDF huddle packet before 7am. Customer if-statements hurt because every
cross-cutting change grows a matrix and Meridian-equivalents never fit the binary.
Discovery questions should cover packet deadline, who marks approve, where exceptions
go, what system of record must be updated, and what cannot leave the hospital network.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
