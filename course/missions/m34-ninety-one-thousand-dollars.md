---
id: M34
slug: ninety-one-thousand-dollars
title: Ninety One Thousand Dollars
subtitle: "Last month the model bill was $22,000. This month it is $91,000. Guessing is not an investigation."
phase: 7
order: 34
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Investigate a cost spike with metrics before proposing a fix
  - Attribute spend to prompt size, retries, model tier, and cache misses
  - Separate an incident echo from a structural cost problem
  - Brief a non-engineer on cost without hiding the engineering causes
concepts: [token cost, prompt bloat, retry amplification, model routing, caching]
competencies: [ai-fundamentals, executive-communication]
prereqs: [M33]
---

## Where you are

The Ledgerlink hold path is live. Hank's queue is moving again. You are starting to
believe production can be boring.

Then finance forwards an invoice.

## The request

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

Dale's version arrives three minutes later as a Slack DM with one line: "Is that
directionally correct?"

Jordan follows with the sentence you have learned to dread.

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

## The conversation

:::dialogue{title="War room, Friday 10:30 AM"}
**Priya:** Show me the blast radius before anyone changes prompts in prod.

**Marcus:** Can't we just switch to a cheaper model?

**You:** Maybe. I do not know what is spending the money yet.

**Tomás:** Is this from the retry bug? We fixed that.

**You:** Part of it might be. Part of it might have been building before Tuesday.

**Nadia:** *on the Zoom tile from Halyard* What would have to be true for the bill to
be mostly one cause?

**You:** I would need the cost broken down by endpoint, model, prompt version, and
retry count.

**Priya:** You have `ai_invocations` from Mission 31. Use it. Do not guess in front of
Dale.
:::

After the call, Tomás looks sick. He thinks the whole bill is his retry worker. It is
not. About 18 percent of the increase is. The rest was already on fire.

:::dialogue{title="Kitchen, 10:45 AM"}
**Tomás:** If I had caught the schema retry thing sooner...

**You:** Then the invoice would still be ugly. Policy prompts are the big piece.

**Tomás:** I can help pull the SQL.

**You:** Yes. Take retries by hour around Tuesday. I will take prompt versions and model
mix. We meet at noon with one table.
:::

## What you know about the system

Every model call should land in `ai_invocations` with `model`, `prompt_version`,
`prompt_tokens`, `completion_tokens`, `latency_ms`, `cost_usd`, `finish_reason`, and
the trace id.

Canon numbers for this month, once you finish the query work:

```text
Last month:     $22,000
This month:     $91,000

Drivers (share of the increase):
  full policy corpus in every prompt ........... 61%
  retry amplification from the M32 bug ......... 18%
  premium model on trivial classification ...... 14%
  no cache on identical extractions ............  7%
```

You do not get those percentages by intuition. You earn them from the table.

## Evidence

:::evidence{type=metrics label="Hosted provider invoice summary"}
```text
Period A (prior):   $22,086.40   calls=184,210   avg_prompt_tokens=1,120
Period B (current): $91,412.17   calls=261,440   avg_prompt_tokens=6,840
```
:::

Calls only rose about 42 percent. Average prompt tokens rose about 6x. That already
kills the "we just got more traffic" story.

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

:::evidence{type=slack label="DM from Sam Ortiz, Friday 11:12 AM"}
```text
Sam:   check prompt_version on policy/answer
Sam:   someone merged "include full corpus for better citations"

You:   someone

Sam:   ...Ah. So you found that.
Sam:   it was a flag. USE_FULL_POLICY_CONTEXT. default true since last Tuesday.
```
:::

## What you do not know

- Whether Dale already told the board the AI would "pay for itself"
- How much of the policy spend is CASCADE overlay duplication
- Whether identical bank statements are being re-extracted on every reopen
- What share of classify traffic is the easy 84 percent slice from Mission 16

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

:::stopandthink
Before you ship a cheaper model everywhere:

1. Which driver would you cut first if you could only cut one this afternoon?
2. If you turn off full-corpus prompting, what quality risk do you accept, and how do
   you measure it?
3. How much of the bill is a one-time incident echo vs a new permanent baseline?
4. What number do you tell Dale that is honest and still useful?

Two minutes. Write it down.
:::

## Working through it

### The wrong turn

Marcus wants the cheap model on everything by lunch. You almost do it. Jordan has already
told Elena "we can optimize."

You flip `DEFAULT_MODEL=cheap-small` in staging and run the golden suite.

:::evidence{type=test label="evals after blanket cheap model"}
```text
overall ................ 91.2%   (was 96.0%)
loan_proceeds .......... 41%    (was 68%)
poor_ocr ............... 38%    (was 61%)
internal_transfer ...... 44%    (was 73%)
card_settlement ........ 98%    (was 99%)
```
:::

You just saved money by breaking the slices that move approvals by five figures. Hank
will feel that as bad declines and bad approvals long before finance feels the invoice.

