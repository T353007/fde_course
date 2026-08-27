---
id: M07
slug: cutting-the-first-slice
title: Cutting the First Slice
subtitle: Small enough to finish in six weeks, real enough that someone's job changes.
phase: 1
order: 7
duration: 210
difficulty: 3
lab: false
status: complete
objectives:
  - Scope a vertical slice that hits a measured bottleneck
  - Write success criteria that belong in a contract
  - Answer the on-call question before promising a build
  - Reject a slice that demos well and moves the wrong clock
concepts: [vertical slice, success criteria, scoping, adoption, SOW]
competencies: [discovery, adoption, customer-communication]
prereqs: [M06]
---

## Where you are

Monday, March 24. Dale told the board a speed story aimed at waits and rework. You
have six weeks of build credibility to earn, and SOW section 3.3 is still blank.

Section 3.3 says success criteria for the first production use case will be mutually
agreed in writing at the end of discovery. That sentence is now due.

## The request

:::evidence{type=email label="Marcus Webb, Monday 8:11 AM"}
```text
Subject: Slice options (quick)

For the working session at 11. Three options I can sell internally:

A) AI drafts the credit memo from the file
B) AI extracts revenue from bank statements and flags what should not
   count, underwriter reviews before anything hits the decision
C) Chatbot for applicants on "where is my application"

I like A. Visible. Dale can screenshot it. Underwriters hate memo
writing.

See you at 11.
M
```
:::

:::evidence{type=slack label="DM from Nadia Ferrante, 8:19 AM"}
```text
Nadia:  vertical slice means one path through the real system
Nadia:  not a feature that looks like progress in a demo

Nadia:  ask what job changes on day one. if nobody's job changes
        you scoped a slideshow
```
:::

## The conversation

:::dialogue{title="Slice working session, Monday 11:00 AM"}
**Marcus:** Option A. Memo drafting. We have wanted that for two years.

**You:** Walk me through what happens to the 5.1 days if A ships.

**Marcus:** Underwriters go faster, so the queue drains.

**Renee:** I do not wait on the memo. I wait on the statements and on clean revenue
numbers. The memo is forty minutes after the hard part is done.

**Marcus:** Can't the AI just do the hard part and the memo?

**Janet:** Who is on call for that.

**You:** For which part.

**Janet:** For whichever thing you put in production. Who gets the page at 2 AM when
it writes a wrong number into a file an underwriter trusts.

**You:** For the first slice I want a human in the loop on every file, and your team
owns the service boundary. Halyard does not take the pager.

**Janet:** Say that again in the SOW.

**Hank:** What does that do to my queue?

**You:** If we cut rework, your queue gets fewer return visits. If we only draft
memos, your queue looks the same and the notes get prettier.

**Renee:** Option B. My spreadsheet. If the system stops counting transfers and loan
proceeds as revenue, I stop keying deposits by hand. That is a real day.

**Marcus:** B is quieter. Board likes visible.

**Priya:** Board likes not missing Q3. Show me the blast radius on B.

**You:** Read documents, extract transactions, classify revenue versus not, show the
underwriter a diff against the current system number. No auto decision. No memo. No
change to `calculateMonthlyRevenue` yet.

**Sam:** ...Ah. So you are going to meet the function before you touch it.

**You:** Yes.

**Janet:** On call.

**You:** Northstar owns on call for anything in your VPC. We write runbooks and sit
jointly for the first two weeks. After that, your rotation. If that is unacceptable we
pick a smaller slice.

**Janet:** B. With that written down. A is a demo.
:::

## What you know about the system

A vertical slice, for this engagement, means:

1. A real input that already exists (bank statement PDFs applicants already upload)
2. A real transformation (extract transactions, classify what counts as operating
   revenue)
3. A real user who changes a step in their job (Renee and the other underwriters who
   use the spreadsheet)
