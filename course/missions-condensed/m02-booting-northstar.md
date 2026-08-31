---
id: M02
slug: booting-northstar
title: Booting Northstar
subtitle: >-
  Bring the system up on your laptop and take the tour. You will not understand
  it. That is expected.
phase: 0
order: 2
duration: 150
difficulty: 2
lab: true
status: complete
objectives:
  - Bring the Northstar lab up and confirm every service is actually healthy
  - Map services to the data they own by observation instead of documentation
  - Find and record a place where the API docs and the API disagree
  - Write down what you do not understand instead of guessing at it
concepts:
  - lab setup
  - system tour
  - API contracts
  - documentation drift
competencies:
  - architecture
  - debugging
  - discovery
prereqs:
  - M01
condensed: true
durationCondensed: 60
---
## Where you are

It is Friday morning. Priya gave you read-only repo access at 6:40 AM. Coffee with Sam
is Tuesday. The kickoff call is Tuesday too. You have three days to stop being someone
who has never seen the system.

Your goal today is not to understand everything. It is to ask a specific question on
Tuesday instead of a vague one.

## The request

:::evidence{type=slack label="DM from Priya Raghunathan, Friday 6:41 AM"}
```text
Priya:  repo access is in. read only for now, we can talk about write
        access after you've met Janet.

Priya:  make bootstrap in lab/ should come up clean. it does on my
        machine and on Sam's.

Priya:  api docs are in confluence, link below. fair warning, some of
        it is old.

You:    how old

Priya:  the auth section is current.
```
:::

"The auth section is current" answers a question she did not answer. Write that down.

Sam's advice: curl first. The docs say what the team meant. The running service says
what shipped.

## Service map

| Port | Service | Owns (per Sam) |
| --- | --- | --- |
| 8081 | application-service | applicants, applications, tenants |
| 8082 | document-service | uploads, OCR |
| 8083 | underwriting-service | decisions, policy, revenue |
| 8084 | fraud-service | fraud scoring |
| 8000 | ai-service | nothing yet (yours) |

Three tenants share the system: `NSC_DIRECT`, `BAYLINE`, and `CASCADE`. Every API call
needs an `X-Tenant-Id` header.

## Bring the lab up

You need Docker, Java 21, and Maven. See [Setting Up the Lab](/reference/lab-setup).

Use **`make bootstrap`**, not `make up` alone. `make up` starts Docker but leaves the
database empty. `make bootstrap` runs migrations and loads seed data.

**Step 1: database**

```bash
cd lab
make bootstrap
```

Check it worked:

```bash
docker compose ps
docker compose exec postgres psql -U northstar -d northstar \
  -c "select count(*) from northstar.applications;"
```

You want six containers running and **1200** applications.

**Step 2: build Java services (once per clone)**

```bash
make apps-build
```

**Step 3: start the two services you will curl**

Open two more terminals. Leave Docker running.

Terminal 2:

```bash
cd lab
make run-application
```

Terminal 3:

```bash
cd lab
make run-underwriting
```

Wait until each logs port **8081** or **8083**. Then run the curls below.

Application IDs in the seed are **1 through 1200**. The examples use **8** and **1130**.

## Evidence

Read what Confluence claims. Then curl what the service returns.

### 1. Application lookup (port 8081)

:::evidence{type=schema label="Confluence: Application API v1, last edited 2022-08-19"}
```text
GET /api/v1/applications/{id}

Required header: X-Tenant-Id (tenant code)

Response:
{
  "applicationId": integer,
  "applicantId": integer,
  "product": string,
  "amountRequested": decimal,
  "status": string,
  "submittedAt": string (ISO-8601),
  "customerId": string
}
```
:::

:::evidence{type=http label="application-service, application 8"}
```bash
curl -s localhost:8081/api/v1/applications/8 \
  -H 'X-Tenant-Id: NSC_DIRECT' | jq
```
```json
{
  "applicationId": 8,
  "applicantId": 8,
  "product": "EQUIPMENT",
  "amountRequested": 620000.00,
  "status": "FUNDED",
  "submittedAt": "2026-02-02T11:42:31.353012Z",
  "decidedAt": "2026-02-09T21:57:22.316167Z",
  "customerId": "NSC-DIRECT",
  "createdAt": "2026-01-28T10:22:38.507180Z",
  "updatedAt": "2026-02-11T20:29:02.493478Z"
}
```
:::

