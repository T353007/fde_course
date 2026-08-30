---
id: M02
slug: booting-northstar
title: Booting Northstar
subtitle: Bring the system up on your laptop and take the tour. You will not understand it. That is expected.
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
concepts: [lab setup, system tour, API contracts, documentation drift]
competencies: [architecture, debugging, discovery]
prereqs: [M01]
---

## Where you are

It is Friday morning. Priya gave you read-only access to the monorepo at 6:40 AM,
which tells you something about her week. Coffee with Sam is Tuesday. The kickoff call
is Tuesday too, which means you have three days to stop being a person who has never
seen the system.

Your goal today is not to understand Northstar. It is to be able to ask a specific
question on Tuesday instead of a general one.

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

"The auth section is current" is a complete answer to a question she did not answer.
Write that down.

## The conversation

Sam agreed to walk you through it on a Slack huddle. He talks the way he writes, which
is not much and never twice.

:::dialogue{title="Slack huddle with Sam Ortiz, Friday 10:00 AM"}
**Sam:** Did it come up?

**You:** Infra is up and seeded. I'm starting the Java services next.

**Sam:** Good. Faster than prod.

**You:** Give me the map. What owns what?

**Sam:** Four Java services. Application service on 8081 owns applicants,
applications, tenants. Document service on 8082 owns uploads and OCR. Underwriting on
8083 owns decisions and policy. Fraud on 8084 is Ada's.

**You:** And the AI service on 8000?

**Sam:** Empty. That is yours.

**You:** What is the oldest?

**Sam:** Application service. 2014. It has 2023 patches in it.

*He does not elaborate.*

**You:** Postgres, Kafka, Redis, MinIO. What is Redis actually for?

**Sam:** Session cache. And two other things nobody remembers agreeing to.

**You:** Vendors?

**Sam:** All stubbed on 8090. OptiScan for OCR, Ledgerlink for bank data, Corveil for
credit, Sentinel for fraud, LoanCore for servicing. LoanCore is SOAP.

**You:** In 2026.

**Sam:** In 2026.

**You:** Where do I start reading?

**Sam:** Don't read. Curl it. The docs describe what we meant.
:::

That last line is the mission. He is not being cynical. He is telling you the cheapest
way to learn a system you have three days with.

## What you know about the system

This is what you can confirm from `docker compose ps` and nothing else. Ownership comes
from Sam, so treat it as a claim, not a fact.

| Port | Thing | Owns, per Sam |
|---|---|---|
| 8081 | `application-service` | applicants, applications, tenants |
| 8082 | `document-service` | uploads, OCR, object storage |
| 8083 | `underwriting-service` | decisions, policy, revenue |
| 8084 | `fraud-service` | fraud scoring, vendor calls |
| 8000 | `ai-service` | nothing yet |
| 5173 | `reviewer-portal` | the screen underwriters use (not in the default lab yet) |
| 5432 | PostgreSQL 16 | schema `northstar` |
| 9092 | Kafka | five topics |
| 6379 | Redis | sessions, and two other things |
| 9000 | MinIO | uploaded documents |
| 8090 | vendor stubs | six fake vendors |
| 8099 | scenario control | lets you break the vendors on purpose |

Three tenants share all of it: `NSC_DIRECT`, `BAYLINE`, and `CASCADE`. Northstar
white-labels its platform to two partner brands, which is where the multi-tenancy comes
from. Every request carries an `X-Tenant-Id` header.

## Bringing it up

First time on this machine? You need **Docker**, **Java 21**, and **Maven**. See
[Setting Up the Lab](/reference/lab-setup) for install checks.

This mission needs the database **and** two Java services (`application-service` on
8081, `underwriting-service` on 8083). Use **`make bootstrap`**, not `make up` alone.
`make up` starts Docker and runs migrations but leaves the database empty. `make bootstrap`
does `make up` and `make seed` in order.

### Step 1 — Database and infrastructure

From the repo root:

```bash
cd lab
make bootstrap
```

That builds the vendor images, starts six infra containers, runs Flyway migrations, and
loads seed data. It takes a few minutes the first time while Docker pulls images.

Check that it worked:

```bash
docker compose ps
docker compose exec postgres psql -U northstar -d northstar \
  -c "select count(*) from northstar.applications;"
```

