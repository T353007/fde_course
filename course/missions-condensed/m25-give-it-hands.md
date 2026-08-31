---
id: M25
slug: give-it-hands
title: Give It Hands
subtitle: The moment your software stops answering questions and starts doing things.
phase: 6
order: 25
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - 'Explain what a tool call actually is, step by step, at the wire level'
  - >-
    Build a read-only tool loop with real schemas, budgets, and termination
    conditions
  - >-
    Measure how the number of tools changes selection accuracy, cost, and
    latency
  - Decide which capabilities deserve to be a tool at all
concepts:
  - tool calling
  - function schemas
  - the agent loop
  - termination conditions
  - token cost
competencies:
  - agent-design
  - coding
  - ai-fundamentals
prereqs:
  - M24
condensed: true
durationCondensed: 108
---
## Where you are

Phase 5 is done. The policy assistant answers questions about the credit policy with citations, filtered by tenant and by effective date. It works. Renee uses it about twice a day.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:52 AM"}
```text
Renee:   I asked it whether application 44219 clears the DSCR floor and it
         gave me a paragraph about what DSCR is

You:     it doesn't have the application. it only has the policy documents

Renee:   Then what is it for

Renee:   Sorry, that came out wrong. I mean it. What is it for if I still
         have to open the app in the portal, copy the revenue number, and
         come back here

Marcus:  can't the AI just look it up? 🙂

Sam:     that's an actual question though
```
:::

Marcus is right for once, and Sam noticed. Renee's complaint is not that the answers are
bad. The answers are fine. The complaint is that the assistant does not have access to
the thing she is asking about, so she is the integration layer.

## Your task

:::task{time="120 min"}
Implement `POST /v1/tools/invoke` in `ai-service` with exactly the three read tools
above. It has to work with `LLM_PROVIDER=stub` and with a real provider.

Then produce a measurement, not a demo:

1. Write 30 reviewer questions in `data/golden/tool-routing-v1.jsonl`. Each case has
   the question and the list of tools a competent analyst would call, in order.
2. Run all 30. Record for each: tools chosen, steps taken, prompt tokens, latency, and
   whether the final answer is correct.
3. Report four numbers. Tool selection accuracy (did it call the right tools),
   answer accuracy, median steps, and median prompt tokens.
4. Write down every case where the tools were right and the answer was still wrong.
   That set is more interesting than the accuracy number.

Save the report as `customers/northstar/tool-baseline.md`.
:::

## Stop and think

:::stopandthink
Before you read any further:

1. Renee said the revenue field on the application record is the old calculation. You
   put that warning in a tool description. What are the ways that fails?
2. Your loop has `maxSteps=6`. What actually happens on step 7, from the reviewer's
   point of view, and is that acceptable?
3. Marcus is going to ask for more tools. Write down, right now, how many tools you
   think a model can choose between reliably. Commit to a number.
4. Every tool here is read-only. Name three things that could still go badly wrong.

Five minutes, in writing. Question 3 is the one this mission is about.
:::

## One line to remember

:::judgment
**A tool call is a suggestion your code chooses to act on. Everything hard about agents
comes from forgetting that sentence.**

The mechanics are small. A schema, a loop, a step limit. Engineers learn them in an
afternoon and then spend two years learning the part that is not mechanical, which is
that the tool list is a design surface with the same weight as an API.

The thing to take from the 61 percent is not "use fewer tools." It is that the tool list
is read by the model the way a new hire reads a wiki page. Two endpoints with similar
names and identical first sentences will be confused, by a person or a model, and the
person at least gets to ask someone. Names, descriptions, and the boundary between one
tool and two are the actual engineering here. Write descriptions that say when not to
use the tool, because that sentence does more work than the sentence describing what it
does.

The other durable habit is measuring routing separately from answers. Answer accuracy
went from 87 to 64 and the cause was invisible at that level. Tool selection accuracy
made it obvious in one table. When a loop gets worse, ask which step got worse before
you touch a prompt.

And the reason Renee's warning went into a tool description rather than the system
prompt: the system prompt is shared by every question, so a warning about one field gets
diluted by everything else in there. The description is loaded right next to the
decision it is meant to change. That is a small thing that compounds.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A freight brokerage, 220 employees. Brokers match shipper loads to trucking carriers by
phone and email all day. You are building an assistant for the broker desk.

Product hands you a list of capabilities they want as tools:

```
searchLoads              searchCarriers            getCarrierInsurance
getCarrierSafetyRating   getCarrierEquipment       getLaneHistory
getSpotRate              getContractRate           getFuelSurcharge
getShipperCreditLimit    getLoadDocuments          getDriverHoursRemaining
bookLoad                 sendCarrierEmail          updateLoadStatus
```

Facts from your first week:

- 80 percent of broker questions are one of five things.
- `searchCarriers` on a common lane returns 400 or more results.
- `getSpotRate` and `getContractRate` return the same field names with different
  meanings, and brokers mix them up too.
- A carrier without current insurance is not bookable. There is no other rule with that
  property.

**Your task**

1. Split the fifteen into read and write. For each write tool, name the worst thing a
   wrong argument does.
2. Merge the read tools down to at most six. Say what each merge costs.
3. `searchCarriers` returns 400 results. What do you return to the model, and why is the
   answer not "all of them"?
4. Write the description for the merged carrier tool, using the four-part shape.
5. Give a termination condition for the loop that is not a step count.

---

**Notes, after you have written yours**

Read and write. The three writes are `bookLoad`, `sendCarrierEmail`, and
`updateLoadStatus`. `bookLoad` with a wrong carrier id commits a real truck to a real
load and the brokerage owes somebody money. `sendCarrierEmail` cannot be recalled and
goes to an outside company under your brand. `updateLoadStatus` is the quiet one:
marking a load delivered when it is not delivered breaks billing and the shipper's
inventory planning. Everything else reads.

The merge. One `getCarrier` that takes a carrier id and returns insurance, safety rating,
equipment, and lane history together, because a broker never wants one of those alone.
One `getRates` with a `type` parameter covering spot, contract, and fuel surcharge, and
returning explicitly named fields so the two rates can never be confused in the output.
Keep `searchLoads`, `searchCarriers`, `getShipperCreditLimit`, and `getLoadDocuments`.
That is six. The cost of merging is payload size. `getCarrier` now returns lane history
nobody asked for on every call, so cap it at the last 10 lanes and say so in the
description.

The 400 results. You return the top 15 with a `totalMatches` count and a short note that
the search was narrowed. Dumping 400 rows does three bad things: it costs thousands of
tokens on this step and every step after, it buries the relevant rows in the middle of a
long context where models attend to them least, and it invites the model to summarize
instead of choosing. The tool should also apply the insurance rule server side. A carrier
without current insurance is not bookable, so it should never appear in the list at all.
Rules that are absolute belong in your code, not in a description you hope gets followed.

The termination condition. Steps are a backstop, not a plan. Better ones are specific to
the job. Stop when a tool returns the same fingerprint twice. Stop when the model has all
inputs the booking form requires and route it to the form rather than another call. Stop
when cumulative prompt tokens cross a budget. And stop when a tool returns
`insufficient`, hand the question to the broker with what you found, and log it as a
capability gap. The last one turns dead ends into a backlog instead of into loops.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
