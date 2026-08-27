-- V3: application_events. Append only status and review history.
-- This is the real clock for cycle time. Mission 05 lives here.

CREATE TABLE northstar.application_events (
    event_id         BIGSERIAL PRIMARY KEY,
    application_id   BIGINT NOT NULL REFERENCES northstar.applications(application_id),
    event_type       TEXT NOT NULL,
    from_status      TEXT,
    to_status        TEXT,
    actor_type       TEXT,
    actor_id         TEXT,
    occurred_at      TIMESTAMPTZ NOT NULL,
    recorded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    detail           TEXT
);

-- Note for whoever reads this later: applications.submitted_at and the
-- SUBMITTED row in this table are not the same moment. The portal writes
-- submitted_at on the client. The backend writes the event when it accepts
-- the request. Median gap is about 40 minutes. Sometimes days.
-- Defect D-11. Do not measure cycle time from applications.submitted_at.

COMMENT ON TABLE northstar.application_events IS
    'Append-only lifecycle log. Source of truth for timing questions.';
