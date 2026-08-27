---
number: 4
slug: phase-4-documents-and-money
title: Documents and Money
subtitle: A PDF of a photo of a fax, and a number that decides whether a business gets funded.
summary: Document intake, OCR failure that looks like success, classifying bank transactions, and drawing the line between what the model decides and what code decides.
arc: The model should never do the arithmetic.
---

Four missions on the actual problem you re-scoped to in Phase 1.

Northstar's applicants send bank statements. Some are clean PDFs from a bank portal.
Some are photos taken at an angle in a truck. One is a scan of a fax of a printout,
and it is not the only one.

Somewhere in those documents is a number: how much money does this business actually
make. Everything downstream depends on it. Getting it wrong in one direction declines
a business that deserved funding. Getting it wrong in the other direction funds one
that cannot pay it back.

## What you do here

You build intake that does not create three copies of a document when someone taps
upload twice on a bad connection.

You find out that OptiScan, the OCR vendor, does not fail loudly. It returns clean,
confident, well formed output that is wrong. Its confidence score does not correlate
with whether it is right, and you have to prove that with data before anyone believes
you.

Then Mission 20, which is the mission this whole course is built around. Five
transactions. A naive sum says 252,400. The correct operating revenue is 147,400. The
gap is an internal transfer and a loan from a competitor. Renee spots it instantly.
The system has never caught it once.

You will be tempted to hand the whole thing to the model. Mission 21 is about where to
put the seam instead.

## What you will get wrong

You will let the model add the numbers up. It will be right most of the time, which is
the worst possible outcome, because it means you will not notice until an underwriter
does.
