---
id: M22
slug: ask-the-policy
title: Ask the Policy
subtitle: "A junior underwriter asks one question. The answer lives in three documents, and your first chunker will split the important sentence in half."
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
  - Recognize that a demo that works is not the same as a system that stays right
concepts: [RAG, embeddings, chunking, citations, policy corpus]
competencies: [rag, coding, ai-fundamentals]
prereqs: [M21]
---

## Where you are

Phase 4 gave you a revenue number you can defend. Phase 5 is about the rules that
number gets judged against.

Renee has the policy memorized. A junior underwriter does not. The reviewer portal
still sends people to a shared drive folder named `Credit Policy (CURRENT)`.

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

## The conversation

:::dialogue{title="#northstar-ai, Tuesday 9:30 AM"}
**Marcus:** Perfect first RAG use case. Dump the policies in and let people ask
questions.

**You:** Which policies?

**Marcus:** All of them. The FINAL ones for sure.

**Sam:** there are four files with FINAL in the name

**Marcus:** Then the newest FINAL.

**Doug:** I care less about newest and more about which one is in force.
:::

:::dialogue{title="Renee, hallway"}
**You:** If a junior asks about time in business for Cascade SBA in California,
where do you look?

**Renee:** Base policy for the months. California overlay for Cascade. SBA overlay
on top if it is actually SBA 7(a). In that order, except SBA wins when it speaks.

**You:** Is that written down?

**Renee:** Not as a flowchart. It is how we do it.
:::

Hold that. Mission 23 is about precedence and dead documents. Mission 22 is about
getting retrieval working at all without destroying the sentences that matter.

## What you know about the system

The corpus on disk:

```text
credit-policy-2024.pdf
credit-policy-2025.pdf
credit-policy-FINAL.pdf          (actually a 2023 draft)
credit-policy-FINAL2.pdf         (2025, missing appendix C)
credit-policy-2026.pdf           (effective 2026-03-01, not before)
California-overlay.pdf           (CASCADE tenant only)
SBA-overlay.pdf
grants-program-addendum.docx     (the one nobody mentions)
```

`ai-service` already declares the answer shape and the config knobs:

```python
    policy_corpus_dir: Path = SERVICE_ROOT / "fixtures" / "policies"
    retrieval_top_k: int = 4
    retrieval_chunk_chars: int = 900
    retrieval_chunk_overlap: int = 150
    embedding_backend: Literal["hash", "sentence-transformers"] = "hash"
    embedding_dim: int = 256
```

`POST /v1/policy/answer` is the endpoint. The prompt template already tells the model
to cite chunk ids and to refuse when the excerpts do not cover the question.

Fixtures live under `lab/ai-service/fixtures/policies/` as markdown with YAML style
headers. Same content as the PDFs under `lab/data/policies/`.

## The code

You are building the retrieval path the routes will call. Start with chunking, because
that is where this mission's trap lives.

Naive chunker, 900 characters, 150 overlap:

```python
def chunk_text(doc_id: str, text: str, size: int = 900, overlap: int = 150):
    chunks = []
    start = 0
    index = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append({
            "chunk_id": f"{doc_id}#{index}",
            "doc_id": doc_id,
            "text": text[start:end],
        })
        if end == len(text):
            break
        start = end - overlap
        index += 1
    return chunks
```

That code is fine for blog posts. It is hostile to policy.

## Evidence

:::evidence{type=policy label="SBA-overlay.md, the sentence that matters"}
```text
Minimum time in business for SBA 7(a) is 24 months.

Exception: if the business is a startup acquiring an existing operating company
with two years of tax returns, the 24 month rule may be waived with credit
committee approval.
```
:::

:::evidence{type=log label="First index build, character chunker"}
```text
chunk SBA-overlay#3 ends with: "Minimum time in business for SBA 7(a) is 24 months."
chunk SBA-overlay#4 starts with: "Exception: if the business is a startup acquiring..."
```
:::

Ask the question.

:::evidence{type=http label="POST /v1/policy/answer, first attempt"}
```json
{
  "question": "Minimum time in business for SBA 7(a)?",
  "answer": "Minimum time in business for SBA 7(a) is 24 months.",
  "citations": [
    {"docId": "SBA-overlay", "chunkId": "SBA-overlay#3", "score": 0.83}
  ]
}
```
:::

