---
id: M10
slug: who-owns-the-applicant
title: Who Owns the Applicant
subtitle: >-
  The same bakery appears four times with four IDs, and every one of those rows
  is correct according to somebody.
phase: 2
order: 10
duration: 210
difficulty: 3
lab: true
status: complete
objectives:
  - Tell a duplicate record apart from a distinct entity that looks similar
  - >-
    Trace one real world business across four systems that each assign their own
    ID
  - >-
    Explain why merging identity records is a business decision, not a data
    cleanup
  - Decide who owns a master record when three systems each believe they do
concepts:
  - identity resolution
  - data ownership
  - master data
  - deduplication risk
competencies:
  - architecture
  - discovery
  - fintech-judgment
prereqs:
  - M09
condensed: true
durationCondensed: 84
---
## Where you are

You are building the first slice. It needs a list of applications with their bank transactions, and it needs to know which business each application belongs to.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 9:48 AM"}
```text
You:    quick one. for the pilot i want to pull the last 12 months of
        applications for one business, so renee and i can look at the
        same statements. any suggestions for a good example?

Renee:  cortland street bakery. marisol reyes. she's applied a few
        times and the statements are messy in a normal way.

You:    perfect, thanks

Carla:  oh cortland. good luck 🙃

You:    ...meaning

Carla:  meaning she calls us about once a quarter asking why we sent
        her two different decisions
```
:::

## Your task

:::task{time="90 min"}
Produce an identity findings memo, `customers/northstar/applicant-identity.md`.

Three parts.

**1. The evidence.** The four Cortland rows, what makes each one different, and the
cause of each difference. Then the table-wide numbers, with a sentence on why each one
is a floor rather than a count.

**2. A decision table.** One row per Cortland record, with these columns:

| applicant_id | Same legal entity? | Same relationship? | Recommended action | Why | Who has to approve |

Your action options are exactly four: `merge`, `link`, `leave`, `escalate`. Use
`escalate` only when the decision genuinely belongs to someone else, and name them.

**3. A recommendation on ownership.** Answer one question in writing: which system
holds the master record for a business, and does the answer change depending on where
the business is in its lifecycle? Two paragraphs. Take a position.

Do not propose a dedupe job. If you already wrote one, keep it and read on.
:::

## Stop and think

:::stopandthink
1. Which of the four rows is a duplicate, and which is something else? Write the
   dividing line you are using as one sentence.
2. Applicant 22910 has a funded loan. What specifically goes wrong if you merge it
   into 10428?
3. Row 40155 is on the `BAYLINE` tenant. Is that a duplicate of the Northstar row, or
   is it a different thing? Argue both sides for one minute each.
4. The warehouse joins on email. Name one situation where that produces a wrong answer
   that nobody would ever notice.

Question 3 is the one people get wrong.
:::

## One line to remember

:::judgment
**Identity resolution looks like a data quality problem and is actually a policy
question. The technical part is easy and the technical part is not the part that is
stopping anyone.**

Every engineer who sees four rows for one bakery reaches for the same fix, because the
fix is genuinely straightforward and the data genuinely is messy. What that instinct
misses is that a duplicate is defined by a decision, not by a distance metric. Two rows
are duplicates when someone with authority says these should be treated as one
customer, and different parts of the business will answer that differently for the same
pair. Fraud wants them separate and linked. Reporting wants them collapsed. Servicing
wants them untouched. All three are right for their own purpose.

The specific trap in lending is that some duplicates are load bearing. An owner with
three entities applying separately is a normal business structure and also the standard
shape of decline shopping. Ada does not need the duplicates removed. She needs them
visible, connected, and still separate. A dedupe job would have taken away the only
signal she has, and it would have looked like a data quality win on the way out the
door.

The move that generalizes is to prefer additive over destructive when the decision
maker has not been identified yet. A link table is additive. A merge is destructive and
irreversible, because the deleted row takes its history with it. When you do not know
who owns a decision, take the action that keeps every option open, and spend your time
finding the owner instead. That is usually slower and it is almost always right, and it
is the same reasoning that kept you out of `calculateMonthlyRevenue` in Mission 09.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A property and casualty insurance carrier, about 1,100 employees. You are five days
into an engagement to build automated policy renewal underwriting.

The policyholder table has these five rows, which all appear to be one household:

```text
 party_id |        name         |    dob     |     address         | policy_status
----------+---------------------+------------+---------------------+--------------
   884201 | ROBERT J HALVERSEN  | 1971-04-02 | 14 Ridge Rd, Apt 2  | ACTIVE
   884202 | Bob Halversen       | 1971-04-02 | 14 Ridge Rd Apt 2   | LAPSED
   902117 | Robert Halvorsen    | 1971-04-02 | 14 Ridge Road #2    | ACTIVE
   911004 | R J HALVERSEN       |            | 14 Ridge Rd, Apt 2  | CANCELLED
   911005 | MARGARET HALVERSEN  | 1974-09-19 | 14 Ridge Rd, Apt 2  | ACTIVE
```

You also learn:

- Row 902117 came from a book of business the carrier acquired in 2022.
- Row 911004 was cancelled for non-payment in 2023.
- Claims are paid against `party_id`, and two of these parties have open claims.
- A state regulator requires the carrier to report claim frequency per insured.

**Your task**

1. Group the five rows. State your dividing line in one sentence before you group.
2. One of these rows is dangerous to merge for a reason that has nothing to do with
   data. Which one and why?
3. The acquired book row spells the name differently. Is that a typo or a fact? How
   would you find out, and what do you do while you wait?
4. Write the first move in four sentences, with no schema in it.

---

**Notes, after you have written yours**

Row 911005 is Margaret. Different first name, different date of birth. She is a
different person who happens to live at the same address, which is completely normal in
a household policy. Any matching rule tuned on address will pull her in. This is the
Cortland catering company in a different costume.

Row 911004 is the dangerous one. It was cancelled for non-payment, and in insurance
that is not a status, it is a fact about a person that affects eligibility and pricing
at renewal, and in some states it is reportable. Merging it into an active party either
carries the non-payment history onto an active policy or erases it. Both of those are
wrong and one of them is a regulatory problem. That row needs an underwriter and
probably a compliance officer, not a matching algorithm.

The acquired book row is the subtle one. `Halvorsen` with an O could be a data entry
error at the acquired carrier, or it could be the correct legal spelling and your
carrier has had it wrong since 2019. You cannot tell from the data, because both
systems are equally confident. You find out from a source outside both, which means the
signed application, a state license, or the person. While you wait, you link with a
confidence value and you do not overwrite either spelling, because whichever one you
pick, some downstream document already has the other.

The open claims are the reversibility test. A claim paid against a party ID is money
that already left the building. Merging parties with open claims changes which insured a
claim is attributed to, which changes claim frequency per insured, which is the number
the regulator asked for. That is not reversible with an UPDATE.

The first move, four sentences: link with confidence and provenance, merge nothing,
route the cancelled row and the acquired spelling to a named human, and get a written
answer on who owns the identity decision at renewal. Same as Northstar. The details
change and the shape does not.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
