package com.northstar.common.dto;

/**
 * Input to fraud-service scoring.
 *
 * <p>Written by Ada's team in 2022. It is a record with real validation because they were
 * the only group that got to build something new instead of patching.
 */
public record FraudScoreRequest(
        Long applicationId,
        String tenantId,
        String legalName,
        String ein,
        String ownerSsnLast4,
        String email,
        String ipAddress,
        String deviceFingerprint) {

    public FraudScoreRequest {
        if (applicationId == null) {
            throw new IllegalArgumentException("applicationId is required");
        }
        if (tenantId == null || tenantId.isBlank()) {
            throw new IllegalArgumentException("tenantId is required");
        }
    }
}