Technically grounded. Practically incomplete. The exception lived in the next chunk
and lost the retrieval race because the question did not say "startup" or "acquiring."

:::evidence{type=slack label="Jordan after trying the assistant"}
```text
Jordan:  it said 24 months flat. Renee just walked by and said "unless it's an
         acquisition." so which is it?
```
:::

## What you do not know

- Whether section aware chunking is enough, or you also need parent document expansion
  at query time.
- How `credit-policy-FINAL.pdf` will behave once semantic search is on. Spoiler for
  your calendar: Mission 23.
- Whether Hank will accept "I do not know from the excerpts" as a valid assistant
  answer, or treat it as the tool being broken.

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

## Working through it

### Stand it up ugly first

```python
# ai_service/retrieval/ingest.py
from pathlib import Path
import re

HEADER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def load_policy_documents(corpus_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = {}
        body = raw
        match = HEADER_RE.match(raw)
        if match:
            for line in match.group(1).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip()] = value.strip()
            body = raw[match.end():]
        docs.append({
            "doc_id": meta.get("docId", path.stem),
            "title": meta.get("title", path.stem),
            "tenant_scope": meta.get("tenantScope", "ALL"),
            "product_scope": meta.get("productScope", "ALL"),
            "effective_from": meta.get("effectiveFrom"),
            "text": body.strip(),
            "path": str(path),
        })
    return docs
```

Index with the hash backend first. It is not pretty. It is deterministic and free, which
means CI can run it.

### The wrong turn: bigger chunks, same knife

Marcus suggests raising `retrieval_chunk_chars` to 2000. The SBA rule and exception
happen to fit. A different exception in the California overlay still splits, because
the structure was never the unit. You only got lucky on one file.

Cost: a false sense of safety and a demo that fails the second question Jordan asks.

### Chunk on structure

```python
def chunk_by_heading(doc: dict) -> list[dict]:
    """Keep a heading block together, including its exception paragraphs.

    Policy authors write rule then exception under one heading. Honor that.
    """
    text = doc["text"]
    parts = re.split(r"(?m)(?=^#+\s)", text)
    chunks = []
    for index, part in enumerate(p for p in parts if p.strip()):
        chunks.append({
            "chunk_id": f"{doc['doc_id']}#{index}",
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "tenant_scope": doc["tenant_scope"],
            "product_scope": doc["product_scope"],
            "effective_from": doc["effective_from"],
            "text": part.strip(),
        })
    return chunks
```

If a heading block is still huge, split on paragraphs but keep a sliding window that
always includes the previous paragraph. Exceptions almost always start with
"Exception:" or "Unless". Prefer those anchors over raw character counts.

### Answer endpoint

```python
@router.post("/v1/policy/answer", response_model=PolicyAnswerResponse)
def policy_answer(payload: PolicyAnswerRequest) -> PolicyAnswerResponse:
    ctx = current_context()
    tenant_id = payload.tenant_id or ctx.tenant_id
    hits = retrieve(
        question=payload.question,
        tenant_id=tenant_id,
        product=payload.product,
        effective_date=payload.effective_date,
        top_k=payload.top_k or get_settings().retrieval_top_k,
    )
    prompt = render(
        "policy_answer_v2",
        question=payload.question,
        tenant_id=tenant_id,
        product=payload.product or "n/a",
        effective_date=str(payload.effective_date or date.today()),
        context=format_hits(hits),
        json_instruction=build_json_instruction(schema_for(PolicyAnswerModelOutput)),
    )
    # complete_structured ... then map cited chunk ids back to Citation objects
```

For this mission, tenant filtering can be naive. Mission 24 will punish naive. Effective
date filtering can be incomplete. Mission 23 will punish incomplete. Do not pretend you
finished governance. Do make the happy path answer real questions with citations.

### Format the hits so citations stay honest

```python
def format_hits(hits: list[dict]) -> str:
    blocks = []
    for hit in hits:
        blocks.append(
            f"[{hit['chunk_id']}] doc={hit['doc_id']} "
            f"tenant={hit.get('tenant_scope')} "
            f"effectiveFrom={hit.get('effective_from')}\n"
            f"{hit['text']}"
        )
    return "\n\n".join(blocks)
```

If a chunk id never appears in the prompt, the model cannot cite it. That sounds
obvious. It is also the main reason to keep top_k small. Four good chunks beat twelve
mixed ones.

### Jordan's question, working

After the chunk fix, a decent retrieval set looks like:

```text
California-overlay  Section 8 time in business (36 months for CA Cascade)
SBA-overlay          24 months with acquisition exception
credit-policy-2025  Section 9 base months
```

The model should say that Cascade California applicants face the overlay, that SBA
adds its own floor and exception, and that the assistant is citing those chunks. It
should not invent a merged number that appears in no document.

Run the same question with `LLM_PROVIDER=stub` and with Ollama if you have it. The
stub path must pass. Local models are optional here, not a gate.

:::dialogue{title="Jordan tries again"}
**Jordan:** Okay, that matches what Renee said, mostly.

**You:** Mostly?

**Jordan:** It also cited credit-policy-FINAL for the old 24 month base thing and
Renee made a face.

**You:** What kind of face?

**Jordan:** The face she makes when someone opens the wrong workbook.
:::

Good. Your retrieval works. Your corpus governance does not. That is the correct ending
for Mission 22. Do not "quickly delete FINAL" tonight. That is Mission 23's wrong turn
and it has a body count.

## Tests

```python
def test_sba_rule_and_exception_stay_in_one_chunk():
    doc = load_one("SBA-overlay.md")
    chunks = chunk_by_heading(doc)
    joined = " ".join(c["text"] for c in chunks)
    assert "24 months" in joined
    matching = [c for c in chunks if "24 months" in c["text"]]
    assert matching, "rule missing"
    assert any("Exception" in c["text"] and "24 months" in c["text"] for c in chunks)


def test_policy_answer_returns_citations(client):
    response = client.post(
        "/v1/policy/answer",
        headers={"X-Tenant-Id": "CASCADE", "X-Trace-Id": "m22"},
        json={
            "question": "Minimum time in business for SBA 7(a) in California?",
            "product": "SBA_7A",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"], "answers must cite"
    assert "I do not know" not in body["answer"].lower() or body["citations"]
```

```bash
make eval SUITE=policy-qa
```

The policy-qa suite will look fine tonight. Remember that feeling. Mission 23 opens on
it.

## Then this happens

Marcus wants to demo to Dale tomorrow. He asks you to index the grants addendum too,
"for completeness."

:::evidence{type=slack label="Priya"}
```text
Priya:  show me the blast radius of putting the grants program into a tool
        every underwriter can query

You:    every answer that retrieves it, plus whatever compliance thinks about
        us advertising a program leadership does not want discussed

Priya:  leave it out of the demo index. keep the file on disk.
```
:::

## Tracking it down

The grants addendum is real and radioactive. Ingest code should support an allow list.
Default demo index: the seven credit documents. Grants stays on disk for Phase 5
later missions and for people who know why it exists.

This is not censorship of retrieval science. This is product judgment about what a
general assistant should be allowed to surface.

## The better version

By the end of the day you have:

- An index built from structured chunks
- An answer endpoint with citations
- A failing case you fixed (rule/exception split)
- A known unpaid bill (FINAL draft still ranks well)
- A known unpaid bill (tenant filter not proven)

Write those unpaid bills in the mission notes. Missions that end clean teach the wrong
habit.

:::judgment
**RAG fails first at chunk boundaries, not at model wit.**

Teams blame the model when the exception lived one chunk away. The model answered the
question it was given from the passage it was given. Your job was to give it the
passage a careful human would have kept together.

Get retrieval working. Cite everything. And treat a green demo as the start of
governance work, not the end of it.
:::

:::commslab
#### To Jordan

> Try the assistant again on the SBA time in business question. It should show the
> 24 month rule and the acquisition exception in one citation now. If it cites
> credit-policy-FINAL, tell me. That file is on our list for tomorrow.

#### To Marcus

> Demo is fine with citations on screen. Do not show grants. Do not claim we handle
> expired drafts yet. We do not.

#### To Doug

> Every answer returns chunk ids and document titles. Refusal when excerpts are thin
> is preferred over a guess. I need your read on whether "I do not know from these
> excerpts" is acceptable language for reviewers.

#### To Renee

> We are not replacing you. We are trying to keep juniors from opening the wrong FINAL
> file. Tomorrow I need fifteen minutes on which documents are actually in force.
:::

## Practice

Different domain, same skill.

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

The lesson in one sentence: make retrieval work with citations, keep rules glued to
their exceptions, and leave the expired draft problem labeled for the next mission
instead of pretending the demo closed it.
