---
id: M12
slug: your-first-model-call
title: Your First Model Call
subtitle: Tokens, context windows, and temperature, learned by watching them cost you money and time.
phase: 3
order: 12
duration: 210
difficulty: 2
lab: true
status: complete
objectives:
  - Make a real call to ai-service and read every field in the response
  - Predict cost and latency from token counts before you run anything
  - Choose a temperature on purpose and know what it does not control
  - Explain what the recorded stub provider buys you and what it hides
concepts: [tokens, context windows, temperature, non-determinism, system prompts, cost per call, stub providers]
competencies: [ai-fundamentals, coding, architecture]
prereqs: [M11]
---

## Where you are

Eleven weeks of this project have been talking. You re-scoped away from the AI
underwriter, you have Renee's eleven rules written down, and you know the 5.1 days of
document wait is the thing worth attacking.

Today you write the first line of code that touches a model.

The slice is small on purpose. Given the text of one credit transaction from a bank
statement, decide whether it is operating revenue or something else. That is it. No
memo writing, no decisions, no policy. One classification.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:52 AM"}
```text
Marcus:  ok so we're building now?? 🎉
Marcus:  I have a product review Thursday. Can I show something?

You:    I can show you a model classifying transactions by Thursday.
You:    It will be one endpoint and it will be ugly.

Marcus:  perfect, that's all I need
Marcus:  quick q, how much does this cost us per application

You:    I'll have a number for you Thursday.

Janet:   how much does it cost when it's wrong
```
:::

Janet's question is better than Marcus's question. Park it. You cannot answer it yet,
and Mission 15 is where you get the tools to.

## The conversation

:::dialogue{title="Nadia, Slack DM, Monday 9:20 AM"}
**Nadia:** first model call today?

**You:** yes

**Nadia:** ok. one ask. before you send a single request, write down what you think
the response is going to contain. every field.

**You:** why

**Nadia:** because you're about to get a JSON blob with nine fields in it and four of
them decide whether this project is affordable. if you read them for the first time
after the call worked, you will skip past them.

**You:** fine. what should I be looking for

**Nadia:** tokens and latency. those two numbers are your whole budget for the rest
of the year and nobody in that building knows they exist yet.

*A minute passes.*

**Nadia:** also. do not run it once and believe the result.
:::

## What you know about the system

`ai-service` runs on port 8000. Python 3.12 and FastAPI. It is the one service in the
lab you own outright.

It talks to models through a provider layer, so no mission depends on one vendor. Four
providers exist and you pick one with an environment variable.

| `LLM_PROVIDER` | What it does |
|---|---|
| `stub` | Default. Replays recorded model output. Offline, free, same answer every time. |
| `ollama` | A model running on your own machine. Mission 17. |
| `openai` | Hosted. Needs a key. |
| `anthropic` | Hosted. Needs a key. |

On top of the provider there is a model alias. An alias is a short name in config that
points at a specific vendor model, so mission code says `hosted-mid` instead of naming
a vendor and a version. Ask the service what it has.

:::evidence{type=http label="GET /v1/models"}
```bash
curl -s localhost:8000/v1/models \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m12-0001' | jq
```

```json
{
  "provider": "stub",
  "default_alias": "hosted-premium",
  "aliases": {
    "hosted-premium": {
      "context_window": 200000,
      "usd_per_1m_prompt_tokens": 15.00,
      "usd_per_1m_completion_tokens": 75.00
    },
    "hosted-mid": {
      "context_window": 128000,
      "usd_per_1m_prompt_tokens": 0.60,
      "usd_per_1m_completion_tokens": 2.40
    },
    "local-qwen8b": {
      "context_window": 32768,
      "usd_per_1m_prompt_tokens": 0.0,
      "usd_per_1m_completion_tokens": 0.0,
      "cost_basis": "fixed hardware, not per token"
    }
  }
}
```
:::

Note `default_alias`. Somebody set it to the most expensive option, probably because
it was the best one in a demo. Hold that thought for about an hour.

## The code

Here is the prompt that ships in the repo. Read it before you send it.

