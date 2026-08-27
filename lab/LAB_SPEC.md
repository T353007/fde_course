# LAB_SPEC.md

This is the contract for the Northstar lab. Mission authors quote it. Code authors
build it. If they disagree, this file wins.

Nothing here is aspirational. If a class, endpoint, table, or topic is listed, it
exists in the repo with that exact name.

---

## 1. Layout

```
lab/
  Makefile                     up, down, seed, test, inject, reset, logs
  docker-compose.yml
  DEFECT_REGISTRY.md           spoiler file, listed in section 9
  infra/
    postgres/
      migrations/              Flyway, V1__ through V14__
      seed/                    SQL + CSV, 1,200 applications
    kafka/topics.sh
    vendors/                   WireMock stubs and scenario control
    minio/
  northstar/                   Maven multi-module, Java 21, Spring Boot 3.3
    pom.xml
    common-lib/
    application-service/
    document-service/
    underwriting-service/
    fraud-service/
  ai-service/                  Python 3.12, FastAPI
  evals/                       Python, importable library
  reviewer-portal/             React 19, TypeScript, Vite
  data/
    bank-statements/           PDFs and OCR fixtures, clean and terrible
    policies/                  the eight policy documents
    golden/                    labeled eval datasets
```

## 2. Ports

| Port | Service |
|---|---|
| 5432 | PostgreSQL 16 |
| 6379 | Redis 7 |
| 9092 | Kafka (KRaft, single node) |
| 9000 | MinIO API |
| 9001 | MinIO console |
| 8081 | application-service |
| 8082 | document-service |
| 8083 | underwriting-service |
| 8084 | fraud-service |
| 8000 | ai-service |
| 8090 | vendor stubs (WireMock) |
| 8099 | vendor scenario control API |
| 5173 | reviewer-portal |

## 3. Make targets

```
make up          docker compose up, wait for health, run migrations
make seed        load 1,200 applications and documents
make down        stop everything
make reset       down, wipe volumes, up, seed
make test        run Java tests, Python tests, eval smoke suite
make logs S=underwriting-service
make inject SCENARIO=ledgerlink-empty-200
make clear-scenarios
make eval SUITE=txn-classification
make ollama-check
```

## 4. Database

Schema `northstar`. Flyway migrations under `infra/postgres/migrations`.

### Core tables

```sql
-- V1
CREATE TABLE applicants (
    applicant_id     BIGSERIAL PRIMARY KEY,
    legal_name       TEXT NOT NULL,
    dba_name         TEXT,
    ein              TEXT,               -- nullable, and often wrong
    owner_ssn_last4  TEXT,
    email            TEXT,
    phone            TEXT,
    tenant_id        TEXT NOT NULL,      -- NSC_DIRECT | BAYLINE | CASCADE
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- No unique constraint on ein. This is defect D-03.

-- V2
CREATE TABLE applications (
    application_id   BIGSERIAL PRIMARY KEY,
    applicant_id     BIGINT NOT NULL REFERENCES applicants(applicant_id),
    product          TEXT NOT NULL,      -- TERM_LOAN | LOC | SBA_7A | EQUIPMENT
    amount_requested NUMERIC(14,2),
    status           TEXT NOT NULL,
    submitted_at     TIMESTAMPTZ,
    decided_at       TIMESTAMPTZ,
    customer_id      TEXT,               -- second tenant convention, defect D-07
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`applications.status` values, in the order they normally occur:

```
DRAFT  SUBMITTED  DOCS_REQUESTED  DOCS_RECEIVED  IN_REVIEW
PENDING_INFO  DECISIONED  DECLINED  APPROVED  FUNDED  WITHDRAWN
```

`PENDING_INFO` is the rework loop. An application can enter it more than once, and the
count of those entries is the number that matters in Mission 05.

### The rest

| Table | Purpose | Notes for missions |
|---|---|---|
| `documents` | uploaded files | `sha256` column added in V9, nullable, mostly null on old rows |
| `document_extractions` | OCR and model output | has `confidence`, which does not mean what people think |
| `bank_transactions` | parsed transactions | `category` nullable, `category_source` in V12 |
| `application_events` | append-only status history | the real source for cycle time, see D-11 |
| `decisions` | underwriting outcomes | `reason_codes` is a comma separated string, not an array |
| `policy_documents` | policy files and metadata | `effective_from` added in V13 and is null on 4 of 8 rows |
| `fraud_signals` | fraud vendor output | |
| `ai_invocations` | model call audit log | added by the learner in Mission 31 |
| `idempotency_keys` | added by the learner in Mission 18 | |

### The timestamp trap

`applications.submitted_at` is set by the portal when the applicant clicks submit.
`application_events` records a `SUBMITTED` event when the backend accepts it. These
differ by a median of 40 minutes and occasionally by days, because the portal writes
`submitted_at` on the client and a nightly job backfills failures. Cycle time measured
from `submitted_at` is wrong and nobody knows. This is defect D-11 and it is the core
of Mission 05.

## 5. Kafka topics

| Topic | Producer | Consumer | Notes |
|---|---|---|---|
| `application.submitted` | application-service | underwriting, fraud | no key set, defect D-14 |
| `document.uploaded` | document-service | document worker | at least once, consumer not idempotent, D-15 |
| `document.extracted` | document-service | underwriting-service | |
| `underwriting.decisioned` | underwriting-service | application-service, CRM sync | |
| `ai.extraction.requested` | underwriting-service | ai-service bridge | added Mission 29 |

## 6. The revenue function

This is the most quoted code in the course. It lives at:

`northstar/underwriting-service/src/main/java/com/northstar/underwriting/revenue/RevenueCalculator.java`

It must appear in the repo exactly as written here, including the comment and the
formatting, because four missions quote it line for line.

```java
package com.northstar.underwriting.revenue;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

