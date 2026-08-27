# COURSE_ARCHITECTURE.md

**Course:** The Forward Deployed Engineer Field Manual
**Subject:** Shipping AI into messy fintech production systems
**Format:** An interactive lab and apprenticeship, not a textbook
**Size:** 16 to 24 weeks, 10 to 15 hours a week, about 220 hours

This file records the design decisions behind the course. It also records where I
changed the original brief and why. Read this before you add or change content.

Writing rules for every file in this repo are in `STYLE_GUIDE.md`. Story facts and
character voices are in `CANON.md`. Build state is in `COURSE_STATUS.md`.

---

## 1. The idea behind the course

Most AI engineering material teaches skills. Here is RAG. Here is tool calling. Here
is an eval. That produces people who can build a demo and then drown in week two of a
real project.

Forward Deployed Engineering is not a skill. It is a long run of judgment calls made
with missing information, inside someone else's codebase, against someone else's
deadline, under someone else's regulator. The skills are the easy part.

So the course is built on one rule:

> Teach a concept only at the moment the project makes it unavoidable.

The learner does not study RAG. The learner has an underwriter say "that is the 2024
policy, we stopped using it in March." Then they have to find out why the assistant
quoted a dead document. RAG is what they arrive at, not what they were assigned.

### The one design constraint that matters most

**The learner has to be wrong on purpose, over and over.**

Missions are built so the obvious answer is usually incomplete and sometimes flatly
wrong. The feeling we want, again and again, is this:

> "I thought the problem was X. I looked into it. The problem is Y, and three people
> had already built workarounds for X."

If a mission can be solved by reading its title, it is a bad mission. Rewrite it.

---

## 2. Where I changed the brief, and why

The brief told me to use my own judgment. Here is what I changed.

### 2.1 The CEO's request is wrong, and it stays wrong for six missions

The brief opens with "we want an AI underwriter, cut processing time by 70 percent."
I kept the request. I also made the real answer completely different from what anyone
in the room expects. That gap is the spine of the whole course, not a single lesson.

The discovery data says this:

| Metric | Value |
|---|---|
| Median time from application to decision | 9.4 days |
| Median time an underwriter actually spends | 41 minutes |
| Median time an application waits for documents | 5.1 days |
| Applications that go through at least one rework loop | 63% |
| Median cost of one rework loop | 2.8 days |

An AI underwriter attacks the 41 minutes. Even if you automate all of it, you cut
about 7 percent of the cycle. The 70 percent target cannot be reached by building the
thing the CEO asked for. It can be reached by fixing document intake and killing the
rework loop. That is a boring problem with an interesting AI-shaped piece inside it.

Why this matters for teaching: it forces the learner to practice the hardest FDE skill
early. You have to tell a customer that their idea will not produce their outcome, and
keep the relationship. That happens in Mission 6, before they write any code. Every
mission after that depends on a problem that was re-scoped correctly.

### 2.2 The lab runs with no API keys, ever

This is the biggest technical change I made, and I think it is the right call.

The `ai-service` ships with four providers you can swap with one environment variable:

```
LLM_PROVIDER=stub       # default. offline, free, deterministic, scripted
LLM_PROVIDER=ollama     # local model on your machine (Qwen and friends)
LLM_PROVIDER=openai     # hosted
LLM_PROVIDER=anthropic  # hosted
```

The stub provider is a teaching tool, not a mock. It is a model simulator with a
scenario registry. When a mission needs the model to return `"$78,231 approximately"`
instead of a number, the stub returns exactly that. Same result on every machine,
every time.

Five reasons this beats requiring API keys:

1. **Broken things stay broken.** You cannot teach incident response if the incident
   only shows up sometimes. Mission 32's outage has to fire the same way for everyone,
   or the debugging walkthrough is fiction.
2. **Eval numbers stay stable.** The course claims 96 percent overall and 68 percent on
   loan proceeds. With a live hosted model those numbers move every time the vendor
   ships an update, and the lesson disappears. The point is the reasoning about slices,
   not the digits.
3. **Cost.** A 220 hour course that runs up a token bill filters out the people who
   most need the training.
4. **Locked down laptops.** Plenty of bank and fintech machines cannot reach an
   external model endpoint at all.
5. It removes "the model did something different for me" as a support problem.

The stub's answers come from real recorded model output stored in
`lab/ai-service/fixtures/recorded/`. Learners see genuine model behavior, frozen.