Core fields match. The response also has `decidedAt`, `createdAt`, and `updatedAt`, which
are not in the schema. Good row for "docs and reality mostly agree."

### 2. Revenue summary (port 8083)

:::evidence{type=schema label="Confluence: Underwriting API v1, revenue-summary"}
```text
GET /api/v1/applications/{id}/revenue-summary

Response:
{
  "applicationId":  integer,
  "monthlyRevenue": decimal,
  "monthsAnalyzed": integer
}

Errors: 404 if no bank data is linked.
```
:::

:::evidence{type=http label="underwriting-service, revenue-summary, application 8"}
```bash
curl -s localhost:8083/api/v1/applications/8/revenue-summary \
  -H 'X-Tenant-Id: NSC_DIRECT' | jq
```
```json
{
  "applicationId": 8,
  "avgMonthlyRevenue": 1068698.91,
  "revenue": null,
  "monthsAnalyzed": 3,
  "calculatedAt": "2026-08-27T19:31:08.118086Z",
  "calcVersion": "v2"
}
```
:::

The docs say `monthlyRevenue`. The API returns `avgMonthlyRevenue`. A client built from
the docs would read `undefined`. There is also an undocumented `revenue` field. It is
null on every id you try.

### 3. Bank transactions (port 8083)

:::evidence{type=schema label="Confluence: Underwriting API v1, bank-transactions"}
```text
GET /api/v1/applications/{id}/bank-transactions

Response:
{
  "applicationId": integer,
  "transactions": [
    { "postedDate": date, "description": string, "amount": decimal }
  ]
}

Errors: 404 when no bank statements are linked.
```
:::

:::evidence{type=http label="underwriting-service, bank-transactions, application 8"}
```bash
curl -s localhost:8083/api/v1/applications/8/bank-transactions \
  -H 'X-Tenant-Id: NSC_DIRECT' | jq -r '.transactions[] | "\(.postedDate)  \(.description)  \(.amount)"'
```
```text
2025-11-01  STRIPE PAYOUT  68422.40
2025-11-02  COMMERCIAL RENT ACH ****8079  -6907.53
... 80 more rows ...
```
```bash
curl -s localhost:8083/api/v1/applications/8/bank-transactions \
  -H 'X-Tenant-Id: NSC_DIRECT' \
  | jq '[.transactions[] | select(.amount > 0) | .amount] | add'
```
```text
3206096.73
```
```text
sum of credits: 3206096.73   /  3 months  =  1068698.91
```
:::

Shape matches the docs. Application **8** has **82** rows. Revenue sums credits only,
then divides by 3.

### 4. No bank data: CASCADE application 1130 (port 8083)

Docs say **404** when nothing is linked. Try application **1130** with tenant `CASCADE`.

:::evidence{type=http label="revenue-summary, application 1130, no data"}
```bash
curl -s localhost:8083/api/v1/applications/1130/revenue-summary \
  -H 'X-Tenant-Id: CASCADE' | jq
```
```json
{
  "applicationId": 1130,
  "avgMonthlyRevenue": 0.00,
  "revenue": null,
  "monthsAnalyzed": 3,
  "calculatedAt": "2026-08-27T19:40:31.475526Z",
  "calcVersion": "v2"
}
```
:::

:::evidence{type=http label="bank-transactions, application 1130, no data"}
```bash
curl -s localhost:8083/api/v1/applications/1130/bank-transactions \
  -H 'X-Tenant-Id: CASCADE' | jq
```
```json
{
  "applicationId": 1130,
  "transactions": []
}
```
:::

HTTP **200** both times, not 404. Use one of these for your fourth table row.

## Questions to carry forward

Do not answer these yet. Write them down.

- Is `avgMonthlyRevenue` the number underwriters actually use?
- What is `revenue` for, and why is it always null?
- What does `calcVersion: "v2"` mean?
- Why does `customerId` use a different format than the header?

## Your task

:::task{time="60 min"}
Produce one page called "observed versus documented." One page.

Four columns: endpoint, what the docs claim, what the endpoint returned, and what a
client written from the docs would do. Cover **at least four endpoints** from this
mission. Use this checklist:

| # | Endpoint | Port | Example curl |
| --- | --- | --- | --- |
| 1 | `GET /api/v1/applications/{id}` | 8081 | application **8**, `X-Tenant-Id: NSC_DIRECT` |
| 2 | `GET /api/v1/applications/{id}/revenue-summary` | 8083 | application **8** |
| 3 | `GET /api/v1/applications/{id}/bank-transactions` | 8083 | application **8** |
| 4 | `GET /api/v1/applications/{id}/revenue-summary` **or** `.../bank-transactions` | 8083 | application **1130**, `X-Tenant-Id: CASCADE` |