```python
# lab/ai-service/ai_service/prompts/txn_classify_v1.py

PROMPT_VERSION = "txn-classify-v1"

SYSTEM = """You classify credit transactions from a small business bank statement.

Return one classification for each transaction you are given.

Allowed values:
  OPERATING_REVENUE   money the business earned from customers
  INTERNAL_TRANSFER   money moved between accounts the business or owner controls
  LOAN_PROCEEDS       money received from a lender or a funding company
  OWNER_CONTRIBUTION  money the owner put into the business
  REFUND_OR_REVERSAL  a returned payment or a chargeback reversal
  OTHER_CREDIT        anything else

Rules:
  Use only the transaction text and the amount. You have no other information.
  If the text does not support a value, use OTHER_CREDIT. Do not guess.
"""

USER_TEMPLATE = """Classify these transactions.

{transactions_json}

Return a JSON array. One object per transaction, with keys txn_id and
classification, in the same order you received them."""
```

Two messages, and the split matters. The system message holds the instructions that
are the same for every request. The user message holds the data that changes. Models
weight the system message more heavily and providers cache it more aggressively, so
putting the rules in the user message costs you both quality and money.

## Evidence

Send forty real transactions. These come out of `bank_transactions` in the seed data.

:::evidence{type=http label="POST /v1/classify/transactions, first 3 of 40 shown"}
```bash
curl -s localhost:8000/v1/classify/transactions \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: m12-0002' \
  -d @scripts/fixtures/m12-batch-40.json | jq
```

```json
{
  "transactions": [
    {"txn_id": "TX-10021", "date": "2026-05-04",
     "description": "STRIPE PAYOUT ST-4471QK", "amount": 48230.00},
    {"txn_id": "TX-10022", "date": "2026-05-06",
     "description": "TRANSFER FROM SAVINGS ****1221", "amount": 30000.00},
    {"txn_id": "TX-10023", "date": "2026-05-18",
     "description": "FASTCAPITAL LOAN ADV 0518", "amount": 75000.00}
  ],
  "options": {"alias": "hosted-premium", "temperature": 0.2,
              "max_output_tokens": 800}
}
```
:::

:::evidence{type=http label="Response, 200 OK"}
```json
{
  "results": [
    {"txn_id": "TX-10021", "classification": "OPERATING_REVENUE"},
    {"txn_id": "TX-10022", "classification": "INTERNAL_TRANSFER"},
    {"txn_id": "TX-10023", "classification": "LOAN_PROCEEDS"}
  ],
  "usage": {
    "model": "hosted-premium",
    "prompt_version": "txn-classify-v1",
    "prompt_tokens": 1282,
    "completion_tokens": 383,
    "latency_ms": 4180,
    "cost_usd": 0.04796,
    "finish_reason": "stop",
    "cost_basis": "hosted per-token pricing"
  }
}
```
:::

It got all three right, including the Fastcapital loan. That feels good and it means
almost nothing, which is Mission 15's problem.

Look at the `usage` block instead.

## What you do not know

- What a token is, precisely enough to predict a bill.
- Whether 1,282 prompt tokens is a lot.
- What happens if you send 900 transactions instead of 40.
- Whether the same request returns the same answer twice.
- Why the default alias costs 25 times what the cheap one costs, and whether that
  buys anything on this task.

:::task{time="75 min"}
Work only from the `usage` block and the alias table above. No new code yet.

1. Compute the cost of that single call by hand. Show prompt cost and completion cost
   separately.
2. Compute the same call under `hosted-mid`.
3. Northstar processes 1,840 applications a month. A three month statement window has
   a median of 61 credit transactions. At 40 transactions per call, work out the
   monthly cost of this endpoint under both aliases.
4. Now compute it again if you send one transaction per call instead of batching 40.
   Assume the system message is 218 tokens and one transaction plus its wrapper is 50
   prompt tokens and 12 completion tokens.
5. Write the four numbers in `customers/northstar/cost-notes.md`. You will need them
   in Mission 34 and you will not remember them.
:::

:::stopandthink
Before you scroll:

1. You batched 40 transactions into one call. Name one thing that gets worse as you
   raise that number, and one thing that gets worse as you lower it.
2. `max_output_tokens` is 800. What do you expect to happen if the model needs 8,000?
   Be specific about what you would see in the response.
