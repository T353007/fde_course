---
id: M03
slug: the-kickoff-call
title: The Kickoff Call
subtitle: Ten people on a video call, one of whom knows how the process actually works. She speaks twice.
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
concepts: [kickoff meetings, stakeholder signals, meeting facilitation, contradiction log]
competencies: [discovery, customer-communication, executive-communication]
prereqs: [M02]
---

## Where you are

It is Tuesday, March 10. You had coffee with Sam at 8:15 and learned more in forty
minutes than in three days of curling endpoints. At 9:00 there is a sixty minute call
called "AI Underwriting Kickoff." Marcus wrote the agenda. Twelve people were invited
and ten will show up.

You have run one of these before, as the second engineer, taking notes. This one is
yours.

## The request

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

Read the agenda as a design document, because that is what it is. Fifty five of sixty
minutes are allocated to people talking about a solution. Zero minutes are allocated to
anyone describing the current process. Renee Blackwell, who has underwritten loans at
Northstar for fourteen years, has no slot.

:::evidence{type=slack label="DM from Jordan Hale, Monday 5:12 PM"}
```text
Jordan:   heads up I put us down for 20 min of platform overview tomorrow
Jordan:   Dale asked for it. he wants Janet's team to see what they're
        getting

You:    that's a third of the call

Jordan:   it's a good deck. 11 slides, I've run it 40 times

You:    ok
```
:::

Remember that "ok." It costs you the mission.

## The conversation

:::dialogue{title="Kickoff, 9:02 AM ET"}
**Dale:** Short version. Fastcapital put out a press release in January about AI
underwriting. Since then we have lost four deals I know about on speed. Not price.
Speed. I want processing time down seventy percent by Q3, and I am telling the board
that on the twenty fourth.

**Dale:** Priya says her team is full. So we brought in Halyard. Jordan, go ahead.

*Jordan shares his screen. Eleven slides. He runs them well.*

**Jordan:** ...and that is the provider layer, so you are never locked to one model
vendor. Questions?

**Janet:** Where does this run?

**Jordan:** Your infrastructure. Your VPC.

**Janet:** Who is on call for it?

**Jordan:** That is a great thing to work out in the first two weeks.

*Janet writes something down.*

**Dale:** Marcus, scope.
:::

It is 9:26. Twenty two minutes of a sixty minute call are gone and nobody has said a
single thing about how a loan gets underwritten today.

:::dialogue{title="Kickoff, 9:26 AM ET"}
**Marcus:** So I have six items for Phase 1. One, the AI reads bank statements and pulls
out monthly revenue. Two, same for tax returns, and we cross check them. Three, the AI
checks the business against credit policy. Four, fraud flags. Five, the AI drafts the
credit memo. Six, approve, decline, or counteroffer recommendation.

**Marcus:** Then the underwriter reviews and clicks approve. End of May for one through
six, June for testing.

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

Renee said five words. Marcus answered a different question than the one she asked, and
she said "okay" and stopped. That is not agreement. That is a person deciding the cost
of continuing is higher than the benefit.

:::dialogue{title="Kickoff, 9:44 AM ET"}
**Priya:** Technical questions. Sam?

**Sam:** Items two and six touch the underwriting service.

**Priya:** How bad?

**Sam:** Depends who you ask.

**Janet:** I want to say the thing again. Whatever gets built, my team owns it at 2 AM.
I need to know what it is before end of May shows up in a deck.

**Marcus:** It is already in the deck.

**Janet:** I know.

**Dale:** Let us not spiral. What do you need from us to start?

**You:** Time with the people who do the work. Three weeks of measurement. On the
twenty first I will bring you where the nine days actually go, and which of Marcus's
six items sit on the slow part.

**Dale:** Nine days is right?

**Hank:** Nine to ten. It is in my SLA report.

**Dale:** Fine. The twenty first.

**Renee:** Most of my files are just waiting on documents anyway.

