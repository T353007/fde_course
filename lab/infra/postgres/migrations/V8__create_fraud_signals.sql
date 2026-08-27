-- V8: fraud_signals. Raw vendor output stored for audit.

CREATE TABLE northstar.fraud_signals (
    signal_id           BIGSERIAL PRIMARY KEY,
    application_id      BIGINT NOT NULL REFERENCES northstar.applications(application_id),
    vendor              TEXT NOT NULL,
    score               INT,
    band                TEXT,
    reason_codes        TEXT,            -- may be null when Sentinel omits them. Defect D-17.
    raw_response        TEXT,
    vendor_latency_ms   INT,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN northstar.fraud_signals.reason_codes IS
    'Vendor reason codes when present. Sentinel sometimes returns score only.';
