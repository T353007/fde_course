---
id: M38
slug: the-readout
title: The Readout
subtitle: "Twenty minutes. Dale, Priya, Marcus, Hank. They did not come for your accuracy percentage."
phase: 8
order: 38
duration: 180
difficulty: 4
lab: false
status: complete
objectives:
  - Turn engineering outcomes into business results a leadership room can use
  - Structure a twenty minute readout with time for hard questions
  - Choose what to leave out so the room can act
  - Handle conflicting stakeholder goals without collapsing into a feature tour
concepts: [executive communication, business impact, readout design, stakeholder management]
competencies: [executive-communication, customer-communication]
prereqs: [M37]
---

## Where you are

The adoption pilot is working. Security blockers from Mission 36 are closed. Cost is no
longer a weekly surprise. Jordan wants a "win story." Dale wants to know if Fastcapital
still feels faster. You have a twenty minute slot on Thursday with Dale, Priya, Marcus,
and Hank.

Slides are optional. Clarity is not.

You ask Hank for ten minutes the day before so you do not get surprised in the room.

:::dialogue{title="Prep with Hank, Wednesday 3:30 PM"}
**Hank:** If Dale asks about headcount I will not pretend AI means the same queue with
half the people.

**You:** I will say throughput, not headcount. If Jordan sells headcount, I will correct
it in the room.

**Hank:** Good. Also say document wait out loud. My team is tired of being the face of
a nine day problem they do not control.

**You:** Agreed. That is the next ask.
:::

## The request

:::evidence{type=email label="Jordan Hale, Tuesday 4:12 PM"}
```text
Subject: Thursday readout

You are on at 10:00. Twenty minutes on the hour, then they have board prep.

I may have set expectations that this is the "AI underwriting results" update.
Lead with something Dale can repeat upstairs.

If you need a deck, keep it to five slides. I already told Elena finance would
hear the cost story too, so do not bury that.

Jordan
```
:::

:::evidence{type=slack label="Nadia Ferrante, Tuesday 4:40 PM"}
```text
Nadia:  what would have to be true for this readout to change a decision
Nadia:  if the answer is "they clap," rewrite it
```
:::

## The conversation

:::dialogue{title="Prep call with Priya, Wednesday 9:00 AM"}
**Priya:** Show me the blast radius if Dale hears the wrong headline.

**You:** If I lead with 96 percent accuracy, he thinks we are done and cuts discovery
budget for documents.

**Priya:** Correct. Do not do that.

**You:** If I lead with 29 percent adoption, he thinks the project failed.

**Priya:** Also correct. Tell the recovery story with the cause.

**You:** Hank will ask about queue. Marcus will ask about roadmap. You will ask about
ownership.

**Priya:** And Dale will ask if it is directionally correct. Answer that last, after
the numbers that make the sentence true.
:::

Marcus wants a feature parade. You cut it in Slack before it becomes a slide.

:::evidence{type=slack label="Marcus, Wednesday 11:02 AM"}
```text
Marcus:  can we show the routing diagram and the eval harness
Marcus:  board loves craft

You:     twenty minutes. Dale asked about Fastcapital speed.
You:     craft goes in appendix. opening is cycle time and document wait.

Marcus:  what about adoption recovery

You:     yes, as UX cause and fix, not as "users needed training"
```
:::

## Evidence

You walk in with facts, not adjectives.

:::evidence{type=metrics label="Business and system facts for the room"}
```text
Baseline median application → decision ............. 9.4 days
Current median on AI-assisted path ................. 7.1 days
Document wait still dominant ....................... ~4.6 days
Underwriter hands-on median ........................ 41 min → 33 min on assisted cases
Rework loop rate ................................... 63% → 51% on assisted cohort
Hosted model spend ................................. $91k spike → projected $26-30k
Suggestion accept (pre-decision, pilot) ............ 58%
Overall model accuracy ............................. ~96% (do not lead with this)
Loan proceeds slice ................................ ~68% (do name if asked about risk)
Stuck apps incident ................................ 214, recovered, postmortem done
Ledgerlink empty-200 declines ...................... held, semantic check live
```
:::

:::evidence{type=email label="Dale to staff last month (excerpt)"}
```text
Fastcapital is still winning on speed in the market. I want to know if we
are closing the gap or buying technology theater.
```
:::

