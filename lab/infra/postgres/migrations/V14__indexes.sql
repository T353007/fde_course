-- V14: indexes people added under pressure.
--
-- idx_applicants_legal_name looks useful for search. Nothing in the hot path
-- uses it. EXPLAIN on underwriting lookups never touches it.
--
-- What Mission 05 actually needs is an index on
-- application_events (application_id, event_type) or (event_type, occurred_at).
-- That index is not here. Learners notice when the timing queries crawl.

CREATE INDEX idx_applicants_legal_name
    ON northstar.applicants (legal_name);

CREATE INDEX idx_applications_status
    ON northstar.applications (status);

CREATE INDEX idx_documents_application_id
    ON northstar.documents (application_id);

CREATE INDEX idx_bank_transactions_application_id
    ON northstar.bank_transactions (application_id);

CREATE INDEX idx_decisions_application_id
    ON northstar.decisions (application_id);

-- application_events has no composite index on (application_id, event_type).
-- Only a lonely FK-ish single column would help a little, and we skipped even
-- that. Cycle time queries scan the whole event log.

COMMENT ON INDEX northstar.idx_applicants_legal_name IS
    'Added for portal typeahead. Portal typeahead was never shipped.';
