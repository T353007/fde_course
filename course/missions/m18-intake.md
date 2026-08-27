---
id: M18
slug: intake
title: Intake
subtitle: A business owner on a bad connection taps upload three times. You now have three documents and two OCR bills.
phase: 4
order: 18
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Diagnose a non-idempotent write path from production evidence instead of from a code review
  - Choose between a client idempotency key and a server-derived content hash, and defend the choice
  - Implement an idempotency key store that replays the original result, with a TTL and cleanup
  - Close the second delivery path instead of stopping at the HTTP endpoint
concepts: [idempotency, content hashing, at-least-once delivery, object storage, deduplication]
competencies: [coding, architecture, production-reliability, fintech-judgment]
prereqs: [M17]
---

## Where you are

Phase 3 is done. You have a model call that returns valid JSON, an eval suite that
scores 96 percent overall, and a slice report that told you the loan proceeds cases sit
at 68 percent. You know the real work is in documents now.

Before you can improve extraction, you need documents to be a stable thing. Right now
they are not. Nobody has said that out loud yet, which is why this mission starts in
Carla's ticket queue and not in the code.

## The request

You asked Carla for a month of tickets tagged `documents`. She sent a CSV with 431 rows
and one line of context: "sorry it's a lot."

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

Two hundred sixty eight of 431 tickets were closed by telling the customer to ignore what
they were seeing or to do it again. That is a workaround with a headcount attached to it.

Look at NSC-88477. "My revenue number changed overnight." That one went to Renee.

## The conversation

:::dialogue{title="Carla Mendes, support lead, Tuesday 10:05 AM"}
**You:** Two hundred sixty eight of these say ignore it or resubmit.

**Carla:** Oh, that. Yeah, we just tell them to resubmit.

**You:** Does that fix it?

**Carla:** It fixes the ticket.

*She scrolls.*

**Carla:** People upload on their phone in a parking lot. The bar sits there, nothing
happens, so they hit it again. Then there are three. We tell them the extra ones don't
matter.

**You:** Do they matter?

**Carla:** Not to me. Ask Renee about the one I escalated.
:::

:::dialogue{title="Renee Blackwell, ten minutes later"}
**Renee:** 88477. Yes. The applicant was right and I could not explain it to him.

**You:** What happened?

**Renee:** Same statement, three copies, and the system pulled a different one on
Thursday than it pulled on Tuesday. Total deposits went from 252,400 to 314,580.

**You:** On the same document.

**Renee:** On three copies of the same document. OptiScan read one of them differently.
I do not know which one is right. I keyed it by hand and used my number.

*She turns her monitor.*

**Renee:** This is why I have the spreadsheet. Not because I enjoy it.
:::

Stop and sit with that for a second. The duplicate uploads are not a cosmetic problem.
They create two extractions of the same bytes, the two extractions disagree, and the
number that decides whether a business gets funded depends on which row a query
happened to return first.

:::dialogue{title="#northstar-ai, Tuesday 2:40 PM"}
**You:** Upload is creating duplicate document rows. Same file, different ids. 431
support tickets last month.

**Marcus:** Easy fix, right? Just disable the button after they click it.

**Sam:** ...

**Sam:** the button is not the only thing that posts to that endpoint

**Janet:** If you're changing document-service I want to know the blast radius and who
is on call for it.

**Marcus:** Wendy can ship the button today though.

**Wendy:** I can ship the button today. It will not fix this.
:::

## What you know about the system

`document-service` runs on 8082. It was rewritten in 2021 and is the sanest service in
the building, which is not the same as being correct.

The upload path does four things in order: write bytes to MinIO, insert a row in
`northstar.documents`, publish a `document.uploaded` event to Kafka, and return 201 with
the new document id. A worker consumes `document.uploaded` and calls OptiScan.

Two facts from the schema matter. `documents.sha256` was added in migration V9. It is
nullable and it is null on almost every historical row, because the multipart path never
computed one. You have a column that would solve half your problem and no data in it.

And `document.uploaded` is at-least-once. Kafka gives you at-least-once unless you do
extra work. Nobody did the extra work, and the consumer has no dedup of its own.

