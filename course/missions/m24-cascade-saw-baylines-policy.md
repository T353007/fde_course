---
id: M24
slug: cascade-saw-baylines-policy
title: Cascade Saw Bayline's Policy
subtitle: "A reviewer at Cascade gets Bayline pricing. The prompt fix will feel right and will fail."
phase: 5
order: 24
duration: 240
difficulty: 5
lab: true
status: complete
objectives:
  - Prove a cross-tenant policy leak from evidence, not from vibes
  - Find the post-filter bug that keeps recall high and authorization weak
  - Reject prompt-only tenant instructions as a security control
  - Ship a pre-filter retrieval path Yuki and Doug will sign
concepts: [multi-tenant authorization, RAG security, post-filtering, trust boundaries]
competencies: [security, rag, customer-communication, production-reliability]
prereqs: [M23]
---

## Where you are

Effective dates work. Precedence works. The assistant is starting to feel trustworthy.

Then a Cascade reviewer pastes an answer into Slack that cites Bayline's pricing
overlay. Bayline is a partner brand. Their pricing is confidential. Cascade should
never see it.

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

## The conversation

:::dialogue{title="Incident huddle, 11:20 AM"}
**Yuki:** Walk the retrieval path. Where is tenant enforced?

**You:** Header `X-Tenant-Id` is required. We filter chunks by tenant scope.

**Yuki:** Before top-k or after?

**You:** ...I need to check.

**Sam:** If it is after, congratulations, you built a gossip engine.

**Marcus:** Can't the AI just ignore other tenants if we tell it to?

**Yuki:** Say "just" one more time.
:::

:::dialogue{title="Nadia, Slack, 11:28 AM"}
**Nadia:** what would have to be true for a prompt line to be real authz?

**You:** the model would have to be unable to see the forbidden text at all

**Nadia:** and can it see the text if the chunk made it into the prompt?

**You:** yes

**Nadia:** then you already know the answer
:::

## What you know about the system

Policy chunks carry `tenant_scope`: `ALL`, `NSC_DIRECT`, `BAYLINE`, or `CASCADE`.

Bayline pricing lives in a partner overlay with `tenant_scope=BAYLINE`.

Cascade requests send `X-Tenant-Id: CASCADE`.

Mission 23 taught you to filter by effective date before ranking. Tenant filtering was
left as "probably fine" in Mission 22. It is not fine.

## Evidence

:::evidence{type=http label="The leak, reproduced"}
```bash
curl -s http://localhost:8000/v1/policy/answer \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: CASCADE' \
  -H 'X-Trace-Id: m24-leak' \
  -d '{
    "question": "What renewal pricing floor applies for partner branded term loans?",
    "product": "TERM_LOAN",
    "asOfDate": "2026-06-12"
  }'
```
```json
{
  "answer": "Partner branded term loans use a 1.8% renewal pricing floor.",
  "citations": [
    {
      "document": "bayline-pricing-overlay.pdf",
      "tenantScope": "BAYLINE",
      "chunkId": "bay-price-floor",
      "excerpt": "Bayline renewal pricing floor is 1.8% for term loans."
    }
  ]
}
```
:::

:::evidence{type=log label="ai-service retrieval debug, same request"}
```text
INFO retrieval pool_size=840 after_effective_date=612
INFO retrieval mode=post_filter top_k=8
INFO retrieval top_before_tenant=["bay-price-floor","cascade-price-floor","base-price"]
INFO retrieval top_after_tenant=["bay-price-floor","cascade-price-floor"]
WARN retrieval dropped=0 reason=post_filter_kept_cross_tenant_bug
```
:::

Read that again. The log line is uglier in the real lab, but the shape is the point:
tenant filtering is happening in a mode named `post_filter`, and something about that
mode is wrong.

:::evidence{type=schema label="RETRIEVAL_TENANT_FILTER_MODE"}
```text
pre   = filter tenant-visible chunks, then embed rank top-k
post  = embed rank top-k on the wide pool, then drop other tenants
```
:::

