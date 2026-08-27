# Prior vendor postmortem

Author: Jordan Hale, Director of Lending Ops (inherited the mess)
Date: 2025-11-18
Status: Internal. Not shared with the vendor.

## What we bought

In March 2025 we hired LatticeFlow AI to "put an AI underwriter in production by
Labor Day." The SOW listed an agent that could read packages, score risk, and
draft decisions. Price: $420,000 plus usage.

## What happened

LatticeFlow demoed well on six clean packages from Region 1. Production packages
are not clean. Region 2 still emails PDF bundles. Region 3 uses a different core
banking cut (v1.4) than the swagger we were given (v2).

By August the agent was drafting memos that looked fluent and cited the wrong
policy version twice in one week. Credit committee started ignoring the drafts.
Adoption in week 6 was under 20%. LatticeFlow blamed "change management." Ops
blamed "the model." Both were partly right and both missed the main issue.

## The actual bottleneck we found later

Median time from application to decision was 11.2 days. Median credit committee
hands-on time was 55 minutes. Median time waiting on a complete package from the
relationship manager was 6.8 days. About 58% of files entered a "missing items"
loop at least once.

We had asked LatticeFlow to automate the 55 minutes. The 6.8 days were never in
the SOW.

## Why this writeup exists

Because the next vendor will get the same email we sent last time, and if they
build the same thing, we will waste another half year.

If you are reading this as an outside engineer: measure where the days go before
you touch a model. Talk to the regional managers separately. They do not run the
same process. Read the support export. The swagger is wrong for two regions.