## The code

Here is the endpoint.

```java
package com.northstar.document.upload;

import java.io.IOException;
import java.time.Instant;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.northstar.common.event.DocumentUploadedEvent;
import com.northstar.common.event.Topics;
import com.northstar.common.tenant.TenantContext;

@RestController
@RequestMapping("/v1/documents")
public class DocumentUploadController {

    private final ObjectStore objectStore;
    private final DocumentRepository documents;
    private final EventPublisher events;

    public DocumentUploadController(ObjectStore objectStore,
                                    DocumentRepository documents,
                                    EventPublisher events) {
        this.objectStore = objectStore;
        this.documents = documents;
        this.events = events;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentUploadResponse> upload(
            @RequestParam("applicationId") Long applicationId,
            @RequestParam("docType") String docType,
            @RequestPart("file") MultipartFile file) throws IOException {

        String tenantId = TenantContext.get();

        // Fresh UUID every call. Two identical uploads get two storage keys.
        String storageKey = "docs/" + applicationId + "/"
                + UUID.randomUUID() + "-" + file.getOriginalFilename();

        objectStore.put(storageKey, file.getBytes(), file.getContentType());

        Long documentId = documents.insert(
                applicationId, tenantId, docType, storageKey, file.getSize());

        events.send(Topics.DOCUMENT_UPLOADED, new DocumentUploadedEvent(
                documentId, applicationId, tenantId, docType, storageKey, null, Instant.now()));

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new DocumentUploadResponse(documentId, storageKey));
    }
}
```

Nothing in there is stupid. It is the shortest correct-looking upload handler you could
write. It has no idea that a second identical request is a repeat, because nothing in the
request tells it and it never looks at the bytes.

## Evidence

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

Identical byte size. Twenty four seconds apart, then thirty three. Three separate
objects in MinIO holding the same 9.4 MB.

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

There is Renee's ticket. Two extractions say 252,400 and one says 314,580. The one that
disagrees has the highest confidence score of the three. Write that down. Mission 19 is
entirely about it.

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

Every upload took about 21.7 seconds and every one of them succeeded.

:::evidence{type=http label="applicant-portal HTTP client config, src/lib/http.ts"}
```text
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 20000,
});

axiosRetry(api, { retries: 2, retryCondition: axiosRetry.isRetryableError });
```
:::

There it is. The client gives up at 20 seconds and retries twice. The server finishes at
21.7 seconds. The upload is not failing. The client walks away 1.7 seconds early and does
it again, twice, automatically.

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

Seventy one percent of the duplicates never involved a human tapping anything. Carla's
theory was 22 percent right, which is the most dangerous kind of right.

:::evidence{type=email label="OptiScan monthly invoice, May"}
```text
Standard tier pages    198,412 @ $0.11    $21,825.32
Enhanced tier pages      6,926 @ $0.34    $ 2,354.84
                                          ----------
Total                                     $24,180.16

Note: enhanced tier applied automatically to pages failing
quality pre-check.
```
:::

Run those pages through a hash and 13.6 percent are bytes OptiScan already read this
month. About $3,290 a month, or $39,000 a year, to read the same PDFs twice. The money is
annoying. The disagreeing extractions are the actual problem.

## What you do not know

- Does any downstream code depend on there being multiple document rows per statement?
- What does the reviewer portal show when there are three copies? Which one wins?
- Are duplicates ever legitimate? A corrected statement is a real thing.
- Who else writes to `documents` besides this endpoint?
- Does the Kafka consumer already handle redelivery somewhere you have not read?

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

## Working through it

### The wrong turn, and it demos beautifully

You let Wendy ship the button. It takes her twenty minutes.

```tsx
<button
  disabled={uploading}
  onClick={handleUpload}
>
  {uploading ? "Uploading..." : "Upload statement"}
</button>
```

In the demo it is perfect. Click upload, the button greys out, one document appears.
Marcus says it looks great. You feel fine for about four days.

Then Carla's weekly queue comes in with 96 duplicate-copy tickets, down from 108. A 12
percent improvement, which is roughly the share of users who were double-tapping in the
same session and noticed.

