-- V7: decisions. Underwriting outcomes.

CREATE TABLE northstar.decisions (
    decision_id           BIGSERIAL PRIMARY KEY,
    application_id        BIGINT NOT NULL REFERENCES northstar.applications(application_id),
    outcome               TEXT NOT NULL,
    approved_amount       NUMERIC(14,2),
    rate_apr              NUMERIC(8,4),
    term_months           INT,
    reason_codes          TEXT,          -- comma separated string, NOT an array. Defect D-04.
    decided_by            TEXT,
    policy_version        TEXT,
    monthly_revenue_used  NUMERIC(14,2),
    dscr                  NUMERIC(8,4),
    decided_at            TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- reason_codes started as a free text box in the 2016 underwriter UI. Someone
-- later started stuffing machine codes into it with commas. Parsing is fragile.
-- Spaces after commas come and go. Trailing commas happen. Defect D-04.

COMMENT ON COLUMN northstar.decisions.reason_codes IS
    'Comma separated adverse / approve codes. Prefer splitting carefully.';