import org.springframework.stereotype.Component;

import com.northstar.common.model.BankTransaction;

@Component
public class RevenueCalculator {

    /**
     * Calculates average monthly revenue from bank transactions.
     *
     * TODO(jkowalski, 2019-08): this counts every credit. Underwriting says
     * transfers and loan deposits should not count. Waiting on a decision
     * from credit policy before changing it. Do not change without asking
     * Renee, three other things depend on this number.
     */
    public BigDecimal calculateMonthlyRevenue(List<BankTransaction> transactions,
                                              int months) {
        BigDecimal total = BigDecimal.ZERO;

        for (BankTransaction t : transactions) {
            if (t.amount().signum() > 0) {
                total = total.add(t.amount());
            }
        }

        if (months <= 0) {
            return BigDecimal.ZERO;
        }

        return total.divide(BigDecimal.valueOf(months), 2, RoundingMode.HALF_UP);
    }
}
```

Jan Kowalski left Northstar in 2021. The decision from credit policy never came.

### The three callers

| Caller | File | What it wants |
|---|---|---|
| `UnderwritingDecisionService` | underwriting-service | Operating revenue. Currently wrong. |
| `DebtServiceCoverageService` | underwriting-service | Operating revenue. Also wrong, and the error compounds. |
| `PortalSummaryController` | application-service, over REST | Total deposits, for a "cash flow" widget shown to the applicant. Currently correct. |

That third one is the trap in Mission 09. Fixing the function correctly for underwriting
silently changes a number on a customer facing screen, and the applicant-facing
definition is arguably the right one for that widget. There is no single correct
definition. That is the point.

## 7. ai-service API

Python 3.12, FastAPI, on 8000. Every endpoint takes `X-Tenant-Id` and `X-Trace-Id`.

```
POST /v1/extract/bank-statement     document text in, structured transactions out
POST /v1/classify/transactions      batch of transactions in, categories out
POST /v1/policy/answer              question + filters in, answer with citations out
POST /v1/memo/draft                 application context in, credit memo draft out
POST /v1/tools/invoke               tool calling entry point, Mission 25 onward
GET  /v1/health
GET  /v1/models                     what providers and models are available
```

### Provider layer

`ai_service/providers/` with a common interface:

```python
class LLMProvider(Protocol):
    name: str

    def complete(self, req: CompletionRequest) -> CompletionResponse: ...
    def supports_json_schema(self) -> bool: ...