Three things the button could never touch. The retry interceptor lives below it, so
`axiosRetry` fires while the button is still disabled, and that is 71 percent of your
duplicates. Bayline posts to `POST /v1/documents` from their own intake form, and your
button is not on their page. The Kafka consumer is a second writer that no front end
change reaches.

The cost was small in dollars and real in credibility. You spent a demo saying the
problem was fixed, and then Renee got another wrong number. Fix it where the write
happens.

### What idempotency actually means

An operation is idempotent when doing it twice has the same effect on the system as
doing it once. Not the same response text. The same effect.

That is different from deduplicated, and the difference is worth being precise about.

Deduplication throws away the extra thing after it arrives. You end up with one document
row, and the caller gets whatever the second call happened to return, which might be an
error, a new id, or nothing. The caller cannot tell what happened.

Idempotency makes the second call a full participant. It returns the original result, the
original id, the original status. The client cannot tell whether it was first or fourth,
and it does not need to. That property is what makes a retry safe.

The practical test: could you put this endpoint behind a retry loop with three attempts
and go to lunch? If not, it is not idempotent yet.

### Client key or content hash

There are two ways to know a request is a repeat, and they answer different questions.

A **client-generated idempotency key** is a value the caller invents once per logical
operation and reuses on every retry of that operation. Usually a UUID in a header.
`Idempotency-Key: 0f3d9c1a-...`. It answers: is this the same intent as before?

A **server-derived content hash** is something you compute from the request itself,
usually sha256 of the bytes. It answers: are these the same bytes as before?

Neither is a superset of the other, and picking one because it is easier is how you get
a bug in six months.

| Situation | Client key | Content hash |
|---|---|---|
| Client retried the same call after a timeout | Correct. Same key. | Correct. Same bytes. |
| Applicant uploads the same PDF to two different applications | Different keys, both saved. Correct. | Same hash. A global hash rule would wrongly reject. |
| Applicant re-uploads a corrected statement, same filename | Different key, saved. Correct. | Different bytes, saved. Correct. |
| Applicant uploads the exact same file again on purpose, a week later | Different key, saved. Arguably correct. | Same hash, rejected. Arguably correct. |
| Caller is a partner who does not send the header | No protection at all. | Still works. |
| Caller has a bug and reuses one key for everything | Silently drops real uploads. | Unaffected. |

Read the last two rows together. The client key protects you when the client cooperates.
The content hash protects you when it does not. Bayline is a partner, you do not control
their code, and you cannot make them ship a header this quarter.

So use both, in a specific order. Client key when it is present, scoped to tenant and
endpoint. Content hash scoped to `(application_id, doc_type, sha256)` when the key is
absent. The scope on the hash is what keeps the same PDF usable on two different
applications, which applicants do when they have two loans in flight.

Store the hash on every row going forward. That is the `documents.sha256` column sitting
there since V9 with nothing in it.

Which brings up the historical rows. There are 340,000 documents with a null sha256. You
are not going to stream 2.9 TB out of MinIO to hash files for applications decided in
2022. Do not pretend you will. Write the constraint so null rows are excluded, and say so
in the migration.

### The migration

```sql
-- V15__idempotency.sql

CREATE TABLE northstar.idempotency_keys (
    tenant_id         TEXT        NOT NULL,
    endpoint          TEXT        NOT NULL,
    idempotency_key   TEXT        NOT NULL,
    request_sha256    TEXT        NOT NULL,
    state             TEXT        NOT NULL,   -- IN_PROGRESS | COMPLETED
    response_status   INT,
    response_body     JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at      TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, endpoint, idempotency_key)
);

CREATE INDEX idx_idem_expires ON northstar.idempotency_keys (expires_at);

-- Content-hash fallback for callers that send no key.
-- Partial on purpose. 340,412 rows predate V9 and have a null sha256. Postgres
-- treats nulls as distinct in a unique index anyway, but writing the predicate
-- makes the intent readable and keeps the index off dead rows.
CREATE UNIQUE INDEX uq_documents_app_type_sha
    ON northstar.documents (application_id, doc_type, sha256)
    WHERE sha256 IS NOT NULL;
```