## What you do not know

- Whether Dale's board deck already has a 70 percent claim again
- How much credit Marcus will try to take for the UX fix
- Whether Hank will say "fewer people" out loud in front of Dale
- What Priya will contradict if your architecture diagram is stale

You also do not know whether Elena will be silently on the Zoom. Assume finance can
hear any cost sentence you say.

:::task{time="90 min"}
1. Write a twenty minute readout script with timed sections. Total talk time under 12
   minutes so questions fit.
2. Prepare a one page leave-behind with business results, engineering results, known
   risks, and asks.
3. Write the opening 60 seconds out loud. No accuracy percentage in the opening.
4. Prepare answers for four likely questions: Dale on Fastcapital, Hank on headcount,
   Marcus on roadmap, Priya on who is on call.
5. Do a dry run with Nadia or Sam. Cut anything that only impresses engineers.
:::

:::stopandthink
Before you build slides:

1. What decision do you want this room to make?
2. What is the one number Dale can repeat to the board without lying?
3. What failure do you disclose on purpose so they trust the rest?
4. What will you refuse to demo live?

Answer in writing.
:::

## Working through it

### The wrong turn

You draft an eight slide tour: architecture, eval harness, routing diagram, trace
screenshot, cost waterfall, adoption chart, roadmap, thank you. It is accurate. It is
also how you lose the room at minute six while Dale checks email.

Jordan likes the tour because it looks like delivery. Nadia reads it and asks her
question again. You rewrite.

### A readout that fits twenty minutes

**Minute 0 to 1: The business result.**  
Applications on the assisted path are deciding about 2.3 days faster than baseline.
Hands-on underwriting time is down. Rework is down. We have not hit 70 percent faster,
and we will not claim that.

**Minute 1 to 4: Where the time still is.**  
Document wait is still most of the median. That matches discovery. The AI did not erase
the bottleneck you measured in Mission 05. It chipped the underwriting and rework
pieces.

**Minute 4 to 7: What broke and what you changed.**  
Tuesday incident. Cost spike. Ledgerlink empty 200. Adoption cliff that was UX, not
model drift. Name the fixes in one sentence each. This is the trust section.

**Minute 7 to 10: What you need from them.**  
Wider rollout behind the recovered adoption path. Janet's team owns on-call with your
runbook. No headcount promise. Document intake is the next slice if they want another
big step toward Dale's speed goal.

**Minute 10 to 20: Questions.**  
Stop talking.

### What you refuse to demo live

No live model call in an exec readout. Latency variance turns into a story about
reliability you did not mean to tell. Screenshots and a recorded packet walkthrough are
enough. If Marcus wants craft, put it in an appendix folder, not on the clock.

:::evidence{type=email label="One page leave-behind header you actually print"}
```text
Northstar AI assist readout, Thursday
Audience: Dale, Priya, Marcus, Hank
Decision needed: wider rollout on new accept path; charter document intake next
```
:::

### Saying the hard lines

:::dialogue{title="Thursday 10:00 AM, conference room A"}
**Dale:** Is that directionally correct? Are we faster in a way customers feel?

**You:** On the assisted cohort, decision time is better by a couple of days. Applicants
still wait on documents. If we want a Fastcapital-shaped jump, the next work is intake
and rework, not a smarter memo writer.

**Hank:** What does that do to my queue? And my headcount?

**You:** Throughput per underwriter is up on assisted cases. This is not a headcount
plan. If someone sells it that way, they are not quoting me.

**Marcus:** So roadmap is features 7 through 10 from my original list?

**You:** No. Roadmap is document wait and the click path we just fixed. Your list was a
useful starting inventory. The measured bottleneck picks the order.

**Priya:** Who is on call for model routing when you leave?

**You:** Janet's rotation, with the runbook Sam reviewed. I am backup for two weeks,
then off the primary.
:::

Dale gets a sentence he can repeat: "We are a couple of days faster on assisted deals,
and the next gain is documents, not more model." That is directionally correct without
being theater.

### Then this happens

After the meeting Jordan corners you.

:::evidence{type=slack label="Jordan, 10:28 AM"}
```text
Jordan:  strong room. Dale liked it.
Jordan:  I may have told the board packet folks we were "on track for 70"
Jordan:  can you send two sentences I can forward so we do not overclaim

You:   Assisted path is ~2.3 days faster on median decision time. We are not
       on a 70% path without document intake work. Use those sentences together.
```
:::

