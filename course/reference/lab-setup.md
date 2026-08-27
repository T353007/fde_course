---
slug: lab-setup
title: Setting Up the Lab
subtitle: Bring Northstar's system up on your laptop. Budget an hour the first time, and expect one thing to go wrong.
kind: setup
order: 1
---

You need this running before Mission 02. Nothing in Phase 0 or Phase 1 requires the
full stack, so if something fails today you can keep going and fix it later.

## What you need installed

| Tool | Version | Why |
|---|---|---|
| Docker | 24 or newer, with Compose v2 | Postgres, Kafka, Redis, MinIO, the vendor stubs |
| Java | 21 | The four Northstar services |
| Maven | 3.9 or newer | Building them |
| Python | 3.12 or newer | The AI service and the eval library |
| Ollama | latest | Only from Mission 17, and optional even then |

Check all of it at once:

```bash
docker --version && java -version && mvn -v && python3 --version
```

## Memory

The full stack wants about 8 GB of free RAM. If you have less, use a smaller profile.

```bash
make up PROFILE=core     # postgres, redis, ai-service, underwriting only
```

`PROFILE=core` covers every mission through Phase 3. You need the full stack starting
in Phase 4, when documents and Kafka enter the story.

## First run

Mission 02 needs seed data. Use **`make bootstrap`** (not `make up` alone).

```bash
cd lab
make bootstrap
```

That starts Docker, runs migrations, and loads 1,200 applications. Then build and run
the Java services you curl in Mission 02:

```bash
make apps-build
# terminal 2
make run-application
# terminal 3
make run-underwriting
```

Or step by step:

```bash
make up
make seed
```

`make up` starts the containers, waits for health checks, and runs the database
migrations. `make seed` loads 1,200 applications. Seed needs Postgres running, so
`make up` has to succeed first. If you want both in one command: `make bootstrap`.

The seed is deterministic. Everyone gets the same 1,200 applications, the same
duplicate bakery, and the same bank statements. When a mission tells you an
application ID, that ID is real on your machine.

## Did it work

Three checks. Run all three.

```bash
# 1. the services answer
curl -s localhost:8081/actuator/health
curl -s localhost:8083/actuator/health
curl -s localhost:8000/v1/health

# 2. the data is there
docker compose exec postgres psql -U northstar -d northstar \
  -c "select count(*) from northstar.applications;"

# 3. the model layer works with no API key
curl -s localhost:8000/v1/models
```

The third one should list the `stub` provider as available. That is the offline model
simulator, and it is the default. You do not need an API key for this course.

## The model providers

The AI service talks to one of four providers. You pick with an environment variable.

```bash
LLM_PROVIDER=stub        # default. offline, free, deterministic
LLM_PROVIDER=ollama      # a model running on your own machine
LLM_PROVIDER=openai      # hosted, needs OPENAI_API_KEY
LLM_PROVIDER=anthropic   # hosted, needs ANTHROPIC_API_KEY
```

**Start with `stub` and stay there until Mission 17.**

The stub is not a mock that returns "hello world." It replays real recorded model
output, including the mistakes. When a mission needs the model to return
`"$78,231 approximately"` instead of a number, the stub returns exactly that, on every
machine, every time. That is what makes the incident in Mission 32 reproducible instead
of a story you read.

## Local models, from Mission 17

Mission 17 has you run a model on your own hardware, because Northstar's compliance
officer does not want bank account data leaving the building. That is a real reason,
and it is a real constraint you will meet in this industry.

```bash
ollama pull qwen3:8b
ollama pull qwen3:1.7b     # smaller, used for routing experiments in Mission 35
make ollama-check
```

`make ollama-check` tells you whether the daemon is up, which models you have, how much
memory is free, and roughly what latency to expect.

Rough guidance:

| Your RAM | What to run |
|---|---|
| 32 GB or more | `qwen3:8b`, comfortable |
| 16 GB | `qwen3:8b`, close the browser tabs |
| 8 GB | `qwen3:1.7b` only, and expect worse quality on hard cases |
| Less than 8 GB | Stay on `stub`. You will still get the lesson. |

Every mission that uses a local model also passes with `LLM_PROVIDER=stub`. If your
machine cannot run one, you are not locked out of anything.

## Breaking things on purpose

Several missions ask you to make a vendor fail. That is what the scenario system is
for.

```bash
make inject SCENARIO=ledgerlink-empty-200
make clear-scenarios
```

The scenarios are documented where the missions need them. Do not go read the whole
list now. Finding out how a vendor fails is part of the work.

## When it goes wrong

Run checks first:

```bash
cd lab
make doctor
```

**Port already in use.** Something else is on 5432 or 9092. Copy `lab/.env.example` to
`lab/.env` and set `LAB_POSTGRES_PORT=5433` if local Postgres is running. Export
`DB_PORT=5433` when you start Java services on the host.

**Docker image will not start / exec format error.** Your disk was probably full earlier
and Docker image layers got corrupted. Re-pull the broken image:

```bash
docker rmi postgres:16-alpine
docker pull postgres:16-alpine
make bootstrap
```

If several images fail, use Docker Desktop -> Troubleshoot -> Clean / Purge data, then
`make bootstrap` again.

**Kafka will not become healthy.** Usually a stale volume from an earlier run.

```bash
make reset
```

That wipes the volumes and reseeds. It takes a few minutes and it fixes most problems.

**Migrations fail partway.** Also `make reset`. Do not hand-patch the schema. The
schema is course content, and a mission later depends on the migrations being in
exactly the order they ship in.

**Services start then die.** Check memory first.

```bash
make logs S=underwriting-service
```

**The AI service returns a `FixtureMissing` error.** That is deliberate. The stub
provider refuses to invent output when it has no recorded response for your input. It
fails loudly instead of quietly returning something wrong. Check that you are sending
the input the mission asked for.

## A word about what you are looking at

The Northstar codebase has real problems in it. Not typos and not made up difficulty.
Actual patterns that show up in production systems that have been alive for a decade:
a shared function with three callers that want different answers, a feature flag from
2021 that still controls live behavior, retry logic that cannot tell one kind of
failure from another, documentation describing what an endpoint was supposed to do.

You are going to find some of these on your own. Some you will walk past three times.
A few of the things that look broken are fine, and a few of the things that look fine
are not.

Do not go looking for a list. There is one, and reading it early costs you the entire
point of Phase 2.