The primary key includes `tenant_id`. Bayline and Cascade both post to this endpoint and
there is no reason two partners cannot pick the same UUID, unlikely as that is. Scoping
by tenant costs nothing and removes the question.

`endpoint` is in the key too. An idempotency key means "this operation." The same key
against a different operation is a different operation.

### The service

```java
package com.northstar.document.idempotency;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * Idempotency for write endpoints.
 *
 * <p>Two calls with the same (tenant, endpoint, key) do the work once. The second
 * caller gets the first caller's stored response, byte for byte, including the
 * status code. That is the property that makes a client retry safe.
 */
@Service
public class IdempotencyService {

    /**
     * How long a key is honored. Twenty four hours covers every retry pattern we
     * have seen, including Bayline's overnight batch, which reuses keys from the
     * previous evening when it restarts.
     */
    private static final Duration TTL = Duration.ofHours(24);

    private final JdbcTemplate jdbc;

    public IdempotencyService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public sealed interface Claim {
        /** You own this key. Do the work, then call complete(). */
        record Proceed() implements Claim {}

        /** Somebody already did this. Return exactly this. */
        record Replay(int status, String body) implements Claim {}

        /** Same key, work still running. Tell the caller to wait. */
        record InFlight() implements Claim {}

        /** Same key, different request. This is a client bug, not a retry. */
        record Mismatch(String storedRequestSha256) implements Claim {}
    }

    public Claim claim(String tenantId, String endpoint, String key, String requestSha256) {
        int inserted = jdbc.update("""
                INSERT INTO northstar.idempotency_keys
                    (tenant_id, endpoint, idempotency_key, request_sha256, state, expires_at)
                VALUES (?, ?, ?, ?, 'IN_PROGRESS', now() + INTERVAL '24 hours')
                ON CONFLICT (tenant_id, endpoint, idempotency_key) DO NOTHING
                """, tenantId, endpoint, key, requestSha256);

        if (inserted == 1) {
            return new Claim.Proceed();
        }

        List<Map<String, Object>> rows = jdbc.queryForList("""
                SELECT request_sha256, state, response_status, response_body::text AS body
                FROM northstar.idempotency_keys
                WHERE tenant_id = ? AND endpoint = ? AND idempotency_key = ?
                """, tenantId, endpoint, key);

        if (rows.isEmpty()) {
            // The row expired between our insert and our select. Rare, and the
            // right move is to let the caller try again rather than guess.
            return new Claim.InFlight();
        }

        Map<String, Object> row = rows.get(0);
        String storedSha = (String) row.get("request_sha256");

        if (!requestSha256.equals(storedSha)) {
            return new Claim.Mismatch(storedSha);
        }
        if (!"COMPLETED".equals(row.get("state"))) {
            return new Claim.InFlight();
        }
        return new Claim.Replay((Integer) row.get("response_status"), (String) row.get("body"));
    }

    public void complete(String tenantId, String endpoint, String key, int status, String body) {
        jdbc.update("""
                UPDATE northstar.idempotency_keys
                   SET state = 'COMPLETED', response_status = ?, response_body = ?::jsonb,
                       completed_at = now()
                 WHERE tenant_id = ? AND endpoint = ? AND idempotency_key = ?
                """, status, body, tenantId, endpoint, key);
    }

    /** Called when the work threw. Frees the key so a real retry can succeed. */
    public void release(String tenantId, String endpoint, String key) {
        jdbc.update("""
                DELETE FROM northstar.idempotency_keys
                 WHERE tenant_id = ? AND endpoint = ? AND idempotency_key = ?
                   AND state = 'IN_PROGRESS'
                """, tenantId, endpoint, key);
    }

    public Optional<Duration> ttl() {
        return Optional.of(TTL);
    }
}
```

Four things in there are load bearing.

`INSERT ... ON CONFLICT DO NOTHING` is the whole concurrency story. Two requests arrive in
the same millisecond and exactly one insert succeeds, because the database enforces the
primary key. The loser reads the row and waits. No lock, no Redis mutex, and no `SELECT`
followed by an `INSERT`, which is the version with a race in it.

