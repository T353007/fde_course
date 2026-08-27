---
id: M09
slug: the-revenue-function
title: The Revenue Function
subtitle: One method. Three callers. Two of them want a different answer and nobody has ever said so out loud.
phase: 2
order: 9
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Trace every caller of a shared function across service boundaries
  - Estimate blast radius with a written method instead of a gut feeling
  - Recognize when a bug has no single correct fix because the callers disagree
  - Choose a first move that is reversible and does not require anyone to be wrong
concepts: [hidden dependencies, blast radius, shared definitions, feature flags, legacy code]
competencies: [architecture, debugging, customer-communication, fintech-judgment]
prereqs: [M08]
---

## Where you are

Your first slice needs a revenue number. That was the point of scoping it that way in
Mission 07: extract revenue from bank statements, compare it to what the system
produces today, and show Renee a difference she can check in ninety seconds.

So you have to find where the system's revenue number comes from. That takes four
minutes. Everything after that takes three days.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:31 AM"}
```text
Marcus:  ok so for the slice, we're comparing our extracted revenue
         against the system's current number right?

You:     right

Marcus:  where does the current number come from

You:     finding out today

Marcus:  cool. if ours is better can we just swap it in? feels like a
         one line change

Sam:     it's one line

Marcus:  see

Sam:     i didn't say it was a small change
```
:::

## The code

Four minutes of grep and you have it.

```java
package com.northstar.underwriting.revenue;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

import org.springframework.stereotype.Component;

import com.northstar.common.model.BankTransaction;

@Component
public class RevenueCalculator {

    /**
     * Calculates average monthly revenue from bank transactions.
     *
     * TODO(jkowalski, 2019-08): this counts every credit. Underwriting says
     * transfers and loan deposits should not count. Waiting on a decision
     * from credit policy before changing it. Do not change without asking
     * Renee, three other things depend on this number.
     */
    public BigDecimal calculateMonthlyRevenue(List<BankTransaction> transactions,
                                              int months) {
        BigDecimal total = BigDecimal.ZERO;

        for (BankTransaction t : transactions) {
            if (t.amount().signum() > 0) {
                total = total.add(t.amount());
            }
        }

        if (months <= 0) {
            return BigDecimal.ZERO;
        }

        return total.divide(BigDecimal.valueOf(months), 2, RoundingMode.HALF_UP);
    }
}
```

Read the comment before you read the code.

Jan Kowalski knew. In August 2019 he knew the function was wrong, he knew how it was
wrong, he wrote down who to ask, and he warned the next person that three things
depend on it. Then he waited for a decision from credit policy that never came, and in
2021 he left.

That comment is not a landmine somebody hid. It is a note somebody left, in the right
place, in plain language, and everyone who read it did what you are about to do, which
is decide it is not their problem this week.

## The conversation

:::dialogue{title="Sam's desk, Wednesday 11:40 AM"}
**You:** I found `calculateMonthlyRevenue`.

*Sam does not say anything for a second.*

**Sam:** ...Ah. So you found that.

**You:** It counts every credit.

**Sam:** It counts every credit.

**You:** Including transfers. Including loan proceeds.

**Sam:** Including a competitor's loan proceeds, yeah. Renee has been working around
that number since before I got here.

**You:** Why hasn't anyone fixed it?

**Sam:** People have tried. Twice that I know of.

**You:** What happened?

**Sam:** First time, nobody could get credit policy to sign off on a definition.
Second time we got most of the way and the guy left.

**You:** So it's a one line change and nobody's made it in seven years.

**Sam:** It's not one line. Go find the callers first.

**You:** How many are there?

**Sam:** That's the question, isn't it.
:::

## Evidence

Start with grep, then stop trusting grep.

