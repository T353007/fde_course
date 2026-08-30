# Observed versus documented

Mission 02. Curl date: 2026-08-29. Stack: `make bootstrap`, `application-service` on
8081, `underwriting-service` on 8083. Docs source: Confluence "Application API v1" and
"Underwriting API v1" (last edited 2022-08-19), per Priya's onboarding link.

| Endpoint | What the docs claim | What the endpoint returned | What a client written from the docs would do |
| --- | --- | --- | --- |
| `GET /api/v1/applications/8` (8081, `X-Tenant-Id: NSC_DIRECT`) | JSON with `applicationId`, `applicantId`, `product`, `amountRequested`, `status`, `submittedAt`, `customerId`. | Same core fields. Also `decidedAt`, `createdAt`, `updatedAt`. `customerId` is `"NSC-DIRECT"` (hyphen) while the request header used `NSC_DIRECT` (underscore). Example: `product` `EQUIPMENT`, `status` `FUNDED`, `amountRequested` `620000.00`. | **Mostly works.** A strict client that validates only documented fields would still parse the response. A client that rejects unknown fields might fail on the three extra timestamps. A client that assumes `customerId` must match the tenant header format would be confused but not broken. |
| `GET /api/v1/applications/8/revenue-summary` (8083) | `applicationId`, `monthlyRevenue`, `monthsAnalyzed`. **404** when no bank data is linked. | HTTP 200. `applicationId` 8, `avgMonthlyRevenue` `1068698.91`, `revenue` null, `monthsAnalyzed` 3, `calculatedAt` (request time), `calcVersion` `"v2"`. No field named `monthlyRevenue`. | **Breaks on the happy path.** `response.monthlyRevenue` is `undefined` in JavaScript; a portal widget would show a blank revenue number. Code that treats 404 as "no bank data" would never run for app 8 even when that pattern matters elsewhere. |
| `GET /api/v1/applications/8/bank-transactions` (8083) | `applicationId` and `transactions[]` with `postedDate`, `description`, `amount`. **404** when no statements linked. | HTTP 200. `applicationId` 8, `transactions` array with **82** rows (mix of credits and debits). Shape matches the doc. Sum of positive amounts is `3206096.73`, which divides by 3 to match `avgMonthlyRevenue` on the revenue-summary call. | **Works for parsing.** A client that only reads `transactions[].amount` and sums credits would get data. A client that expects 404 when data is missing would be wrong for app 1130 (see next row). |
| `GET /api/v1/applications/1130/revenue-summary` (8083, `X-Tenant-Id: CASCADE`) | Same as revenue-summary above: fields listed, **404** when no bank data. | HTTP 200. `applicationId` 1130, `avgMonthlyRevenue` `0.00`, `revenue` null, `monthsAnalyzed` **3** (not 0), `calcVersion` `"v2"`. Companion call to `.../bank-transactions` returns `"transactions": []` (length 0), also HTTP 200. | **Silent failure mode.** A client written from the docs would expect 404 and might show "link bank account." Instead it gets a numeric zero and `monthsAnalyzed: 3`, which looks like three months of real history with no revenue. Charts and policy rules that compare `avgMonthlyRevenue` to a floor cannot distinguish "no data" from "no revenue." |

## Questions, not conclusions

- Is `avgMonthlyRevenue` the number Renee's team actually uses in manual review, or is there another definition of revenue I have not found yet? **(Renee Blackwell)**

- When the Confluence page says 404 for missing bank data, was that ever true, or was it aspirational? Who decided that 200 with `0.00` was acceptable? **(Sam Ortiz)**

- What is the `revenue` field for on the revenue-summary response, and why is it null on every application id I sampled (8, 17, 20, 33, 37, 1130)? **(Sam Ortiz)**

- Does `calcVersion: "v2"` mean `RevenueCalculatorV2` is live, given `USE_NEW_REVENUE_CALC_V2_TEMP` is false in `application.yml`? **(Sam Ortiz or Tomás Ferreira)**

- Should `customerId` (`NSC-DIRECT`) and `X-Tenant-Id` (`NSC_DIRECT`) be normalized, and which one is authoritative for tenancy? **(Sam Ortiz)**

- Who maintains the Confluence API pages, and is anyone still reading them before onboarding new engineers? **(Priya Raghunathan)**