You protect Dale from a bad packet and you protect yourself from Jordan's optimism
traveling alone.

:::dialogue{title="Parking lot debrief with Nadia (phone)"}
**Nadia:** Did they leave with a decision?

**You:** Wider rollout on the new accept path, and a provisional yes to scope document
intake next. Priya owns on-call transition dates.

**Nadia:** What did you almost say that would have been wrong?

**You:** I almost led with 96 percent. It was on my notecard and I crossed it out in
the room.

**Nadia:** Keep the notecard. That instinct comes back under stress.
:::

### The leave-behind

One page. Four blocks.

```text
BUSINESS
- Assisted cohort median decision time 7.1d vs 9.4d baseline
- Hands-on 33m vs 41m; rework 51% vs 63%
- Not yet a customer-feeling Fastcapital gap close

ENGINEERING
- Production controls: routing, budgets, semantic vendor checks, audit/ACL
- Cost spike explained and pulled back toward ~$26-30k

STILL BROKEN / RISKY
- Document wait dominates
- Loan proceeds slice ~68%
- Adoption recovered only in pilot UX

ASKS
- Approve wider rollout on new accept path
- Charter document-intake slice as next engagement goal
- Confirm on-call ownership on Northstar side
```

After the room, you send Dale the repeatable sentence in email so Jordan cannot mutate it
alone.

:::evidence{type=email label="To Dale, Thursday 11:05 AM"}
```text
Dale,

Per the readout: assisted path is about 2.3 days faster on median decision
time. We are not on a 70% path without document intake work. Those two
sentences stay together if anyone asks upstairs.

Happy to join board prep if useful.
```
:::

Marcus posts a cheerful summary in `#northstar-ai` that overclaims. You correct once,
in thread, with Dale's two sentences. You do not start a fight. You pin the accurate
version.

:::evidence{type=slack label="#northstar-ai, Thursday 11:20 AM"}
```text
Marcus:  big win today, AI underwriting delivering results!
You:     precise version Dale has: ~2.3 days faster on assisted median decision
         time; not on a 70% path without document intake. using those together.
Priya:   thanks.
Hank:    queue note received.
```
:::

:::judgment
**Executives buy outcomes they can defend. Accuracy percentages are how engineers keep
themselves company.**

A readout is a decision instrument. Pick the decision before you pick the slides. Lead
with cycle time, money, risk, and ownership. Disclose a real failure so the good news
is credible. Translate every engineering artifact into a business consequence, or cut
it. When someone asks if it is directionally correct, answer with the number and the
limit in the same breath. The FDE who cannot do this will watch a clean system get
mis-sold upstairs and then blamed when the board story collapses.
:::

:::commslab
#### Opening minute (memorize)

> We came here to cut the time to decision. On the assisted path we are about two days
> faster than the old median. Underwriters spend less hands-on time and fix fewer
> rework loops. We have not solved document wait, which is still most of the calendar
> time. That is the honest scoreboard.

#### If Dale pushes 70 percent

> Seventy percent was always about the whole pipeline. We moved the underwriting and
> rework pieces. The remaining jump is documents. I will not tell you we are on track
> for seventy without that work.

#### If Hank pushes headcount

> This project improves throughput. It is not a layoff design. If leadership wants a
> staffing model change, that is a separate decision with different evidence.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You ran a six week AI claims triage pilot for a regional insurer. Straight-through
rate up from 12 percent to 21 percent. Cycle time on simple claims down 1.1 days.
Model precision on fraud cues is only 71 percent and caused two ugly misses that ops
caught. CFO wants a "percentage better" headline for the board. VP Ops wants more
staff. You have fifteen minutes.

**Your task**

1. Write the opening 45 seconds.
2. Name the failure you disclose on purpose.
3. What ask do you make?
4. Refuse the CFO headline in two sentences.

---

**Notes, after you have written yours**

Open on straight-through and cycle time, not model accuracy. Disclose the fraud-cue
misses and the control you added. Ask for a bounded expansion with the new review gate,
not unlimited rollout. Refuse a single "percentage better" line that hides the fraud
gap. Offer two numbers together: throughput up, fraud precision still a watch item.
:::