Missions that teach real model variance (temperature, model comparison,
non-determinism) have a second track that runs against a hosted model or a local one,
with a stated cost ceiling.

### 2.3 There is a full mission on running the model yourself

Local models are not a footnote here. Mission 17 is built around them.

The story reason is the right one. Doug in compliance and Yuki in security look at the
design and ask why bank transaction text and SSNs are being sent to a vendor. In real
fintech work that question ends projects. So the learner installs Ollama, pulls a Qwen
model, points `ai-service` at it, and runs the same eval suite against it.

Then they have to deal with what they find. The local model is slower per token on a
laptop. It is worse at the hard slices and fine on the easy ones. It costs nothing per
call but it costs hardware. That is a real engineering tradeoff, and it sets up model
routing in Mission 35, where cheap local inference handles the 84 percent of volume
that is easy and a hosted model handles the rest.

This also gives the course a second honest answer to the cost explosion in Mission 34.

### 2.4 Ten phases that follow the project, not a list of topics

The brief's 33 item list is a good inventory of concepts but a poor story. In real
work, a concept like idempotency does not appear once. It comes back with higher
stakes. So the course is organized as ten phases that follow the shape of a real
deployment, and concepts spiral.

Idempotency, for example, shows up four times. The learner finds it as a bug during
archaeology. They decide to leave it alone because it is out of scope for the first
slice. It becomes the root cause of a production incident. Then it becomes a platform
primitive when the second customer arrives. Same idea, four visits, more depth each
time. That is how engineers actually learn it.

### 2.5 Multi-tenancy starts with the first customer

The brief brings in multi-tenancy with the second customer. I moved it earlier.
Northstar white-labels its platform to two partner brands, Bayline and Cascade. So
tenant isolation, tenant-filtered retrieval, and the cross-tenant leak are all live
problems in Phase 5 while there is still only one customer.

Redwood Bank in Phase 9 then teaches a different thing. Not "another tenant" but
"another shape of business," with a different workflow, a different core system, and a
different way of deciding. Those are two separate axes. Engineers who confuse them are
exactly the ones who end up writing `if (customer.equals("NORTHSTAR"))`.

### 2.6 Every mission is graded two ways

Judgment-only content cannot be checked, so learners cannot tell how they are doing.
Code-only content teaches syntax instead of the job. So each mission has both:

- A `verify` target. Tests, an eval threshold, or a script that proves the code works.
- A judgment rubric. A scored self-check with a written answer key that explains how an
  experienced FDE reasons, including the wrong answers that look right and what they cost.

The learner is told up front that passing tests does not mean passing the mission.

### 2.7 Markdown is the source of truth, the website is a renderer

All prose lives in `course/` as Markdown with YAML frontmatter. The Next.js site reads
it at build time. Nothing about the course is trapped in the site. You can read it in
an editor, grep it, diff it, and review it in a pull request. It can be republished
somewhere else later without a rewrite.

### 2.8 The website sits at the repo root

The Next.js app is at the root instead of in a `web/` folder. That is a deployment
call. Vercel deploys a root level Next app with no configuration, and content in
`course/` is easy to read at build time. Putting the app in a subfolder means either a
root directory override with "include files outside root" turned on, or a copy step
before every build. Both work. Neither is worth the support questions. Lab code lives
under `lab/` and is excluded from the site build.

### 2.9 Humor does a job

The brief asked for light humor. I treat a running joke as a memory aid. When a learner
remembers `revenue_check_v7_FINAL.xlsx`, what they are really remembering is that the
real source of truth was not in the database and nobody in engineering knew about it.
Every running gag in `CANON.md` is tied to a specific lesson.

The jokes are dry and come from the situation. They never make a stakeholder look
stupid. Contempt for the customer is the number one way real FDEs fail, and the course
should not model it.

---

## 3. The map

40 missions across 10 phases, then 6 certification exams and a capstone.

