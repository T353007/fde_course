import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getAllPhases, getPhase, formatDuration } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";

export function generateStaticParams() {
  return getAllPhases().map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const phase = getPhase(slug);
  if (!phase) return {};
  return { title: phase.title, description: phase.summary };
}

export default async function PhasePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const phase = getPhase(slug);
  if (!phase) notFound();

  const html = await renderMarkdown(phase.body);
  const total = phase.missions.reduce((s, m) => s + m.duration, 0);

  return (
    <div className="mx-auto max-w-4xl px-5 py-16">
      <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
        Phase {String(phase.number).padStart(2, "0")} ·{" "}
        {phase.missions.length} missions · {formatDuration(total)}
      </div>

      <h1 className="mt-4 font-[family-name:var(--font-display)] text-4xl leading-tight text-white">
        {phase.title}
      </h1>
      {phase.subtitle && (
        <p className="mt-3 text-[17px] leading-relaxed text-[var(--color-fg-dim)]">
          {phase.subtitle}
        </p>
      )}

      <div className="prose mt-10" dangerouslySetInnerHTML={{ __html: html }} />

      <h2 className="mt-14 font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
        Missions in this phase
      </h2>
      <div className="mt-4 space-y-px overflow-hidden rounded-xl border border-[var(--color-line)] bg-[var(--color-line)]">
        {phase.missions.map((m) => (
          <Link
            key={m.id}
            href={`/missions/${m.slug}`}
            className="group flex items-start gap-4 bg-[var(--color-ink-2)] px-5 py-4 transition-colors hover:bg-[var(--color-panel)]"
          >
            <span className="pt-0.5 font-mono text-[12px] text-[var(--color-fg-mute)]">
              {m.id}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[15px] font-medium text-[var(--color-fg)] group-hover:text-[var(--color-teal)]">
                {m.title}
              </span>
              {m.subtitle && (
                <span className="mt-1 block text-[13px] leading-relaxed text-[var(--color-fg-mute)]">
                  {m.subtitle}
                </span>
              )}
            </span>
            <span className="shrink-0 pt-1 font-mono text-[11px] text-[var(--color-fg-mute)]">
              {formatDuration(m.duration)}
            </span>
          </Link>
        ))}
      </div>

      <div className="mt-10">
        <Link
          href="/missions"
          className="text-[13px] text-[var(--color-teal)] hover:underline"
        >
          ← All phases
        </Link>
      </div>
    </div>
  );
}