:::evidence{type=log label="grep session, lab/northstar"}
```text
$ grep -rn "calculateMonthlyRevenue" --include=*.java . | grep -v /test/

./underwriting-service/src/main/java/com/northstar/underwriting/revenue/RevenueCalculator.java:36:
    public BigDecimal calculateMonthlyRevenue(List<BankTransaction> transactions,
./underwriting-service/src/main/java/com/northstar/underwriting/decision/UnderwritingDecisionService.java:44:
    BigDecimal monthlyRevenue = revenueCalculator.calculateMonthlyRevenue(txns, months);
./underwriting-service/src/main/java/com/northstar/underwriting/credit/DebtServiceCoverageService.java:51:
    BigDecimal monthlyRevenue = revenueCalculator.calculateMonthlyRevenue(txns, months);
./underwriting-service/src/main/java/com/northstar/underwriting/api/InternalRevenueController.java:29:
    return calculator.calculateMonthlyRevenue(txns, months);
```
:::

Three call sites. Two are ordinary Java calls inside the same service. The third is a
REST controller, which means the real caller is not in this repo.

This is where a lot of engineers stop. Grep found three, and the TODO comment said
three. Do not stop. A controller is a door, and grep cannot see who walks through it.

:::evidence{type=log label="access log, underwriting-service, 24 hours"}
```text
$ make logs S=underwriting-service | grep "/internal/v1/revenue" | \
    awk '{print $NF}' | sort | uniq -c | sort -rn

   1841 caller=application-service/3.1.0
     22 caller=reviewer-portal-bff/0.9.2
      3 caller=curl/8.4.0
```
:::

Two more callers than the code showed. `application-service` calls it 1,841 times a
day. The second is a portal backend nobody has mentioned to you. The third is somebody
at a terminal, which is fine.

Go find the big one.

```java
package com.northstar.application.portal;

import java.math.BigDecimal;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v1/portal")
public class PortalSummaryController {

    private final UnderwritingClient underwriting;

    public PortalSummaryController(UnderwritingClient underwriting) {
        this.underwriting = underwriting;
    }

    /**
     * Powers the "Your cash flow" card in the applicant portal.
     *
     * Product wants this to match what the applicant sees in their own bank
     * app, so it is total deposits, not operating revenue. Do not filter.
     * See PORTAL-1188.
     */
    @GetMapping("/applications/{id}/cash-flow")
    public CashFlowSummary cashFlow(@PathVariable long id,
                                    @RequestHeader("X-Tenant-Id") String tenantId) {

        BigDecimal monthlyDeposits = underwriting.monthlyRevenue(id, 3);

        return new CashFlowSummary(
                id,
                monthlyDeposits,
                "Average monthly deposits, last 3 months");
    }
}
```

Read that comment too. "Do not filter."

Somebody made a deliberate product decision that this number should be total deposits,
wrote it down, and referenced a ticket. An applicant looking at a cash flow card wants
it to match their own bank app, and their bank app counts every deposit. Show them a
smaller number and they call support to ask why yours is wrong.

That number is correct for what it does. And it comes out of a function whose TODO
comment says it is wrong.

## The three callers

Here is what you have now.

| Caller | Where | What it wants | What it gets |
|---|---|---|---|
| `UnderwritingDecisionService` | underwriting-service | Operating revenue | Total deposits. Wrong. |
| `DebtServiceCoverageService` | underwriting-service | Operating revenue | Total deposits. Wrong, and it gets worse. |
| `PortalSummaryController` | application-service, over REST | Total deposits | Total deposits. Correct. |

Two callers want a number the function does not produce. One wants exactly what it
does produce. All three call the same method and none of them know about each other.

Here is the first one.

```java
@Service
public class UnderwritingDecisionService {

    private static final BigDecimal MIN_MONTHLY_REVENUE = new BigDecimal("15000");

    private final RevenueCalculator revenueCalculator;
    private final TransactionRepository transactions;
    private final PolicyEngine policyEngine;

    public UnderwritingDecisionService(RevenueCalculator revenueCalculator,
                                       TransactionRepository transactions,
                                       PolicyEngine policyEngine) {
        this.revenueCalculator = revenueCalculator;
        this.transactions = transactions;
        this.policyEngine = policyEngine;
    }

    public Decision decide(long applicationId, int months) {
        List<BankTransaction> txns = transactions.findForApplication(applicationId, months);

        // credit policy 4.2: minimum operating revenue
        BigDecimal monthlyRevenue = revenueCalculator.calculateMonthlyRevenue(txns, months);

        if (monthlyRevenue.compareTo(MIN_MONTHLY_REVENUE) < 0) {
            return Decision.decline(applicationId, "REV_BELOW_MIN");
        }
        return policyEngine.evaluate(applicationId, monthlyRevenue);
    }
}
```

