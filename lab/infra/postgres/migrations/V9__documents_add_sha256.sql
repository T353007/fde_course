-- V9: add sha256 to documents for portal upload dedupe work.
-- Rolled out only on the portal path. Email, fax, and vendor pulls still
-- land with null. Most historical rows stay null forever. Defect D-09.

ALTER TABLE northstar.documents
    ADD COLUMN sha256 TEXT;

COMMENT ON COLUMN northstar.documents.sha256 IS
    'Content hash when the upload path computed one. Null on older and non-portal rows.';
