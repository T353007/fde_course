import Link from "next/link";

export function DocView({
  eyebrow,
  title,
  subtitle,
  html,
  backHref,
  backLabel,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  html: string;
  backHref?: string;
  backLabel?: string;
}) {
  return (
    <div className="mx-auto max-w-4xl px-5 py-16">
      {eyebrow && (
        <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
          {eyebrow}
        </div>
      )}

      <h1 className="mt-4 font-[family-name:var(--font-display)] text-4xl leading-tight text-white">
        {title}
      </h1>

      {subtitle && (
        <p className="mt-3 max-w-2xl text-[16px] leading-relaxed text-[var(--color-fg-dim)]">
          {subtitle}
        </p>
      )}

      <div className="prose mt-10" dangerouslySetInnerHTML={{ __html: html }} />

      {backHref && (
        <div className="mt-14 border-t border-[var(--color-line)] pt-6">
          <Link
            href={backHref}
            className="text-[13px] text-[var(--color-teal)] hover:underline"
          >
            ← {backLabel ?? "Back"}
          </Link>
        </div>
      )}
    </div>
  );
}
