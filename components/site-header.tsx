import Link from "next/link";

const NAV = [
  { href: "/missions", label: "Missions" },
  { href: "/lab", label: "The Lab" },
  { href: "/certification", label: "Certification" },
  { href: "/reference", label: "Reference" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-line)] bg-[color-mix(in_srgb,var(--color-ink)_88%,transparent)] backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-5">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md border border-[var(--color-teal-dim)] bg-[color-mix(in_srgb,var(--color-teal)_14%,transparent)] font-mono text-[11px] font-bold text-[var(--color-teal)]">
            FD
          </span>
          <span className="text-[13px] font-semibold tracking-tight text-[var(--color-fg)]">
            FDE Field Manual
          </span>
        </Link>

        <nav className="ml-auto flex items-center gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-[13px] text-[var(--color-fg-dim)] transition-colors hover:bg-[var(--color-panel)] hover:text-[var(--color-fg)]"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
