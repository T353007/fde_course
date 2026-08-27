---
id: M25
slug: give-it-hands
title: Give It Hands
subtitle: "The moment your software stops answering questions and starts doing things."
phase: 6
order: 25
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Explain what a tool call actually is, step by step, at the wire level
  - Build a read-only tool loop with real schemas, budgets, and termination conditions
  - Measure how the number of tools changes selection accuracy, cost, and latency
  - Decide which capabilities deserve to be a tool at all
concepts: [tool calling, function schemas, the agent loop, termination conditions, token cost]
competencies: [agent-design, coding, ai-fundamentals]
prereqs: [M24]
---

## Where you are

Phase 5 is done. The policy assistant answers questions about the credit policy with
citations, filtered by tenant and by effective date. It works. Renee uses it about
twice a day.

It is Monday, June 8. Everything your system has done so far has one property in
common: it reads text and produces text. A person reads the output and decides what to
do. That property is about to go away, and it is the single largest change in risk this
project will ever make.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:52 AM"}
```text
Renee:   I asked it whether application 44219 clears the DSCR floor and it
         gave me a paragraph about what DSCR is

You:     it doesn't have the application. it only has the policy documents

Renee:   Then what is it for

Renee:   Sorry, that came out wrong. I mean it. What is it for if I still
         have to open the app in the portal, copy the revenue number, and
         come back here

Marcus:  can't the AI just look it up? 🙂

Sam:     that's an actual question though
```
:::

Marcus is right for once, and Sam noticed. Renee's complaint is not that the answers are
bad. The answers are fine. The complaint is that the assistant does not have access to
the thing she is asking about, so she is the integration layer.

## The conversation

:::dialogue{title="Renee's desk, Monday 10:40 AM"}
**You:** Walk me through the last question you asked it.

**Renee:** Forty four two one nine. Term loan, two fifty. I wanted to know if the
coverage clears with the numbers we have.

**You:** What did you have to do?

**Renee:** Portal, application tab, copy the revenue. Portal, documents tab, check the
statement dates because the revenue field lies if the statements are stale. Then back
to the chat and I type all of it in.

**You:** How long?

**Renee:** Four minutes? It is not the four minutes. It is that I have to be right
about which numbers to paste in, and if I am already right about that, I did not need
the assistant.

*She turns her monitor slightly so you can see it.*

**Renee:** We don't use that number, by the way. The revenue field on the application
tab. That is the old calculation.
:::

That last line is the mission. If you give the assistant the ability to fetch data, it
will fetch the wrong field forever, silently, at machine speed. Renee catches it because
she has fourteen years of knowing which field is a lie.

:::dialogue{title="Slack DM with Nadia Ferrante, Monday 2:15 PM"}
**You:** Adding tool calling this week. Read-only, three tools.

**Nadia:** ok. what does "the model calls the API" mean to you

**You:** The model hits our endpoint and gets data back.

**Nadia:** the model cannot hit anything. it has no socket.

**You:** Fine. It requests a call and we make it.

**Nadia:** right. and whose credentials

**You:** ...Ours.

**Nadia:** so when it goes wrong, who made the call
:::

## What a tool call actually is

Here is the whole mechanism. There is less to it than the word "agent" suggests.

**One.** You send the model a normal prompt, plus a list of tool definitions. A tool
definition is a name, a description in English, and a JSON Schema for its arguments.
The tool definitions are just more text in the prompt. You pay tokens for them on every
single call.

**Two.** The model generates output. Sometimes that output is an answer. Sometimes it is
a structured request that says "call `get_application` with `{"applicationId": 44219}`."
The provider parses that into an object for you and sets `finish_reason` to something
like `tool_calls`.

**Three.** Your code receives that request. Your code decides whether to run it. Your
code runs it, with your service credentials, from your network, inside your VPC. The
model is not involved in this step at all.

**Four.** You append the result to the conversation as a new message and call the model
again. The model now sees the question, its own request, and the result.

**Five.** Repeat until the model returns an answer instead of a request, or until you
stop it.

That is it. There is no connection between the model and your systems. There is a
proposal and there is your code accepting the proposal.

