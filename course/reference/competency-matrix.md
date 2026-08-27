---
slug: competency-matrix
title: Competency Matrix
subtitle: The fifteen things you are being trained to do, where each one is taught, and where each one is tested under pressure.
kind: assessment
order: 2
---

Every competency is practiced at least twice. Once when it is introduced, and once
later when the situation is worse and you have less time.

The certification exams score against these names, so mission frontmatter uses the same
names.

## The fifteen

| Competency | What it means in practice |
|---|---|
| `discovery` | Finding the real problem behind the stated request |
| `customer-communication` | Saying hard things to people who can end the project |
| `architecture` | Understanding and designing systems you did not build |
| `coding` | Writing production code in an unfamiliar codebase |
| `debugging` | Getting from a symptom to a root cause using evidence |
| `ai-fundamentals` | Knowing what a model can and cannot be trusted to do |
| `evals` | Measuring quality in a way that survives contact with reality |
| `rag` | Getting the right information in front of a model, safely |
| `agent-design` | Choosing control flow, and deciding what software may do on its own |
| `security` | Trust boundaries, injection, authorization, and blast radius |
| `fintech-judgment` | Knowing what is different when the data is money and identity |
| `production-reliability` | Deploying, observing, and surviving incidents |
| `adoption` | Making a correct system into a used system |
| `productization` | Turning one customer's solution into a capability |
| `executive-communication` | Reporting results to people who do not read code |

## Where each one is taught and tested

| Competency | Introduced | Practiced again | Tested under pressure |
|---|---|---|---|
| discovery | M01, M03 | M04, M05 | M39, Exam 1, Capstone |
| customer-communication | M01 | M06, M11 | M36, Exam 5, Capstone |
| architecture | M08 | M09, M21, M28 | M40, Exam 3, Capstone |
| coding | M12 | M18, M20, M25 | M35, M39 |
| debugging | M05 | M19, M23 | M32, M33, Exam 2 |
| ai-fundamentals | M12, M13 | M14, M17 | M34, M35 |
| evals | M15 | M16 | M20, M37, Capstone |
| rag | M22 | M23 | M24, Exam 3 |
| agent-design | M25 | M27, M28 | M29, Exam 3 |
| security | M24 | M26, M27 | M36, Exam 2 |
| fintech-judgment | M10, M11 | M20, M21 | M36, Capstone |
| production-reliability | M30 | M31, M33 | M32, Exam 4 |
| adoption | M07 | M29 | M37, Capstone |
| productization | M21 | M39 | M40 |
| executive-communication | M06 | M34 | M38, Exam 6 |

## Coverage of the original outcome list

The course was commissioned against a list of 33 outcomes. Here is where each one is
practiced. Nothing on the list is only discussed.

| # | Outcome | Missions |
|---|---|---|
| 1 | Understand the business problem | M01, M03, M05 |
| 2 | Interview stakeholders | M04, M11 |
| 3 | Challenge incorrect requirements | M06, M07, M27 |
| 4 | Map the workflow | M05, M07 |
| 5 | Understand an unfamiliar architecture | M08 |
| 6 | Navigate an unfamiliar codebase | M08, M09 |
| 7 | Find hidden dependencies | M09, M10 |
| 8 | Identify the real bottleneck | M05, M34 |
| 9 | Decide whether AI is appropriate | M07, M21, M28 |
| 10 | Decide what stays deterministic | M20, M21 |
| 11 | Scope a vertical slice | M07 |
| 12 | Build the solution | M18, M20, M22, M29 |
| 13 | Integrate LLMs safely | M12, M13, M26 |
| 14 | Use structured outputs | M13, M32 |
| 15 | Build evals | M15, M16 |
| 16 | Use RAG where appropriate | M22, M23 |
| 17 | Build tool-calling workflows | M25, M28 |
| 18 | Use agents only where justified | M28 |
| 19 | Human in the loop controls | M27, M29 |
| 20 | Handle PII and fintech data | M10, M31, M36 |
| 21 | Multi-tenant authorization | M24, M36 |
| 22 | Prompt injection and tool abuse | M26, M27 |
| 23 | Integrate legacy and third parties | M09, M33, M39 |
| 24 | Deploy the system | M30 |
| 25 | Observe it in production | M31 |
| 26 | Debug failures | M19, M32, M33 |
| 27 | Handle incidents | M32 |
| 28 | Control latency and cost | M34, M35 |
| 29 | Work with compliance and security | M36 |
| 30 | Improve customer adoption | M37 |
| 31 | Measure business impact | M38 |
| 32 | Explain results to executives | M06, M38 |
| 33 | Turn solutions into product | M39, M40 |

## Scoring

Each competency is scored 0 to 4 in the certification exams and the capstone.

| Score | Meaning |
|---|---|
| 0 | Did not attempt, or the attempt showed a misunderstanding of the goal |
| 1 | Attempted, needed direction to reach a workable answer |
| 2 | Reached a workable answer independently, missed important considerations |
| 3 | Solid independent work, sound reasoning, minor gaps |
| 4 | Would trust this person to do it alone at a real customer |

A passing capstone needs an average of 3.0 with no competency below 2, and no score
below 3 in `discovery`, `customer-communication`, or `security`. Those three carry a
higher bar because failure in them is the kind that ends engagements rather than the
kind that gets caught in code review.
