---
id: M08
slug: reading-someone-elses-system
title: Reading Someone Else's System
subtitle: >-
  The architecture diagram is 18 months old and wrong in one way that will cost
  you three weeks if you believe it.
phase: 2
order: 8
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Map an unfamiliar system from evidence instead of from documentation
  - 'Find undocumented call paths using logs, config, and grep'
  - Record how confident you are in every edge on your map
  - Tell the difference between a design document and a description of a system
concepts:
  - architecture archaeology
  - dependency mapping
  - evidence over documentation
  - undocumented integrations
competencies:
  - architecture
  - discovery
  - debugging
prereqs:
  - M07
condensed: true
durationCondensed: 96
---
## Where you are

Discovery is done. You told Dale on the 21st that the nine days live in document intake and rework, not in underwriting, and he took it better than you expected. The first slice is scoped. Now you have to build inside a codebase that three people started in 2013 with eight weeks and about forty engineers have patched since.

## Key artifacts

:::evidence{type=email label="Priya Raghunathan, Monday 8:04 AM"}
```text
Subject: Architecture

Attaching the platform diagram so you don't have to reverse engineer
everything. Sam or Janet can answer questions on the parts that aren't
obvious.

One ask. Before you propose any change that touches underwriting, show me
the blast radius. I don't need a design doc. I need to know what else
moves.

P.
```
:::

:::evidence{type=schema label="northstar-platform-arch.pdf, page 1, transcribed"}
```text
                       [ reviewer-portal :5173 ]
                                 |
                                 v
    [ application-service :8081 ] ---> [ underwriting-service :8083 ]
                 |                                |
                 v                                v
    [ document-service :8082 ]            [ fraud-service :8084 ]
                 |                                |
                 v                                v
          [ OptiScan OCR ]                 [ Sentinel Risk ]

    Kafka: application.submitted, document.uploaded, document.extracted,
           underwriting.decisioned

    Rev 4.2  |  Last updated: 2024-09-30  |  P. Raghunathan
```
:::

:::evidence{type=sql label="psql, layer 1: table ownership by service"}
```sql
-- Every Flyway migration records which module applied it.
SELECT installed_by, count(*) AS migrations, min(installed_on)::date AS first
FROM northstar.flyway_schema_history
GROUP BY 1 ORDER BY 2 DESC;
```
```text
    installed_by     | migrations |   first
---------------------+------------+------------
 northstar_migrator  |         14 | 2019-04-02
(1 row)
```
:::

## Evidence to use

:::evidence{type=email label="Priya Raghunathan, Monday 8:04 AM"}
```text
Subject: Architecture

Attaching the platform diagram so you don't have to reverse engineer
everything. Sam or Janet can answer questions on the parts that aren't
obvious.

One ask. Before you propose any change that touches underwriting, show me
the blast radius. I don't need a design doc. I need to know what else
moves.

P.
```
:::

:::evidence{type=schema label="northstar-platform-arch.pdf, page 1, transcribed"}
```text
                       [ reviewer-portal :5173 ]
                                 |
                                 v
    [ application-service :8081 ] ---> [ underwriting-service :8083 ]
                 |                                |
                 v                                v
    [ document-service :8082 ]            [ fraud-service :8084 ]
                 |                                |
                 v                                v
          [ OptiScan OCR ]                 [ Sentinel Risk ]

    Kafka: application.submitted, document.uploaded, document.extracted,
           underwriting.decisioned

    Rev 4.2  |  Last updated: 2024-09-30  |  P. Raghunathan
```
:::

:::evidence{type=sql label="psql, layer 1: table ownership by service"}
```sql
-- Every Flyway migration records which module applied it.
SELECT installed_by, count(*) AS migrations, min(installed_on)::date AS first
FROM northstar.flyway_schema_history
GROUP BY 1 ORDER BY 2 DESC;
```
```text
    installed_by     | migrations |   first
---------------------+------------+------------
 northstar_migrator  |         14 | 2019-04-02
(1 row)
```
:::