"The model called the API" is a dangerous sentence for one reason. It puts the
responsibility somewhere it is not. Your service account fetched that credit report.
Your audit log has your service name on it. If the argument was wrong, your code passed
the wrong argument. The model produced a suggestion, in text, the same way it produces
everything else, and it can be wrong in exactly the same ways.

Say it the accurate way and the design decisions fall out of it: **the model proposes,
your code disposes.**

## What you know about the system

`ai-service` already has the endpoint. It is in `LAB_SPEC.md` section 7 and it has been
returning `501 Not Implemented` since Phase 3. You are implementing it now.

:::evidence{type=http label="The contract you are building against"}
```text
POST /v1/tools/invoke
X-Tenant-Id: NSC_DIRECT
X-Trace-Id: 7f21a0c4
Content-Type: application/json

{
  "question": "Does application 44219 clear the DSCR floor?",
  "tools": ["get_application", "get_bank_transactions", "search_policy"],
  "context": {
    "applicationId": 44219,
    "actingUserId": "renee.blackwell"
  },
  "maxSteps": 6,
  "budget": { "maxPromptTokens": 24000, "maxCostUsd": 0.10 }
}
```

```text
200 OK

{
  "answer": "...",
  "citations": [...],
  "steps": [
    {"n": 1, "type": "tool_call", "tool": "get_application",
     "arguments": {"applicationId": 44219}, "latencyMs": 41},
    {"n": 2, "type": "tool_call", "tool": "get_bank_transactions",
     "arguments": {"applicationId": 44219, "months": 3}, "latencyMs": 88},
    {"n": 3, "type": "answer"}
  ],
  "usage": {"promptTokens": 9140, "completionTokens": 388,
            "costUsd": 0.019, "latencyMs": 6210},
  "finishReason": "answered"
}
```
:::

Two things in that request matter more than they look.

`tools` is a list of names, chosen by the caller, not a flag that turns on everything.
And `context.applicationId` is passed in by the portal. The model does not get to decide
which tenant it is operating in. Tenant comes from the header, the same way it has since
Mission 24, and it is never a model-supplied argument.

## The code

Start with the tool definition type. A tool is four things and one of them is a lie
detector.

```python
# lab/ai-service/ai_service/tools/spec.py
from dataclasses import dataclass
from typing import Any, Callable, Literal

Effect = Literal["read", "write"]


@dataclass(frozen=True)
class ToolSpec:
    """One capability the model may propose using.

    `effect` is not used yet. Read tools and write tools get different
    rules in Mission 27, and the field exists now so nothing has to be
    retrofitted later.
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema, draft 2020-12
    effect: Effect
    handler: Callable[..., dict[str, Any]]

    def to_wire(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
```

Now three read tools. Notice what the handlers do not accept.

