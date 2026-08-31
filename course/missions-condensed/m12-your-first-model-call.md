---
id: M12
slug: your-first-model-call
title: Your First Model Call
subtitle: >-
  Tokens, context windows, and temperature, learned by watching them cost you
  money and time.
phase: 3
order: 12
duration: 210
difficulty: 2
lab: true
status: complete
objectives:
  - Make a real call to ai-service and read every field in the response
  - Predict cost and latency from token counts before you run anything
  - Choose a temperature on purpose and know what it does not control
  - Explain what the recorded stub provider buys you and what it hides
concepts:
  - tokens
  - context windows
  - temperature
  - non-determinism
  - system prompts
  - cost per call
  - stub providers
competencies:
  - ai-fundamentals
  - coding
  - architecture
prereqs:
  - M11
condensed: true
durationCondensed: 84
---
## Where you are

Eleven weeks of this project have been talking. You re-scoped away from the AI underwriter, you have Renee's eleven rules written down, and you know the 5.1 days of document wait is the thing worth attacking.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:52 AM"}
```text
Marcus:  ok so we're building now?? 🎉
Marcus:  I have a product review Thursday. Can I show something?

You:    I can show you a model classifying transactions by Thursday.
You:    It will be one endpoint and it will be ugly.

Marcus:  perfect, that's all I need
Marcus:  quick q, how much does this cost us per application

You:    I'll have a number for you Thursday.

Janet:   how much does it cost when it's wrong
```
:::

Janet's question is better than Marcus's question. Park it. You cannot answer it yet,
and Mission 15 is where you get the tools to.

## Your task

:::task{time="75 min"}
Work only from the `usage` block and the alias table above. No new code yet.

1. Compute the cost of that single call by hand. Show prompt cost and completion cost
   separately.
2. Compute the same call under `hosted-mid`.
3. Northstar processes 1,840 applications a month. A three month statement window has
   a median of 61 credit transactions. At 40 transactions per call, work out the
   monthly cost of this endpoint under both aliases.
4. Now compute it again if you send one transaction per call instead of batching 40.
   Assume the system message is 218 tokens and one transaction plus its wrapper is 50
   prompt tokens and 12 completion tokens.
5. Write the four numbers in `customers/northstar/cost-notes.md`. You will need them
   in Mission 34 and you will not remember them.
:::

## Stop and think

:::stopandthink
Before you scroll:

1. You batched 40 transactions into one call. Name one thing that gets worse as you
   raise that number, and one thing that gets worse as you lower it.
2. `max_output_tokens` is 800. What do you expect to happen if the model needs 8,000?
   Be specific about what you would see in the response.
3. You are about to set `temperature: 0` because you want the same answer every time.
   Write down what you believe that guarantees.
4. Marcus asks "how much per application" on Thursday. Which of your four numbers do
   you give him, and what do you say about the other three?

Two minutes. Write it down. Question 3 is the one that costs people money.
:::

## One line to remember

:::judgment
**Tokens and latency are not implementation details. They are the two constraints that
decide what your system is allowed to be.**

Most engineers coming to production AI treat the model call like any other network
call: send a request, handle the response, move on. The habit that separates people who
ship affordable systems from people who get a surprise invoice is reading the usage
block every single time, especially when the answer was correct.

The specific trap in this mission is worth naming because almost everyone walks into
it. Temperature 0 feels like `--deterministic`. It is not. It is a variance reduction
knob on one source of randomness out of several, and the ones it does not touch are the
ones outside your process. An engineer who understands that builds caches with version
keys, tests properties instead of bytes, and stores the model version with every
result. An engineer who does not builds a system that works for four months and then
quietly disagrees with itself.

The other durable habit here is smaller and pays constantly: batch size and model
choice are cost decisions you make before you have any quality data. Make them
explicitly, write down that they are unverified, and go build the thing that can verify
them. An unverified decision you wrote down is engineering. The same decision you
forgot about is the reason a bill goes up 4x and nobody can say why.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A medical billing company processes denied insurance claims. They want a model to read
each denial letter and pick the correct appeal template.

What you know:

- 34,000 denial letters a month.
- A denial letter averages 2,900 tokens after OCR. The longest 5 percent run past
  14,000 tokens.
- The current prompt sends the letter plus a 26,000 token reference document listing
  every appeal template and the rules for choosing one.
- Their engineer set `max_output_tokens: 4096` because the model sometimes explains
  its choice at length.
- They use the premium alias: $15 per million prompt tokens, $75 per million
  completion tokens.
- Their engineer reports the pilot cost as "about $400 a month" based on 200 test
  letters.

**Your task**

1. Compute the real monthly cost. Show prompt and completion separately.
2. Their engineer's $400 estimate is wrong. Find the reason. It is not arithmetic.
3. Name the single change with the largest cost effect, and estimate the new bill.
4. One of the facts above is a correctness risk, not a cost risk. Which one, and what
   goes wrong?

---

**Notes, after you have written yours**

**The real cost.** Prompt per letter is 26,000 + 2,900 = 28,900 tokens. Times 34,000
letters is 982.6 million prompt tokens, at $15 per million, which is $14,739. Assume
output averages half the allowance, say 2,000 tokens: 68 million completion tokens at
$75 per million is $5,100. Total near $19,800 a month, not $400.

**Why the estimate was wrong.** He measured 200 letters and multiplied by cost per
letter, which is the right method. The error is that his 200 test letters were short
and clean, so his average prompt was maybe 1,100 tokens instead of 2,900, and his
average output was short because easy letters get short answers. Test samples are
almost always easier than production. This is the same mistake the golden dataset in
Mission 15 is built to catch, and it shows up in cost estimates before it shows up in
quality numbers.

**The largest change.** Stop sending the 26,000 token reference document in every
request. It is 90 percent of the prompt and it is identical every time. Retrieve the
three or four relevant templates instead, or fine tune, or at minimum use provider
prompt caching on the static block. Cutting the static block to 2,000 retrieved tokens
takes prompt tokens to 4,900 per letter, so $2,499 a month, and total near $7,600. If
you can also stop asking for prose reasoning and get a template ID plus a short
citation, completion drops to maybe 200 tokens and the bill lands near $2,900.

That single change is worth more than every other optimization combined, which is the
general shape of LLM cost work: find the big static block in the prompt.

**The correctness risk.** `max_output_tokens: 4096` combined with letters that run
past 14,000 tokens. Long letters produce long explanations, explanations get cut at
4,096, and the response comes back with `finish_reason: length` and a truncated
answer. If their code reads the template ID from the end of the output, or parses JSON,
those letters fail. If it takes the first template mentioned in a half-finished
explanation, they file the wrong appeal and nobody notices, because a 200 response with
plausible text does not look like a failure.

Ask to see how many of their pilot responses had `finish_reason` other than `stop`.
The answer is almost never zero, and it is almost never something anyone has checked.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
