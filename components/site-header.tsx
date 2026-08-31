import Link from "next/link";
import { cookies } from "next/headers";
import { TrackToggle } from "@/components/track-toggle";
import { parseTrack, TRACK_COOKIE } from "@/lib/track";

const NAV = [
  { href: "/missions", label: "Missions" },
  { href: "/lab", label: "The Lab" },
  { href: "/certification", label: "Certification" },
  { href: "/reference", label: "Reference" },
];

export async function SiteHeader() {
  const cookieStore = await cookies();
  const track = parseTrack(cookieStore.get(TRACK_COOKIE)?.value);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-line)] bg-[color-mix(in_srgb,var(--color-ink)_88%,transparent)] backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-5">
        <Link href="/" className="group flex shrink-0 items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md border border-[var(--color-teal-dim)] bg-[color-mix(in_srgb,var(--color-teal)_14%,transparent)] font-mono text-[11px] font-bold text-[var(--color-teal)]">
            FD
          </span>
          <span className="hidden text-[13px] font-semibold tracking-tight text-[var(--color-fg)] sm:inline">
            FDE Field Manual
          </span>
        </Link>

        <nav className="ml-auto flex items-center gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="hidden rounded-md px-3 py-1.5 text-[13px] text-[var(--color-fg-dim)] transition-colors hover:bg-[var(--color-panel)] hover:text-[var(--color-fg)] sm:inline"
            >
              {item.label}
            </Link>
          ))}
          <TrackToggle track={track} compact />
        </nav>
      </div>
    </header>
  );
}