```python
# lab/ai-service/ai_service/tools/registry.py
from ai_service.clients import application_service, underwriting_service
from ai_service.retrieval import policy_index
from ai_service.tools.spec import ToolSpec


def _get_application(*, application_id: int, tenant_id: str) -> dict:
    app = application_service.get_application(application_id, tenant_id=tenant_id)
    return {
        "applicationId": app["applicationId"],
        "legalName": app["applicant"]["legalName"],
        "product": app["product"],
        "amountRequested": app["amountRequested"],
        "status": app["status"],
        "submittedAt": app["submittedAt"],
    }


def _get_bank_transactions(*, application_id: int, months: int, tenant_id: str) -> dict:
    txns = underwriting_service.transactions(
        application_id, months=months, tenant_id=tenant_id
    )
    return {
        "applicationId": application_id,
        "monthsCovered": months,
        "transactionCount": len(txns),
        "transactions": [
            {
                "date": t["postedDate"],
                "description": t["description"],
                "amount": t["amount"],
                "category": t.get("category"),
                "categorySource": t.get("categorySource"),
            }
            for t in txns
        ],
    }


def _search_policy(*, query: str, product: str | None, tenant_id: str) -> dict:
    hits = policy_index.search(
        query, tenant_id=tenant_id, product=product, effective_on="today", k=4
    )
    return {
        "results": [
            {
                "documentId": h.document_id,
                "section": h.section,
                "effectiveFrom": h.effective_from,
                "text": h.text,
            }
            for h in hits
        ]
    }


GET_APPLICATION = ToolSpec(
    name="get_application",
    description=(
        "Fetch the loan application record: product, amount requested, "
        "current status, and the legal name of the business. "
        "Use this when the question names an application. "
        "This does NOT return revenue or any calculated underwriting figure."
    ),
    parameters={
        "type": "object",
        "properties": {
            "applicationId": {
                "type": "integer",
                "description": "Numeric application id, for example 44219.",
            }
        },
        "required": ["applicationId"],
        "additionalProperties": False,
    },
    effect="read",
    handler=_get_application,
)

GET_BANK_TRANSACTIONS = ToolSpec(
    name="get_bank_transactions",
    description=(
        "Fetch parsed bank transactions for an application, newest first. "
        "Use this whenever the question involves revenue, deposits, cash "
        "flow, or coverage. Revenue must be computed from these lines. "
        "Do not use the revenue field on the application record."
    ),
    parameters={
        "type": "object",
        "properties": {
            "applicationId": {"type": "integer"},
            "months": {
                "type": "integer",
                "minimum": 1,
                "maximum": 12,
                "description": "How many months back to return. Default 3.",
            },
        },
        "required": ["applicationId", "months"],
        "additionalProperties": False,
    },
    effect="read",
    handler=_get_bank_transactions,
)

SEARCH_POLICY = ToolSpec(
    name="search_policy",
    description=(
        "Search Northstar credit policy for the rule that applies today. "
        "Returns passages with document id, section, and effective date. "
        "Use this for thresholds, floors, and eligibility rules. "
        "Do not use this to look up facts about a specific applicant."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "product": {
                "type": "string",
                "enum": ["TERM_LOAN", "LOC", "SBA_7A", "EQUIPMENT"],
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    effect="read",
    handler=_search_policy,
)

REGISTRY = {t.name: t for t in (GET_APPLICATION, GET_BANK_TRANSACTIONS, SEARCH_POLICY)}
```

Read the description on `get_application` again. The last sentence is there because of
what Renee said on Monday. The description is prompt text. It is the only place you get
to tell the model which of your fields is a lie, and it ships with the same review
process as any other prompt.

Now the loop.

