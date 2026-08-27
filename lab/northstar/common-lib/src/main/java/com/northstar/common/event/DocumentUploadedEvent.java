package com.northstar.common.event;

import java.time.Instant;

/**
 * Published on document.uploaded.
 *
 * <p>sha256 is null for uploads that came through the old multipart path, because that
 * path never computed one. The consumer treats null as "not seen before".
 */
public record DocumentUploadedEvent(
        Long documentId,
        Long applicationId,
        String tenantId,
        String docType,
        String storageKey,
        String sha256,
        Instant uploadedAt) {
}
