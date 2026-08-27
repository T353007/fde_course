---
number: 2
slug: phase-2-archaeology
title: Archaeology
subtitle: Eleven years of decisions, three tenant ID conventions, and one spreadsheet that runs the company.
summary: Reading an unfamiliar system, finding hidden dependencies, sorting out who owns which data, and recovering business rules that were never written down.
arc: Every terrible thing in this codebase was once a reasonable decision.
---

Four missions in someone else's code.

Northstar's platform was started in 2013 by three people who had eight weeks. It has
been patched by roughly forty engineers since. Nobody currently employed there was
present for the original design decisions, and the person who understood the
underwriting service best left in 2021.

This phase teaches a specific skill, and it is not "reading code." It is figuring out
what a system actually does when the documentation describes what it was supposed to
do, the tests cover the parts that were easy to test, and the person who wrote it is
gone.

## What you do here

You map the architecture from evidence instead of from diagrams. Priya's diagram is 18
months old and it is wrong in one important way that matters later.

You find `calculateMonthlyRevenue()`. Three services call it. Two of them want
different answers from it. Nobody knows this. You get to be the one who tells them.

You find out that the same small business exists in the database four times, with four
different applicant IDs, and that this is not a bug so much as a decision from 2017
that nobody revisited.

And you sit down with Renee and go through `revenue_check_v7_FINAL.xlsx` cell by cell
until you have extracted eleven business rules that exist in no repository, no
document, and no person's memory except hers.

## What you will get wrong

You will want to fix things. Several of the things you find are genuinely broken and
you will be able to see the fix in about four minutes.

Do not fix them yet. Mission 09 shows you what happens when you change a function that
three services depend on and only one of them has tests. Your credibility in this
building is worth more than any single fix, and you have not earned it yet.
