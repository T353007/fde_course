-- V12: track who (or what) set bank_transactions.category.

ALTER TABLE northstar.bank_transactions
    ADD COLUMN category_source TEXT;

-- TEMPORARY (2021-03-14, jkowalski): category_source values are messy across
-- OPTISCAN_RULES / MODEL_V1 / MANUAL / null. Clean this up after the revenue
-- calc rewrite ships. Do not build reports on this column yet.
--
-- (Jan left in 2021. The rewrite never shipped. The comment stayed.)

COMMENT ON COLUMN northstar.bank_transactions.category_source IS
    'Who set category. Null when category is null or when source was never recorded.';
