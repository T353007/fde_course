---
id: M07
slug: cutting-the-first-slice
title: Cutting the First Slice
subtitle: 'Small enough to finish in six weeks, real enough that someone''s job changes.'
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
concepts:
  - vertical slice
  - success criteria
  - scoping
  - adoption
  - SOW
competencies:
  - discovery
  - adoption
  - customer-communication
prereqs:
  - M06
condensed: true
durationCondensed: 84
---
## Where you are

Monday, March 24. Dale told the board a speed story aimed at waits and rework. You have six weeks of build credibility to earn, and SOW section 3.3 is still blank.

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

## Your task

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

## Stop and think

:::stopandthink
Before you read how the slice got chosen:

1. Why is a credit memo demo dangerous even if underwriters say they hate memos?
2. What makes Option B vertical instead of a model experiment?
3. Janet asked who is on call. What answer would end the meeting badly?
4. If success is "Dale likes the screenshot," what fails in week six?

Seven minutes.
:::

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
