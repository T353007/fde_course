---
id: M09
slug: the-revenue-function
title: The Revenue Function
subtitle: >-
  One method. Three callers. Two of them want a different answer and nobody has
  ever said so out loud.
phase: 2
order: 9
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Trace every caller of a shared function across service boundaries
  - Estimate blast radius with a written method instead of a gut feeling
  - Recognize when a bug has no single correct fix because the callers disagree
  - >-
    Choose a first move that is reversible and does not require anyone to be
    wrong
concepts:
  - hidden dependencies
  - blast radius
  - shared definitions
  - feature flags
  - legacy code
competencies:
  - architecture
  - debugging
  - customer-communication
  - fintech-judgment
prereqs:
  - M08
condensed: true
durationCondensed: 96
---
## Where you are

Your first slice needs a revenue number. That was the point of scoping it that way in Mission 07: extract revenue from bank statements, compare it to what the system produces today, and show Renee a difference she can check in ninety seconds.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:31 AM"}
```text
Marcus:  ok so for the slice, we're comparing our extracted revenue
         against the system's current number right?

You:     right

Marcus:  where does the current number come from

You:     finding out today

Marcus:  cool. if ours is better can we just swap it in? feels like a
         one line change

Sam:     it's one line

Marcus:  see

Sam:     i didn't say it was a small change
```
:::

## Your task

:::task{time="120 min"}
Produce two artifacts.

**1. A blast radius table.** One row per caller. Columns:

| Caller | What it wants | What it gets today | What changes if fixed | Who sees the change | Downstream effect | Reversible? | Detectable? |

Fill in all five callers you found, including the two that only appear in access logs.
If you cannot fill a cell, write "unknown" rather than guessing. An honest unknown is
a finding.

**2. A one page recommendation.** It must not propose changing
`calculateMonthlyRevenue()` in this engagement. Your job is to say what the first move
is, why it is reversible, and what has to be true before anyone touches the shared
function.

Save both as `customers/northstar/revenue-function-blast-radius.md`.
:::

## Stop and think

:::stopandthink
Do this before you read on. It is the most useful five minutes in Phase 2.

1. Your instinct is to fix the function. Write down, specifically, what breaks.
2. The portal number is correct for the portal and wrong for underwriting. Who decides
   which one is "the" definition of revenue at Northstar? Name the person.
3. If you shipped the fix today and it was wrong, how would you find out, and how long
   would that take?
4. Marcus said "one line change." What is the shortest true sentence that corrects him
   without making him look bad in the channel?

Write all four down.
:::

## One line to remember

:::judgment
**When a shared value has three consumers and two of them disagree about what it
means, you do not have a bug. You have an undocumented product decision, and code
cannot resolve it.**

The tell is a function name that describes a quantity rather than a computation.
`calculateMonthlyRevenue` names a business concept. `sumPositiveTransactionsDividedByMonths`
names an operation. The first kind of name invites every caller to bring its own
definition, every caller does, and none of them ever meet.

Once you see it, the reflex to suppress is the fix reflex. The change is small, you can
see it clearly, and being the person who fixed the seven year old bug feels good. It is
also how consultants get thrown out of buildings. Nobody is going to thank you for
changing this number on a Wednesday, and if a customer facing figure moves without
warning, Carla's team pays for it and you will not be there.

The move that works is additive and reversible. Add the correctly named function. Leave
the old one running. Make the disagreement visible so the people with authority to
settle it can see it. Migrate one caller at a time with measurement in place. This is
slower and it is the only version that survives you leaving, which is the actual
requirement.

And read the flags. `USE_NEW_REVENUE_CALC_V2_TEMP` looks like technical debt. It is a
research report. Someone smart already attempted your exact change, got most of the
way, and stopped for a reason. Finding out why they stopped is worth more than a week
of your own analysis, because it tells you what is genuinely hard here. In this case
the answer was an open vocabulary of lender names, which is the shape of the AI problem
you were hired to solve. The person who gave up in 2021 wrote your Phase 4 scope.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A payroll company, 220 employees, running payroll for about 9,000 small businesses. You
are two weeks in.

You find this in the core service:

```java
/**
 * Gross pay for the period.
 * TODO(2020): does this include the employer 401k match? Ask Denise.
 */
public Money computeGrossPay(Employee e, PayPeriod p) { ... }
```

Callers you can find:

- `TaxWithholdingService`, in the same service. Wants taxable wages.
- `PaystubRenderer`, in the same service. Wants the number the employee sees at the top
  of their paystub.
- `GET /internal/v1/gross-pay`, called 14,000 times a day by something.
- A nightly export to a 401k provider, written in Ruby, in a different repo.

Denise retired in 2022.

**Your task**

1. Name the number that changes for each caller if the definition is corrected, and
   who physically sees it.
2. Rank the four callers by reversibility. Be specific about what "put it back" means
   for each.
3. One of these callers has a consequence the other three do not. Which one, and why
   does it change your entire plan?
4. Write the first move, in three sentences, with no code in it.

---

**Notes, after you have written yours**

The caller that changes everything is the nightly 401k export. The other three produce
a number on a screen. That one produces a contribution amount sent to a regulated
retirement plan provider, and once a contribution is filed, unwinding it is not a code
change. It is a correction filing with a compliance deadline attached. Reversibility
for the first three is measured in minutes. For that one it is measured in lawyers.

The rule this teaches: rank callers by whether the output leaves your building. A
number on an internal screen, a number on a customer's screen, and a number filed with
a third party are three different risk levels, and a blast radius table that does not
separate them is not doing its job.

The second thing to catch is `TaxWithholdingService` versus `PaystubRenderer`. Taxable
wages and displayed gross pay are genuinely different numbers under US payroll rules,
and both are correct for their own purpose. Same shape as the Northstar portal. Two
legitimate definitions, one function name, and the disagreement has never been said out
loud because the name hid it.

Your first move is the same as Mission 09. Add a second, honestly named function, leave
the existing one alone, and migrate the internal callers first while the external ones
stay put. Then find out what makes 14,000 calls a day to that endpoint, because you
cannot finish the estimate until you know.

And go look for whatever Denise left behind. A retired payroll specialist who was the
named authority on a definition in 2020 almost certainly had a spreadsheet.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
