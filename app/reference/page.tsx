import Link from "next/link";
import type { Metadata } from "next";
import { getDocs } from "@/lib/content";

export const metadata: Metadata = {
  title: "Reference",
  description:
    "The cast, the systems, the AI concept primers, and the competency map. Look things up here when a mission assumes you remember.",
};

export default function ReferencePage() {
  const docs = getDocs("reference");

  return (
    <div className="mx-auto max-w-4xl px-5 py-16">
      <h1 className="font-[family-name:var(--font-display)] text-4xl text-white">
        Reference
      </h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[var(--color-fg-dim)]">
        Short pages you look up mid mission. Who is who at Northstar, what the
        services do, and plain explanations of the AI concepts the missions use.
      </p>

      <div className="mt-12 grid gap-3 sm:grid-cols-2">
        {docs.map((d) => (
          <Link
            key={d.slug}
            href={`/reference/${d.slug}`}
            className="group rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-5 transition-colors hover:border-[var(--color-line-2)]"
          >
            {d.kind && (
              <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--color-fg-mute)]">
                {d.kind}
              </span>
            )}
            <div className="mt-1 text-[15px] font-medium text-white group-hover:text-[var(--color-teal)]">
              {d.title}
            </div>
            {d.subtitle && (
              <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--color-fg-mute)]">
                {d.subtitle}
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
