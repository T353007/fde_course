package com.northstar.fraud.scoring;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Service;

import com.northstar.common.dto.FraudScoreRequest;
import com.northstar.common.dto.FraudScoreResponse;
import com.northstar.fraud.vendor.SentinelRiskClient;
import com.northstar.fraud.vendor.SentinelRiskClient.SentinelScore;

/**
 * Local rules plus Sentinel. Always returns a full response, including fields
 * underwriting currently ignores.
 */
@Service
public class FraudScoringService {

    private final SentinelRiskClient sentinel;

    public FraudScoringService(SentinelRiskClient sentinel) {
        this.sentinel = sentinel;
    }

    public FraudScoreResponse score(FraudScoreRequest request) {
        SentinelScore vendor = sentinel.fetch(request.ein(), request.legalName());
        List<String> reasons = new ArrayList<>(vendor.reasonCodes());
        List<String> velocity = new ArrayList<>();

        int score = vendor.score();
        if (request.ein() == null || request.ein().isBlank()) {
            score = Math.max(score, 400);
            reasons.add("MISSING_EIN");
        }
        if (looksLikeRoundRobinEmail(request.email())) {
            score = Math.max(score, 620);
            velocity.add("EMAIL_PATTERN");
            reasons.add("VELOCITY_EMAIL");
        }

        String band = bandFor(score);
        boolean degraded = vendor.degraded();
        if (degraded && reasons.isEmpty()) {
            reasons.add("VENDOR_DEGRADED");
        }

        return new FraudScoreResponse(
                request.applicationId(),
                Math.min(score, 1000),
                band,
                reasons,
                degraded ? "UNKNOWN" : "OK",
                velocity,
                degraded ? null : "sentinel-" + request.applicationId(),
                degraded,
                Instant.now());
    }

    static String bandFor(int score) {
        if (score >= 800) {
            return "HIGH";
        }
        if (score >= 600) {
            return "REVIEW";
        }
        if (score >= 350) {
            return "MEDIUM";
        }
        return "LOW";
    }

    static boolean looksLikeRoundRobinEmail(String email) {
        if (email == null) {
            return false;
        }
        String lower = email.toLowerCase();
        return lower.contains("temporary") || lower.contains("mailinator") || lower.contains("+app");
    }
}
