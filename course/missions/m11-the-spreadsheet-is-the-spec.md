---
id: M11
slug: the-spreadsheet-is-the-spec
title: The Spreadsheet Is the Spec
subtitle: Eleven business rules that exist in no repository, no document, and no person's memory except hers.
phase: 2
order: 11
duration: 240
difficulty: 3
lab: false
status: complete
objectives:
  - Extract undocumented business rules from a working underwriter without rewriting them into jargon
  - Separate rules that belong in code from rules that need a model judgment
  - Leave the session with a written rule sheet Renee will sign, not a summary of what she said
  - Resist the urge to "clean up" rules that look messy but move money
concepts: [undocumented rules, domain expertise, hybrid systems, source of truth]
competencies: [discovery, customer-communication, fintech-judgment]
prereqs: [M10]
---

## Where you are

You have walked the architecture. You found `calculateMonthlyRevenue()`. You know the
applicant identity mess. None of that tells you what "revenue" means on Tuesday when
Renee has a statement open and forty minutes left on the clock.

She keeps a file on her desktop called `revenue_check_v7_FINAL.xlsx`. Six other
underwriters have local copies with different names. The system has never matched her
number. That is why the file exists.

## The request

:::evidence{type=slack label="DM from Renee Blackwell, Monday 8:14 AM"}
```text
Renee:  Hank said you want the spreadsheet walkthrough
Renee:  I have 90 minutes before the 10am queue. Conference B.
Renee:  Bring a notebook. I am not emailing this.
```
:::

She is not being difficult. She has watched consultants take her file, rename the
columns, and ship something that still counts loan proceeds as sales. The notebook is a
filter.

## The conversation

:::dialogue{title="Conference B, Monday 8:40 AM"}
**Renee:** We don't use that number.

**You:** Which number?

**Renee:** The one on the portal. Average monthly revenue. It is wrong on purpose
until someone fixes the calculator, and nobody fixed the calculator.

**You:** So you use the spreadsheet.

**Renee:** I use the spreadsheet. Sit down.
:::

:::dialogue{title="Same room, five minutes later"}
**You:** How many rules are in there?

**Renee:** Eleven that I trust. The rest of the tabs are notes and old fights with
credit policy.

**You:** Can we go through all eleven?

**Renee:** That is why you are here. Start with Coastal Supply. You already know that
file.
:::

She opens the May statement. Stripe. Transfer. Stripe. Fastcapital. Stripe. She does
not wait for you to ask about Fastcapital.

:::dialogue{title="Coastal Supply, line by line"}
**Renee:** Stripe counts. Transfer does not. Stripe counts. Fastcapital does not.
Stripe counts. 147,400.

**You:** The system says 252,400.

**Renee:** The system adds every credit. That is not underwriting. That is a bank
balance hobby.

**You:** Who wrote the eleven rules?

**Renee:** I did. Over about six years. Some of them used to be email threads. Some of
them used to be arguments with Hank. None of them are in Confluence.
:::

## What you know about the system

From Missions 09 and 10 you already know:

| Fact | Source |
|---|---|
| Java calculator sums every positive amount | `RevenueCalculator.java` |
| Jan Kowalski left a TODO in 2019 asking credit policy | same file |
| Portal "cash flow" widget wants total deposits | third caller |
| Underwriting and DSCR want operating revenue | first two callers |
| Renee's number for Coastal Supply | 147,400 |

What you do not have yet is the full rule set that turns a statement into that number.
Without it, every model call you write later is guessing.

## Evidence

She screenshares the Rules tab. She will not give you the file yet. You type.

