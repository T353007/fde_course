-- V4: documents. Uploaded files for an application.
-- sha256 arrives later in V9. Do not add it here.

CREATE TABLE northstar.documents (
    document_id      BIGSERIAL PRIMARY KEY,
    application_id   BIGINT NOT NULL REFERENCES northstar.applications(application_id),
    doc_type         TEXT NOT NULL,
    file_name        TEXT,
    mime_type        TEXT,
    size_bytes       BIGINT,
    storage_key      TEXT,
    source           TEXT,               -- PORTAL_UPLOAD | EMAIL | FAX | BRANCH_SCAN | VENDOR
    page_count       INT,
    uploaded_by      TEXT,
    uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    status           TEXT NOT NULL DEFAULT 'RECEIVED',
    ocr_quality      TEXT
);

COMMENT ON COLUMN northstar.documents.source IS
    'How the file arrived. Portal path is the only one that later got hashing.';
