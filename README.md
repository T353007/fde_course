# The Forward Deployed Engineer Field Manual

A hands-on course that trains an engineer to walk into a messy fintech company and
ship AI into production without breaking anything important.

It is not a set of tutorials. It is one long customer engagement. You get a lender
with an 11 year old Java codebase, four vendors that fail in quiet ways, an
underwriter who keeps the real business rules in a spreadsheet, and a CEO who read a
competitor's press release and now wants an AI underwriter.

Forty missions, a lab that runs on your laptop, six practical exams, and a capstone
with a new customer and no hints.

---

## What makes it different

**The first answer is usually wrong.** Missions are built so the obvious hypothesis is
incomplete. The CEO's request cannot produce the outcome he wants, and it takes six
missions of measurement to prove it. That is on purpose.

**The lab actually runs.** Java 21 services, Postgres, Kafka, Redis, MinIO, and
simulated vendors that fail in specific documented ways. You curl an endpoint, get a
wrong number, and go find out why.

**No API keys required.** The model layer ships with a deterministic simulator built
from recorded output. Set one environment variable to run a local Qwen model through
Ollama instead, or a hosted model if you have a key. Every mission works offline.

**AI is often the wrong tool.** Several missions are solved correctly by writing plain
code and deleting the model call. Knowing when not to reach for a model is graded.

---

## Repository layout

```
.
├── app/                  Next.js site (the course reader)
├── components/           UI components
├── lib/                  markdown pipeline and content loading
├── course/               ALL COURSE PROSE. Markdown is the source of truth.
│   ├── missions/         m01 through m40
│   ├── phases/           the ten phase introductions
│   ├── certification/    exams, rubrics, capstone
│   └── reference/        cast, systems, concept primers, templates
├── lab/                  the runnable Northstar system
│   ├── LAB_SPEC.md       the contract everything else is built against
│   ├── northstar/        Java 21, Spring Boot, four services
│   ├── ai-service/       Python, FastAPI, the model layer
│   ├── evals/            the evaluation library
│   ├── infra/            compose, migrations, seed data, vendor stubs
│   └── data/             bank statements, policies, golden datasets
├── customers/            engagement artifacts you produce and consume
├── solutions/            reference solutions, do not read ahead
├── CANON.md              story bible, the facts that cannot change
├── STYLE_GUIDE.md        writing rules
└── COURSE_STATUS.md      what is built and what is not
```

---

## Running the site

```bash
npm install
npm run dev
```

Open http://localhost:3000.

The site reads Markdown from `course/` at build time. Editing a mission and refreshing
is the whole workflow. There is no database and no CMS.

To deploy, push to a Git remote and import the repo into Vercel. It is a root level
Next.js app, so no configuration is needed.

---

## Running the lab

You need Docker, Java 21, Maven, and Python 3.12 or newer.

```bash
cd lab
make up          # start postgres, redis, kafka, minio, vendor stubs, services
make seed        # load 1,200 applications with realistic dirt in them
make test        # java tests, python tests, eval smoke suite
```

If your laptop is tight on memory, run a smaller profile:

```bash
make up PROFILE=core
```

For the local model missions:

```bash
ollama pull qwen3:8b
make ollama-check
```

You do not need Ollama before Mission 17, and every mission that uses it also works
with the offline stub provider.

Full setup notes and troubleshooting are in `lab/README.md`.

---

## Who this is for

You should be comfortable writing backend code. Java and Python examples assume you can
read both without a tutorial. You do not need any experience with LLMs, RAG, evals, or
agents. Those are taught inside the project as they become necessary.

You should expect to spend 10 to 15 hours a week for 16 to 24 weeks if you do the work
properly. Reading it all in a weekend teaches you almost nothing, because the missions
are built around decisions you have to actually make.

---

## Contributing

Read three files before writing anything:

1. `STYLE_GUIDE.md`. Eighth grade reading level, no em dashes, no AI sounding phrases.
   This is enforced, not suggested.
2. `CANON.md`. The characters, the systems, and the numbers. If your content
   contradicts canon, your content is wrong.
3. `course/reference/MISSION_TEMPLATE.md`. The structure a mission has to follow and
   the quality bar it has to clear.

`course/missions/m01-what-the-job-actually-is.md` is the reference for voice and depth.
Match it.

Before you open a pull request:

```bash
npm run build          # must pass
npm run course:validate # frontmatter and canon checks
```

---

## A note on the fiction

Northstar Capital, Redwood Bank, Meridian Financial, every person named in this course,
and every vendor are invented. No real company or person is being described.

The failures are not invented. Every planted defect in the lab is a pattern that shows
up in real production systems, usually for the reason given in the defect registry.
