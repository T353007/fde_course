---
id: M23
slug: that-policy-expired-in-march
title: That Policy Expired in March
subtitle: "credit-policy-FINAL.pdf is a 2023 draft. Semantically perfect. Completely wrong."
phase: 5
order: 23
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - Diagnose a confident RAG answer that cites a document that was never in force
  - Extract precedence rules from Doug and Renee when no flowchart exists
  - Filter retrieval by effective date and document status, not by filename
  - Refuse the cleanup impulse that deletes old policies from the corpus
concepts: [RAG metadata, effective dates, policy precedence, citations, document lifecycle]
competencies: [rag, debugging, fintech-judgment, customer-communication]
prereqs: [M22]
---

## Where you are

Mission 22 ended with a working policy assistant and two unpaid bills. One of them just
came due.

Jordan asked the time-in-business question again this morning. The answer looked great.
Citations were neat. Renee read one filename and stopped the demo with one sentence.

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

## The conversation

:::dialogue{title="War room screen share, 9:25 AM"}
**You:** Walk me through what FINAL means in that folder.

**Renee:** Nothing useful. People rename things FINAL when they are tired.

**You:** Which file is in force for NSC_DIRECT term loans today?

**Renee:** credit-policy-2025.pdf for most of last year. credit-policy-2026.pdf
starting March 1, 2026. We are past that.

**Doug:** And overlays still sit on top. Tenant, then product, then base. SBA wins
when the product is SBA 7(a).

**You:** Is that written down?

**Doug:** Not as a diagram you would like.
:::

:::dialogue{title="Marcus, same call"}
**Marcus:** Can't the AI just prefer the newest file?

**You:** Newest by what? Filename year, upload time, or effective date?

**Marcus:** Whichever.

**Priya:** Show me the blast radius if "whichever" picks a draft.

**You:** Every answer that looks authoritative and is wrong.
:::

## What you know about the system

From Mission 22 and the lab:

| Document | Reality |
|---|---|
| `credit-policy-2024.pdf` | Older base, superseded |
| `credit-policy-2025.pdf` | Prior base |
| `credit-policy-FINAL.pdf` | 2023 draft, never adopted |
| `credit-policy-FINAL2.pdf` | 2025 text, missing appendix C |
| `credit-policy-2026.pdf` | Effective 2026-03-01 |
| `California-overlay.pdf` | CASCADE only |
| `SBA-overlay.pdf` | SBA 7(a) product |
| `grants-program-addendum.docx` | Real, radioactive, still not in the demo index |

`policy_documents.effective_from` exists because of migration V13. Four of eight rows
are still null. Retrieval currently ranks by embedding similarity. Filenames do not
participate as law.

## Evidence

:::evidence{type=http label="POST /v1/policy/answer, the bad good answer"}
```bash
curl -s http://localhost:8000/v1/policy/answer \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m23-final-draft' \
  -d '{
    "question": "What is the minimum time in business for a term loan?",
    "product": "TERM_LOAN",
    "asOfDate": "2026-06-12"
  }'
```
```json
{
  "answer": "Minimum time in business is 18 months for term loans.",
  "citations": [
    {
      "document": "credit-policy-FINAL.pdf",
      "chunkId": "final-tib-18",
      "excerpt": "Term loans require eighteen (18) months time in business."
    }
  ]
}
```
:::

:::evidence{type=policy label="credit-policy-2026.pdf, section 4.2"}
```text
4.2 Time in business
Term loans require twenty-four (24) months time in business unless an
exception in Appendix B applies.
Effective: 2026-03-01
```
:::

:::evidence{type=sql label="policy_documents metadata gaps"}
```sql
SELECT filename, status, effective_from, superseded_by
FROM northstar.policy_documents
ORDER BY filename;
```
```text
 filename                      | status  | effective_from | superseded_by
-------------------------------+---------+----------------+---------------
 California-overlay.pdf        | active  | 2025-01-15     |
 SBA-overlay.pdf               | active  | 2024-06-01     |
 credit-policy-2024.pdf        | unknown |                |
 credit-policy-2025.pdf        | unknown |                |
 credit-policy-2026.pdf        | active  | 2026-03-01     |
 credit-policy-FINAL.pdf       | unknown |                |
 credit-policy-FINAL2.pdf      | unknown |                |
 grants-program-addendum.docx  | active  | 2022-09-01     |
```
:::