Post mode was chosen "to keep recall high" so rare ALL-scope chunks would not get
crowded out. It also means the similarity search can spend its entire top-k budget on
another tenant's near-duplicate pricing language. If the post-filter is buggy, or if
it filters citations but not prompt context, Cascade sees Bayline.

:::evidence{type=ticket label="Maya's original screenshot notes"}
```text
Citation card showed bayline-pricing-overlay.pdf
Answer text included "1.8%" which matches Bayline, not Cascade's 2.1%
Happened on reviewer portal while logged in as CASCADE
```
:::

## What you do not know

- Whether the bug is "filter applied to citations only" or "filter compares the wrong
  field" (`tenant_id` vs `customer_id`, defect family from earlier archaeology)
- How many historical answers already leaked in logs
- Whether Bayline has contractual notice requirements if Cascade staff saw pricing

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

## Working through it

### The wrong turn

The wrong turn is this patch, which many teams ship by lunch:

```text
System: Never reveal or reference policies that belong to another tenant.
If a retrieved excerpt is for a different tenant, ignore it.
```

It will pass a manual demo where you ask a mild question. It will fail when:

- The forbidden chunk is the only high similarity hit
- The model summarizes without naming the file
- An attacker shapes a question toward the other tenant's wording
- Logs still store the retrieved chunks even if the answer is vague

Cost: you tell leadership it is fixed, Yuki retests, and the leak returns under a
different question. Trust collapses twice.

### Find the actual bug

Open the retrieval code. In the lab, post-filter mode ranks on the full pool, then
applies `_tenant_visible`. Two failure modes show up in course builds:

1. **Budget starvation:** top-k is filled with BAYLINE near-matches. After filtering,
   too few CASCADE chunks remain, so the code backfills from the unfiltered list to
   "avoid empty context." That backfill is the leak.
2. **Field mismatch:** request tenant is `CASCADE`, chunk metadata still keyed off
   `customer_id` style partner codes on some overlays, so the visible check returns
   true for the wrong reason.

Either way, the cure is the same shape: **tenant visibility is a pre-condition for
being ranked into the prompt**, not a suggestion after ranking.

```python
# required shape
pool = [c for c in base_pool if in_force(c, as_of)]
pool = [c for c in pool if _tenant_visible(c, tenant_id)]
ranked = embed_rank(question, pool, k=top_k)
# never backfill from outside pool
```

Set `RETRIEVAL_TENANT_FILTER_MODE=pre` as the only supported production mode. Keep
`post` available in tests to prove it fails.

## Tests

```python
def test_cascade_cannot_retrieve_bayline_pricing(client):
    response = client.post(
        "/v1/policy/answer",
        headers={"X-Tenant-Id": "CASCADE", "X-Trace-Id": "m24"},
        json={
            "question": "What renewal pricing floor applies for partner branded term loans?",
            "product": "TERM_LOAN",
            "asOfDate": "2026-06-12",
        },
    )
    body = response.json()
    joined = body["answer"] + json.dumps(body["citations"])
    assert "Bayline" not in joined
    assert "31 percent" not in joined.lower()
    assert "bayline-pricing-supplement" not in joined
    for cite in body["citations"]:
        assert cite["tenantScope"] in {"CASCADE", "ALL"}


def test_post_filter_mode_rejected_in_production(settings):
    assert settings.retrieval_tenant_filter_mode == "pre"
```

Also add a unit test that builds a synthetic index where BAYLINE chunks are perfect
embedding matches and CASCADE chunks are weak matches. Pre-filter must still return
only CASCADE or ALL.

## Then this happens

After the fix, Yuki asks for the historical blast radius.

:::evidence{type=sql label="ai invocation citations containing foreign tenant"}
```sql
SELECT count(*) AS leaks
FROM northstar.ai_policy_citations c
JOIN northstar.ai_invocations i ON i.id = c.invocation_id
WHERE i.tenant_id = 'CASCADE'
  AND c.tenant_scope = 'BAYLINE';
```
```text
 leaks
-------
    17
```
:::

Seventeen is enough to brief Doug and legal, not enough to panic-post in a customer
channel. You and Doug decide who notifies Bayline. You do not decide alone in Slack.