```python
# lab/ai-service/ai_service/tools/runner.py
import json
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator, ValidationError

from ai_service.providers import get_provider
from ai_service.providers.base import CompletionRequest
from ai_service.tools.registry import REGISTRY

SYSTEM = (
    "You answer underwriting questions for Northstar Capital reviewers.\n"
    "Use the tools to get facts. Never state a number you did not read "
    "from a tool result. If a tool result does not contain what you need, "
    "say what is missing and stop."
)


@dataclass
class Budget:
    max_prompt_tokens: int = 24_000
    max_cost_usd: float = 0.10
    spent_prompt_tokens: int = 0
    spent_cost_usd: float = 0.0

    def exceeded(self) -> str | None:
        if self.spent_prompt_tokens > self.max_prompt_tokens:
            return "prompt_token_budget"
        if self.spent_cost_usd > self.max_cost_usd:
            return "cost_budget"
        return None


@dataclass
class Result:
    answer: str | None
    steps: list[dict] = field(default_factory=list)
    finish_reason: str = "answered"
    usage: dict = field(default_factory=dict)


def run(question: str, tool_names: list[str], ctx: dict,
        max_steps: int = 6, budget: Budget | None = None) -> Result:
    budget = budget or Budget()
    tools = [REGISTRY[n] for n in tool_names]
    provider = get_provider()

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    result = Result(answer=None)
    seen_calls: set[str] = set()

    for n in range(1, max_steps + 1):
        resp = provider.complete(
            CompletionRequest(messages=messages, tools=[t.to_wire() for t in tools])
        )
        budget.spent_prompt_tokens += resp.prompt_tokens
        budget.spent_cost_usd += resp.cost_usd

        if resp.finish_reason != "tool_calls":
            result.answer = resp.text
            result.steps.append({"n": n, "type": "answer"})
            break

        messages.append(resp.raw_assistant_message)

        for call in resp.tool_calls:
            payload, status = _execute(call, ctx, seen_calls)
            result.steps.append(
                {"n": n, "type": "tool_call", "tool": call.name,
                 "arguments": call.arguments, "status": status}
            )
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(payload),
            })

        stop = budget.exceeded()
        if stop:
            result.finish_reason = stop
            result.answer = None
            break
    else:
        result.finish_reason = "max_steps"

    result.usage = {
        "promptTokens": budget.spent_prompt_tokens,
        "costUsd": round(budget.spent_cost_usd, 4),
    }
    return result


def _execute(call, ctx: dict, seen_calls: set[str]) -> tuple[dict, str]:
    spec = REGISTRY.get(call.name)
    if spec is None:
        return {"error": "unknown_tool", "tool": call.name}, "unknown_tool"

    try:
        Draft202012Validator(spec.parameters).validate(call.arguments)
    except ValidationError as e:
        return {"error": "invalid_arguments", "detail": e.message}, "invalid_arguments"

    fingerprint = call.name + json.dumps(call.arguments, sort_keys=True)
    if fingerprint in seen_calls:
        return (
            {"error": "duplicate_call",
             "detail": "You already called this with these arguments. "
                       "Use the earlier result or answer with what you have."},
            "duplicate",
        )
    seen_calls.add(fingerprint)

    args = {_snake(k): v for k, v in call.arguments.items()}
    args["tenant_id"] = ctx["tenantId"]
    return spec.handler(**args), "ok"


def _snake(key: str) -> str:
    return "".join("_" + c.lower() if c.isupper() else c for c in key)
```

Five defenses live in about forty lines. Unknown tool names return an error instead of
raising. Arguments are validated against the schema before anything runs, because the
model will eventually send `{"applicationId": "44219"}` as a string. Repeated identical
calls are refused with a message the model can act on. Tenant is injected by you, after
validation, so a model-supplied `tenantId` cannot override it. And the loop has a hard
step ceiling with a `for/else` that records why it stopped.

## Evidence

Run it against the stub provider and read the transcript.

:::evidence{type=trace label="POST /v1/tools/invoke, trace 7f21a0c4, LLM_PROVIDER=stub"}
```text
step 1  model    finish_reason=tool_calls
                 get_application {"applicationId": 44219}
        tool     ok  41ms  {"product":"TERM_LOAN","amountRequested":250000.00,...}

step 2  model    finish_reason=tool_calls   prompt_tokens=2884
                 get_bank_transactions {"applicationId": 44219, "months": 3}
        tool     ok  88ms  {"transactionCount": 61, ...}

step 3  model    finish_reason=tool_calls   prompt_tokens=6510
                 search_policy {"query":"debt service coverage ratio floor",
                                "product":"TERM_LOAN"}
        tool     ok  120ms {"results":[{"documentId":"credit-policy-2025.pdf",
                            "section":"4.2","effectiveFrom":"2025-01-01",...}]}

step 4  model    finish_reason=stop         prompt_tokens=9140
                 answer, 388 completion tokens

total   4 model calls, 3 tool calls, 6.21s, 9,140 prompt tokens
```
:::

Look at the prompt token column. 2,884 then 6,510 then 9,140. Every step replays the
entire conversation, including all three tool schemas and every tool result so far. A
three-step loop is four model calls and roughly three times the tokens of a single call,
not one and a bit.

That is the cost model of the loop, and it is the number people get wrong when they
estimate. Latency behaves the same way. Four sequential model round trips at 1.4 to 1.9
seconds each is the floor, before your tools do any work.

## What you do not know

- Does the model handle a tool that returns an empty result, or does it invent one?
- What happens when two tools could plausibly answer the same question?
- What does the loop do when a tool times out?
- How many tools is too many? Nobody has told you a number and nobody knows one.
- Does the answer stay correct when the transaction list is 240 lines instead of 61?

