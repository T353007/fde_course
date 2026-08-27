#!/usr/bin/env bash
# Load seed CSVs into Postgres. Migrations must already be applied.
set -euo pipefail

# This file lives at lab/infra/postgres/seed/load_seed.sh.
# Lab root is three levels up (seed -> postgres -> infra -> lab).
LAB_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DATA="$(cd "$(dirname "$0")" && pwd)/data"
COMPOSE_FILE="${COMPOSE_FILE:-$LAB_ROOT/docker-compose.yml}"
COMPOSE="docker compose -f $COMPOSE_FILE"

if [ ! -d "$DATA" ]; then
  echo "No seed data at $DATA. Run: python3 seed_generator.py"
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

echo "Loading seed from $DATA"

# Copy CSVs into the postgres container, then COPY FROM those paths.
$COMPOSE exec -T postgres bash -lc 'mkdir -p /seed-data'
$COMPOSE cp "$DATA/." postgres:/seed-data/

$COMPOSE exec -T postgres psql -U northstar -d northstar -v ON_ERROR_STOP=1 <<'SQL'
TRUNCATE
  northstar.fraud_signals,
  northstar.decisions,
  northstar.bank_transactions,
  northstar.document_extractions,
  northstar.documents,
  northstar.application_events,
  northstar.applications,
  northstar.applicants,
  northstar.policy_documents
CASCADE;

COPY northstar.applicants FROM '/seed-data/applicants.csv' CSV HEADER;
COPY northstar.applications FROM '/seed-data/applications.csv' CSV HEADER;
COPY northstar.application_events FROM '/seed-data/application_events.csv' CSV HEADER;
COPY northstar.documents FROM '/seed-data/documents.csv' CSV HEADER;
COPY northstar.document_extractions FROM '/seed-data/document_extractions.csv' CSV HEADER;
COPY northstar.bank_transactions (
  transaction_id, application_id, document_id, account_last4, posted_date,
  description, amount, running_balance, category, category_source, created_at
) FROM '/seed-data/bank_transactions.csv' CSV HEADER;
COPY northstar.decisions FROM '/seed-data/decisions.csv' CSV HEADER;
COPY northstar.fraud_signals FROM '/seed-data/fraud_signals.csv' CSV HEADER;
COPY northstar.policy_documents FROM '/seed-data/policy_documents.csv' CSV HEADER;

SELECT 'applicants' AS t, count(*) FROM northstar.applicants
UNION ALL SELECT 'applications', count(*) FROM northstar.applications
UNION ALL SELECT 'events', count(*) FROM northstar.application_events
UNION ALL SELECT 'transactions', count(*) FROM northstar.bank_transactions;
SQL

echo "Seed loaded."
