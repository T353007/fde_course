package com.northstar.application.portal;

import java.math.BigDecimal;

/** Body for the applicant-facing cash flow card. */
public record CashFlowSummary(long applicationId, BigDecimal monthlyDeposits, String label) {
}
