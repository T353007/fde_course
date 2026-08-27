package com.northstar.underwriting.kafka;

import java.math.BigDecimal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import com.northstar.common.event.ApplicationSubmittedEvent;
import com.northstar.underwriting.decision.DecisionRequest;
import com.northstar.underwriting.decision.UnderwritingDecisionService;

/**
 * Consumes application.submitted.
 *
 * <p>The producer sets no key on this topic, so events for the same application can land on
 * different partitions and arrive out of order. In practice this shows up as a resubmitted
 * application getting decisioned twice with the second decision written first.
 */
@Component
public class ApplicationSubmittedListener {

    private static final Logger log = LoggerFactory.getLogger(ApplicationSubmittedListener.class);

    private final UnderwritingDecisionService decisionService;

    public ApplicationSubmittedListener(UnderwritingDecisionService decisionService) {
        this.decisionService = decisionService;
    }

    @KafkaListener(topics = "application.submitted", groupId = "underwriting-service")
    public void onApplicationSubmitted(ApplicationSubmittedEvent event) {
        log.info("application submitted event received applicationId={} tenant={}",
                event.applicationId(), event.tenantId());

        // timeInBusinessMonths and ownerFico are not on the event. Passing 0 and null means
        // every automated pass from this path refers or declines. Underwriters pick them up
        // from the queue and rerun by hand from the portal, which does have the fields.
        DecisionRequest request = new DecisionRequest(
                event.applicationId(),
                event.tenantId(),
                event.product(),
                null,
                null,
                null,
                event.amountRequested(),
                estimateDebtService(event.amountRequested()),
                0,
                0,
                null);

        decisionService.decide(request);
    }

    /**
     * Rough payment estimate when the real amortization is not available.
     *
     * <p>Assumes 36 months at no interest, which understates the payment. It was a
     * placeholder in 2019.
     */
    private BigDecimal estimateDebtService(BigDecimal amountRequested) {
        if (amountRequested == null || amountRequested.signum() <= 0) {
            return BigDecimal.ZERO;
        }
        return amountRequested.divide(BigDecimal.valueOf(36), 2, java.math.RoundingMode.HALF_UP);
    }
}
