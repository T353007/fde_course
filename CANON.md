# CANON.md

This is the story bible for the course. Every mission has to match it.

If a mission contradicts this file, the mission is wrong. If the canon needs to change,
change it here first, then fix the missions it affects.

Writing rules are in `STYLE_GUIDE.md`. Read that too before you write anything.

---

## 1. The setup

**You** are a Forward Deployed Engineer at **Halyard AI**. Halyard sells an AI
application platform to financial firms. This is your first account on your own.
When a calendar invite or email needs a real name, use **Imtiaz Alam**.

**The customer** is **Northstar Capital**, a small business lender in Charlotte, North
Carolina. Started in 2013. About 340 employees. They originate roughly **$780 million a
year** across term loans, lines of credit, SBA 7(a) loans, and equipment financing.
They also run a small grants program for a state economic development agency. Nobody
wants to talk about the grants program. It matters in Phase 5.

Northstar white-labels its platform to two partner brands. That is where their
multi-tenancy comes from.

| Tenant code | Brand | Notes |
|---|---|---|
| `NSC_DIRECT` | Northstar Capital | Their own brand. 71% of volume. |
| `BAYLINE` | Bayline Capital | Partner. Different pricing, same policy engine. |
| `CASCADE` | Cascade Funding | Partner. Has a California-only policy overlay. |

Later customers: **Redwood Bank** in Phase 9, and **Meridian Financial** for the capstone.

---

## 2. The cast

Voices stay consistent across every mission. Each person has something they are good at,
something they are wrong about, and a phrase they repeat.

**Nobody here is stupid.** Every wrong belief has a reason that made sense at the time.

### Halyard AI, your side

**Imtiaz Alam**, Forward Deployed Engineer. That is you. First solo account.
Email when a signature is needed: `imtiaz.alam@halyard.ai`.

**Nadia Ferrante**, Principal FDE, your mentor and manager. Shows up at decision points,
usually by Slack, sometimes to stop you from doing something expensive. Asks questions
instead of answering them, which is either great mentoring or annoying depending on the
week. Says: "What would have to be true for that to be the answer?" She has never worked
inside a regulated company, so she underrates how much compliance slows things down.

**Jordan Hale**, Account Executive. Sold the deal. Warm, relentless, and has already told
the customer things you did not agree to. Says: "I may have set expectations." He is not
a villain. He believes the pitch, and he is right about the business value more often
than engineers expect.

### Northstar leadership

**Dale Whitmore**, CEO. Former commercial banker. Not technical, but sharper than he
lets on. He wants AI because a competitor called Fastcapital put out a press release
about an AI underwriting engine. Says: "Is that directionally correct?" He thinks cycle
time is an underwriting problem because underwriting is the part he can see.

**Priya Raghunathan**, CTO. Joined in 2019 to clean up the platform and has been
firefighting ever since. Practical, protective of her team, and will back you if you
respect them. Says: "Show me the blast radius." She trusts her own architecture
diagrams, which are 18 months out of date.

### Northstar product and engineering

**Marcus Webb**, VP Product. High energy, ships things, promises too much. Writes
requirements as solutions. Says: "Can't the AI just do that?" He measures adoption by
logins. He turns into a real ally in Phase 8 once he sees actual user interviews.

**Janet Osei**, Engineering Manager for the lending platform. Controls the roadmap.
Suspicious of consultants who drop a demo and leave. Says: "Who is on call for that?"
Winning her over in Phase 2 is a real objective, not a side quest.

**Sam Ortiz**, Senior Backend Engineer. Nine years at Northstar. Knows where every body
is buried and stopped being surprised years ago. Deadpan. Extremely helpful once he
decides you are serious. Says nothing for a moment, then: "...Ah. So you found that."
He is the most valuable person in the building and the org chart does not show it.

**Tomás Ferreira**, Backend Engineer, two years in. Wrote the retry worker that causes
the Phase 7 incident. Earnest and fast. His code is not bad. It was never reviewed.

**Wendy Kaur**, Frontend lead on the reviewer portal. Cares about how many clicks a task
takes. She is right in Phase 8, and she said it back in Phase 6 when nobody listened.

### Northstar business side

**Renee Blackwell**, Senior Underwriter, 14 years. She is the domain expert of the whole
course. She keeps `revenue_check_v7_FINAL.xlsx` on her desktop. It holds eleven business
rules that exist nowhere in the code. She is not being difficult. The system gave her
wrong numbers and she had a job to do. Says: "We don't use that number." Learners who
dismiss her miss the point of the course.

**Hank Delgado**, Underwriting Manager. Owns the SLA and wants throughput. He suspects
"AI" means "fewer people," and he is not completely wrong. That tension is real and the
course does not pretend otherwise. Says: "What does that do to my queue?"