At least one row must be a case where the docs and reality **agree** (or mostly agree).
Endpoints **1** and **3** on application **8** are the easiest fits. Endpoints **2**
and **4** are where the Confluence page is wrong or incomplete.

Add a short section at the bottom titled "questions, not conclusions." Every item is
phrased as a question, and every question names the person most likely to know.

Save it as `customers/northstar/system-observations.md`. Create the folder if you
have not already (`mkdir -p customers/northstar`). A blank table lives in
`customers/northstar/system-observations.template.md`. Do not send your page to anyone
yet.
:::

## Stop and think

:::stopandthink
Before you read on:

1. You found a documented field that does not exist. Who do you tell, and when?
2. Is this a bug in the endpoint or a bug in the docs? How would you decide?
3. `revenue` is null on every row you checked. Name three explanations that are all
   consistent with what you have seen.
4. You have read-only access. What is the first thing you would do if you had write
   access, and why is it good that you do not?

Two minutes, in writing.
:::

## One line to remember

:::judgment
**The docs say what the team intended. The running system says what they shipped. The
gap between them shows where attention ran out.**

Curl first. The endpoint cannot be wrong about itself.

You will find real problems today. Do not send a bug list on Friday. Ask Sam on Tuesday
in a coffee, one question at a time. A defect you understand the history of is worth
more than a list of complaints from a stranger.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You are three days into an engagement with a healthcare claims clearinghouse. They
process claims from small clinics and forward them to payers. Their integration guide,
last updated two years ago, documents the endpoint below. You send four real claims from
staging and compare the responses to that contract.

**Documented contract (integration guide, 2024)**

```text
POST /v2/claims/validate

Request:
  { "claimId": string, "payerId": string, "lines": [...] }

Response:
  {
    "claimId": string,
    "valid": boolean,
    "errors": [ { "code": string, "message": string } ]
  }

Semantics: a claim with valid=true is accepted by the payer.
```

**Observed responses (four claims from staging)**

```json
{"claimId":"CLM-88120","valid":true,"errors":[],"warnings":[{"code":"W41","message":"NPI not found in payer roster"}]}
{"claimId":"CLM-88121","valid":true,"errors":[]}
{"claimId":"CLM-88122","valid":false,"errors":[{"code":"E12","message":"invalid date of service"}]}
{"claimId":"CLM-88123","valid":true,"errors":[],"warnings":[{"code":"W41","message":"NPI not found in payer roster"}]}
```

**What happened eleven days later**

You check their reporting database. **CLM-88120** and **CLM-88123** were both rejected by
the payer. The other two were accepted.

**Your task**

1. List every difference between the documented contract and the observed responses.
2. One of those differences is much more expensive than the others. Which one, and what
   is the cost measured in something a business person cares about?
3. Write the single question you would ask their senior engineer, in one sentence.
4. Write the contract check you would leave behind. Pseudocode is fine.

---

**Notes, after you have written yours**

The differences: an undocumented `warnings` array, and the array is absent rather than
empty when there are no warnings, which is a second problem for any client that does
`response.warnings.length`.

The expensive one is the meaning of `valid`. The docs say a claim with `valid=true` is
accepted by the payer. Two of your four `valid=true` claims were rejected. So `valid`
means "passed our syntax checks," and the `W41` warning about the NPI roster is the part
that actually predicts rejection. A warning that predicts rejection is not a warning.

The cost is measured in days and rework, not in fields. A claim rejected by the payer
eleven days later has to be corrected and resubmitted, the clinic does not get paid, and
somebody at the clinic calls support. If W41 predicts rejection with any reliability,
the clearinghouse is currently telling clinics "you are fine" and then failing them a
week and a half later. Go measure the rejection rate for claims with W41 versus without
before you say another word about it, because that number is either a small
documentation issue or the whole engagement.

Your one question to their engineer: "Does `valid: true` mean we passed your checks, or
that the payer will accept it?" Not "your docs are wrong." The docs being wrong is your
conclusion. The definition of `valid` is his knowledge.

The check you leave behind records the field set, asserts `warnings` is present as an
array even when empty (which is a request, not an assertion, until they change it), and
logs the W41 rate per payer per day so the correlation becomes visible to them without
you in the room.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