Four unknowns. One of them is the draft that just beat the real policy in ranking
because "18 months" sits closer to Jordan's phrasing than "twenty-four (24) months."

:::evidence{type=slack label="Nadia DM"}
```text
Nadia:  what would have to be true for FINAL to be the right citation?
You:    it would have to be adopted, effective on the as-of date, and not
        superseded
Nadia:  and is any of that true
You:    no
Nadia:  then the bug is not the model
```
:::

## What you do not know

- The exact adoption date of the 2025 base, if anyone still remembers
- Whether FINAL2 was ever emailed as "use this" to the floor
- How grants precedence interacts when someone forces that file into an index
- Whether Cascade reviewers have been citing FINAL in tickets for months

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

:::stopandthink
Before you touch deletion or prompts:

1. Why did similarity retrieval prefer the draft?
2. If you delete FINAL, what breaks when someone asks "what was policy in January
   2024?"
3. Where should precedence live: prompt text, or ranking and filter code?
4. What evidence would convince Doug the answer is explainable in writing?

Two minutes. Write it. Then continue.
:::

## Working through it

### The wrong turn

Marcus's delete idea is the wrong turn, and it is popular because it feels like
hygiene.

If you remove `credit-policy-FINAL.pdf` from disk:

- You lose the ability to answer historical questions
- You lose the audit trail that shows why old decisions cited 18 months
- You teach the team that "cleanup" is a substitute for metadata
- The next badly named FINAL2 becomes the new landmine

Cost: a clean demo folder and a system that cannot explain last year's declines.

### Pull the precedence out of people

You need a short working session, not a workshop.

:::dialogue{title="Doug and Renee, 25 minutes"}
**You:** Order of wins, today.

**Renee:** For Cascade SBA in California: California overlay, then SBA overlay, then
base. No. SBA beats California when they conflict on an SBA product.

**Doug:** Tenant overlay beats product overlay beats base, filtered by effective date.
Exception: SBA overlay beats everything when product is SBA 7(a).

**You:** Grants?

**Renee:** We don't use that number. We also do not talk about that program in the
general assistant.

**Doug:** Keep it out of the default index. It is still binding for the people who
originate those files.
:::

Write that as code comments and as a test table. Do not leave it in chat.

### Metadata before cleverness

Backfill first. Example values you should confirm in the room, then load:

```text
credit-policy-FINAL.pdf      status=draft     effective_from=null
credit-policy-FINAL2.pdf     status=incomplete effective_from=2025-04-01
credit-policy-2024.pdf       status=superseded effective_from=2024-01-01
credit-policy-2025.pdf       status=superseded effective_from=2025-01-01
credit-policy-2026.pdf       status=active     effective_from=2026-03-01
```

Drafts with null effective dates never enter the in-force pool for a dated question.
They can still be retrieved if the caller passes `includeDrafts=true` for research, and
that flag defaults to false.

### Filter, then rank, then apply precedence

```python
def retrieve_policy_chunks(question, tenant_id, product, as_of):
    pool = [c for c in index if in_force(c, as_of)]
    pool = [c for c in pool if tenant_visible(c, tenant_id)]
    pool = [c for c in pool if product_visible(c, product)]
    ranked = embed_rank(question, pool, k=20)
    return apply_precedence(ranked, tenant_id=tenant_id, product=product)
```

Precedence is not "ask the model which PDF feels official." Precedence is a sort key.

```python
def precedence_key(chunk, tenant_id, product):
    if product == "SBA_7A" and chunk.doc_type == "sba_overlay":
        return (0, chunk.effective_from)
    if chunk.tenant_scope == tenant_id:
        return (1, chunk.effective_from)
    if chunk.doc_type == "product_overlay":
        return (2, chunk.effective_from)
    return (3, chunk.effective_from)
```

## Tests

