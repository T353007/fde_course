package com.northstar.fraud.vendor;

import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/**
 * Calls Sentinel Risk.
 *
 * <p>There is no timeout configured. That is not an accident in the code. It is a gap.
 * Sentinel's p99 is usually fine. When it is not, this thread waits until the socket
 * dies. Underwriting then waits on us. See FraudGateway.
 */
@Component
public class SentinelRiskClient {

    private static final Logger log = LoggerFactory.getLogger(SentinelRiskClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public SentinelRiskClient(@Value("${northstar.sentinel.base-url:http://localhost:8090}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.restTemplate = new RestTemplate();
    }

    public SentinelScore fetch(String ein, String legalName) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> body = restTemplate.getForObject(
                    baseUrl + "/sentinel/v1/score?ein={ein}&name={name}",
                    Map.class,
                    ein == null ? "" : ein,
                    legalName == null ? "" : legalName);
            if (body == null) {
                return SentinelScore.unavailable();
            }
            int score = asInt(body.get("score"), 0);
            Object reasons = body.get("reasonCodes");
            List<String> codes = reasons instanceof List<?> list
                    ? list.stream().map(String::valueOf).toList()
                    : List.of();
            boolean degraded = codes.isEmpty() && body.get("score") != null;
            return new SentinelScore(score, codes, degraded);
        } catch (RestClientException e) {
            log.warn("Sentinel call failed, falling back to local rules: {}", e.getMessage());
            return SentinelScore.unavailable();
        }
    }

    private static int asInt(Object value, int fallback) {
        if (value instanceof Number n) {
            return n.intValue();
        }
        return fallback;
    }

    public record SentinelScore(int score, List<String> reasonCodes, boolean degraded) {
        public static SentinelScore unavailable() {
            return new SentinelScore(0, List.of(), true);
        }
    }
}
