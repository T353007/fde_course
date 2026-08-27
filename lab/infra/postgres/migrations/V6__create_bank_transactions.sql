-- V6: bank_transactions. Parsed statement lines.
-- category_source arrives in V12.

CREATE TABLE northstar.bank_transactions (
    transaction_id     BIGSERIAL PRIMARY KEY,
    application_id     BIGINT NOT NULL REFERENCES northstar.applications(application_id),
    document_id        BIGINT REFERENCES northstar.documents(document_id),
    account_last4      TEXT,
    posted_date        DATE,
    description        TEXT,
    amount             NUMERIC(14,2) NOT NULL,
    running_balance    NUMERIC(14,2),
    category           TEXT,             -- nullable on purpose; many rows never classified
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN northstar.bank_transactions.category IS
    'Nullable. Null means nobody (or no model) classified this line yet.';
