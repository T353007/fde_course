---
id: M24
slug: cascade-saw-baylines-policy
title: Cascade Saw Bayline's Policy
subtitle: >-
  A reviewer at Cascade gets Bayline pricing. The prompt fix will feel right and
  will fail.
phase: 5
order: 24
duration: 240
difficulty: 5
lab: true
status: complete
objectives:
  - 'Prove a cross-tenant policy leak from evidence, not from vibes'
  - Find the post-filter bug that keeps recall high and authorization weak
  - Reject prompt-only tenant instructions as a security control
  - Ship a pre-filter retrieval path Yuki and Doug will sign
concepts:
  - multi-tenant authorization
  - RAG security
  - post-filtering
  - trust boundaries
competencies:
  - security
  - rag
  - customer-communication
  - production-reliability
prereqs:
  - M23
condensed: true
durationCondensed: 96
---
## Where you are

Effective dates work. Precedence works. The assistant is starting to feel trustworthy.

## The request

:::evidence{type=slack label="#northstar-ai, Thursday 11:04 AM"}
```text
Maya (Cascade UW):  um. the assistant just quoted Bayline's rate card
Maya:               in an answer about our renewal pricing
Maya:               I am not supposed to see that right?

Yuki:               Say "just" one more time if someone suggests a prompt fix

Doug:               Can you explain that decision to the applicant in writing
                    when the citation belongs to another tenant?

Ada:                Assume the applicant is hostile. Also assume the reviewer
                    screenshot is already in email.
```
:::

This is not an awkward demo. This is a partner-confidentiality incident with a small
blast radius that can become a large one if you shrug.

## Your task

:::task{time="150 min"}
1. Reproduce the Cascade or Bayline leak with a failing test.
2. Read `ai_service/retrieval.py` and identify whether tenant filtering runs before or
   after top-k.
3. Fix authorization so forbidden tenant chunks never enter the prompt assembly step.
4. Add a regression test that a CASCADE question cannot cite or echo BAYLINE-only
   text.
5. Write a short incident note for Yuki and Doug: blast radius, fix, residual risk.

Do not "fix" this by adding a system prompt line that says ignore other tenants.
:::

## Stop and think

:::stopandthink
Before you edit prompts:

1. If a Bayline chunk is inside the model context, can any prompt reliably stop the
   model from using it?
2. What is the difference between filtering citations for display and filtering the
   retrieval pool for generation?
3. Why did post-filter feel reasonable to whoever shipped it?
4. What would Yuki accept as proof the leak is closed?

Write answers first. Two minutes.
:::

## One line to remember

:::judgment
**Authorization belongs in the query, not in the instructions.**

If a model can see a chunk, you should assume a determined user can get the meaning of
that chunk out. In multi-tenant RAG, retrieval is an access control surface. Ranking
tricks that filter after top-k are how confidential partner terms leak while dashboards
stay green.

When Yuki says say "just" one more time, she is not teasing you. She is naming the
exact class of fix that fails under pressure.

Post filtering feels like security because there is a filter function with the word
tenant in it. Ranking over the forbidden set still lets forbidden text win slots,
poison prompts, and, when metadata is wrong, survive into the answer. Treat a prompt
line the way you would treat a SQL comment that says do not return other customers'
rows. Then put the WHERE clause back where it belongs.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A multi-tenant HR software company builds a benefits policy assistant. Tenant A is a
union shop. Tenant B is non-union. Post-filter retrieval lets a Tenant B manager
question retrieve Tenant A's union wage tables because the embedding match is strong,
then a fallback backfills when Tenant B chunks are sparse. Someone proposes: "Add to
prompt: never discuss other customers."

**Your task**

1. Why does the prompt line fail?
2. Where must the tenant check run?
3. What evidence closes the incident for security?
4. What do you tell Tenant A in the first hour without guessing that nobody read it?

---

**Notes, after you have written yours**

The prompt fails because the wage table text is already in context. The check must run
before ranking into prompt assembly, with no backfill from foreign tenants. Closing
evidence is a failing-then-passing test with perfect foreign matches in the index, plus
a log or metric that foreign tenant chunks are zero in prompt context for the request.
In the first hour you tell Tenant A what class of data was exposed, the time window you
know so far, and that access is already blocked. Do not say "probably nobody noticed."
Same as Cascade and Bayline, different nouns.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
