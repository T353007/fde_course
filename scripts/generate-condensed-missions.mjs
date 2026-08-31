#!/usr/bin/env node
/**
 * Build course/missions-condensed/*.md from full missions.
 * Keeps tasks, stop-and-think, practice spoilers, and all fenced code blocks.
 * Skips long dialogue and "Working through it" sections.
 *
 * Run: node scripts/generate-condensed-missions.mjs
 */

import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

const ROOT = process.cwd();
const MISSIONS = path.join(ROOT, "course", "missions");
const OUT = path.join(ROOT, "course", "missions-condensed");

function firstParagraph(text, heading) {
  const re = new RegExp(`## ${heading}\\s*\\n+([^#]+)`, "i");
  const m = text.match(re);
  if (!m) return "";
  return m[1]
    .trim()
    .split(/\n\n+/)[0]
    .replace(/^:::.*?\n/gm, "")
    .replace(/^:::\s*$/gm, "")
    .trim();
}

function extractBlocks(body, directiveName) {
  const re = new RegExp(
    `:::${directiveName}(?:\\{[^}]*\\})?\\s*\\n([\\s\\S]*?)\\n:::`,
    "g"
  );
  const out = [];
  let m;
  while ((m = re.exec(body)) !== null) {
    out.push(m[0]);
  }
  return out;
}

function extractSection(body, heading) {
  const re = new RegExp(`(## ${heading}[\\s\\S]*?)(?=\\n## |$)`, "i");
  const m = body.match(re);
  return m ? m[1].trim() : "";
}

function simplifyParagraph(p) {
  return p
    .replace(/\s+/g, " ")
    .replace(/—/g, ",")
    .replace(/–/g, ",")
    .trim();
}

function buildCondensedBody(fullBody, meta) {
  const where = simplifyParagraph(firstParagraph(fullBody, "Where you are"));
  const request = extractSection(fullBody, "The request").slice(0, 1200);
  const evidenceBlocks = extractBlocks(fullBody, "evidence");
  const tasks = extractBlocks(fullBody, "task");
  const stops = extractBlocks(fullBody, "stopandthink");
  const practice = extractBlocks(fullBody, "spoiler");
  const judgment = extractBlocks(fullBody, "judgment");

  const lines = [
    "## Where you are",
    "",
    where ||
      "You are in the middle of the Northstar engagement. Do the work below. Read the full track if you want the scenes.",
    "",
  ];

  if (request && request.length < 900) {
    lines.push(request, "");
  } else if (evidenceBlocks.length > 0) {
    lines.push("## Key artifacts", "");
    for (const block of evidenceBlocks.slice(0, 3)) {
      lines.push(block, "");
    }
  }

  const labSection = extractSection(fullBody, "Bringing it up");
  if (labSection) {
    lines.push("## Bring the lab up", "");
    lines.push(
      labSection
        .replace(/^## Bringing it up\s*/i, "")
        .replace(/### Step \d+[^\n]*/g, (h) => h.replace("—", ","))
        .trim(),
      ""
    );
  }

  const evidenceSection = extractSection(fullBody, "Evidence");
  if (evidenceSection) {
    lines.push(evidenceSection, "");
  }

  const keyEvidence = evidenceBlocks.slice(0, 6);
  if (keyEvidence.length > 0 && request && request.length >= 900 && !evidenceSection) {
    lines.push("## Evidence to use", "");
    for (const block of keyEvidence) {
      lines.push(block, "");
    }
  }

  if (tasks.length) {
    lines.push("## Your task", "");
    for (const t of tasks) {
      lines.push(t, "");
    }
  }

  if (stops.length) {
    lines.push("## Stop and think", "");
    for (const s of stops) {
      lines.push(s, "");
    }
  }

  if (judgment.length) {
    lines.push("## One line to remember", "");
    lines.push(judgment[0], "");
  }

  if (practice.length) {
    lines.push("## Practice", "");
    lines.push(
      "Same skill, different industry. Open the spoiler only after you write your answer.",
      ""
    );
    lines.push(practice[0], "");
  }

  lines.push(
    "---",
    "",
    "*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*",
    ""
  );

  return lines.join("\n");
}

if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

const files = fs.readdirSync(MISSIONS).filter((f) => f.endsWith(".md"));

for (const file of files) {
  const raw = fs.readFileSync(path.join(MISSIONS, file), "utf8");
  const { data, content } = matter(raw);
  const condensedBody = buildCondensedBody(content, data);
  const outData = {
    ...data,
    condensed: true,
    durationCondensed: Math.max(30, Math.round(Number(data.duration ?? 120) * 0.4)),
  };
  const out = matter.stringify(condensedBody, outData);
  fs.writeFileSync(path.join(OUT, file), out);
  console.log("wrote", file);
}

console.log(`Done. ${files.length} condensed missions in course/missions-condensed/`);
