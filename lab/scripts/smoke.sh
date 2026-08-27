#!/usr/bin/env bash
# Mission 02 smoke checks after make bootstrap and starting Java services.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$LAB_ROOT/docker-compose.yml}"
COMPOSE="docker compose -f $COMPOSE_FILE"
TENANT_HEADER="X-Tenant-Id: NSC_DIRECT"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

pass() {
  echo "OK: $*"
}

echo "== Northstar lab smoke (Mission 02) =="

command -v docker >/dev/null || fail "Docker is not installed"
docker info >/dev/null 2>&1 || fail "Docker is not running"

if ! $COMPOSE ps --status running --services 2>/dev/null | grep -qx postgres; then
  fail "Postgres is not running. Run: cd lab && make bootstrap"
fi

echo "Checking seed counts..."
counts=$($COMPOSE exec -T postgres psql -U northstar -d northstar -At -c "
SELECT 'applications:' || count(*) FROM northstar.applications
UNION ALL SELECT 'transactions:' || count(*) FROM northstar.bank_transactions
UNION ALL SELECT 'events:' || count(*) FROM northstar.application_events;
")
echo "$counts"

echo "$counts" | grep -q '^applications:1200$' || fail "expected 1200 applications (run: make seed)"
echo "$counts" | grep -q '^transactions:61912$' || fail "expected 61912 transactions"
echo "$counts" | grep -q '^events:17400$' || fail "expected 17400 events"
pass "database seeded"

wait_http() {
  local url=$1
  local name=$2
  for _ in $(seq 1 30); do
    if curl -sf "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  fail "$name not reachable at $url (start with: make run-application / make run-underwriting)"
}

wait_http "http://localhost:8081/actuator/health" "application-service" 2>/dev/null || \
  wait_http "http://localhost:8081/api/v1/applications/8" "application-service"

wait_http "http://localhost:8083/actuator/health" "underwriting-service" 2>/dev/null || \
  wait_http "http://localhost:8083/api/v1/applications/8/revenue-summary" "underwriting-service"

app_json=$(curl -sf "http://localhost:8081/api/v1/applications/8" -H "$TENANT_HEADER")
echo "$app_json" | grep -q '"applicationId":8' || fail "application 8 lookup failed"
echo "$app_json" | grep -q '"customerId":"NSC-DIRECT"' || fail "application 8 missing customerId NSC-DIRECT"
pass "application-service /applications/8"

rev_json=$(curl -sf "http://localhost:8083/api/v1/applications/8/revenue-summary" -H "$TENANT_HEADER")
echo "$rev_json" | grep -q '"applicationId":8' || fail "revenue-summary for app 8 failed"
echo "$rev_json" | grep -q '"avgMonthlyRevenue"' || fail "revenue-summary missing avgMonthlyRevenue"
echo "$rev_json" | grep -q '"calcVersion":"v2"' || fail "revenue-summary missing calcVersion v2"
pass "underwriting-service /applications/8/revenue-summary"

tx_json=$(curl -sf "http://localhost:8083/api/v1/applications/8/bank-transactions" -H "$TENANT_HEADER")
echo "$tx_json" | grep -q '"transactions"' || fail "bank-transactions response missing transactions array"
pass "underwriting-service /applications/8/bank-transactions"

cascade_json=$(curl -sf "http://localhost:8083/api/v1/applications/1130/revenue-summary" -H "$TENANT_HEADER" || true)
if [ -n "$cascade_json" ]; then
  echo "$cascade_json" | grep -q '"applicationId":1130' || fail "CASCADE app 1130 revenue-summary failed"
  pass "underwriting-service /applications/1130/revenue-summary (CASCADE, no bank data)"
fi

echo ""
echo "Smoke passed. Mission 02 endpoints look good."
