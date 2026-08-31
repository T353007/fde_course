---
id: M22
slug: ask-the-policy
title: Ask the Policy
subtitle: >-
  A junior underwriter asks one question. The answer lives in three documents,
  and your first chunker will split the important sentence in half.
phase: 5
order: 22
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Stand up retrieval over the Northstar policy corpus from an empty index
  - Choose a chunking approach that keeps rules next to their exceptions
  - Return answers with citations a reviewer can open
  - >-
    Recognize that a demo that works is not the same as a system that stays
    right
concepts:
  - RAG
  - embeddings
  - chunking
  - citations
  - policy corpus
competencies:
  - rag
  - coding
  - ai-fundamentals
prereqs:
  - M21
condensed: true
durationCondensed: 108
---
## Where you are

Phase 4 gave you a revenue number you can defend. Phase 5 is about the rules that number gets judged against.

## The request

:::evidence{type=ticket label="NSC-90211 from underwriting floor"}
```text
Question from Jordan Lee (junior UW):

"What is the minimum time in business for an SBA 7(a) in California under
Cascade? I found three PDFs and they do not agree."

Carla routed it to #northstar-ai because "you have the AI now."
```
:::

That question is why RAG exists here. Retrieval Augmented Generation means: find the
right passages first, then ask the model to answer only from those passages. You are
not fine tuning a model on policy. You are searching documents and then reading.

## Your task

:::task{time="130 min"}
1. Ingest the eight policy documents into a local index using the hash embedding
   backend so the mission runs offline.
2. Implement `POST /v1/policy/answer` end to end with citations.
3. Reproduce the chunk split that separates the SBA 24 month rule from its exception.
4. Fix chunking so a rule and its immediately following exception stay together.
5. Demo an answer to Jordan's Cascade California SBA question that cites more than one
   document. Do not yet solve expired drafts. Note what still looks wrong.
:::

## Stop and think

:::stopandthink
1. If your chunker splits a rule from its exception, who gets hurt first?
2. Is a confident partial answer better or worse than "I do not know"?
3. What metadata are you ignoring right now that Mission 23 will force you to face?

Write before you scroll.
:::

## One line to remember

:::judgment
**RAG fails first at chunk boundaries, not at model wit.**

Teams blame the model when the exception lived one chunk away. The model answered the
question it was given from the passage it was given. Your job was to give it the
passage a careful human would have kept together.

Get retrieval working. Cite everything. And treat a green demo as the start of
governance work, not the end of it.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A university builds a RAG assistant over academic integrity policy. One section says
students may not submit AI generated work as their own. The next sentence says
instructors may allow AI tools when the syllabus says so.

Your first chunker splits those sentences into different chunks. Students ask "Can I
use ChatGPT on my essay?" and get a hard no with a citation to sentence one.

**Your task**

1. What did chunking get wrong?
2. What should a good chunk contain for this section?
3. What unpaid bill remains even after you fix the chunk?

---

**Notes, after you have written yours**

The chunker separated a rule from its governing exception. A good chunk keeps the
prohibition and the syllabus exception together, ideally under the same heading.
Unpaid bill: syllabus level permissions are per course and do not live in the central
policy PDF, so a correct assistant must refuse to give a course specific yes without
that syllabus. Fixing chunking does not finish governance.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