:::evidence{type=schema label="underwriting-service/src/main/resources/application.yml, lines 38 to 58"}
```yaml
northstar:
  underwriting:
    min-monthly-revenue: 15000
    dscr-floor: 1.25
  vendors:
    corveil:
      base-url: ${CORVEIL_URL:http://vendor-stubs:8090/corveil}
      connect-timeout-ms: 2000
      read-timeout-ms: 45000
    optiscan:
      base-url: ${OPTISCAN_URL:http://vendor-stubs:8090/optiscan}
      api-key: ${OPTISCAN_API_KEY:}
      connect-timeout-ms: 2000
      read-timeout-ms: 30000
      # CX-4471 re-extraction. temporary, remove after Q1 2022.
      reextract-enabled: ${REEXTRACT_ENABLED:true}
      reextract-max-per-application: 3
```
:::

:::evidence{type=log label="grep session, lab/northstar"}
```text
$ grep -rn --include=*.java --include=*.yml -i optiscan . | grep -v /test/

./document-service/src/main/resources/application.yml:34:      base-url: ${OPTISCAN_URL:...}
./document-service/src/main/java/com/northstar/document/ocr/OptiScanClient.java:28:public class OptiScanClient {
./document-service/src/main/java/com/northstar/document/ocr/OptiScanClient.java:41:    private final String optiscanBaseUrl;
./document-service/src/main/java/com/northstar/document/ocr/ExtractionOrchestrator.java:57:        OptiScanResponse res = optiScanClient.extract(req);
./underwriting-service/src/main/resources/application.yml:47:      base-url: ${OPTISCAN_URL:...}
./underwriting-service/src/main/java/com/northstar/underwriting/reextract/ReExtractionClient.java:33:public class ReExtractionClient {
./underwriting-service/src/main/java/com/northstar/underwriting/reextract/ReExtractionClient.java:52:        return optiscan.postForObject(url, req, OptiScanResponse.class);
```
:::

:::evidence{type=log label="vendor stub access log, Monday afternoon"}
```text
2026-03-23T14:02:11.334Z INFO optiscan-stub POST /optiscan/v2/extract 200 1840ms
    ua="northstar-document-service/2.4.1"    trace=7f21a0 doc=DOC-88213
2026-03-23T14:02:19.006Z INFO optiscan-stub POST /optiscan/v2/extract 200 2210ms
    ua="northstar-underwriting-service/1.9.7" trace=7f21a0 doc=DOC-88213
2026-03-23T14:07:44.918Z INFO optiscan-stub POST /optiscan/v2/extract 200 1975ms
    ua="northstar-underwriting-service/1.9.7" trace=7f21a0 doc=DOC-88213
```
:::

## Your task

:::task{time="120 min"}
Build a dependency map of the Northstar platform from evidence. Not a picture. A
table.

One row per edge, with these columns:

| From | To | How | Evidence | Confidence |

Confidence has exactly three values and you must use them honestly:

- **confirmed** means you saw it in traffic. A log line, a trace, a captured request.
- **inferred** means you saw it in code or config but not in traffic.
- **claimed** means a document or a person told you and you have not checked.

Cover all five layers. Data writes, HTTP and SOAP edges, Kafka topics with real
producers and consumers, scheduled jobs, and human steps.

Then write a second short list: every place where your map disagrees with rev 4.2 of
Priya's diagram. Keep it factual. No editorializing about documentation.

Save both as `customers/northstar/dependency-map.md`.
:::

## Stop and think

:::stopandthink
Before you read how this normally goes:

1. You are about to tell the CTO her diagram is wrong. What is the version of that
   sentence that does not make her defensive?
2. The re-extraction path was added for a customer escalation and marked temporary
   four years ago. What is your first instinct, and what is the argument against it?
3. Your first slice touches document extraction. How does a second, undocumented
   caller of the OCR vendor change your estimate?
