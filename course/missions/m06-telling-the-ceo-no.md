---
id: M06
slug: telling-the-ceo-no
title: Telling the CEO No
subtitle: His target is real. His plan cannot reach it. You have twenty minutes and he has a board meeting on the 24th.
phase: 1
order: 6
duration: 180
difficulty: 4
lab: false
status: complete
objectives:
  - Lead a hard conversation with the outcome the executive actually wants
  - Separate a real target from a plan that cannot reach it
  - Protect a stakeholder who was wrong without making them the villain
  - Leave with a re-scoped mandate in writing
concepts: [executive communication, reframing, saying no, stakeholder protection, mandate]
competencies: [customer-communication, executive-communication, discovery]
prereqs: [M05]
---

## Where you are

Friday, March 21. Twenty minutes on Dale's calendar. Title: "Discovery readout." Jordan
asked for thirty and got twenty. The board meeting is Monday the twenty fourth.

You have the numbers. 9.4 days. 41 minutes. 5.1 days waiting on documents. 63 percent
rework. 2.8 days per rework loop. Automating the 41 minutes caps out near 7 percent.

You also have Marcus, who will be in the room, who told Dale underwriting was the
bottleneck, and who will hear you take that apart in front of his CEO.

## The request

:::evidence{type=email label="Calendar invite from Dale's assistant"}
```text
Discovery readout
Fri Mar 21, 10:00 - 10:20 AM ET

Attendees: Dale Whitmore, Priya Raghunathan, Marcus Webb, Jordan Hale, Imtiaz Alam

Dale needs a clean story for the board on Monday. Please keep to twenty
minutes. Deck optional.
```
:::

:::evidence{type=slack label="DM from Jordan Hale, Thursday 6:48 PM"}
```text
Jordan:   do not walk in and say the AI underwriter is dead
Jordan:   he bought a story. give him a better story that still has AI
        in it or this account gets weird fast

You:    the plan can't hit 70

Jordan:   then say that. carefully. I may have set expectations.
```
:::

## The conversation

You try this meeting three times in your head before you walk in. Two of them fail.
Study the failures. The third one is the one you run.

### Version A: lead with "your idea will not work"

:::dialogue{title="Version A, the one that loses the room"}
**You:** Thanks for the time. I measured cycle time. The AI underwriter will not get
you to seventy percent.

**Dale:** Is that directionally correct?

**You:** The underwriter only touches the file for forty one minutes. Automating that
is about seven percent of the nine days.

**Dale:** So you are saying my plan is wrong.

**You:** I am saying the plan cannot reach the target.

**Dale:** Fastcapital shipped an AI underwriter. We are losing deals to them on speed.

**You:** Their press release is not a measurement of our process.

*Priya looks at the table. Marcus's jaw tightens. Jordan has stopped taking notes.*

**Dale:** I have a board meeting on Monday. What exactly am I supposed to tell them.
That we hired a firm to tell me no.

**You:** That the bottleneck is documents and rework, not underwriting.

**Dale:** That is not what Marcus told me.

**Marcus:** I said what I believed at the time.

**Dale:** We are done for today. Send me the slides.
:::

What broke: you led with the negation. Dale's identity in this project is "the CEO who
responded to Fastcapital." When you open by killing his plan, he has to defend the
plan to defend himself. The numbers never get a fair hearing. Marcus gets hung out as
the person who misled him. You leave with no mandate.

### Version B: soft enough that nothing changes

:::dialogue{title="Version B, the one that sounds fine and does nothing"}
**You:** We learned a lot this week. Cycle time is about nine days. There are some
real opportunities in document intake, and underwriting is also in the mix.

**Dale:** Is that directionally correct?

**You:** Directionally yes. We think a phased approach makes sense. Keep the AI
underwriter as the north star, and maybe also look at documents.

**Marcus:** So Phase 1 is still items one through six?

**You:** We could sequence it. Documents first, then the fuller underwriter later.

**Dale:** So we are still on track for seventy percent by Q3.

**You:** We will know more after the first slice.

**Dale:** Good. Put that in the board deck. Jordan, stay with the original story. Board
does not need the weeds.
:::

What broke: you never said the hard sentence. "Phased" and "also" let Dale keep the
plan and the target fused. Monday he tells the board they are building an AI
underwriter for a seventy percent cut. In July that sentence becomes your failure.
Soft is not kind here. Soft is expensive.

### Version C: lead with Dale's real goal

:::dialogue{title="Version C, Friday 10:00 AM, the one you run"}
**You:** You said you are losing deals to Fastcapital on speed. That is the problem I
measured.

