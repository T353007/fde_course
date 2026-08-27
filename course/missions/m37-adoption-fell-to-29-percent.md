---
id: M37
slug: adoption-fell-to-29-percent
title: Adoption Fell to 29 Percent
subtitle: "Week 1 was 67 percent. Week 3 is 29. The model did not get worse. The workflow did not get better."
phase: 8
order: 37
duration: 240
difficulty: 4
lab: false
status: complete
objectives:
  - Separate model quality regressions from workflow adoption failures
  - Run user interviews that reveal friction instead of opinions about AI
  - Map the click path that makes a correct suggestion useless
  - Repair the workflow with Wendy instead of "training users harder"
concepts: [adoption, user research, workflow friction, human in the loop, suggestion timing]
competencies: [adoption, evals]
prereqs: [M29, M36]
---

## Where you are

Yuki and Doug signed off on the blockers. The flag is wider. Eval dashboards still look
fine. Marcus sends a chart in the channel with no caption, which is how he panics.

## The request

:::evidence{type=metrics label="Reviewer suggestion acceptance, trailing weeks"}
```text
Week 1:  67%
Week 2:  48%
Week 3:  29%

Definition Marcus used: accepted suggestions / shown suggestions
among reviewers who logged in at least once that week
```
:::

:::evidence{type=slack label="#northstar-ai, Wednesday 8:41 AM"}
```text
Marcus:  adoption is falling off a cliff
Marcus:  is the model drifting
Marcus:  should we fine tune

Hank:    my people say it slowed them down
Hank:    What does that do to my queue?

Wendy:   I filed this in Phase 6
Wendy:   six clicks to accept. suggestion arrives after they already decided

Renee:   We don't use that number.
Renee:   Meaning the suggestion. By the time I see it I already have an answer.
```
:::

## The conversation

:::dialogue{title="Marcus's desk, Wednesday 9:10 AM"}
**Marcus:** Can't the AI just be more confident so people trust it?

**You:** Confidence is not the metric that moved.

**Marcus:** Evals?

**You:** I will check. If evals are flat, this is not a model story.

**Wendy:** *from the doorway* It is a portal story. I said it when we shipped the
copilot. You wanted the panel on the summary tab because it looked clean in the demo.

**Marcus:** We needed something visible for Dale.

**Wendy:** Visible is not usable.
:::

Wendy was right in Mission 29. She is still right. Your job is to prove it with
evidence Marcus cannot wave away, without humiliating him in public.

Hank walks by with coffee and says the quiet part.

:::dialogue{title="Hallway"}
**Hank:** What does that do to my queue if people ignore the panel on purpose?

**You:** Then the panel is not part of the process. It is decoration.

**Hank:** Fix the process. Do not schedule another training. We tried training in
Week 2. That is when it fell to 48.
:::

## Evidence

:::evidence{type=test label="Eval suite this morning vs three weeks ago"}
```text
                week0   week3
overall         96.0    95.7
loan_proceeds   68.0    67.4
poor_ocr        61.0    60.8
card_settle     99.1    99.0
```
:::

Flat. Not the cliff.

:::evidence{type=metrics label="Suggestion timing vs decision time"}
```text
median time from case open → underwriter decision click ..... 6.2 min
median time from case open → suggestion panel ready ........ 7.9 min
share of accepts among suggestions shown before decision ... 61%
share of accepts among suggestions shown after decision .... 11%
```
:::

:::evidence{type=ticket label="Wendy's Phase 6 ticket, still open"}
```text
Title: Copilot accept path is six clicks
Status: Backlog
Description:
1) Open application
2) Open documents
3) Open statement
4) Jump to summary tab
5) Expand AI panel
6) Click accept
7) Confirm modal
Underwriters decide on the documents tab. Panel is elsewhere.
```
:::

She counted six interactions to accept. The confirm modal makes it worse. The important
part is step location: the suggestion does not live where the decision happens.

:::evidence{type=slack label="Renee, after interview 1"}
```text
Renee:  I already had the Fastcapital loan spotted before the panel drew
Renee:  then it suggested excluding loan proceeds
Renee:  correctly
Renee:  and asked me to confirm a confirm
Renee:  We don't use that number. We also do not use that UX.
```
:::

