---
id: M18
slug: intake
title: Intake
subtitle: >-
  A business owner on a bad connection taps upload three times. You now have
  three documents and two OCR bills.
phase: 4
order: 18
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - >-
    Diagnose a non-idempotent write path from production evidence instead of
    from a code review
  - >-
    Choose between a client idempotency key and a server-derived content hash,
    and defend the choice
  - >-
    Implement an idempotency key store that replays the original result, with a
    TTL and cleanup
  - Close the second delivery path instead of stopping at the HTTP endpoint
concepts:
  - idempotency
  - content hashing
  - at-least-once delivery
  - object storage
  - deduplication
competencies:
  - coding
  - architecture
  - production-reliability
  - fintech-judgment
prereqs:
  - M17
condensed: true
durationCondensed: 96
---
## Where you are

Phase 3 is done. You have a model call that returns valid JSON, an eval suite that scores 96 percent overall, and a slice report that told you the loan proceeds cases sit at 68 percent. You know the real work is in documents now.

## Key artifacts

:::evidence{type=ticket label="Support queue export, May, filtered to doc_type=BANK_STATEMENT"}
```text
NSC-88214  "Charged twice for statement review?"          resolved  "explained fee"
NSC-88301  "I uploaded once, portal shows 3 copies"       resolved  "told to ignore"
NSC-88355  "Underwriter asked for statement I sent"       resolved  "resent"
NSC-88402  "Which May statement are you using"            resolved  "checked manually"
NSC-88477  "My revenue number changed overnight"          escalated  Renee B.
NSC-88510  "I uploaded once, portal shows 2 copies"       resolved  "told to ignore"
NSC-88604  "Why does it say 4 documents"                  resolved  "told to ignore"
...
Total rows: 431
Rows whose resolution note contains "ignore" or "resubmit": 268
```
:::

:::evidence{type=sql label="psql, northstar schema"}
```sql
SELECT document_id, doc_type, storage_key, byte_size, sha256, created_at
FROM northstar.documents
WHERE application_id = 84412
ORDER BY created_at;
```
```text
 document_id | doc_type       | storage_key                            | byte_size | sha256 | created_at
-------------+----------------+----------------------------------------+-----------+--------+------------------------
      771402 | BANK_STATEMENT | docs/84412/6f1c..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:22:07-04
      771403 | BANK_STATEMENT | docs/84412/a208..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:22:31-04
      771404 | BANK_STATEMENT | docs/84412/c94b..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:23:04-04
```
:::

:::evidence{type=sql label="The extractions those rows produced"}
```sql
SELECT extraction_id, document_id, confidence,
       payload->>'totalCredits' AS total_credits
FROM northstar.document_extractions
WHERE document_id IN (771402, 771403, 771404);
```
```text
 extraction_id | document_id | confidence | total_credits
---------------+-------------+------------+---------------
        512880 |      771402 |       0.94 | 252400.00
        512881 |      771403 |       0.96 | 314580.00
        512882 |      771404 |       0.94 | 252400.00
```
:::

## Evidence to use

:::evidence{type=ticket label="Support queue export, May, filtered to doc_type=BANK_STATEMENT"}
```text
NSC-88214  "Charged twice for statement review?"          resolved  "explained fee"
NSC-88301  "I uploaded once, portal shows 3 copies"       resolved  "told to ignore"
NSC-88355  "Underwriter asked for statement I sent"       resolved  "resent"
NSC-88402  "Which May statement are you using"            resolved  "checked manually"
NSC-88477  "My revenue number changed overnight"          escalated  Renee B.
NSC-88510  "I uploaded once, portal shows 2 copies"       resolved  "told to ignore"
NSC-88604  "Why does it say 4 documents"                  resolved  "told to ignore"
...
Total rows: 431
Rows whose resolution note contains "ignore" or "resubmit": 268
```
:::

:::evidence{type=sql label="psql, northstar schema"}
```sql
SELECT document_id, doc_type, storage_key, byte_size, sha256, created_at
FROM northstar.documents
WHERE application_id = 84412
ORDER BY created_at;
```
```text
 document_id | doc_type       | storage_key                            | byte_size | sha256 | created_at
-------------+----------------+----------------------------------------+-----------+--------+------------------------
      771402 | BANK_STATEMENT | docs/84412/6f1c..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:22:07-04
      771403 | BANK_STATEMENT | docs/84412/a208..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:22:31-04
      771404 | BANK_STATEMENT | docs/84412/c94b..-may_statement.pdf    |   9418223 | <null> | 2026-05-28 14:23:04-04
```
:::

