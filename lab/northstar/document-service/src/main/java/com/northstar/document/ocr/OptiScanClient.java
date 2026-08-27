package com.northstar.document.ocr;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/**
 * Calls the OptiScan OCR vendor.
 *
 * <p>This service was rewritten in 2021 and this client came out of that work, so it has
 * timeouts and it logs the vendor job id. That is not true of every vendor client at
 * Northstar. See SentinelRiskClient in fraud-service.
 *
 * <p>What it does not do is judge the answer. OptiScan returns high confidence on faxed
 * statements and the numbers are wrong. There is no check for that here, because there is
 * nothing to check it against.
 */
@Component
public class OptiScanClient {

    private static final Logger log = LoggerFactory.getLogger(OptiScanClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public OptiScanClient(RestTemplateBuilder builder,
                          @Value("${northstar.vendors.optiscan.base-url:http://localhost:8090}") String baseUrl,
                          @Value("${northstar.vendors.optiscan.timeout-ms:20000}") long timeoutMs) {
        this.baseUrl = baseUrl;
        this.restTemplate = builder
                .setConnectTimeout(Duration.ofMillis(5000))
                .setReadTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }

    /**
     * Sends a document for extraction.
     *
     * @param storageKey MinIO key. OptiScan reads the object itself, we do not stream bytes.
     * @return the vendor response, or null when the call failed
     */
    public OptiScanResponse extract(String storageKey, String docType) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("storageKey", storageKey);
        body.put("documentType", docType);
        body.put("mode", "BANK_STATEMENT");

        try {
            OptiScanResponse response = restTemplate.postForObject(
                    baseUrl + "/optiscan/v2/extract", body, OptiScanResponse.class);

            if (response != null) {
                log.info("optiscan extract ok jobId={} confidence={} lines={}",
                        response.jobId(), response.confidence(),
                        response.lines() == null ? 0 : response.lines().size());
            }
            return response;

        } catch (RestClientException e) {
            log.error("optiscan extract failed for storageKey={}", storageKey, e);
            return null;
        }
    }
}
