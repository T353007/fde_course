---
id: M10
slug: who-owns-the-applicant
title: Who Owns the Applicant
subtitle: The same bakery appears four times with four IDs, and every one of those rows is correct according to somebody.
phase: 2
order: 10
duration: 210
difficulty: 3
lab: true
status: complete
objectives:
  - Tell a duplicate record apart from a distinct entity that looks similar
  - Trace one real world business across four systems that each assign their own ID
  - Explain why merging identity records is a business decision, not a data cleanup
  - Decide who owns a master record when three systems each believe they do
concepts: [identity resolution, data ownership, master data, deduplication risk]
competencies: [architecture, discovery, fintech-judgment]
prereqs: [M09]
---

## Where you are

You are building the first slice. It needs a list of applications with their bank
transactions, and it needs to know which business each application belongs to.

That last part sounds like a foreign key. It is a foreign key. The foreign key is
fine. The problem is what it points at.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 9:48 AM"}
```text
You:    quick one. for the pilot i want to pull the last 12 months of
        applications for one business, so renee and i can look at the
        same statements. any suggestions for a good example?

Renee:  cortland street bakery. marisol reyes. she's applied a few
        times and the statements are messy in a normal way.

You:    perfect, thanks

Carla:  oh cortland. good luck 🙃

You:    ...meaning

Carla:  meaning she calls us about once a quarter asking why we sent
        her two different decisions
```
:::

## The conversation

:::dialogue{title="Ten minutes later, DM with Carla Mendes"}
**You:** Two different decisions for the same business?

**Carla:** Yeah. That happens.

**You:** How often is "happens"?

**Carla:** Couple times a month? Somebody applies, gets declined, applies again
through a different channel, gets a different answer.

**You:** And that is not a bug?

**Carla:** I mean it is, but they're different applications so the system is doing
what it's told.

**You:** What do you tell the customer?

**Carla:** Oh, that. Yeah, we just tell them to resubmit.

*A pause.*

**Carla:** Look, I have a note in my ticket macros about it. It's been there since
2021. I assumed engineering knew.
:::

Nobody in engineering knows. Carla has been absorbing this for five years and
documenting the workaround in a support macro, which is a place no engineer has ever
looked.

## Evidence

Go find the bakery.

:::evidence{type=sql label="psql, find Cortland"}
```sql
SELECT applicant_id, legal_name, dba_name, ein, email, tenant_id,
       created_at::date AS created
FROM northstar.applicants
WHERE legal_name ILIKE '%cortland%' OR dba_name ILIKE '%cortland%'
ORDER BY created_at;
```
```text
 applicant_id |         legal_name         |    dba_name     |    ein     |          email          | tenant_id  |  created
--------------+----------------------------+-----------------+------------+-------------------------+------------+------------
        10428 | CORTLAND STREET BAKERY LLC | Cortland Bakery | 47-2938114 | mreyes@cortlandbake.com | NSC_DIRECT | 2019-06-11
        22910 | Cortland Street Bakery, LLC |                | 472938114  | mreyes@cortlandbake.com | NSC_DIRECT | 2021-02-03
        31877 | Cortland Bakery            |                 | 47-2938141 | orders@cortlandbake.com | NSC_DIRECT | 2023-08-19
        40155 | CORTLAND ST BAKERY LLC     | The Cortland    | 47-2938114 | mreyes@cortlandbake.com | BAYLINE    | 2026-02-28
(4 rows)
```
:::

Four rows. One bakery on Cortland Street in Charlotte. Look at what makes each one
different, because each difference has a separate cause.

**10428** is the original from 2019. Legal name in caps, EIN with a hyphen.

**22910** is the same legal name with a comma and different capitalization, and the
EIN has no hyphen. There is no format rule on the column, so both are stored as typed.

**31877** uses the DBA as the legal name, has a different email, and the EIN is
`47-2938141`. Compare it to `47-2938114`. The last two digits are swapped. That is a
typo, and it means no exact match and no normalized match will ever find it.

**40155** is on `BAYLINE`. The bakery applied through the partner brand in February.
Same EIN as the original, abbreviated name, and a different DBA.

Now check the whole table.

