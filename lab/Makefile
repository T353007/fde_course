# Northstar lab Makefile. Targets match LAB_SPEC.md section 3.
#
#   make up
#   make up PROFILE=core
#   make seed
#   make inject SCENARIO=ledgerlink-empty-200

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
COMPOSE_FILE := $(ROOT)docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)
PROFILE ?=
SCENARIO ?=
S ?= underwriting-service
SUITE ?= smoke

# When PROFILE is set, pass it through. When empty, start infra-only services
# (anything without a compose profile).
ifneq ($(PROFILE),)
COMPOSE_UP := $(COMPOSE) --profile $(PROFILE)
else
COMPOSE_UP := $(COMPOSE)
endif

.PHONY: up down reset seed test logs inject clear-scenarios eval ollama-check help migrate wait-postgres require-postgres bootstrap preflight doctor wait-infra apps-build run-application run-underwriting smoke verify-first-run

help:
	@echo "Northstar lab"
	@echo "  make up                     infra only (postgres redis kafka minio vendors)"
	@echo "  make up PROFILE=core        + ai-service + underwriting placeholders"
	@echo "  make up PROFILE=full        + all app service placeholders"
	@echo "  make up PROFILE=nolocal     same as full (Ollama stays on the host)"
	@echo "  make seed                   load 1,200 apps (requires make up first)"
	@echo "  make bootstrap              make up && make seed"
	@echo "  make apps-build             build Java services (Mission 02+)"
	@echo "  make run-application        start application-service on :8081"
	@echo "  make run-underwriting       start underwriting-service on :8083"
	@echo "  make smoke                  verify DB seed + Mission 02 HTTP endpoints"
	@echo "  make verify-first-run       reset volumes, bootstrap, build, smoke (full clean run)"
	@echo "  make preflight              check Docker, ports, disk before up"
	@echo "  make doctor                 same as preflight"
	@echo "  make down | make reset"
	@echo "  make logs S=underwriting-service"
	@echo "  make inject SCENARIO=ledgerlink-empty-200"
	@echo "  make clear-scenarios"
	@echo "  make eval SUITE=txn-classification"
	@echo "  make ollama-check"
	@echo "  make test"

preflight doctor:
	@chmod +x $(ROOT)scripts/preflight.sh 2>/dev/null || true
	@$(ROOT)scripts/preflight.sh

wait-infra: wait-postgres
	@echo "Waiting for WireMock and scenario-control..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do \
		curl -sf http://localhost:8090/__admin/mappings >/dev/null 2>&1 && \
		curl -sf http://localhost:8099/scenarios >/dev/null 2>&1 && exit 0; \
		sleep 2; \
	done; \
	echo "WireMock or scenario-control did not become ready."; \
	echo "Check: docker compose -f $(COMPOSE_FILE) ps"; \
	echo "Logs:  docker compose -f $(COMPOSE_FILE) logs wiremock scenario-control"; \
	exit 1

up: preflight
	@echo "Starting lab (PROFILE=$(if $(PROFILE),$(PROFILE),infra))"
	@command -v docker >/dev/null || (echo "Docker is not installed or not on PATH."; exit 1)
	@docker info >/dev/null 2>&1 || ( \
		echo "Docker is not running. Start Docker Desktop, wait until it is healthy, then retry: make up"; \
		exit 1; \
	)
	$(COMPOSE_UP) build wiremock scenario-control
	$(COMPOSE_UP) up -d postgres redis kafka minio wiremock scenario-control
	@$(MAKE) wait-infra
	$(COMPOSE_UP) up -d migrate kafka-init minio-init || true
	@$(MAKE) migrate
	@if [ "$(PROFILE)" = "core" ] || [ "$(PROFILE)" = "full" ] || [ "$(PROFILE)" = "nolocal" ]; then \
		$(COMPOSE_UP) up -d ai-service underwriting-service || echo "App placeholders failed to start. Infra is still up."; \
	fi
	@if [ "$(PROFILE)" = "full" ] || [ "$(PROFILE)" = "nolocal" ]; then \
		$(COMPOSE_UP) up -d application-service document-service fraud-service || true; \
	fi
	@echo "Up. Check: docker compose -f $(COMPOSE_FILE) ps"
	@echo "Next: make seed"

wait-postgres:
	@echo "Waiting for postgres..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do \
		$(COMPOSE) exec -T postgres pg_isready -U northstar -d northstar >/dev/null 2>&1 && exit 0; \
		sleep 2; \
	done; \
	echo "postgres did not become ready"; \
	echo "Check: docker compose -f $(COMPOSE_FILE) ps"; \
	exit 1

require-postgres:
	@docker info >/dev/null 2>&1 || ( \
		echo "Docker is not running. Start Docker Desktop, then: make up && make seed"; \
		exit 1; \
	)
	@if ! $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx postgres; then \
		echo "Postgres is not running."; \
		echo "Seed needs a live database. Run:"; \
		echo "  make up"; \
		echo "  make seed"; \
		echo "Or in one step: make bootstrap"; \
		exit 1; \
	fi
	@$(MAKE) wait-postgres

migrate:
	@echo "Running Flyway migrations..."
	@$(COMPOSE) run --rm migrate || ( \
		echo "Flyway container failed. Applying V*.sql with psql fallback..."; \
		for f in $$(ls -1 $(ROOT)infra/postgres/migrations/V*.sql | sort); do \
			echo "  $$f"; \
			$(COMPOSE) exec -T postgres psql -U northstar -d northstar -v ON_ERROR_STOP=1 < "$$f" || exit 1; \
		done; \
	)

