---
id: M04
slug: eleven-interviews
title: Eleven Interviews
subtitle: >-
  Everyone describes the same process. No two descriptions match, and all of
  them are honest.
phase: 1
order: 4
duration: 240
difficulty: 3
lab: false
status: complete
objectives:
  - Run an interview that produces artifacts instead of opinions
  - Reconcile eleven partly wrong accounts of one process
  - >-
    Build a stakeholder map covering what each person knows, believes, and
    controls
  - Recognize when someone's workaround is the real system
concepts:
  - interviewing
  - stakeholder mapping
  - workarounds
  - requirements elicitation
competencies:
  - discovery
  - customer-communication
  - adoption
prereqs:
  - M03
condensed: true
durationCondensed: 96
---
## Where you are

March 11 to March 17. Seven days, eleven people, about nine hours of scheduled time and another four you did not schedule because someone kept talking after the meeting ended.

## The request

:::evidence{type=slack label="DM from Nadia Ferrante, Tuesday 6:02 PM"}
```text
Nadia:  how many interviews

You:    eleven booked

Nadia:  good. two rules.

Nadia:  1. never ask anyone what they want. they'll tell you, you'll
        write it down, and it'll be wrong and now you're committed

Nadia:  2. leave every one of them with an artifact. a file, a report,
        a screenshot, a saved search. opinions decay, artifacts don't

You:    what if they don't have one

Nadia:  everybody has one. they just don't think it counts because
        it's in excel
```
:::

## Your task

:::task{time="120 min"}
Build a stakeholder map. Not an org chart. A table with one row per person and four
columns.

**Knows.** Things this person has direct evidence for. Renee knows what she keys into a
spreadsheet. Hank knows his SLA percentage. Restrict this column to facts they can show
you.

**Believes.** Things they stated as fact that you have not verified, especially where two
people's beliefs conflict. Sam believes the portal widget is unused. Marcus believes
underwriting is the bottleneck.

**Controls.** What they can stop, start, or block. This column decides who you talk to
before the CEO readout. Janet controls the roadmap. Doug can block a launch. Renee
controls whether eleven underwriters actually use what you build.

**Artifact.** The file, report, query, or script you got from them. Any row with an empty
artifact cell means that interview is not done.

Then add one line per person: what would change their mind. This is the column people
skip and it is the one you will use in Mission 06.

Save it as `customers/northstar/stakeholder-map.md`.
:::

## Stop and think

:::stopandthink
Before you read on:

1. Eleven descriptions of one process. Which two people's accounts conflict most
   directly, and how would you settle it with data rather than a meeting?
2. Renee, Carla, and Bill each described a piece of the same problem without knowing it.
   What is the problem?
3. Marcus said underwriting is the bottleneck. What is the cheapest way to prove or
   disprove that in one day?
4. Which of the eleven would you bring to the CEO readout on the twenty first? Why that
   person and not Renee?

Ten minutes. In writing.
:::

## One line to remember

:::judgment
**When eleven honest people describe one process eleven different ways, the process is
not the thing they are describing. It is the thing that fills the gaps between their
descriptions.**

Renee reads the PDF herself. Carla tells people to resubmit. Bill runs a script that
marks documents as failed. Hank's clock does not start until the documents arrive.
Nobody is wrong, nobody is hiding anything, and no single person can see the loop those
four facts form. That loop is the actual system, and it exists in the space between four
job descriptions.

Your advantage as an outsider is not intelligence and it is not tooling. It is that you
are the only person in the building who talks to all eleven of them in one week. That
advantage has a short half-life. In four months you will have absorbed the local
assumptions and stopped noticing the gaps, which is exactly what happened to everyone
you interviewed.

So the practical discipline is this. Ask about the last real instance, not the general
case. Ask to see it, always. Leave with a file. And when someone shows you a workaround,
do not treat it as a defect to be removed. Treat it as a specification written by
someone who was not allowed to write specifications. Renee's spreadsheet is the most
accurate document at Northstar. It is also the one with the least authority. Those two
facts together tell you almost everything about how this company works.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital system, six sites. They want AI to handle prior authorization requests to
insurers. You interview five people in three days. Excerpts:

```text
VP Revenue Cycle:
  "Auths are our biggest denial driver. If AI submits them
   correctly the first time, denials drop."

Auth Coordinator (11 years):
  "I don't submit through the portal for Aetna. I fax. The portal
   loses attachments and then you're starting over."

Scheduler:
  "We book the appointment first and start the auth after. Otherwise
   the patient goes somewhere else."

Physician:
  "I dictate the medical necessity note at the end of clinic. Usually
   two, three days later."

Denials Analyst:
  "Sixty-two percent of our auth denials are 'insufficient clinical
   documentation.' I have a spreadsheet by payer."
```

**Your task**

1. Which two accounts cannot both be true, and what data settles it?
2. One person described a workaround. What is it, and what does it tell you about the
   system?
3. The physician's answer contains the largest number in this project. Explain.
4. Write the three questions you would ask the Auth Coordinator in a second interview,
   and say what artifact you would ask her for.

---

**Notes, after you have written yours**

The conflict: the VP says denials come from incorrect submissions, and the Denials
Analyst says 62 percent are insufficient clinical documentation. Those point at different
causes. Incorrect submission is a form-filling problem, which AI is good at. Insufficient
clinical documentation is a problem of information that does not exist yet when the
request is submitted, which is a workflow problem. Get the analyst's spreadsheet and
break the denial reasons down by payer and by service line. That one file probably
reframes the project.

The workaround is the fax. An eleven year coordinator bypasses the official portal for a
major payer because the portal loses attachments. That tells you the submission channel
data is unreliable, so any metric computed from portal submissions is missing a chunk of
volume, and it tells you that "submit correctly the first time" is not the constraint she
experiences.

The physician's answer is the biggest number in the project. Medical necessity notes are
dictated two to three days after the visit. If the note is required for the auth and the
note does not exist for two to three days, then two to three days of delay are structural
and no amount of automated form filling touches them. It also connects directly to the
62 percent: a request submitted before the note exists is a request submitted with
insufficient clinical documentation. The scheduler's answer completes the loop, because
appointments get booked before the auth starts, so the clock is running from day one.
Four people described one loop and none of them could see it.

Your three questions for the coordinator: walk me through the last Aetna auth you
submitted, start to finish. When you get a denial, what do you do next and how long does
it take. How do you know a request is missing something before you send it. The artifact
to ask for: whatever she uses to track in-flight auths, which will be a spreadsheet or a
paper log, and it will be better than the system of record.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
