---
id: M08
slug: reading-someone-elses-system
title: Reading Someone Else's System
subtitle: The architecture diagram is 18 months old and wrong in one way that will cost you three weeks if you believe it.
phase: 2
order: 8
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Map an unfamiliar system from evidence instead of from documentation
  - Find undocumented call paths using logs, config, and grep
  - Record how confident you are in every edge on your map
  - Tell the difference between a design document and a description of a system
concepts: [architecture archaeology, dependency mapping, evidence over documentation, undocumented integrations]
competencies: [architecture, discovery, debugging]
prereqs: [M07]
---

## Where you are

Discovery is done. You told Dale on the 21st that the nine days live in document
intake and rework, not in underwriting, and he took it better than you expected. The
first slice is scoped. Now you have to build inside a codebase that three people
started in 2013 with eight weeks and about forty engineers have patched since.

It is Monday. You have the repo, a laptop with `make up` running, and a PDF from
Priya.

## The request

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

The diagram is clean. Seven boxes, arrows between them, a legend. Someone spent real
time on it.

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

Look at the date. September 2024. That is 18 months ago. Everything on this page was
true at some point, and Priya is not careless. She drew it, it was correct, and then
the system kept moving and the drawing did not.

## The conversation

:::dialogue{title="Coffee with Sam Ortiz, Monday 10:15 AM"}
**You:** Priya sent me the architecture diagram.

**Sam:** Rev 4.2?

**You:** Rev 4.2.

**Sam:** It's a good diagram.

*He says that in a completely flat voice.*

**You:** Is it right?

**Sam:** It's right about most things.

**You:** Which things is it wrong about?

**Sam:** If I could list them I'd have fixed them.

*He drinks some coffee.*

**Sam:** That's the actual problem. Nobody who works here has the whole picture. I
know the underwriting side. Tomás knows the workers. Bill knows what runs at night.
Priya drew the version she was told about.

**You:** So how do people find out what talks to what?

**Sam:** Something breaks and then we know.
:::

That is not a joke and Sam did not mean it as one. In most companies the dependency
map exists only as a set of scars.

## What you know about the system

You are going to build a map from evidence. Not from the diagram, and not from the
READMEs. Evidence means something the running system produced or something the build
depends on.

There are five layers, and you do them in this order.

**1. The data.** Tables, and which service writes to each one. Data outlives code by
a decade. If two services write the same table, that is a coupling nobody drew.

**2. The edges.** What calls what, over HTTP or SOAP. You find these in config and in
traffic, not in docs. A base URL in an `application.yml` is a dependency even if no
code path currently uses it.

**3. The async paths.** Kafka topics, producers, consumers. These are the edges people
forget, because nothing in the producer's code names the consumer.

**4. The scheduled work.** Cron, batch windows, nightly jobs. Scheduled work is
invisible during the day and load bearing at 2 AM.

**5. The humans.** The manual steps. Someone re-runs a script. Someone copies a
number into a spreadsheet. If a human step is required for the system to be correct,
it belongs on the map.

Data first, because a table tells you the truth about what a service actually owns.
Docs tell you what someone hoped it would own.

## Evidence

Start with layer one. Which service writes which table.

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

One migration user for all fourteen migrations. So the database does not know which
service owns what. That is your first real finding, and it is a bad one. Every service
connects with the same Postgres role, so nothing at the database level stops
`underwriting-service` from writing to `applicants`.

Write that down. You will need it in Phase 5.

Now layer two. The edges live in config.

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

Read that again. The underwriting service has an OptiScan base URL and an OptiScan API
key. On Priya's diagram, OptiScan connects to `document-service` and nothing else.

Confirm it with grep before you believe it.

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

Two services call the OCR vendor. The diagram shows one.

Now go look at traffic, because config proves a path exists and traffic proves it is
used.

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

Same trace ID. Same document. Three extractions, from two different services, eight
seconds and five minutes apart.

## The code

Here is the path the diagram does not have.

```java
package com.northstar.underwriting.reextract;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class ReExtractionClient {

    private final RestTemplate optiscan;
    private final String baseUrl;
    private final boolean enabled;
    private final int maxPerApplication;

    public ReExtractionClient(RestTemplate optiscan,
            @Value("${northstar.vendors.optiscan.base-url}") String baseUrl,
            @Value("${northstar.vendors.optiscan.reextract-enabled}") boolean enabled,
            @Value("${northstar.vendors.optiscan.reextract-max-per-application}") int max) {
        this.optiscan = optiscan;
        this.baseUrl = baseUrl;
        this.enabled = enabled;
        this.maxPerApplication = max;
    }

    /**
     * CX-4471. Underwriters were waiting on the document-service queue to
     * re-run OCR after a rejected page. This calls the vendor inline so the
     * reviewer gets an answer in the same session.
     *
     * Remove once document-service exposes a priority queue.
     */
    public OptiScanResponse reExtract(String documentId, int attempt) {
        if (!enabled || attempt > maxPerApplication) {
            return OptiScanResponse.skipped();
        }
        String url = baseUrl + "/v2/extract";
        OptiScanRequest req = OptiScanRequest.forDocument(documentId);
        return optiscan.postForObject(url, req, OptiScanResponse.class);
    }
}
```

