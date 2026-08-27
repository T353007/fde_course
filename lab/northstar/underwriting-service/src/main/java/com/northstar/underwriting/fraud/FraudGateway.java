package com.northstar.underwriting.fraud;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.northstar.common.dto.FraudScoreRequest;
import com.northstar.common.dto.FraudScoreResponse;

/**
 * Calls fraud-service.
 *
 * <p>fraud-service returns nine fields. This gateway hands back one integer.
 *
 * <p>The reason is history, not disagreement. When this was written in 2019, fraud-service
 * returned a bare score. Ada's team rebuilt it in 2022 and added reason codes, a device
 * risk signal, velocity flags, and a vendorDegraded marker that says "the vendor answered
 * but with missing data, so this score came from local rules only". They told the
 * underwriting team. The underwriting team had a release to ship.
 *
 * <p>So today an application can come back with vendorDegraded true and REVIEW risk band,
 * and underwriting sees the integer 812 and treats it like any other 812. The reason codes
 * that would have explained it are dropped on the floor here.
 */
@Component
public class FraudGateway {

    private static final Logger log = LoggerFactory.getLogger(FraudGateway.class);

    private final RestTemplate restTemplate;
    private final String fraudServiceBaseUrl;

    public FraudGateway(@Value("${northstar.fraud-service.base-url:http://localhost:8084}") String baseUrl) {
        this.fraudServiceBaseUrl = baseUrl;

        // No timeout set. A plain RestTemplate with no request factory config waits as long
        // as the socket stays open. fraud-service itself has no timeout on the Sentinel
        // vendor call, so a slow Sentinel holds this thread too. See SentinelRiskClient.
        this.restTemplate = new RestTemplate();
    }

    /**
     * Returns the fraud score, or 0 when the call fails.
     *
     * <p>Returning 0 on failure means a fraud-service outage reads as "no fraud risk". That
     * is the wrong direction to fail. It was done this way so an outage would not stop
     * decisions, which was the right call for uptime and the wrong call for risk.
     */
    public int getFraudScore(Long applicationId, String tenantId, String legalName, String ein) {
        try {
            FraudScoreRequest request = new FraudScoreRequest(
                    applicationId, tenantId, legalName, ein, null, null, null, null);

            FraudScoreResponse response = restTemplate.postForObject(
                    fraudServiceBaseUrl + "/api/v1/fraud/score", request, FraudScoreResponse.class);

            if (response == null) {
                return 0;
            }

            // Everything except score() is discarded right here.
            return response.score();

        } catch (RestClientException e) {
            log.warn("fraud-service call failed for application {}, continuing with score 0", applicationId, e);
            return 0;
        }
    }
}