3. You are about to set `temperature: 0` because you want the same answer every time.
   Write down what you believe that guarantees.
4. Marcus asks "how much per application" on Thursday. Which of your four numbers do
   you give him, and what do you say about the other three?

Two minutes. Write it down. Question 3 is the one that costs people money.
:::

## Working through it

### What a token actually is

A token is a chunk of text the model reads as one unit. Roughly a common word, or a
piece of a rare one. `PAYOUT` is one token. `ST-4471QK` is five, because the model has
never seen it before and has to spell it out in pieces.

That is the whole idea, and here is why it matters. You are billed per token, in both
directions. Latency also scales with tokens, because the model generates output one
token at a time. So token count is the single number that drives your bill and your
response time.

Two consequences that are not obvious:

Long identifiers are expensive. A transaction description full of reference codes
costs two to three times a plain English one of the same length. Northstar's statements
are full of reference codes.

Output is much more expensive than input. Under `hosted-premium` it is five times the
price per token. So a change that makes the model explain its reasoning in prose can
triple your bill without changing a single input.

### The cost math

The call was 1,282 prompt tokens and 383 completion tokens.

```
hosted-premium
  prompt      1,282 / 1,000,000 x $15.00  = $0.019230
  completion    383 / 1,000,000 x $75.00  = $0.028725
  total                                     $0.047955

hosted-mid
  prompt      1,282 / 1,000,000 x $0.60   = $0.000769
  completion    383 / 1,000,000 x $2.40   = $0.000919
  total                                     $0.001688
```

Now scale it. 61 credits per application at 40 per call is 2 calls. 1,840
applications a month is 3,680 calls.

| Setup | Cost per call | Cost per month |
|---|---|---|
| `hosted-premium`, batched 40 | $0.04796 | $176.45 |
| `hosted-mid`, batched 40 | $0.00169 | $6.21 |
| `hosted-mid`, one call per transaction | $0.00006 | $13.63 |

That last row surprises people. Per call it is cheap. In total it is worse, because
the 218 token system message gets sent 61 times per application instead of 2 times.
You pay for the instructions over and over.

The per-transaction version is also 30 times slower end to end, because you serialize
61 network round trips instead of 2.

### The alias decision

Switch classification to `hosted-mid` and the monthly bill drops from $176 to $6.

Does quality drop? You do not know yet. That is not a reason to keep paying 28 times
more, and it is not a reason to switch blindly either. It is a reason to build the
thing in Mission 15 that can answer the question.

For now, switch it and write down that the decision is unverified.

```python
# lab/ai-service/ai_service/config.py
CLASSIFY_ALIAS = os.getenv("CLASSIFY_ALIAS", "hosted-mid")  # M12, unverified
```

Remember this change. In Mission 34 you find out that a different endpoint never got
it, and that one premium model doing trivial work is 14 percent of a $91,000 bill.

### The context window

The context window is the maximum number of tokens a model can hold in one request,
counting your input and its output together. `hosted-mid` holds 128,000. The local
model in Mission 17 holds 32,768, and its runner defaults to 4,096, which will ruin
your afternoon later.

Send 900 transactions and watch the edge.

```bash
python scripts/m12_big_batch.py --count 900 --max-output-tokens 800
```

:::evidence{type=http label="Response, 200 OK, truncated output"}
```json
{
  "results": [
    {"txn_id": "TX-10021", "classification": "OPERATING_REVENUE"},
    "... 82 more parsed ..."
  ],
  "parse_error": "unterminated object at char 7994",
  "usage": {
    "prompt_tokens": 23642,
    "completion_tokens": 800,
    "latency_ms": 9611,
    "finish_reason": "length"
  }
}
```
:::

The input fit fine. 23,642 tokens is nowhere near 128,000. The output did not fit.
900 results need about 8,600 completion tokens and you allowed 800, so the model
stopped in the middle of an object and the JSON is not valid JSON.

`finish_reason` is the field that tells you. `stop` means the model finished. `length`
means you cut it off. Anything other than `stop` and your output is suspect no matter
how good it looks.

This is the number one cause of parse failures in production LLM systems, and it does
not throw an error anywhere. You get a 200 and a broken string. Mission 13 is entirely
about what to do with it.

