"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import type { ReadingTrack } from "@/lib/track";
import { TRACK_COOKIE, trackDescription, trackLabel } from "@/lib/track";

const OPTIONS: ReadingTrack[] = ["full", "condensed"];

export function TrackToggle({
  track,
  compact = false,
}: {
  track: ReadingTrack;
  compact?: boolean;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function setTrack(next: ReadingTrack) {
    if (next === track) return;
    document.cookie = `${TRACK_COOKIE}=${next};path=/;max-age=31536000;samesite=lax`;
    startTransition(() => {
      router.refresh();
    });
  }

  return (
    <div
      className={compact ? "" : "rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-4"}
      role="group"
      aria-label="Reading track"
    >
      {!compact && (
        <div className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-fg-mute)]">
          Reading track
        </div>
      )}
      <div className={`flex gap-1 ${compact ? "" : "mt-3"}`}>
        {OPTIONS.map((opt) => {
          const active = track === opt;
          return (
            <button
              key={opt}
              type="button"
              disabled={pending}
              onClick={() => setTrack(opt)}
              title={trackDescription(opt)}
              className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${
                active
                  ? "bg-[var(--color-teal)] text-[#06231e]"
                  : "text-[var(--color-fg-dim)] hover:bg-[var(--color-ink-2)] hover:text-[var(--color-fg)]"
              }`}
            >
              {trackLabel(opt)}
            </button>
          );
        })}
      </div>
      {!compact && (
        <p className="mt-2 text-[12px] leading-relaxed text-[var(--color-fg-mute)]">
          {trackDescription(track)}
        </p>
      )}
    </div>
  );
}
