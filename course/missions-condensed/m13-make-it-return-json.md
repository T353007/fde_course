---
id: M13
slug: make-it-return-json
title: Make It Return JSON
subtitle: >-
  It returns clean JSON every time you test it, and 3.1% of the time in a batch
  of four hundred.
phase: 3
order: 13
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Measure a structured output failure rate instead of estimating it
  - Apply the four rungs of structured output in the right order
  - Build a typed failure taxonomy that separates schema errors from timeouts
  - Recognize when a retry makes a failure worse instead of better
concepts:
  - structured output
  - json schema
  - response format
  - parsing
  - pydantic validation
  - failure taxonomy
  - retries
competencies:
  - coding
  - ai-fundamentals
  - production-reliability
prereqs:
  - M12
condensed: true
durationCondensed: 96
---
## Where you are

Classification works. You showed Marcus on Thursday, he was happy, and Wendy asked when she could call it from the portal.

## The request

:::evidence{type=slack label="DM from Tomás Ferreira, Monday 9:41 AM"}
```text
Tomás:  hey, wiring underwriting-service to your classify endpoint
Tomás:  what does it return when the model messes up

You:    it returns the same shape every time, results array with txn_id
        and classification

Tomás:  no I mean when the model returns something weird. does the JSON
        ever come back broken

You:    haven't seen it. I've run it maybe thirty times

Tomás:  ok cool, I'll just parse it then

You:    yeah should be fine
```
:::

Read your last message again. "Haven't seen it" and "should be fine" are the two
phrases that appear right before every LLM parsing incident, and you just said both in
one conversation.

## Your task

:::task{time="60 min"}
Before you fix anything, measure it.

1. Pull 400 statement pages from the seed data, spread across all three tenants and
   both OCR quality levels. Do not filter for clean ones.
2. Call `/v1/classify/transactions` for each one with the prompt exactly as it is
   today.
3. Count how many responses cannot be parsed into your expected shape, and record
   the raw text of every failure.
4. Group the failures by what is actually wrong with them. Do not group them by
   "parse error."
5. Write the rate in `customers/northstar/notes/m13-json-rate.md` with the date, the
   prompt version, and the model alias. All three matter.
:::

## Stop and think

:::stopandthink
Before the solution:

1. You are about to add "Return only valid JSON. No markdown, no explanation." to the
   prompt. Which of the five failure groups does that fix, and which does it not
   touch? Go group by group.
2. The two truncated responses came back with HTTP 200 and `finish_reason: length`.
   Should your service retry those? Should it retry the refusal? Are those the same
   decision?
3. Tomás is writing a retry in the Java worker. If your service returns HTTP 500 for
   all five groups, what does his worker do to the refusal case?
4. 3.1 percent of 3,680 monthly calls is 114 calls. Each call covers roughly 30
   transactions on one statement page. Estimate how many applications a month are
   affected, and say what "affected" means to Renee.

Write answers to all four. Question 1 is the one people skip, and it is the whole
mission.
:::

## One line to remember

:::judgment
**A structured output failure rate you have not measured is not low, it is unknown, and
the fix that feels sufficient is the one that only moves it halfway.**

The ladder has an order for a reason. Ask nicely, because it is free and it halves the
rate. Enforce the schema at the provider, because that removes whole categories rather
than reducing them. Parse with repair, because you will always meet a provider or a
truncation that enforcement does not cover. Validate with types, because valid JSON
that is missing a transaction is more dangerous than JSON that fails to parse.

The rung most people never build is the fourth one, and it is the one that pays. Not
the pydantic model itself, but the failure taxonomy next to it. The moment a failure
has a name, three things become possible: the caller can decide what to do, your
metrics can show you which kind is growing, and a retry can be a decision instead of a
reflex. Without names, every failure is `Exception`, and the only available response to
`Exception` is "do it again," which is correct for timeouts and actively harmful for
everything else.

Two things happened in this mission that you should not feel finished about. You said
"should be fine" to a downstream engineer based on thirty runs on clean data, and the
person consuming your API wrote a parser with no error branch because of it. And you
found a retry worker in someone else's service that cannot tell a schema error from a
timeout, correctly judged it out of scope, and moved on. Both decisions were
reasonable. Write down the second one anyway.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A freight brokerage uses a model to read shipping manifests emailed by carriers and
turn them into structured records. The output feeds their billing system directly.

Their schema:

```json
{
  "bol_number": "string",
  "shipper": "string",
  "consignee": "string",
  "pieces": "integer",
  "weight_lbs": "number",
  "accessorials": ["string"],
  "total_charges": "number"
}
```

What you find in a week of production logs, out of 9,400 manifests:

```text
211  parse failure, caught, retried, eventually manual
 38  valid JSON, weight_lbs came back as "12,400 lbs"
 17  valid JSON, accessorials was a comma separated string, not an array
  9  valid JSON, total_charges was 0.00 and the manifest showed $2,180
  4  valid JSON, bol_number was a plausible number that is not on the manifest
```

Their engineer is proud that the 211 parse failures all get caught and retried, and
says the system is "99.997 percent reliable" because only the 4 bad BOL numbers made
it to billing uncaught.

**Your task**

1. Rank those five rows by how much damage they do, worst first. Justify the top one.
2. Which rows would a provider level JSON schema eliminate? Which would it not?
3. `weight_lbs: "12,400 lbs"` parses fine as JSON. Where should this be caught, and
   what type of failure is it?
4. The engineer's reliability number is wrong. Explain why in two sentences you could
   say to their VP.
5. `total_charges: 0.00` when the manifest says $2,180 is the one to be frightened of.
   Say why, and describe the check that catches it.

---

**Notes, after you have written yours**

**Ranking.** Worst is `total_charges: 0.00`, then the fabricated BOL number, then the
comma separated accessorials, then the weight string, then the 211 parse failures.

That ordering surprises people, and the principle behind it is the one to carry: the
failures ranked by damage are almost exactly the inverse of the failures ranked by
visibility. A parse failure is loud, cheap, and already handled. A zero that should
have been $2,180 is silent, passes every type check, and goes straight onto an invoice.

**What schema enforcement fixes.** It removes most of the 211 parse failures, and it
fixes the accessorials type error by forcing an array. It does nothing about the
weight string if the schema types that field as a string, and nothing at all about the
zero charge or the invented BOL number, because both are well formed values of the
right type. Enforcement guarantees shape. It has no opinion about truth.

**Where the weight string is caught.** Validation, as a `VALIDATION_ERROR`, not a
parse error. Then fix it properly by typing the field as a number in the schema and
normalizing in the prompt. Do not write a coercion that strips commas and the word
"lbs" and silently continues, because the same coercion will happily turn "12,400 kg"
into 12400 pounds.

**Why 99.997 percent is wrong.** He is counting only the failures his parser noticed.
The 64 rows that produced valid JSON with wrong contents are failures that reached
billing, so the real uncaught rate is at least 68 in 9,400, which is 0.72 percent, and
that is a floor because nobody has audited the manifests that produced no error at all.

**The zero charge check.** Cross-validate the extracted value against something
outside the model. Sum the line items and compare to `total_charges`. Compare against
the carrier's contracted rate for that lane and weight. Reject any invoice where
charges are zero but pieces and weight are not, because that combination cannot exist
in their business. The general rule is the one Mission 14 is built on: a value the
model produced is a claim, and a claim about money gets checked against a source that
is not the model.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