Now the history.

:::evidence{type=log label="git log, underwriting-service/.../reextract/"}
```text
$ git log --oneline -3 -- src/main/java/com/northstar/underwriting/reextract/
9c31ab2 CX-4471: cap re-extraction at 3 per application
4d80f11 CX-4471: allow underwriting to re-run extraction on rejected docs
1a92e07 CX-4471: hotfix, skip document-service for re-extract (queue backed up)

$ git show -s --format='%an  %ad  %s' 1a92e07
Sam Ortiz  Thu Feb 17 22:41:08 2022 -0500  CX-4471: hotfix, skip document-service
```
:::

February 2022, 10:41 PM. A hotfix for one customer escalation, four years ago, marked
temporary in the comment. `reextract-enabled` still defaults to `true`.

And the author is Sam. Which explains why he told you to check the underwriting config
instead of just telling you what was in it.

## The wrong turn

Here is the part that would have cost you three weeks, and it is the most reasonable
mistake in this mission.

Before you found any of the above, you read this.

:::evidence{type=policy label="document-service/README.md"}
```markdown
# document-service

Owns everything about a document: upload, storage, OCR, and extraction.

## Rules

1. All vendor OCR calls go through this service. No other service talks to
   OptiScan directly.
2. Extraction results are published to `document.extracted`. Consumers read
   the topic. They do not call the vendor.
3. If you need a document re-extracted, call
   `POST /v1/documents/{documentId}/extract`.

Last reviewed: 2021-09-30
```
:::

It is a good README. It is specific, it is confident, and it has rules with numbers.
It is also a description of an intention, not a system. Rule 1 was true for about five
months. Then the queue backed up in February 2022 and someone fixed a customer's
problem at 10:41 PM.

Look at the last line. "Last reviewed: 2021-09-30." The hotfix that breaks rule 1
landed four and a half months later. Nobody updated the README, because the person
writing a 10 PM hotfix for an escalation is not thinking about documentation, and
nobody has read that file since.

## What you do not know

- Does the re-extraction path write its result anywhere, or is it used inline and
  thrown away?
- Which extraction does underwriting actually use if both paths ran?
- Are there other callers of OptiScan outside these two services? What about the cron
  jobs?
- How many other "temporary" flags are on in production right now?
- Which parts of Priya's diagram are wrong in ways you have not found yet?

That last question does not have an answer and never will. What you can do is record
how confident you are in each edge, so the next person knows which parts to check.

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

## Working through it

### The map, partially filled

Here is what the first pass looks like. Yours will be longer.

| From | To | How | Evidence | Confidence |
|---|---|---|---|---|
| application-service | `applicants`, `applications` | JDBC write | code, migrations V1 to V2 | confirmed |
| underwriting-service | `decisions` | JDBC write | code, migration V4 | confirmed |
| underwriting-service | `bank_transactions` | JDBC write | code, migration V12 | confirmed |
| document-service | `documents`, `document_extractions` | JDBC write | code, migrations V6, V9 | confirmed |
| underwriting-service | `applications` | JDBC update of `status` | grep, `ApplicationStatusWriter` | confirmed |
| document-service | OptiScan | HTTPS | vendor access log | confirmed |
| underwriting-service | OptiScan | HTTPS | vendor access log, `ReExtractionClient` | confirmed |
| underwriting-service | Corveil | HTTPS | config, no traffic today | inferred |
| application-service | `application.submitted` | Kafka produce | code | confirmed |
| underwriting-service | `application.submitted` | Kafka consume | consumer group lag | confirmed |
| fraud-service | `application.submitted` | Kafka consume | consumer group lag | confirmed |
| document-service | `document.extracted` | Kafka produce | code | confirmed |
| underwriting-service | `document.extracted` | Kafka consume | code | confirmed |
| cron on `ops-1` | `applications` | direct SQL | Bill, crontab | claimed |
| Bill Tran | `fix_stuff.sh` | manual, when it fails | Bill said so | claimed |

Row five is the one people miss. `underwriting-service` writes `applications.status`,
a table `application-service` owns. Two writers, no lock, no ownership boundary. That
is not on any diagram and it is going to matter.

The last two rows are the human layer. Bill runs four cron jobs. Three are documented.
The fourth is `fix_stuff.sh`, and it patches a nightly mismatch nobody has explained
since 2022. He described it as "it's fine, I run it by hand if it fails," which is a
sentence that belongs on an architecture diagram.

### The re-extraction result goes nowhere

You had a question: does the inline path store what it gets back? Check.

:::evidence{type=sql label="psql, extractions per month"}
```sql
SELECT date_trunc('month', created_at)::date AS month, count(*) AS extractions
FROM northstar.document_extractions
WHERE created_at >= '2026-01-01'
GROUP BY 1 ORDER BY 1;
```
```text
   month    | extractions
------------+-------------
 2026-01-01 |        3102
 2026-02-01 |        2988
```
:::

