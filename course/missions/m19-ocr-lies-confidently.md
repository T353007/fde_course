---
id: M19
slug: ocr-lies-confidently
title: OCR Lies Confidently
subtitle: "OptiScan returns clean JSON, a 0.96 confidence score, and the wrong amount. The score never blinked."
phase: 4
order: 19
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - Prove that vendor OCR confidence does not predict accuracy on real Northstar documents
  - Build reconciliation checks that catch confident wrong extractions before they reach underwriting
  - Choose a fallback path that routes bad pages to a human instead of more prompting
  - Resist the urge to fix a broken OCR vendor with prompt tuning
concepts: [OCR, confidence calibration, reconciliation, vendor failure modes, fallback]
competencies: [debugging, evals, coding, ai-fundamentals]
prereqs: [M18]
---

## Where you are

Mission 18 left you with a note you were supposed to hold onto. Same statement, three
copies, three extractions. Two said 252,400. One said 314,580. The wrong one had the
highest confidence.

Today you are going to treat that note like evidence, not like a curiosity.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:12 AM"}
```text
Marcus:  can we just raise the confidence threshold and drop the bad ones?

You:     raise it to what

Marcus:  like 0.95? the bad one was 0.96 wait

Sam:     ...

Sam:     Ah. So you found that.
```
:::

Marcus is not wrong to want a threshold. He is wrong about what the number means.

## The conversation

:::dialogue{title="Document-service war room, Wednesday 9:40 AM"}
**You:** Walk me through what OptiScan claims confidence is.

**Sam:** Character level. How sure the engine is about the glyphs it read.

**You:** Not whether the amount is right.

**Sam:** Not whether the amount is right. Not whether the line is a deposit. Not
whether the page is even a bank statement.

**You:** So a fax of a fax can come back at 0.94.

**Sam:** Frequently.
:::

:::dialogue{title="Renee Blackwell, same morning"}
**Renee:** I stopped trusting the confidence column in 2021.

**You:** What do you use instead?

**Renee:** My eyes. And the spreadsheet. If the statement ending balance does not
match the running total of the lines, I throw the extraction out and key it.

**You:** Does the system ever check that?

**Renee:** We don't use that number. The system does. That is the problem.
:::

## What you know about the system

`document-service` calls OptiScan through `OptiScanClient`. The vendor reads the MinIO
object and returns a job payload. Confidence is one float for the whole page. Lines
arrive as strings. Amounts keep whatever formatting the source had.

OCR is Optical Character Recognition. It turns pixels into text. OptiScan is Northstar's
OCR vendor. It fails quietly on faxed and scanned statements. It does not return an
error. It returns confident garbage.

The extraction row in `document_extractions` stores that confidence next to the payload.
Nothing downstream asks whether the number on the page matches the number in the JSON.

## The code

```java
package com.northstar.document.ocr;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record OptiScanResponse(
        String jobId,
        String status,
        Double confidence,
        List<Line> lines) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Line(String date, String description, String amount, String type) {
    }
}
```

And the orchestrator that trusts it:

```java
    public void process(DocumentEntity document) {
        OptiScanResponse vendorResponse = optiScanClient.extract(
                document.getStorageKey(), document.getDocType());

        DocumentExtractionEntity extraction = new DocumentExtractionEntity();
        extraction.setDocumentId(document.getDocumentId());
        extraction.setExtractor("OPTISCAN_V2");
        extraction.setCreatedAt(Instant.now());

        if (vendorResponse == null) {
            extraction.setStatus("FAILED");
            extraction.setConfidence(null);
            extractionRepository.save(extraction);
            return;
        }

        extraction.setStatus("COMPLETED");
        extraction.setConfidence(vendorResponse.confidence());
        extraction.setRawPayload(String.valueOf(vendorResponse.lines()));
        extractionRepository.save(extraction);
        // ... publishes document.extracted with the transactions
    }
```

