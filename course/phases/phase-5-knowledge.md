---
number: 5
slug: phase-5-knowledge
title: Knowledge
subtitle: Eight policy documents, four of which are named FINAL, and one tenant who should not see another tenant's rules.
summary: Retrieval that works, retrieval that quietly returns a dead policy, and a leak that a prompt change cannot fix.
arc: Retrieval is an authorization surface. Almost nobody treats it like one.
---

Three missions on getting the right information in front of the model.

Renee has the policy memorized. The reviewer portal does not. When a junior underwriter
needs to know the minimum time in business for an SBA 7(a) loan in California under the
Cascade brand, the answer lives in three documents, two of which contradict each other,
and one of which stopped applying in March.

This is where RAG shows up. Not as a technique to learn, but as the only reasonable
answer to a question you cannot solve any other way.

## What you do here

You build retrieval over the policy corpus and it works well enough to demo, which is
where most teams stop.

Then Renee looks at an answer and says the sentence that starts Mission 23. The system
quoted `credit-policy-FINAL.pdf`. That file is a 2023 draft that was never adopted. It
is semantically the closest match to the question, and it is completely wrong. Fixing
this is not a chunking problem. It is a metadata and precedence problem, and you have
to go extract the precedence rules from Doug and Renee because they exist in no
document.

Then Mission 24, which is worse. A reviewer at Cascade gets an answer that cites
Bayline's pricing overlay. That is one customer seeing another customer's confidential
terms. The root cause is a real authorization bug in the retrieval path, and no amount
of prompt instruction will close it.

## What you will get wrong

When the leak appears, your first instinct will be to add a line to the system prompt
telling the model not to reference other tenants. Write that instinct down. Mission 24
explains exactly why it fails, and it is the same reason a `WHERE` clause belongs in
the query and not in a comment.
