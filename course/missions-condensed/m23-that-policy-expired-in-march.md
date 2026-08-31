---
id: M23
slug: that-policy-expired-in-march
title: That Policy Expired in March
subtitle: >-
  credit-policy-FINAL.pdf is a 2023 draft. Semantically perfect. Completely
  wrong.
phase: 5
order: 23
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Diagnose a confident RAG answer that cites a document that was never in
    force
  - Extract precedence rules from Doug and Renee when no flowchart exists
  - 'Filter retrieval by effective date and document status, not by filename'
  - Refuse the cleanup impulse that deletes old policies from the corpus
concepts:
  - RAG metadata
  - effective dates
  - policy precedence
  - citations
  - document lifecycle
competencies:
  - rag
  - debugging
  - fintech-judgment
  - customer-communication
prereqs:
  - M22
condensed: true
durationCondensed: 108
---
## Where you are

Mission 22 ended with a working policy assistant and two unpaid bills. One of them just came due.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:12 AM"}
```text
Jordan:  assistant says 18 months for term loans
Jordan:  cites credit-policy-FINAL.pdf

Renee:   that policy expired in March
Renee:   actually it never started. FINAL was a 2023 draft.

Marcus:  wait so should we delete the old ones?

Doug:    Can you explain that decision to the applicant in writing if the
         citation is a draft?
```
:::

"Delete the old ones" is the sentence you are going to want to agree with. Write it
down as a temptation. Then do not do it.

## Your task

:::task{time="150 min"}
Fix retrieval so an `asOfDate` question cannot cite a never-adopted draft as current
law.

1. Backfill `status` and `effective_from` for all eight policy rows. Use Doug and
   Renee. Do not guess from filenames alone.
2. Change retrieval to filter to documents in force on `asOfDate` before ranking.
3. Implement precedence among remaining candidates: tenant overlay, product overlay,
   base policy. SBA overlay wins when product is `SBA_7A`.
4. Keep old documents in the corpus for historical `asOfDate` queries. Do not delete
   FINAL.
5. Add a test that Jordan's question on 2026-06-12 cites 2026, not FINAL.

Lab profile: full stack or `PROFILE=core` plus policy fixtures.
:::

## Stop and think

:::stopandthink
Before you touch deletion or prompts:

1. Why did similarity retrieval prefer the draft?
2. If you delete FINAL, what breaks when someone asks "what was policy in January
   2024?"
3. Where should precedence live: prompt text, or ranking and filter code?
4. What evidence would convince Doug the answer is explainable in writing?

Two minutes. Write it. Then continue.
:::

## One line to remember

:::judgment
**Semantic similarity is not legal authority.**

A draft can be the closest paragraph in vector space and still be worthless as a
citation. Retrieval systems in regulated work need document status, effective dates,
and precedence before they need a better embedding model.

When a reviewer says a policy expired, or never started, believe them before you tune
chunk size. Then make the corpus honest enough that the next junior does not have to
catch it live on a demo.

Dead documents can be the best semantic match to a bad question. That is exactly when
retrieval without metadata is most dangerous. The fix is not clever prompting and not
deleting history. The fix is treating effective dates and adoption status as part of
authorization for knowledge.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital RAG bot answers clinician questions over clinical guidelines. The corpus
has `sepsis-bundle-FINAL.pdf` (2019 draft), `sepsis-bundle-2024.pdf` (in force), and
`sepsis-bundle-2025-draft.pdf` (future, not approved). A nurse asks for the current
lactate timing rule. The bot cites FINAL because the wording is shorter and closer.

Product wants the drafts deleted before a Joint Commission visit.

**Your task**

1. What metadata fields do you need before re-ranking?
2. Why is deletion the wrong turn before an audit?
3. How do you answer a question about what policy applied on a admit date in 2020?

---

**Notes, after you have written yours**

You need status, effective_from, effective_to or superseded_by, and audience scope.
Deletion destroys the ability to reconstruct why a 2020 chart used an older bundle,
which auditors ask for. Historical as-of retrieval over superseded docs is the answer,
with clear labels that the doc is not current. Same pattern as Northstar, higher
stakes nouns.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