:::evidence{type=sql label="psql, normalized EIN collisions across all applicants"}
```sql
SELECT regexp_replace(ein, '\D', '', 'g') AS ein_norm,
       count(*)                            AS applicants,
       count(DISTINCT tenant_id)           AS tenants
FROM northstar.applicants
WHERE ein IS NOT NULL AND ein <> ''
GROUP BY 1
HAVING count(*) > 1
ORDER BY 2 DESC, 1;
```
```text
 ein_norm  | applicants | tenants
-----------+------------+---------
 472938114 |          3 |       2
 883012447 |          3 |       1
 550119284 |          3 |       1
 611200938 |          2 |       1
 749003318 |          2 |       2
 ...
(118 rows)
```
:::

118 groups. Note that Cortland shows 3 here, not 4, because the typo row is invisible
to this query. Whatever number you produce for "how many duplicates do we have," it is
a floor.

:::evidence{type=sql label="psql, how bad is the EIN column"}
```sql
SELECT count(*)                                            AS applicants,
       count(*) FILTER (WHERE ein IS NULL OR ein = '')     AS missing_ein,
       count(DISTINCT regexp_replace(ein,'\D','','g'))     AS distinct_ein_norm
FROM northstar.applicants;
```
```text
 applicants | missing_ein | distinct_ein_norm
------------+-------------+-------------------
       1043 |         147 |               872
```
:::

147 applicants with no EIN at all. There is no unique constraint on the column and
never has been, which was a deliberate call in 2017: sole proprietors often apply with
an SSN and no EIN, and a NOT NULL UNIQUE constraint would have blocked a real customer
segment on day one. That was a correct decision. Nothing was ever built to handle the
consequence.

## The applications

The rows are only interesting because of what hangs off them.

:::evidence{type=sql label="psql, applications for the four Cortland rows"}
```sql
SELECT ap.applicant_id, ap.application_id, ap.product, ap.status,
       ap.amount_requested, ap.submitted_at::date AS submitted,
       ap.decided_at::date AS decided, ap.customer_id
FROM northstar.applications ap
WHERE ap.applicant_id IN (10428, 22910, 31877, 40155)
ORDER BY ap.submitted_at;
```
```text
 applicant_id | application_id |  product  |  status   | amount_requested | submitted  |  decided   |   customer_id
--------------+----------------+-----------+-----------+------------------+------------+------------+-----------------
        10428 |          10871 | TERM_LOAN | DECLINED  |        120000.00 | 2019-06-14 | 2019-06-27 |
        10428 |          14402 | LOC       | WITHDRAWN |         75000.00 | 2020-03-02 |            | nsc
        22910 |          21188 | TERM_LOAN | FUNDED    |        250000.00 | 2021-02-09 | 2021-02-24 | nsc
        31877 |          33940 | EQUIPMENT | DECLINED  |         64000.00 | 2023-08-22 | 2023-09-01 | northstar
        40155 |          44017 | TERM_LOAN | IN_REVIEW |        180000.00 | 2026-03-16 |            | bayline-partner
(5 rows)
```
:::

Read the `customer_id` column. Blank, `nsc`, `nsc`, `northstar`, `bayline-partner`.
That is a second tenant convention living beside the real one, added at some point by
someone who did not know `tenant_id` existed. Note it, do not fix it, keep moving.

Now the thing that matters. Application 21188 is `FUNDED`. Applicant 22910 has an
active loan. There is a real borrower, a real payment schedule, and a real servicing
record in LoanCore with 22910's details on it.

Any merge that touches 22910 changes the servicing record of a live loan.

## Four systems, four IDs

The Postgres row is one of four places this bakery exists.

| System | Identifier | Assigned by | Used for |
|---|---|---|---|
| `applicants` table | `applicant_id` 10428, 22910, 31877, 40155 | application-service, on submit | Origination |
| Salesforce | Account ID `0018X00002mQZlP` | Sales, on first contact | Pipeline, marketing |
| LoanCore | Borrower number `NSC-0044871` | Servicing, on funding | Payments, payoff, collections |
| Data warehouse | `customer_key` 8842 | Nightly ETL | Reporting, Dale's dashboard |

Four identifiers, four owners, four moments of creation. None of them are wrong.
Salesforce creates a record when a salesperson has a conversation, which can be six
months before an application exists. LoanCore creates a borrower when money moves.
Neither of those events is an application submission.

The warehouse is the interesting one.

:::dialogue{title="Fifteen minutes with Bill Tran, Tuesday"}
**You:** How does the warehouse decide two applicants are the same business?

**Bill:** Email.

**You:** Just email?

**Bill:** Email, then EIN if there's no email match. It was supposed to be the other
way round but EIN was too dirty.

