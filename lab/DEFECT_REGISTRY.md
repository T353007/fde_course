# DEFECT_REGISTRY.md

**SPOILER WARNING**

Do not open this file until Phase 9 unless a mentor tells you to.

Every entry below is planted on purpose. Missions refer to defects by ID in
author notes only. Learner-facing text never names these IDs.

Other engineers may append Java and Python defects later. This file starts with
the infra, schema, seed, and vendor ones.

| ID | Description | Location | Mission | Red herring | History |
|---|---|---|---|---|---|
| D-03 | No unique constraint on `applicants.ein` | `V1__create_schema_and_applicants.sql` | M10 | no | 2014 portal rewrite. Product wanted "save draft even with a bad EIN." Unique index was never added. Corner Rise Bakery exists four times. |
| D-04 | `decisions.reason_codes` is comma separated TEXT | `V7__create_decisions.sql`, seed | M12 | no | 2016 underwriter UI used a free text box. Machine codes got stuffed in later. Spaces and trailing commas vary by row. |
| D-05 | `document_extractions.confidence` is not correctness | `V5__create_document_extractions.sql`, OptiScan stubs | M19 | no | OptiScan reports character confidence. Faxed statements score high and still invent digits. Nobody calibrated it. |
| D-07 | Two tenant conventions: `tenant_id` and `customer_id` | `applications.customer_id`, seed | M24 | no | Bayline onboarding in 2020. Product refused to touch `applicants.tenant_id`, so CRM got a second field. Formats include `BAY`, `bayline`, `2`, null. |
| D-09 | `documents.sha256` null on most historical and non-portal rows | `V9__documents_add_sha256.sql`, seed | M18 | no | Hashing shipped for portal uploads only. Email, fax, and vendor pulls still land null. Dedupe cannot see cross-channel duplicates. |
| D-11 | `applications.submitted_at` differs from SUBMITTED events | portal write path, seed offsets | M05 | no | Portal writes client time. Backend writes the event when it accepts. Median gap about 40 minutes. Nightly backfill makes some gaps days. |
| D-12 | Helpful looking unused index on `applicants.legal_name` | `V14__indexes.sql` | M05 | yes | Added for a portal typeahead that never shipped. Shows up in `\d` and wastes attention during timing work. |
| D-13 | Missing index on `application_events(application_id, event_type)` | absent from V14 | M05 | no | Event log grew. Timing queries scan the table. The index people reach for is the unused legal_name one. |
| D-14 | `application.submitted` Kafka messages have no key | application-service producer | M29 | no | Oldest producer. Partitioning was "we will add keys when we need ordered consumers." That day never came. |
| D-15 | `document.uploaded` consumer is not idempotent | document-service Kafka consumer | M18 | no | At-least-once delivery plus a write path that always inserts. Duplicate uploads create duplicate rows. |
| D-16 | Ledgerlink returns HTTP 200 with empty accounts | WireMock scenario `ledgerlink-empty-200` | M33 | no | Stale bank connections look healthy. Empty array, status still looks fine. Underwriting treats it as "no deposits." |
| D-17 | Sentinel sometimes returns score with no reason codes | seed fraud_signals, scenario `sentinel-no-reason-codes` | M27 | no | Vendor schema drift. Fraud service stores whatever came back. Downstream assumes codes always exist. |
| D-18 | Corveil rate limits with 40s p99 | scenarios `corveil-ratelimit`, `corveil-slow` | M31 | no | Shared bureau pool. Burst traffic from retries trips 429s. Callers hold JDBC pool threads while waiting. |
| D-19 | LoanCore rejects funding outside 02:00-04:00 ET | scenario `loancore-batch-window` | M33 | no | Servicing runs a nightly batch. The SOAP fault says `BATCH_WINDOW_CLOSED`. Ops knows. The runbook is tribal. |
| D-20 | OptiScan degraded path returns confident garbage | scenario `optiscan-degraded` | M19 | no | Fax and scan artifacts. Confidence stays above 0.98. Amounts come back with OCR letter/digit swaps. |
| D-21 | `policy_documents.effective_from` null on 4 of 8 rows | `V13__policy_effective_from.sql`, seed | M22 | no | Column added late for dated retrieval. Drafts and overlays were never backfilled. Precedence code has to guess. |
| D-22 | `credit-policy-FINAL.pdf` is a 2023 draft | policy seed row | M22 | yes | Filename says FINAL. Contents are old. Looks like the current policy in a file listing. |
| D-23 | Temporary 2021 comment still gates category_source cleanup | `V12__bank_transactions_category_source.sql` | M09 | yes | Jan Kowalski left a "TEMPORARY (2021-03-14)" note. Looks like the smoking gun for revenue. It is not. |
| D-24 | Some REVIEW_CLOSED events never land | seed event builder | M05 | no | Reviewer closes the tab. Six percent of sessions miss the close event. Hands-on time from open/close pairs undercounts. |
| D-25 | Webhook order from DocuSign / Twilio / Salesforce is not guaranteed | vendor stubs | M30 | yes | Out of order webhooks look like a state machine bug. Usually the consumer is fine and the vendor is chatty. |
| D-26 | `fix_stuff.sh` nightly patch job | ops folklore, Bill Tran | M08 | no | Patches a tenant mismatch after doc sweep. Undocumented. Bill runs it by hand when it fails. |
| D-27 | Feature flag `USE_NEW_REVENUE_CALC_V2_TEMP` from 2021 still live | underwriting `application.yml` | M09 | no | Half finished V2 calculator gated by a "temp" flag. Default true in some envs. The exclusion logic never finished. |
| D-28 | RevenueCalculator counts every credit | `RevenueCalculator.java` | M09 | no | Jan's 2019 TODO. Transfers and loan deposits inflate operating revenue. Three callers disagree on the definition. |
| D-29 | Portal cash-flow widget wants total deposits on purpose | application-service PortalSummaryController | M09 | yes | Looks like the same revenue bug. For the applicant-facing widget, total deposits is arguably correct. |
| D-30 | Document upload HTTP path is not idempotent | document-service upload API | M18 | no | Two rapid identical uploads create two rows. No idempotency key store until the learner builds one. |

## Rules for this registry

1. Every defect has a plausible history. Do not invent cartoon villains.
2. Every defect is discoverable from lab evidence without reading this file.
3. At least six entries are red herrings. They look worse than they are.
4. When you plant a new one, add a row here in the same format.
