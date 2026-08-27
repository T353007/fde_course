package com.northstar.underwriting.decision;

import java.math.BigDecimal;

/**
 * Input to the decision engine.
 *
 * <p>Half of these fields come from the application row and half come from whatever the
 * caller happened to have. timeInBusinessMonths is not stored anywhere. The portal asks for
 * it and passes it through, and the batch rerun job passes 0, which means every reran
 * application declines on time in business. Bill's fix_stuff.sh cleans those up.
 */
public record DecisionRequest(
        Long applicationId,
        String tenantId,
        String product,
        String stateCode,
        String legalName,
        String ein,
        BigDecimal amountRequested,
        BigDecimal monthlyDebtService,
        int monthsOfHistory,
        int timeInBusinessMonths,
        Integer ownerFico) {
}