| Phase | Title | Missions | Where you are in the project |
|---|---|---|---|
| 0 | Arrival | M01 to M02 | You land. You get a laptop and a bad brief. |
| 1 | Discovery | M03 to M07 | Interviews, the workflow map, the hard conversation, the first slice. |
| 2 | Archaeology | M08 to M11 | An 11 year old codebase and nobody agrees who owns which table. |
| 3 | First Blood | M12 to M17 | First model call, JSON, hallucination, evals, local models. |
| 4 | Documents and Money | M18 to M21 | Intake, OCR, what counts as revenue, the AI boundary. |
| 5 | Knowledge | M22 to M24 | RAG, a policy that expired, a tenant leak. |
| 6 | Action | M25 to M29 | Tools, prompt injection, tool authorization, workflow vs agent, the copilot. |
| 7 | Production | M30 to M35 | Deploy, observe, an incident, a lying vendor, a cost spike, routing. |
| 8 | The Human Layer | M36 to M38 | Security and compliance review, adoption collapse, the exec readout. |
| 9 | Productization | M39 to M40 | Redwood Bank, and pulling out a platform without over-building it. |
| C | Certification | 6 exams | Discovery, debugging, architecture, incident, customer comms, exec review. |
| ★ | Capstone | Meridian | A cold, messy project with no guidance. |

### Full mission list

| # | Mission | Core skill |
|---|---|---|
| M01 | What the job actually is | FDE role, engagement shape |
| M02 | Booting Northstar | Lab setup, first tour of the system |
| M03 | The kickoff call | Reading an executive request |
| M04 | Eleven interviews | Stakeholder discovery |
| M05 | The nine day question | Workflow mapping, cycle time analysis |
| M06 | Telling the CEO no | Challenging a requirement, keeping the room |
| M07 | Cutting the first slice | Vertical slice scoping, success metrics |
| M08 | Reading someone else's system | Architecture archaeology |
| M09 | The revenue function | Hidden dependencies, blast radius |
| M10 | Who owns the applicant | Duplicate identity, data ownership |
| M11 | The spreadsheet is the spec | Extracting undocumented business rules |
| M12 | Your first model call | LLM basics, tokens, context, temperature |
| M13 | Make it return JSON | Structured output, schema validation |
| M14 | It made up a number | Hallucination, missing data, refusal paths |
| M15 | Prove it works | Golden datasets, first eval |
| M16 | The 96 percent that lied | Slice metrics, label noise |
| M17 | Running the model in the building | Local models with Ollama and Qwen |
| M18 | Intake | Idempotent uploads, object storage |
| M19 | OCR lies confidently | OCR failure, confidence, fallback |
| M20 | What counts as revenue | The signature hybrid problem |
| M21 | The seam | Where AI stops and code starts |
| M22 | Ask the policy | Embeddings, chunking, retrieval |
| M23 | That policy expired in March | Effective dates, precedence, citations |
| M24 | Cascade saw Bayline's policy | Cross-tenant leak, real authz bug |
| M25 | Give it hands | Tool calling |
| M26 | The PDF that gave orders | Prompt injection, trust boundaries |
| M27 | It declined the loan | Tool authorization, dry run, approval gates |
| M28 | Workflow or agent | Choosing control flow honestly |
| M29 | The copilot | Human in the loop, explainability |
| M30 | Shipping it | Deploy, config, flags, versioning |
| M31 | Seeing inside | Traces, spans, AI observability |
| M32 | 214 stuck applications | Incident response end to end |
| M33 | The vendor said 200 | Transport vs semantic success |
| M34 | Ninety one thousand dollars | Cost investigation |
| M35 | Routing and budgets | Model routing, caching, token budgets |
| M36 | Yuki and Doug have questions | Security and compliance review |
| M37 | Adoption fell to 29 percent | Workflow design, user research |
| M38 | The readout | Executive communication, business impact |
| M39 | Redwood Bank | Second customer, different shape |
| M40 | What belongs in the product | Productization without over-abstraction |

The full map from every competency in the brief to the missions that practice it is in
`course/reference/competency-matrix.md`. Every competency appears at least twice. Once
to learn it, once under pressure.

---

## 4. The Northstar lab

### 4.1 Why real code and not code listings

A listing teaches reading. A running system teaches investigation. The learner needs to
be able to curl an endpoint, get a wrong answer, and go find out why. So the lab is real
and it runs.

```
lab/
  northstar/            Java 21, Spring Boot 3, multi-module Maven build
    application-service     :8081   applicants and application lifecycle
    document-service        :8082   uploads and OCR orchestration
    underwriting-service    :8083   decisions, policy, the revenue function
    fraud-service           :8084   scoring and vendor calls
    common-lib                      shared DTOs, and shared mistakes
  ai-service/           :8000  Python 3.12, FastAPI, all model work
  reviewer-portal/      :5173  React 19, TypeScript, Vite
  evals/                Python eval framework, importable and reusable
  infra/                docker-compose, Flyway migrations, vendor stubs
  data/                 seeds, bank statements, policy files, OCR fixtures
```

