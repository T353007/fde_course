package com.northstar.document.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.northstar.common.event.DocumentExtractedEvent;
import com.northstar.common.event.DocumentUploadedEvent;
import com.northstar.common.event.Topics;

/** Produces document.uploaded and document.extracted. */
@Component
public class DocumentEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(DocumentEventPublisher.class);

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public DocumentEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publishUploaded(DocumentUploadedEvent event) {
        // Keyed by application id so all documents for one application stay in order.
        String key = String.valueOf(event.applicationId());
        send(Topics.DOCUMENT_UPLOADED, key, event);
    }

    public void publishExtracted(DocumentExtractedEvent event) {
        String key = String.valueOf(event.applicationId());
        send(Topics.DOCUMENT_EXTRACTED, key, event);
    }

    private void send(String topic, String key, Object payload) {
        try {
            kafkaTemplate.send(topic, key, payload);
        } catch (RuntimeException e) {
            log.error("failed to publish to {} key={}", topic, key, e);
        }
    }
}