Look at what is missing. No checksum against the statement total. No check that credit
lines sum to the ending balance. No flag when a line amount failed to parse and got
dropped. There is a warn log when lines drop. Nobody alerts on it.

## Evidence

Start with the faxed May statement from the fixture set. Inject the overconfident
scenario so the stub vendor behaves like OptiScan on a bad page.

```bash
make inject SCENARIO=optiscan-overconfident
curl -s -X POST http://localhost:8090/__admin/scenarios/optiscan-overconfident/start
```

:::evidence{type=http label="POST /optiscan/v2/extract, storage key for app 84412 fax copy"}
```json
{
  "jobId": "os-9c21aa",
  "status": "COMPLETED",
  "confidence": 0.96,
  "lines": [
    {"date": "05/04/2026", "description": "STRIPE PAYOUT", "amount": "48,230.00", "type": "CREDIT"},
    {"date": "05/06/2026", "description": "TRANSFER FROM SAVINGS", "amount": "30,000.00", "type": "CREDIT"},
    {"date": "05/11/2026", "description": "STRIPE PAYOUT", "amount": "51,340.00", "type": "CREDIT"},
    {"date": "05/18/2026", "description": "FASTCAPITAL LOAN", "amount": "137,180.00", "type": "CREDIT"},
    {"date": "05/22/2026", "description": "STRIPE PAYOUT", "amount": "47,830.00", "type": "CREDIT"}
  ]
}
```
:::

The real loan line is 75,000. OptiScan read a 7 as a 1 and a 5 as a 3 and produced
137,180. Confidence: 0.96. Status: COMPLETED. No warning field.

:::evidence{type=sql label="Golden labels vs OptiScan on the poor OCR slice"}
```sql
SELECT
  g.case_id,
  g.expected_amount,
  e.extracted_amount,
  e.confidence,
  ABS(g.expected_amount - e.extracted_amount) AS abs_err
FROM northstar.eval_ocr_labels g
JOIN northstar.document_extractions e ON e.document_id = g.document_id
WHERE g.ocr_quality = 'poor'
ORDER BY e.confidence DESC
LIMIT 8;
```
```text
 case_id  | expected | extracted | confidence | abs_err
----------+----------+-----------+------------+---------
 OCR-4412 |  75000.00| 137180.00 |       0.96 | 62180.00
 OCR-4418 |  30000.00|  80000.00 |       0.95 | 50000.00
 OCR-4401 |  48230.00|  48230.00 |       0.94 |     0.00
 OCR-4420 |  12000.00|  17000.00 |       0.93 |  5000.00
 OCR-4399 |  51340.00|  51340.00 |       0.91 |     0.00
 OCR-4415 |   4500.00|   4500.00 |       0.88 |     0.00
 OCR-4407 |  22000.00|  28000.00 |       0.87 |  6000.00
 OCR-4411 |   9800.00|   9800.00 |       0.72 |     0.00
```
:::

Plot confidence against absolute error on the full poor-OCR slice. The line is flat.
High confidence and low confidence both hit right and wrong. Correlation sits near
zero. That is the finding. Write it down before anyone asks you to "just raise the
threshold."

:::evidence{type=metrics label="Confidence vs accuracy, n=400 poor OCR pages"}
```text
bucket          n    exact_match_rate   mean_abs_err
0.95 - 1.00   118              0.41         18420
0.90 - 0.95   141              0.44         16110
0.80 - 0.90    97              0.48         14200
below 0.80     44              0.52         11950

Pearson r (confidence, exact_match): -0.07
```
:::

The highest confidence bucket is the worst exact match rate. Not by a lot. By enough
that a threshold of 0.95 would keep the bad ones and drop some of the good ones.

:::evidence{type=log label="document-service, dropped lines, no alert"}
```text
11:04:18.221 WARN  c.n.doc.ocr.OcrOrchestrator - dropped 3 unparseable lines
             for application 85102
11:04:18.224 INFO  c.n.doc.ocr.OcrOrchestrator - extraction complete
             documentId=779901 confidence=0.93 status=COMPLETED
```
:::

