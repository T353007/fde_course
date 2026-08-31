---
id: M11
slug: the-spreadsheet-is-the-spec
title: The Spreadsheet Is the Spec
subtitle: >-
  Eleven business rules that exist in no repository, no document, and no
  person's memory except hers.
phase: 2
order: 11
duration: 240
difficulty: 3
lab: false
status: complete
objectives:
  - >-
    Extract undocumented business rules from a working underwriter without
    rewriting them into jargon
  - Separate rules that belong in code from rules that need a model judgment
  - >-
    Leave the session with a written rule sheet Renee will sign, not a summary
    of what she said
  - Resist the urge to "clean up" rules that look messy but move money
concepts:
  - undocumented rules
  - domain expertise
  - hybrid systems
  - source of truth
competencies:
  - discovery
  - customer-communication
  - fintech-judgment
prereqs:
  - M10
condensed: true
durationCondensed: 96
---
## Where you are

You have walked the architecture. You found `calculateMonthlyRevenue()`. You know the applicant identity mess. None of that tells you what "revenue" means on Tuesday when Renee has a statement open and forty minutes left on the clock.

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

## Your task

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

## Stop and think

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

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
