---
id: M04
slug: eleven-interviews
title: Eleven Interviews
subtitle: Everyone describes the same process. No two descriptions match, and all of them are honest.
phase: 1
order: 4
duration: 240
difficulty: 3
lab: false
status: complete
objectives:
  - Run an interview that produces artifacts instead of opinions
  - Reconcile eleven partly wrong accounts of one process
  - Build a stakeholder map covering what each person knows, believes, and controls
  - Recognize when someone's workaround is the real system
concepts: [interviewing, stakeholder mapping, workarounds, requirements elicitation]
competencies: [discovery, customer-communication, adoption]
prereqs: [M03]
---

## Where you are

March 11 to March 17. Seven days, eleven people, about nine hours of scheduled time and
another four you did not schedule because someone kept talking after the meeting ended.

You have one week before you have to say a number out loud. This mission is where the
number comes from, even though nobody in it gives you a number.

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

## The eleven

These are excerpts. Each interview ran thirty to sixty minutes. What follows is the part
that mattered, which was usually not the part you planned.

### 1. Renee Blackwell, Senior Underwriter, Wednesday 10:00 AM

You asked for a screen share and to watch her do a real file.

:::dialogue{title="Renee, at her desk, screen sharing"}
**You:** Walk me through the last one you decided.

**Renee:** Okay. This is a term loan, two fifty, HVAC contractor out of Greensboro.

*She opens the reviewer portal, then immediately opens a second window.*

**You:** What is that second window?

**Renee:** The statement PDF. I read it myself.

**You:** The portal shows you a revenue number.

**Renee:** It does.

**You:** Do you look at it?

**Renee:** I look at it to see how far off it is.

*She opens a third window. A spreadsheet. The filename is `revenue_check_v7_FINAL.xlsx`.*

**You:** What is that?

**Renee:** My check. I key in the deposits and it tells me what counts.

**You:** How long does that take?

**Renee:** Fifteen, twenty minutes. Longer if the scan is bad.

**You:** How many of the eleven underwriters do it this way?

**Renee:** I sent it to four of them. I do not know if they use it.
:::

She thinks the system's revenue number is unused by anyone. She is wrong about that in a
way that will matter in Phase 2. She is completely right about everything else.

### 2. Hank Delgado, Underwriting Manager, Wednesday 2:00 PM

:::dialogue{title="Hank, conference room, with a printed report"}
**Hank:** Before you ask. We hit our SLA ninety one percent of the time.

**You:** What is the SLA?

**Hank:** Five business days from complete file to decision.

**You:** Complete file meaning what, exactly?

**Hank:** All required documents received and passed intake QC.

*A pause while you do arithmetic.*

**You:** So the clock starts after the documents arrive.

**Hank:** That is the part we control.

**You:** And before that?

**Hank:** Before that is the applicant. If they take three weeks to send a bank
statement that is not my queue.

**You:** Does anyone report the number from application to decision?

**Hank:** Dale asks for it sometimes. I give him nine to ten days.

**You:** Where does that come from?

**Hank:** Finance pulls it. I do not know how.
:::

Here is the reason nobody at Northstar has noticed the problem. Hank's number is 91
percent green. Dale's number is nine to ten days and bad. Both are true, because they
measure different clocks, and the gap between the two clocks is where the entire project
lives.

### 3. Carla Mendes, Customer Support Lead, Thursday 9:00 AM

:::dialogue{title="Carla, on a video call with her ticket queue open"}
**You:** What is the thing you get asked about most?

**Carla:** Documents. Way ahead of anything else.

**You:** Asked what about documents?

**Carla:** "I already sent that." They send a bank statement, then a week later we ask
for it again.

**You:** How often?

**Carla:** All day. I have a saved search, hang on.

*She shares her screen. A filter called "RESUB (mine)".*

**Carla:** Six months. Four thousand one hundred eighteen tickets total. Fifteen forty
tagged document resubmission.

**You:** Has anyone asked you for this before?

**Carla:** For the tickets? No.

**You:** Three years?

**Carla:** Oh, that. Yeah, we just tell them to resubmit.
:::

