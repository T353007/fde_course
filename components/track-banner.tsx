import type { ReadingTrack } from "@/lib/track";
import { TrackToggle } from "@/components/track-toggle";

export function TrackBanner({
  track,
  hasCondensed,
}: {
  track: ReadingTrack;
  hasCondensed: boolean;
}) {
  if (track === "full") {
    return (
      <div className="mt-6 flex flex-col gap-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[13px] text-[var(--color-fg-dim)]">
          Short on time? Switch to{" "}
          <strong className="font-medium text-[var(--color-fg)]">Compressed</strong>. Same
          lab steps and same saved files.
        </p>
        <TrackToggle track={track} compact />
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-xl border border-[var(--color-teal-dim)] bg-[color-mix(in_srgb,var(--color-teal)_8%,transparent)] px-4 py-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-teal)]">
            Compressed track
          </div>
          <p className="mt-1 text-[13px] leading-relaxed text-[var(--color-fg-dim)]">
            Same code, same deliverables, less story. Need the full kickoff transcript or
            comms examples? Switch to full engagement using the header toggle.
          </p>
          {!hasCondensed && (
            <p className="mt-2 text-[13px] text-[var(--color-amber)]">
              A hand-written compressed version for this mission is not ready yet. Showing
              the full text.
            </p>
          )}
        </div>
        <TrackToggle track={track} compact />
      </div>
    </div>
  );
}
