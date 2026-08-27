---
number: 8
slug: phase-8-the-human-layer
title: The Human Layer
subtitle: The system works. Usage is falling every week. Nobody can tell you why.
summary: A security and compliance review you have to survive, an adoption collapse that is not about model quality, and the meeting where you tell executives what actually happened.
arc: A correct system that nobody uses has produced zero business value.
---

Three missions where the code is mostly done and the project can still fail.

This phase exists because engineers consistently underestimate it. You can build a
system that is accurate, fast, cheap, and well tested, and still deliver nothing,
because the people who were supposed to use it went back to the spreadsheet in week
three.

## What you do here

Yuki and Doug sit down with your architecture. Yuki wants to know what happens when a
tenant's document contains instructions, where the audit trail lives, and who can read
the trace payloads that contain full bank transaction text. Doug wants to know whether
you can explain a declined application to the applicant in writing, in plain English,
with the specific reasons. If you cannot, the feature does not ship. Neither of them
is being difficult. Both are describing constraints you should have designed for.

Then adoption. Week 1 was 67 percent. Week 2 was 48. Week 3 is 29. Your first
hypothesis will be model quality, and you will have eval data that seems to support it.
You will be wrong. Six user interviews later you find that accepting a suggestion takes
six clicks and the suggestion appears after the reviewer has already made up their
mind. Wendy told everyone this in Phase 6.

Mission 38 is the executive readout. Dale, Priya, Marcus, and Hank in one room. You
report the business result, the engineering result, what is still broken, and what you
would do next. You have twenty minutes and slides are optional.

## What you will get wrong

You will present the accuracy number. Nobody in that room cares about the accuracy
number. Mission 38 is about translating engineering results into the two or three
things a business leader can act on.