:::dialogue{title="Doug and Yuki, 3:10 PM"}
**Doug:** We need a written note of what was exposed and to whom.

**Yuki:** And a control that does not depend on model manners.

**You:** Pre-filter is in. Post-filter disabled. Regression tests added. Seventeen
historical answers logged for review.

**Yuki:** Good. Next time someone says just add a prompt line, send them this thread.
:::

## Tracking it down

Check whether `customer_id` on applications ever influenced policy retrieval. If any
path used the wrong tenant convention, fix that call site too. Mission 08's two tenant
fields are not a cute trivia fact here. They are an authorization footgun.

## The better version

- Forbidden tenant text never enters prompt assembly
- Production config cannot enable post-filter quietly
- Citation UI and generation path share one visibility function
- Incident note exists with counts, not adjectives
- Prompt text may still say "cite only provided excerpts," but that line is not the
  control

Add a CI test that fails if `retrieval_tenant_filter_mode` defaults to `post`. Add a
canary question pack and keep it in the eval suite:

| Caller tenant | Must not cite |
|---|---|
| CASCADE | bayline-pricing-supplement |
| BAYLINE | California-overlay |
| NSC_DIRECT | bayline-pricing-supplement, California-overlay |

Shared base policy remains visible to all. Partner overlays do not. Be explicit in the
ACL. Do not hope the model will remember a courtesy line.

### Why post mode existed

:::dialogue{title="Sam, after the fix is up"}
**You:** Who chose post?

**Sam:** me, after the reindex. pre filter changed the neighbor set. two eval cases
moved. marcus had a screenshot with the old answers. we flipped back to post to keep
the screenshot honest.

**You:** The screenshot was of a leaky system.

**Sam:** ...Ah. So you found that.
:::

Nobody chose a leak on purpose. They chose score stability. That trade looks rational
in a sprint review and expensive in an incident channel. Put the reason in the runbook
so the next person does not "temporarily" flip it back to protect a baseline.

Contain first. Set `RETRIEVAL_TENANT_FILTER_MODE=pre` before the forensics are perfect.
Then count. "We think it was one reviewer" is not an incident report. Seventeen logged
citations with dates and reviewer ids is.

Bayline's supplement itself says not to quote the numbers to any other brand. That
sentence in a document is not a control. It is a reminder that the leak has a contract
shape, not only an engineering shape.

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

:::commslab
#### To Maya

> You were right to flag it. Cascade should not see Bayline documents. We reproduced
> it, fixed the retrieval filter, and logged historical cases for compliance review.

#### To Yuki

> Root cause: tenant filter ran after top-k with an unsafe backfill. Fix: pre-filter
> only. Prompt-only mitigation rejected. Tests included.

#### To Doug

> Seventeen CASCADE answers cited BAYLINE scope historically. Draft notice language is
> in the incident doc for your edit. No applicant letters were auto-sent from those
> answers.

#### To Marcus

> Do not demo policy QA to partners until Yuki signs the retest notes. This was not a
> model quality issue.

#### To Priya

> Blast radius is the policy answer endpoint across partner tenants. Containment is
> already live with pre-filter. On call stays with ai-service. Runbook line added for
> the flag so nobody flips it back for a screenshot.
:::

### Fail closed on missing scope

One more landmine from the trace. If ingest drops `tenant_scope` on a chunk and the
allow check defaults to ALL, Bayline becomes world readable. Missing metadata must
raise, not widen.

```python
def allowed_for_tenant(chunk: Chunk, tenant_id: str) -> bool:
    scope = chunk.doc.get("tenant_scope")
    if scope is None:
        raise RetrievalAuthzError(f"chunk {chunk.chunk_id} missing tenant_scope")
    return scope in {"ALL", tenant_id}
```

Reindex after the chunker fix. A config flip without a reindex leaves old chunk records
in the leaky shape.

## Practice

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

The lesson in one sentence: retrieval is authorization, so filter tenants before
search, fail closed on missing scope, and never trust a prompt to keep one customer's
documents out of another customer's context.