Then you ask Bill for the OptiScan invoice, because vendors count better than we do.

:::evidence{type=slack label="DM with Bill Tran, Tuesday 9:12 AM"}
```text
You:   do we get a usage line on the optiscan invoice

Bill:  yeah, per extraction. january was 4,190

You:   4,190 for january?

Bill:  yep. finance asked about it once. we said volume was up.

You:   was volume up

Bill:  applications were flat. i didn't push it
```
:::

January: 3,102 extractions in the database, 4,190 on the invoice. The gap is 1,088.

The re-extraction path caches its answer in Redis and uses it inline. It never writes
to `document_extractions`. So roughly a quarter of the OCR results the underwriting
service used in January are not in the database at all. If you tried to audit a
decision from January, you could not reconstruct the numbers it was based on.

Write that one down carefully. Doug is going to ask about it in Phase 8.

## Then this happens

Wednesday sync. Before you found the invoice gap, you said this out loud.

:::evidence{type=slack label="#northstar-ai, Wednesday 11:22 AM"}
```text
You:    quick scoping note: OCR has one integration point, it's all
        behind document-service. so swapping our extraction in is
        contained to one service.

Janet:  ok good. i'll pencil it as one sprint.

Marcus: love it 🙌

Sam:    ...

Sam:    check the underwriting config
```
:::

Janet penciled a sprint. That number now exists.

You spend Wednesday afternoon finding out you were wrong, and Thursday morning
correcting it. Two days, plus a correction in the channel where Janet watched a
consultant confidently describe her system incorrectly in week four.

Sam gave you the story at lunch.

:::dialogue{title="Lunch, Thursday"}
**Sam:** We did this in 2023 with the fraud vendor.

**You:** Did what.

**Sam:** Swapped Sentinel for a cheaper one. Everybody agreed there was one caller.
Fraud-service. Clean.

**You:** And?

**Sam:** Three weeks. There was a second caller. It was a cron job that scored
applications that came in overnight, so it only ran when nobody was watching. Numbers
were wrong for eleven days before anyone noticed.

**You:** Why didn't the cron job show up?

**Sam:** It wasn't in the repo. It was a script on a box.

*He shrugs.*

**Sam:** That's why I said check the config. Config lies less than code, and code lies
less than a diagram.
:::

Three weeks. That is the number in the subtitle, and it is not hypothetical. It
happened here, to these people, two years ago.

## The better version

The map is not the deliverable. The map plus the confidence column is the deliverable.

An architecture diagram with no confidence marks makes every edge look equally true.
That is what made rev 4.2 dangerous. The Kafka arrows on it are correct and were
verified. The OptiScan arrow was correct in 2024. Both are drawn in the same weight of
black line, so a reader has no way to tell which one to trust.

When you hand Priya your map, the confirmed rows are a gift and the claimed rows are a
request for help. "Bill runs `fix_stuff.sh` by hand" sitting in a table marked
`claimed` is an invitation for someone who knows to correct you. A diagram never gets
that.

Two more habits worth keeping.

**Check the vendor's numbers against yours.** Vendors bill per call, which means they
count every call, which means their invoice is a more complete call log than your
database. Any gap between what a vendor charged you for and what you recorded is an
undocumented code path. This is the cheapest architecture discovery tool there is and
almost nobody uses it.

**Grep for base URLs, not for class names.** A class can be dead. A configured base
URL with a real API key in it is a live dependency someone is paying for. Start from
config, then confirm in traffic, then read the code last.

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

:::commslab
You have to tell four people that the diagram is wrong. Only one of those
conversations is about the diagram.

#### To Sam

> Found the re-extraction path. It's not writing to `document_extractions`, so about a
> quarter of January's OCR results aren't in the database. Is that known, or did I
> just find something?

Direct, technical, no apology for being wrong on Wednesday. He does not care that you
were wrong. He cares whether you fixed it fast.

#### To Priya, the CTO

> I built a dependency map from logs and config so I'd stop guessing. Two things it
> found that aren't on rev 4.2. Sending it as a table with a confidence column so you
> can see which parts I actually verified and which parts I'm taking on faith.

She drew that diagram. Never say "your diagram is wrong." Say what the map found, and
give her the confidence column so she can see you are not claiming more than you know.
She asked for blast radius. A map with confidence marks is the tool for producing one.

#### To Janet, the engineering manager

> I told you OCR was one integration point on Wednesday. It's two. The second one is
> in underwriting and it bypasses document-service. That changes the estimate and I
> wanted you to hear it from me before you built a sprint on my number.

She is suspicious of consultants who drop a demo and leave. The fastest way through
that is to correct your own number before she finds it. Do not explain why you were
wrong. Say what is true now.

#### To Dale, the CEO

Nothing. Dale does not need to know about this and telling him makes it a problem
instead of a Tuesday. Save your executive airtime for things he can act on.
:::

## Practice

Different industry. Same skill.

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
