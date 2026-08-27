import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

const COURSE_DIR = path.join(process.cwd(), "course");

export type MissionStatus = "draft" | "complete" | "stub";

export interface MissionMeta {
  id: string; // "M04"
  slug: string; // "the-nine-day-question"
  title: string;
  subtitle?: string;
  phase: number;
  order: number;
  duration: number; // minutes
  difficulty: 1 | 2 | 3 | 4 | 5;
  objectives: string[];
  concepts: string[];
  competencies: string[];
  lab: boolean;
  status: MissionStatus;
  prereqs?: string[];
}

export interface Mission extends MissionMeta {
  body: string;
}

export interface PhaseMeta {
  number: number;
  slug: string;
  title: string;
  subtitle?: string;
  summary: string;
  arc?: string;
}

export interface Phase extends PhaseMeta {
  body: string;
  missions: MissionMeta[];
}

export interface DocMeta {
  slug: string;
  title: string;
  subtitle?: string;
  kind?: string;
  order?: number;
  duration?: number;
  competencies?: string[];
}

export interface Doc extends DocMeta {
  body: string;
}

function readDir(dir: string): string[] {
  const full = path.join(COURSE_DIR, dir);
  if (!fs.existsSync(full)) return [];
  return fs
    .readdirSync(full)
    .filter((f) => f.endsWith(".md"))
    .sort();
}

function parseFile(dir: string, file: string) {
  const full = path.join(COURSE_DIR, dir, file);
  const raw = fs.readFileSync(full, "utf8");
  return matter(raw);
}

let missionCache: Mission[] | null = null;

export function getAllMissions(): Mission[] {
  if (missionCache) return missionCache;

  const missions = readDir("missions").map((file) => {
    const { data, content } = parseFile("missions", file);
    const fallbackSlug = file.replace(/\.md$/, "").replace(/^m\d+-/i, "");

    return {
      id: String(data.id ?? file.slice(0, 3).toUpperCase()),
      slug: String(data.slug ?? fallbackSlug),
      title: String(data.title ?? fallbackSlug),
      subtitle: data.subtitle ? String(data.subtitle) : undefined,
      phase: Number(data.phase ?? 0),
      order: Number(data.order ?? 0),
      duration: Number(data.duration ?? 120),
      difficulty: (Number(data.difficulty ?? 3) as MissionMeta["difficulty"]),
      objectives: (data.objectives ?? []) as string[],
      concepts: (data.concepts ?? []) as string[],
      competencies: (data.competencies ?? []) as string[],
      lab: Boolean(data.lab ?? false),
      status: (data.status ?? "draft") as MissionStatus,
      prereqs: (data.prereqs ?? []) as string[],
      body: content,
    } satisfies Mission;
  });

  missions.sort((a, b) => a.order - b.order);
  missionCache = missions;
  return missions;
}

export function getMission(slug: string): Mission | undefined {
  return getAllMissions().find((m) => m.slug === slug);
}

export function getMissionNeighbors(slug: string) {
  const all = getAllMissions();
  const i = all.findIndex((m) => m.slug === slug);
  return {
    prev: i > 0 ? all[i - 1] : undefined,
    next: i >= 0 && i < all.length - 1 ? all[i + 1] : undefined,
  };
}

let phaseCache: Phase[] | null = null;

export function getAllPhases(): Phase[] {
  if (phaseCache) return phaseCache;

  const missions = getAllMissions();
  const phases = readDir("phases").map((file) => {
    const { data, content } = parseFile("phases", file);
    const number = Number(data.number ?? 0);
    return {
      number,
      slug: String(data.slug ?? `phase-${number}`),
      title: String(data.title ?? `Phase ${number}`),
      subtitle: data.subtitle ? String(data.subtitle) : undefined,
      summary: String(data.summary ?? ""),
      arc: data.arc ? String(data.arc) : undefined,
      body: content,
      missions: missions
        .filter((m) => m.phase === number)
        .map(({ body: _body, ...meta }) => meta),
    } satisfies Phase;
  });

  phases.sort((a, b) => a.number - b.number);
  phaseCache = phases;
  return phases;
}

export function getPhase(slug: string): Phase | undefined {
  return getAllPhases().find((p) => p.slug === slug);
}

export function getDocs(dir: "certification" | "reference"): Doc[] {
  return readDir(dir)
    .map((file) => {
      const { data, content } = parseFile(dir, file);
      return {
        slug: String(data.slug ?? file.replace(/\.md$/, "")),
        title: String(data.title ?? file),
        subtitle: data.subtitle ? String(data.subtitle) : undefined,
        kind: data.kind ? String(data.kind) : undefined,
        order: Number(data.order ?? 99),
        duration: data.duration ? Number(data.duration) : undefined,
        competencies: (data.competencies ?? []) as string[],
        body: content,
      } satisfies Doc;
    })
    .sort((a, b) => (a.order ?? 99) - (b.order ?? 99));
}

export function getDoc(
  dir: "certification" | "reference",
  slug: string
): Doc | undefined {
  return getDocs(dir).find((d) => d.slug === slug);
}

export interface CourseStats {
  missions: number;
  complete: number;
  phases: number;
  minutes: number;
  exams: number;
}

export function getCourseStats(): CourseStats {
  const missions = getAllMissions();
  return {
    missions: missions.length,
    complete: missions.filter((m) => m.status === "complete").length,
    phases: getAllPhases().length,
    minutes: missions.reduce((sum, m) => sum + m.duration, 0),
    exams: getDocs("certification").filter((d) => d.kind === "exam").length,
  };
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}
