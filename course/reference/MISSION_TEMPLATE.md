---
slug: mission-template
title: How a mission is built
subtitle: The required skeleton, the directives, and the bar a mission has to clear before it ships.
kind: authoring
order: 90
---

Read `STYLE_GUIDE.md` and `CANON.md` first. This page covers structure only.

## Frontmatter

Every mission file is `course/missions/mNN-slug.md` and starts with this block.

```yaml
---
id: M09
slug: the-revenue-function
title: The Revenue Function
subtitle: One method. Three callers. Two of them want different answers.
phase: 2
order: 9
duration: 240          # minutes, realistic, including the lab work
difficulty: 3          # 1 to 5
lab: true              # does the learner need the lab running
status: complete       # stub | draft | complete
objectives:
  - Trace a dependency across service boundaries without a call graph
  - Estimate blast radius before proposing a change
concepts: [dependencies, blast radius, legacy code]
competencies: [architecture, debugging, customer-communication]
prereqs: [M08]
---
```

`concepts` are topics. `competencies` map to the certification rubric and must use the
names from `course/reference/competency-matrix.md`.

## The seventeen sections

Sections marked required appear in every mission. The others appear when the mission
has that kind of content. A discovery mission has no code. A debugging mission has no
new architecture. Do not pad a mission with an empty section to satisfy the list.

| # | Section heading | Required | Directive |
|---|---|---|---|
| 1 | Where you are | yes | plain prose, 2 to 4 sentences |
| 2 | The request | yes | `:::evidence` or dialogue |
| 3 | The conversation | yes | `:::dialogue` |
| 4 | What you know about the system | when relevant | prose, diagram, table |
| 5 | The code | when relevant | fenced blocks with real code |
| 6 | Evidence | yes | `:::evidence` blocks, several kinds |
| 7 | What you do not know | yes | short list, honest |
| 8 | Your task | yes | `:::task` |
| 9 | Stop and think | yes | `:::stopandthink` |
| 10 | Working through it | when there is an implementation | prose plus code |
| 11 | Tests | when there is code | real test files |
| 12 | Then this happens | strongly encouraged | new failure after the first fix |
| 13 | Tracking it down | with section 12 | step by step from evidence |
| 14 | The better version | with section 12 | improved design and why |
| 15 | What an FDE takes from this | yes | `:::judgment` |
| 16 | Saying it out loud | when there is a stakeholder | `:::commslab` |
| 17 | Practice | yes | `:::spoiler` with a different scenario |

## Directives

````
:::dialogue{title="Kickoff call, Tuesday 9:15am"}
**Dale:** We want an AI underwriter.

**You:** How long does an application take today, start to finish?

**Dale:** Too long. That is the problem.

*He looks at Priya. Priya does not look up.*
:::
````

A paragraph that starts with a bolded name becomes a speaker turn. Anything else in the
block renders as narration. Keep turns to four lines or fewer.

````
:::evidence{type=log label="underwriting-service, 14:03 ET"}
```text
ERROR c.n.uw.RevenueParser - Cannot deserialize value of type BigDecimal
```
:::
````

`type` sets the color and label. Use: `log`, `sql`, `http`, `kafka`, `metrics`,
`trace`, `ticket`, `email`, `slack`, `schema`, `test`, `policy`, `spreadsheet`.

````
:::stopandthink
1. What is your hypothesis right now?
2. What evidence would move you off it?
3. What is the blast radius if you are wrong?

Write your answers down before you scroll. Two minutes.
:::
````

````
:::task{time="90 min"}
Trace every caller of `calculateMonthlyRevenue()` across all four services. Produce a
table of caller, expected definition, and what breaks if the definition changes.
:::
````

````
:::judgment
The lesson in one sentence, then two or three paragraphs on how an experienced FDE
recognizes this pattern next time.
:::
````

````
:::commslab
#### To Sam
...
#### To Marcus
...
#### To Dale
...
:::
````

````
:::spoiler{label="Answer key"}
Content stays collapsed until the learner opens it.
:::
````

## The quality bar

Before a mission ships, it has to pass all seven of these.

1. Would an experienced backend engineer say this is realistic?
2. Does the learner have to investigate rather than guess?
3. Does it teach judgment, not just syntax?
4. Is there enough evidence in the mission to actually reason it out?
5. Is there a real cost to choosing badly?
6. Does the solution explain why it is better, not only what to type?
7. Is the mission unsolvable from its title alone?

If any answer is no, rewrite it.

## Two more rules

**One wrong turn per mission, minimum.** Somewhere in the mission, a reasonable engineer
takes a path that does not work. Show the path, show the cost, show the recovery.

**No mission ends with the FDE being right the whole time.** If you write one, add the
part where they were wrong.