*Nobody responds. Marcus is already sharing the next slide.*

**Marcus:** Last thing, I want to name the workstreams...
:::

The call ended at 10:04. Renee spoke twice, for a total of about eleven seconds, and
both times she said something that makes Marcus's plan impossible.

## What she actually said

Line one: **"We don't use that number."**

Marcus heard "the number is wrong, so fix it." That is not what she said. She said
underwriters do not use the system's revenue figure at all. If that is true, then
building a better version of a number nobody consults changes nothing, and there is
something else that produces the number they do use. That something else is not in any
architecture diagram, is not owned by any team, and has no on-call rotation.

Line two: **"Most of my files are just waiting on documents anyway."**

If most of the time is spent waiting on documents, then the entire six item plan is
aimed at the wrong part of the cycle. Every item Marcus listed happens after the
documents arrive.

Neither line is a complaint. Both are a fourteen year expert stating a plain fact about
her day, in a room where the fact does not fit the agenda.

## What you do not know

- If underwriters do not use the system's revenue number, what do they use?
- How many days does an application spend waiting on documents? Renee said "most."
- Why are documents late? Applicant slowness, or bad requests from Northstar, or both?
- What is Hank's SLA, exactly, and what happens when it is missed?
- How many of the eleven underwriters do it Renee's way?
- Who decided the credit memo was item five instead of item one, and why?

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

## Working through it

### What a kickoff is for

A kickoff is not for alignment. Alignment at a kickoff is a warning sign, because on day
one nobody has enough shared information to genuinely agree, so apparent agreement means
the disagreements are still in the room and now they are invisible.

A kickoff has three jobs.

Surface the disagreements while they are still cheap. A disagreement found on March 10
costs a conversation. The same disagreement found in June costs a rebuild.

Find out how decisions actually get made here. Who talks after whom. Who Dale looks at
before he answers. Who has to be convinced and who has to be informed.

Get access. Names, calendars, artifacts. This is the only job with a deliverable, and if
you leave a kickoff without booked time with the people who do the work, the meeting
failed no matter how it felt.

### The agenda that would have worked

Same hour, different design.

```
9:00  Dale: why now, and what breaks if we do nothing        5 min
9:05  Hank: walk us through last week's queue                10 min
9:15  Renee: walk us through the last file you decided       15 min
9:30  Marcus: the six items, as hypotheses to test           10 min
9:40  Sam + Janet: what worries you about items 1-6          10 min
9:50  Me: what I need in the next three weeks, and by when   10 min
```

Two things changed. The people who perform the process go first, and Marcus's list is
introduced as a set of hypotheses rather than a scope. Both changes are small and both
are hard, because the second one requires Marcus to agree in advance, and you get that
by calling him on Monday, not by reframing his slide in front of the CEO.

"Walk us through the last file you decided" is the highest yield fifteen minutes
available on a kickoff call. It is specific, it is past tense, and it cannot be answered
with a generality. You will use that sentence for the rest of your career.

### Spotting the person who knows

Every room has one. The signals are consistent across every industry.

They speak in past tense and in specifics. Marcus said "the AI will pull it properly."
Renee said "we don't use that number." One is a future claim, the other is a report from
last Thursday.

They correct a number rather than a concept. Hank did it too: Dale said nine days, Hank
said "nine to ten, it is in my SLA report." People who touch the work carry numbers
around.

They reference artifacts. A spreadsheet, a report, a queue, a folder. Marcus referenced
a plan. Sam referenced a service. Renee will reference a file on her desktop, once
somebody asks.

They get interrupted, and they let it happen. This is the strongest signal and the
saddest one. The domain expert has usually been in ten of these meetings, has been
overruled in most of them, and has learned that correcting a VP in front of the CEO
costs her something and changes nothing. So she says her piece in five words, once, and
then she stops. If you are not listening closely, it reads as buy-in.

### Why she went quiet, in her terms