4. Rule 1 in that README is false. Where else in this codebase would you go check for
   the same kind of false confidence?

Write your answers. Five minutes. Question 4 is the one that pays off.
:::

## One line to remember

:::judgment
**Documentation tells you what someone intended. Evidence tells you what happened.
When they disagree, evidence wins, and they always disagree somewhere.**

The instinct to trust a well-written README is not laziness. It is a reasonable prior.
Most of the time a README is roughly right, and reading one is much faster than
reconstructing a system from traffic. The problem is that the failure is silent and
the wrong parts are not marked. `document-service/README.md` is accurate in every line
except one, and the one it gets wrong is the one that would have shaped your estimate.

The generalizable move is not "never trust docs." It is "record where each fact came
from." Once your map has a confidence column, you have separated the things you would
bet a sprint on from the things you would not, and you can go spend your investigation
time on the second group. That is the whole method. Everything else is grep.

There is one more thing to take from this mission, and it is about people rather than
systems. Sam knew about the re-extraction path the entire time. He did not tell you.
He said "check the underwriting config," which is six words, and he said it in public
in a way that let you find it yourself. That is what a senior engineer at a company
with eleven years of scar tissue does when they are deciding whether you are worth
their time. He gave you a thread. Whether you pull it is the test.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A healthcare billing company, 400 employees. They process claims for outpatient
clinics. You are three days into an engagement to add automated claim scrubbing.

The VP of Engineering gives you a Confluence page titled "Claims Pipeline Overview,"
last edited 14 months ago. It says:

> Claims enter through `intake-api`, are validated by `scrub-service`, and are
> submitted to the clearinghouse by `submit-worker`. All clearinghouse communication
> is owned by `submit-worker`. Rejections return on the `claims.rejected` topic.

What you have access to: the repo, read-only production database, 30 days of
application logs, the cloud provider's billing console, and one hour a week with a
senior engineer who has been there six years.

You also learn, separately, that a biller named Denise "fixes the stuck ones" every
morning before 9 AM.

**Your task**

1. List the first six things you would check, in order, and say what evidence each one
   produces.
2. The doc says `submit-worker` owns all clearinghouse communication. Name three
   places a second caller could be hiding that a code search would miss.
3. What do you ask Denise, and why is she on the architecture map?
4. You get one hour with the senior engineer. Write the four questions you would use
   it on.

---

**Notes, after you have written yours**

The first six checks, roughly in order. Migration history and which database role each
service connects as, because that tells you the real data ownership. Every base URL
and credential in every config file, which finds configured dependencies whether or
not code uses them today. Consumer group lag per topic, which proves who is actually
reading each topic rather than who claims to. The cloud billing console broken down by
service, because egress charges and per-call vendor charges reveal traffic that no
internal log records. Thirty days of logs filtered by outbound user agent. And the
crontab on every host, which is almost never in the repo.

The three hiding places for a second clearinghouse caller. A scheduled job or script
living on a host rather than in version control, which is what bit Northstar in 2023.
A shared library that any service can import, so the call site is in
`submit-worker`'s code but the caller is whichever service pulled the jar. And a
manual or semi-manual path, which is a person with a portal login or a Postman
collection, and which produces real traffic that no code search will ever find.

Denise is the third one. She is not a workaround around the system. As of this
morning, she is part of the system. Ask her what "stuck" means, how she knows a claim
is stuck, exactly what she does about it, how many she handles a day, and what happens
on the day she is out. If her answer includes touching the clearinghouse portal
directly, she is an undocumented edge on your map with a confidence of confirmed, and
your scrubbing project has to account for whatever she is silently correcting.

The four questions for the senior engineer. What broke most recently and why. What is
the oldest thing still running that nobody wants to touch. What was added for one
customer and never removed. And what would you check first if the numbers came out
wrong. Do not ask them to describe the architecture. They will describe the diagram,
because that is the version everyone has agreed to say out loud. Ask about failures
instead, because failures are where the real edges reveal themselves.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