:::evidence{type=metrics label="Login vanity vs useful assist"}
```text
Week 3 reviewers with >=1 login .............................. 11/11
Week 3 reviewers who opened AI panel ......................... 6/11
Week 3 accepts ................................................ 29% of shown
Week 3 suggestions shown after human decision already saved .. 71% of shown
```
:::

Marcus's denominator is "shown." Most "shown" events are late. The metric is punishing
the product for appearing after the work ended.

## What you do not know

- Whether "29 percent" counts dismissed suggestions that were never seen
- How Bayline reviewers differ from NSC_DIRECT
- What Hank told his team in the staff meeting after Week 1
- Whether Renee's spreadsheet is absorbing work the copilot was supposed to take

You already suspect the spreadsheet. In interview 2 she shares her screen for twelve
seconds too long.

:::evidence{type=spreadsheet label="revenue_check_v7_FINAL.xlsx, visible sheet edge"}
```text
col F: "AI suggestion?" 
rows mostly blank
two rows: "late" and "wrong tab"
```
:::

She built a tracking column for your product and abandoned it. That is adoption data
you will not get from Marcus's login chart.

:::task{time="120 min"}
1. Recompute adoption with at least two definitions: (a) Marcus's login-based rate,
   (b) accepts among suggestions that appeared before the human decision.
2. Interview six reviewers (use the lab personas / scripts if live interviews are not
   available). Ask them to open a real case and think aloud. Do not ask "do you like
   the AI?"
3. Produce a one page friction map: where the suggestion appears, when it appears, and
   what the click path is.
4. With Wendy, propose the smallest portal change that puts accept within one click of
   the decision surface and shows the suggestion before opinion hardens.
5. Write the note to Marcus explaining why fine tuning is the wrong next spend.
:::

:::stopandthink
Before you schedule model work:

1. What evidence would convince you this *is* a model quality problem?
2. What evidence do you already have that it is not?
3. If you "train the users," what are you actually refusing to fix?
4. How will you bring Marcus along without making Wendy's "I told you" into the story?

Two minutes.
:::

## Working through it

### The wrong turn

You almost open a fine-tune proposal. Jordan likes it because it sounds like progress.
You pull Week 3 misses and find a handful of ugly loan-proceeds cases. It feels
productive.

Then you sit with Devon, a mid-level underwriter, for twenty minutes.

:::dialogue{title="Interview 3 of 6, Devon's screen share"}
**You:** Open the next case the way you normally would.

**Devon:** Documents tab. Statements. I skim Stripe and transfers. I already know if
revenue is real.

**You:** When do you look at the AI panel?

**Devon:** If Hank asks. Or if I am unsure. Usually I have clicked decision before the
panel finishes. Then it pops and asks me to accept something I already did.

**You:** What if it was right?

**Devon:** Then it is a homework grade on work I finished. I dismiss it.

**You:** How many clicks to accept when you try?

**Devon:** Too many. There is a confirm. I stop.
:::

Five of six interviews rhyme. One junior reviewer likes the panel because they are
still learning. They are not the throughput bottleneck.

Fine tuning would polish an answer nobody is positioned to use.

### The interview guide you actually use

Do not ask "Would AI help you?" That collects fantasies. Ask them to work.

```text
1. Open the next case. Talk through what you look at first.
2. When do you feel ready to decide?
3. Where is the AI panel right now relative to your eyes?
4. Try to accept a suggestion the way the UI wants. Count clicks out loud.
5. What would make you use this without Hank asking?
```

Write timestamps while they work. The clock is the argument.

:::evidence{type=ticket label="Your notes, interview 5 condensed"}
```text
Reviewer: Priya-of-underwriting (different Priya), 11 years
Ready to decide: 4:10 after open
Panel ready: 8:02
Clicks to accept when forced: 6 + confirm
Quote: "It grades my homework after I turned it in."
```
:::

### Tracking it down

Adoption math that matters:

```text
Shown before decision, accepted .................. useful assist
Shown after decision, dismissed ................. noise
Never shown because user never left docs tab .... design miss
Logged in but never opened a flagged case ....... Marcus vanity metric
```

Marcus measured logins and accepts over shown. As people learned the panel was late and
heavy, they dismissed more. The rate fell. The model stayed put.

Wendy's fix is unglamorous:

1. Render the suggestion on the documents tab beside the statement.
2. Start inference when the case opens, not when the panel expands.
3. Accept is one click. Undo is allowed. Drop the confirm modal for accept. Keep confirm
   for decline recommendations if compliance wants friction there.
4. If the human already decided, do not ask for accept. Ask "file for audit" or hide.

### Then this happens

You pilot the documents-tab placement with three reviewers for four days.

:::evidence{type=metrics label="Pilot cohort, four days"}
```text
acceptance among pre-decision suggestions: 58%
median suggestion ready: 2.4 min after open (was 7.9)
Hank: "queue feels less stupid"
Marcus: "can we call this adoption recovery in the readout?"
```
:::

Marcus wants a victory slide. Keep him honest. 58 percent on a tiny pilot is not Week 1
nostalgia. It is evidence the workflow was the lever.

Also expect a new complaint: early suggestions on poor OCR still wrong. That is an eval
slice problem, not a reason to resurrect six clicks.

:::dialogue{title="Interview notes readout with Marcus and Wendy"}
**You:** Six interviews. Five decide on the documents tab. Suggestion is late and far.

**Marcus:** So we need better onboarding copy.

**Wendy:** No.

**You:** Evals are flat. Fine tuning is the wrong spend. Wendy's ticket is the fix.

**Marcus:** If we move it, Dale will not see the panel on the summary screenshot.

**Wendy:** Dale does not underwrite. Put the screenshot on the documents tab.

**Marcus:** ...Okay. Pilot three people. If Hank likes it I will stop measuring logins
as adoption.
:::

That last line is the Phase 8 turn the course promised. Marcus becomes useful when the
evidence is about users, not about his demo aesthetic.

### The better version

Bring Marcus a chart with two lines: model overall accuracy (flat) and pre-decision
accept rate (moved with UX). Put Wendy's name on the fix. Phase 6 overruled her. Phase
8 should not repeat that quietly.

:::evidence{type=email label="Note to file after the pilot"}
```text
Adoption week3 29% was not model drift. Pre-decision accept in the
documents-tab pilot is 58% with suggestion ready at 2.4 minutes.
Next rollout gate: panel default on documents tab, one-click accept,
no post-decision nag. Eval watch on poor_ocr remains separate work.
```
:::

Hank's staff meeting the following Monday uses your framing. That matters more than
Marcus's chart color.

You close the mission by updating the success metric in the engagement notes:

```text
Old: % of logged-in reviewers who accept a suggestion
New: % of suggestions shown before decision that are accepted or explicitly dismissed
      with a reason, on the documents tab surface
```

Marcus agrees to put the new definition in the readout appendix. That is how adoption
stops being a vanity number.

:::judgment
**When usage falls and evals are flat, stop tuning the model and start watching the
human's hands.**

Adoption is not a vibe and it is not logins. It is whether a correct answer arrives in
time, in place, with a cheap way to act. FDEs lose months fine tuning products that
lost the workflow argument in a design review. The tell is a domain expert saying they
already decided before the UI asked. Believe them. Instrument timing. Sit beside users.
Fix the click path with the frontend lead who warned you, and keep model work for the
slices that are actually wrong.
:::

:::commslab
#### To Marcus

> Evals are flat. Acceptance fell because the suggestion shows up after the decision
> and takes too many clicks. We are piloting Wendy's placement on the documents tab.
> Fine tuning will not fix late UI.

#### To Hank

> We are moving the assist to where your team already works and making accept one click.
> I want four days of feedback from three reviewers before we force it on everyone.

#### To Wendy

> You were right in Phase 6. I am not going to make this "a product insight we just
> had." Help me ship the smallest version.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital discharge AI drafts follow-up orders. Week 1 accept rate 62 percent. Week 3
is 24 percent. Model evals are flat. Nurses say the draft appears on a different tab
after they already entered orders in the EHR. Accept takes five clicks and a confirm.
A physician executive asks for a fine-tuned model on "hospital language."

**Your task**

1. What is your primary hypothesis?
2. Which two metrics prove or kill it?
3. What do you say to the physician executive?

---

**Notes, after you have written yours**

Primary hypothesis: workflow timing and placement, not model quality. Metrics:
suggestion-ready vs first order entry time, and accept rate for drafts shown before
entry. Tell the executive fine tuning waits until the draft appears where orders are
written with one-click accept. Otherwise you will polish text nobody uses.
:::
