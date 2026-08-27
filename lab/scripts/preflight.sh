#!/usr/bin/env bash
# Quick checks before `make up` / `make bootstrap`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not on PATH."
  echo "Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running."
  echo "Start Docker Desktop, wait until it is healthy, then retry."
  exit 1
fi

# shellcheck disable=SC1091
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env"
  set +a
fi

LAB_POSTGRES_PORT="${LAB_POSTGRES_PORT:-5432}"

check_port() {
  local port="$1"
  local label="$2"

  # Lab already running on this port (e.g. re-running make bootstrap).
  if docker ps --filter "publish=${port}" --format '{{.Names}}' 2>/dev/null \
    | grep -q '^northstar-'; then
    return 0
  fi

  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo ""
    echo "Port $port ($label) is already in use."
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sed -n '1,3p' || true
    if [[ "$port" == "$LAB_POSTGRES_PORT" && "$LAB_POSTGRES_PORT" == "5432" ]]; then
      echo ""
      echo "Another Postgres is probably running on 5432."
      echo "Either stop it, or set a different host port:"
      echo "  cp .env.example .env"
      echo "  # edit .env: LAB_POSTGRES_PORT=5433"
      echo "  # when running Java on the host: export DB_PORT=5433"
    fi
    return 1
  fi

  return 0
}

failed=0
check_port "$LAB_POSTGRES_PORT" "lab Postgres" || failed=1
check_port 6379 "Redis" || failed=1
check_port 9092 "Kafka" || failed=1
check_port 8090 "WireMock" || failed=1
check_port 8099 "scenario-control" || failed=1
check_port 9000 "MinIO API" || failed=1
check_port 9001 "MinIO console" || failed=1

if [[ "$failed" -ne 0 ]]; then
  echo ""
  echo "Fix the port conflict(s) above, then run: make bootstrap"
  exit 1
fi

# Warn when disk is tight (Docker needs headroom for images and volumes).
if command -v df >/dev/null 2>&1; then
  avail_kb="$(df -k /System/Volumes/Data 2>/dev/null | awk 'NR==2 {print $4}' || df -k . | awk 'NR==2 {print $4}')"
  if [[ -n "${avail_kb:-}" && "$avail_kb" -lt 2097152 ]]; then
    echo "Warning: less than 2 GB free disk space. Docker may fail to start containers."
    echo "Free space, then retry if you see read-only filesystem or pull errors."
  fi
fi

echo "Preflight OK."

# Catch corrupted image layers (common after disk-full / read-only Docker errors).
verify_image() {
  local image="$1"
  local probe="$2"
  if docker run --rm "$image" $probe >/dev/null 2>&1; then
    return 0
  fi
  echo ""
  echo "Docker image $image will not start (often a corrupt local layer after disk-full)."
  echo "Attempting repair: docker rmi $image && docker pull $image"
  docker rmi "$image" >/dev/null 2>&1 || true
  if docker pull "$image" >/dev/null 2>&1 && docker run --rm "$image" $probe >/dev/null 2>&1; then
    echo "Repaired $image."
    return 0
  fi
  echo "Repair failed. Try Docker Desktop -> Troubleshoot -> Clean / Purge data,"
  echo "then run make bootstrap again."
  exit 1
}

echo "Checking core images..."
verify_image postgres:16-alpine "pg_isready --version"
verify_image redis:7 "redis-server --version"
echo "Images OK."
