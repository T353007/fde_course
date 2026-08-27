---
id: M01
slug: what-the-job-actually-is
title: What the Job Actually Is
subtitle: Before you meet the customer, find out what was sold, what was promised, and which of those two things you are on the hook for.
phase: 0
order: 1
duration: 120
difficulty: 1
lab: false
status: complete
objectives:
  - Separate a customer's request from the customer's problem
  - Read a statement of work for the traps in it
  - Write an engagement brief that survives contact with a stakeholder
  - Recognize scope that arrives already damaged
concepts: [engagement scoping, stakeholder mapping, requirements]
competencies: [discovery, customer-communication, fintech-judgment]
prereqs: []
---

## Where you are

It is Thursday. You have been at Halyard AI for five months doing implementation work
on accounts that other people ran. This morning you got a calendar invite titled
"NSC handoff" with no description, and a Slack message from your manager that says
"congrats" with no other context.

Northstar Capital is yours now.

## The request

Here is the email that started the deal. Jordan forwarded it to you eleven minutes
before the handoff call, which is roughly his standard.

:::evidence{type=email label="Forwarded by Jordan Hale, subject: FW: FW: AI underwriting"}
```text
From: Dale Whitmore <dwhitmore@northstarcapital.com>
To: Jordan Hale <jordan.hale@halyard.ai>
Date: Tue, Mar 3, 7:42 AM
Subject: AI underwriting

Jordan,

Good talking last week. Bringing this to the board on the 24th so I want to
move.

We want an AI underwriter. Our process takes too long. Fastcapital announced
theirs in January and we are losing deals to them on speed, not price. I want
processing time down 70% by Q3.

Priya says her team is at capacity. That is why I am calling you.

What do you need from us to start?

Dale
```
:::

Read it again. There are four separate claims in there and only one of them is a
technical requirement.

## The conversation

:::dialogue{title="Handoff call, Thursday 2:00 PM"}
**Jordan:** So this one is great. Dale is bought in at the top, which you know is half
the battle. Budget is approved. They want to start next week.

**You:** What did we actually sell them?

**Jordan:** Discovery and a first production use case. Ten weeks.

**You:** Ten weeks to production?

**Jordan:** Ten weeks to something in production. Not the whole underwriting system,
obviously.

*A pause.*

**You:** Does Dale know it is not the whole underwriting system?

**Jordan:** ...I may have set expectations.

**You:** Jordan.

**Jordan:** Look, he asked if we could get him to 70 percent and I said that a
70 percent reduction is achievable with the right scope. Which is true.

**You:** With the right scope.

**Jordan:** With the right scope. That is your part. Honestly this is why we send you
in first now, we learned that lesson on the Pemberton account.

**You:** Who else at Northstar knows about this project?

**Jordan:** Dale, Priya the CTO, and Marcus who runs product. Marcus is excited. He has
been sending me feature ideas at eleven at night.

**You:** Has anyone talked to an underwriter?

*Longer pause.*

**Jordan:** ...Define talked to.
:::

That last exchange is the entire course in miniature. A company is about to spend real
money changing a process, and nobody has spoken to the eleven people who perform that
process every day.

This is not because Northstar is badly run. It is because the request came from the
top, and requests that come from the top arrive already shaped into a solution. By the
time it reaches you, "our process takes too long" has become "we want an AI
underwriter," and the reasoning that connected those two things happened in someone's
head on a Tuesday and was never written down.

## What you actually got hired to do

An FDE engagement has four jobs. Only one of them is writing code.

**Find the real problem.** The stated problem is a hypothesis. Sometimes it is right.
At Northstar it is partly right, which is worse than being wrong, because partly right
survives scrutiny long enough to get built.

**Build the smallest thing that proves value.** Not a prototype. Not a demo. A working
piece of the real system, handling real cases, in production, that a real person uses
on purpose. Small enough to finish, real enough to count.

**Make it survive you.** Northstar's engineers keep this after you leave. Janet is
going to ask who is on call for it, and "you" is not an answer that ends the meeting.

**Tell the truth in a way people can act on.** Including when the truth is that the
thing they asked for will not do what they want.

