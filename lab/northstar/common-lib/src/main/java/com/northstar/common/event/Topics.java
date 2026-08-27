package com.northstar.common.event;

/**
 * Kafka topic names.
 *
 * <p>These are duplicated as string literals in two Python jobs and one Looker block.
 * Renaming a topic here does not rename it there.
 */
public final class Topics {

    public static final String APPLICATION_SUBMITTED = "application.submitted";
    public static final String DOCUMENT_UPLOADED = "document.uploaded";
    public static final String DOCUMENT_EXTRACTED = "document.extracted";
    public static final String UNDERWRITING_DECISIONED = "underwriting.decisioned";

    /** Added for the AI bridge. Nothing produces to it yet. */
    public static final String AI_EXTRACTION_REQUESTED = "ai.extraction.requested";

    private Topics() {
    }
}