You want **six** containers running (`northstar-postgres`, `northstar-redis`,
`northstar-kafka`, `northstar-minio`, `northstar-wiremock`,
`northstar-scenario-control`) and a row count of **1200**.

If something fails, run `make doctor` from `lab/` and read the message. Port 5432
already in use is common; see [lab-setup](/reference/lab-setup).

### Step 2 — Build the Java services (once per clone)

Still in `lab/`:

```bash
make apps-build
```

### Step 3 — Start the two services this mission curls

Open **two more terminals**. Leave Docker running.

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

Wait until each one logs that it started on port **8081** or **8083**. Then run the
curl commands below.

:::note{label="Extra: commands and profiles"}
- **`make up`** then **`make seed`** is the same as **`make bootstrap`**, just split
  into two steps.
- **`make up PROFILE=full`** adds Docker *placeholders* for the Java services. They do
  not answer API calls. For Mission 02, run the real jars with `make run-application`
  and `make run-underwriting` as above.
- Application IDs in the seed are **1 through 1200**. The examples below use **8** and
  **1130**; any id in that range works for exploration.
:::

Seed load summary (your `make bootstrap` output should look like this):

```text
Seed loaded.
 applicants   |  1200
 applications |  1200
 events       | 17400
 transactions | 61912
```

There are 1,200 applicants and 1,200 applications, one per applicant. `application_events`
has 17,400 rows, about 14 events per application on average. Do not chase that today.
Put it on a list.

## Evidence

Start with one application. Pick any id in range.

:::evidence{type=http label="application-service, port 8081"}
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

The Confluence page for application lookup (same wiki, same vintage):

:::evidence{type=schema label="Confluence: Application API v1, last edited 2022-08-19"}
```text
GET /api/v1/applications/{id}

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

For application **8**, the core fields above match what you curled. The response also
includes `decidedAt`, `createdAt`, and `updatedAt`, which are not in that schema. That
is a good candidate for the row where **docs and reality mostly agree**.

Note that `customerId` is `"NSC-DIRECT"` with a hyphen, while the header you sent was
`NSC_DIRECT` with an underscore. Both appear to work. Add it to the list.

Now the interesting one. Underwriting exposes a revenue summary, and the Confluence page
documents it like this.

:::evidence{type=schema label="Confluence: Underwriting API v1, last edited 2022-08-19"}
```text
GET /api/v1/applications/{id}/revenue-summary

Returns the applicant's monthly revenue as computed from linked bank
accounts.

Response:
{
  "applicationId":  integer,
  "monthlyRevenue": decimal,   // operating revenue per month, USD
  "monthsAnalyzed": integer
}

Errors: 404 if no bank data is linked.
```
:::

Here is what it actually returns.

:::evidence{type=http label="underwriting-service, port 8083"}
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

`calculatedAt` is the request time. Yours will differ. The other fields should match
after a fresh `make bootstrap`.

Three differences, and they are not the same kind of difference.

The documented field `monthlyRevenue` does not exist. The real field is
`avgMonthlyRevenue`. Any client written from the docs would read `undefined` and, in
JavaScript, probably render a blank.

There is an undocumented field called `revenue`. It is null here. Try five more ids and
it is null in all of them.

```bash
for id in 8 17 20 33 37; do
  curl -s localhost:8083/api/v1/applications/$id/revenue-summary \
    -H 'X-Tenant-Id: NSC_DIRECT' | jq -c '{id: .applicationId, revenue, avgMonthlyRevenue}'
done
```

```text
{"id":8,"revenue":null,"avgMonthlyRevenue":1068698.91}
{"id":17,"revenue":null,"avgMonthlyRevenue":46106.67}
{"id":20,"revenue":null,"avgMonthlyRevenue":34101.19}
{"id":33,"revenue":null,"avgMonthlyRevenue":63130.65}
{"id":37,"revenue":null,"avgMonthlyRevenue":97949.57}
```

And there are two fields nobody documented at all: `calculatedAt` and `calcVersion`.
`calcVersion` says `"v2"`.

While you are here, look at what the number is built from.

:::evidence{type=http label="underwriting-service, transactions behind that number"}
```bash
curl -s localhost:8083/api/v1/applications/8/bank-transactions \
  -H 'X-Tenant-Id: NSC_DIRECT' | jq -r '.transactions[] | "\(.postedDate)  \(.description)  \(.amount)"'