The comment says operating revenue. The call returns total deposits. That gap is the
whole mission.

And here is the second one, where the error stops being a rounding problem and starts
being money.

```java
@Service
public class DebtServiceCoverageService {

    /** Sector expense ratio, credit policy appendix B. */
    private static final BigDecimal EXPENSE_RATIO = new BigDecimal("0.72");

    private final RevenueCalculator revenueCalculator;
    private final TransactionRepository transactions;

    public DebtServiceCoverageService(RevenueCalculator revenueCalculator,
                                      TransactionRepository transactions) {
        this.revenueCalculator = revenueCalculator;
        this.transactions = transactions;
    }

    /**
     * DSCR = net operating income / annual debt service.
     *
     * Most applicants do not give us a P&L, so we estimate net operating
     * income from revenue using the sector expense ratio.
     */
    public BigDecimal calculateDscr(long applicationId,
                                    BigDecimal annualDebtService,
                                    int months) {

        List<BankTransaction> txns = transactions.findForApplication(applicationId, months);
        BigDecimal monthlyRevenue = revenueCalculator.calculateMonthlyRevenue(txns, months);

        BigDecimal annualRevenue = monthlyRevenue.multiply(BigDecimal.valueOf(12));
        BigDecimal netOperatingIncome =
                annualRevenue.multiply(BigDecimal.ONE.subtract(EXPENSE_RATIO));

        if (annualDebtService.signum() <= 0) {
            return BigDecimal.ZERO;
        }
        return netOperatingIncome.divide(annualDebtService, 2, RoundingMode.HALF_UP);
    }
}
```

## The arithmetic

Take one real application from the seed data. Application 10871, three months of
statements, requesting a term loan with $240,000 of annual debt service.

```text
Total credits over 3 months .................... 340,200
  of which, transfer from savings .............. -30,000
  of which, FASTCAPITAL LOAN ................... -75,000
Operating credits .............................. 235,200
```

Now run it both ways.

| Step | What the system computes | What is true |
|---|---|---|
| Monthly revenue | 340,200 / 3 = **113,400.00** | 235,200 / 3 = **78,400.00** |
| Annual revenue | 1,360,800 | 940,800 |
| Net operating income at 28% | 381,024 | 263,424 |
| Annual debt service | 240,000 | 240,000 |
| DSCR | **1.59** | **1.10** |

Northstar's DSCR floor is 1.25, from the config file you read in Mission 08. So this
applicant fails policy by 0.15, and the system says they clear it by 0.34.

It does not stop there, because DSCR also sets the price.

| DSCR band | Rate offered |
|---|---|
| 1.50 and above | 11.9% |
| 1.25 to 1.49 | 14.4% |
| 1.10 to 1.24 | 17.9% |
| Below 1.10 | Decline |

At 1.59 this applicant gets the best tier. At the true 1.10 they get the worst tier
that is still an approval, and only if a human overrides the floor.

That is what "the error compounds" means. One wrong number produced three wrong
outputs: an eligibility check, a coverage ratio, and a price. Nobody wrote a bug in
DSCR. DSCR is correct arithmetic on a wrong input, which is the kind of failure that
survives code review forever.

How often does this happen? You cannot answer precisely, because
`bank_transactions.category` is null on most rows. You can approximate.

:::evidence{type=sql label="psql, applications with a suspect large credit"}
```sql
SELECT count(DISTINCT a.application_id) AS apps_with_suspect_credit,
       (SELECT count(*) FROM northstar.applications) AS total_apps
FROM northstar.applications a
JOIN northstar.bank_transactions t USING (application_id)
WHERE t.amount > 10000
  AND (t.description ILIKE '%TRANSFER%'
    OR t.description ILIKE '%LOAN%'
    OR t.description ILIKE '%FASTCAPITAL%'
    OR t.description ILIKE '%ONDECK%'
    OR t.description ILIKE '%KABBAGE%');
```
```text
 apps_with_suspect_credit | total_apps
--------------------------+------------
                      271 |       1200
```
:::

