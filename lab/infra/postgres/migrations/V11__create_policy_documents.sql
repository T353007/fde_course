-- V11: policy_documents. Metadata for the policy corpus in object storage.
-- effective_from is intentionally missing here. It arrives in V13.

CREATE TABLE northstar.policy_documents (
    policy_document_id  BIGSERIAL PRIMARY KEY,
    file_name           TEXT NOT NULL,
    title               TEXT,
    doc_kind            TEXT,            -- BASE | TENANT_OVERLAY | PRODUCT_OVERLAY | ADDENDUM
    tenant_id           TEXT,
    product             TEXT,
    version_label       TEXT,
    storage_key         TEXT,
    uploaded_by         TEXT,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE northstar.policy_documents IS
    'Policy file registry. Precedence rules live in people heads, not in this table.';