:::task{time="120 min"}
Implement `POST /v1/tools/invoke` in `ai-service` with exactly the three read tools
above. It has to work with `LLM_PROVIDER=stub` and with a real provider.

Then produce a measurement, not a demo:

1. Write 30 reviewer questions in `data/golden/tool-routing-v1.jsonl`. Each case has
   the question and the list of tools a competent analyst would call, in order.
2. Run all 30. Record for each: tools chosen, steps taken, prompt tokens, latency, and
   whether the final answer is correct.
3. Report four numbers. Tool selection accuracy (did it call the right tools),
   answer accuracy, median steps, and median prompt tokens.
4. Write down every case where the tools were right and the answer was still wrong.
   That set is more interesting than the accuracy number.

Save the report as `customers/northstar/tool-baseline.md`.
:::

:::stopandthink
Before you read any further:

1. Renee said the revenue field on the application record is the old calculation. You
   put that warning in a tool description. What are the ways that fails?
2. Your loop has `maxSteps=6`. What actually happens on step 7, from the reviewer's
   point of view, and is that acceptable?
3. Marcus is going to ask for more tools. Write down, right now, how many tools you
   think a model can choose between reliably. Commit to a number.
4. Every tool here is read-only. Name three things that could still go badly wrong.

Five minutes, in writing. Question 3 is the one this mission is about.
:::

## Working through it

### Tests, before anything else

The loop is the part that will bite you, so test the loop rather than the model.

```python
# lab/ai-service/tests/test_tool_runner.py
import pytest

from ai_service.tools import runner
from ai_service.tools.runner import Budget
from tests.fakes import FakeProvider, call

CTX = {"tenantId": "NSC_DIRECT", "actingUserId": "renee.blackwell"}


def test_happy_path_two_tools(monkeypatch):
    provider = FakeProvider([
        [call("get_application", {"applicationId": 44219})],
        [call("get_bank_transactions", {"applicationId": 44219, "months": 3})],
        "Average operating revenue is 147,400 per month.",
    ])
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("does 44219 clear DSCR", ["get_application",
                                             "get_bank_transactions"], CTX)

    assert r.finish_reason == "answered"
    assert [s["tool"] for s in r.steps if s["type"] == "tool_call"] == [
        "get_application", "get_bank_transactions"]


def test_invalid_arguments_do_not_reach_the_handler(monkeypatch):
    provider = FakeProvider([
        [call("get_application", {"applicationId": "44219"})],  # string, not int
        "I could not read that application id.",
    ])
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("q", ["get_application"], CTX)

    assert r.steps[0]["status"] == "invalid_arguments"


def test_model_cannot_override_tenant(monkeypatch):
    provider = FakeProvider([
        [call("get_application", {"applicationId": 44219, "tenantId": "BAYLINE"})],
        "done",
    ])
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("q", ["get_application"], CTX)

    # additionalProperties is false, so the extra key is rejected outright.
    assert r.steps[0]["status"] == "invalid_arguments"


def test_repeated_identical_call_is_refused(monkeypatch):
    same = [call("get_application", {"applicationId": 44219})]
    provider = FakeProvider([same, same, "ok"])
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("q", ["get_application"], CTX)

    assert [s["status"] for s in r.steps if s["type"] == "tool_call"] == [
        "ok", "duplicate"]


def test_step_ceiling_stops_the_loop(monkeypatch):
    forever = [call("get_application", {"applicationId": 44219})]
    provider = FakeProvider([forever] * 20)
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("q", ["get_application"], CTX, max_steps=4)

    assert r.finish_reason == "max_steps"
    assert r.answer is None


def test_budget_stops_the_loop(monkeypatch):
    provider = FakeProvider([[call("get_application", {"applicationId": 44219})]] * 10,
                            prompt_tokens=9_000)
    monkeypatch.setattr(runner, "get_provider", lambda: provider)

    r = runner.run("q", ["get_application"], CTX,
                   budget=Budget(max_prompt_tokens=10_000))

    assert r.finish_reason == "prompt_token_budget"
```

The third test is the one to keep. Tenant isolation was a real bug in Mission 24, and a
tool argument is a brand new way to reintroduce it.