Thirty seven percent of her support volume is one problem. She believes it is an upload
bug in the portal. It is partly an upload bug and mostly something else, which you will
not work out until Mission 05.

### 4. Bill Tran, Operations, Thursday 11:00 AM

:::dialogue{title="Bill, at his desk"}
**You:** What runs overnight?

**Bill:** Four jobs. Document sweep at 1, the LoanCore batch at 2, the finance extract
at 4, and then mine.

**You:** Yours?

**Bill:** `fix_stuff.sh`.

**You:** What does it fix?

**Bill:** There is a mismatch between what document service thinks it has and what is
in the bucket. Job reconciles it.

**You:** Since when?

**Bill:** 2022. Maybe late 2021.

**You:** Does anyone know why the mismatch happens?

**Bill:** Not that I have heard. It is fine, I run it by hand if it fails.

**You:** How often does it fail?

**Bill:** Couple times a month. It is fine.
:::

Ask for the script. He will send it. He does not think of it as software.

### 5. Adaeze Nwosu, Fraud Lead, Thursday 3:00 PM

:::dialogue{title="Ada, video call"}
**Ada:** What are you planning to feed the model?

**You:** Bank statements, to start.

**Ada:** Applicant-supplied PDFs.

**You:** Yes.

**Ada:** Assume the applicant is hostile. Then tell me what your design does.

**You:** I do not have a design yet.

**Ada:** Good answer. Come back when you do.

**You:** How much of the delay is fraud holds?

**Ada:** Four percent of files get a manual hold. Median two days.

**You:** So not the bottleneck.

**Ada:** Not the bottleneck. My service is well tested and badly wired in, and neither
of those is your problem this month.
:::

She thinks fraud holds are a bigger share of the delay than they are. She is the only
person in eleven interviews who asked what you were going to build before telling you
what to build.

### 6. Sam Ortiz, Senior Backend Engineer, Friday 8:15 AM

:::dialogue{title="Sam, second coffee"}
**You:** Renee keys deposits into a spreadsheet because the system's number is wrong.

**Sam:** ...Ah.

**You:** Where does that number come from?

**Sam:** `RevenueCalculator`. One method. It adds up every credit and divides by months.

**You:** Every credit.

**Sam:** Every credit.

**You:** Who calls it?

**Sam:** Decision service. Debt service coverage. And the portal, over REST.

**You:** The applicant-facing portal?

**Sam:** There is a cash flow widget. I doubt anyone looks at it.

**You:** Has anyone tried to change the function?

**Sam:** There is a TODO in it from 2019 that says do not change it without asking
Renee.

**You:** Who wrote it?

**Sam:** Jan Kowalski. He left in 2021.
:::

Sam believes the portal widget is unused. That belief is the trap in Mission 09.

### 7. Tomás Ferreira, Backend Engineer, Friday 10:00 AM

:::dialogue{title="Tomás, screen sharing his own code"}
**You:** What did you build most recently that you are proud of?

**Tomás:** The retry worker. Before that, a failed vendor call just dropped the
application.

**You:** What does it retry on?

**Tomás:** Any exception. Five attempts, exponential backoff.

**You:** Any exception?

**Tomás:** Timeouts, connection resets, 500s. Yeah.

**You:** What if the vendor returns a 200 with a body you cannot parse?

*He thinks about it.*

**Tomás:** That would throw in the mapper, so... it would retry.

**You:** Five times.

**Tomás:** Five times. Is that bad?

**You:** Was it reviewed?

**Tomás:** Janet approved it. I do not think anyone read it line by line.
:::

His code is not bad. Nobody read it. Write this one down and do nothing with it for
twenty eight missions.

### 8. Marcus Webb, VP Product, Friday 1:00 PM

:::dialogue{title="Marcus, walking between meetings"}
**You:** Where do you think the time goes?

**Marcus:** Underwriting. It is the only manual step left.

**You:** How do you know?

**Marcus:** It is the only place a human makes a judgment call. Everything else is
automated.

**You:** Have you watched an underwriter work?