:::evidence{type=spreadsheet label="revenue_check_v7_FINAL.xlsx, Rules tab as Renee reads it"}
```text
R-01  Only credits can contribute to operating revenue. Debits never add.
R-02  Internal transfers between the owner's own accounts are not operating
      revenue. "TRANSFER FROM SAVINGS", "TRANSFER TO CHECKING", same-name
      wires between accounts she already linked.
R-03  Owner capital contributions and equity injections are not operating
      revenue. Look for "OWNER CONTRIB", "CAPITAL INJECT", personal name wires
      that match the guarantor.
R-04  Loan proceeds, MCA deposits, and line draws are not operating revenue.
      Includes Fastcapital, OnDeck, Kabbage, Square Capital, and any description
      that says LOAN, ADVANCE, or DRAW with a lender name.
R-05  Tax refunds and IRS deposits are not operating revenue.
R-06  Insurance claim payouts are not operating revenue. Flag them. Do not
      silently drop them without a note.
R-07  Card settlement payouts (Stripe, Square, PayPal, Shopify Payout) count
      as operating revenue even when the amount is lumpy.
R-08  Month-end clustering: if a large credit lands in the last three business
      days of a month and a similar debit leaves in the first three business
      days of the next month, treat the credit as non-operating until proven
      otherwise. Window dressing shows up here.
R-09  Related-party deposits from entities that share an address, phone, or
      owner name need manual review. Do not auto-count them as sales.
R-10  Average monthly revenue uses the last three complete calendar months.
      Not a rolling 90 day window. Partial current month is ignored.
R-11  When a description names a competitor lender (Fastcapital especially),
      exclude the dollars under R-04 AND flag the application for existing
      debt review. The flag is separate from the revenue math.
```
:::

:::evidence{type=spreadsheet label="Worked example tab, Coastal Supply May"}
```text
05/04  STRIPE PAYOUT           +48,230   R-07 include
05/06  TRANSFER FROM SAVINGS   +30,000   R-02 exclude
05/11  STRIPE PAYOUT           +51,340   R-07 include
05/18  FASTCAPITAL LOAN        +75,000   R-04 exclude, R-11 flag
05/22  STRIPE PAYOUT           +47,830   R-07 include

Naive credits:     252,400
Operating revenue: 147,400
Flags:             existing debt review (Fastcapital)
```
:::

:::evidence{type=slack label="Hank, after you leave Conference B"}
```text
Hank:   did you get what you needed from Renee
You:    eleven rules. writing them up now.
Hank:   good. What does that do to my queue?
You:    if we encode them wrong, your people keep the spreadsheet forever
Hank:   then do not encode them wrong
```
:::

## What you do not know

- Which of the eleven rules already exist, half broken, somewhere in Java
- Whether Bayline and Cascade underwriters use the same eleven or local variants
- What Renee does when two rules conflict on one line
- Whether Doug will accept "Renee said so" as an audit trail
- Whether Marcus will try to turn all eleven into a single prompt by Thursday

:::task{time="120 min"}
Sit with Renee (or the transcript and spreadsheet excerpts above if you are working
solo) and produce `customers/northstar/revenue-rules-v1.md`.

The file must contain:

1. All eleven rules in her language first, then a one line engineer paraphrase.
2. For each rule, a column: **code**, **model**, or **human**. You choose. She does
   not have to agree yet, but she has to see the column.
3. At least one worked example per rule, with a real-looking description line.
4. A conflict note: what happens if R-08 and R-07 both seem to apply.
5. Her sign-off line at the bottom. Literally a place for her name and date.

Do not invent a twelfth rule to make the list look cleaner. Do not merge R-04 and
R-11. They are different jobs.
:::

:::stopandthink
Before you classify anything as code or model:

1. Which rules fail safely if a model is wrong, and which ones move an approval by five
   figures if the model is wrong?
2. R-08 (month-end clustering) needs a calendar and two months of history. Is that a
   prompt, or is that software?
3. If you put Fastcapital detection only in a prompt, what happens the week the model
   is slightly off on lender names?
4. What is the wrong turn a reasonable engineer takes in this meeting?

Write those four down. Two minutes. Then keep reading.
:::

## Working through it

### The wrong turn