### The baseline

Thirty questions, three tools, stub provider.

| Measure | Result |
|---|---|
| Tool selection accuracy | 93% (28 of 30) |
| Answer accuracy | 87% (26 of 30) |
| Median steps | 3 |
| Median prompt tokens | 8,900 |
| p50 latency | 6.2s |
| Cost per question, hosted track | $0.019 |

The four wrong answers are more useful than the 87 percent. Three of them are the same
failure: the transaction list came back with `category: null`, and the model classified
the lines itself instead of saying it could not. One of them is the Fastcapital loan
counted as revenue, which is Mission 20 arriving again with a new coat on.

## Then this happens

You demo it on Wednesday. It goes well, which is the problem.

:::evidence{type=slack label="#northstar-ai, Wednesday 3:12 PM"}
```text
Marcus:  this is great. can it also pull the credit report

Marcus:  and the fraud score. and the doc list. Renee asks about missing
         docs constantly

Hank:    if it can see the queue that would save my team real time

Marcus:  @you how hard is adding a tool

You:     about an hour each

Marcus:  amazing 🚀
```
:::

An hour each is true. You add eleven more over Thursday and Friday.

```text
get_application            get_bank_transactions       search_policy
get_credit_report          get_fraud_score             get_documents
get_missing_documents      get_application_events      get_decision_history
get_applicant              get_related_applications    get_queue_position
get_tenant_policy_overlay  get_ocr_confidence
```

Fourteen tools. Every one is read-only, tested, and correct. You rerun the same 30
questions on Monday morning.

| Measure | 3 tools | 14 tools |
|---|---|---|
| Tool selection accuracy | 93% | 61% |
| Answer accuracy | 87% | 64% |
| Median steps | 3 | 5 |
| Median prompt tokens | 8,900 | 21,400 |
| p50 latency | 6.2s | 14.9s |
| Cost per question, hosted track | $0.019 | $0.061 |

Nothing broke. Every tool works. The system got worse at almost everything.

## Tracking it down

Pull the tool choices for the eleven newly failing cases and put them next to what a
person would have called.

:::evidence{type=metrics label="Tool routing errors, 14-tool run, 30 cases"}
```text
question                                    expected              actual
-----------------------------------------   -------------------   -------------------
"is 44219's revenue enough for 250k"        get_bank_transactions get_application
                                                                  get_credit_report
"what documents are we still waiting on"    get_missing_documents get_documents
                                                                  get_application_events
"has this applicant applied before"         get_related_apps      get_applicant
                                                                  get_decision_history
                                                                  get_related_apps
"what is the DSCR floor for SBA"            search_policy         get_tenant_overlay
                                                                  search_policy
"why is the revenue number off"             get_bank_transactions get_ocr_confidence
                                                                  get_fraud_score
                                                                  get_bank_transactions
```
:::

Three separate problems are hiding in that table.

**Overlapping descriptions.** `get_documents` returns every document. `get_missing_documents`
returns the ones not yet received. Both descriptions start with "Fetch documents for an
application." From the model's position they are the same tool with different names, so
it calls both. A human reading only the descriptions would make the same mistake.

**Schema tokens crowd the question.** Fourteen schemas cost 3,180 prompt tokens. That
block is resent on every step. At five steps, you are paying for those schemas five
times, and the actual question is a smaller and smaller fraction of what the model is
reading.

**More tools means more plausible next moves.** With three tools, "what is the revenue"
has one sensible first call. With fourteen, six tools are arguably relevant, and the
model tries several to be thorough. Every extra call adds a result to the context, which
adds tokens, which pushes the original question further back.

Notice that none of these is the model being stupid. Give a new analyst fourteen
undocumented internal endpoints with overlapping names and watch what happens.

## The better version

Cut to five tools. Merge, do not delete.

```text
get_application          + get_applicant  + get_application_events
                         -> one tool, one record, an `include` parameter

get_bank_transactions    + get_ocr_confidence
                         -> confidence rides along on every transaction

get_documents            + get_missing_documents
                         -> one tool with a `status` filter

search_policy            + get_tenant_policy_overlay
                         -> overlay resolution was already server side (M23)

get_risk_signals         = get_credit_report + get_fraud_score
                         -> one call, both vendors, one shape
```

