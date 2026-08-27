-- V10: mailing address bolted onto applicants for partner reporting.
-- Added under a Bayline SLA push. Nobody backfilled historical rows carefully.

ALTER TABLE northstar.applicants
    ADD COLUMN mailing_city  TEXT,
    ADD COLUMN mailing_state TEXT,
    ADD COLUMN mailing_zip   TEXT;

COMMENT ON COLUMN northstar.applicants.mailing_state IS
    'US state code when known. Partner reports group on this.';