Put yourself in Renee's seat. You have fourteen years here. You have watched at least
two previous automation attempts start and end. You have a workaround that makes your
job possible, and every version of "we are going to automate underwriting" that you have
heard has ended with either nothing happening or your workaround being called a problem.

There is also the part nobody says out loud. Hank suspects that AI means fewer people,
and he is not completely wrong. Renee has done the same arithmetic. Her incentive to
volunteer the details of how her job actually works is not obviously positive.

None of that makes her difficult. It makes her rational. Your job is to change the
math, and you do that by making her the expert rather than the subject. Which means
asking her about her method, using her words for it, and giving her credit in front of
Dale later. In Mission 06 you will do exactly that, and it is the thing that saves the
project.

### The wrong turn: "ok"

The mistake was Monday at 5:12 PM.

Jordan asked for twenty minutes. You typed "ok" because he is your AE, Dale requested it,
and pushing back on a deck felt like a fight not worth having in week one.

The cost was measurable. Twenty two of sixty minutes went to a presentation that six of
the ten attendees did not need. Renee got eleven seconds. Hank's real question got a
one word non-answer. And the six item scope went unchallenged into a recap email,
because there was no time left to challenge it.

What you should have sent on Monday:

:::evidence{type=slack label="What you should have sent, Monday 5:20 PM"}
```text
You:    can we cut the overview to 8 min and put the other 12 into
        Renee walking through the last file she decided

You:    two reasons. Janet's question is going to be "who is on call"
        and slides won't answer it. and I need Dale to hear an
        underwriter describe the process before Marcus scopes it.

You:    you can have the full 20 with Janet's team on Thursday, no
        exec in the room, they'll ask better questions anyway
```
:::

That message gives Jordan something instead of taking something away. He gets a better
audience for his deck. You get the twelve minutes that matter.

### Whether to interrupt

Do not interrupt Marcus to defend Renee. In the moment it looks like advocacy and lands
as a correction of a VP in front of his CEO. Marcus becomes the person who has to defend
his plan, which makes the plan more permanent, and Renee becomes the reason it happened,
which is worse for her than being ignored.

Do use your own agenda slot, which you had.

You can also do the cheapest thing available, which is to say her line back into the
room without opinion attached:

> Renee, I want to make sure I wrote that down right. You said underwriters do not use
> the revenue number the system produces. Can I get thirty minutes with you this week to
> understand what you use instead?

Fourteen words of content, one booked meeting, no argument. Dale hears the sentence.
Marcus is not contradicted. Renee is asked rather than defended.

## Then this happens

10:41 AM.

:::evidence{type=email label="Marcus Webb to all attendees, 10:41 AM"}
```text
Subject: Kickoff recap - Phase 1 AI Underwriting

Great kickoff everyone! Really good energy.

Recap:
- Team aligned on Phase 1 scope = items 1-6
- Target: items 1-6 by end of May, June for testing
- Halyard running discovery in parallel, findings on the 21st
- Open item: on-call model (Janet + Halyard to figure out)

Action items:
- Marcus: workstream doc by Thursday
- Halyard: discovery plan
- Janet: eng capacity estimate for items 1-6

Let's go!
M
```
:::

Nothing in that email is a lie and almost none of it is true.

"Team aligned on Phase 1 scope" describes a meeting in which the underwriting manager
questioned item six, the senior engineer flagged items two and six, the engineering
manager objected to the date twice, and the senior underwriter said the target of item
one is a number her team does not use. Marcus is not being dishonest. He heard no formal
objection, so he recorded no formal objection, and now Janet has an action item to
estimate capacity for six features nobody has validated.

The last line of the email is the real problem. Janet is going to produce an estimate.
Estimates become plans.

### Fixing it without a fight

Do not reply-all with corrections. Reply-all with an addition.