`get_related_applications`, `get_decision_history`, and `get_queue_position` get removed
entirely. They answered three questions out of thirty, and reviewers get those from the
portal in one click.

Then rewrite every description to the same four-part shape.

```python
GET_DOCUMENTS = ToolSpec(
    name="get_documents",
    description=(
        # what it returns
        "List documents attached to an application, with type, upload date, "
        "OCR quality, and receipt status.\n"
        # when to use it
        "Use this for any question about what has been submitted, what is "
        "missing, or whether a document is readable.\n"
        # when not to use it
        "Do not use this to read the contents of a document. Use "
        "get_bank_transactions for parsed financial data.\n"
        # what it does not do
        "This does not tell you whether a document is sufficient for a "
        "decision. That is a policy question."
    ),
    parameters={
        "type": "object",
        "properties": {
            "applicationId": {"type": "integer"},
            "status": {
                "type": "string",
                "enum": ["ALL", "RECEIVED", "MISSING", "UNREADABLE"],
                "description": "Default ALL. Use MISSING for 'what are we "
                               "waiting on' questions.",
            },
        },
        "required": ["applicationId"],
        "additionalProperties": False,
    },
    effect="read",
    handler=_get_documents,
)
```

Rerun the 30 cases.

| Measure | 3 tools | 14 tools | 5 merged tools |
|---|---|---|---|
| Tool selection accuracy | 93% | 61% | 94% |
| Answer accuracy | 87% | 64% | 91% |
| Median steps | 3 | 5 | 3 |
| Median prompt tokens | 8,900 | 21,400 | 9,600 |
| p50 latency | 6.2s | 14.9s | 6.8s |
| Cost per question | $0.019 | $0.061 | $0.021 |

Five tools beat three, because the merged ones cover more ground without adding a
choice. Five tools beat fourteen on every column including the ones you would expect
more capability to help.

One more change worth making. `POST /v1/tools/invoke` takes a `tools` list from the
caller. The reviewer portal knows which screen the reviewer is on. A revenue panel sends
three tools. A document panel sends two. The model never sees a tool it has no business
using on that screen, which is both a quality improvement and, in Mission 27, a security
control.

:::judgment
**A tool call is a suggestion your code chooses to act on. Everything hard about agents
comes from forgetting that sentence.**

The mechanics are small. A schema, a loop, a step limit. Engineers learn them in an
afternoon and then spend two years learning the part that is not mechanical, which is
that the tool list is a design surface with the same weight as an API.

The thing to take from the 61 percent is not "use fewer tools." It is that the tool list
is read by the model the way a new hire reads a wiki page. Two endpoints with similar
names and identical first sentences will be confused, by a person or a model, and the
person at least gets to ask someone. Names, descriptions, and the boundary between one
tool and two are the actual engineering here. Write descriptions that say when not to
use the tool, because that sentence does more work than the sentence describing what it
does.

The other durable habit is measuring routing separately from answers. Answer accuracy
went from 87 to 64 and the cause was invisible at that level. Tool selection accuracy
made it obvious in one table. When a loop gets worse, ask which step got worse before
you touch a prompt.

And the reason Renee's warning went into a tool description rather than the system
prompt: the system prompt is shared by every question, so a warning about one field gets
diluted by everything else in there. The description is loaded right next to the
decision it is meant to change. That is a small thing that compounds.
:::

:::commslab
#### To Renee

> The assistant can pull the application and the transactions itself now, so you should
> not have to paste anything. I put your warning about the revenue field directly into
> the code so it never uses that number. Try it for a week and tell me every time it
> reaches for something you would not have reached for.

She reported a real bug in the form of an offhand comment. Say out loud that you acted
on it, or she stops making them.

#### To Marcus

> Adding a tool is an hour of code and a permanent cost to every other question. We went
> from 3 tools to 14 and answer quality dropped from 87 percent to 64. Merging back to
> 5 put it at 91. So the answer on new tools is yes, with a measurement before and after,
> and sometimes the measurement says no.