`Mismatch` exists because a key already used with different bytes is not a retry.
Something is wrong on the client. Returning the old result there is worse than an error,
because the client would think its new file was saved.

`release` exists because a failed attempt must not poison the key for 24 hours.

The TTL is not a cleanup detail. It is a promise about how long you will honor a retry.
Twenty four hours because Bayline's batch restarts overnight and reuses keys.

### Cleanup

```java
package com.northstar.document.idempotency;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class IdempotencyKeyReaper {

    private static final Logger log = LoggerFactory.getLogger(IdempotencyKeyReaper.class);

    private final JdbcTemplate jdbc;

    public IdempotencyKeyReaper(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** Every hour at :17. Deletes in bounded batches so it never locks the table. */
    @Scheduled(cron = "0 17 * * * *")
    public void reap() {
        int total = 0;
        int deleted;
        do {
            deleted = jdbc.update("""
                    DELETE FROM northstar.idempotency_keys
                     WHERE (tenant_id, endpoint, idempotency_key) IN (
                        SELECT tenant_id, endpoint, idempotency_key
                        FROM northstar.idempotency_keys
                        WHERE expires_at < now()
                        LIMIT 5000
                     )
                    """);
            total += deleted;
        } while (deleted == 5000);

        if (total > 0) {
            log.info("reaped {} expired idempotency keys", total);
        }
    }
}
```

Bounded batches, not one big delete. At 1,840 applications a month this table is small.
It will not stay small if someone points a load test at it, and a `DELETE` that takes a
lock on a hot table during business hours is a bad afternoon.

### The endpoint

```java
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> upload(
            @RequestParam("applicationId") Long applicationId,
            @RequestParam("docType") String docType,
            @RequestHeader(value = "Idempotency-Key", required = false) String clientKey,
            @RequestPart("file") MultipartFile file) throws IOException {

        String tenantId = TenantContext.get();
        byte[] bytes = file.getBytes();
        String sha256 = Hashing.sha256Hex(bytes);

        // Client key when we have one. Content hash when we do not. Bayline does
        // not send the header and will not this quarter.
        boolean clientProvided = clientKey != null && !clientKey.isBlank();
        String key = clientProvided
                ? clientKey
                : "sha256:" + applicationId + ":" + docType + ":" + sha256;

        // What the key is a promise about. Includes the bytes so a reused key
        // with a different file is caught instead of silently replayed.
        String requestSha = Hashing.sha256Hex(
                (applicationId + "|" + docType + "|" + sha256).getBytes(UTF_8));

        var claim = idempotency.claim(tenantId, ENDPOINT, key, requestSha);

        if (claim instanceof IdempotencyService.Claim.Replay r) {
            return ResponseEntity.status(r.status())
                    .header("Idempotent-Replay", "true")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(r.body());
        }
        if (claim instanceof IdempotencyService.Claim.InFlight) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .header("Retry-After", "2")
                    .body(Map.of("error", "upload_in_progress", "documentKey", key));
        }
        if (claim instanceof IdempotencyService.Claim.Mismatch) {
            return ResponseEntity.unprocessableEntity()
                    .body(Map.of("error", "idempotency_key_reused_with_different_request"));
        }

        try {
            // Storage key derives from the content now, so a redelivery overwrites
            // the same object instead of creating a second copy of 9.4 MB.
            String storageKey = "docs/" + applicationId + "/" + sha256 + "/"
                    + Sanitize.filename(file.getOriginalFilename());

            objectStore.putIfAbsent(storageKey, bytes, file.getContentType());

            Long documentId = documents.insertOrGet(
                    applicationId, tenantId, docType, storageKey, bytes.length, sha256);

            events.send(Topics.DOCUMENT_UPLOADED, new DocumentUploadedEvent(
                    documentId, applicationId, tenantId, docType, storageKey,
                    sha256, Instant.now()));

            var body = new DocumentUploadResponse(documentId, storageKey, sha256);
            String json = mapper.writeValueAsString(body);
            idempotency.complete(tenantId, ENDPOINT, key, 201, json);

            return ResponseEntity.status(HttpStatus.CREATED).body(body);
        } catch (RuntimeException | IOException e) {
            idempotency.release(tenantId, ENDPOINT, key);
            throw e;
        }
    }
```

