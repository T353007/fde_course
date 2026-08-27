#!/usr/bin/env bash
# Create Kafka topics used by the Northstar lab.
# Safe to re-run. Kafka must already be accepting connections.
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP:-localhost:9092}"

topics=(
  application.submitted
  document.uploaded
  document.extracted
  underwriting.decisioned
  ai.extraction.requested
)

echo "Creating Kafka topics on $BOOTSTRAP"
for topic in "${topics[@]}"; do
  kafka-topics.sh --bootstrap-server "$BOOTSTRAP" \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions 3 \
    --replication-factor 1 \
    || true
done

echo "Topics:"
kafka-topics.sh --bootstrap-server "$BOOTSTRAP" --list
