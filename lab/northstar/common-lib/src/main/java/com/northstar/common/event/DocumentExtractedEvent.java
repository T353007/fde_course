package com.northstar.common.event;

import java.time.Instant;
import java.util.List;

import com.northstar.common.model.BankTransaction;

/**
 * Published on document.extracted. underwriting-service consumes it.
 *
 * <p>confidence is the number OptiScan hands back. People read it as "how likely the
 * values are right". It is closer to "how sure the OCR engine is that it read the
 * characters it read". Those are different and the difference costs money on faxed
 * statements.
 */
public record DocumentExtractedEvent(
        Long documentId,
        Long applicationId,
        String tenantId,
        String extractor,
        Double confidence,
        List<BankTransaction> transactions,
        Instant extractedAt) {
}