## Evidence

Four artifacts landed in your inbox this week. None of them agree with each other, and
that disagreement is information.

:::evidence{type=email label="Statement of work, section 3, excerpt"}
```text
3. SCOPE OF SERVICES

3.1  Consultant shall conduct a discovery assessment of Client's loan
     origination workflow (weeks 1-3).

3.2  Consultant shall design and implement one (1) production use case
     applying machine learning or large language model technology to
     Client's underwriting process (weeks 4-10).

3.3  Success criteria for 3.2 to be mutually agreed in writing at the
     conclusion of the discovery phase.

3.4  Client acknowledges that outcomes described in preliminary
     discussions are illustrative and not contractual commitments.
```
:::

Section 3.3 is the most important sentence in the document. Success criteria are not
defined yet. That is not sloppiness. That is the one piece of room you have, and
whoever wrote it did you a real favor. Your job in the next three weeks is to fill in
3.3 with something honest before someone fills it in with 70 percent.

Section 3.4 is legal protection. It is not social protection. If Dale walks into a board
meeting on the 24th expecting 70 percent, pointing at 3.4 in July will not help you.

:::evidence{type=slack label="Direct message from Nadia Ferrante, 4:47 PM"}
```text
Nadia:  saw you got Northstar. congrats, genuinely
Nadia:  one thing before you go in

You:    go ahead

Nadia:  jordan said 70 percent to the ceo. you know that.
Nadia:  what you probably don't know yet is whether 70 percent is
        reachable at all. neither does anyone else.

You:    so how do I find out

Nadia:  you measure where the time actually goes. all of it. not the
        part they told you about.

Nadia:  and do it before week 3, because in week 3 you have to say a
        number out loud and it's going to be in a deck forever

You:    what if the number is bad

Nadia:  then you say the bad number in week 3 instead of week 9.
        week 3 it's a finding. week 9 it's a failure.
```
:::

:::evidence{type=email label="Marcus Webb, VP Product, Friday 11:20 PM"}
```text
Subject: Requirements! (draft, very rough)

Hey! Super excited to get going. Threw together some initial requirements
so we hit the ground running. Rough draft, tear it apart.

1.  AI reads the bank statements and pulls out revenue
2.  AI reads the tax returns and pulls out revenue (cross check with #1)
3.  AI checks the business against our credit policy
4.  AI flags fraud
5.  AI writes the credit memo
6.  AI recommends approve / decline / counteroffer
7.  Underwriter reviews and clicks approve
8.  Chatbot in the portal so applicants can ask about status
9.  AI calls the applicant for missing docs (can it call? Let's discuss)
10. Dashboard for Dale

Timeline thought: could we have 1-6 by end of May? That gives us June
for testing. Let me know if that works and I'll put it in the board deck.

M
```
:::

Look at the timestamp. Friday, 11:20 PM. Marcus is not being unreasonable. He is
excited, he is trying to help, and he has done the thing product people are trained to
do, which is turn a vague ask into a concrete list.

The problem is that his list is ten solutions and zero problems. Not one line says what
is slow, what is expensive, or what goes wrong today. Item 9 is a person calling a
business owner, described as a feature. Item 10 is a dashboard, which is what people
ask for when they do not know what they need.

And at the bottom is the real move: he wants to put your timeline in the board deck.

## What you do not know

Write this list down. Keep it. You will add to it for three weeks.

- How long does an application actually take, end to end?
- Where in that time does the time go?
- What does an underwriter do during those 41 minutes, or however long it is?
- Who else touches an application besides an underwriter?
- What does "processing time" mean to Dale? Application submitted to decision?
  To funding? Something else?
- Why does Fastcapital feel faster to customers? Is it actually faster, or does it feel
  faster?
- What has Northstar already tried?
- Who tried it, and what happened to them?

That last one matters more than it looks. Most companies have already attempted the
thing you were hired to do. Whatever happened to that attempt is the single most
useful piece of information available to you, and nobody will volunteer it.

:::task{time="60 min"}
Write a one page engagement brief. One page means one page.

It has five parts:

1. **The request as stated.** Dale's words, not your interpretation.
2. **The problem as you currently understand it.** Separate from the request. If you
   cannot separate them, say so.
3. **What you must learn in discovery.** Six to ten questions, ranked. The top three
   should be the ones that could change the shape of the project.
4. **Who you need to talk to and why.** Include people nobody suggested.
5. **What "done" looks like for week 3.** Not week 10. Week 3.

Then write one more paragraph, for yourself only: what would have to be true for the
AI underwriter to be the right answer? Be specific and be fair to it. You will check
this paragraph against real data in Mission 05.

Save it as `customers/northstar/engagement-brief.md`.
:::

:::stopandthink
Before you look at how this is normally handled:

1. Marcus wants your timeline for the board deck by Friday. What do you send him?
2. Dale said 70 percent. You do not yet know if that is reachable. Do you push back
   now, later, or never?
3. Jordan already told the customer something you cannot deliver. What do you owe Jordan,
   and what do you owe Dale?
4. Whose problem is it if this project fails? Write down every name.

Answer all four in writing. This takes five minutes and it will change what you notice
in Mission 03.
:::

## Working through it

### Pulling the request apart from the problem

Dale's email has four claims stacked into eleven lines. Separating them is the whole
skill.

| What he wrote | What kind of claim | Is it checkable? |
|---|---|---|
| "Our process takes too long" | Problem statement | Yes. Measure cycle time. |
| "We want an AI underwriter" | Proposed solution | No. It is a preference. |
| "Losing deals to Fastcapital on speed" | Business claim | Yes, partly. Ask sales. |
| "70% by Q3" | Target | Yes, once you know the baseline. |

Only the second row is a solution, and it is the only row anyone at Northstar is
currently talking about.

The other three rows are gold. "Losing deals on speed, not price" is a testable claim
that tells you what Dale actually cares about, which is not underwriting at all. It is
losing customers. If applications got decisions in two days, Dale would not care
whether a model or a person made the decision.

Hold onto that. In Mission 06 it becomes the thing that saves the project.

### What to send Marcus

Not a timeline. You do not have one, and any number you send becomes real the moment it
enters a board deck.

You also do not send nothing, and you do not send a lecture about how requirements
should be problems rather than solutions. He is a VP, he is trying to help, and he is
going to be your ally later.

Send this:

:::evidence{type=email label="Your reply, Saturday 9:15 AM"}
```text
Subject: Re: Requirements! (draft, very rough)

Marcus,

This is a useful list, thank you. It tells me a lot about where you want
this to go.

I can't give you a timeline for the board deck yet, and I'd rather explain
why than guess.

Right now every item on your list is a thing we would build. What I don't
have yet is what each one is worth. Item 1 and item 5 might save very
different amounts of time, and I don't know which is which. If I estimate
now, I'll be estimating the wrong six things.

Give me until the 21st. What I'll bring is:

  - where the 9 days actually go, measured, not estimated
  - which two or three of your ten items sit on the slow part
  - a real timeline for those

That's a better slide than a date I made up this week, and it survives
questions in the room.

One ask: can you get me 45 minutes with Renee Blackwell and 30 with
Carla in support? Not to pitch anything. I want to watch them work.

Thanks for putting this together on a Friday night. Genuinely.

Imtiaz Alam
Forward Deployed Engineer, Halyard AI
```
:::

Four things are happening in that email.

He gets a date, just not the one he asked for. He gets a reason that is about his
interests, not your comfort. He gets a preview of a better slide than the one he was
going to build. And buried in the last paragraph, you got access to the two people
nobody thought to include.

The compliment at the end is not filler. He worked late on this. Say so.

### The number in the deck

Notice what you did not do. You did not tell Marcus that 70 percent is unrealistic. You
do not know that yet. You have a suspicion, and a suspicion presented as a finding is
how consultants lose credibility in week one.

Nadia's advice was specific. Week 3 it is a finding. Week 9 it is a failure. Right now
it is neither, because you have no data. Your only job this week is to make sure nobody
writes 70 percent into a permanent document before you do have data.

