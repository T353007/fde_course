package com.northstar.document.ocr;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.northstar.common.event.DocumentExtractedEvent;
import com.northstar.common.model.BankTransaction;
import com.northstar.document.entity.DocumentEntity;
import com.northstar.document.entity.DocumentExtractionEntity;
import com.northstar.document.kafka.DocumentEventPublisher;
import com.northstar.document.repo.DocumentExtractionRepository;

/**
 * Runs OCR on a document and publishes what came out.
 *
 * <p>Order of work: call the vendor, write an extraction row, publish document.extracted.
 * If the publish fails the extraction row is still there, so a replay is possible in
 * principle. There is no replay tool.
 */
@Service
public class OcrOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(OcrOrchestrator.class);

    /** OptiScan sends MM/dd/yyyy most of the time and MM/dd sometimes. */
    private static final DateTimeFormatter FULL_DATE = DateTimeFormatter.ofPattern("MM/dd/yyyy");

    private final OptiScanClient optiScanClient;
    private final DocumentExtractionRepository extractionRepository;
    private final DocumentEventPublisher eventPublisher;

    public OcrOrchestrator(OptiScanClient optiScanClient,
                           DocumentExtractionRepository extractionRepository,
                           DocumentEventPublisher eventPublisher) {
        this.optiScanClient = optiScanClient;
        this.extractionRepository = extractionRepository;
        this.eventPublisher = eventPublisher;
    }

    public void process(DocumentEntity document) {
        OptiScanResponse vendorResponse = optiScanClient.extract(document.getStorageKey(), document.getDocType());

        DocumentExtractionEntity extraction = new DocumentExtractionEntity();
        extraction.setDocumentId(document.getDocumentId());
        extraction.setExtractor("OPTISCAN_V2");
        extraction.setExtractorVersion("2.14.3");
        extraction.setExtractedAt(Instant.now());

        if (vendorResponse == null) {
            extraction.setFieldName("_ocr_failed");
            extraction.setFieldValue("no vendor response");
            extractionRepository.save(extraction);
            log.warn("no extraction for document {}", document.getDocumentId());
            return;
        }

        extraction.setFieldName("statement_lines");
        extraction.setFieldValue(String.valueOf(
                vendorResponse.lines() == null ? 0 : vendorResponse.lines().size()));
        extraction.setConfidence(vendorResponse.confidence());
        extraction.setRawResponse(String.valueOf(vendorResponse.lines()));
        extractionRepository.save(extraction);

        List<BankTransaction> transactions = toTransactions(document.getApplicationId(), vendorResponse);

        eventPublisher.publishExtracted(new DocumentExtractedEvent(
                document.getDocumentId(),
                document.getApplicationId(),
                document.getTenantId(),
                "OPTISCAN_V2",
                vendorResponse.confidence(),
                transactions,
                Instant.now()));
    }

    private List<BankTransaction> toTransactions(Long applicationId, OptiScanResponse response) {
        List<BankTransaction> out = new ArrayList<>();
        if (response.lines() == null) {
            return out;
        }

        int dropped = 0;
        for (OptiScanResponse.Line line : response.lines()) {
            BigDecimal amount = AmountParser.parse(line.amount());
            LocalDate date = parseDate(line.date());

            if (amount == null || date == null) {
                dropped++;
                continue;
            }

            // category and category_source are left null. The classifier that was supposed
            // to fill them in was scoped in 2022 and never built.
            out.add(new BankTransaction(null, applicationId, date, line.description(), amount, null, null));
        }

        if (dropped > 0) {
            // This is the only sign that lines went missing. Nobody alerts on it.
            log.warn("dropped {} unparseable lines for application {}", dropped, applicationId);
        }

        return out;
    }

    private LocalDate parseDate(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            return LocalDate.parse(raw.trim(), FULL_DATE);
        } catch (DateTimeParseException e) {
            // MM/dd with no year. Assumes the current year, which is wrong every January
            // for December statements.
            try {
                String withYear = raw.trim() + "/" + LocalDate.now().getYear();
                return LocalDate.parse(withYear, FULL_DATE);
            } catch (DateTimeParseException e2) {
                return null;
            }
        }
    }
}