Support services: PostgreSQL 16 on 5432, Kafka on 9092, Redis on 6379, MinIO on 9000,
and the fake vendors on 8090.

### 4.2 Planted problems

The system contains 41 planted defects, listed in `lab/DEFECT_REGISTRY.md`. That file
is a spoiler and the learner is told not to open it until Phase 9. Each entry records
the defect, the mission that surfaces it, whether it is a red herring, and the realistic
reason it exists. Every bad line of code in a real system was once a reasonable decision
made under pressure. An FDE who cannot see that becomes a bad consultant.

What is planted: duplicate applicant identities, three different tenant ID conventions,
a revenue function with three consumers and one wrong definition, a Kafka consumer with
no idempotency, retry logic that cannot tell a timeout from a schema error, a feature
flag from 2021 that still controls live behavior, docs that describe what an endpoint
was supposed to do rather than what it does, a vendor that returns HTTP 200 with an
empty body, a cron job called `fix_stuff.sh`, and a spreadsheet that is the real source
of truth for a rule nobody wrote down.

### 4.3 Fake vendors that fail like real ones

Every third party is a WireMock service with scenario control (`infra/vendors/`). OCR,
bank aggregation, credit bureau, fraud, e-sign, CRM, and servicing. Scenarios include
partial outage, slow then timeout, HTTP 200 with an empty body, and quiet schema drift.
A mission can tell the learner to run `make inject SCENARIO=ledgerlink-empty-200` and
the failure happens live.

### 4.4 Running it

`make up` starts Postgres, Kafka, Redis, MinIO, the vendor stubs, and every service.
`make seed` loads 1,200 synthetic applications with realistic dirt in them. It all runs
on one laptop, with no external network and no API keys.

---

## 5. The eval framework

`lab/evals/` is a real library, not a pile of per-mission scripts. The course claims to
teach eval engineering, so the artifact has to survive a second use case. It gets reused
without changes for Redwood in Phase 9, which is the actual test of whether it was
designed well.

It provides dataset loading with provenance, human labeling and agreement scoring,
exact and fuzzy and numeric-tolerance matchers, per-slice metrics, cost and latency
capture, a regression gate for CI, and prompt and model comparison reports.

The teaching centerpiece is a golden dataset built so overall accuracy reads 96 percent
while the slices that carry the money sit between 61 and 73 percent. The learner ships
it, feels good, and then a slice report ruins their afternoon.

About 2 percent of the labels in that dataset are wrong on purpose. Ground truth is not
scripture, and the learner has to deal with a case where Renee and a junior underwriter
disagree and Renee is right for a reason nobody wrote down.

---

## 6. How the learner is assessed

- Per mission: an automated `verify` target plus a judgment rubric with an answer key.
- Certification: six timed practical exams scored against published rubrics in
  `course/certification/rubrics/`.
- Capstone: Meridian Financial. A cold customer package, no hints, no stated right
  answer, scored on a 15 competency rubric.

Discovery and communication are weighted the same as implementation. That matches where
junior FDEs actually fail.

---

## 7. Content conventions

Missions are Markdown with frontmatter and a fixed 17 section skeleton. The template is
in `course/reference/MISSION_TEMPLATE.md`. These container directives render as rich UI:

```
:::dialogue          a conversation, rendered as a transcript
:::evidence{type=}   logs, SQL, HTTP, Kafka, tickets, Slack, traces
:::stopandthink      questions the reader answers before the solution appears
:::judgment          the durable lesson
:::commslab          how to say it to an engineer, product, customer, executive
:::spoiler           answer keys, collapsed by default
:::task              the concrete thing to go do
```

The site keeps `:::spoiler` closed and puts the solution behind the stop and think
block. Reading ahead is the main way people waste a course like this, so the interface
gets in the way on purpose.

---

## 8. What this course is not

- Not a legal reference. Compliance appears only where it changes the architecture.
- Not a model training course. No fine tuning and no GPU work beyond running a local model.
- Not a Java tutorial. Java skill is assumed. Unusual Spring patterns get a note.
- Not tied to one vendor. The provider swaps with an environment variable and no mission
  depends on a single vendor's features.
