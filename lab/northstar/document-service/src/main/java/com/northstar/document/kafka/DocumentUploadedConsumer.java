package com.northstar.document.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import com.northstar.common.event.DocumentUploadedEvent;
import com.northstar.document.entity.DocumentEntity;
import com.northstar.document.ocr.OcrOrchestrator;
import com.northstar.document.repo.DocumentRepository;

/**
 * The document worker. Consumes document.uploaded and runs OCR.
 *
 * <p>Kafka gives at least once delivery. That means this method will sometimes run twice
 * for the same event, usually after a consumer group rebalance or a deploy. There is no
 * check for that here. Running twice creates a second document_extractions row and
 * publishes document.extracted a second time, which makes underwriting-service store the
 * same bank transactions again.
 *
 * <p>The effect is doubled revenue on the affected application. It is rare enough that it
 * reads as a data quality problem rather than a bug. Renee has a note in her spreadsheet
 * that says "check for double lines" and she checks by hand.
 *
 * <p>The pieces to fix it are already here. document_extractions has a document_id, and
 * DocumentRepository.findFirstByApplicationIdAndSha256 exists. Nothing calls them for this.
 */
@Component
public class DocumentUploadedConsumer {

    private static final Logger log = LoggerFactory.getLogger(DocumentUploadedConsumer.class);

    private final DocumentRepository documentRepository;
    private final OcrOrchestrator ocrOrchestrator;

    public DocumentUploadedConsumer(DocumentRepository documentRepository, OcrOrchestrator ocrOrchestrator) {
        this.documentRepository = documentRepository;
        this.ocrOrchestrator = ocrOrchestrator;
    }

    @KafkaListener(topics = "document.uploaded", groupId = "document-worker")
    public void onDocumentUploaded(DocumentUploadedEvent event) {
        log.info("document.uploaded received documentId={} applicationId={}",
                event.documentId(), event.applicationId());

        DocumentEntity document = documentRepository.findById(event.documentId()).orElse(null);
        if (document == null) {
            // Happens when the consumer reads the event before the upload transaction
            // commits. Rare. The event is dropped and the document is never OCRed until
            // someone reuploads it.
            log.warn("document {} not found, dropping event", event.documentId());
            return;
        }

        ocrOrchestrator.process(document);
    }
}
