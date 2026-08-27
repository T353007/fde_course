-- V1: applicants. The oldest table in the lending platform.
-- Sam Ortiz says this went live in 2014 with the first portal rewrite.

CREATE SCHEMA IF NOT EXISTS northstar;

CREATE TABLE northstar.applicants (
    applicant_id     BIGSERIAL PRIMARY KEY,
    legal_name       TEXT NOT NULL,
    dba_name         TEXT,
    ein              TEXT,               -- nullable, and often wrong
    owner_ssn_last4  TEXT,
    email            TEXT,
    phone            TEXT,
    tenant_id        TEXT NOT NULL,      -- NSC_DIRECT | BAYLINE | CASCADE
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- No unique constraint on ein. Two underwriters can open the same bakery
-- under different EIN spellings and nobody notices until Mission 10.
-- That is defect D-03. Leaving it alone on purpose.

COMMENT ON COLUMN northstar.applicants.ein IS
    'Federal EIN. Free text. Formatting is not enforced.';