That is why the reply asks for the 21st. It is not a delay tactic. It is putting a
stake in the ground so the number gets set by measurement instead of by momentum.

## Then this happens

Monday morning, before you have met anyone, this shows up in the shared channel.

:::evidence{type=slack label="#northstar-ai, Monday 8:31 AM"}
```text
Marcus:  Morning! Quick update, I moved some things around so we can
         start faster 🎉
Marcus:  Talked to Dale on Sunday, he's on board with scoping to items
         1-6 and we're calling that "Phase 1 AI Underwriting"
Marcus:  Put a placeholder in the board deck for end of May, we can
         adjust
Marcus:  @you can you confirm 1-6 is doable by then? Just directionally

Priya:   Marcus, they haven't seen the codebase yet

Marcus:  Totally! Just directionally 🙂

Sam:     items 2 and 6 touch the underwriting service

Marcus:  is that hard?

Sam:     ...
```
:::

So the placeholder went in the deck anyway.

This is not a betrayal and Marcus is not sabotaging you. He is doing exactly what he
has always done, which is create forward motion. In most of his career that has been
the right instinct. Here it has just committed you to six features and a date, before
anyone has opened the repository.

Also notice Sam's two messages. `items 2 and 6 touch the underwriting service`, then a
single ellipsis in response to "is that hard?" Sam has been at Northstar nine years. He
just told you something important in twelve words, and he is watching to see whether
you can hear it.

### What went wrong, exactly

Nothing you did was wrong. Your email to Marcus was good. It just was not fast enough,
because Marcus talks to Dale on Sundays and you did not know that.

The real mistake was earlier and quieter. You treated a Friday night email as a draft
to be answered on Saturday. In a company where the VP of Product has a standing Sunday
call with the CEO, a Friday night requirements list is not a draft. It is a proposal in
motion.

You could not have known that. But now you do, and the lesson generalizes: **find out
how decisions actually get made at this company in your first week, because it is
almost never the way the org chart suggests.**

### The better version

You cannot un-send Marcus's message. You can make sure it does not harden.

Do not correct him in the channel. Nothing good happens there. Six people are watching,
Dale might read it, and Marcus will have to defend himself, which makes the date more
permanent instead of less.

Reply in the channel with something short and neutral, then move to a call.

:::evidence{type=slack label="Your reply, 8:47 AM"}
```text
You:     Morning. I'll have a real answer on scope + dates on the 21st
         after we've measured where the time goes.
You:     Marcus got 15 min today? Want to make sure the deck holds up
         when someone on the board asks how we got the number.
```
:::

The framing matters. You are not saying his date is wrong. You are protecting him from
a question in a board meeting, which is a thing he genuinely cares about and a thing
you can genuinely help with.

On the call, one ask: label it a placeholder in the deck itself, with the word
"pending discovery" next to it, and a note that the real number comes on the 21st.

Then privately, to Sam:

:::evidence{type=slack label="DM to Sam Ortiz, 9:02 AM"}
```text
You:   you said items 2 and 6 touch the underwriting service
You:   what happens to people who touch the underwriting service

Sam:   how much time do you have

You:   as much as you want. coffee tomorrow?

Sam:   ok
```
:::

That is the most valuable thing you did all morning.

:::judgment
**The request is not the problem, and the person who gave you the request usually
cannot tell you the difference.**

Dale is not confused. He is a former commercial banker running a lending business, and
he has correctly identified that speed is costing him deals. Then he did what everyone
does, which is guess at the mechanism. His guess came from a competitor's press
release.

Your value in the first three weeks is not building. It is holding the problem open
long enough to find out what is actually causing it, while the entire social system
around you pushes to close it. Marcus closes it with a feature list. Jordan closed it
with a percentage. Dale closed it with a job title, "AI underwriter." Everyone is
trying to be helpful. The pressure to commit is not hostile, and that is exactly what
makes it hard to resist.

The tool that buys you time is a date. Not a refusal, a date. "I will have a real
answer on the 21st" is not obstruction, it is a commitment, and it reframes you from
someone slowing things down into someone bringing something specific. You get about
three weeks of this. Spend them well.