:::evidence{type=email label="Your reply-all, 11:05 AM"}
```text
Subject: Re: Kickoff recap - Phase 1 AI Underwriting

Thanks Marcus. One addition and one ask.

Addition: I logged four open questions from the call that I don't think
we answered yet, and I'd rather they live in writing than in my notes.

  1. Renee: underwriters don't currently use the system's revenue
     number. Need to understand what they use instead. (me, this week)
  2. Hank: effect on queue and SLA if reviews get faster but count
     stays the same. (me + Hank, this week)
  3. Sam: items 2 and 6 touch underwriting-service. Blast radius
     unknown. (me + Sam, next week)
  4. Janet: on-call ownership. (me + Janet, before any build starts)

Ask: Janet, can we hold the capacity estimate until the 21st? If the
discovery numbers move the scope, I'd rather you size the real thing
once than size six things twice.

I'll bring the measured cycle time breakdown on the 21st.
```
:::

Look at what that email does. It puts Renee's sentence into the permanent record with
her name on it, so that on the twenty first it is a documented open question rather than
your opinion. It gives Janet a reason to not do work, which she will take. It attaches
your name as owner to all four items, so nothing reads as a complaint about someone
else's team. And it does not contain the word "aligned."

Marcus replied "great, thanks!" and meant it. He is not your opponent. He is fast, and
fast people need a paper trail more than slow people do.

:::judgment
**On a kickoff call, the volume of a person's contribution is usually the inverse of its
information content.**

The people who talk most are the people whose job is to talk: the executive, the product
lead, the vendor. Their contributions are real, but they are claims about the future.
The people who perform the process contribute claims about the past, which is the only
kind of claim you can check.

So run a kickoff like a hunt for the past tense. When somebody says "we should" or "the
AI will," note it and keep moving. When somebody says "we don't" or "last Tuesday I
had to," stop and get a meeting.

Two habits carry most of the value. Ask "walk me through the last one you did" instead
of "how does the process work," because the second question gets you the official
process and the first gets you the real one. And write a contradiction log instead of
meeting notes, because meeting notes record what was said and a contradiction log
records what cannot all be true at once. Notes get filed. A contradiction log generates
work.

The last thing is about Renee, and it generalizes. A domain expert who has been overruled
before will state a fact once, quietly, and then let it go. She is not testing you on
purpose, but the effect is the same as a test. Everyone in that meeting heard "we don't
use that number." One person wrote it down. Twelve days later that sentence is the reason
the project gets re-scoped instead of cancelled.
:::

:::commslab
Same call, five people to follow up with. Sent between 10:15 and 11:30.

#### To Renee, 10:15 AM

> You said underwriters do not use the revenue number the system gives you. I want to
> understand what you use instead. Thirty minutes this week, no slides, and I would
> rather watch you work through a real file than ask you questions.

Short, quotes her exactly, asks for her method rather than her opinion. "No slides"
matters. She has sat through enough of them.

#### To Hank, 10:20 AM

> You asked what this does to your queue and you got "it should help." That is not an
> answer. Can I see your SLA report and sit with you for an hour? I want your number in
> my findings, not mine.

He is worried about headcount and he is not going to say so. Offering to carry his
number into the CEO readout is the most useful thing you can give him.

#### To Marcus, private, 11:15 AM

> Your six items are the right list of candidates. What I do not know yet is which two
> are worth the most, and I would rather you present that on the twenty first than have
> me present it. Can we do thirty minutes on the eighteenth so you see the numbers
> first?

He is going to lose four of six items in two weeks. Start converting him from author to
co-author now, while it costs nothing.

#### To Janet, 11:20 AM

> You asked twice and got a non-answer twice. I am not going to hand your team a service
> with no runbook. Whatever we build, I want your name on the design and a Northstar
> engineer paired with me from week one.

Answer the question she actually asked, in her language, and offer the thing she wants,
which is control.

#### To Dale, no message

Nothing today. He gave you the twenty first. Every message you send him before then
spends credibility you have not earned yet. Show up on the twenty first with a number.
:::

## Practice

Different industry, same room.

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