**Dale:** Go.

**You:** Median time from application to decision is 9.4 days. I will show where those
days go in one picture.

*You put the map on the screen. Five numbers. No clip art.*

**You:** Underwriters have their hands on a file for 41 minutes median. Waiting on
documents is 5.1 days. Sixty three percent of applications take at least one rework
loop. Each loop costs 2.8 days median.

**Dale:** Is that directionally correct?

**You:** It is measured from the event history, not from the portal timestamps. Sam
checked the queries with me.

**Dale:** So where is the seventy percent.

**You:** In documents and rework. Not in the forty one minutes.

**Dale:** Fastcapital announced an AI underwriter.

**You:** They announced a story about speed. Your losses are about speed. If we cut
document wait and rework, you get speed whether or not we replace the underwriter.

**Marcus:** I thought underwriting was the slow part.

**You:** Calendar time in review is about two days. Most of that is queue. Hands-on is
forty one minutes. Product and I sorted that this week. The useful question is which
wait kills the deal.

**Dale:** So you are telling me not to build the AI underwriter.

**You:** I am telling you the AI underwriter, aimed at judgment, cannot hit a seventy
percent cycle cut. The target is right. The first build has to aim at the 5.1 and the
rework, or Monday's slide becomes a promise we miss.

**Priya:** Show me the blast radius if we touch intake instead of decisioning.

**You:** Smaller. Document service and the reviewer queue. We stay out of the revenue
function until we have earned the right to be there.

**Dale:** What do I tell the board.

**You:** That we are cutting time to decision by fixing the waits that dominate the
clock, using AI where reading documents and classifying transactions removes rework.
Seventy percent remains the target. The vehicle changes.

**Dale:** Marcus, you good.

**Marcus:** Yeah. I want the first slice to be something underwriters feel in a week,
not a dashboard.

**Dale:** You have a re-scoped mandate. Write it down today. I am not putting seventy
percent AI underwriter on Monday's slide. I am putting speed, and a six week proof.
:::

## Evidence

:::evidence{type=email label="Your follow-up, Friday 11:40 AM"}
```text
Subject: Re-scoped mandate, for Monday's board language

Dale, Priya, Marcus, Jordan,

Capturing what we agreed in the room so Monday's wording stays clean.

Goal (unchanged):
  Reduce median time from application to decision. Target remains
  70% faster than the current 9.4 day median.

Plan (changed):
  We are not building a full AI underwriter in the first slice.
  First production use case will attack document intake quality and
  the rework loops that currently hit 63% of applications.
  Underwriter hands-on time is 41 minutes median. Automating it
  alone cannot reach the target.

Board language I recommend:
  "We measured where the nine days go. Most of the delay is document
   wait and rework, not underwriting judgment. First build targets
   those waits. Success criteria for the first slice to be written
   into SOW 3.3 next week."

Marcus: I will not frame this as product being wrong. The 2.2 day
review clock was a real signal. We separated queue time from
hands-on time together.

If any of this does not match your memory of the meeting, reply
before end of day.

Thanks,
Imtiaz Alam
```
:::

:::evidence{type=slack label="DM from Marcus, Friday 12:02 PM"}
```text
Marcus:  thanks for the cover on the 2.2 days
Marcus:  I almost corrected you in the room and then I got it
Marcus:  don't make me look clever. just don't make me look dumb

You:    deal
```
:::

## What you do not know

- Whether Dale's board will accept the reframe without a number for Q3
- Whether Hank will hear "rework" as "my team is the problem"
- What Janet will demand before any intake change ships
- Whether Jordan already emailed a partner about the AI underwriter story
- What the first slice actually is (that is Monday, Mission 07)

:::task{time="75 min"}
Write the talking track for Version C in your own words. One page max.

Constraints:

1. First sentence must be Dale's goal (losing deals on speed), not your finding.
2. You must say the seventy percent target is real and the original plan cannot reach
   it. Both clauses. Same paragraph is fine.
3. Marcus's 2.2 day clock gets explained as queue versus hands-on. His name is not
   blamed.
4. End with a concrete ask: re-scoped mandate in writing before Monday.

Then write the three sentences you will not say, even if Dale pushes. Example of the
shape: anything that makes Jordan or Marcus the villain in front of Dale.

Save as `customers/northstar/ceo-readout-talking-track.md`.
:::

:::stopandthink
Before you read the judgment:

1. In Version A, which sentence made Dale defend the plan instead of hearing the
   numbers?