```

Implementations: `StubProvider`, `OllamaProvider`, `OpenAIProvider`, `AnthropicProvider`.

Selected with `LLM_PROVIDER`. Default `stub`.

`CompletionResponse` always carries `model`, `prompt_version`, `prompt_tokens`,
`completion_tokens`, `latency_ms`, `cost_usd`, and `finish_reason`. Cost for local and
stub providers is 0.0 and `cost_basis` says why.

### StubProvider

Deterministic. Key is `(prompt_version, sha256(normalized_input), scenario)`. Looks up
`fixtures/recorded/*.json`, which came from real recorded model output. If no fixture
matches, it raises `FixtureMissing` rather than inventing an answer, so a missing
fixture is a loud failure in CI instead of a quiet wrong number.

Scenarios are set with the `X-Stub-Scenario` header or `STUB_SCENARIO`:

| Scenario | Behavior | Used by |
|---|---|---|
| `default` | the recorded good path | everywhere |
| `revenue-as-string` | returns `"$78,231 approximately"` | M32 |
| `slow-p99` | sleeps 9 to 40 seconds | M31, M34 |
| `truncated-json` | cuts output at the token limit | M13 |
| `hallucinated-ein` | invents an EIN that was blank in the source | M14 |
| `injected-instructions` | obeys the text in the document | M26 |
| `overconfident-ocr` | high confidence, wrong values | M19 |
| `tool-overreach` | calls `declineApplication` on a read question | M27 |

### Ollama

`OLLAMA_HOST` defaults to `http://localhost:11434`. Models used by the course:
`qwen3:8b` for the main path, `qwen3:1.7b` for routing experiments, `llama3.1:8b` for
comparison. `make ollama-check` verifies the daemon and pulls what is missing.

Every mission that uses Ollama must also pass with `LLM_PROVIDER=stub`.

## 8. Eval framework API

`evals/` is a library, not scripts.

```python
from northstar_evals import Dataset, Runner, Slice, metrics

ds = Dataset.load("data/golden/txn-classification-v3.jsonl")

result = Runner(
    task=classify_transactions,
    dataset=ds,
    slices=[
        Slice("loan_proceeds",     lambda c: c.tags.get("kind") == "loan"),
        Slice("internal_transfer", lambda c: c.tags.get("kind") == "transfer"),
        Slice("poor_ocr",          lambda c: c.tags.get("ocr_quality") == "poor"),
        Slice("card_settlement",   lambda c: c.tags.get("kind") == "settlement"),
    ],
).run()

result.report()          # console table, overall plus every slice
result.assert_no_regression(baseline="baselines/txn-v3-qwen8b.json")
```

Case format, one JSON object per line:

```json
{
  "caseId": "TX-10021",
  "input": {"description": "TRANSFER FROM SAVINGS ****1221", "amount": 30000},
  "expected": {"classification": "INTERNAL_TRANSFER"},
  "tags": {"kind": "transfer", "ocr_quality": "good", "tenant": "NSC_DIRECT"},
  "labeledBy": "renee.blackwell",
  "labeledAt": "2026-04-11",
  "confidence": "high"
}
```

`labeledBy` and `confidence` matter. Cases labeled by a junior underwriter with
`confidence: "low"` are where the 2 percent of wrong labels live.

## 9. Planted defects

Full list with mission mapping is in `DEFECT_REGISTRY.md`, which learners should not
open until Phase 9. Every defect has an ID like `D-07`. Missions refer to defects by ID
in author comments only, never in learner-facing text.

Rules for planting a defect:

1. It must have a plausible history. Write that history in the registry.
2. It must be discoverable from evidence available in the lab.
3. At least six of the 41 must be red herrings that look worse than they are.
4. No defect may be discoverable only by reading the registry.

## 10. Running with less

The lab is heavy. There are two smaller profiles.

```
make up PROFILE=core      postgres, redis, ai-service, underwriting only
make up PROFILE=nolocal   everything except Ollama dependencies
```

Missions state which profile they need in frontmatter comments. Nothing in Phases 0
through 3 requires the full stack.