**Marcus:** I have seen the portal.

**You:** How would you know if the project worked?

**Marcus:** Logins. If they are using it every day, it works.
:::

He is confidently wrong about the bottleneck and he is wrong about logins. He is also
going to become one of your two most useful allies, so do not enjoy this too much.

### 9. Doug Feinberg, Compliance, Monday 10:00 AM

:::dialogue{title="Doug, his office, with a binder"}
**Doug:** What happens when the model recommends a decline?

**You:** An underwriter reviews it.

**Doug:** And when we decline, what do we send the applicant?

**You:** An adverse action notice.

**Doug:** With specific reasons. Within thirty days. Reasons that reflect the actual
basis for the decision.

**You:** So if the model's reason is "the score was low," that is not enough.

**Doug:** That is not a reason, that is an output.

**You:** What if a human wrote the final reasons?

**Doug:** Then I need to know the human actually considered the file and did not just
click accept. I have to be able to show that.

**You:** Can you explain that decision to the applicant in writing. That is the test.

**Doug:** That is the whole test. You are the first person from a vendor who said it
back to me.
:::

Doug is not an obstacle. He just generated three architecture requirements in eight
minutes, and one of them (proving a human actually reviewed rather than clicked) shapes
everything you build in Phase 6.

### 10. Wendy Kaur, Frontend Lead, Monday 2:00 PM

:::dialogue{title="Wendy, screen sharing the reviewer portal"}
**You:** How was this laid out?

**Wendy:** It mirrors the paper form. Section by section.

**You:** Whose paper form?

**Wendy:** The 2016 credit application.

**You:** Do underwriters work in that order?

**Wendy:** No. Renee opens tab four first, every time. I have watched her do it.

**You:** Has anyone changed the order?

**Wendy:** I proposed it. It got deprioritized twice.

**You:** How many clicks to finish a review?

**Wendy:** I counted once. It depends. More than it should be.
:::

She has already done user research nobody asked for. Remember her name for Phase 8, when
she turns out to have been right for two years.

### 11. Priya Raghunathan, CTO, Tuesday 9:00 AM

:::dialogue{title="Priya, with an architecture diagram on the screen"}
**Priya:** This is the current state.

**You:** When was it last updated?

**Priya:** Last year. Maybe eighteen months.

**You:** Can I check two things against it?

**Priya:** Go ahead.

**You:** There is a `notification-service` on the diagram. It is not in the compose
file.

**Priya:** ...It was folded into application-service. 2024.

**You:** And there is a scenario control API on 8099 that is not on here at all.

**Priya:** That is test infrastructure. Sam built it.

**You:** Show me the blast radius question you would ask me, if I proposed touching
underwriting-service.

**Priya:** I would ask what breaks if you are wrong, and who finds out first.
:::

Her diagram is wrong in both directions: it contains something that does not exist and
omits something that does. She is not careless. Diagrams are snapshots and nobody is
funded to maintain them.

## Evidence

Two artifacts came out of the week. Both were sitting there the whole time.

:::evidence{type=ticket label="Carla's saved search, exported, Sept 2025 to Mar 2026"}
```text
Total tickets                                    4,118
  document resubmission                          1,540   (37.4%)
  status / where is my application                 902   (21.9%)
  portal login                                    511   (12.4%)
  payoff / servicing questions                    440   (10.7%)
  decline explanation                             288    (7.0%)
  other                                           437   (10.6%)

Top text in resubmission tickets (Carla's tags):
  "already sent"                                 1,104
  "which months"                                   372
  "file too large"                                 191
```
:::

:::evidence{type=log label="Bill's fourth cron job, emailed as an attachment"}
```bash
#!/bin/bash
# fix_stuff.sh - run nightly after doc sweep
# BT 2021-11, ticket OPS-2210 (closed, no notes)

psql -At -c "
  SELECT d.document_id, d.storage_key
  FROM northstar.documents d
  WHERE d.storage_key IS NOT NULL
    AND d.status = 'STORED'
    AND d.created_at > now() - interval '3 days'
" | while IFS='|' read -r id key; do
  if ! mc stat "minio/northstar-docs/$key" >/dev/null 2>&1; then
    echo "missing in bucket: doc=$id key=$key"
    psql -c "UPDATE northstar.documents SET status='UPLOAD_FAILED' WHERE document_id=$id"
  fi
done
```
:::