## Tests

```python
# lab/ai-service/tests/test_classify_usage.py
import httpx

BASE = "http://localhost:8000"
HEADERS = {"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "test-m12"}


def load_batch(n: int) -> dict:
    txns = [
        {"txn_id": f"TX-{10000 + i}", "date": "2026-05-04",
         "description": "STRIPE PAYOUT ST-4471QK", "amount": 1000.00 + i}
        for i in range(n)
    ]
    return {"transactions": txns,
            "options": {"alias": "hosted-mid", "temperature": 0.0,
                        "max_output_tokens": 800}}


def test_usage_block_is_complete():
    r = httpx.post(f"{BASE}/v1/classify/transactions",
                   json=load_batch(40), headers=HEADERS, timeout=60)
    u = r.json()["usage"]
    for field in ("model", "prompt_version", "prompt_tokens",
                  "completion_tokens", "latency_ms", "cost_usd",
                  "finish_reason", "cost_basis"):
        assert field in u, f"missing {field}"
    assert u["finish_reason"] == "stop"


def test_output_limit_reports_length_not_success():
    r = httpx.post(f"{BASE}/v1/classify/transactions",
                   json=load_batch(900), headers=HEADERS, timeout=120)
    u = r.json()["usage"]
    assert u["finish_reason"] == "length"
    assert u["completion_tokens"] == 800
```

The second test is the useful one. It asserts that when you cut the model off, the
service says so out loud instead of returning a partial answer that looks complete.

## Then this happens

You set `temperature: 0.0` everywhere, because you want the same answer every time.
Then you write the test you have written a hundred times in your career.

```python
def test_classification_is_stable():
    body = load_batch(40)
    first = httpx.post(f"{BASE}/v1/classify/transactions",
                       json=body, headers=HEADERS, timeout=60).json()["results"]
    second = httpx.post(f"{BASE}/v1/classify/transactions",
                        json=body, headers=HEADERS, timeout=60).json()["results"]
    assert first == second
```

It passes. You run it twenty more times. It passes twenty more times. You merge it.

Then Tuesday at 6:14 AM, CI goes red on a branch that has nothing to do with you, and
Sam's deploy sits in the queue for two hours.

:::evidence{type=slack label="#northstar-eng, Tuesday 8:31 AM"}
```text
Sam:     ai-service test is flaky. blocking my deploy.
Sam:     test_classification_is_stable, one item differs

Janet:   how long has that been in main

Sam:     six days

Janet:   who is on call for a test that fails at 6am

You:     me. I'm on it. sorry.

Sam:     ...Ah. So you found that.

You:     found what

Sam:     temperature zero.
```
:::

## Tracking it down

Run it fifty times and count instead of asserting.

```python
# lab/ai-service/scripts/m12_variance.py
import hashlib, json, collections, httpx

BASE = "http://localhost:8000"
HEADERS = {"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "m12-variance"}

body = {
    "transactions": json.load(open("scripts/fixtures/m12-batch-40.json"))["transactions"],
    "options": {"alias": "hosted-mid", "temperature": 0.0, "max_output_tokens": 800},
}

seen = collections.Counter()
for _ in range(50):
    results = httpx.post(f"{BASE}/v1/classify/transactions",
                         json=body, headers=HEADERS, timeout=60).json()["results"]
    seen[hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()[:12]] += 1

for digest, count in seen.most_common():
    print(f"{digest}  {count:>3}")
```

Against the stub provider, this prints one line with a count of 50, because the stub
is deterministic by design. That is exactly why the stub cannot teach you this. Run it
against a real model.

```bash
LLM_PROVIDER=ollama python scripts/m12_variance.py
```

```text
a91c4d0f7b22   47
3e77b1aa04c9    2
c0d5f2891ee6    1
```

Three distinct outputs from fifty identical requests at temperature 0.

### What temperature actually does

When the model picks the next token, it has a score for every possible token.
Temperature reshapes those scores before the pick. High temperature flattens them, so
unlikely tokens get a real chance. Low temperature sharpens them, so the top token
almost always wins. Zero means always take the top token.

"Almost always" is doing the work in that sentence. Temperature 0 removes the
deliberate randomness. It does not remove these:

**Ties.** When two tokens have nearly identical scores, tiny numeric differences
decide the winner. On a GPU, adding a batch of floating point numbers in a different
order gives a slightly different sum. Your request is batched with whatever other
requests arrived at the same millisecond, so the order changes.

**The provider.** They update models, change serving code, and roll out to a fraction
of traffic. `hosted-mid` in June is not byte-for-byte the same function as
`hosted-mid` in May, and nobody sends you an email.

Your three transactions that flipped were all borderline: `DEP CHECK 4471`,
`ACH CREDIT MERCH SVCS`, and `ZELLE FROM J HARLOWE`. Ambiguous input is exactly where
near-ties live.

### The real cost

The flaky test was two hours of Sam's deploy window and a hit to your credibility with
Janet in week one of writing code.

The larger cost was avoided by luck. You had already told Wendy that her portal could
cache classifications forever because the same input gives the same output. If she had
built that, two underwriters would eventually see different categories for the same
transaction on the same statement, and the bug report would have come from a customer.

## The better version

Temperature 0 is still the right setting here. You just cannot build on top of a
guarantee it does not make.

```python
# lab/ai-service/ai_service/config.py
CLASSIFY_TEMPERATURE = 0.0      # lowers variance, does not eliminate it
```

Three changes.

**Test the property, not the bytes.** You care that classifications are stable enough
to be useful, not that two JSON strings are equal.

```python
def test_classification_is_stable_enough():
    body = load_batch(40)
    runs = [httpx.post(f"{BASE}/v1/classify/transactions", json=body,
                       headers=HEADERS, timeout=60).json()["results"]
            for _ in range(5)]
    baseline = {r["txn_id"]: r["classification"] for r in runs[0]}
    disagreements = sum(
        1 for run in runs[1:] for r in run
        if baseline[r["txn_id"]] != r["classification"]
    )
    total = 40 * (len(runs) - 1)
    assert disagreements / total < 0.02, f"{disagreements}/{total} unstable"
```

**Record what answered.** Every response already carries `model` and `prompt_version`.
Store them next to the result. When output changes next quarter, you need to know
whether the model changed, the prompt changed, or the input changed. Mission 31 turns
this into the `ai_invocations` table.

**Cache with a version in the key.** Not `sha256(input)`. Use
`(prompt_version, model, sha256(input))`, so a prompt or model change invalidates the
cache instead of serving answers from a system that no longer exists.

### Why this course records model output

Now the stub makes sense.

`StubProvider` looks up a fixture by `(prompt_version, sha256(normalized_input),
scenario)` and replays real recorded model output. If no fixture matches it raises
`FixtureMissing` rather than inventing an answer, so a gap is a loud CI failure
instead of a quiet wrong number.

That buys three things. Mission 32's incident fires the same way on every machine, so
the debugging walkthrough is not fiction. The eval numbers in Mission 16 stay put
instead of moving every time a vendor ships an update. And nobody needs an API key or
a budget to take this course.

What it hides is exactly the thing you just spent two hours on. Real variance. So the
missions that teach variance say so and tell you to run against `ollama` or a hosted
model. This one did.

:::judgment
**Tokens and latency are not implementation details. They are the two constraints that
decide what your system is allowed to be.**

Most engineers coming to production AI treat the model call like any other network
call: send a request, handle the response, move on. The habit that separates people who
ship affordable systems from people who get a surprise invoice is reading the usage
block every single time, especially when the answer was correct.

The specific trap in this mission is worth naming because almost everyone walks into
it. Temperature 0 feels like `--deterministic`. It is not. It is a variance reduction
knob on one source of randomness out of several, and the ones it does not touch are the
ones outside your process. An engineer who understands that builds caches with version
keys, tests properties instead of bytes, and stores the model version with every
result. An engineer who does not builds a system that works for four months and then
quietly disagrees with itself.

The other durable habit here is smaller and pays constantly: batch size and model
choice are cost decisions you make before you have any quality data. Make them
explicitly, write down that they are unverified, and go build the thing that can verify
them. An unverified decision you wrote down is engineering. The same decision you
forgot about is the reason a bill goes up 4x and nobody can say why.
:::

