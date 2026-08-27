---
id: M28
slug: workflow-or-agent
title: Workflow or Agent
subtitle: "You built an agent. Then you measured it. Ninety four percent of the time it walked the same path."
phase: 6
order: 28
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Instrument an agent loop and recover the actual path distribution
  - Decide when a state machine beats an agent on latency, cost, and on-call clarity
  - Rewrite the dominant path as an explicit workflow without losing the hard cases
  - Answer Janet's on-call question with a design she can page
concepts: [agent vs workflow, path instrumentation, control flow, on-call ownership]
competencies: [architecture, agent-design, production-reliability]
prereqs: [M27]
---

## Where you are

Write tools no longer execute from chat. The remaining assistant still plans tool calls
for every question. Marcus calls it an agent in every deck. You have started to believe
him.

It is Monday, July 6. Janet Osei puts thirty minutes on your calendar titled "on-call
for the agent." She does not put a question mark.

## The request

:::evidence{type=slack label="DM from Janet Osei, Monday 8:40 AM"}
```text
Janet:  who is on call for that

You:    for the assistant?

Janet:  for the thing that decides which tools to call and when it stops.
        if it loops at 2am, who gets the page, and what do they read
```
:::

## The conversation

:::dialogue{title="Janet's office, Monday 10:00 AM"}
**Janet:** Draw the control flow.

**You:** Model picks tools, we run them, model answers or picks again, until it stops.

**Janet:** So the next step lives in the model.

**You:** For the flexible cases, yes.

**Janet:** Show me the flexible cases.

*Silence.*

**Janet:** You do not have a list. You have a feeling.

**You:** I can get a list.

**Janet:** Get a list. If ninety percent of turns follow one path, that path should be
code I can read at 2 a.m. The model can keep the leftover.
:::

:::dialogue{title="Nadia, after you complain"}
**Nadia:** what would have to be true for the agent to be the right default

**You:** The next step really is unknown most of the time.

**Nadia:** so measure how unknown it is
:::

## What you know about the system

The chat assistant for underwriting questions still uses the five-tool set from
Mission 25, plus dry-run proposals for writes. Every question enters the same loop.

You add path logging for one week without changing behavior.

```python
# lab/ai-service/ai_service/tools/path_log.py
def fingerprint(steps: list[dict]) -> str:
    return ">".join(
        s["tool"] if s["type"] == "tool_call" else s["type"]
        for s in steps
    )
```

## Evidence

:::evidence{type=metrics label="Assistant path fingerprints, 1,200 pilot questions"}
```text
path                                                         count   pct
----------------------------------------------------------   -----   ----
get_application>get_bank_transactions>search_policy>answer     912   76.0
get_application>get_bank_transactions>answer                   144   12.0
get_documents>answer                                            72    6.0
get_application>search_policy>answer                            48    4.0
other (12 distinct paths)                                       24    2.0

dominant family (first two rows + small variants):                    94%
median latency, dominant path:                                        6.9s
median latency, other:                                               11.4s
median cost, dominant path:                                         $0.021
median cost, other:                                                 $0.048
```
:::

:::evidence{type=log label="Sample dominant path, application 45220"}
```text
step1 tool=get_application           args={"applicationId":45220}     38ms
step2 tool=get_bank_transactions     args={"applicationId":45220,"months":3} 81ms
step3 tool=search_policy             args={"query":"DSCR floor TERM_LOAN"} 120ms
step4 answer                         tokens_out=286
total_latency_ms=7044 cost_usd=0.020
```
:::

:::evidence{type=slack label="Marcus, reading the same table"}
```text
Marcus:  94% means the agent learned the job. that is success

You:     94% means we should stop asking the model what to do next on that path

Marcus:  can't the AI just keep deciding? it is already deciding correctly

Janet:   correctly and accountably are different words
```
:::

## What you do not know

- Whether the 6 percent document path is stable enough to hard-code.
- How reviewers will react if the UI feels less "agentic."
- Whether Dale's board story depends on the word agent.
- What breaks if you leave the agent as a fallback and it slowly eats the workflow again.

## Your task

:::task{time="140 min"}
1. Reproduce the path table from one week of `ai_invocations` / path logs in the lab
   (seed includes the 1,200 question sample).
2. Implement `UnderwritingQuestionWorkflow` for the dominant path as plain code: fetch
   application, fetch transactions, search policy, then one model call to draft the
   answer with those results already in hand.
3. Keep an agent fallback only for fingerprints outside the dominant family, behind a
   flag.
4. Write the on-call runbook section Janet asked for: what pages, what to read, how to
   disable the agent fallback.
5. Document the wrong turn: keeping the agent because the dashboard said 94 percent
   success.
:::

## Stop and think

:::stopandthink
1. If the next step is known, what does the model add on steps 1 to 3 besides latency?
2. What does Janet need at 2 a.m. that a trace of "model chose get_application" does not
   give her?
3. Where should the 6 percent document questions go on day one of the rewrite?

Write your answers before you scroll. Two minutes.
:::

## Working through it

### Build the path table yourself

