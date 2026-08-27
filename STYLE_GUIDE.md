# STYLE_GUIDE.md

Every word in this course follows these rules. No exceptions.
This applies to missions, docs, code comments, UI text, and commit messages.

---

## Rule 1: Eighth grade reading level

Write so a smart 13 year old could follow the sentence structure, even if the
technical topic is above them.

**How to hit it:**

- Keep most sentences under 20 words.
- One idea per sentence.
- Use the common word. Say "use" not "utilize". Say "start" not "initiate".
- Active voice. "The parser fails" beats "a failure is experienced by the parser."
- Break long sentences into two short ones.
- Cut clauses that only add rhythm.

**Technical terms are allowed.** Words like idempotency, tenant, and OCR have to
appear. When a term shows up for the first time, explain it in one plain sentence,
then use it freely after that.

Bad:

> Given the inherent non-determinism of large language models, it becomes necessary
> to establish evaluation infrastructure prior to deploying any inference-dependent
> workflow into a production environment.

Good:

> The model gives different answers to the same question. So you need a way to
> measure it before you ship it.

---

## Rule 2: No em dashes

Never use the em dash (the long one). Never use an en dash as a substitute either.

Replace it with:

- A period. Two short sentences are almost always better.
- A comma.
- A colon, when a list or an explanation follows.
- Parentheses, for a real aside.

Bad:

> The model returned a string — not a number — and the parser threw.

Good:

> The model returned a string instead of a number. The parser threw.

In tables, use "n/a" or leave the cell empty. Do not use a dash as a filler.
Hyphens inside words are fine. "Multi-tenant" and "read-only" are normal words.

---

## Rule 3: No AI fingerprints

These patterns make writing sound machine generated. Do not use them.

**Banned words and phrases:**

delve, tapestry, landscape (as a metaphor), realm, testament to, navigate the
complexities, embark, unlock the power, harness, elevate, seamless, robust (unless
you mean it literally), leverage (as a verb), streamline, crucial, pivotal, vital,
game changer, paradigm, holistic, synergy, cutting edge, state of the art, in
today's fast paced world, it is important to note that, it is worth noting,
that said, rest assured, dive in, deep dive, let's explore, journey.

**Banned sentence shapes:**

- "It's not just X. It's Y." This construction is the loudest tell there is.
- "X isn't about Y. It's about Z."
- Three item lists used for rhythm rather than because there are three things.
  If there are two reasons, give two.
- Starting sentences with Moreover, Furthermore, Additionally, or Indeed.
- Ending a section with a summary sentence that repeats what you just said.
- "Whether you're a beginner or an expert..."
- Rhetorical questions used as transitions.

**Banned formatting habits:**

- Emoji. None, anywhere, unless a piece of evidence realistically contains one
  (a Slack message can have a reaction).
- Bolding for emphasis more than once or twice per section.
- A heading for every paragraph.
- Bullet lists where a sentence would do.

---

## Rule 4: Sound like a person who has done the job

The voice of this course is a working engineer talking to a colleague. Direct,
specific, a little tired, occasionally funny.

- Prefer the concrete number over the adjective. "9.4 days" beats "very slow."
- Name things. "Sam's revenue function" beats "a legacy component."
- Admit uncertainty when it is real. "Nobody knows why this cron job exists" is a
  fine thing to write.
- Humor comes from the situation, not from jokes you insert. A file named
  `revenue_check_v7_FINAL.xlsx` is funny by itself. Do not add a wink after it.

---

## Rule 5: Dialogue rules

Most teaching happens in conversation. Dialogue has its own bar.

- People interrupt, hedge, and go quiet. Write that.
- Nobody explains a concept in a clean paragraph out loud. Break it up.
- Characters should disagree and both be partly right.
- Never write a character who exists only to be corrected.
- Keep turns short. Four lines is long for one turn.
- No character says "great question."

---

## Rule 6: Quick self check before saving a file

Read the draft and ask:

1. Did I use an em dash? Fix it.
2. Is any sentence over 25 words? Split it.
3. Did I use a banned word? Replace it.
4. Would a working engineer say this out loud? If not, rewrite.
5. Is there a number I could use instead of an adjective?