2. In Version B, which word let the old plan survive?
3. Why lead with Fastcapital losses instead of with 41 minutes?
4. What do you owe Marcus after this meeting, in one sentence?

Five minutes.
:::

## Working through it

### Why Version C works

Dale does not buy engineering. He buys not losing deals to Fastcapital. When you open
on that sentence, you are on his side of the table. The numbers then explain his
problem more precisely than his plan did. He can keep the target and drop the vehicle
without losing face.

The phrase that does the work is short: **the target is real, the plan cannot reach
it.** Say both halves. Target alone is flattery. Plan alone is an attack. Together they
are a decision.

### Protecting Marcus

Marcus was wrong about the bottleneck. He was also the person who got you into rooms,
who pushed for speed, and who will still be here when you leave. If Friday's story is
"product misled the CEO," you win the meeting and lose the account.

In the room you say "product and I sorted that." In the email you repeat it. In the
deck there is no slide titled "what we believed that was false." There is a slide that
shows two clocks and what each one means.

### Dale will push back

He does. Expect these three, and answer them cold.

**"Fastcapital shipped an AI underwriter."**  
Answer: they shipped a speed story. Measure our waits. Match their speed where our
clocks actually burn.

**"So what do I tell the board."**  
Answer: give him language in the room, then in writing the same hour. Empty air after
a hard meeting is how the old story returns over the weekend.

**"Are you telling me not to use AI."**  
Answer: no. You are telling him where to aim it. Documents and rework first.
Judgment later, if the math still says so.

### The wrong turn: correcting Jordan in the room

Jordan told Dale seventy percent was achievable. That is true with the right scope and
false with the scope Dale heard. If you unpack that distinction while Dale is watching,
Jordan has to defend himself, Dale has to pick a side, and the numbers become secondary.

Talk to Jordan before the meeting and after. In the room, the subject is Dale's goal and
the measured clock. Sales history is not a third agenda item in a twenty minute slot.

:::judgment
**Say no to the plan. Never say no to the goal, and never make a colleague pay for the
correction.**

Executives can change vehicles in public if you give them a better destination story
before you take the keys. Lead with their loss, show the measured clock, separate
target from plan in one clean sentence, and protect the people who were wrong for
ordinary reasons. Then write the mandate down before the board deck freezes.

If you only remember one move from this mission, remember Version C's first line. You
did not walk in as the person killing an AI project. You walked in as the person who
finally measured why deals are slow. Everything else was arithmetic.
:::

:::commslab
Full set. Same facts. Four audiences. After the Friday meeting.

#### To Dale

> Your target stays. Seventy percent faster than 9.4 days. The first build aims at
> document wait and rework, because that is where the days are. I sent board language
> in email. If you want a different sentence for Monday, tell me before Sunday noon.

#### To Marcus

> You asked for a slice underwriters feel in a week. That is the right bar. I will not
> retell the 2.2 day story as a product miss. Help me pick the slice on Monday so it
> is yours as much as mine.

#### To Priya

> We stay off the revenue function for the first slice. Blast radius is document
> service, intake, and the reviewer queue. I will bring Janet the on-call question
> before I bring you a design.

#### To Jordan

> Account is intact. Story for Monday is speed via waits and rework, with AI in the
> document path. Do not send partner email that still says "AI underwriter Phase 1"
> until you and I sync on the sentence. I am not hanging you out. I need the outside
> story to match the room.
:::

## Practice

Different company. Same twenty minutes.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A mid-market EHR vendor. CEO wants an "AI clinical documentation scribe" to cut
physician after-hours charting by 50 percent. Board on Thursday. You measured:

```text
Median after-hours charting: 68 minutes per clinic day
Median time waiting on lab results before note can close: 5.4 hours
Share of notes reopened after addenda from coding: 57%
Median addendum loop: 1.1 days until note locks
```

The CMIO told the CEO the bottleneck is "doctors typing." The CMIO will be in the
room.

**Your task**

1. Write Version A's opening sentence (the one that fails).
2. Write Version C's opening sentence (the one that works).
3. One paragraph that keeps the 50 percent target and kills the scribe-first plan.
4. One sentence that protects the CMIO without lying.

---

**Notes, after you have written yours**

Version A opens on "the scribe will not hit 50 percent." CEO defends the purchase.

Version C opens on after-hours burden and notes that do not lock, which is what the
CEO actually hates when physicians complain.

The paragraph: 50 percent is real if you remove waits and addenda. A scribe replaces
typing. Typing is 68 minutes. The larger clock is labs and coding loops.

Protect the CMIO: "Typing time is real. We separated it from the waits that keep notes
open overnight."
:::