**You:** So two businesses that share an email address become one row.

**Bill:** ...Yeah. Yeah, they would.

*He thinks about it.*

**Bill:** That might be the nightly thing.

**You:** The nightly thing?

**Bill:** There's a mismatch that shows up in the borrower mapping some nights. I have
a script. `fix_stuff.sh`. It's fine, I run it by hand if it fails.

**You:** Since when?

**Bill:** 2022.
:::

Do not chase that yet. Write it down as a hypothesis with a question mark on it: the
nightly mismatch may be the borrower mapping picking a different applicant row when
several match. You do not have evidence, and Bill is not asking you to solve it.

## What you do not know

- Which of the four rows does Salesforce think is the account?
- Does LoanCore's borrower record point at an `applicant_id` at all, or at a name?
- How many of the 118 EIN groups contain a funded loan?
- How many duplicates exist that share no EIN and no email, like the typo row?
- Does anyone at Northstar currently want these merged, or has everyone just adapted?

:::task{time="90 min"}
Produce an identity findings memo, `customers/northstar/applicant-identity.md`.

Three parts.

**1. The evidence.** The four Cortland rows, what makes each one different, and the
cause of each difference. Then the table-wide numbers, with a sentence on why each one
is a floor rather than a count.

**2. A decision table.** One row per Cortland record, with these columns:

| applicant_id | Same legal entity? | Same relationship? | Recommended action | Why | Who has to approve |

Your action options are exactly four: `merge`, `link`, `leave`, `escalate`. Use
`escalate` only when the decision genuinely belongs to someone else, and name them.

**3. A recommendation on ownership.** Answer one question in writing: which system
holds the master record for a business, and does the answer change depending on where
the business is in its lifecycle? Two paragraphs. Take a position.

Do not propose a dedupe job. If you already wrote one, keep it and read on.
:::

:::stopandthink
1. Which of the four rows is a duplicate, and which is something else? Write the
   dividing line you are using as one sentence.
2. Applicant 22910 has a funded loan. What specifically goes wrong if you merge it
   into 10428?
3. Row 40155 is on the `BAYLINE` tenant. Is that a duplicate of the Northstar row, or
   is it a different thing? Argue both sides for one minute each.
4. The warehouse joins on email. Name one situation where that produces a wrong answer
   that nobody would ever notice.

Question 3 is the one people get wrong.
:::

## Working through it

### The wrong turn

The dedupe job takes about an hour to write and it is very satisfying.

You normalize the EIN, group applicants, pick the oldest row in each group as the
survivor, repoint every `applications.applicant_id` at the survivor, and soft delete
the rest. You run it as a dry run against a copy. It resolves 118 groups and collapses
263 applicant rows into 118. You post the plan.

:::evidence{type=slack label="#northstar-ai, Tuesday 3:14 PM"}
```text
You:    dry ran a dedupe on applicants. normalized EIN, oldest row
        survives, repoint applications. 263 rows collapse to 118.
        happy to write the real one.

Marcus: this is great, our data quality has been a mess forever

Janet:  who is on call for that

Ada:    don't run that

Ada:    can you send me the 118 groups

You:    sending

Ada:    ...ok. at least six of those are deliberate. can we talk
```
:::

### Ada explains the part you missed

:::dialogue{title="Ada Nwosu, fraud lead, Tuesday 4:00 PM"}
**Ada:** Look at Cortland. You have four rows. How many businesses is that?

**You:** One. It's one bakery.

**Ada:** Now look at this.

*She runs a query.*

**Ada:** Cortland Street Catering LLC. Different EIN. Same owner, same email. Applied
eleven days after the bakery got declined on the equipment loan.

**You:** So it's the same person applying again as a different entity.

**Ada:** Right. Now, that is completely legal. She may own two real businesses. Lots of
restaurant people do.

**You:** But.

**Ada:** But it is also exactly what it looks like when someone shops a decline. And
either way I need to see both. If you merge on email, they become one customer and I
lose the pattern.

**You:** And if I merge on EIN they stay separate.

**Ada:** They stay separate and I still can't see the link, because nothing records
that they're connected. Right now the only place that link exists is in my head.

*She shrugs.*

**Ada:** Assume the applicant is hostile. Not because they are. Because if your data
model can't represent a hostile one, you'll never find the ones who are.
:::

