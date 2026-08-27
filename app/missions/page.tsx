import Link from "next/link";
import type { Metadata } from "next";
import { getAllPhases, formatDuration, type MissionMeta } from "@/lib/content";

export const metadata: Metadata = {
  title: "All missions",
  description:
    "Forty missions across ten phases of a single fintech engagement, from the first bad requirement to the incident review.",
};

function Difficulty({ level }: { level: number }) {
  return (
    <span className="inline-flex gap-[3px]" title={`Difficulty ${level} of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`h-[3px] w-[7px] rounded-sm ${
            i <= level ? "bg-[var(--color-amber)]" : "bg-[var(--color-line-2)]"
          }`}
        />
      ))}
    </span>
  );
}

function MissionRow({ m }: { m: MissionMeta }) {
  const stub = m.status === "stub";
  return (
    <Link
      href={`/missions/${m.slug}`}
      className="group grid grid-cols-[3rem_1fr] items-start gap-4 bg-[var(--color-ink-2)] px-5 py-4 transition-colors hover:bg-[var(--color-panel)] sm:grid-cols-[3.5rem_1fr_auto]"
    >
      <span className="pt-0.5 font-mono text-[12px] text-[var(--color-fg-mute)]">
        {m.id}
      </span>

      <span className="min-w-0">
        <span className="flex flex-wrap items-center gap-2">
          <span className="text-[15px] font-medium text-[var(--color-fg)] group-hover:text-[var(--color-teal)]">
            {m.title}
          </span>
          {m.lab && (
            <span className="tag border-[var(--color-teal-dim)] text-[var(--color-teal)]">
              lab
            </span>
          )}
          {stub && <span className="tag">planned</span>}
        </span>
        {m.subtitle && (
          <span className="mt-1 block text-[13px] leading-relaxed text-[var(--color-fg-mute)]">
            {m.subtitle}
          </span>
        )}
      </span>

      <span className="col-start-2 flex items-center gap-4 sm:col-start-3 sm:pt-1">
        <Difficulty level={m.difficulty} />
        <span className="font-mono text-[11px] text-[var(--color-fg-mute)]">
          {formatDuration(m.duration)}
        </span>
      </span>
    </Link>
  );
}

export default function MissionsPage() {
  const phases = getAllPhases();

  return (
    <div className="mx-auto max-w-4xl px-5 py-16">
      <h1 className="font-[family-name:var(--font-display)] text-4xl text-white">
        The engagement, mission by mission
      </h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[var(--color-fg-dim)]">
        Work these in order. Each one assumes you know what the last one taught you
        and, more importantly, that you carry the same wrong assumptions the last
        one left you with.
      </p>

      <div className="mt-14 space-y-12">
        {phases.map((p) => (
          <section key={p.slug}>
            <div className="flex items-baseline gap-3">
              <span className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
                Phase {String(p.number).padStart(2, "0")}
              </span>
              <Link
                href={`/phases/${p.slug}`}
                className="font-[family-name:var(--font-display)] text-2xl text-white hover:text-[var(--color-teal)]"
              >
                {p.title}
              </Link>
            </div>
            <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-[var(--color-fg-mute)]">
              {p.summary}
            </p>

            <div className="mt-5 space-y-px overflow-hidden rounded-xl border border-[var(--color-line)] bg-[var(--color-line)]">
              {p.missions.map((m) => (
                <MissionRow key={m.id} m={m} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
