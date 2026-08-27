package com.northstar.document.ocr;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * What OptiScan sends back.
 *
 * <p>Amounts come back as strings, with whatever formatting the source document had. We
 * have seen "48,230.00", "48230.00", "$48,230.00", and on faxed statements "48.230,00".
 * {@link OcrOrchestrator} cleans them up.
 *
 * <p>OptiScan adds fields without telling anyone, so this is lenient about unknowns.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record OptiScanResponse(
        String jobId,
        String status,
        Double confidence,
        List<Line> lines) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Line(String date, String description, String amount, String type) {
    }
}
