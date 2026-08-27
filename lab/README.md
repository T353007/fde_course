# Lab README

Bring Northstar up on your laptop. Budget about an hour the first time.

## What you get

| Port | Service |
|---|---|
| 5432 | PostgreSQL 16 (Alpine) |
| 6379 | Redis 7 |
| 9092 | Kafka (KRaft) |
| 9000 / 9001 | MinIO API / console |
| 8090 | Vendor stubs (WireMock) |
| 8099 | Scenario control API |

Java services and ai-service sit behind compose profiles. Default `make up`
starts infrastructure only, so you can seed data before the apps are wired.

## Prerequisites

- Docker with Compose v2
- Python 3.12+ (for seed checks and later ai-service)
- Java 21 and Maven when you run the Northstar services
- Ollama only from Mission 17, and optional even then

## First run

```bash
cd lab
cp .env.example .env    # only if you need non-default ports
make doctor             # optional: check Docker and ports
make bootstrap          # up + seed
make apps-build         # build Java services (Mission 02+)
```

In two more terminals:

```bash
make run-application    # :8081
make run-underwriting   # :8083
```

Then confirm Mission 02 endpoints:

```bash
make smoke
```

For a full clean-slate check (wipes lab volumes, re-bootstrap, builds, curls):

```bash
make verify-first-run
```

Or step by step:

```bash
make up
make seed
```

`make up` starts containers, waits for Postgres, and runs Flyway migrations
V1 through V14. `make seed` loads 1,200 applications from CSV. Seed will refuse
to run if Postgres is not up, and tell you to run `make up` first.

Check the row count:

```bash
docker compose exec postgres psql -U northstar -d northstar \
  -c "select count(*) from northstar.applications;"
```

You want `1200`.

## Profiles

```bash
make up                     # infra only
make up PROFILE=core        # + ai-service and underwriting placeholders
make up PROFILE=full        # + every app service placeholder
make up PROFILE=nolocal     # same as full; Ollama stays on the host
```

`PROFILE=core` is enough through Phase 3. Documents and Kafka matter starting
in Phase 4, so use `full` then.

## Useful targets

```bash
make bootstrap              # first run: up + seed
make apps-build             # build Java services (Mission 02+)
make run-application        # :8081 in a second terminal
make run-underwriting       # :8083 in a third terminal
make smoke                  # verify seed counts + Mission 02 HTTP endpoints
make verify-first-run       # wipe volumes, bootstrap, build, smoke (CI-style)
make logs S=postgres
make inject SCENARIO=ledgerlink-empty-200
make clear-scenarios
make eval SUITE=txn-classification
make ollama-check
make test
make down
make reset                  # wipe volumes, up, seed
```

## Vendor failure injection

Vendors live behind WireMock on 8090. Scenario control on 8099 swaps stubs.

```bash
make inject SCENARIO=ledgerlink-empty-200
curl -s http://localhost:8090/ledgerlink/v1/connections/demo/accounts
make clear-scenarios
```

Scenarios:

- `ledgerlink-empty-200`
- `optiscan-degraded`
- `corveil-ratelimit`
- `sentinel-no-reason-codes`
- `loancore-batch-window`
- `corveil-slow`

## Seed data

CSVs live in `infra/postgres/seed/data/`. Regenerate with:

```bash
python3 infra/postgres/seed/seed_generator.py --check
```

`--check` fails if the canon discovery numbers drift.

## Troubleshooting

**Run checks first.**

```bash
make doctor
```

**Port already in use.** Another app is using a lab port (often 5432 for Postgres).
Stop it, or copy `.env.example` to `.env` and set `LAB_POSTGRES_PORT=5433`. When you
run Java services on the host, also set `export DB_PORT=5433`.

**WireMock exits on start.** Rebuild the vendor image and retry:

```bash
docker compose build --no-cache wiremock
make bootstrap
```

**Docker read-only filesystem or pull errors.** Your disk is probably full. Free several
GB, restart Docker Desktop, then run `make doctor` again.

**Flyway failed.** `make migrate` falls back to applying `V*.sql` with `psql`
in order. Re-run `make migrate`, then `make seed`.

**Seed says not 1200.** Run `make migrate` first. Tables must exist before
COPY. Then `make seed` again. It truncates and reloads.

**Kafka unhealthy.** Give it 30 seconds on first boot. `make up` already waits
on Postgres; Kafka init retries create topics once the broker is ready.

**Scenario control 404.** Start infra with `make up` so WireMock and
scenario-control are both running. Then inject again.

**Low RAM.** Use `make up PROFILE=core`. Keep Ollama off until Mission 17.

## Layout

```
lab/
  Makefile
  docker-compose.yml
  DEFECT_REGISTRY.md          spoiler. leave it closed until Phase 9
  infra/postgres/migrations/  Flyway V1..V14
  infra/postgres/seed/        generator + CSVs + load_seed.sh
  infra/vendors/              WireMock stubs + scenario-control
  infra/kafka/                topic helper
  infra/minio/                bucket helper
```

## Do not open yet

`DEFECT_REGISTRY.md` lists planted defects. Missions tell you when that file is
fair game. Until Phase 9, treat it as a spoiler.
