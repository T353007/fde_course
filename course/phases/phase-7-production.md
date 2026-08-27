---
number: 7
slug: phase-7-production
title: Production
subtitle: Real applications, real money, and a Tuesday afternoon that goes badly.
summary: Deploying, tracing an AI workflow, running an incident from detection to writeup, catching a vendor that fails while returning 200, and finding out why the bill quadrupled.
arc: Green dashboards during a live outage are the normal case, not the exception.
---

Six missions. This is the longest phase and the one people remember.

Your system is live. Not for everyone, and behind a flag, but real applications from
real businesses are flowing through code you wrote. The gap between staging and
production is about to become a personal experience rather than a concept.

## What you do here

You deploy properly. Flags, config, versioned prompts, and a rollback path that works
when you are stressed.

You build observability for an AI workflow, which is different from normal
observability. A span with a duration is not enough. You need the model, the prompt
version, the token counts, the retrieved documents, the validation result, and the
reason a fallback fired. When something goes wrong at 2 a.m., that metadata is the
difference between fifteen minutes and six hours.

Then Tuesday. At 14:02 the model starts returning `"$78,231 approximately"` where a
number should be. The Java parser throws. The retry worker cannot tell a schema error
from a timeout, so it retries five times. By 16:47, when Carla's ticket volume finally
gets someone's attention, 214 applications are stuck and your dashboards are green.
You run the whole incident. Contain, fix, recover the stuck work, then write it up
honestly.

Mission 33 is a quieter failure and a worse one. Ledgerlink returns HTTP 200 with an
empty account list. Your code reads that as zero revenue and declines people.

Mission 34 is the bill. 22,000 last month, 91,000 this month. You investigate with real
metrics instead of guessing. Mission 35 fixes it with routing, caching, and the local
model you set up back in Mission 17.

## What you will get wrong

During the incident you will want to fix the root cause first. That is the wrong order.
Mission 32 teaches containment before diagnosis, and the difference between them is
about two hours of customer impact.