One more thing. The most important sentence in this entire mission was Sam's ellipsis.
Institutional knowledge does not show up in documentation, and the people who have it
rarely volunteer it, because they have been ignored before. They test you first. If you
notice the test and follow up, you get access to nine years of context in a single
coffee. If you do not, you spend two months rediscovering it from the code.
:::

:::commslab
Same situation, four audiences. Notice what changes and what does not.

#### To Sam, the senior engineer

> You said items 2 and 6 touch the underwriting service. I read that as a warning.
> What am I walking into?

Direct, no framing, treats his shorthand as expertise. Sam does not want to be managed.

#### To Marcus, the VP of Product

> I want the number in your deck to hold up when a board member asks how you got it.
> Give me until the 21st and I will bring you where the nine days actually go, plus
> which of your ten items sits on the slow part.

Framed around his risk, not your process. Gives him something better than what he asked
for.

#### To Priya, the CTO

> Before I propose anything I want three weeks of measurement and some time with your
> team. I am not going to recommend changes to the underwriting service based on a
> diagram. If your engineers tell me something is dangerous, I will believe them.

She is protecting her team from a consultant who breaks things and leaves. Address that
directly, then prove it.

#### To Dale, the CEO

> You said you are losing deals on speed. That is the thing I am going to work on. I
> want to be careful that we are solving for deals won and not just for a number that
> looks good, because those can come apart. Give me to the 21st and I will show you
> exactly where the time goes.

He does not care about your method. He cares about losing deals to Fastcapital. Say his
goal back to him, more precisely than he said it. Never mention the AI underwriter.
Never say his idea is wrong. You do not know that yet, and if you say it now, defending
it becomes his position.
:::

## Practice

New situation. Same skill. No answer key until you have written a response.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A payments company, 90 employees. The COO emails your firm:

> We need an AI agent to handle chargebacks. Our dispute team is drowning and we
> are paying a vendor $40k a month to handle overflow. Every competitor has
> automated this. Can you build us an agent by end of quarter?

On your intro call you learn:

- The dispute team is four people.
- Chargeback volume grew 3x in a year, though total payment volume grew 1.4x.
- The $40k vendor was hired eight months ago and the COO calls it "a stopgap."
- The COO's boss asked her about AI in the last board meeting.
- Nobody mentions why chargebacks grew faster than payments.

**Your task**

1. List every claim in the email and mark each one as problem, solution, or target.
2. Write the three discovery questions most likely to change the shape of this project.
3. One of the facts above should stop you cold. Which one, and what does it suggest?
4. The COO wants a proposal by Friday. Write your reply in under 150 words.

---

**Notes, after you have written yours**

The fact that should stop you: chargebacks grew 3x while payments grew 1.4x. Disputes
should scale roughly with volume. A gap that size means something changed. New merchant
category, a fraud ring, a product change that confuses customers, a billing descriptor
nobody recognizes, or a broken refund flow pushing people to their bank instead.

If any of those is true, the problem is not dispute handling capacity. It is dispute
generation. Automating the response to a flood is worth much less than turning off the
tap, and it can be worth negative, because it makes the flood cheaper to tolerate and
removes the pressure to fix the cause.

The three questions, roughly:

1. What changed in the last twelve months that could explain 3x versus 1.4x? Break the
   growth down by merchant, by reason code, by product.
2. What does the $40k vendor actually do, and what would happen if you stopped paying
   them tomorrow? This tells you the real cost baseline and whether the work is
   genuinely necessary.
3. What are the four people on the dispute team actually doing all day? Time it. In
   most shops a large share of dispute work is gathering evidence from internal
   systems, which is a boring integration problem and not an agent problem.

The board meeting detail matters. It tells you where the AI framing came from, and it
tells you the COO needs a story for her boss. A good FDE gives her a better story, not
a lecture. "You cut disputes 40 percent at the source" plays better in a board meeting
than "we bought an agent," and it is cheaper to build.

Your Friday reply should decline to propose a solution, commit to a specific date,
name the one number you are going to explain, and ask for two things you need. Under
150 words.
:::
