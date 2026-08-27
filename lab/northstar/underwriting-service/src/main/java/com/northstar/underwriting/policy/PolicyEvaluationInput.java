package com.northstar.underwriting.policy;

import java.math.BigDecimal;

/**
 * What the rule engine needs to make a call.
 *
 * <p>monthlyRevenue is whatever RevenueCalculator produced. The rule engine has no idea
 * which definition of revenue that is and no way to ask.
 */
public record PolicyEvaluationInput(
        Long applicationId,
        String tenantId,
        String product,
        String stateCode,
        BigDecimal amountRequested,
        BigDecimal monthlyRevenue,
        int monthsOfStatementHistory,
        int timeInBusinessMonths,
        Integer ownerFico) {
}
