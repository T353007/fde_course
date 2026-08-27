---
id: M39
slug: redwood-bank
title: Redwood Bank
subtitle: "The second customer wants what Northstar has. Almost none of their workflow matches. You will feel pressure to write the customer name into an if-statement."
phase: 9
order: 39
duration: 300
difficulty: 5
lab: true
status: complete
objectives:
  - Map a second customer's workflow without forcing Northstar's shape onto it
  - Spot assumptions in your design that were accidents, not principles
  - Live with a customer-name branch long enough to feel the failure mode
  - Recover toward seams that do not hardcode NORTHSTAR vs REDWOOD
concepts: [second customer, workflow mismatch, accidental architecture, customer branches]
competencies: [discovery, coding, productization]
prereqs: [M38]
---

## Where you are

Northstar is stable enough that Halyard sold a second deal. Redwood Bank does equipment
financing through branch officers. They saw a demo. They want "the Northstar AI." Jordan
scheduled kickoff before you finished reading their architecture packet.

You still have the Northstar lab. Redwood's differences are modeled as config, fixtures,
and a parallel workflow path you will extend in this mission.

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

## The conversation

:::dialogue{title="Kickoff, Redwood HQ board room, Monday 11:00 AM"}
**CIO:** We want what Northstar has. The revenue read, the policy assist, the reviewer
help.

**You:** Northstar's reviewers work in a portal all day. Your decisions happen in a
committee twice a week. Walk me through Tuesday.

**Committee chair:** Officers drop packets by Monday 4. We read overnight. Tuesday we
vote. If something is missing we defer two days.

**You:** Where would an AI suggestion need to show up to matter?

**Chair:** In the packet before Monday night. Not in a chat panel on Wednesday.

**Jordan:** But the engine is the same, right?

**You:** Parts of it. The workflow is not.
:::

After kickoff, their compliance lead walks you to the elevators.

:::dialogue{title="Elevator bank"}
**Compliance:** We take deposits. Our exam team will ask where bank data goes. If your
answer is "same as the fintech lender demo," we are done talking.

**You:** Northstar's hosted hard path is not your default. We need your VPC plan in
writing before any production text leaves.

**Compliance:** Good. Also our officers will not live in a new portal. Do not sell that
to the CIO behind our back.

**You:** Understood. Packet first.
:::

## What you know about the system

Northstar assumptions baked into your code and brain:

| Northstar assumption | Redwood reality |
|---|---|
| Online applicant portal | Branch officer packet |
| Kafka events | Nightly SFTP |
| Live bank aggregation | Core extract files |
| Single underwriter decision | Two person committee |
| Reviewer portal all day | Burst review Mon night / Tue |
| Tenant partners Bayline/Cascade | Deposit bank, different regs |

If you "just deploy" the portal copilot, you will build a feature for a room that meets
90 minutes twice a week and ignores chat UIs.

## Evidence

:::evidence{type=schema label="Northstar decision path (simplified)"}
```text
application.submitted (Kafka)
  → underwriting-service
  → ai-service extract/classify
  → reviewer-portal suggestion
  → underwriter click
  → underwriting.decisioned
```
:::

:::evidence{type=log label="First naive Redwood spike attempt"}
```text
ERROR bridge.RedwoodIngest - no Kafka topic application.submitted
ERROR portal - user cohort empty: no reviewers online weekday mornings
WARN  ledgerlink - not configured; revenue path returned 0.00
```
:::

:::evidence{type=slack label="DM from Nadia, Monday 5:10 PM"}
```text
Nadia:  what would have to be true for a Northstar if-statement to be fine
Nadia:  write the answer down before you type customer.equals
```
:::

## What you do not know

- Whether Redwood will allow any document text to leave their VPC at all
- How committee votes are recorded today (email? shared drive? core notes?)
- Whether their "revenue" definition matches Renee's operating revenue rules
- Who owns BranchOS vendor tickets when the SFTP file is late

You also do not know whether Redwood's "equipment financing" uses the same operating
revenue definition Renee fought for. Ask early. Do not discover it in a committee
argument on a Tuesday.

:::dialogue{title="Phone with Renee, Tuesday"}
**You:** If a core extract includes a lender credit labeled oddly, what do you want
Redwood's calculator to do?

**Renee:** Same as us. Loan proceeds are not operating revenue. We don't use that
number. Neither should a bank just because their file layout is different.

**You:** Good. That stays platform.
:::

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

:::stopandthink
Before the Friday demo panic:

1. Which Northstar component is actually product, and which is costume?
2. If you write `if (customer.equals("NORTHSTAR"))`, what breaks when Meridian arrives?
3. Where must the AI output land to change a Tuesday vote?
4. What will you refuse to promise in nine weeks?

Write it.
:::

## Working through it

### The wrong turn, on purpose

Friday arrives. Jordan wants a screen. The CIO will be in the room. You do this:

```java
if (customer.equals("NORTHSTAR")) {
    return ledgerlinkRevenue(applicationId);
} else if (customer.equals("REDWOOD")) {
    return coreExtractRevenue(applicationId);
} else {
    throw new IllegalStateException("unknown customer");
}
```

It works. The demo lands. People nod. You tell yourself you will clean it up after the
pilot.

### Live with it

Two weeks later in the lab timeline, these patches appear around the branch:

