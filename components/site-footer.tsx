import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-[var(--color-line)]">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <div className="text-[13px] font-semibold text-[var(--color-fg)]">
            The Forward Deployed Engineer Field Manual
          </div>
          <p className="mt-2 max-w-sm text-[13px] leading-relaxed text-[var(--color-fg-mute)]">
            A hands-on lab for engineers who have to ship AI into real financial
            systems. You work one long customer engagement, from the first bad
            requirement to the incident review.
          </p>
        </div>

        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-[var(--color-fg-mute)]">
            Course
          </div>
          <ul className="mt-3 space-y-2 text-[13px]">
            <li>
              <Link href="/missions" className="text-[var(--color-fg-dim)] hover:text-[var(--color-teal)]">
                All missions
              </Link>
            </li>
            <li>
              <Link href="/lab" className="text-[var(--color-fg-dim)] hover:text-[var(--color-teal)]">
                Lab setup
              </Link>
            </li>
            <li>
              <Link href="/certification" className="text-[var(--color-fg-dim)] hover:text-[var(--color-teal)]">
                Certification
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-[var(--color-fg-mute)]">
            The account
          </div>
          <ul className="mt-3 space-y-2 text-[13px] text-[var(--color-fg-mute)]">
            <li>Northstar Capital</li>
            <li>Redwood Bank</li>
            <li>Meridian Financial</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-[var(--color-line)] px-5 py-5">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 text-[12px] text-[var(--color-fg-mute)]">
          <span>
            Every company, person, and vendor in this course is fictional. The
            failures are not.
          </span>
          <span className="font-mono">v0.1</span>
        </div>
      </div>
    </footer>
  );
}