:::evidence{type=sql label="The extractions those rows produced"}
```sql
SELECT extraction_id, document_id, confidence,
       payload->>'totalCredits' AS total_credits
FROM northstar.document_extractions
WHERE document_id IN (771402, 771403, 771404);
```
```text
 extraction_id | document_id | confidence | total_credits
---------------+-------------+------------+---------------
        512880 |      771402 |       0.94 | 252400.00
        512881 |      771403 |       0.96 | 314580.00
        512882 |      771404 |       0.94 | 252400.00
```
:::

:::evidence{type=log label="document-service, 2026-05-28, correlated on trace 9f2a11"}
```text
14:22:07.402 INFO  c.n.doc.upload.DocumentUploadController - upload start app=84412 bytes=9418223
14:22:29.118 INFO  c.n.doc.upload.DocumentUploadController - upload ok app=84412 documentId=771402 ms=21716
14:22:31.006 INFO  c.n.doc.upload.DocumentUploadController - upload start app=84412 bytes=9418223
14:22:52.744 INFO  c.n.doc.upload.DocumentUploadController - upload ok app=84412 documentId=771403 ms=21738
14:23:04.881 INFO  c.n.doc.upload.DocumentUploadController - upload start app=84412 bytes=9418223
14:23:26.560 INFO  c.n.doc.upload.DocumentUploadController - upload ok app=84412 documentId=771404 ms=21679
```
:::

:::evidence{type=http label="applicant-portal HTTP client config, src/lib/http.ts"}
```text
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 20000,
});

axiosRetry(api, { retries: 2, retryCondition: axiosRetry.isRetryableError });
```
:::

:::evidence{type=metrics label="Query over May uploads, grouped by cause"}
```sql
-- duplicate groups = same application_id, doc_type, byte_size within 10 minutes
-- cause inferred from user_agent and inter-arrival gap
```
```text
cause                                        groups   share
client retry interceptor (gap 20-25s)         1,204   71%
user re-tap (gap > 45s, same session)           373   22%
kafka redelivery (no new documents row)         119    7%
```
:::

## Your task

:::task{time="120 min"}
Make document upload idempotent, end to end.

1. Write down which uniqueness rule you are enforcing, in one sentence, before you
   write code. "Same file" is not a rule. Define it.
2. Add a migration for whatever state you need. Do not modify V1 through V14.
3. Change the endpoint. A repeated upload must return the original result, not an error
   and not a new document id.
4. Handle the case where the same key arrives with different bytes. Decide what the
   status code is and why.
5. Write tests that would have caught the bug. At least one has to exercise two
   concurrent requests.
6. Then find the second path. There is one. Fixing HTTP alone leaves it open.

Run `make test` and `make up` before you claim it works.
:::

## Stop and think

:::stopandthink
Answer in writing before you scroll.

1. What is your uniqueness rule? Same bytes? Same application and doc type? Same
   client-supplied key? Each of those is wrong for a different real case. Name the case.
2. A repeat request arrives. Do you return 200 or 201? With what body?
3. The same idempotency key arrives with a different file attached. What now?
4. How long do you keep the key? What happens after that?
5. Marcus wants Wendy to disable the button. What exactly does that fix, and what does
   it not fix? Be specific about the 71 percent.

Five minutes. Question 3 is the one most people skip and it is the one that matters in
an audit.
:::

## One line to remember

:::judgment
**A duplicate write is a property of the write path, not of the user, and a write path
usually has more entrances than the one you are looking at.**

The instinct to fix this at the button is not laziness. It is the correct instinct applied
one layer too high. Something enters the system twice, so you stop it where you can see
it. The trouble is that the UI is the entrance you control least and that carries the
least traffic.

The habit to build is enumeration. Before you fix a duplicate, list every writer. At
Northstar that list was the portal, a partner's own form, a retry layer, and a Kafka
consumer. The button covered one of four, partially. When you find yourself fixing a data
integrity problem in a front end, stop and count.