**Adaeze Nwosu**, goes by Ada, Fraud Lead. Trusts nothing, correctly. She is the first
person to spot the prompt injection PDF. Says: "Assume the applicant is hostile."

**Bill Tran**, Operations. Runs four cron jobs. Three are documented. The fourth is
called `fix_stuff.sh` and it patches a nightly mismatch nobody has explained since 2022.
Says: "It's fine, I run it by hand if it fails."

**Carla Mendes**, Customer Support Lead. Knows every workaround because she invented most
of them. Her ticket queue is the best data in the company and nobody has ever read it.
Says: "Oh, that. Yeah, we just tell them to resubmit."

**Doug Feinberg**, Compliance. Cares about adverse action notices, fair lending, and
model governance. He is not an obstacle. He generates constraints. Says: "Can you
explain that decision to the applicant in writing?"

**Yuki Sato**, Security Engineer. Threat models for a living. Says: "Say 'just' one more
time." Runs the Phase 8 security review the learner has to survive.

**Mei**, Finance analyst (appears in Mission 05). Pulls cycle time from
`applications.submitted_at`, knows it is messy, and rounds. She is not wrong on purpose.
She is using the column that her reports have always used.

---

## 3. The systems

### Northstar services, Java 21 and Spring Boot 3

| Service | Port | Owns | Reality |
|---|---|---|---|
| `application-service` | 8081 | applications, applicants, tenants | Oldest. 2014 code with 2023 patches. |
| `document-service` | 8082 | uploads, OCR, object storage | Rewritten in 2021. Mostly sane. |
| `underwriting-service` | 8083 | decisions, policy, the revenue function | The valuable part and the crime scene. |
| `fraud-service` | 8084 | fraud scoring, vendor calls | Ada's team. Well tested, badly integrated. |
| `common-lib` | n/a | shared DTOs | Where inconsistency became permanent. |
| `ai-service` | 8000 | Python and FastAPI, all model work | New. You build most of it. |
| `reviewer-portal` | 5173 | React 19 and TypeScript | Wendy's. Six clicks too many. |

Infrastructure: PostgreSQL 16 on 5432, Kafka on 9092, Redis on 6379, MinIO on 9000,
vendor stubs on 8090.

### Vendors, all simulated

| Vendor | Role | How it fails |
|---|---|---|
| **OptiScan** | OCR | Quietly falls apart on faxed and scanned statements. Returns confident garbage. |
| **Ledgerlink** | Bank aggregation | Returns `HTTP 200 {"accounts": []}` when a connection has gone stale. |
| **Corveil** | Credit bureau | Rate limits at unpredictable points. 40 second p99. |
| **Sentinel Risk** | Fraud | Sometimes returns a score with no reason codes. |
| **LoanCore** | Loan servicing | SOAP. Yes, really. Has batch windows. |
| **DocuSign, Twilio, Salesforce** | e-sign, SMS, CRM | Normal, except webhook order is not guaranteed. |

### The local model setup, Mission 17 and Mission 35

Doug and Yuki push back on sending bank transaction text and SSNs to an outside vendor.
That is the reason the learner installs a local model, not a hardware hobby.

| Fact | Value |
|---|---|
| Runner | Ollama, on the learner's laptop |
| Main model | `qwen3:8b` |
| Small model for routing | `qwen3:1.7b` |
| Backup model used for comparison | `llama3.1:8b` |
| Minimum practical hardware | 16 GB RAM. 8 GB works with the 1.7b model. |
| Northstar's stated production plan | Two A10G instances in their own VPC |
| Measured laptop latency, 8b, 400 token output | 6 to 11 seconds |
| Hosted model latency for the same task | 1.9 seconds |
| Local eval result, easy slice | Within 1 point of hosted |
| Local eval result, loan proceeds slice | 14 points worse than hosted |

Those last two lines are the whole lesson. The local model is good enough for the 84
percent of volume that is easy and not good enough for the cases that move money. That
is what makes routing in Mission 35 an honest engineering decision instead of a trick.

Every mission that uses a local model must also run with `LLM_PROVIDER=stub`, so a
learner on a small machine is never blocked.

---

## 4. Facts that must never change

### Discovery numbers, set in Mission 5, used forever

```
Median time from application to decision ....... 9.4 days
Median underwriter hands-on time ............... 41 minutes
Median time waiting on documents ............... 5.1 days
Applications with at least one rework loop ..... 63%
Median cost of one rework loop ................. 2.8 days
Applications per month ......................... 1,840
Underwriters on staff .......................... 11
Dale's stated target ........................... 70% faster
```

What the learner has to work out: automating the 41 minutes caps out near 7 percent.
The 70 percent lives in document intake and rework.

### SOW section 3.3 success criteria (set in Mission 07)

Pilot success for the first slice, written into the SOW:

- Time spent on revenue reconciliation drops by **50%** versus the pre-pilot baseline
  on the same product mix