A reasonable engineer opens the spreadsheet, sees eleven rows, and thinks: "Great, we
will put these in the system prompt and the model will follow them."

That path feels fast. Marcus will love it. It also turns Renee's careful rules into
suggestions the model can ignore when the description is weird, which is exactly when
you need the rules most.

Cost of that turn: you ship a demo that looks right on Coastal Supply, then fails on
the next Fastcapital variant spelled `FAST CAPITAL LOAN FUNDING`, and Renee quietly
keeps the spreadsheet. Adoption dies before Phase 8 has a name.

### Code versus model versus human

Walk the list with her. Do not lecture. Ask where she would trust a machine.

| Rule | Bucket | Why |
|---|---|---|
| R-01 | code | Sign of the amount is not a judgment call |
| R-02 | model then code | Model proposes INTERNAL_TRANSFER. Code excludes dollars |
| R-03 | model then code | Same pattern. Owner names are messy |
| R-04 | model then code | Lender names vary. Exclusion must be deterministic once labeled |
| R-05 | model then code | IRS text is mostly stable, still label then exclude |
| R-06 | model then human | Insurance payouts are rare and politically loaded |
| R-07 | model then code | Settlements are the easy volume. Code sums labeled lines |
| R-08 | code | Needs date math across months. Prompts are bad calendars |
| R-09 | human | Related party is a relationship judgment, not a regex |
| R-10 | code | Window definition is policy arithmetic |
| R-11 | code on top of R-04 | Flag is a side effect. Do not bury it in the revenue total |

She pushes on R-08.

:::dialogue{title="Month-end clustering"}
**Renee:** Sometimes the cluster is real sales. A contractor gets paid on the 29th.

**You:** So the rule is a hold, not an auto-exclude?

**Renee:** Hold and look. If there is no matching outflow next month, it can count.

**You:** That is human.

**Renee:** For now. Do not let anyone pretend a prompt can see next month's statement
that is not uploaded yet.
:::

That sentence belongs in the rule sheet. Write it under R-08.

### What already lives in code

You check after the meeting. Almost nothing of the eleven is implemented.

:::evidence{type=log label="Notes after grepping underwriting-service"}
```text
RevenueCalculator: sums credits. No categories. No lender list.
PolicyRuleEngine: revenue floor in dollars, not transaction rules.
No month-end cluster check anywhere.
No Fastcapital string list in Java. One TODO comment from 2019.
```
:::

So the spreadsheet is not a duplicate of the system. The spreadsheet is the system.
The Java is a rough sketch that got stuck waiting for a meeting that never happened.

### Getting her sign-off

Send the markdown the same day. Same day matters. Overnight, people "improve" wording
and she stops recognizing her own rules.

:::evidence{type=email label="Your note to Renee, Monday 4:10 PM"}
```text
Subject: revenue-rules-v1 for your eyes only

Renee,

Attached is what I heard. Your words first, my paraphrase second, then the
code / model / human column we marked in the room.

Two places I want you to fight me if I got them wrong:

1. R-08 hold-and-look, not auto-exclude
2. R-11 flag stays even when the dollars are already excluded under R-04

I did not merge any rules. I did not add a twelfth.

If this matches, reply with your name and today's date on the sign-off
line. If it does not, redline the file. Do not summarize in Slack. The
file is the artifact.

Thank you for the ninety minutes. The portal number is wrong for the
reasons you said.
```
:::

## Then this happens

Marcus reads the channel summary and replies before Renee signs.

:::evidence{type=slack label="#northstar-ai, Monday 5:02 PM"}
```text
Marcus:  love this. can we just put all 11 in the prompt for Thursday's demo?
Marcus:  Can't the AI just do that?

You:     prompt can propose labels for 02-07. arithmetic and R-08 stay in code.
You:     R-09 stays human. R-11 is a flag in code.

Marcus:  feels slower

Sam:     slower than shipping a wrong number into underwriting? pick one

Marcus:  fine. but I want the Fastcapital thing visible in the demo.
```
:::