Read that script twice. It sets documents to `UPLOAD_FAILED` when the file is not in the
bucket. Which means the system regularly believes it has a document that it does not
have. Which means somebody asks the applicant for it again.

Carla's number is 1,540 resubmission tickets. Bill's script fails "a couple times a
month." Those two facts are related and neither person has met the other's data.

## What you do not know

- What are the eleven rules in Renee's spreadsheet?
- How many underwriters use it? She sent it to four and does not know.
- Why do documents go missing from the bucket?
- What is the real gap between Hank's clock and Dale's clock, in days?
- How much of the 5-plus days of document waiting is our fault versus the applicant's?
- Which of Carla's 1,540 tickets map to which applications?
- Who is Finance's analyst, and how do they compute the nine to ten days?

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

## Working through it

### The wrong turn: interviewing Marcus first

Marcus was the easiest person to book, because he wanted to be booked. So he went first,
on Monday, and you built your question list out of that conversation.

His framing was "underwriting is the bottleneck." So for the next two interviews you
asked variations of "where could AI help most in underwriting?"

Here is what that produced with Hank.

:::dialogue{title="Hank, first attempt, Tuesday 4:00 PM"}
**You:** Where do you think AI could help your team most?

**Hank:** Honestly? Hiring. We are two people short.

**You:** In the review process, I mean.

**Hank:** I would have to think about it. Faster document review, maybe.

**You:** Anything else?

**Hank:** Not off the top of my head. Send me a list and I will react to it.
:::

That interview produced nothing and cost you forty minutes plus a rebook. Compare it to
Wednesday, when you asked him for his SLA report and he opened with 91 percent, which
turned out to be the single most useful sentence of the week.

The cost was not the forty minutes. It was the near miss. On Tuesday you were one
question away from writing "faster document review" into your notes as a requirement
from the underwriting manager. It would have sounded credible in a readout, and it was an
opinion he formed in the four seconds after you asked him.

### Why "what do you want" fails

It sounds respectful. It is a request to do your job for you.

The person answers because they are polite, and the answer comes from whatever they can
retrieve in four seconds. Then you have a stated requirement with a name attached, which
is very hard to drop later, and they feel committed to an idea they invented under time
pressure. You learned nothing about the work, because a wish is not evidence.

Ask about the past instead. The past is fixed, specific, and checkable. And interview the
people who perform the work before the people who describe it, because the first group
gives you the vocabulary you need to ask the second group anything useful.

### The questions that actually worked

Six questions produced almost everything in this mission.

**"Walk me through the last one you did."** Renee's spreadsheet came from this. Note the
two constraints: the last one, so they cannot pick a flattering example, and walk me
through, so they narrate rather than summarize. If they start summarizing, ask what
happened next.

**"Can you show me?"** Say it every time. A screen share converts a description into an
observation. Renee's third window is the entire discovery phase and she never would have
mentioned it, because to her it is not part of the system. It is just how she works.

**"How do you know when the system is wrong?"** This gets you the workaround. Every
experienced operator has a wrongness detector and a routine that follows it. Both are
undocumented, and the routine is usually the real business logic.

**"Has anyone asked you for this before?"** Carla's "no" told you her ticket queue had
never been read. That is a statement about the company, not about tickets. When the best
data in the building has never been requested, you know how decisions get made here.

**"Who do you call when you are stuck?"** This builds the real org chart. Everyone's
answer contained Sam.

**"What would you have to stop doing if we took that away?"** Save this one. Ask it about
the workaround, not the system. When you eventually ask Renee what she would stop doing
if the spreadsheet went away, the answer is the acceptance criteria for the whole
project.

And one question to ask compliance, always, in the first week: "what do you have to be
able to prove?" Doug answered it in eight minutes and gave you more architecture than
anyone in engineering.

