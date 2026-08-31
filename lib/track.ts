export type ReadingTrack = "full" | "condensed";

export const TRACK_COOKIE = "fde-reading-track";
export const TRACK_DEFAULT: ReadingTrack = "full";

export function parseTrack(value: string | undefined | null): ReadingTrack {
  return value === "condensed" ? "condensed" : "full";
}

export function trackLabel(track: ReadingTrack): string {
  return track === "condensed" ? "Compressed" : "Full engagement";
}

export function trackDescription(track: ReadingTrack): string {
  if (track === "condensed") {
    return "Same lab, same curls, same deliverables. Less story.";
  }
  return "Full scenes, dialogue, and debriefs.";
}
