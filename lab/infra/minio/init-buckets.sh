#!/usr/bin/env bash
# Create MinIO buckets used by document-service and policy storage.
set -euo pipefail

MC_HOST="${MC_HOST:-local}"
ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
ACCESS="${MINIO_ROOT_USER:-northstar}"
SECRET="${MINIO_ROOT_PASSWORD:-northstarsecret}"

echo "Waiting for MinIO at $ENDPOINT"
for i in $(seq 1 60); do
  if curl -sf "$ENDPOINT/minio/health/ready" >/dev/null; then
    break
  fi
  sleep 1
done

mc alias set "$MC_HOST" "$ENDPOINT" "$ACCESS" "$SECRET"
mc mb --ignore-existing "$MC_HOST/northstar-documents"
mc mb --ignore-existing "$MC_HOST/northstar-policies"
echo "MinIO buckets ready"
