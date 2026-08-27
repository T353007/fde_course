---
number: 3
slug: phase-3-first-blood
title: First Blood
subtitle: Your first model call, and every way it can quietly ruin your week.
summary: LLM fundamentals learned by doing, structured output, hallucination, the first real eval, and running a model on your own hardware because compliance says so.
arc: The model works on your six examples. That fact means nothing.
---

Six missions. This is where the AI actually starts, and where most people's mental
model of AI gets taken apart.

If you have used a chat assistant, you have a set of intuitions about how models
behave. Some of those intuitions transfer to production systems. Several of them will
cost you money and one of them will cost you an incident.

## What you do here

You make your first model call from the Python service and learn what tokens, context
windows, and temperature actually do to your bill and your latency.

You ask for JSON and get JSON, then you ask for JSON four hundred times and find out
what percentage of the time you do not get JSON. Then you fix that properly, which is
not by asking more nicely in the prompt.

You watch the model invent a number for a field that was blank in the source document,
and you learn why "it made it up" is the wrong description of what happened.

You build the first eval. Sixty labeled cases from Renee. It is not impressive
infrastructure and it immediately changes how you work.

Then Doug and Yuki read the design document and ask why account numbers are being sent
to an outside vendor. So you install Ollama, pull Qwen, run the whole eval suite
against a model on your own machine, and get a result that is genuinely mixed.

## What you will get wrong

You will believe your first accuracy number. It is 96 percent. It is real, and it is
useless, and Mission 16 explains why in a way that will stay with you.