Do not take Marcus's slide. Query the logs.

```sql
SELECT path_fingerprint, count(*) AS n,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct,
       round(avg(latency_ms)) AS avg_ms,
       round(avg(cost_usd)::numeric, 3) AS avg_cost
FROM ai_tool_paths
WHERE created_at >= now() - interval '7 days'
GROUP BY 1
ORDER BY n DESC;
```

Print it. Tape it next to your monitor. Architecture arguments without this table are
cosplay.

:::dialogue{title="Renee, looking at the table"}
**Renee:** That first row is every question I ask before coffee.

**You:** Application, transactions, policy, answer.

**Renee:** I do not need the model to invent that order. I need it to not lie about the
revenue field when it gets there.

**You:** The workflow will call the same tools you trust. The model only writes the
paragraph at the end.
:::

### The wrong turn: celebrate the 94 percent

Marcus wants a slide: "Agent selects correct tools 94 percent of the time."

That slide is true and points at the wrong design. High path concentration means the
control flow is known. Keeping an agent there buys you nondeterminism, harder pages, and
extra model round trips in exchange for flexibility you are not using.

You almost ship a tuning pass on tool descriptions instead of a workflow. That would
raise the 94 toward 96 and leave Janet's question unanswered.

:::dialogue{title="Nadia, after you describe the tuning plan"}
**Nadia:** what would have to be true for better descriptions to be the main fix

**You:** That the next step is still unknown and we are only mis-labeling tools.

**Nadia:** is the next step unknown on the top row

**You:** No. It is known.

**Nadia:** then stop tuning the menu and cook the meal the same way each time
:::

### Rewrite the dominant path

```python
# lab/ai-service/ai_service/workflows/underwriting_question.py
from ai_service.tools.registry import (
    GET_APPLICATION,
    GET_BANK_TRANSACTIONS,
    SEARCH_POLICY,
)
from ai_service.providers import get_provider


def run_underwriting_question(application_id: int, question: str, tenant_id: str) -> dict:
    app = GET_APPLICATION.handler(application_id=application_id, tenant_id=tenant_id)
    txns = GET_BANK_TRANSACTIONS.handler(
        application_id=application_id, months=3, tenant_id=tenant_id
    )
    policy = SEARCH_POLICY.handler(
        query=question, product=app.get("product"), tenant_id=tenant_id
    )

    provider = get_provider()
    completion = provider.complete(
        system=(
            "Answer the underwriter using only the JSON facts provided. "
            "If a fact is missing, say what is missing. Do not call tools."
        ),
        user={
            "question": question,
            "application": app,
            "transactions": txns,
            "policyPassages": policy,
        },
    )
    return {
        "answer": completion.text,
        "path": "workflow:app>txns>policy>answer",
        "usage": completion.usage,
        "mode": "workflow",
    }
```

Notice what disappeared: three model round trips that only existed to choose the next
fetch. The fetches are code. The prose is the model.

Router:

```python
def answer_question(req: QuestionRequest) -> dict:
    if req.force_agent or not feature_enabled("UW_QUESTION_WORKFLOW", req.tenant_id):
        return run_agent_loop(req)

    if looks_like_document_question(req.question):
        # Still workflow-shaped: documents then answer. Not an open tool loop.
        return run_document_question(req)

    if looks_like_open_ended(req.question):
        return run_agent_loop(req)

    return run_underwriting_question(req.application_id, req.question, req.tenant_id)
```

After the change, on the same 1,200 questions:

| Measure | Agent everywhere | Workflow + agent fallback |
|---|---|---|
| Dominant path latency p50 | 6.9s | 4.1s |
| Cost per dominant question | $0.021 | $0.011 |
| Tool selection errors on dominant path | 3% | 0% (no selection) |
| Questions using agent fallback | 100% | 2.1% |
| On-call: next step visible in code | no | yes for 98% |

### On-call card

Janet accepts this card only after you make Tomás read it cold and disable the fallback
without asking you.

```text
SERVICE: ai-service underwriting assistant
SYMPTOM: loop, high latency, weird tool choices
1. Check mode tag on the response or ai_invocations.route
2. If mode=agent and volume spike: set UW_QUESTION_WORKFLOW_AGENT_FALLBACK=false
3. Dominant traffic should remain on workflow mode
4. Page underwriting-service only if get_application / transactions fail
5. Do not "fix" by adding tools mid-incident
```

:::dialogue{title="Tomás after the cold read"}
**Tomás:** I can kill the fallback. I cannot read the model's mind when the workflow
path breaks.

**You:** When the workflow path breaks, the stack trace points at a function with a
name. That is the whole point.

**Tomás:** Okay. Put my name on the secondary for the worker, not for the planner.
:::
## Tests