He is not going to stop asking for capability, and he should not. Give him a rule with a
number in it rather than a refusal.

#### To Janet

> Read-only tools, five of them, all going through existing service endpoints with the
> same tenant header the portal uses. No new database access, no new credentials. Hard
> caps on steps and tokens per request so a loop cannot run away. Write tools are not in
> this and I will bring that to you separately.

She will ask who is on call. Answer it before she asks: the tools call services her team
already owns and already pages on.

#### To Yuki

> Every tool is read-only and the tenant comes from the request header, never from a
> model argument. Arguments are schema validated before any handler runs, and
> `additionalProperties` is false so the model cannot smuggle in a field. I would like an
> hour with you before I add anything that writes.

Do not tell Yuki it is safe. Tell her the three specific controls and invite the review.
:::

## Practice

Different industry, same skill.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A freight brokerage, 220 employees. Brokers match shipper loads to trucking carriers by
phone and email all day. You are building an assistant for the broker desk.

Product hands you a list of capabilities they want as tools:

```
searchLoads              searchCarriers            getCarrierInsurance
getCarrierSafetyRating   getCarrierEquipment       getLaneHistory
getSpotRate              getContractRate           getFuelSurcharge
getShipperCreditLimit    getLoadDocuments          getDriverHoursRemaining
bookLoad                 sendCarrierEmail          updateLoadStatus
```

Facts from your first week:

- 80 percent of broker questions are one of five things.
- `searchCarriers` on a common lane returns 400 or more results.
- `getSpotRate` and `getContractRate` return the same field names with different
  meanings, and brokers mix them up too.
- A carrier without current insurance is not bookable. There is no other rule with that
  property.

**Your task**

1. Split the fifteen into read and write. For each write tool, name the worst thing a
   wrong argument does.
2. Merge the read tools down to at most six. Say what each merge costs.
3. `searchCarriers` returns 400 results. What do you return to the model, and why is the
   answer not "all of them"?
4. Write the description for the merged carrier tool, using the four-part shape.
5. Give a termination condition for the loop that is not a step count.

---

**Notes, after you have written yours**

Read and write. The three writes are `bookLoad`, `sendCarrierEmail`, and
`updateLoadStatus`. `bookLoad` with a wrong carrier id commits a real truck to a real
load and the brokerage owes somebody money. `sendCarrierEmail` cannot be recalled and
goes to an outside company under your brand. `updateLoadStatus` is the quiet one:
marking a load delivered when it is not delivered breaks billing and the shipper's
inventory planning. Everything else reads.

The merge. One `getCarrier` that takes a carrier id and returns insurance, safety rating,
equipment, and lane history together, because a broker never wants one of those alone.
One `getRates` with a `type` parameter covering spot, contract, and fuel surcharge, and
returning explicitly named fields so the two rates can never be confused in the output.
Keep `searchLoads`, `searchCarriers`, `getShipperCreditLimit`, and `getLoadDocuments`.
That is six. The cost of merging is payload size. `getCarrier` now returns lane history
nobody asked for on every call, so cap it at the last 10 lanes and say so in the
description.

The 400 results. You return the top 15 with a `totalMatches` count and a short note that
the search was narrowed. Dumping 400 rows does three bad things: it costs thousands of
tokens on this step and every step after, it buries the relevant rows in the middle of a
long context where models attend to them least, and it invites the model to summarize
instead of choosing. The tool should also apply the insurance rule server side. A carrier
without current insurance is not bookable, so it should never appear in the list at all.
Rules that are absolute belong in your code, not in a description you hope gets followed.

The termination condition. Steps are a backstop, not a plan. Better ones are specific to
the job. Stop when a tool returns the same fingerprint twice. Stop when the model has all
inputs the booking form requires and route it to the form rather than another call. Stop
when cumulative prompt tokens cross a budget. And stop when a tool returns
`insufficient`, hand the question to the broker with what you found, and log it as a
capability gap. The last one turns dead ends into a backlog instead of into loops.
:::