:::commslab
Marcus wants a number for Thursday. Three audiences, one set of facts.

#### To Marcus, VP Product

> Six dollars a month for this piece, at your current volume. That is real but it is
> only the classification step, so do not quote it as the cost of the project. The
> number I would put on a slide is "under a dollar per application for the AI, and the
> risk is quality, not cost." I will have quality numbers in about two weeks.

He wants one number he can say out loud without being wrong. Give him one, plus the
sentence that stops him from over-claiming.

#### To Janet, Engineering Manager

> I broke your morning. The test asserted exact equality on model output, which is not
> a property models have. I replaced it with a stability threshold and I am recording
> the model version on every call so we can tell provider changes from our own. That
> class of test will not go back in.

No explanation of temperature. She does not need the lesson, she needs to know it
will not happen again and that you understood why it happened.

#### To Priya, CTO

> One thing to flag early. Our cost and our latency both scale with text volume, not
> with request count. That means statement size drives the bill, and our worst
> statements are the biggest ones. I want to put a token budget per application in the
> design before we build more of it.

She thinks in blast radius. Frame the token economics as a system property with a
control on it.
:::

## Practice

Different domain. Same reasoning. Write your answers before opening the notes.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A medical billing company processes denied insurance claims. They want a model to read
each denial letter and pick the correct appeal template.

What you know:

- 34,000 denial letters a month.
- A denial letter averages 2,900 tokens after OCR. The longest 5 percent run past
  14,000 tokens.
- The current prompt sends the letter plus a 26,000 token reference document listing
  every appeal template and the rules for choosing one.
- Their engineer set `max_output_tokens: 4096` because the model sometimes explains
  its choice at length.
- They use the premium alias: $15 per million prompt tokens, $75 per million
  completion tokens.
- Their engineer reports the pilot cost as "about $400 a month" based on 200 test
  letters.

**Your task**

1. Compute the real monthly cost. Show prompt and completion separately.
2. Their engineer's $400 estimate is wrong. Find the reason. It is not arithmetic.
3. Name the single change with the largest cost effect, and estimate the new bill.
4. One of the facts above is a correctness risk, not a cost risk. Which one, and what
   goes wrong?

---

**Notes, after you have written yours**

**The real cost.** Prompt per letter is 26,000 + 2,900 = 28,900 tokens. Times 34,000
letters is 982.6 million prompt tokens, at $15 per million, which is $14,739. Assume
output averages half the allowance, say 2,000 tokens: 68 million completion tokens at
$75 per million is $5,100. Total near $19,800 a month, not $400.

**Why the estimate was wrong.** He measured 200 letters and multiplied by cost per
letter, which is the right method. The error is that his 200 test letters were short
and clean, so his average prompt was maybe 1,100 tokens instead of 2,900, and his
average output was short because easy letters get short answers. Test samples are
almost always easier than production. This is the same mistake the golden dataset in
Mission 15 is built to catch, and it shows up in cost estimates before it shows up in
quality numbers.

**The largest change.** Stop sending the 26,000 token reference document in every
request. It is 90 percent of the prompt and it is identical every time. Retrieve the
three or four relevant templates instead, or fine tune, or at minimum use provider
prompt caching on the static block. Cutting the static block to 2,000 retrieved tokens
takes prompt tokens to 4,900 per letter, so $2,499 a month, and total near $7,600. If
you can also stop asking for prose reasoning and get a template ID plus a short
citation, completion drops to maybe 200 tokens and the bill lands near $2,900.

That single change is worth more than every other optimization combined, which is the
general shape of LLM cost work: find the big static block in the prompt.

**The correctness risk.** `max_output_tokens: 4096` combined with letters that run
past 14,000 tokens. Long letters produce long explanations, explanations get cut at
4,096, and the response comes back with `finish_reason: length` and a truncated
answer. If their code reads the template ID from the end of the output, or parses JSON,
those letters fail. If it takes the first template mentioned in a half-finished
explanation, they file the wrong appeal and nobody notices, because a 200 response with
plausible text does not look like a failure.

Ask to see how many of their pilot responses had `finish_reason` other than `stop`.
The answer is almost never zero, and it is almost never something anyone has checked.
:::