:::evidence{type=sql label="psql, the same email across different EINs"}
```sql
SELECT applicant_id, legal_name,
       regexp_replace(ein,'\D','','g') AS ein_norm,
       email, created_at::date AS created
FROM northstar.applicants
WHERE email = 'mreyes@cortlandbake.com'
ORDER BY created_at;
```
```text
 applicant_id |          legal_name          | ein_norm  |          email          |  created
--------------+------------------------------+-----------+-------------------------+------------
        10428 | CORTLAND STREET BAKERY LLC   | 472938114 | mreyes@cortlandbake.com | 2019-06-11
        22910 | Cortland Street Bakery, LLC  | 472938114 | mreyes@cortlandbake.com | 2021-02-03
        36002 | CORTLAND STREET CATERING LLC | 815520037 | mreyes@cortlandbake.com | 2023-09-05
        40155 | CORTLAND ST BAKERY LLC       | 472938114 | mreyes@cortlandbake.com | 2026-02-28
(4 rows)
```
:::

The catering company has a different EIN, a different legal entity, and a different
credit profile. In the data warehouse, which joins on email, it is the same customer as
the bakery. Every number Dale looks at that counts customers has been quietly merging
these two since the warehouse was built.

### The cost of the dedupe job

You did not run it. Here is what it would have done anyway, because this is the number
that makes the lesson stick.

:::evidence{type=sql label="psql, EIN groups containing a funded loan"}
```sql
WITH grp AS (
  SELECT regexp_replace(ein,'\D','','g') AS ein_norm, applicant_id
  FROM northstar.applicants
  WHERE ein IS NOT NULL AND ein <> ''
)
SELECT count(DISTINCT g.ein_norm) AS groups_with_funded_loan
FROM grp g
JOIN northstar.applications ap ON ap.applicant_id = g.applicant_id
WHERE ap.status = 'FUNDED'
  AND g.ein_norm IN (SELECT ein_norm FROM grp GROUP BY 1 HAVING count(*) > 1);
```
```text
 groups_with_funded_loan
-------------------------
                      41
```
:::

41 of the 118 groups contain at least one funded loan. Repointing those rows changes
the applicant of record on a live credit obligation. In lending, the borrower on a
funded loan is not a data field. It is a party to a contract. Changing it is not a
migration, it is an amendment, and Doug would need to be in the room before anyone
typed an UPDATE.

The real cost of that Tuesday: about four hours of work you cannot use, a public walk
back, and Janet watching a consultant propose a bulk write to production data in week
four. Ada caught it. If she had been on vacation, Marcus was already enthusiastic and
Janet was one "who is on call" away from letting it through.

### Duplicate, or distinct?

Here is the dividing line, and it is not technical.

A **duplicate** is one real world entity recorded more than once by accident. Same
legal entity, same relationship, no reason for both rows to exist.

A **distinct entity that looks similar** is two real world entities that share
attributes. Same owner, same address, same email, different legal entity. They look
identical to a matching algorithm and they are not the same thing.

A **separate relationship with the same entity** is one legal entity that has more than
one relationship with you. Same business, different tenant, different product line,
different point in time.

Run the four Cortland rows through it.

| applicant_id | Same legal entity? | Same relationship? | Action | Why |
|---|---|---|---|---|
| 10428 | Yes, the bakery | Yes, NSC_DIRECT origination | `leave` as survivor | Oldest, cleanest EIN, no active obligation |
| 22910 | Yes, the bakery | Yes | `link` to 10428, do not merge | Funded loan. Servicing record points here |
| 31877 | Yes, probably | Yes | `escalate` to Renee | EIN typo. Needs a human to confirm it is the same business |
| 40155 | Yes, the bakery | **No.** Different tenant | `link` only | Bayline relationship, separate consent and pricing |
| 36002 | **No.** Catering LLC | No | `leave`, and link as related party | Different entity, same owner. Ada needs the link |

Row 40155 is the one people get wrong. It is the same bakery, so merging feels correct.
It is a Bayline relationship. Bayline has its own pricing, its own agreement with the
applicant, and its own consent to pull credit. Collapsing it into the Northstar row
means a Northstar underwriter can see a Bayline application, which is a tenant
isolation failure that would be reported as a security incident rather than a data bug.

That is the same boundary that breaks in Mission 24, from the other direction.

Notice that nothing in this table says `merge`. Merging destroys information and is
almost never reversible, because the row you deleted took its history with it. Linking
adds information and can be undone with a delete. When the two options are close, take
the reversible one.

