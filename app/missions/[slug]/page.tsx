import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { cookies } from "next/headers";
import {
  getAllMissions,
  getMissionForTrack,
  getMissionNeighbors,
  getAllPhases,
  formatDuration,
} from "@/lib/content";
import { renderMarkdown, extractToc } from "@/lib/markdown";
import { TrackBanner } from "@/components/track-banner";
import { parseTrack, TRACK_COOKIE } from "@/lib/track";

export function generateStaticParams() {
  return getAllMissions().map((m) => ({ slug: m.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const cookieStore = await cookies();
  const track = parseTrack(cookieStore.get(TRACK_COOKIE)?.value);
  const loaded = getMissionForTrack(slug, track);
  if (!loaded) return {};
  const { mission } = loaded;
  const suffix = track === "condensed" ? " (Compressed)" : "";
  return {
    title: `${mission.id} · ${mission.title}${suffix}`,
    description: mission.subtitle,
  };
}

export default async function MissionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const cookieStore = await cookies();
  const track = parseTrack(cookieStore.get(TRACK_COOKIE)?.value);
  const loaded = getMissionForTrack(slug, track);
  if (!loaded) notFound();

  const { mission, usingCondensed } = loaded;
  const fullMeta = getMissionForTrack(slug, "full")!.mission;

  const html = await renderMarkdown(mission.body);
  const toc = extractToc(mission.body).filter((t) => t.depth === 2);
  const { prev, next } = getMissionNeighbors(slug);
  const phase = getAllPhases().find((p) => p.number === mission.phase);
  const displayDuration =
    usingCondensed && mission.durationCondensed
      ? mission.durationCondensed
      : mission.duration;

  return (
    <div className="mx-auto max-w-6xl px-5 py-12">
      <div className="lg:grid lg:grid-cols-[1fr_15rem] lg:gap-12">
        <article className="min-w-0">
          <header className="border-b border-[var(--color-line)] pb-8">
            <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[var(--color-fg-mute)]">
              <span className="text-[var(--color-teal)]">{mission.id}</span>
              <span>/</span>
              {phase && (
                <Link
                  href={`/phases/${phase.slug}`}
                  className="hover:text-[var(--color-fg)]"
                >
                  {phase.title}
                </Link>
              )}
              <span>/</span>
              <span>{formatDuration(displayDuration)}</span>
              {usingCondensed && (
                <>
                  <span>/</span>
                  <span className="text-[var(--color-teal)]">compressed</span>
                </>
              )}
              {mission.lab && (
                <>
                  <span>/</span>
                  <span className="text-[var(--color-amber)]">lab required</span>
                </>
              )}
            </div>

            <h1 className="mt-4 font-[family-name:var(--font-display)] text-4xl leading-tight tracking-tight text-white">
              {mission.title}
            </h1>
            {mission.subtitle && (
              <p className="mt-3 max-w-2xl text-[16px] leading-relaxed text-[var(--color-fg-dim)]">
                {mission.subtitle}
              </p>
            )}

            <TrackBanner track={track} hasCondensed={fullMeta.hasCondensed ?? false} />

            {mission.objectives.length > 0 && (
              <div className="mt-7 rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-5">
                <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
                  By the end of this mission you can
                </div>
                <ul className="mt-3 space-y-1.5">
                  {mission.objectives.map((o) => (
                    <li
                      key={o}
                      className="flex gap-2.5 text-[14px] leading-relaxed text-[var(--color-fg-dim)]"
                    >
                      <span className="mt-[9px] h-[4px] w-[4px] shrink-0 rounded-sm bg-[var(--color-teal-dim)]" />
                      {o}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </header>

          <div
            className="prose mt-10"
            dangerouslySetInnerHTML={{ __html: html }}
          />

          <nav className="mt-16 grid gap-3 border-t border-[var(--color-line)] pt-8 sm:grid-cols-2">
            {prev ? (
              <Link
                href={`/missions/${prev.slug}`}
                className="rounded-xl border border-[var(--color-line)] p-4 transition-colors hover:border-[var(--color-line-2)] hover:bg-[var(--color-panel)]"
              >
                <div className="font-mono text-[11px] text-[var(--color-fg-mute)]">
                  ← {prev.id}
                </div>
                <div className="mt-1 text-[14px] text-[var(--color-fg)]">
                  {prev.title}
                </div>
              </Link>
            ) : (
              <span />
            )}
            {next && (
              <Link
                href={`/missions/${next.slug}`}
                className="rounded-xl border border-[var(--color-line)] p-4 text-right transition-colors hover:border-[var(--color-line-2)] hover:bg-[var(--color-panel)] sm:col-start-2"
              >
                <div className="font-mono text-[11px] text-[var(--color-fg-mute)]">
                  {next.id} →
                </div>
                <div className="mt-1 text-[14px] text-[var(--color-fg)]">
                  {next.title}
                </div>
              </Link>
            )}
          </nav>
        </article>

        <aside className="mt-12 lg:mt-0">
          <div className="lg:sticky lg:top-20">
            {toc.length > 0 && (
              <>
                <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
                  In this mission
                </div>
                <ul className="mt-3 space-y-1.5 border-l border-[var(--color-line)]">
                  {toc.map((t) => (
                    <li key={t.id}>
                      <a
                        href={`#${t.id}`}
                        className="-ml-px block border-l border-transparent py-0.5 pl-3 text-[13px] leading-snug text-[var(--color-fg-mute)] transition-colors hover:border-[var(--color-teal)] hover:text-[var(--color-fg)]"
                      >
                        {t.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {mission.concepts.length > 0 && (
              <div className="mt-8">
                <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
                  Concepts
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {mission.concepts.map((c) => (
                    <span key={c} className="tag">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
