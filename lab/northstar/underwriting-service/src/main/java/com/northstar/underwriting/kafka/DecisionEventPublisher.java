package com.northstar.underwriting.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.northstar.common.event.Topics;
import com.northstar.common.event.UnderwritingDecisionedEvent;

/**
 * Publishes underwriting.decisioned.
 *
 * <p>This one does set a key, unlike application-service. The key is the application id, so
 * decisions for the same application land on the same partition and stay in order. That
 * matters because an application can be decisioned more than once.
 */
@Component
public class DecisionEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(DecisionEventPublisher.class);

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public DecisionEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publishDecisioned(UnderwritingDecisionedEvent event) {
        String key = String.valueOf(event.applicationId());
        try {
            kafkaTemplate.send(Topics.UNDERWRITING_DECISIONED, key, event);
        } catch (RuntimeException e) {
            // Swallowed. A broker problem should not roll back a decision we already wrote.
            // The CRM sync will be out of date until someone replays. There is no replay
            // tool, so someone means Bill.
            log.error("failed to publish underwriting.decisioned for application {}", event.applicationId(), e);
        }
    }
}