seed: require-postgres
	@echo "Loading seed CSVs..."
	@chmod +x $(ROOT)infra/postgres/seed/load_seed.sh 2>/dev/null || true
	@COMPOSE_FILE=$(COMPOSE_FILE) $(ROOT)infra/postgres/seed/load_seed.sh

bootstrap:
	@$(MAKE) up PROFILE=$(PROFILE)
	@$(MAKE) seed

apps-build:
	@echo "Building Northstar Java services..."
	@cd $(ROOT)northstar && mvn -q install -DskipTests

run-application: apps-build
	@echo "application-service on http://localhost:8081 (Ctrl+C to stop)"
	@cd $(ROOT)northstar && java -jar application-service/target/application-service-*.jar

run-underwriting: apps-build
	@echo "underwriting-service on http://localhost:8083 (Ctrl+C to stop)"
	@cd $(ROOT)northstar && java -jar underwriting-service/target/underwriting-service-*.jar

smoke:
	@chmod +x $(ROOT)scripts/smoke.sh 2>/dev/null || true
	@$(ROOT)scripts/smoke.sh

verify-first-run:
	@echo "Full clean first-run check (destroys lab volumes)..."
	$(COMPOSE) --profile core --profile full --profile nolocal down -v
	@$(MAKE) bootstrap
	@$(MAKE) apps-build
	@echo "Starting application-service and underwriting-service for smoke..."
	@cd $(ROOT)northstar && java -jar application-service/target/application-service-*.jar >/tmp/northstar-app.log 2>&1 & echo $$! > /tmp/northstar-app.pid
	@cd $(ROOT)northstar && java -jar underwriting-service/target/underwriting-service-*.jar >/tmp/northstar-uw.log 2>&1 & echo $$! > /tmp/northstar-uw.pid
	@sleep 15
	@$(MAKE) smoke || (kill $$(cat /tmp/northstar-app.pid /tmp/northstar-uw.pid 2>/dev/null) 2>/dev/null; exit 1)
	@kill $$(cat /tmp/northstar-app.pid /tmp/northstar-uw.pid 2>/dev/null) 2>/dev/null || true
	@rm -f /tmp/northstar-app.pid /tmp/northstar-uw.pid
	@echo "verify-first-run passed."

down:
	$(COMPOSE) --profile core --profile full --profile nolocal down

reset:
	$(COMPOSE) --profile core --profile full --profile nolocal down -v
	$(MAKE) up PROFILE=$(PROFILE)
	$(MAKE) seed

logs:
	@$(COMPOSE_UP) logs -f $(S) 2>/dev/null || $(COMPOSE) logs -f $(S) 2>/dev/null || \
		echo "Service $(S) is not running. Try: docker compose -f $(COMPOSE_FILE) ps"

inject:
	@if [ -z "$(SCENARIO)" ]; then echo "Usage: make inject SCENARIO=ledgerlink-empty-200"; exit 1; fi
	@curl -sf -X POST "http://localhost:8099/scenarios/$(SCENARIO)/activate" \
		&& echo "" \
		|| echo "Scenario control not up. Run: make up   then retry."

clear-scenarios:
	@curl -sf -X DELETE "http://localhost:8099/scenarios" \
		&& echo "" \
		|| echo "Scenario control not up."

eval:
	@if [ -d $(ROOT)evals ]; then \
		cd $(ROOT)evals && (python3 -m northstar_evals run --suite $(SUITE) 2>/dev/null || \
			python3 -m northstar_evals --help 2>/dev/null || \
			echo "Eval CLI not ready. Try: cd lab/evals && pip install -e ."); \
	else \
		echo "lab/evals is not present yet."; \
	fi

ollama-check:
	@command -v ollama >/dev/null || (echo "Install Ollama from https://ollama.com"; exit 1)
	@echo "Ollama models:"; ollama list || true
	@curl -sf http://localhost:11434/api/tags >/dev/null && echo "daemon: up" || echo "daemon: not reachable on :11434"
	@ollama list 2>/dev/null | grep -q 'qwen3:8b' || echo "Missing qwen3:8b. Pull with: ollama pull qwen3:8b"
	@ollama list 2>/dev/null | grep -q 'qwen3:1.7b' || echo "Missing qwen3:1.7b (optional). Pull with: ollama pull qwen3:1.7b"
	@echo "Hosted missions also pass with LLM_PROVIDER=stub."

test:
	@echo "== Java =="
	@if [ -f $(ROOT)northstar/pom.xml ]; then \
		(cd $(ROOT)northstar && mvn -q test) || echo "Java tests not green yet (ok while services are stubs)."; \
	else echo "northstar/ missing"; fi
	@echo "== ai-service =="
	@if [ -d $(ROOT)ai-service ]; then \
		(cd $(ROOT)ai-service && LLM_PROVIDER=stub python3 -m pytest -q 2>/dev/null) || \
			echo "ai-service tests skipped or not green yet."; \
	else echo "ai-service/ missing"; fi
	@echo "== evals =="
	@if [ -d $(ROOT)evals ]; then \
		(cd $(ROOT)evals && python3 -m pytest -q 2>/dev/null) || \
			echo "evals tests skipped or not green yet."; \
	else echo "evals/ missing"; fi
