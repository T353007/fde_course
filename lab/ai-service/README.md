# Northstar ai-service

All model work for the Northstar lab lives here. FastAPI on port 8000.

The default provider is `stub`. It replays recorded model output from disk.
You do not need an API key to run the course.

## Quick start

```bash
cd lab/ai-service
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn ai_service.main:app --host 0.0.0.0 --port 8000
```

Check it:

```bash
curl -s http://localhost:8000/v1/health
```

Classify the canonical May statement:

```bash
curl -s http://localhost:8000/v1/classify/transactions \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  -H 'X-Trace-Id: demo-1' \
  -d '{
    "transactions": [
      {"date":"05/04","description":"STRIPE PAYOUT","amount":48230},
      {"date":"05/06","description":"TRANSFER FROM SAVINGS","amount":30000},
      {"date":"05/11","description":"STRIPE PAYOUT","amount":51340},
      {"date":"05/18","description":"FASTCAPITAL LOAN","amount":75000},
      {"date":"05/22","description":"STRIPE PAYOUT","amount":47830}
    ]
  }'
```

You should see `naiveTotalCredits` of 252400.00 and `operatingRevenue` of 147400.00.
The model labeled the rows. Python added the money.

## Providers

Set `LLM_PROVIDER` to one of:

| Value | What it does |
|---|---|
| `stub` | Offline. Deterministic. Default. |
| `ollama` | A model on your machine |
| `openai` | Hosted |
| `anthropic` | Hosted |

### Stub scenarios

Send `X-Stub-Scenario` or set `STUB_SCENARIO`:

| Scenario | Behavior |
|---|---|
| `default` | Recorded good path |
| `revenue-as-string` | Returns `$78,231 approximately` |
| `slow-p99` | Sleeps 9 to 40 seconds |
| `truncated-json` | Cuts output at the token limit |
| `hallucinated-ein` | Invents an EIN |
| `injected-instructions` | Obeys text in the document |
| `overconfident-ocr` | High confidence, wrong values |
| `tool-overreach` | Calls `declineApplication` on a read question |

Tests set `STUB_SLOW_SCALE=0` so `slow-p99` does not actually sleep.

### Ollama

```bash
ollama pull qwen3:8b
ollama pull qwen3:1.7b
ollama pull llama3.1:8b
export LLM_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
```

`qwen3:8b` wants roughly 8 to 10 GB of RAM free. `qwen3:1.7b` is lighter and
is used for routing experiments.

### Hosted

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
# or
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

Nothing in the core course path requires a hosted key.

## Tests

```bash
LLM_PROVIDER=stub STUB_SLOW_SCALE=0 pytest
```

## Endpoints

See `lab/LAB_SPEC.md` section 7. Short list:

- `POST /v1/extract/bank-statement`
- `POST /v1/classify/transactions`
- `POST /v1/policy/answer`
- `POST /v1/memo/draft`
- `POST /v1/tools/invoke`
- `GET /v1/health`
- `GET /v1/models`
- `GET /v1/traces/{traceId}`

Every request should send `X-Tenant-Id` and `X-Trace-Id`.
