---
slug: cast
title: Who Is Who at Northstar
subtitle: Fifteen people, what each of them knows, and what each of them is wrong about.
kind: reference
order: 3
---

Keep this open during the discovery missions. The fastest way to be useless at a
customer is to talk to the wrong person about the wrong thing.

One rule before the list. **Nobody here is stupid, and nobody is the villain.** Every
wrong belief in this building has a reason behind it that made sense when it formed.
Your job is to find the reason, not to correct the person.

---

## Your side

### Imtiaz Alam, Forward Deployed Engineer, Halyard AI

That is you. First account on your own.

Knows: less than everyone in the room on day one, which is useful for about two weeks.
Wrong about: how much of the SOW was already promised in a hallway.
Watch for: the urge to build before you can measure.

### Nadia Ferrante, Principal FDE, Halyard AI

Your mentor and manager. Shows up at decision points, usually by Slack, occasionally to
stop you from doing something expensive.

Knows: how these projects fail, and the order they fail in.
Wrong about: how long compliance takes. She has never worked inside a regulated shop.
Watch for: she asks questions instead of answering them. The question is the answer.

### Jordan Hale, Account Executive, Halyard AI

Sold the deal. Warm, relentless, and has already told the customer things you did not
agree to.

Knows: what the customer actually wants to buy, which is not the same as what they
asked for.
Wrong about: what is technically reachable in ten weeks.
Watch for: "I may have set expectations."

---

## Northstar leadership

### Dale Whitmore, CEO

Former commercial banker. Not technical. Sharper than he lets on. He wants AI because
Fastcapital put out a press release.

Knows: he is losing deals on speed and it is costing real money.
Wrong about: where the time goes. He thinks it is underwriting because underwriting is
the part he can see.
Talk to him about: deals won and lost. Never about your method.

### Priya Raghunathan, CTO

Joined in 2019 to clean up the platform and has been firefighting since. She will back
you if you respect her team.

Knows: which parts of the system are dangerous.
Wrong about: her own architecture diagram, which is 18 months old.
Talk to her about: blast radius. It is the word she uses and the thing she cares about.

---

## Product and engineering

### Marcus Webb, VP Product

High energy, ships things, promises too much. Writes requirements as solutions.

Knows: the roadmap, the politics, and what Dale will say yes to.
Wrong about: adoption. He measures it by logins.
Watch for: he talks to Dale on Sundays. A Friday night email from Marcus is not a
draft, it is a proposal already in motion.

### Janet Osei, Engineering Manager, Lending Platform

Controls the roadmap. Suspicious of consultants who drop a demo and leave, because that
has happened to her twice.

Knows: what her team can actually absorb.
Wrong about: nothing important. She is mostly right and mostly ignored.
Talk to her about: who is on call. Have an answer before she asks.

### Sam Ortiz, Senior Backend Engineer

Nine years here. Knows where every body is buried and stopped being surprised in about
year four.

Knows: more than the documentation, the diagrams, and the tests combined.
Wrong about: how much of what he knows is written down anywhere. He assumes people know
things they do not.
Watch for: when Sam goes quiet, or says something in twelve words and stops, he has
just told you something important and is waiting to see if you caught it.

### Tomás Ferreira, Backend Engineer

Two years in. Earnest, fast, under-mentored.

Knows: the newer code, because he wrote a lot of it.
Wrong about: retry logic, in a way that costs the company a bad Tuesday.
Be careful: when his code causes an incident, how you handle it in front of his team
matters more than the fix.

### Wendy Kaur, Frontend Lead, Reviewer Portal

Cares about how many clicks a task takes.

Knows: what the reviewers actually do all day, because she watches them.
Wrong about: nothing. She is right early and gets overruled.
Note: if you find yourself explaining to Wendy why the workflow is fine, stop and go
watch a reviewer use it.

---

## The business

### Renee Blackwell, Senior Underwriter

Fourteen years. She is the most important person in this course.

She keeps `revenue_check_v7_FINAL.xlsx` on her desktop. It holds eleven business rules
that exist nowhere in the code. She built it because the system gave her wrong numbers
and she still had a job to do.

Knows: how lending actually works at this company. All of it.
Wrong about: almost nothing in her domain. On one specific case in the eval set she
disagrees with a junior underwriter and she is right for a reason she has never written
down.
Watch for: "We don't use that number." When she says that, stop and find out why.

### Hank Delgado, Underwriting Manager

Owns the SLA. Wants throughput.

Knows: the queue, the backlog, and who is behind.
Worried about: whether "AI" means "fewer underwriters." He is not entirely wrong, and
pretending otherwise will cost you his trust.
Talk to him about: what this does to his queue.

### Adaeze Nwosu, Fraud Lead

Goes by Ada. Trusts nothing, correctly.

Knows: how applicants actually try to cheat.
Wrong about: how much the rest of the company understands about fraud. She assumes
context nobody has.
Watch for: she is the first person to notice the prompt injection, and she will be right
about a risk before you can prove it.

### Bill Tran, Operations

Runs four cron jobs. Three are documented. The fourth is called `fix_stuff.sh`.

Knows: what actually keeps the pipeline moving at 6 a.m.
Wrong about: how load-bearing his manual work is. He thinks it is minor. It is not.
Watch for: "It's fine, I run it by hand if it fails."

### Carla Mendes, Customer Support Lead

Knows every workaround because she invented most of them.

Knows: what applicants actually experience, in volume, with dates.
Wrong about: whether anyone wants to hear it. Nobody has ever asked her.
Note: her ticket queue is the highest quality data source in the building. Read it in
Mission 04, not later.

### Doug Feinberg, Compliance

Cares about adverse action notices, fair lending, and model governance.

Knows: what will get Northstar in trouble.
Wrong about: nothing, but he will say no to things that could have been yes if you had
designed for him from the start.
Talk to him about: whether you can explain a decision to an applicant in writing.
Bring him in early. Bringing him in late is how features die.

### Yuki Sato, Security Engineer

Threat models for a living.

Knows: how your system gets abused.
Wrong about: nothing you will win an argument about.
Watch for: "Say 'just' one more time." If you are using the word "just" to describe a
control, you have not thought it through.

---

## How to use this list

In discovery, ask each person for three things:

1. **Walk me through the last one you did.** Not the process. The last real one.
2. **Show me the artifact.** The spreadsheet, the ticket, the query, the email thread.
3. **What happens when it goes wrong?** The exception path is where the real system lives.

Never ask "what do you want." You will get a feature request, and a feature request is
a solution someone already picked without telling you what problem it solves.
