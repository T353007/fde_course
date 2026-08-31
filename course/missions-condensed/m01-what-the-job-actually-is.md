---
id: M01
slug: what-the-job-actually-is
title: What the Job Actually Is
subtitle: >-
  Before you meet the customer, find out what was sold, what was promised, and
  which of those two things you are on the hook for.
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
concepts:
  - engagement scoping
  - stakeholder mapping
  - requirements
competencies:
  - discovery
  - customer-communication
  - fintech-judgment
prereqs: []
condensed: true
durationCondensed: 48
---
## Where you are

It is Thursday. You have been at Halyard AI for five months. This morning you got a
calendar invite called "NSC handoff" with no description. Your manager sent "congrats"
on Slack with no other context.

## Key artifacts

Read these before you write anything.

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

Sam's ellipsis matters. He knows something Marcus does not. Write that down.

## Your task

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

## Stop and think

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

## One line to remember

:::judgment
**The request is not the problem. The person who gave you the request usually cannot
tell you the difference.**

Dale wants speed. That is real. "AI underwriter" is his guess at the fix. Your job in
weeks 1 to 3 is not to build. It is to measure where the time goes before everyone locks
in a plan.

Give a date, not a refusal. "I will have a real answer on the 21st" buys you time and
sounds like a commitment.

Watch who speaks little but knows a lot. Sam's ellipsis is a test. Follow up and you
get years of context. Miss it and you rediscover it from the code.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