### Reconciling eleven honest accounts

Nobody lied. Each person described the slice of the process they can see, and the slices
barely overlap. The method for reconciling them is not to average the accounts. It is to
find the places where two accounts cannot both be true, then go get data.

| Conflict | Person A | Person B | How to settle it |
|---|---|---|---|
| Where the time goes | Marcus: underwriting | Renee: waiting on documents | Measure state durations from `application_events` |
| Is the process fast | Hank: 91% on SLA | Dale: 9 to 10 days | Compare clock start points. Both are right. |
| Are documents resent because applicants are slow | Hank: applicant's fault | Carla: we ask twice | Join resubmission tickets to application events |
| Is the revenue number used | Sam: portal widget unused | n/a | Check access logs on the widget endpoint |
| Are documents actually received | `documents.status` = STORED | Bill's script says missing | Count rows flipped to UPLOAD_FAILED per night |

Every row in that table is a query. None of them is a meeting. That is the point of a
week of interviews: it converts opinions into a short list of things you can measure, and
Mission 05 is where you measure them.

## Then this happens

Wednesday morning, Renee sends you something unprompted.

:::evidence{type=slack label="DM from Renee Blackwell, 7:52 AM"}
```text
Renee:  You asked how many of us use the sheet.

Renee:  I asked around. 6 of 11. Two of them have their own version.

Renee:  Kevin's has an extra tab for equipment loans that mine doesn't.

Renee:  Attached: revenue_check_v7_FINAL.xlsx

Renee:  Please don't send this to Marcus.
```
:::

Read the last line carefully. She did not say do not use it. She said do not send it to
Marcus.

She is protecting herself from the version of this project where her spreadsheet gets
labeled shadow IT and taken away. That is a rational fear, and if you forward that file
to a VP of Product this week, you lose her, and losing her means the project fails in
month four for reasons nobody will trace back to this Wednesday.

What you send back:

:::evidence{type=slack label="Your reply, 8:04 AM"}
```text
You:    I won't. Two things I want to promise you.

You:    1. If your rules are right, they end up in the system with your
        name on them, not deleted. If they're wrong I'll show you why
        before I show anyone else.

You:    2. Nothing about how you work changes because of anything I
        write in the next 3 weeks. I'm measuring, not designing.

You:    Can I have 45 min next week to go through the sheet rule by
        rule? Bring Kevin if he'll come.

Renee:  Ok. Thursday?
```
:::

There is a real problem in that file. Six of eleven underwriters are applying credit
rules from desktop spreadsheets with no review, and two have local variants. That is a
fair lending exposure and Doug does not know about it.

You will have to tell Doug. Not this week, not without Renee in the room, and not framed
as her mistake. The spreadsheet exists because the system gave her wrong numbers and she
had a job to do. Any version of that conversation which skips that fact is both unfair
and tactically stupid.

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

:::commslab
Four follow-ups from the same week.

#### To Renee

> I want your rules in the system with your name on them. If any of them turn out to be
> wrong I will show you first, before anyone else sees it.

She is protecting a tool that makes her job possible. Say what happens to it, concretely,
and then do that.

#### To Carla

> Your ticket queue answered a question I have been asking engineers for a week. Can I
> cite it in the CEO readout on the twenty first, with your name on the slide?

The best data in the company has never been read. Credit is the cheapest currency you
have and she has never been paid in it.

#### To Marcus

> You said underwriting is the bottleneck. I am measuring it this week. If you are right
> your six items get easier to defend. If you are wrong I want you to see the number
> before Dale does.

He is going to be wrong. Give him a version of being wrong that costs him nothing.

#### To Doug

> Six of eleven underwriters are applying revenue rules from a spreadsheet on their
> desktop, and at least two have local variants. I found out this week. I want to bring
> you the full picture with Renee present, next week, because the reason it exists is
> that the system gave them a wrong number.

Do not sit on this and do not fire it off in a channel. Compliance findings delivered
badly turn a fixable problem into a personnel problem.
:::

## Practice

Different industry, same week.

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