```
```text
2025-11-01  STRIPE PAYOUT  68422.40
2025-11-02  COMMERCIAL RENT ACH ****8079  -6907.53
2025-11-03  us foods ach debit  -40539.50
2025-11-05  COMMERCIAL RENT ACH 11524334  -61598.95
2025-11-06  MERCHANT BANKCD DEP ****6677  162245.11
... 77 more rows ...
```
```bash
# credits only — what the revenue number actually sums
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

Confluence on bank transactions (same Underwriting API v1 page):

:::evidence{type=schema label="Confluence: bank-transactions, last edited 2022-08-19"}
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

For application **8**, the shape matches: `applicationId` plus a `transactions` array of
`postedDate`, `description`, and `amount`. That is your second **mostly agrees** row if
you need one besides application lookup.

You do not know enough yet to say whether 1,068,698.91 is right. Keep it. The endpoint
returns **82** rows for application 8. Most of them are debits. The revenue number
ignores debits and adds every credit, then divides by 3.

One more thing. Check the terminal where `make run-underwriting` is running.

:::evidence{type=log label="make run-underwriting, startup excerpt"}
```text
INFO  c.n.u.UnderwritingServiceApplication - Starting UnderwritingServiceApplication v11.4.2-SNAPSHOT using Java 21...
INFO  o.s.b.w.embedded.tomcat.TomcatWebServer  - Tomcat started on port 8083 (http)
INFO  c.n.u.UnderwritingServiceApplication - Started UnderwritingServiceApplication in 2.8 seconds
```
:::

There is no feature-flag loader in the logs. The flags live in
`lab/northstar/underwriting-service/src/main/resources/application.yml`:

```yaml
northstar:
  features:
    USE_NEW_REVENUE_CALC_V2_TEMP: false
    CASCADE_OVERLAY_ENABLED: true
```

`USE_NEW_REVENUE_CALC_V2_TEMP` is **false** by default. The revenue-summary response
still says `"calcVersion": "v2"`. Those two facts disagree. You have no idea which one
the decision engine actually uses. That is fine. Note them and move on.

### Fourth endpoint: CASCADE application 1130 (no bank data)

`CASCADE` tenant, application **1130**. Same paths as endpoints 2 and 3, but the seed
has **no** bank transactions for this application. Confluence says **404** when nothing
is linked. See what you get.

:::evidence{type=http label="underwriting-service, port 8083 — revenue-summary, no data"}
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

:::evidence{type=http label="underwriting-service, port 8083 — bank-transactions, no data"}
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

HTTP **200** both times, not 404. `revenue-summary` returns `0.00`; `bank-transactions`
returns an empty array. Use **one** of these for your fourth table row (either is valid;
the other is optional extra credit).

## What you do not know

Keep this list in a file. It is the most valuable document you will produce this week.

- Is `avgMonthlyRevenue` the number underwriters actually use?
- What is `revenue` for, and why is it always null?
- What does `calcVersion: "v2"` mean, and what was v1?
- What turns `USE_NEW_REVENUE_CALC_V2_TEMP` on or off, and who last touched it?
- Why does `customerId` use a different tenant format than the header?
- Which of the 1,200 applications belong to `BAYLINE` and `CASCADE`?
- Who reads the Confluence page? If nobody, why is it still linked in onboarding?

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

## Working through it

### The wrong turn: the bug list

The natural move on Friday afternoon is to write it all up and send it. You found nine
things in four hours. That is a good afternoon, and Priya asked you to look.

Here is what happens if you send it.

:::evidence{type=slack label="#northstar-ai, Friday 4:50 PM"}
```text
You:     First pass on the API surface. 9 issues, worst first:
You:     1. revenue-summary documents monthlyRevenue, endpoint returns
            avgMonthlyRevenue. Any client from docs gets undefined.
You:     2. undocumented `revenue` field, null on every row sampled
You:     3. customerId format inconsistent with X-Tenant-Id
         ...

Janet:   Tomás, can you confirm 1 and 3?

Tomás:   on it

Sam:     1 and 3 are known

Janet:   known where
```
:::

Tomás spent three hours on Monday confirming two things Sam already knew. Janet learned
that her team's known issues are not written down anywhere, which is true and not
something she wanted to learn from a consultant in a public channel in week one. And
your nine items are now a list of complaints from an outsider rather than a set of
questions.