`insertOrGet` does an `INSERT ... ON CONFLICT ... DO NOTHING` against the partial unique
index and selects the existing row when it loses. That is the second line of defense. Wipe
the idempotency table and you still cannot get two document rows for the same bytes on the
same application.

The `Idempotent-Replay: true` header is for you, not the client. When Carla says a
customer saw something odd on Thursday, you want to grep for it.

Note what the replay returns. Status 201, the original document id, the original storage
key. Not 200, not 409, not a new id. The client's second attempt believes it created the
document, because in every sense that matters to the client, it did.

## Tests

```java
package com.northstar.document.upload;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;

import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest
class DocumentUploadIdempotencyTest {

    private static final byte[] PDF = "%PDF-1.4 may statement bytes".getBytes();

    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;

    private MvcResult post(String key) throws Exception {
        var file = new MockMultipartFile("file", "may_statement.pdf",
                MediaType.APPLICATION_PDF_VALUE, PDF);
        var req = multipart("/v1/documents").file(file)
                .param("applicationId", "84412")
                .param("docType", "BANK_STATEMENT")
                .header("X-Tenant-Id", "NSC_DIRECT");
        if (key != null) {
            req = req.header("Idempotency-Key", key);
        }
        return mvc.perform(req).andReturn();
    }

    @Test
    void repeatWithSameKeyReturnsTheOriginalDocumentId() throws Exception {
        MvcResult first = post("k-1");
        MvcResult second = post("k-1");

        assertThat(first.getResponse().getStatus()).isEqualTo(201);
        assertThat(second.getResponse().getStatus()).isEqualTo(201);
        assertThat(second.getResponse().getContentAsString())
                .isEqualTo(first.getResponse().getContentAsString());
        assertThat(second.getResponse().getHeader("Idempotent-Replay")).isEqualTo("true");

        assertThat(countDocs()).isEqualTo(1);
    }

    @Test
    void noKeyHeaderStillDedupesOnContentHash() throws Exception {
        post(null);
        post(null);
        post(null);

        // This is the Bayline case. Three identical posts, no header, one row.
        assertThat(countDocs()).isEqualTo(1);
    }

    @Test
    void sameKeyWithDifferentBytesIs422() throws Exception {
        post("k-2");

        var other = new MockMultipartFile("file", "may_statement.pdf",
                MediaType.APPLICATION_PDF_VALUE, "%PDF-1.4 corrected".getBytes());
        int status = mvc.perform(multipart("/v1/documents").file(other)
                        .param("applicationId", "84412")
                        .param("docType", "BANK_STATEMENT")
                        .header("X-Tenant-Id", "NSC_DIRECT")
                        .header("Idempotency-Key", "k-2"))
                .andReturn().getResponse().getStatus();

        assertThat(status).isEqualTo(422);
        assertThat(countDocs()).isEqualTo(1);
    }

    @Test
    void tenConcurrentIdenticalUploadsProduceOneDocument() throws Exception {
        var pool = Executors.newFixedThreadPool(10);
        List<Callable<Integer>> calls = java.util.stream.IntStream.range(0, 10)
                .mapToObj(i -> (Callable<Integer>) () -> post("k-3").getResponse().getStatus())
                .toList();

        List<Future<Integer>> results = pool.invokeAll(calls);
        pool.shutdown();

        for (Future<Integer> r : results) {
            // 201 for the winner and every completed replay. 409 only if a loser
            // read the row while the winner was still writing, which is correct.
            assertThat(r.get()).isIn(201, 409);
        }
        assertThat(countDocs()).isEqualTo(1);
    }

    private Integer countDocs() {
        return jdbc.queryForObject("""
                SELECT count(*) FROM northstar.documents
                 WHERE application_id = 84412 AND doc_type = 'BANK_STATEMENT'
                """, Integer.class);
    }
}
```

