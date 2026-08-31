---
id: M03
slug: the-kickoff-call
title: The Kickoff Call
subtitle: >-
  Ten people on a video call, one of whom knows how the process actually works.
  She speaks twice.
phase: 1
order: 3
duration: 150
difficulty: 2
lab: false
status: complete
objectives:
  - Run a kickoff that surfaces disagreement instead of manufacturing agreement
  - Identify which person in the room actually performs the process
  - Catch a contradiction in real time and turn it into a booked follow-up
  - Leave a kickoff with commitments and artifacts rather than enthusiasm
concepts:
  - kickoff meetings
  - stakeholder signals
  - meeting facilitation
  - contradiction log
competencies:
  - discovery
  - customer-communication
  - executive-communication
prereqs:
  - M02
condensed: true
durationCondensed: 60
---
## Where you are

It is Tuesday, March 10. You had coffee with Sam at 8:15. At 9:00 there is a sixty
minute call called "AI Underwriting Kickoff." Marcus wrote the agenda. Ten people will
show up.

## Key artifacts

:::evidence{type=email label="Calendar invite, sent by Marcus Webb"}
```text
AI Underwriting Kickoff
Tue Mar 10, 9:00 - 10:00 AM ET

Attendees: Dale Whitmore, Priya Raghunathan, Marcus Webb, Janet Osei,
Hank Delgado, Sam Ortiz, Renee Blackwell, Jordan Hale, Imtiaz Alam,
+ 3 from Product

Agenda
  9:00  Welcome + why now (Dale)
  9:05  Halyard platform overview (Jordan / Halyard)
  9:25  Phase 1 AI Underwriting scope, items 1-6 (Marcus)
  9:45  Technical Q&A
  9:55  Next steps
```
:::

Jordan gets twenty minutes for slides. That is a third of the call. Renee gets zero
minutes on the agenda.

## Kickoff transcript (the parts that matter)

:::dialogue{title="Kickoff, 9:05 to 9:26 AM ET"}
**Dale:** Priya says her team is full. So we brought in Halyard. Jordan, go ahead.

*Jordan shares his screen. Eleven slides.*

**Janet:** Where does this run?

**Jordan:** Your infrastructure. Your VPC.

**Janet:** Who is on call for it?

**Jordan:** That is a great thing to work out in the first two weeks.

**Dale:** Marcus, scope.
:::

Twenty two minutes are gone. Nobody has said how a loan gets underwritten today.

:::dialogue{title="Kickoff, 9:26 AM ET"}
**Marcus:** Six items for Phase 1. One, AI reads bank statements and pulls monthly
revenue. Two, same for tax returns, cross check. Three, AI checks credit policy. Four,
fraud flags. Five, AI drafts the credit memo. Six, approve, decline, or counteroffer
recommendation. Underwriter reviews and clicks approve. End of May for one through
six.

**Dale:** Is that directionally correct?

**Marcus:** That is the plan.

**Renee:** We don't use that number.

*A pause of about two seconds.*

**Marcus:** Which number, sorry?

**Renee:** Monthly revenue. The one the system gives us.

**Marcus:** Right, that is exactly what we are fixing. The AI will pull it properly out
of the statements.

**Renee:** Okay.

**Hank:** Marcus, on item six. If the AI recommends a decision, who owns it?

**Marcus:** The underwriter still approves.

**Hank:** So it is the same number of reviews.

**Marcus:** Faster reviews.

**Hank:** What does that do to my queue? I have eleven people and an SLA.

**Marcus:** It should help the queue.

**Hank:** Should.
:::

Renee said five words. Marcus answered a different question. She said "okay" and stopped.

:::dialogue{title="Kickoff, 9:44 AM ET"}
**Priya:** Technical questions. Sam?

**Sam:** Items two and six touch the underwriting service.

**Janet:** Whatever gets built, my team owns it at 2 AM. I need to know what it is
before end of May shows up in a deck.

**Marcus:** It is already in the deck.

**Dale:** What do you need from us to start?

**You:** Time with the people who do the work. Three weeks of measurement. On the
twenty first I will bring you where the nine days actually go, and which of Marcus's
six items sit on the slow part.

**Dale:** Nine days is right?

**Hank:** Nine to ten. It is in my SLA report.

**Renee:** Most of my files are just waiting on documents anyway.

*Nobody responds. Marcus is already sharing the next slide.*
:::

Renee spoke twice, about eleven seconds total. Both times she said something that breaks
Marcus's plan.

## What she actually said

**"We don't use that number."** Marcus heard "fix the number." Renee said underwriters
do not use the system's revenue figure at all. If that is true, a better number changes
nothing.

**"Most of my files are just waiting on documents anyway."** If most time is waiting on
docs, Marcus's six items all happen after the docs arrive. They may aim at the wrong
part of the cycle.

## Your task

