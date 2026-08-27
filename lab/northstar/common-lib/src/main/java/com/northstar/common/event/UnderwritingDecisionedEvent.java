package com.northstar.common.event;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Published on underwriting.decisioned.
 *
 * <p>reasonCodes is a comma separated string, not a list. The decisions table stores it
 * that way and this record copies the column so the CRM sync does not have to change.
 */
public record UnderwritingDecisionedEvent(
        Long applicationId,
        String tenantId,
        String outcome,
        String reasonCodes,
        BigDecimal monthlyRevenue,
        BigDecimal dscr,
        Instant decidedAt) {
}