Roughly 23 percent, and that is a floor, not an estimate. It only finds the ones whose
description happens to contain a word you thought of.

## What you do not know

- Does anyone outside Northstar's own services call `/internal/v1/revenue`? The name
  says internal. The name is not a firewall rule.
- What is `reviewer-portal-bff` and who owns it? It made 22 calls yesterday.
- Do the underwriters already correct for this by hand, and if so, does the corrected
  number get written anywhere?
- If you fixed the number, how many past decisions would have gone the other way, and
  does anyone have to be told?
- What did the two previous attempts actually produce?

## Your task

:::task{time="120 min"}
Produce two artifacts.

**1. A blast radius table.** One row per caller. Columns:

| Caller | What it wants | What it gets today | What changes if fixed | Who sees the change | Downstream effect | Reversible? | Detectable? |

Fill in all five callers you found, including the two that only appear in access logs.
If you cannot fill a cell, write "unknown" rather than guessing. An honest unknown is
a finding.

**2. A one page recommendation.** It must not propose changing
`calculateMonthlyRevenue()` in this engagement. Your job is to say what the first move
is, why it is reversible, and what has to be true before anyone touches the shared
function.

Save both as `customers/northstar/revenue-function-blast-radius.md`.
:::

:::stopandthink
Do this before you read on. It is the most useful five minutes in Phase 2.

1. Your instinct is to fix the function. Write down, specifically, what breaks.
2. The portal number is correct for the portal and wrong for underwriting. Who decides
   which one is "the" definition of revenue at Northstar? Name the person.
3. If you shipped the fix today and it was wrong, how would you find out, and how long
   would that take?
4. Marcus said "one line change." What is the shortest true sentence that corrects him
   without making him look bad in the channel?

Write all four down.
:::

## Working through it

### Blast radius, as an actual method

Most engineers estimate blast radius by feeling. It is shared so it feels scary, or it
has tests so it feels safe. You cannot hand a feeling to a CTO who said "show me the
blast radius."

Here is a method. Six steps, in order, and you write down the answer to each.

**1. Enumerate every caller.** Not every caller in this repo. Every caller. Grep finds
in-process calls. Access logs find network calls. Consumer group lag finds Kafka
consumers. Vendor invoices find callers you have no logs for.

**2. Write what each caller thinks the value means.** One sentence, in the words of
whoever owns it. Not your interpretation. If you cannot get their words, mark it
unknown and go ask.

**3. Name the number that visibly changes.** A DSCR on a screen. A dollar figure in an
email. A decision code in a database. If you cannot name a specific number, you have
not traced far enough.

**4. Trace one step past that number.** The DSCR does not just get displayed, it sets a
rate. The portal figure sits on a page an applicant can screenshot. This is where most
blast radius estimates fall apart, because people stop at the API boundary.

**5. Rate reversibility.** Can you put it back in under an hour, and does putting it
back undo the damage? A config flag is reversible. An email to 1,840 applicants is not.
Those are different risks and they get treated the same all the time.

**6. Rate detectability.** If you are wrong, what tells you, and how fast? "A support
ticket in four days" is a real answer and a bad one. Poor detectability argues for a
smaller first move, not for more testing.

Run those six on the revenue function and the answer arrives on its own.

### The table

