package com.northstar.common.dto;

import java.time.Instant;
import java.util.Collections;
import java.util.List;

/**
 * Output from fraud-service scoring.
 *
 * <p>Every field here is set on purpose and documented. Three of them are ignored by the
 * only caller in production. See FraudGateway in underwriting-service.
 *
 * @param score          0 to 1000. Higher is riskier.
 * @param riskBand       LOW, MEDIUM, HIGH, or REVIEW.
 * @param reasonCodes    why the score came out that way. Never null, sometimes empty when
 *                       the vendor returns a bare score.
 * @param deviceRisk     device level signal, separate from the applicant signal.
 * @param velocityFlags  the same EIN or email applying more than once in a short window.
 * @param vendorDegraded true when Sentinel answered but with missing data, so the score is
 *                       from local rules only.
 */
public record FraudScoreResponse(
        Long applicationId,
        int score,
        String riskBand,
        List<String> reasonCodes,
        String deviceRisk,
        List<String> velocityFlags,
        String vendorReferenceId,
        boolean vendorDegraded,
        Instant evaluatedAt) {

    public FraudScoreResponse {
        reasonCodes = reasonCodes == null ? List.of() : List.copyOf(reasonCodes);
        velocityFlags = velocityFlags == null ? List.of() : List.copyOf(velocityFlags);
    }

    public static FraudScoreResponse empty(Long applicationId) {
        return new FraudScoreResponse(applicationId, 0, "LOW", Collections.emptyList(), "UNKNOWN",
                Collections.emptyList(), null, true, Instant.now());
    }

    public boolean isBlocking() {
        return "HIGH".equals(riskBand) || "REVIEW".equals(riskBand);
    }
}
