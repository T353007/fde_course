package com.northstar.common.event;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Published on application.submitted.
 *
 * <p>Two timestamps ride along and they are not the same thing. submittedAt is whatever
 * the portal put in the request body, which is the applicant's browser clock.
 * acceptedAt is when this service wrote the row. Downstream consumers pick whichever one
 * they noticed first.
 */
public record ApplicationSubmittedEvent(
        Long applicationId,
        Long applicantId,
        String tenantId,
        String product,
        BigDecimal amountRequested,
        Instant submittedAt,
        Instant acceptedAt) {
}