| Caller | Wants | Gets today | If fixed | Who sees it | Downstream | Reversible | Detectable |
|---|---|---|---|---|---|---|---|
| `UnderwritingDecisionService` | Operating revenue | Total deposits | Revenue drops, up to 41% | Underwriters, applicants via decline | Eligibility flips on the boundary cases | Yes, config | Yes, decline rate moves |
| `DebtServiceCoverageService` | Operating revenue | Total deposits | DSCR drops, 1.59 to 1.10 in one case | Underwriters, credit committee | Rate tier changes, some approvals become declines | Yes, config | Partly. Nobody charts DSCR distribution |
| `PortalSummaryController` | Total deposits | Total deposits | Applicant-facing number silently drops | 1,840 applicants a month | Support tickets, trust | No. The screenshot already happened | Only through Carla's queue |
| `reviewer-portal-bff` | unknown | Total deposits | unknown | unknown | unknown | unknown | unknown |
| `curl/8.4.0` | Somebody debugging | n/a | n/a | One engineer | None | n/a | n/a |

Row three is the trap and row four is the reason you do not ship this week.

### The wrong turn

Here is the path most people take, and it is not a stupid one.

Wednesday afternoon you write the correct function, run the suite, and it is green.
You open a small pull request titled "fix revenue calculation to exclude transfers and
loan proceeds," and you post it in the channel.

:::evidence{type=slack label="#northstar-ai, Wednesday 4:52 PM"}
```text
You:     PR up for the revenue calc. excludes transfers + loan proceeds.
         all tests green.

Marcus:  amazing, that was fast 🙌

Janet:   who is on call for that

Sam:     don't merge that

Sam:     the portal reads it

You:     the applicant portal reads the underwriting revenue function?

Sam:     it reads the endpoint. same function.

Sam:     and the portal wants deposits, not revenue. that one's correct.
```
:::

The cost is real even though nothing shipped. An afternoon spent on a change that
cannot land. A public correction from Sam in front of Janet, who is already suspicious
of consultants. And Marcus now believes the revenue fix was fast and easy, which is a
belief you will be arguing with for the rest of the engagement.

The technical mistake was small: you treated grep as complete. The judgment mistake was
larger. You proposed a change to a shared value before you knew what every consumer
wanted from it, in a building where nobody had ever written that down.

### Why fixing it is the wrong first move

You can write the correct function in twenty minutes. You cannot ship it, for three
separate reasons, and only one of them is technical.

The portal number would silently change for roughly 23 percent of applicants. They
would see a smaller cash flow figure than their own bank app shows, with no
explanation, on a screen built to create confidence mid-application. Carla's team eats
that. When Northstar changed a portal figure without notice in 2024, her queue took
about 300 extra tickets in four days.

The `reviewer-portal-bff` caller is unknown. You do not change a value an unknown
consumer reads. That is not caution, it is arithmetic: you cannot estimate a blast
radius with an unknown in it.

And there is no agreed definition to fix it to. Seven years after Kowalski's TODO,
credit policy has still not produced one. Both previous attempts failed on that, not on
engineering difficulty. "Revenue" means two things at Northstar and both are
legitimate.

## Tests

Here is why nobody caught this.

```java
class RevenueCalculatorTest {

    private final RevenueCalculator calc = new RevenueCalculator();

    @Test
    void sumsCreditsAndDividesByMonths() {
        List<BankTransaction> txns = List.of(
                credit("STRIPE PAYOUT", "48230.00"),
                credit("STRIPE PAYOUT", "51340.00"),
                debit("RENT", "-4200.00"));

        assertThat(calc.calculateMonthlyRevenue(txns, 2))
                .isEqualByComparingTo("49785.00");
    }

    @Test
    void returnsZeroWhenMonthsIsZero() {
        assertThat(calc.calculateMonthlyRevenue(List.of(), 0))
                .isEqualByComparingTo(BigDecimal.ZERO);
    }
}
```

Two tests. Both pass. Both are correct.

Neither one has an opinion about what revenue means. They test the arithmetic, which
was never in doubt. There is no test anywhere that says a transfer should be excluded,
because writing that test would have required a decision from credit policy, which is
the exact thing nobody could get.

And there is no test at all on `/v1/portal/applications/{id}/cash-flow`. So when you
"fixed" the calculator on Wednesday, the whole suite went green while the applicant
facing number changed for 23 percent of people.

Green tests told you the change was safe. They were measuring the part that was easy
to measure.

## Then this happens