The cost is not the three hours. The cost is that Janet's first data point about you is
"generates work for my team." She is the person whose team has to own whatever you
build. `CANON` gives her one line and she means it: who is on call for that.

### What to do instead

Nothing, until Tuesday. Then ask Sam, in the coffee you already scheduled, in this
order:

> The revenue summary endpoint returns `avgMonthlyRevenue`. The docs say
> `monthlyRevenue`. Which one is right?

That question has a correct answer and Sam knows it. It also contains no accusation and
no proposed fix.

The answer, when you ask on Tuesday:

:::dialogue{title="Coffee with Sam, Tuesday 8:15 AM"}
**You:** Docs say `monthlyRevenue`. Endpoint says `avgMonthlyRevenue`.

**Sam:** Endpoint is right. Docs were written before the rename.

**You:** When was the rename?

**Sam:** 2019. Maybe 2020.

**You:** And `revenue`? It is null on everything I sampled.

*Sam says nothing for a moment.*

**Sam:** ...Ah. So you found that.

**You:** Is it dead?

**Sam:** It is not dead. It has never been populated. There was going to be a second
number.

**You:** A second number.

**Sam:** Ask me again after you have talked to Renee.

**You:** What about `USE_NEW_REVENUE_CALC_V2_TEMP`?

**Sam:** Not today.
:::

He did not refuse. He sequenced you. Two of your questions are about a thing you cannot
understand until you have met an underwriter, and he knows that better than you do.

### Why the docs are wrong in this specific way

Docs drift in a pattern, and the pattern is useful.

A field rename that nobody propagated means the docs were written once, as a
deliverable, and never treated as code. If the docs lived in the repo next to the
controller, the rename would have shown up in a diff. They live in Confluence, so it
did not.

An undocumented field that is always null means somebody added a column and a getter in
anticipation of a decision. The decision did not come. The field stayed. This is the
single most common shape of dead weight in an old service, and it is almost never worth
removing, because removing it is a breaking change for a client you cannot find.

`calcVersion` and `calculatedAt` being undocumented means those were added by whoever
built the v2 calculation, and that person was thinking about debugging, not about the
published contract. Which is a compliment to them, honestly.

None of this is Northstar being sloppy. Every one of those changes was correct at the
time and cheap to make. The docs were the only artifact with no test protecting it.

### Turn the observation into a check

An observation you write in a document decays. An observation you write as a test does
not. You have read-only database access but you can run scripts, so write the smallest
possible contract check.

```bash
#!/usr/bin/env bash
# customers/northstar/checks/revenue-summary-contract.sh
# Records what the endpoint returns today, so we notice if it changes under us.
set -euo pipefail

APP_ID="${1:-8}"
BASE="${BASE:-http://localhost:8083}"

body=$(curl -sf "$BASE/api/v1/applications/$APP_ID/revenue-summary" \
  -H 'X-Tenant-Id: NSC_DIRECT')

fields=$(jq -r 'keys_unsorted | join(",")' <<<"$body")
expected="applicationId,avgMonthlyRevenue,revenue,monthsAnalyzed,calculatedAt,calcVersion"

if [[ "$fields" != "$expected" ]]; then
  echo "FAIL field set changed"
  echo "  expected: $expected"
  echo "  actual:   $fields"
  exit 1
fi

if [[ "$(jq -r '.revenue' <<<"$body")" != "null" ]]; then
  echo "NOTICE .revenue is populated for $APP_ID. Someone turned something on."
  exit 2
fi

echo "OK $APP_ID avgMonthlyRevenue=$(jq -r '.avgMonthlyRevenue' <<<"$body") calcVersion=$(jq -r '.calcVersion' <<<"$body")"
```

```text
$ ./checks/revenue-summary-contract.sh 8
OK 8 avgMonthlyRevenue=1068698.91 calcVersion=v2
```

Exit code 2 on a populated `revenue` field is deliberate. You do not know what it means
yet, and "tell me if this changes" is a legitimate thing for a check to do. This file
becomes useful in Phase 2 for a reason you cannot see from here.

## Then this happens

Saturday morning you run the same curls on application **1130** again. You already hit
these for the deliverable if you followed the checklist above. The difference is you
now know why the answer matters.

:::evidence{type=http label="Saturday 9:20 AM — revenue-summary (repeat)"}
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

