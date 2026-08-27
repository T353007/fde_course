package com.northstar.application.portal;

import java.math.BigDecimal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.northstar.common.dto.UnderwritingRevenueView;

/**
 * Calls underwriting-service for the number the portal cash flow widget shows.
 *
 * <p>This is caller number three of the revenue function, over REST. Product wants total
 * deposits here. See PORTAL-1188 on PortalSummaryController.
 */
@Component
public class UnderwritingClient {

    private static final Logger log = LoggerFactory.getLogger(UnderwritingClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public UnderwritingClient(@Value("${northstar.underwriting.base-url:http://localhost:8083}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.restTemplate = new RestTemplate();
    }

    public BigDecimal monthlyRevenue(long applicationId, int months) {
        try {
            UnderwritingRevenueView view = restTemplate.getForObject(
                    baseUrl + "/api/v1/underwriting/applications/{id}/revenue?months={months}",
                    UnderwritingRevenueView.class,
                    applicationId,
                    months);
            if (view == null || view.getMonthlyRevenue() == null) {
                return BigDecimal.ZERO;
            }
            return view.getMonthlyRevenue();
        } catch (RestClientException e) {
            log.warn("underwriting revenue call failed for application {}: {}", applicationId, e.getMessage());
            return BigDecimal.ZERO;
        }
    }
}
