---
number: 9
slug: phase-9-productization
title: Productization
subtitle: A second customer wants the same thing, except almost none of it is the same.
summary: Deploying to a bank with a different workflow, resisting the customer name if-statement, and working out which parts of Northstar's solution were actually product.
arc: The second customer is what tells you which of your decisions were principles and which were accidents.
---

Two missions, and they are the reason this job has the word "forward" in it.

Redwood Bank is not Northstar. They do equipment financing through branch officers
instead of an online portal. Their core banking system is a vendor product from 2009
that talks over SFTP on a nightly batch. They have no Kafka. Their credit decisions go
through a two person committee that meets on Tuesdays and Thursdays. Their compliance
posture is tighter because they take deposits.

They saw a demo of what you built for Northstar and they want it.

## What you do here

Mission 39 puts you in the Redwood deployment with a working Northstar system and a
customer whose workflow breaks four of your assumptions. You will feel real pressure to
write this:

```java
if (customer.equals("NORTHSTAR")) {
    // ...
} else if (customer.equals("REDWOOD")) {
    // ...
}
```

That code is not a joke. It is what actually happens, it ships, and it works for about
seven months. Mission 39 lets you write it and then makes you live with it long enough
to feel the specific way it goes bad.

Mission 40 is the extraction. Which parts are platform, which are adapters, which are
configuration, and which should stay customer specific forever. The hard part is not
building an abstraction. The hard part is knowing that two examples is the earliest
you can responsibly build one, and that some things with two examples still should not
be abstracted.

## What you will get wrong

You will over-abstract. Given two customers, you will design for eight. Mission 40
shows you the cost of the abstraction you did not need, which is usually paid by the
third customer, who does not fit it either.