```python
def test_dominant_question_uses_workflow(client):
    resp = client.post(
        "/v1/tools/invoke",
        headers={"X-Tenant-Id": "NSC_DIRECT"},
        json={
            "question": "Does 45220 clear the DSCR floor?",
            "context": {"applicationId": 45220, "actingUserId": "renee.blackwell"},
        },
    )
    body = resp.json()
    assert body["mode"] == "workflow"
    assert body["path"].startswith("workflow:")


def test_flag_off_falls_back_to_agent(client, monkeypatch):
    monkeypatch.setenv("UW_QUESTION_WORKFLOW", "false")
    resp = client.post(
        "/v1/tools/invoke",
        headers={"X-Tenant-Id": "NSC_DIRECT"},
        json={
            "question": "Does 45220 clear the DSCR floor?",
            "context": {"applicationId": 45220, "actingUserId": "renee.blackwell"},
        },
    )
    assert resp.json()["mode"] == "agent"
```

## Then this happens

Jordan asks whether he has to take the word "agent" out of the Q3 update.

:::dialogue{title="Jordan, hallway"}
**Jordan:** I may have set expectations. Dale liked the agent story.

**You:** Tell him the system answers underwriting questions in production. The part that
used to guess the next step on every call is now a workflow for almost all volume. The
agent remains for the weird two percent.

**Jordan:** Is that directionally... I mean, will Dale hear that as a downgrade?

**You:** He will hear four seconds instead of seven, and Janet taking the page. Lead
with that.
:::

:::dialogue{title="Dale, five minutes at the end of the weekly"}
**Dale:** So we still have an AI underwriter?

**You:** You have an assistant that answers underwriting questions on real files. Most
of the path is ordinary software now. That is why engineering will support it overnight.

**Dale:** Is that directionally correct for the board?

**You:** Use "assistant in production on NSC_DIRECT questions" and the latency number.
Skip the word agent unless you are talking about the two percent fallback.
:::

## Tracking it down

You sample the 2.1 percent fallback. Half are compound questions ("compare this file to
the applicant's last decline and the California overlay"). Those stay on the agent until
you have a real multi-application workflow. The other half are misrouted document
questions. You tighten the classifier and the fallback rate drops under 2 percent.

:::evidence{type=metrics label="Fallback audit, 40 sampled questions"}
```text
true open-ended (keep agent) .................. 19
misrouted document questions .................. 14
should have been dominant workflow ............  5
unclear / needs product decision ..............  2
```
:::

The five that should have been workflow are classifier bugs, not arguments for keeping
the agent wide open. Fix the classifier. Do not reopen the tool loop for them.

## The better version

Decision rule you write on the runbook card:

1. Log paths for a representative week before arguing architecture.
2. If one family exceeds roughly 80 percent, implement that family as a workflow.
3. Keep an agent only where the next step is genuinely unknown, behind a flag.
4. On-call must be able to disable the agent without disabling the workflow.

Marcus still wants to demo "the agent thinking." You give him a staged fallback
question for demos and keep production traffic on the workflow. Demo theater and
production control flow are allowed to differ. Lying about which one reviewers use is
not.

:::judgment
**An agent is a control flow you cannot read. Use it when you cannot write the flow.
When you can, write it.**

The interesting demo and the operable system are different shapes. Measuring path
concentration is how you tell which one you have. Ninety four percent one path is not a
trophy for the agent. It is a specification for a state machine that was hiding inside
tool traces.

Janet's question is the real acceptance test. If a senior engineer cannot say who is on
call and what they will read, you do not have a production design yet. You have a loop.
:::
:::commslab
#### To Janet

> Dominant path is now a workflow in `underwriting_question.py`: application,
> transactions, policy, one completion. Agent fallback is flagged
> `UW_QUESTION_WORKFLOW_AGENT_FALLBACK`, default on for the 2 percent tail, kill switch
> documented in the runbook. Page goes to ai-service on-call; your team owns the
> underlying read APIs the same as today.

#### To Marcus

> We kept the product capability. We changed the control flow for 98 percent of
> questions because the agent took the same three steps almost every time. Latency and
> cost dropped. Please stop calling the whole feature "the agent" in reviewer training.
> Call it the assistant. The agent is the fallback.

#### To Dale

> The assistant is faster and cheaper on the questions reviewers actually ask. We
> reserved the open-ended planner for the rare cases. That is the production shape, and
> it is the one engineering can support overnight.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital scheduling "agent" books follow-up appointments. After two weeks of path
logs:

```
findPatient>findOpenSlots>bookSlot>answer     89%
findPatient>findOpenSlots>answer (no book)     7%
other                                          4%
```

The CIO loves the agent narrative. Nursing on-call hates 2 a.m. loops.

**Your task**

1. What do you rewrite as a workflow first?
2. What stays on an agent, if anything?
3. Write Janet's equivalent question for this domain.
4. Draft the three sentence CIO update that does not sound like a retreat.

---

**Notes, after you have written yours**

Rewrite `findPatient>findOpenSlots>bookSlot` as a workflow with an explicit confirm
before `bookSlot`. Keep an agent or human handoff for the 4 percent (multi-patient,
interpreter needed, outside referral rules).

On-call question: who pages when booking loops, and what code path do they read?

CIO update: lead with reliability and time-to-book, name that the common path is now
deterministic, and keep "flexible planner" language only for the exception path.
:::