Three lines vanished. The extraction still completed. Confidence still looks fine.
Underwriting never hears about the drop.

## What you do not know

- Whether OptiScan has a field level confidence you are not reading.
- Whether the bank portal PDF path has the same problem, or only fax and phone photos.
- What Renee's reconciliation rule should look like in code, in exact words.
- Whether underwriting will accept a "needs human OCR review" status without Hank
  killing the queue SLA.

## Your task

:::task{time="120 min"}
1. Reproduce the overconfident OptiScan response on the faxed May statement. Confirm
   the Fastcapital line reads 137,180 at confidence 0.96.
2. Run the poor OCR slice through the lab eval suite. Report exact match rate by
   confidence bucket. Show that the relationship is flat.
3. Implement a reconciliation check in `document-service` that compares extracted line
   totals to statement header totals when the header is present, and flags the
   extraction when they disagree by more than one cent.
4. Route flagged extractions to a human review status. Do not send them to
   underwriting as completed.
5. Write down the prompt tuning idea you almost tried, then write why it cannot fix
   this.
:::

## Stop and think

:::stopandthink
1. If confidence does not predict accuracy, what signal would you trust instead?
2. Is this an AI problem or a vendor integration problem?
3. What happens to Hank's queue if every poor OCR page goes to human review?

Write your answers before you scroll. Two minutes.
:::

## Working through it

The wrong turn shows up first, because it is the one a reasonable engineer takes.

### The wrong turn: prompt the model harder

Marcus suggests feeding the OptiScan text into the extraction model with a sterner
prompt. "Be careful with amounts. Double check every digit."

You try it. The stub scenario `overconfident-ocr` still returns high confidence wrong
values, because the model is reading wrong source text. A careful reader of garbage
still produces garbage. You burn an afternoon and the exact match rate on the poor OCR
slice moves from 61 percent to 63 percent. Inside the noise.

Nadia Slack-messages you.

:::evidence{type=slack label="Nadia Ferrante, 2:11 PM"}
```text
Nadia:  what would have to be true for prompt tuning to fix this?

You:    the digits would have to be right in the OCR text already

Nadia:  and are they?

You:    no

Nadia:  then you are polishing the wrong step
```
:::

Pull the prompt change. Leave a comment in the PR that says why. Future you will thank
you when Marcus asks again in Phase 7.

### Reconciliation instead

Renee's rule is the right shape. If the statement prints an ending balance or a period
total, the sum of parsed lines has to match. If it does not, the extraction is not
done. It is suspect.

```java
package com.northstar.document.ocr;

import java.math.BigDecimal;
import java.util.List;

import com.northstar.common.model.BankTransaction;

public final class ExtractionReconciler {

    private ExtractionReconciler() {}

    public record Result(boolean ok, BigDecimal lineSum, BigDecimal headerTotal,
                         String reason) {}

    public static Result check(List<BankTransaction> lines, BigDecimal headerTotal) {
        BigDecimal sum = BigDecimal.ZERO;
        for (BankTransaction t : lines) {
            if (t.amount().signum() > 0) {
                sum = sum.add(t.amount());
            }
        }

        if (headerTotal == null) {
            return new Result(true, sum, null, "no header total to compare");
        }

        if (sum.subtract(headerTotal).abs().compareTo(new BigDecimal("0.01")) > 0) {
            return new Result(false, sum, headerTotal,
                    "line sum " + sum + " disagrees with header total " + headerTotal);
        }
        return new Result(true, sum, headerTotal, "matched");
    }
}
```

Wire it into the orchestrator after `toTransactions`. On failure, set status to
`NEEDS_REVIEW`, keep the payload for the human, and do not publish
`document.extracted` as a completed extraction.