The second habit is precision about idempotent versus deduplicated. Deduplicated means
the extra thing is thrown away. Idempotent means the second caller cannot tell it was
second. Only the second one lets you turn on retries and stop worrying, and that is the
entire point. If your repeat call returns 409, you have not finished. You have moved the
problem into every client.

Last, notice what the duplicates actually cost. The $3,290 a month in duplicate OptiScan
pages is the number that gets into a slide. The number that matters is Renee being unable
to explain to an applicant why his revenue changed overnight. Duplicate rows plus a
nondeterministic vendor equals a number that depends on query order. In a lending system,
a number that depends on query order is not a bug. It is an audit finding.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A healthcare clearinghouse. Providers submit claims through three channels: a web portal,
an SFTP batch drop of X12 837 files, and a REST API used by four EHR vendors.

Duplicate claims are a compliance problem, not just a cost problem. A duplicate paid
claim is an overpayment, and overpayments have a 60 day refund clock.

What you learn in two days:

- The web portal already sends a `Claim-Submission-Id` header. Two of the four EHR
  vendors do not send anything.
- SFTP batches are re-dropped by providers "to be safe" when a confirmation email is
  slow. About 9 percent of batches are re-drops.
- Each 837 file contains a control number in the ISA and GS envelope segments, and a
  `CLM01` patient control number per claim.
- Providers legitimately resubmit a corrected claim with the same `CLM01` and a
  different `CLM05-3` frequency code. The frequency code is what says "this replaces
  claim X."
- One provider sends the same `CLM01` for two genuinely different claims, because their
  practice management software reuses the number after a year.
- The payer's adjudication engine is consumed off a queue with at-least-once delivery.

**Your task**

1. Write the uniqueness rule in one sentence. It has to survive the corrected-claim case
   and the number-reuse case.
2. Decide, per channel, whether you use a caller-supplied key, a derived hash, or both.
   Say what you do about the two EHR vendors who send nothing.
3. What do you return when the same key arrives with different claim content?
4. What is your TTL, and what is the argument for that number? The 60 day refund clock is
   relevant.
5. Name the second write path and how you close it.

---

**Notes, after you have written yours**

The rule most people write first is "same `CLM01` means same claim." That fails in two
directions. The corrected claim shares `CLM01` and must be accepted. The reused `CLM01` is
a different claim and must also be accepted.

A rule that survives both: a claim is the same claim when the provider id, the `CLM01`,
the frequency code, the service date span, and a hash of the service lines all match. The
frequency code lets a correction through, because a replacement claim has a different one.
The service date span breaks the reuse case, because a claim reused a year later has
different dates.

Channel by channel. The portal and the two cooperative EHR vendors have a caller key, so
use it, scoped to provider. The two that send nothing get the derived hash, and you do not
wait for them to ship a header, because a compliance exposure does not pause for a vendor
roadmap. SFTP gets both layers. The envelope control number catches the whole-file re-drop
cheaply, and the per-claim hash catches a file the provider edited slightly. Nine percent
of batches are identical re-drops, so the cheap check at the envelope saves you hashing
40,000 claim segments to learn what one control number could have told you.

Same key with different content is a 422 with a specific error code, and it goes on a
queue somebody reads. In healthcare that pattern is usually a provider software bug and
the provider needs to hear about it. Replaying the old result silently tells them their
corrected claim was accepted when it was not, and then a denied claim never gets
resubmitted and a patient gets a bill.

The TTL is the interesting one. Twenty four hours is the retry answer and it is wrong
here. The exposure is an overpayment with a 60 day refund clock, so you need to answer
"did we already pay this" for far longer than a retry window. Split it. A short TTL on the
idempotency key table, because that is about retries. A permanent claim fingerprint on the
claim record, because that is about duplicate detection and audit. Two mechanisms, two
lifetimes, two questions. One table with a 60 day TTL gives you a large hot table and
still cannot answer the audit question on day 61.

The second write path is the adjudication queue, and the adjudicator is the thing that
moves money. Guard it the way you guarded the extraction: a unique constraint on
`(claim_fingerprint, adjudication_ruleset_version)`, with a cheap existence check before
the expensive work. Fix only intake and you have built a system that accepts a claim once
and can still pay it twice.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
