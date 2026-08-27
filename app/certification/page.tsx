import Link from "next/link";
import type { Metadata } from "next";
import { getDocs, formatDuration } from "@/lib/content";

export const metadata: Metadata = {
  title: "Certification",
  description:
    "Six practical exams and a cold capstone. Scored on discovery, debugging, architecture, incident response, and communication.",
};

export default function CertificationPage() {
  const docs = getDocs("certification");
  const exams = docs.filter((d) => d.kind === "exam");
  const other = docs.filter((d) => d.kind !== "exam");

  return (
    <div className="mx-auto max-w-4xl px-5 py-16">
      <h1 className="font-[family-name:var(--font-display)] text-4xl text-white">
        Certification
      </h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[var(--color-fg-dim)]">
        The missions teach. These test. Each exam gives you a situation and no
        answer key until you have committed to a response in writing. Discovery and
        communication carry the same weight as implementation, because that is where
        new FDEs actually fail.
      </p>

      {exams.length > 0 && (
        <div className="mt-12 space-y-px overflow-hidden rounded-xl border border-[var(--color-line)] bg-[var(--color-line)]">
          {exams.map((d, i) => (
            <Link
              key={d.slug}
              href={`/certification/${d.slug}`}
              className="group flex items-start gap-4 bg-[var(--color-ink-2)] px-5 py-5 transition-colors hover:bg-[var(--color-panel)]"
            >
              <span className="pt-0.5 font-mono text-[12px] text-[var(--color-fg-mute)]">
                E{String(i + 1).padStart(2, "0")}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[15px] font-medium text-[var(--color-fg)] group-hover:text-[var(--color-teal)]">
                  {d.title}
                </span>
                {d.subtitle && (
                  <span className="mt-1 block text-[13px] leading-relaxed text-[var(--color-fg-mute)]">
                    {d.subtitle}
                  </span>
                )}
              </span>
              {d.duration && (
                <span className="shrink-0 pt-1 font-mono text-[11px] text-[var(--color-fg-mute)]">
                  {formatDuration(d.duration)}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}

      {other.length > 0 && (
        <>
          <h2 className="mt-14 font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
            Rubrics and reference
          </h2>
          <div className="mt-4 space-y-px overflow-hidden rounded-xl border border-[var(--color-line)] bg-[var(--color-line)]">
            {other.map((d) => (
              <Link
                key={d.slug}
                href={`/certification/${d.slug}`}
                className="group block bg-[var(--color-ink-2)] px-5 py-4 transition-colors hover:bg-[var(--color-panel)]"
              >
                <span className="text-[14px] text-[var(--color-fg)] group-hover:text-[var(--color-teal)]">
                  {d.title}
                </span>
                {d.subtitle && (
                  <span className="mt-1 block text-[13px] text-[var(--color-fg-mute)]">
                    {d.subtitle}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