Thursday morning, before you write the recommendation, you go looking for the two
previous attempts. Sam said one of them got most of the way.

:::evidence{type=schema label="underwriting-service application.yml, lines 61 to 68"}
```yaml
features:
  USE_NEW_REVENUE_CALC_V2_TEMP: ${NEW_REVENUE_CALC:true}
  ENABLE_SHADOW_REVENUE_LOG: ${SHADOW_REVENUE_LOG:true}
  # both added 2021-06 for the revenue rework. remove when v2 ships.
```
:::

A flag named `USE_NEW_REVENUE_CALC_V2_TEMP`, added in 2021, still set to true.

:::evidence{type=log label="grep for the flag"}
```text
$ grep -rn "USE_NEW_REVENUE_CALC_V2_TEMP" --include=*.java --include=*.yml .

./underwriting-service/src/main/resources/application.yml:62:  USE_NEW_REVENUE_CALC_V2_TEMP: ...
./underwriting-service/src/main/java/com/northstar/underwriting/revenue/RevenueShadowListener.java:31:
    @ConditionalOnProperty("features.USE_NEW_REVENUE_CALC_V2_TEMP")
```
:::

One reference. Not in the decision path. In a listener.

```java
package com.northstar.underwriting.revenue;

@Component
@ConditionalOnProperty("features.USE_NEW_REVENUE_CALC_V2_TEMP")
public class RevenueShadowListener {

    private static final Logger log = LoggerFactory.getLogger(RevenueShadowListener.class);

    private final RevenueCalculator v1;
    private final RevenueCalculatorV2 v2;

    // ... constructor omitted

    @EventListener
    public void onRevenueComputed(RevenueComputedEvent e) {
        BigDecimal a = v1.calculateMonthlyRevenue(e.transactions(), e.months());
        BigDecimal b = v2.calculateOperatingRevenue(e.transactions(), e.months());

        BigDecimal delta = b.subtract(a);
        BigDecimal pct = a.signum() == 0
                ? BigDecimal.ZERO
                : delta.multiply(BigDecimal.valueOf(100))
                       .divide(a, 2, RoundingMode.HALF_UP);

        log.debug("app={} v1={} v2={} delta={} pct={}", e.applicationId(), a, b, delta, pct);
    }
}
```

Somebody in 2021 built the new calculation, wired it beside the old one, computed the
difference on every application, logged it, and never switched anything over.

Northstar has been generating a live measurement of this exact change for five years.
Nobody has ever read it.

:::evidence{type=log label="30 days of shadow logs, summarized"}
```text
$ make logs S=underwriting-service | grep RevenueShadowListener | \
    sed 's/.*pct=//' | sort -n > /tmp/pct.txt
$ wc -l /tmp/pct.txt
    1804 /tmp/pct.txt

percentile of pct change (v2 vs v1)
  p50 ......    0.00
  p75 ......   -2.10
  p90 ......   -9.40
  p95 ......  -14.80
  p99 ......  -31.60
  max ......  -41.20
```
:::

That is the blast radius, measured, on real production traffic, and it was sitting in a
log file the whole time.

More than half of applications do not change at all. The damage is concentrated in a
tail. That is the same shape you are going to see again in Mission 16 when the eval
report reads 96 percent overall and 68 percent on loan proceeds, and it is the shape
that makes overall averages useless in this business.

### Why the 2021 attempt stopped

```java
@Component
public class RevenueCalculatorV2 {

    private static final Set<String> TRANSFER_PREFIXES = Set.of(
            "TRANSFER FROM", "TRANSFER TO", "INTERNAL XFER", "XFER FROM SA");

    // TODO(mchen, 2021-06-14): loan proceeds. Renee says look for the lender
    // name in the description. We don't have a lender list and legal won't
    // give us one. Parked until we do. This is why v2 is not on yet.

    public BigDecimal calculateOperatingRevenue(List<BankTransaction> txns, int months) {
        BigDecimal total = BigDecimal.ZERO;

        for (BankTransaction t : txns) {
            if (t.amount().signum() <= 0) {
                continue;
            }
            String desc = t.description() == null ? "" : t.description().toUpperCase();
            boolean isTransfer = TRANSFER_PREFIXES.stream().anyMatch(desc::startsWith);
            if (!isTransfer) {
                total = total.add(t.amount());
            }
        }

        if (months <= 0) {
            return BigDecimal.ZERO;
        }
        return total.divide(BigDecimal.valueOf(months), 2, RoundingMode.HALF_UP);
    }
}
```