## Then this happens

Wednesday, you go looking for how LoanCore knows which applicant a borrower is.

:::evidence{type=http label="LoanCore SOAP response, borrower lookup, trimmed"}
```xml
<GetBorrowerResponse>
  <BorrowerNumber>NSC-0044871</BorrowerNumber>
  <LegalName>CORTLAND STREET BAKERY LLC</LegalName>
  <TaxId>472938114</TaxId>
  <OriginationRef>21188</OriginationRef>
  <Status>ACTIVE</Status>
</GetBorrowerResponse>
```
:::

`OriginationRef` is `21188`. That is the application ID, not the applicant ID.

Which is better than it sounds. An application is immutable once it is decided. An
applicant row is not. By pointing at the application, LoanCore accidentally got the
stable identifier, and whoever built that integration in 2016 either knew what they
were doing or got lucky.

But `LegalName` is a copy, frozen at funding. If you edit `applicants.legal_name` today
to clean it up, LoanCore keeps the 2021 spelling forever and the two systems disagree
silently. Every downstream reconciliation that compares names by string will start
producing a mismatch every night.

Which is very likely what `fix_stuff.sh` has been patching since 2022.

You still cannot prove that. Write it as a hypothesis with the evidence attached, and
give it to Bill. It is his script.

## The better version

The recommendation is three sentences long and none of them involve deleting a row.

**Do not merge anything.** Not now, and probably not in this engagement. There is no
business owner for the merge decision today, and a technical team cannot self-assign
one.

**Add a link, not a survivor.** A separate table that records "these two applicant rows
are believed to be the same legal entity," with a confidence, a source, and who decided.
That is additive, reversible, and it lets three different consumers disagree about how
strict to be. Underwriting can require a confirmed link. Ada can look at every proposed
link including the weak ones. Reporting can pick a threshold. One table, three
different levels of strictness, no data destroyed.

**Separate two questions that everyone is currently asking as one.** "Is this the same
legal entity" is a factual question with a real answer, and EIN plus state registration
mostly settles it. "Should these be treated as one customer" is a policy question with
a different answer per use case, and it belongs to a person, not to a join.

On ownership, the honest answer is that no single system is the master, and pretending
otherwise is what created the problem. Salesforce is the master of the relationship
before an application exists. `applicants` is the master during origination. LoanCore is
the master from funding onward, and it is legally the master, because the servicing
record is what a regulator would ask to see. The warehouse should be the master of
nothing and currently behaves as though it is the master of everything, because it is
the only system that produces a single row per customer and that single row is what
ends up on Dale's dashboard.

The near term move is to write that sentence down and get Priya and Doug to agree with
it. Identity architecture without a named owner per lifecycle stage is how you get four
rows and a support macro.

:::judgment
**Identity resolution looks like a data quality problem and is actually a policy
question. The technical part is easy and the technical part is not the part that is
stopping anyone.**

Every engineer who sees four rows for one bakery reaches for the same fix, because the
fix is genuinely straightforward and the data genuinely is messy. What that instinct
misses is that a duplicate is defined by a decision, not by a distance metric. Two rows
are duplicates when someone with authority says these should be treated as one
customer, and different parts of the business will answer that differently for the same
pair. Fraud wants them separate and linked. Reporting wants them collapsed. Servicing
wants them untouched. All three are right for their own purpose.

The specific trap in lending is that some duplicates are load bearing. An owner with
three entities applying separately is a normal business structure and also the standard
shape of decline shopping. Ada does not need the duplicates removed. She needs them
visible, connected, and still separate. A dedupe job would have taken away the only
signal she has, and it would have looked like a data quality win on the way out the
door.

The move that generalizes is to prefer additive over destructive when the decision
maker has not been identified yet. A link table is additive. A merge is destructive and
irreversible, because the deleted row takes its history with it. When you do not know
who owns a decision, take the action that keeps every option open, and spend your time
finding the owner instead. That is usually slower and it is almost always right, and it
is the same reasoning that kept you out of `calculateMonthlyRevenue` in Mission 09.
:::

:::commslab
#### To Ada, fraud lead

> You were right and I nearly broke something. I want to propose a link table instead
> of a merge, so you can see every candidate pair including the weak ones. What is the
> minimum you would need on a link record to make it useful to you?

She stopped you from doing damage. Say so once, briefly, then immediately give her
influence over the design. That is what turns a save into a working relationship.