:::task{time="75 min"}
Three artifacts. All three today, while the call is fresh.

**1. A contradiction log.** Not meeting notes. A table with four columns: what was
said, who said it, what it contradicts, and how you would check which one is true. Start
with Renee's two lines. There are at least four more contradictions in the transcript
above. Find them.

**2. Six interview requests, sent today.** Each one names a person, a length, and a
reason that serves them and not you. Do not send a single email to all six. Rank them:
if you only get three, which three?

**3. One message to Renee.** Two or three sentences. She got talked over in front of the
CEO and then said the most important thing on the call to silence. Write what you send
her at 10:15 AM.

Save the log as `customers/northstar/contradiction-log.md`. You will add to it for three
weeks and it becomes the backbone of Mission 05.
:::

## Stop and think

:::stopandthink
Before you read on:

1. Renee said "we don't use that number" and Marcus moved on. Should you have
   interrupted him in the moment? Argue both sides before you pick.
2. Twenty two minutes went to Jordan's deck. Whose fault is that, and what would you have
   done differently on Monday at 5:12 PM?
3. Hank asked what it does to his queue and got "it should help." What is Hank actually
   worried about?
4. Rank all ten attendees by how much they know about how an application really moves
   through Northstar. Then rank them by how much they spoke. Compare the lists.

Write it down. Five minutes.
:::

## One line to remember

:::judgment
**On a kickoff, the loudest person often knows the least about how work actually
happens.**

Ask "walk me through the last one you did" instead of "how does the process work." The
second question gets the official process. The first gets the real one.

Write a contradiction log, not meeting notes. Notes record what was said. A contradiction
log records what cannot all be true at once.

Renee stated facts once, quietly, then let them go. One person wrote them down. That
sentence later re-scopes the project.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A freight brokerage, 220 employees. They match shipper loads to carriers. The COO wants
"an AI dispatcher" that automatically assigns loads to carriers, and there is a kickoff
call with nine people. Here is the part of the transcript that matters.

```text
COO:        We're leaving margin on the table because dispatch takes
            too long. Competitors are automating this.

VP Product: So the model scores every carrier against every load and
            picks the best match. Rate, on-time history, equipment,
            lane. We have all four in the system.

Ops Lead:   What about carriers that only take our calls?

VP Product: Meaning?

Ops Lead:   Nothing, go ahead.

VP Product: Then dispatch just confirms. Should cut assignment from
            twenty minutes to two.

CFO:        Twenty minutes is the assignment or the whole thing?

VP Product: The assignment.

Dispatcher: We usually book the carrier before the load is in the
            system.

*silence*

VP Product: Right, and that's part of what we're cleaning up.
```

**Your task**

1. Two people said something that breaks the plan. Quote both lines and explain what
   each one breaks.
2. The CFO asked a question that nobody answered. What is he actually asking, and why
   does it matter more than the answer he got?
3. Write your one intervention during the call. One sentence, no interruption of the VP.
4. List the first three people you book time with, in order, with the reason for each.

---

**Notes, after you have written yours**

"What about carriers that only take our calls?" The Ops Lead is saying that carrier
relationships are personal and informal. Some carriers accept loads because a specific
dispatcher calls them, not because the rate is best. A model that ranks by rate,
on-time, equipment, and lane has no feature for "answers the phone for Marisol." If a
meaningful share of capacity works that way, the model's top-ranked carrier will decline,
and the automated dispatcher will be slower than the human one because it will burn
turns on carriers who say no.

"We usually book the carrier before the load is in the system." This one is larger. It
means the system's timestamps do not describe reality. If the carrier is booked by phone
before the load record exists, then the twenty minute assignment time measured in the
system is measuring data entry, not dispatch. The entire premise, that dispatch is slow,
may be an artifact of when people type things in. Notice that the room went silent and
then the VP called it something to clean up. That is the most expensive sentence on the
call and it got reframed as a data hygiene problem in nine words.

The CFO's question is the right one. He is asking whether twenty minutes is the whole
cycle or one step in it. If the whole load lifecycle is fourteen hours and the assignment
is twenty minutes of it, then automating assignment cannot produce the margin the COO
wants, no matter how good the model is. He is asking for a denominator. Nobody gave him
one, and without a denominator the project has no ceiling and no way to fail honestly.
You are going to spend the next three weeks producing that denominator.

Your one intervention: "Can I get the dispatcher's line into the notes? If carriers get
booked before the load is entered, I need to know what our timestamps are actually
measuring before I trust the twenty minutes." No contradiction of the VP, one fact
preserved, one meeting implied.

First three bookings: the dispatcher who spoke, because he described reality; the Ops
Lead, because he stopped mid-sentence and that means there is more; and whoever owns the
load records, because you need to know how a load gets created and by whom before any
number in this system means anything. The VP of Product comes fourth, and by then you
will have questions worth his time.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