There it is. V2 excludes transfers and does nothing about loan proceeds, because a
prefix list cannot recognize a lender it has never heard of.

On application 10871, V2 removes the 30,000 transfer and keeps the 75,000 Fastcapital
loan. It produces 103,400 against a truth of 78,400. Better than 113,400, still wrong,
and wrong in the direction that approves loans that should be declined. M. Chen was
right to stop. A half fix on a credit decision is worse than nothing, because it makes
the number look reviewed.

That TODO also tells you something about your own project. "Look for the lender name in
the description" with no list of lenders is a matching problem with an open vocabulary.
Bad fit for a prefix table, good fit for a model. That is the reason Northstar has an
AI project at all, and nobody there has connected those two facts yet.

## The better version

The recommendation is not "fix it." It is not "do not fix it" either.

**Add a new function beside the old one and name it honestly.**

```java
/**
 * Average monthly operating revenue: deposits from customers, excluding
 * internal transfers, loan proceeds, and owner contributions.
 *
 * This is the number credit policy 4.2 means when it says "revenue".
 * It is NOT the number the applicant portal wants. The portal wants
 * total deposits, which is calculateMonthlyRevenue().
 */
public BigDecimal calculateOperatingRevenue(List<BankTransaction> transactions,
                                            int months) { ... }
```

Four things happen when you do it this way and none of them require anyone to be
wrong.

Nothing breaks today, because no existing caller changes. The portal keeps its number,
underwriting keeps its number, and you have removed no behavior.

The definition becomes visible. Northstar has one name for two concepts, which is why
nobody could ever have the argument. Two names make the disagreement speakable, and
once it is speakable Renee and Doug can settle it. That conversation is Mission 11.

The migration becomes per caller. Move `UnderwritingDecisionService` first, behind a
flag, with the shadow log already in place to measure the effect. Then DSCR. Then find
out what `reviewer-portal-bff` is. The portal may never move, and that is fine.

And the old name eventually becomes honest. Once nothing that wants operating revenue
calls it, `calculateMonthlyRevenue` becomes `calculateTotalDeposits` and the seven year
old TODO comes out. That is the last step, not the first.

Put one more line in the recommendation: give the shadow log an owner. It has produced
exactly the measurement needed to approve this change for five years, and it goes to
`log.debug` and nowhere else. That is not a bug in the code. It is a bug in whose job
it was to look.

:::judgment
**When a shared value has three consumers and two of them disagree about what it
means, you do not have a bug. You have an undocumented product decision, and code
cannot resolve it.**

The tell is a function name that describes a quantity rather than a computation.
`calculateMonthlyRevenue` names a business concept. `sumPositiveTransactionsDividedByMonths`
names an operation. The first kind of name invites every caller to bring its own
definition, every caller does, and none of them ever meet.

Once you see it, the reflex to suppress is the fix reflex. The change is small, you can
see it clearly, and being the person who fixed the seven year old bug feels good. It is
also how consultants get thrown out of buildings. Nobody is going to thank you for
changing this number on a Wednesday, and if a customer facing figure moves without
warning, Carla's team pays for it and you will not be there.

The move that works is additive and reversible. Add the correctly named function. Leave
the old one running. Make the disagreement visible so the people with authority to
settle it can see it. Migrate one caller at a time with measurement in place. This is
slower and it is the only version that survives you leaving, which is the actual
requirement.

And read the flags. `USE_NEW_REVENUE_CALC_V2_TEMP` looks like technical debt. It is a
research report. Someone smart already attempted your exact change, got most of the
way, and stopped for a reason. Finding out why they stopped is worth more than a week
of your own analysis, because it tells you what is genuinely hard here. In this case
the answer was an open vocabulary of lender names, which is the shape of the AI problem
you were hired to solve. The person who gave up in 2021 wrote your Phase 4 scope.
:::

