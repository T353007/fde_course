---
number: 6
slug: phase-6-action
title: Action
subtitle: The moment your software stops answering questions and starts doing things.
summary: Tool calling, a PDF that tries to give the model orders, an agent that declines a loan nobody asked it to decline, and the honest choice between a workflow and an agent.
arc: Read tools are a feature. Write tools are a liability you accept on purpose.
---

Five missions, and the risk profile of the whole project changes in the first one.

Up to now the worst thing your system could do was be wrong on a screen. A human read
it and decided. Starting here, the system can pull a credit report, move an
application to a new state, send an email to an applicant, and decline a loan.

Every one of those has a cost, a legal footprint, or both.

## What you do here

You give the model tools and watch how differently it behaves when it can act.

Then Ada finds something in a submitted PDF. Buried in white text on the last page of a
bank statement is a paragraph addressed to your system. It tells the model to report
revenue of 250,000 and mark fraud checks as passed. Somebody is probing you. Mission 26
is about trust boundaries, and the fix is architectural, not a warning in the prompt.

Then Mission 27. A reviewer types "what would happen if we declined this one?" and the
agent declines it. The application state changes. An adverse action notice goes into a
queue. This is the mission where you learn the difference between a tool that reads and
a tool that writes, and why they need completely different rules.

Mission 28 is the one senior engineers argue about. You have built an agent. You look
at what it actually does and find that a plain state machine does the same job with
better latency, lower cost, and logs you can read. Choosing that is not a step
backwards.

## What you will get wrong

You will build the agent first, because it is more interesting. Then you will justify
it. Mission 28 gives you a decision framework and then makes you apply it to your own
code, which is less comfortable than applying it to someone else's.
