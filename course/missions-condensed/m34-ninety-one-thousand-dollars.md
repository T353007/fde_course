---
id: M34
slug: ninety-one-thousand-dollars
title: Ninety One Thousand Dollars
subtitle: >-
  Last month the model bill was $22,000. This month it is $91,000. Guessing is
  not an investigation.
phase: 7
order: 34
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Investigate a cost spike with metrics before proposing a fix
  - 'Attribute spend to prompt size, retries, model tier, and cache misses'
  - Separate an incident echo from a structural cost problem
  - Brief a non-engineer on cost without hiding the engineering causes
concepts:
  - token cost
  - prompt bloat
  - retry amplification
  - model routing
  - caching
competencies:
  - ai-fundamentals
  - executive-communication
prereqs:
  - M33
condensed: true
durationCondensed: 96
---
## Where you are

The Ledgerlink hold path is live. Hank's queue is moving again. You are starting to believe production can be boring.

## Key artifacts

:::evidence{type=email label="From Northstar finance ops, Friday 10:06 AM"}
```text
Subject: Halyard AI usage - please explain

Hi,

Our hosted model invoice for this billing period is $91,412.17.
Prior period was $22,086.40.

Dale asked whether this is expected as we scale. Can someone from the
project walk Priya and me through the drivers by end of day?

Thanks,
Elena Vargas
Finance Operations
```
:::

:::evidence{type=slack label="Jordan Hale, 10:09 AM"}
```text
Jordan:  I may have set expectations with Elena that usage would scale
       sublinearly once we cached
Jordan:  do we have caching

You:   not on extractions

Jordan:  ah
Jordan:  can we still say sublinear on the Monday call

You:   after I finish the attribution table. not before.
```
:::

:::evidence{type=metrics label="Hosted provider invoice summary"}
```text
Period A (prior):   $22,086.40   calls=184,210   avg_prompt_tokens=1,120
Period B (current): $91,412.17   calls=261,440   avg_prompt_tokens=6,840
```
:::

## Evidence to use

:::evidence{type=email label="From Northstar finance ops, Friday 10:06 AM"}
```text
Subject: Halyard AI usage - please explain

Hi,

Our hosted model invoice for this billing period is $91,412.17.
Prior period was $22,086.40.

Dale asked whether this is expected as we scale. Can someone from the
project walk Priya and me through the drivers by end of day?

Thanks,
Elena Vargas
Finance Operations
```
:::

:::evidence{type=slack label="Jordan Hale, 10:09 AM"}
```text
Jordan:  I may have set expectations with Elena that usage would scale
       sublinearly once we cached
Jordan:  do we have caching

You:   not on extractions

Jordan:  ah
Jordan:  can we still say sublinear on the Monday call

You:   after I finish the attribution table. not before.
```
:::

:::evidence{type=metrics label="Hosted provider invoice summary"}
```text
Period A (prior):   $22,086.40   calls=184,210   avg_prompt_tokens=1,120
Period B (current): $91,412.17   calls=261,440   avg_prompt_tokens=6,840
```
:::

:::evidence{type=sql label="Cost by endpoint this period"}
```sql
SELECT endpoint,
       COUNT(*) AS calls,
       ROUND(SUM(cost_usd)::numeric, 2) AS spend,
       ROUND(AVG(prompt_tokens)::numeric, 0) AS avg_prompt_tok,
       ROUND(AVG(completion_tokens)::numeric, 0) AS avg_out_tok
FROM ai_invocations
WHERE created_at >= date_trunc('month', now())
GROUP BY endpoint
ORDER BY spend DESC;
```

```text
endpoint                     calls    spend     avg_prompt_tok  avg_out_tok
/v1/policy/answer            41022    41208.11  18440           380
/v1/extract/bank-statement   88010    22105.40   4210           520
/v1/classify/transactions   102188    18840.22   1980            90
/v1/memo/draft                9220     9258.44   6120           900
```
:::

:::evidence{type=sql label="Retry amplification around the M32 window"}
```sql
SELECT date_trunc('hour', created_at) AS hour,
       COUNT(*) AS calls,
       SUM(CASE WHEN metadata->>'retry_of' IS NOT NULL THEN 1 ELSE 0 END) AS retries,
       ROUND(SUM(cost_usd)::numeric, 2) AS spend
FROM ai_invocations
WHERE created_at BETWEEN '2026-06-16 14:00-04' AND '2026-06-16 18:00-04'
GROUP BY 1
ORDER BY 1;
```

```text
hour                 calls   retries   spend
2026-06-16 14:00     4120     1880     4102.18
2026-06-16 15:00     5208     2411     5310.55
2026-06-16 16:00     4988     2204     5022.09
```
:::

:::evidence{type=sql label="Model mix on classify"}
```sql
SELECT model, COUNT(*) AS calls, ROUND(SUM(cost_usd)::numeric, 2) AS spend
FROM ai_invocations
WHERE endpoint = '/v1/classify/transactions'
  AND created_at >= date_trunc('month', now())
GROUP BY model
ORDER BY spend DESC;
```

```text
model                 calls     spend
claude-opus-ish       74102     16210.40
qwen-hosted-small     28086      2629.82
```
:::

## Your task

:::task{time="120 min"}
1. Using `ai_invocations`, reproduce a cost table by endpoint, model, and prompt
   version for this period vs last period.
2. Attribute the $69k increase into the four buckets from canon. Your percentages
   should land within a few points of 61 / 18 / 14 / 7.
3. Identify the flag or prompt version that stuffed the full policy corpus into every
   call.
4. Write a one page cost brief for Priya and Elena: drivers, what is already fixed,
   what you will change next week, and what the steady-state monthly range should be.
5. Do not implement the routing fix yet. That is Mission 35. This mission is the
   investigation and the temporary controls.
:::

## Stop and think

:::stopandthink
Before you ship a cheaper model everywhere:

1. Which driver would you cut first if you could only cut one this afternoon?
2. If you turn off full-corpus prompting, what quality risk do you accept, and how do
   you measure it?
3. How much of the bill is a one-time incident echo vs a new permanent baseline?
4. What number do you tell Dale that is honest and still useful?

Two minutes. Write it down.
:::

## One line to remember

:::judgment
**Cost is a production signal. Treat a 4x invoice like an incident until the drivers are
measured.**

Engineers love to jump to architecture. Executives love to jump to "is AI worth it."
Your job in the middle is attribution. Token averages, retry rates, model mix, and
cache hit rate will usually explain a spike without a new platform. The dangerous move
is a global model downgrade that trades a finance problem for a credit decision problem.
Fix the largest structural driver first, name the one-time incident spend so it does
not poison the baseline, and keep eval slices on the table whenever someone says
"just use the cheap one."
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A claims automation vendor. Last month LLM spend $8.2k. This month $27.9k. Volume of
claims up 15 percent. Your traces show average prompt tokens up from 900 to 4,400 on
`/summarize-claim`. A new "include full guidelines PDF" option defaulted on. Retries on
timeouts also doubled after a latency regression.

**Your task**

1. Rank the likely drivers before you query.
2. Which one do you cut today vs schedule?
3. What do you tell the CFO in four sentences?
4. What eval do you refuse to skip when someone asks for the cheap model?

---

**Notes, after you have written yours**

Likely order: prompt bloat first (token average exploded), retries second (latency
regression), volume last (only 15 percent). Cut the guidelines default today if
retrieval exists. Schedule retry budget and caching. Tell the CFO the increase is
mostly prompt size and retries, not claim volume, and give a restored range. Refuse to
skip the injury-type and fraud-cue slices when downgrading models. Those are where
wrong summaries hurt people.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