:::commslab
One finding, four audiences. Notice that the technical content shrinks each time and
the decision gets sharper.

#### To Sam

> Traced it. Five callers, not three. The portal one wants deposits and it's right to
> want that. I'm not touching the shared function. Plan is a new
> `calculateOperatingRevenue` beside it and move underwriting over behind a flag. Does
> that break anything you know about?

Peer to peer. State the plan, invite the correction, do not perform gratitude for the
save he gave you in public.

#### To Priya, the CTO

> You asked for blast radius. Five callers. Two want operating revenue and get total
> deposits. One is an applicant facing number that is correct as-is and would silently
> change. One I can't identify yet. My recommendation is to add a second function and
> migrate one caller at a time, and to not touch the existing one during this
> engagement.

She said "show me the blast radius." Give her the count, the conflict, the unknown, and
the recommendation, in that order. The unknown caller is the part she will react to.

#### To Renee, the underwriter

> I found the code that produces the revenue number in the system. It counts every
> deposit, including transfers between your applicant's own accounts and money from
> other lenders. Is that why you don't use it?

She has known this for years and has been working around it alone. Do not present it as
a discovery. Present it as a confirmation of something she already knew, and then be
quiet.

#### To Marcus, VP Product

> It is one line in the underwriting service. That line is also read by the applicant
> portal, where the current number is the right one. So the work isn't the fix, it's
> splitting one number into two. About a week, and nothing changes for applicants.

He said "one line change" in public. Agree with him, then add the fact that changes the
conclusion. He gets to be right about the line and still reach the correct answer.
:::

## Practice

Different industry, same trap.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A payroll company, 220 employees, running payroll for about 9,000 small businesses. You
are two weeks in.

You find this in the core service:

```java
/**
 * Gross pay for the period.
 * TODO(2020): does this include the employer 401k match? Ask Denise.
 */
public Money computeGrossPay(Employee e, PayPeriod p) { ... }
```

Callers you can find:

- `TaxWithholdingService`, in the same service. Wants taxable wages.
- `PaystubRenderer`, in the same service. Wants the number the employee sees at the top
  of their paystub.
- `GET /internal/v1/gross-pay`, called 14,000 times a day by something.
- A nightly export to a 401k provider, written in Ruby, in a different repo.

Denise retired in 2022.

**Your task**

1. Name the number that changes for each caller if the definition is corrected, and
   who physically sees it.
2. Rank the four callers by reversibility. Be specific about what "put it back" means
   for each.
3. One of these callers has a consequence the other three do not. Which one, and why
   does it change your entire plan?
4. Write the first move, in three sentences, with no code in it.

---

**Notes, after you have written yours**

The caller that changes everything is the nightly 401k export. The other three produce
a number on a screen. That one produces a contribution amount sent to a regulated
retirement plan provider, and once a contribution is filed, unwinding it is not a code
change. It is a correction filing with a compliance deadline attached. Reversibility
for the first three is measured in minutes. For that one it is measured in lawyers.

The rule this teaches: rank callers by whether the output leaves your building. A
number on an internal screen, a number on a customer's screen, and a number filed with
a third party are three different risk levels, and a blast radius table that does not
separate them is not doing its job.

The second thing to catch is `TaxWithholdingService` versus `PaystubRenderer`. Taxable
wages and displayed gross pay are genuinely different numbers under US payroll rules,
and both are correct for their own purpose. Same shape as the Northstar portal. Two
legitimate definitions, one function name, and the disagreement has never been said out
loud because the name hid it.

Your first move is the same as Mission 09. Add a second, honestly named function, leave
the existing one alone, and migrate the internal callers first while the external ones
stay put. Then find out what makes 14,000 calls a day to that endpoint, because you
cannot finish the estimate until you know.

And go look for whatever Denise left behind. A retired payroll specialist who was the
named authority on a definition in 2020 almost certainly had a spreadsheet.
:::
