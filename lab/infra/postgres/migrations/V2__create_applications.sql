-- V2: applications. One row per loan request.

CREATE TABLE northstar.applications (
    application_id   BIGSERIAL PRIMARY KEY,
    applicant_id     BIGINT NOT NULL REFERENCES northstar.applicants(applicant_id),
    product          TEXT NOT NULL,      -- TERM_LOAN | LOC | SBA_7A | EQUIPMENT
    amount_requested NUMERIC(14,2),
    status           TEXT NOT NULL,
    submitted_at     TIMESTAMPTZ,
    decided_at       TIMESTAMPTZ,
    customer_id      TEXT,               -- second tenant convention, defect D-07
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- customer_id was added for Bayline onboarding in 2020. Product did not want
-- to touch applicants.tenant_id, so a second convention landed here. Values are
-- "BAY", "bayline", "2", "NSC-DIRECT", "CASCADE-FUNDING", null, and worse.
-- Defect D-07.

COMMENT ON COLUMN northstar.applications.submitted_at IS
    'Set by the portal when the applicant clicks submit. Not the source of truth for cycle time. See application_events.';

COMMENT ON COLUMN northstar.applications.customer_id IS
    'Partner / tenant code used by CRM sync. Do not confuse with applicants.tenant_id.';
