-- V5: document_extractions. Field level OCR / model output.

CREATE TABLE northstar.document_extractions (
    extraction_id      BIGSERIAL PRIMARY KEY,
    document_id        BIGINT NOT NULL REFERENCES northstar.documents(document_id),
    extractor          TEXT NOT NULL,
    extractor_version  TEXT,
    field_name         TEXT NOT NULL,
    field_value        TEXT,
    confidence         NUMERIC(8,6),     -- character confidence from OptiScan, not correctness
    is_correct         BOOLEAN,
    raw_response       TEXT,
    extracted_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- confidence is whatever the vendor reported. For OptiScan it is character
-- level OCR confidence. It does not mean "this number is right." Faxed
-- statements often score above 0.95 and still invent digits. Defect D-05.

COMMENT ON COLUMN northstar.document_extractions.confidence IS
    'Vendor reported confidence. Not calibrated against ground truth.';