The concurrency test is the one that earns its keep. A `SELECT` then `INSERT`
implementation passes the first three tests and fails this one, sometimes, on a loaded
machine. Run it 50 times in CI before you believe it.

## Then this happens

Two weeks later, on a Thursday, Carla pings you.

:::evidence{type=slack label="DM from Carla, 3:12 PM"}
```text
Carla:  hey the duplicate thing is way better
Carla:  down to like 4 tickets this week
Carla:  but 84771 has two extractions again and the underwriter is asking
```

:::

:::evidence{type=sql label="Checking 84771"}
```sql
SELECT document_id, sha256, created_at FROM northstar.documents
WHERE application_id = 84771;
```
```text
 document_id | sha256                     | created_at
-------------+----------------------------+------------------------
      779118 | 4c1f8a...e2                | 2026-06-11 09:14:02-04
```
```sql
SELECT extraction_id, document_id, created_at, confidence
FROM northstar.document_extractions WHERE document_id = 779118;
```
```text
 extraction_id | document_id | created_at             | confidence
---------------+-------------+------------------------+------------
        529004 |      779118 | 2026-06-11 09:14:39-04 |       0.93
        529011 |      779118 | 2026-06-11 09:16:51-04 |       0.91
```
:::

One document. Two extractions. Two OptiScan charges. Two different confidence scores on
identical bytes.

The HTTP fix worked. The other path is open.

## Tracking it down

Start with the consumer, because that is the only other thing that writes extractions.

:::evidence{type=kafka label="document.uploaded, consumer group document-worker"}
```text
$ kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group document-worker --describe

TOPIC              PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
document.uploaded  0          44102           44102           0
document.uploaded  1          43887           43887           0

$ kafka-console-consumer --bootstrap-server localhost:9092 \
    --topic document.uploaded --partition 0 --offset 44099 --max-messages 3 \
    --property print.timestamp=true

CreateTime:1749647679412  {"documentId":779118,"applicationId":84771,...,"sha256":"4c1f8a...e2"}
CreateTime:1749647811004  {"documentId":779118,"applicationId":84771,...,"sha256":"4c1f8a...e2"}
```
:::

The same event, twice, 131 seconds apart. That is not two uploads. That is one upload and
one redelivery.

:::evidence{type=log label="document-worker, 09:16:20"}
```text
09:16:20.118 WARN  o.a.k.c.c.i.ConsumerCoordinator - [Consumer clientId=document-worker-1,
             groupId=document-worker] Member document-worker-1 sending LeaveGroup request
             due to consumer poll timeout has expired. This means the time between
             subsequent calls to poll() was longer than the configured
             max.poll.interval.ms
09:16:20.402 INFO  o.a.k.c.c.i.ConsumerCoordinator - Revoke previously assigned
             partitions document.uploaded-0, document.uploaded-1
09:16:51.007 INFO  c.n.doc.worker.DocumentWorker - extracting documentId=779118
```
:::

Now it is clear. OptiScan took longer than `max.poll.interval.ms` on that page. Kafka
decided the consumer was dead, revoked the partition, and handed the message to the
rebalanced consumer. The first attempt had already called OptiScan. The offset was never
committed, so the message came back.

Kafka's contract is at-least-once. Your consumer read it as exactly-once and nobody
noticed, because until this month a redelivery just added a duplicate row to a pile of
duplicate rows.

Here is the consumer:

```java
    @KafkaListener(topics = Topics.DOCUMENT_UPLOADED, groupId = "document-worker")
    public void onDocumentUploaded(DocumentUploadedEvent event) {
        var result = optiScan.extract(event.storageKey());
        extractions.insert(event.documentId(), result.payload(), result.confidence());
        events.send(Topics.DOCUMENT_EXTRACTED, toExtracted(event, result));
    }
```

Every line of that is a side effect and none of them is guarded.

## The better version

The consumer needs the same property the endpoint got, applied to the event instead of the
request. Two options.

A `processed_events` table keyed on topic, consumer group, and event identity works, and
it is the general answer. It is also one more table to reason about, and it protects the
consumer without protecting the work.

