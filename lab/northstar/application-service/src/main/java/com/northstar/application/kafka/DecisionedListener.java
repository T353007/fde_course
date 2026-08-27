package com.northstar.application.kafka;

import java.time.Instant;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import com.northstar.application.entity.ApplicationEntity;
import com.northstar.application.repo.ApplicationRepository;
import com.northstar.common.event.UnderwritingDecisionedEvent;

/**
 * Applies underwriting.decisioned back onto the application row.
 *
 * <p>Status mapping is a switch on outcome strings. A new outcome from underwriting that
 * nobody told this service about leaves the row in whatever status it had.
 */
@Component
public class DecisionedListener {

    private static final Logger log = LoggerFactory.getLogger(DecisionedListener.class);

    private final ApplicationRepository applicationRepository;

    public DecisionedListener(ApplicationRepository applicationRepository) {
        this.applicationRepository = applicationRepository;
    }

    @KafkaListener(topics = "underwriting.decisioned", groupId = "application-service")
    public void onDecisioned(UnderwritingDecisionedEvent event) {
        ApplicationEntity app = applicationRepository.findById(event.applicationId()).orElse(null);
        if (app == null) {
            log.warn("decisioned event for missing application {}", event.applicationId());
            return;
        }

        String nextStatus = switch (event.outcome()) {
            case "APPROVED" -> "APPROVED";
            case "DECLINED" -> "DECLINED";
            case "REFER_MANUAL" -> "IN_REVIEW";
            default -> app.getStatus();
        };

        app.setStatus(nextStatus);
        app.setDecidedAt(event.decidedAt());
        app.setUpdatedAt(Instant.now());
        applicationRepository.save(app);
    }
}