Blanket model downgrades are not cost control. They are quality roulette.

### Tracking it down

Walk the four drivers with evidence, not slogans.

**1. Full policy in every prompt (61%).**  
`USE_FULL_POLICY_CONTEXT=true` pulls every policy PDF into `/v1/policy/answer`. Average
prompt tokens on that endpoint jumped from about 2.1k to 18k. Retrieval already existed
from Phase 5. Someone bypassed it to "improve citations" after a single bad answer in a
demo. Temporary flag. Still on. Classic.

Temporary control: set the flag false in prod, keep retrieval, watch citation evals for
24 hours.

**2. Retry amplification (18%).**  
Mission 32's schema failures retried model calls five times. That spend is mostly in
the three hour window. It should not recur now that schema errors are not retried. Call
it out as incident cost so Dale does not think the new baseline is $91k forever.

**3. Premium model on trivial classify (14%).**  
Transaction classification for standard card settlements is the 84 percent easy slice.
A premium model on that work is vanity. Keep premium (or hosted strong) for hard
slices. Mission 35 will formalize routing. Today, pin classify to the small hosted
model and re-run slice evals.

**4. No cache (7%).**  
Identical document hashes are re-extracted when a reviewer reopens a file. Redis already
exists on 6379. Cache key: `(tenant_id, sha256, prompt_version, model)`.

### Then this happens

You turn off full corpus. Spend drops. Doug messages you.

:::evidence{type=slack label="Doug Feinberg, Friday 3:40 PM"}
```text
Doug:  policy answers lost appendix citations on two SBA questions this afternoon
Doug:  can you explain a decline that relied on SBA overlay if the model never saw it

You:   retrieval should still surface SBA-overlay.pdf when product=SBA_7A
You:   sending you the two traces

Doug:  one of them retrieved the 2023 FINAL draft instead
Doug:  we have had this conversation
```
:::

Cost control without retrieval discipline just resurfaces Mission 23. You fix the
filter, not by stuffing the corpus back in.

### How you build the attribution table

Do not average your way into a story. Start from spend, then peel.

```text
Step 1  Total increase                     $69.3k
Step 2  Subtract Tuesday retry window      ~$12.5k   → residual $56.8k
Step 3  Diff policy/answer vs last month   ~$42.3k   → residual $14.5k
Step 4  Diff premium vs small on classify  ~$9.7k    → residual $4.8k
Step 5  Estimate duplicate extract hashes  ~$4.8k    → residual ~$0
```

If your residuals do not close, you are missing a driver. Keep querying. Do not round
the mystery into "overhead."

:::evidence{type=metrics label="Duplicate extraction estimate"}
```text
distinct (tenant_id, sha256, prompt_version) extract calls ..... 61,400
total extract calls ............................................ 88,010
implied repeat factor .......................................... 1.43
approx avoidable spend if cached ............................... $4.8k
```
:::

:::evidence{type=slack label="Janet Osei, Friday 2:05 PM"}
```text
Janet:  Who is on call for the policy flag rollback tonight
You:    me primary, Sam secondary, you notified
Janet:  good. if citation evals drop more than two points wake Doug too
```
:::

### The better version of the Friday brief

Give Elena and Priya numbers they can act on:

```text
Increase:                 $69.3k
  Policy prompt bloat:    ~$42.3k   (flag off today; retrieval restored)
  Incident retries:       ~$12.5k   (one-time; fix already shipped)
  Premium on classify:    ~$9.7k    (pin small model pending M35 routing)
  Cache misses:           ~$4.8k    (cache shipping Monday)

Expected next month if controls hold: $24k to $31k at current volume
Risk if we cheapen all models: loan-proceeds slice collapses
```

Dale gets three sentences, not the table. The table is for Priya.

:::dialogue{title="Elena and Priya, Friday 4:10 PM"}
**Elena:** So $91k is not the new normal?

**You:** Not if the flag stays off and classify stays off the premium model. Incident
retries should not repeat.

**Priya:** Show me the blast radius if someone turns full corpus back on for a demo.

**You:** About forty thousand dollars a month at current answer volume, plus Mission 23
class citation bugs. Flag is locked behind change management.

**Elena:** Put the steady-state range in writing for Dale.
:::

You send Dale three sentences. You do not send him the SQL.

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

:::commslab
#### To Elena in finance

> The $91k invoice is real. About $12k is a one-time retry storm from Tuesday's
> incident. About $42k came from a flag that put the full policy set into every answer
> call. We turned that off today. I expect next month closer to the low thirties at
> current volume if the remaining controls land.

#### To Dale

> The bill jumped for specific engineering reasons, not because volume alone 4x'd. We
> already cut the largest driver. I will show Priya the steady-state range on Monday. I
> am not going to cheapen the model on the hard cases that change approvals.

#### To Marcus

> Please do not put "switch to cheaper model" in a deck yet. On the easy slice it is
> fine. On loan proceeds it is not. Mission 35 is the routing design.
:::

## Practice

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
