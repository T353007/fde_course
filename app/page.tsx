import Link from "next/link";
import { getAllPhases, getCourseStats, formatDuration } from "@/lib/content";

export default function HomePage() {
  const phases = getAllPhases();
  const stats = getCourseStats();
  const hours = Math.round(stats.minutes / 60);

  return (
    <>
      {/* ---------------------------------------------------------------- hero */}
      <section className="relative overflow-hidden border-b border-[var(--color-line)]">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:py-28">
          <div className="fade-up">
            <span className="tag border-[var(--color-teal-dim)] text-[var(--color-teal)]">
              Halyard AI · Field training
            </span>

            <h1 className="mt-6 max-w-3xl font-[family-name:var(--font-display)] text-4xl leading-[1.08] tracking-tight text-white sm:text-6xl">
              The Forward Deployed
              <br />
              Engineer Field Manual
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-[var(--color-fg-dim)]">
              You are a Forward Deployed Engineer at Halyard AI. You are dropped into a
              lender with an 11 year old Java codebase, four vendors that lie, an
              underwriter who keeps the real business rules in a spreadsheet, and a CEO
              who wants AI. Nobody agrees on what the system does. Your job starts
              anyway.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link
                href="/missions/what-the-job-actually-is"
                className="rounded-lg bg-[var(--color-teal)] px-5 py-2.5 text-[14px] font-semibold text-[#06231e] transition-transform hover:-translate-y-px hover:bg-[#4fdcc0]"
              >
                Start Mission 01
              </Link>
              <Link
                href="/missions"
                className="rounded-lg border border-[var(--color-line-2)] px-5 py-2.5 text-[14px] font-medium text-[var(--color-fg-dim)] transition-colors hover:border-[var(--color-fg-mute)] hover:text-[var(--color-fg)]"
              >
                See all {stats.missions} missions
              </Link>
            </div>
          </div>

          {/* the request that starts everything */}
          <figure className="fade-up mt-16 max-w-2xl rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
            <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
              Email · Day 1 · 7:42 AM
            </div>
            <blockquote className="mt-4 font-[family-name:var(--font-display)] text-xl leading-relaxed text-[#e9eef5]">
              &ldquo;We want an AI underwriter. Our process takes too long. I want
              processing time down 70 percent by Q3.&rdquo;
            </blockquote>
            <figcaption className="mt-4 text-[13px] text-[var(--color-fg-mute)]">
              Dale Whitmore, CEO, Northstar Capital
            </figcaption>
            <div className="mt-5 border-t border-dashed border-[var(--color-line-2)] pt-4 text-[13px] leading-relaxed text-[var(--color-fg-dim)]">
              He is wrong about the solution and right about the problem. You have to
              prove which is which before you write much code.
            </div>
          </figure>
        </div>
      </section>

      {/* --------------------------------------------------------------- stats */}
      <section className="border-b border-[var(--color-line)]">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px bg-[var(--color-line)] sm:grid-cols-4">
          {[
            { n: String(stats.missions), l: "Missions" },
            { n: String(stats.phases), l: "Engagement phases" },
            { n: `${hours}h`, l: "Guided lab time" },
            { n: "3", l: "Customers" },
          ].map((s) => (
            <div key={s.l} className="bg-[var(--color-ink)] px-5 py-8">
              <div className="font-[family-name:var(--font-display)] text-3xl text-white">
                {s.n}
              </div>
              <div className="mt-1 font-mono text-[11px] uppercase tracking-wider text-[var(--color-fg-mute)]">
                {s.l}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------ what is different */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="font-[family-name:var(--font-display)] text-3xl text-white">
          What you are walking into
        </h2>
        <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-[var(--color-fg-dim)]">
          A customer, a codebase full of real mistakes, and a deadline. The easy
          answer is usually incomplete.
        </p>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {[
            {
              t: "The first answer is usually wrong",
              d: "The obvious hypothesis is incomplete. You investigate, you find the real cause, and it is rarely the thing anyone in the meeting named.",
            },
            {
              t: "The lab actually runs",
              d: "Java 21 services, Postgres, Kafka, Redis, and four vendors that fail in specific ways. You curl an endpoint, get a wrong number, and go find out why.",
            },
            {
              t: "No API keys needed",
              d: "The model layer ships with a deterministic simulator built from recorded output. Swap one variable to run a local Qwen model or a hosted one instead.",
            },
            {
              t: "AI is often the wrong tool",
              d: "Sometimes the right move is plain code and deleting the model call. Knowing when not to reach for AI is part of the job.",
            },
            {
              t: "You practice the conversation",
              d: "Telling a CEO his target is unreachable is a skill. So is a security review and an incident update. Those conversations are the work.",
            },
            {
              t: "Two more customers at the end",
              d: "Once Northstar works, a bank with a completely different workflow arrives. Then a cold engagement with no hints and no stated right answer.",
            },
          ].map((c) => (
            <div
              key={c.t}
              className="rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-5 transition-colors hover:border-[var(--color-line-2)]"
            >
              <h3 className="text-[15px] font-semibold text-white">{c.t}</h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-[var(--color-fg-dim)]">
                {c.d}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* -------------------------------------------------------------- phases */}
      <section className="mx-auto max-w-6xl px-5 pb-20">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-[family-name:var(--font-display)] text-3xl text-white">
            The engagement
          </h2>
          <Link
            href="/missions"
            className="text-[13px] text-[var(--color-teal)] hover:underline"
          >
            All missions
          </Link>
        </div>

        <div className="mt-8 space-y-px overflow-hidden rounded-xl border border-[var(--color-line)] bg-[var(--color-line)]">
          {phases.map((p) => (
            <Link
              key={p.slug}
              href={`/phases/${p.slug}`}
              className="group flex flex-col gap-3 bg-[var(--color-ink-2)] px-5 py-5 transition-colors hover:bg-[var(--color-panel)] sm:flex-row sm:items-center sm:gap-6"
            >
              <div className="flex w-24 shrink-0 items-center gap-3">
                <span className="font-mono text-[11px] text-[var(--color-fg-mute)]">
                  PHASE {String(p.number).padStart(2, "0")}
                </span>
              </div>

              <div className="min-w-0 flex-1">
                <div className="text-[15px] font-semibold text-white group-hover:text-[var(--color-teal)]">
                  {p.title}
                </div>
                <div className="mt-0.5 truncate text-[13px] text-[var(--color-fg-mute)]">
                  {p.subtitle}
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-4 font-mono text-[11px] text-[var(--color-fg-mute)]">
                <span>{p.missions.length} missions</span>
                <span>
                  {formatDuration(
                    p.missions.reduce((s, m) => s + m.duration, 0)
                  )}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------------- closing */}
      <section className="border-t border-[var(--color-line)] bg-[var(--color-ink-2)]">
        <div className="mx-auto max-w-3xl px-5 py-20 text-center">
          <h2 className="font-[family-name:var(--font-display)] text-3xl leading-snug text-white">
            You finish when you can do this cold
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-[var(--color-fg-dim)]">
            The last engagement hands you a new lender, a folder of messy artifacts, and
            no guidance. No hints, no stated answer, no one to tell you where the real
            problem is. That is also just Tuesday.
          </p>
          <Link
            href="/capstone"
            className="mt-8 inline-block rounded-lg border border-[var(--color-line-2)] px-5 py-2.5 text-[14px] text-[var(--color-fg-dim)] transition-colors hover:border-[var(--color-teal-dim)] hover:text-[var(--color-teal)]"
          >
            Look at the capstone
          </Link>
        </div>
      </section>
    </>
  );
}