- Revenue-related `PENDING_INFO` rework drops by **25%** on the pilot cohort
- Halyard shadows on-call jointly for **fourteen days**, then Northstar owns the pager

Do not invent a different 3.3 without updating this block.

### The bank statement, Mission 20, the signature example of the course

```
05/04  STRIPE PAYOUT                    +48,230
05/06  TRANSFER FROM SAVINGS            +30,000
05/11  STRIPE PAYOUT                    +51,340
05/18  FASTCAPITAL LOAN                 +75,000
05/22  STRIPE PAYOUT                    +47,830
```

Naive total of credits: **252,400**
Correct operating revenue: **147,400**
The two things to exclude: the internal transfer of 30,000 and the loan proceeds of 75,000.

Fastcapital is Northstar's competitor. The applicant already has a loan from them. Renee
sees this in two seconds. The system has never once caught it.

### The eval slice table, Missions 16 and 20

```
Overall accuracy ............................... 96.0%
  loan proceeds ................................ 68%
  poor OCR quality ............................. 61%
  internal transfers ........................... 73%
  standard card settlements .................... 99%
```

The 96 percent is real and useless. The 99 percent slice is 84 percent of the volume.
The failing slices are the ones that move an approval by five figures.

About 2 percent of the golden labels are wrong on purpose. In at least one case Renee
and a junior underwriter disagree, and Renee is right for a reason nobody wrote down.

### The incident, Mission 32

```
Expected:  {"averageRevenue": 78231.00}
Actual:    {"averageRevenue": "$78,231 approximately"}
```

The Java parser throws. Tomás's retry worker cannot tell a schema error from a timeout,
so it retries five times with backoff. **214 applications get stuck.**

Timeline: starts 14:02 ET on a Tuesday. Detected at 16:47 because Carla's ticket volume
spiked, not because monitoring caught it. Monitoring was green. The health check tested
the endpoint, not the workflow.

### The cost spike, Mission 34

```
Last month:     $22,000
This month:     $91,000
```

Causes in order of size: the full policy corpus stuffed into every prompt (61%), retry
amplification from the Mission 32 bug (18%), a premium model doing a trivial
classification (14%), and no caching of identical document extractions (7%).

### Adoption collapse, Mission 37

```
Week 1: 67%     Week 2: 48%     Week 3: 29%
```

It is not model quality. Reviewers have to click through six screens to accept a
suggestion, and the suggestion shows up after they have already made up their mind.
Wendy said this in Phase 6 and was overruled.

### The policy corpus, Missions 22 and 23

```
credit-policy-2024.pdf
credit-policy-2025.pdf
credit-policy-FINAL.pdf          (actually a 2023 draft)
credit-policy-FINAL2.pdf         (2025, missing appendix C)
credit-policy-2026.pdf           (effective 2026-03-01, not before)
California-overlay.pdf           (CASCADE tenant only)
SBA-overlay.pdf
grants-program-addendum.docx     (the one nobody mentions)
```

The precedence rule, which is written down nowhere and has to be pulled out of Doug and
Renee: tenant overlay beats product overlay, which beats base policy, filtered by
effective date. SBA overlay beats everything when the product is SBA 7(a).

---

## 5. Running jokes, and the lesson attached to each

| The joke | What it teaches |
|---|---|
| `revenue_check_v7_FINAL.xlsx` | The real source of truth is not in the database. |
| Dale saying "directionally correct" | Executives buy a story. You have to translate. |
| `fix_stuff.sh` | Undocumented ops work holds the system up. |
| Flag `USE_NEW_REVENUE_CALC_V2_TEMP`, set in 2021, still on | "Temporary" is the longest lived word in engineering. |
| Sam's pause, then "...Ah. So you found that." | Institutional knowledge has no API. |
| A Fastcapital loan in every sample statement | Your competitor is already inside your customer's data. |
| Jordan's "I may have set expectations." | Scope shows up pre-broken. |

Rules for humor: dry, character driven, never mocking anyone's intelligence, and never
punching down at ops, support, or underwriters. The system is the joke. The people are not.

---

## 6. Rules for writing a mission

1. Lead with dialogue whenever you can. Prose only carries what conversation cannot.
2. Show evidence before you interpret it. Logs and SQL first, conclusions later.
3. The learner decides before anything is revealed. `:::stopandthink` always comes first.
4. Every mission has at least one wrong turn a reasonable engineer would take.
5. Code is complete and it runs. No `// implement this` unless that is the exercise.
6. State the lesson in one sentence at the end.
7. No mission can be solved from its title.
8. Write to the learner as "you." Scenes are in present tense.
9. American dates, US dollars, Eastern time. Northstar is in Charlotte.
10. The FDE is not right by default. Show the plausible mistake and what it costs.
11. Follow `STYLE_GUIDE.md`. Eighth grade sentences. No em dashes. No AI tells.
