---
slug: exam-03-architecture
title: "Exam 03: Architecture"
subtitle: Design an AI-assisted multi-tenant underwriting assist system. Constraints are real. Fancy diagrams are not the point.
kind: exam
order: 3
duration: 150
competencies: [architecture, agent-design, rag, security, fintech-judgment]
---

## The ask

Design the production architecture for Northstar's underwriting copilot:

- Three tenants: NSC_DIRECT, BAYLINE, CASCADE
- Bank statement extraction and classification
- Policy Q and A with citations
- Human review required before any decision
- Adverse action explanations Doug can stand behind
- No raw bank data to third-party model vendors without a documented alternative path

## Deliverables

1. Component diagram in text (boxes and arrows is fine).
2. For each component, say what is deterministic code, model, retrieval, workflow, or human.
3. Data flow for one application, including PII boundaries.
4. How tenant isolation works in retrieval and in tools.
5. Failure modes: OCR wrong, model schema fail, vendor empty 200, prompt injection in a PDF.
6. What you would not build in v1.

:::stopandthink
Sketch all six before the key. Graders punish agent-everything designs.
:::

:::spoiler{label="Answer key and rubric"}
A strong answer looks like:

- Intake and OCR orchestration in document-service (deterministic + vendor)
- Classification: model for ambiguous labels only, rules for known patterns, Python/Java for arithmetic
- Policy answers: retrieval with tenant and effective-date filters in the query (pre-filter), citations required
- Copilot UI: suggestions after reviewer forms a view, six clicks is a product bug
- Write tools behind approval gates; read tools default-open for authorized reviewers
- Local or VPC-hosted model path for bank text; hosted allowed only for non-sensitive slices or redacted text
- Observability spans with prompt version, tokens, cost, retrieved doc ids, validation result
- v1 excludes autonomous decline, phone bots, and chat with applicants

**Fail patterns:** agent as the control plane, tenant filter only in the prompt, model computes DSCR or revenue totals, no human gate on write tools, no audit of retrieved docs.

**Rubric**

| Score | Behavior |
|---|---|
| 4 | Clear seams, pre-filter tenancy, hybrid AI boundary, honest v1 cuts |
| 3 | Solid seams, weak on vendor semantic failure |
| 2 | RAG + agent diagram with little fintech constraint handling |
| 1 | "One agent with tools for everything" |
:::
