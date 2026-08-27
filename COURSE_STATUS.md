# COURSE_STATUS.md

Last updated: after resume session

## Snapshot

| Area | State |
|---|---|
| Site (Next.js) | builds clean, Vercel-ready |
| Style guide + canon + architecture | done |
| Missions | **40/40** present |
| Content validator | `npm run course:validate` |
| Certification | 6 exams + Meridian capstone brief |
| Lab compose + Makefile + README | done |
| DEFECT_REGISTRY | 41 entries (spoiler) |
| Postgres migrations V1-V14 | done |
| Seed CSVs (1,200 apps) | done |
| ai-service + stub fixtures | runnable offline |
| Eval golden datasets | verified: 96/68/61/73.3/99.1 at 84% volume; evals pytest 13 passed |
| Java services | partial (underwriting/document/common strong; fraud thin) |
| Reviewer portal | not started |
| Meridian package | skeleton + key discovery files |

## How to run the site

```bash
npm install
npm run dev
# http://localhost:3000
```

Deploy: push to GitHub/Git and import in Vercel. Root Next.js app, no special config.

## How to run the lab

```bash
cd lab
make up PROFILE=core
make seed
cd ai-service && LLM_PROVIDER=stub uvicorn ai_service.main:app --port 8000
```

## Still rough (honest)

1. Full `make test` end-to-end not proven green on a clean machine this session
2. Reviewer portal UI for M29 is described in the mission more than implemented
3. Meridian capstone package needs more artifacts under each folder
4. Some missions are denser than others. Spot-check M23/M24 (just finished) and any mission that feels thin
5. Java `application-service` and `fraud-service` need another pass before Mission 02 curl tour matches every URL

## Definition of done for v1 publish

- [x] 40 missions validating
- [x] Site builds
- [x] Lab boots with stub LLM offline
- [ ] `make test` green
- [ ] Meridian package fleshed out
- [ ] Spot editorial pass for style on late missions
- [ ] Vercel preview URL shared