Zero revenue, but `monthsAnalyzed` still says **3**, and an HTTP 200. The documented
behavior for no bank data is a 404. You get a 200 with a zero.

You already confirmed there are no transactions:

```bash
curl -s localhost:8083/api/v1/applications/1130/bank-transactions \
  -H 'X-Tenant-Id: CASCADE' | jq '.transactions | length'
```

```text
0
```

That is worse than the field rename, and for a reason that has nothing to do with
documentation. A 404 is loud. A `0.00` is a number, and numbers get charted, compared,
and fed into rules. Somewhere in this system there is probably a policy check that reads
`avgMonthlyRevenue` and decides something, and it cannot tell "no data" from "no
revenue." Worse: `monthsAnalyzed: 3` makes it look like three months of history were
reviewed.

Do not fix it. Do not report it as a bug yet. Add one line to your observation page:

> `revenue-summary` returns HTTP 200 with `avgMonthlyRevenue: 0.00` when there is no
> bank data. Docs say 404. Question for Sam: is there a caller that treats 0.00 as a
> real number?

You will find out the answer in Phase 2, and the answer is yes.

:::judgment
**The documentation tells you what the team intended. The running system tells you what
the team shipped. The gap between them is a map of where attention ran out.**

New FDEs read documentation first because it is the polite thing to do and because it
feels like preparation. It is preparation for the wrong exam. Every doc you were given
was written at a moment when someone had time, and the interesting parts of the system
were built at moments when nobody did.

Curl first. The endpoint cannot be out of date about itself.

The second half of this is harder, and it is about restraint. You found nine real
problems in an afternoon. Every instinct says to demonstrate competence by listing
them. But a list of defects from a stranger reads as criticism no matter how you phrase
it, and worse, it burns the finite attention of the two or three people who can actually
explain the system to you. Sam has nine years of context. You get maybe six hours of it
in the first month. Spend those hours on questions whose answers you cannot get any
other way.

A defect you found is worth almost nothing on day three. A defect you understand the
history of is worth a great deal, because history tells you whether it is safe to
change. Those two things are separated by one conversation with the right person, and
you only get that conversation if they think you are trying to learn rather than trying
to audit.
:::

:::commslab
Same nine findings. Three audiences.

#### To Sam, the senior engineer

> Two things I could not work out from curling it. The revenue summary returns
> `avgMonthlyRevenue` where the docs say `monthlyRevenue`, and there is a `revenue`
> field that is null on everything I sampled. Which of those is on purpose?

One question, no fix proposed, treats him as the authority. He will answer both and
then tell you a third thing.

#### To Priya, the CTO

> The stack came up clean on the first try, which is not common. I have a page of
> questions about the API surface rather than a bug list, because I do not know yet
> which of these are known and which are news. Can I walk Sam through it before it goes
> anywhere else?

She warned you the docs were old. Confirming she was right costs you nothing and buys
you the "before it goes anywhere else," which is the actual ask.

#### To Janet, the engineering manager

> I am not going to file tickets against your team from the outside. When I find
> something, I will bring it to Sam or Tomás first and we can decide together whether
> it is worth a ticket.

Janet's fear is a consultant who generates work and leaves. Say the opposite of that
out loud in week one, then behave that way for six weeks.
:::

## Practice

Different system, different industry, same skill.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

You are three days into an engagement with a healthcare claims clearinghouse. They
process claims from small clinics and forward them to payers. Their integration guide,
last updated two years ago, documents this endpoint:

```text
POST /v2/claims/validate

Request:  { "claimId": string, "payerId": string, "lines": [...] }
Response: { "claimId": string, "valid": boolean, "errors": [ {"code": string,
            "message": string} ] }

A claim with valid=true is accepted by the payer.
```

You send four real claims from their staging data and get back:

```json
{"claimId":"CLM-88120","valid":true,"errors":[],"warnings":[{"code":"W41","message":"NPI not found in payer roster"}]}
{"claimId":"CLM-88121","valid":true,"errors":[]}
{"claimId":"CLM-88122","valid":false,"errors":[{"code":"E12","message":"invalid date of service"}]}
{"claimId":"CLM-88123","valid":true,"errors":[],"warnings":[{"code":"W41","message":"NPI not found in payer roster"}]}
```

You then check the outcome of those four claims in their reporting database. CLM-88120
and CLM-88123 were both rejected by the payer eleven days later.

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