```python
def test_term_loan_tib_ignores_final_draft(client):
    response = client.post(
        "/v1/policy/answer",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "m23"},
        json={
            "question": "Minimum time in business for a term loan?",
            "product": "TERM_LOAN",
            "asOfDate": "2026-06-12",
        },
    )
    body = response.json()
    docs = [c["document"] for c in body["citations"]]
    assert "credit-policy-FINAL.pdf" not in docs
    assert any("2026" in d for d in docs)
    assert "24" in body["answer"] or "twenty-four" in body["answer"].lower()


def test_historical_as_of_can_still_see_2025(client):
    response = client.post(
        "/v1/policy/answer",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "m23-hist"},
        json={
            "question": "Minimum time in business for a term loan?",
            "product": "TERM_LOAN",
            "asOfDate": "2025-08-01",
        },
    )
    docs = [c["document"] for c in response.json()["citations"]]
    assert any("2025" in d for d in docs)
```

```bash
make eval SUITE=policy-qa
make test
```

## Then this happens

After the filter ships, Jordan asks a Cascade California SBA question. The answer cites
SBA and California correctly. Then Ada forwards a grants ticket and asks why the
assistant refuses.

:::evidence{type=ticket label="Support, grants program"}
```text
Applicant asked whether the state grants addendum still allows a lower
revenue floor. Assistant said it could not find an in-force source.
Ops knows the addendum is real.
```
:::

That is not a regression of the FINAL fix. That is the allow list doing its job. Route
grants questions to a human queue. Do not "just index it for completeness" without
Priya and Doug in the thread.

## Tracking it down

Confirm FINAL's draft status in email archives if needed. Sam will know where the 2023
credit policy thread lives.

:::dialogue{title="Sam, after you find the thread"}
**Sam:** ...Ah. So you found that.

**You:** FINAL was attached to a review invite that got cancelled.

**Sam:** And then someone dropped it in the shared drive anyway.

**You:** And embeddings loved it.

**Sam:** Filenames are not governance.
:::

## The better version

End state for this mission:

- Drafts do not answer dated production questions
- Old policies remain available for historical `asOfDate`
- Precedence is code with tests
- Citations can be explained to Doug without blushing
- Grants still out of the default index on purpose

Write the precedence card into the repo where Mission 24 can import it. Do not leave it
only in a Slack thread.

```text
1. Exclude NEVER_ADOPTED and DRAFT unless include_superseded / historical mode.
2. Exclude effective_from in the future relative to asOfDate.
3. Exclude superseded documents on or before asOfDate.
4. Rank remaining by precedence tier, then by retrieval score.
5. If product is SBA_7A, SBA overlay outranks other tiers when it has a hit.
6. Tenant overlay still outranks base for non-SBA products.
```

Doug and Renee should recognize their own words in that list. If they do not, you
invented process. Go back to the whiteboard.

### Prompt stays a seatbelt, not the brake

The policy answer prompt already says to watch dates. Keep that line. It is a seatbelt
after the index filter. If a superseded chunk never enters the context, the model
cannot cite it by accident. If you rely on the prompt alone, you are back to Mission
22's demo confidence with Mission 23's hangover.

:::dialogue{title="Jordan, Wednesday 2:20 PM"}
**You:** Yesterday the assistant cited a draft. That is on us, not on you.

**Jordan:** How was I supposed to know FINAL was fake?

**You:** You were not. The citation should have been impossible. It is impossible now
for live answers.

**Jordan:** And if I need old language for a 2024 file?

**You:** Historical as-of mode. Not the default. Ask Doug before you turn it on for a
real applicant.
:::

Juniors should not feel stupid for trusting a citation. The system invited the trust.
Your fix has to make the safe path the default path.

Also mark FINAL2 carefully. It is not a draft, but it is incomplete. Prefer
`credit-policy-2025.pdf` when both match. Keep FINAL2 on disk for audit. Incomplete is
not the same as never adopted, and pretending they are the same will confuse the next
person who greps the corpus.

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

:::commslab
#### To Renee

> Jordan's term loan question now cites 2026. FINAL stays on disk for history and is
> blocked for current as-of queries. Thank you for stopping the demo.

#### To Marcus

> We are not deleting old policies. We are dating them. Deletion would break historical
> answers and hide the mistake instead of fixing ranking.

#### To Doug

> Every production answer filters to in-force docs on asOfDate, then applies the
> precedence you gave us. Citations are only from that pool.

#### To Priya

> Blast radius of the bug was any assistant answer that cited FINAL. Blast radius of
> the fix is limited to policy QA. Grants remain allow-listed out.
:::

## Practice

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

The lesson in one sentence: dead documents can be the best semantic match, so filter
by effective date and precedence in code, and never delete history to make the demo
look clean.
