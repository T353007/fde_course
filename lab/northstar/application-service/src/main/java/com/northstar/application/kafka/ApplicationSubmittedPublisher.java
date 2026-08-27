package com.northstar.application.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.northstar.common.event.ApplicationSubmittedEvent;
import com.northstar.common.event.Topics;

/**
 * Publishes application.submitted.
 *
 * <p>No key is set. Partitioning was "we will add keys when we need ordered consumers."
 * That day never came. Underwriting and fraud both consume this topic.
 */
@Component
public class ApplicationSubmittedPublisher {

    private static final Logger log = LoggerFactory.getLogger(ApplicationSubmittedPublisher.class);

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public ApplicationSubmittedPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publish(ApplicationSubmittedEvent event) {
        try {
            kafkaTemplate.send(Topics.APPLICATION_SUBMITTED, event);
        } catch (RuntimeException e) {
            log.error("failed to publish application.submitted for application {}", event.applicationId(), e);
        }
    }
}