Or make the work itself idempotent, keyed on what determines the result. An extraction is
determined by the document bytes and the extractor version. Same two, same extraction, no
reason for two rows. Do this one. It is smaller and it survives a consumer group rename.

```sql
-- V16__extraction_identity.sql

ALTER TABLE northstar.document_extractions
    ADD COLUMN extractor_version TEXT;

UPDATE northstar.document_extractions
   SET extractor_version = 'optiscan-v1-legacy'
 WHERE extractor_version IS NULL;

ALTER TABLE northstar.document_extractions
    ALTER COLUMN extractor_version SET NOT NULL;

CREATE UNIQUE INDEX uq_extraction_doc_version
    ON northstar.document_extractions (document_id, extractor_version);
```

```java
    @KafkaListener(topics = Topics.DOCUMENT_UPLOADED, groupId = "document-worker")
    public void onDocumentUploaded(DocumentUploadedEvent event) {
        String version = optiScan.extractorVersion();

        // Cheap read first. Skips the vendor call on a redelivery, which is the
        // difference between a duplicate row and a duplicate invoice line.
        if (extractions.exists(event.documentId(), version)) {
            log.info("skip duplicate extraction documentId={} version={}",
                    event.documentId(), version);
            return;
        }

        var result = optiScan.extract(event.storageKey());

        // The read above can lose a race. The index is what actually guarantees it.
        boolean stored = extractions.insertIfAbsent(
                event.documentId(), version, result.payload(), result.confidence());

        if (!stored) {
            log.info("lost insert race, another worker stored documentId={}", event.documentId());
            return;
        }

        events.send(Topics.DOCUMENT_EXTRACTED, toExtracted(event, result));
    }
```

Also raise `max.poll.interval.ms` past OptiScan's p99, or move the vendor call off the
poll thread. Otherwise you have fixed the duplicate and left the rebalance loop running,
which will bite you in Phase 7.

```yaml
spring:
  kafka:
    consumer:
      max-poll-interval-ms: 300000
      max-poll-records: 1
```

`max-poll-records: 1` is deliberate. One slow vendor call should not put four other
documents at risk of redelivery.

There is one more thing to notice, and it is the reason this mission comes before Mission
19. The two extractions on document 779118 had confidence 0.93 and 0.91 on identical
bytes. Same file, same vendor, different answer, and neither score knew it. Hold onto
that.

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

:::commslab
Same fix, four audiences.

#### To Sam

> Upload has four writers, not one. Portal, Bayline's form, the axios retry layer, and
> the document.uploaded consumer. I am putting the key in the endpoint and a unique index
> on `(application_id, doc_type, sha256)` where sha256 is not null. Not backfilling the
> 340k old rows. Anything I am going to break?

He does not need the concept explained. Give him the scope, the constraint you chose, and
one question. He will tell you about the writer you missed.

#### To Janet

> Blast radius: one endpoint in document-service, one new table, two indexes, one consumer
> guard. No changes to application-service or underwriting. Migration is additive and the
> partial index skips the historical nulls, so it builds in about 40 seconds on a copy of
> prod. On call is your team, and the runbook entry is one paragraph: if uploads start
> returning 409, check the reaper job.

She asked who is on call. Answer it before she asks twice, and answer it with a runbook,
not with a promise.

#### To Marcus

> The button was a real 12 percent. The other 88 percent is below the button, in the retry
> layer and in Bayline's form, so we fixed it at the endpoint. Same outcome you wanted,
> and it now also covers the partners.

Do not tell him he was wrong. He was 12 percent right and he moved fast, which is what he
is for. Give him the number and the outcome.

#### To Carla

> You can stop telling people to ignore the extra copies. If a customer still sees two
> after this week, send me the application id and I want to know about it same day, not in
> a monthly export.

She has been absorbing this failure with her own labor for years. Say the part where she
gets to stop. Then ask for the thing you actually need, which is a fast signal instead of
a slow one.
:::

## Practice

Different domain, same skill. Write your answer before you open the notes.

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

The lesson in one sentence: make the write path idempotent at the write, define your
uniqueness rule in words before you write code, and count the entrances before you
declare it fixed.
