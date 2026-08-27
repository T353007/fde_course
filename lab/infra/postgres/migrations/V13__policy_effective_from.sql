-- V13: policy effective dates. Added when Doug asked for dated retrieval.
-- Four of the eight seed rows stay null because nobody backfilled the drafts
-- and overlays. Defect lives in the data, enabled by this nullable column.

ALTER TABLE northstar.policy_documents
    ADD COLUMN effective_from DATE;

COMMENT ON COLUMN northstar.policy_documents.effective_from IS
    'When this file becomes active. Null means unknown / draft / never set.';