He is not wrong about wanting Fastcapital visible. He is wrong about the mechanism.
Show the flag in the UI. Do not show a prompt paragraph that says "never count
Fastcapital."

## Tracking it down

Bayline has a local copy. Cascade has two. You ask Hank for thirty minutes with one
Bayline underwriter later in the week. Do not assume NSC_DIRECT rules are universal
just because Renee is the best teacher in the building.

Also ask Doug one question, not ten:

:::dialogue{title="Doug, doorway, 5:40 PM"}
**You:** If we encode Renee's rules and cite the signed markdown in the decision
audit, is that enough for adverse action support?

**Doug:** Can you explain that decision to the applicant in writing?

**You:** The letter would say we excluded non-operating deposits including loan
proceeds. It would not name the internal rule ids.

**Doug:** Then keep the rule ids in the internal audit, keep plain English in the
letter, and do not let the model invent a third story.
:::

## The better version

By Tuesday morning you should have:

- `revenue-rules-v1.md` with eleven rules and Renee's sign-off
- A bucket per rule: code, model, or human
- A public agreement that dollars are never summed by the model
- A named unpaid bill: Bayline and Cascade variants not yet confirmed

That unpaid bill is fine. Pretending you finished multi-tenant policy in one meeting is
how M24 gets worse.

:::judgment
**The real specification is often a spreadsheet on someone's desktop, and treating
that person as a blocker is how projects fail.**

Renee did not refuse to automate. She refused to be the next person blamed when a
system number was wrong. Your job in this mission is not clever extraction. It is
making her rules durable enough that she can put the file in a folder named archive
without risking her queue.

When you meet the next domain expert, ask for the artifact they trust when the official
system lies. Then walk it line by line. Then put code around the parts that must not
drift, models around the parts that need judgment over messy text, and humans on the
parts that create political or legal risk. Write the sign-off the same day.
:::

:::commslab
#### To Renee

> Rules file attached. Your wording first. Please sign or redline today. I will not
> let Marcus put the whole list in a prompt.

#### To Marcus

> Thursday demo can show Fastcapital excluded and flagged. The exclusion is code after
> a label. If we only prompt it, the demo lies the first week a description changes.

#### To Hank

> Encoding these correctly is what lets your team stop re-keying deposits. Encoding
> them as prompt poetry keeps the spreadsheet alive.

#### To Janet

> No service change ships from this mission. Artifact only. When we implement, R-08 and
> R-10 are deterministic and need tests before any model work.
:::

## Practice

Same skill. Different desk.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A mid-market insurer has a senior claims adjuster named Gloria. She keeps
`total_loss_v4_REAL.xlsx` on her desktop. The claims system calculates actual cash
value. Gloria's file adjusts for:

1. Aftermarket parts availability in rural ZIP codes
2. Storage fees after day 14
3. Betterment on tires older than 4 years
4. A "customer goodwill" cap her manager verbally approved in 2021
5. Flood vs water intrusion wording that changes deductible handling

Product wants an "AI claims assistant" by month end. Engineering wants Gloria's file
exported to JSON tonight.

**Your task**

1. Which items are code, model, or human? Mark all five.
2. What is the wrong turn if you only have one hour with Gloria?
3. What do you put in the sign-off artifact before anyone writes a prompt?

---

**Notes, after you have written yours**

1 and 2 are mostly code once the ZIP and day-count inputs exist. 3 is code with a
clear age rule. 4 is human and management policy, not a model toy. 5 is model-assisted
classification of messy notes, then code for deductible math.

The wrong turn is exporting the spreadsheet to JSON without walking examples, then
calling that a spec. You will miss that 4 was never written down and 5 depends on
wording Gloria has memorized.

The sign-off artifact needs her language, worked examples, bucket labels, and an
explicit note that goodwill caps are not model output. Same shape as Renee's sheet.
The insurance nouns change. The job does not.
:::