#### To Priya, the CTO

> There are 118 EIN groups with more than one applicant row, 41 of them contain a
> funded loan, and there is a fourth Cortland row on the Bayline tenant that must not
> be merged for isolation reasons. I am not proposing a cleanup. I am proposing we
> write down which system owns identity at each stage, because right now nobody does
> and the warehouse has filled the gap by joining on email.

She wants blast radius. Lead with the 41, because that is the number that tells her
this is not a data hygiene ticket. Then name the missing decision instead of proposing
a project.

#### To Marcus, VP Product

> I'm not doing the dedupe. Roughly a third of those groups have a live loan attached,
> and changing the borrower of record on a funded loan is a legal amendment, not a
> migration. What I can do is make it visible when the same business shows up twice, so
> an underwriter sees the earlier decline before they decide.

He wanted the data quality win. Give him a different win he can talk about, and give
him the reason in terms of contracts rather than schemas.

#### To Doug, compliance

> If two applicant records are merged, the borrower of record on a funded loan changes.
> Before anyone builds that I want to know what your requirements are for changing a
> party on an active obligation, and whether a linkage record has any retention or
> disclosure implications.

He generates constraints and he is faster when you bring him a specific action rather
than a concept. Never ask compliance "is this okay." Ask what the requirements are.
:::

## Practice

Different industry. Same trap, sharper edges.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A property and casualty insurance carrier, about 1,100 employees. You are five days
into an engagement to build automated policy renewal underwriting.

The policyholder table has these five rows, which all appear to be one household:

```text
 party_id |        name         |    dob     |     address         | policy_status
----------+---------------------+------------+---------------------+--------------
   884201 | ROBERT J HALVERSEN  | 1971-04-02 | 14 Ridge Rd, Apt 2  | ACTIVE
   884202 | Bob Halversen       | 1971-04-02 | 14 Ridge Rd Apt 2   | LAPSED
   902117 | Robert Halvorsen    | 1971-04-02 | 14 Ridge Road #2    | ACTIVE
   911004 | R J HALVERSEN       |            | 14 Ridge Rd, Apt 2  | CANCELLED
   911005 | MARGARET HALVERSEN  | 1974-09-19 | 14 Ridge Rd, Apt 2  | ACTIVE
```

You also learn:

- Row 902117 came from a book of business the carrier acquired in 2022.
- Row 911004 was cancelled for non-payment in 2023.
- Claims are paid against `party_id`, and two of these parties have open claims.
- A state regulator requires the carrier to report claim frequency per insured.

**Your task**

1. Group the five rows. State your dividing line in one sentence before you group.
2. One of these rows is dangerous to merge for a reason that has nothing to do with
   data. Which one and why?
3. The acquired book row spells the name differently. Is that a typo or a fact? How
   would you find out, and what do you do while you wait?
4. Write the first move in four sentences, with no schema in it.

---

**Notes, after you have written yours**

Row 911005 is Margaret. Different first name, different date of birth. She is a
different person who happens to live at the same address, which is completely normal in
a household policy. Any matching rule tuned on address will pull her in. This is the
Cortland catering company in a different costume.

Row 911004 is the dangerous one. It was cancelled for non-payment, and in insurance
that is not a status, it is a fact about a person that affects eligibility and pricing
at renewal, and in some states it is reportable. Merging it into an active party either
carries the non-payment history onto an active policy or erases it. Both of those are
wrong and one of them is a regulatory problem. That row needs an underwriter and
probably a compliance officer, not a matching algorithm.

The acquired book row is the subtle one. `Halvorsen` with an O could be a data entry
error at the acquired carrier, or it could be the correct legal spelling and your
carrier has had it wrong since 2019. You cannot tell from the data, because both
systems are equally confident. You find out from a source outside both, which means the
signed application, a state license, or the person. While you wait, you link with a
confidence value and you do not overwrite either spelling, because whichever one you
pick, some downstream document already has the other.

The open claims are the reversibility test. A claim paid against a party ID is money
that already left the building. Merging parties with open claims changes which insured a
claim is attributed to, which changes claim frequency per insured, which is the number
the regulator asked for. That is not reversible with an UPDATE.

The first move, four sentences: link with confidence and provenance, merge nothing,
route the cancelled row and the acquired spelling to a named human, and get a written
answer on who owns the identity decision at renewal. Same as Northstar. The details
change and the shape does not.
:::