```java
if (customer.equals("NORTHSTAR") || customer.equals("REDWOOD")) {
    // both need audit reason codes now
}

if (customer.equals("REDWOOD") && !isCommitteeDay()) {
    // suppress portal nag notifications
}

if (customer.equals("NORTHSTAR")) {
    kafka.publish(...);
} else if (customer.equals("REDWOOD")) {
    sftp.drop(...); // except board packets still need email PDF
}
```

Tomás adds a third condition for a Redwood sandbox tenant named `REDWOOD_UAT`. Sam
stares at the file.

:::dialogue{title="Sam on a video call"}
**Sam:** You know Meridian is in pipeline.

**You:** Yes.

**Sam:** Where does Meridian go in this if.

**You:** ...

**Sam:** ...Ah. So you found that.
:::

The pain is specific. Every new behavior needs a customer name. Shared fixes fork.
Tests multiply by customer. On-call needs a mental matrix. You shipped a classification
of the world that cannot survive a third example.

:::evidence{type=ticket label="Internal, week 2 after the demo branch"}
```text
Title: REDWOOD_UAT needs same stale-bank hold as prod Redwood but not Northstar portal toast
Assignee: Tomás
Comments:
  Tomás: added another else-if. sorry.
  Sam: stop. extract adapter.
  You: agreeing. demo debt is now prod risk.
```
:::

:::evidence{type=slack label="Jordan during the cleanup"}
```text
Jordan:  CIO loved the Friday demo. can we keep the branch until GA
You:   we can keep the behavior. we cannot keep the if-statement
Jordan:  I may have told them the code was already multi-tenant clean
You:   then help me by not promising Meridian is a config flip
```
:::

### Tracking it down to a seam

Replace customer names with capabilities:

```text
BankDataAdapter: LedgerlinkAdapter | CoreExtractAdapter
DecisionProcess: SingleReviewerProcess | CommitteeBatchProcess
NotificationChannel: PortalToast | PacketPdf | None
EventTransport: KafkaTransport | NightlyBatchTransport
```

Binding happens in config:

```yaml
customer: redwood
bank_data: core_extract
decision_process: committee_batch
notifications: packet_pdf
events: nightly_batch
```

Business logic asks `bankDataAdapter.refresh(applicationId)`, not "are we Northstar."

You still need customer-specific code. Put it in adapters and config, not in the revenue
function's arteries.

### A day in the Redwood lab path

```bash
# load Redwood batch fixtures
make seed PROFILE=redwood-batch
# produce Monday packet for committee
curl -X POST localhost:8000/v1/memo/draft \
  -H 'X-Tenant-Id: REDWOOD' \
  -H 'X-Capability-Profile: committee_batch' \
  -d @fixtures/redwood/packet_441.json
```

The memo endpoint does not care that Kafka is absent. The batch adapter already wrote
normalized transactions. That is the point of the seam.

:::evidence{type=http label="Packet summary excerpt for committee"}
```text
Equipment loan request $180,000 - Branch 14 packet
Operating revenue (3 mo avg): $61,400
Excluded: internal transfer $12,000; lender credit $40,000 (competitor note)
Open questions: OCR confidence low on page 3 of statements
Policy: equipment LTV ceiling citation, effective 2025-01-01
```
:::

### Then this happens

The committee chair rejects a portal login plan.

:::evidence{type=email label="Committee chair, week 3"}
```text
We will not ask six officers to live in a new UI for a twice-weekly meeting.
If the AI cannot put a two page packet summary in the folder we already use
by Monday 6pm, it does not exist for us.
```
:::

That email is a gift. Delivery surface is the packet. Build for that. Do not argue them
into your React app because it is what you have.

### The better demo, after the pain

Show Monday packet PDFs with:

- operating revenue estimate and exclusions
- policy citations with effective dates
- open questions for the committee
- explicit "model low confidence" on hard slices

No customer string in the calculator. Redwood binds `CoreExtractAdapter`. Northstar
keeps Ledgerlink.

:::dialogue{title="Friday demo, take two, week 4"}
**CIO:** Where do my officers click?

**You:** They do not. The summary lands in the packet folder by Monday 6. Committee
reads what they already read, with better numbers.

**Chair:** That I will use.

**Jordan:** And the portal?

**You:** Optional later. Not the wedge.
:::

Living with the if-statement taught the lesson faster than a lecture. Deleting it is
the productization homework Mission 40 finishes.

Before you leave Redwood for the week, write the assumption failures in the engagement
brief so Capstone-you does not repeat them:

```text
Failed assumptions from Northstar transfer:
1. Reviewers live in a portal all day
2. Events are streaming
3. Bank data is an interactive aggregator
4. A single human clicks decide
5. "Connected" UX metaphors mean anything to a branch packet world
```

One more cost of the early if-statement: Tomás spent a day duplicating the Ledgerlink
semantic empty-accounts hold into the Redwood branch by copy paste, then you deleted
both copies when the adapter landed. That is two days of churn for a demo shortcut.
Worth naming in the retro so the next engagement pays once. Write the churn hours in
the engagement brief next to the demo date so nobody calls the shortcut free.

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

:::commslab
#### To Jordan

> The engine pieces transfer. The workflow does not. Please stop telling them the
> playbook is copy-paste. I need cover to redefine the demo as a committee packet, not
> a portal clone.

#### To Priya at Northstar

> We are extracting adapters so Redwood work does not fork your code paths with
> customer-name branches. Your runtime stays bound to current config.

#### To Redwood CIO

> Nine weeks to "Northstar in your bank" is not honest. Nine weeks to a Monday packet
> assist on equipment deals with your batch files is a scoped yes if compliance agrees
> on data boundaries.
:::

## Practice

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