4. A real success check you can count in production (rework rate, time to clean
   revenue number, agreement with Renee's rules)

It is not a chatbot. It is not a dashboard for Dale. It is not a memo writer that sits
downstream of the still-broken revenue number.

The measured bottleneck is document wait and rework. A large share of rework starts
when the system's revenue number is wrong and an underwriter sends the file back, or
when statements have to be re-requested because intake failed. Slice B attacks the
classification error that makes Renee distrust the portal. That is upstream of the
memo. That is why B moves a clock A cannot touch.

## Evidence

:::evidence{type=email label="SOW section 3.3, current text"}
```text
3.3  Success criteria for 3.2 to be mutually agreed in writing at the
     conclusion of the discovery phase.
```
:::

:::evidence{type=slack label="Carla Mendes, after you pinged her"}
```text
You:    if underwriters stopped sending files back over revenue
        questions, what happens to your resubmit pile

Carla:  it gets quieter. a lot of "already sent" is really "please
        send again, the number looks wrong so we're treating the
        file as incomplete"

Carla:  I don't have a clean tag for that. but it's in there
```
:::

## What you do not know

- Exactly which of Renee's eleven spreadsheet rules are code versus model work
- How bad OptiScan is on faxed statements (you will learn by burning a week)
- Whether Kevin's equipment-loan tab disagrees with Renee on purpose
- What Hank will accept as a queue metric that is not "logins"
- Whether Dale will try to add the memo back after the first internal demo

:::task{time="100 min"}
Fill SOW 3.3. Bring a draft to Janet and Hank before you send it to Dale.

Required contents:

1. **Slice name and one sentence description.** Bank statement revenue extraction and
   classification for underwriter review, aimed at rework.
2. **In scope / out of scope.** Out of scope must explicitly name credit memo drafting,
   auto approve or decline, and any change to `calculateMonthlyRevenue` in this slice.
3. **Users.** Which roles' jobs change on day one.
4. **Success criteria.** Three to five criteria, each measurable within six weeks.
   At least one must be about rework or underwriter time on revenue checks. At least
   one must be about human review (nothing silent).
5. **Operations.** Who is on call. What "jointly" means for the first two weeks.
6. **Non-goals.** One short list. Include Marcus's Option A and Option C by name so
   they cannot return as "also while we are in there."

Save as `customers/northstar/sow-3-3-draft.md`.
:::

:::stopandthink
Before you read how the slice got chosen:

1. Why is a credit memo demo dangerous even if underwriters say they hate memos?
2. What makes Option B vertical instead of a model experiment?
3. Janet asked who is on call. What answer would end the meeting badly?
4. If success is "Dale likes the screenshot," what fails in week six?

Seven minutes.
:::

## Working through it

### The wrong turn: shipping the memo first

Marcus is not foolish for wanting Option A. Memos are painful. They are visible. A
model can draft a bad one in seconds and a polished one in a minute. In a board deck,
A looks like AI underwriting.

Here is the failure mode. The memo is downstream of the revenue number. The revenue
number still counts transfers and Fastcapital loan proceeds as operating revenue.
Renee will read your beautiful memo, open her spreadsheet, and ignore you. Adoption
dies. You spent six weeks on a feature that never touched the 5.1 or the 2.8.

The tell is Nadia's test. Whose job changes on day one? With A, the underwriter still
keys the spreadsheet, still waits on docs, and now also edits a generated memo. You
added work. With B, six of eleven underwriters can stop re-keying deposits for the
cases the classifier gets right, and the misses show up as a review queue instead of a
silent wrong number.

### Why B targets rework

Rework is not only "applicant forgot a file." It is also "underwriter does not trust
the file." Wrong revenue creates `PENDING_INFO`. Wrong revenue creates Carla tickets
that look like resubmits. Slice B does not fix Bill's bucket mismatch by itself. It
does remove one reason humans treat a complete file as incomplete.

You will still need intake work later. This slice is the wedge that puts AI on the
path where Renee already invented the rules.

### Draft language that survives Janet

:::evidence{type=email label="SOW 3.3 draft, excerpt"}
```text
3.3 Success criteria (First Production Use Case)

Use case: Bank statement revenue extraction and classification for
underwriter review.

In scope:
  - Extract transactions from applicant-uploaded bank statement PDFs
  - Classify transactions as operating revenue or excluded
  - Present results to the underwriter for accept / edit / reject
    before any downstream use
  - Compare model output to the current system revenue number as a
    diff, without replacing that number in this slice

Out of scope for this slice:
  - Credit memo drafting (Marcus option A)
  - Applicant status chatbot (Marcus option C)
  - Automatic approve, decline, or counteroffer
  - Changes to calculateMonthlyRevenue or its callers

Users whose job changes on day one:
  - Underwriters currently using revenue_check_v7_FINAL.xlsx (and
    local variants) for deposit review

Success criteria (six week window after production start):
  1. For NSC_DIRECT term loans in the pilot queue, median underwriter
     time spent on revenue reconciliation drops by 50% versus the
     pre-slice baseline measured with Renee's cohort.
  2. Share of pilot applications entering PENDING_INFO with a revenue
     or bank-statement reason code drops by 25% versus the prior
     eight weeks.
  3. 100% of model outputs in the pilot require underwriter accept
     or edit. Zero silent writes to decisioning.
  4. Agreement rate against Renee's labeled set on the easy slice is
     published weekly. No launch if the week-one easy-slice agreement
     is below the threshold set with Renee and Doug before go-live.

Operations:
  - Northstar engineering owns on-call for services in the Northstar
    VPC.
  - Halyard provides joint on-call shadowing for fourteen days after
    production start, then support via ticket during business hours
    unless otherwise agreed in writing.
```
:::

Hank will argue about the twenty five percent. Good. A number he will fight for is
better than "improve rework" which nobody can fail.

### Six weeks, not ten

The SOW sold ten weeks to a production use case. Discovery ate three. You have about
six weeks of build if you are honest. That constraint is a feature. It forces B to stay
narrow. If your draft needs a policy RAG system, a memo engine, and a chatbot to look
complete, you have not cut a slice. You have cut a roadmap and called it a slice.

:::judgment
**A first slice is a promise about whose Tuesday changes, not a promise about what the
model can generate.**

Pick the thinnest path that touches a measured wait, lands in a real user's hands, and
can fail in public without breaking decisioning. Write the on-call sentence before the
architecture diagram. Put the demos you rejected in the out-of-scope list by name.
Then stop talking about AI underwriting until the spreadsheet rules are in a document
with examples.

Mission 08 starts in the codebase. Mission 11 sits down with Renee and treats her
file as the spec it already is. The slice you just chose is why both of those missions
exist.
:::

:::commslab
#### To Janet

> Northstar owns the pager. We shadow for fourteen days. If that is not enough
> comfort, we cut scope again before we cut that sentence.

#### To Hank

> Success criterion 2 is yours to pressure test. If 25 percent is wrong, give me the
> number you would bet your queue on.

#### To Marcus

> A and C are on the out-of-scope list by name so they do not return as "small adds."
> I need you to defend B in rooms I am not in, because it is quieter than a memo demo.

#### To Renee

> The slice is your spreadsheet, put into the system with your name on the rules. Next
> week I want the eleven rules written with examples. Nothing ships that you have not
> walked through.
:::

## Practice

Same scoping problem. Different domain.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A property manager wants AI to "handle resident maintenance." Measured pain:

```text
Median time from resident report to vendor dispatch: 18 hours
Median time coordinator spends writing the vendor brief: 12 minutes
Share of jobs returned by vendors for "wrong access instructions": 34%
```

Product wants a resident chatbot that takes the request. Ops wants auto-dispatch.
The coordinator lead wants structured access instructions extracted from the lease
PDF and shown to a human before dispatch.

**Your task**

1. Which slice is vertical, and whose job changes on day one?
2. Write three success criteria, each measurable in six weeks.
3. Write the on-call sentence.
4. Name the wrong turn that demos best.

---

**Notes, after you have written yours**

The vertical slice is access-instruction extraction with human review before
dispatch. Coordinators change a step they already do badly under time pressure.
Chatbot and auto-dispatch demo well and leave the 34 percent return rate untouched.

Success criteria ideas: return rate down, coordinator time on access notes down, 100
percent human confirm on extracted access fields.

On call: customer owns production paging for anything that can dispatch a vendor.
Vendor wrong-turn: auto-dispatch, because a confident wrong lockbox code is worse than
a slow correct one.
:::