```java
        List<BankTransaction> transactions = toTransactions(
                document.getApplicationId(), vendorResponse);
        BigDecimal headerTotal = HeaderTotalParser.fromPayload(vendorResponse);
        ExtractionReconciler.Result check =
                ExtractionReconciler.check(transactions, headerTotal);

        if (!check.ok()) {
            extraction.setStatus("NEEDS_REVIEW");
            extraction.setConfidence(vendorResponse.confidence());
            extraction.setRawPayload(String.valueOf(vendorResponse.lines()));
            extractionRepository.save(extraction);
            log.warn("reconciliation failed documentId={} reason={}",
                    document.getDocumentId(), check.reason());
            return;
        }
```

Header totals are not always present. Phone photos often crop them. That is fine. The
check is a net, not a guarantee. When the header is missing, fall back to a second
signal: if more than two lines were dropped as unparseable, also mark `NEEDS_REVIEW`.
Silent line drops are how 314,580 happened.

### What you tell Hank

:::dialogue{title="Hank Delgado, Underwriting Manager, 4:05 PM"}
**Hank:** What does that do to my queue?

**You:** About 16 percent of bank statements in the last month would hit review
instead of flowing straight through.

**Hank:** Sixteen percent.

**You:** Those are the ones Renee was already rekeying by hand. The difference is the
system will stop pretending they are done.

**Hank:** And the other 84?

**You:** Keep flowing. Confidence score stays in the row for audit. We just stop
using it as a gate.
:::

He does not love it. He does not block it. That is as good as this conversation gets.

## Tests

```java
@Test
void flagsWhenLineSumDisagreesWithHeader() {
    var lines = List.of(
            txn("FASTCAPITAL LOAN", "137180.00"),
            txn("STRIPE PAYOUT", "48230.00"));
    var result = ExtractionReconciler.check(lines, new BigDecimal("123230.00"));
    assertFalse(result.ok());
    assertEquals(new BigDecimal("185410.00"), result.lineSum());
}

@Test
void passesWhenSumsMatchWithinOneCent() {
    var lines = List.of(txn("STRIPE PAYOUT", "48230.00"));
    var result = ExtractionReconciler.check(lines, new BigDecimal("48230.00"));
    assertTrue(result.ok());
}

@Test
void skipsCheckWhenHeaderMissing() {
    var lines = List.of(txn("STRIPE PAYOUT", "48230.00"));
    var result = ExtractionReconciler.check(lines, null);
    assertTrue(result.ok());
    assertEquals("no header total to compare", result.reason());
}
```

Run them with the document-service module tests. Then run the poor OCR eval slice and
confirm that flagged pages no longer enter the completed set that underwriting reads.

```bash
make test
make eval SUITE=ocr-reconciliation
```

## Then this happens

Thursday morning, Carla escalates a ticket. An applicant uploaded a clean bank portal
PDF. Reconciliation failed. Header total says 147,400. Line sum says 147,400.01.
One cent.

:::evidence{type=ticket label="NSC-89102"}
```text
Applicant: "Why is my statement stuck in review? I uploaded the PDF from Chase."
Resolution: open, assigned to you
Note from Carla: "this one is a clean PDF. not a fax. please look."
```
:::

## Tracking it down

OptiScan returned one Stripe line as `47,830.01` on a statement that printed
`47,830.00`. Rounding from the vendor's internal float. Your one cent tolerance is
correct for real disagreement and wrong for vendor noise.

Widen the tolerance to five cents for header comparison, and log the delta either way.
Five cents will not move an approval. Sixty two thousand dollars will. You are drawing
a line between noise and a funding decision.

Also add the dropped-line rule. The clean PDF had zero dropped lines. The fax that
started this mission had three. Different failure, different signal.

## The better version

Confidence becomes an audit field. It is not a gate. Gates are reconciliation, dropped
line count, and a human review status that Hank can see in the queue.

The extraction model in `ai-service` still helps on clean text. It does not get to
override a failed reconciliation. If the pixels are wrong, no amount of careful reading
fixes the digits.

Document the finding in the engagement notes:

```text
OptiScan confidence is uncorrelated with amount accuracy on poor OCR pages
(r ≈ -0.07, n=400). Do not threshold on it. Reconcile to statement totals and
route failures to NEEDS_REVIEW.
```

That sentence will get quoted in the Phase 8 security review. Write it so Yuki does
not have to translate.

:::judgment
**A confidence score from a vendor is a claim about the vendor's internal process, not
a claim about your business fact.**

The instinct to threshold on confidence is reasonable. It works for models that are
calibrated. OptiScan is not calibrated for "is this the amount on the page." It is
calibrated for "did our glyph model like these pixels." Those are different questions,
and treating them as the same question is how 137,180 enters underwriting with a smile.

When a number decides whether a business gets funded, trust checks that can fail hard.
Reconciliation against a printed total is one. Counting dropped lines is another.
Prompting a second model to "be careful" is not a check. It is hope with a temperature
parameter.

Next time a vendor shows you a green dashboard and a high confidence column, ask what
the score is a score of. If the answer is not the business fact you care about, build
your own check.
:::

:::commslab
#### To Sam

> OptiScan confidence is flat against amount accuracy on the poor OCR slice. I am
> adding ExtractionReconciler and a NEEDS_REVIEW status. No more completed extractions
> when line sum disagrees with the header by more than five cents, or when more than
> two lines drop. Anything I am about to break in the worker?

#### To Hank

> About 16 percent of statements will land in a review bucket instead of flowing
> straight through. Those are the ones your team was already rekeying. The queue label
> will say NEEDS_REVIEW so nobody mistakes them for done.

#### To Marcus

> Raising the confidence threshold would have kept the worst errors and cut some good
> pages. We fixed it with a balance check instead. Same goal, different gate.

#### To Renee

> Your ending balance check is now in code. If a statement still looks wrong after it
> clears reconciliation, send me the application id. I want the cases the check missed.
:::

## Practice

Different domain, same skill. Write before you open the notes.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital network uses a third party service to read handwritten medication orders
from scanned charts. The vendor returns a drug name, a dose, and a confidence score.
Pharmacy dispenses when confidence is above 0.90.

What you learn in a week:

- On a labeled set of 1,000 orders, exact dose match is 81 percent overall.
- Above 0.95 confidence, exact dose match is 79 percent.
- Below 0.80 confidence, exact dose match is 84 percent.
- The vendor's confidence measures character clarity, not whether the dose is a
  plausible dose for that drug.
- Pharmacists already catch many errors by checking the dose against a formulary
  range. That check is not in the software path.
- A wrong dose that ships is a patient safety event. A delayed order that waits for a
  pharmacist is a throughput event.

**Your task**

1. Should pharmacy keep the 0.90 confidence gate? Why or why not?
2. Name two reconciliation style checks that would catch errors confidence misses.
3. What is the wrong turn that looks productive for a week?
4. How do you explain the change to a chief nursing officer who asked for "higher
   AI confidence"?

---

**Notes, after you have written yours**

Drop the confidence gate as a hard stop. Keep the score in the audit log. The data says
it does not sort safe from unsafe.

Two checks that work: dose within formulary min and max for that drug and route, and
a second pass that rejects orders where the drug name and dose were both changed from
a prior active order without a matching discontinue. The first is a range check. The
second is a continuity check. Neither needs the vendor's score.

The wrong turn is prompt tuning a second model to "verify the dose." If the OCR text
says 10 mg and the chart said 1.0 mg, the verifier reads 10. You are stacking readers
on broken pixels.

To the CNO: confidence went up and safety did not. We are putting the formulary range
check in the path that dispenses, and routing out-of-range orders to a pharmacist
before anything ships. Throughput takes a hit on the messy charts. Patient safety does
not take a hit on the clean looking wrong ones.
:::

The lesson in one sentence: when a vendor is confidently wrong, stop reading its
confidence and start checking the fact against something the page itself asserts.
