#!/usr/bin/env node
/**
 * Checks course content against STYLE_GUIDE.md and CANON.md.
 *
 * Run: npm run course:validate
 * Exits non-zero if any error-level rule fails, so it can gate a build.
 */

import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const COURSE = path.join(ROOT, "course");

const ERRORS = [];
const WARNINGS = [];

function err(file, line, msg) {
  ERRORS.push({ file, line, msg });
}
function warn(file, line, msg) {
  WARNINGS.push({ file, line, msg });
}

/* ------------------------------------------------------------------ rules */

// Words and phrases that make writing sound machine generated.
const BANNED_WORDS = [
  "delve",
  "tapestry",
  "realm",
  "testament to",
  "navigate the complexities",
  "embark",
  "unlock the power",
  "elevate your",
  "seamless",
  "leverage the",
  "streamline",
  "game changer",
  "game-changer",
  "paradigm",
  "holistic",
  "synergy",
  "cutting edge",
  "cutting-edge",
  "state of the art",
  "state-of-the-art",
  "in today's fast paced",
  "in today's fast-paced",
  "it is important to note",
  "it's important to note",
  "it is worth noting",
  "it's worth noting",
  "rest assured",
  "deep dive",
  "let's dive",
  "lets dive",
  "dive into",
  "buckle up",
  "in conclusion",
  "at the end of the day",
];

// Sentence shapes that are the loudest tells.
const BANNED_PATTERNS = [
  {
    re: /\bit'?s not just .{1,40}\.\s*it'?s\b/gi,
    msg: "banned construction: \"it's not just X. It's Y\"",
  },
  {
    re: /\b(isn'?t|aren'?t) about .{1,40}\.\s*(it'?s|they'?re) about\b/gi,
    msg: 'banned construction: "X isn\'t about Y, it\'s about Z"',
  },
  {
    re: /^\s*(Moreover|Furthermore|Additionally|Indeed),/gim,
    msg: "banned sentence opener",
  },
  {
    re: /\bwhether you'?re a .{1,30} or a\b/gi,
    msg: 'banned construction: "whether you\'re X or Y"',
  },
];

const REQUIRED_MISSION_FIELDS = [
  "id",
  "slug",
  "title",
  "subtitle",
  "phase",
  "order",
  "duration",
  "difficulty",
  "lab",
  "status",
  "objectives",
  "concepts",
  "competencies",
];

const VALID_COMPETENCIES = new Set([
  "discovery",
  "customer-communication",
  "architecture",
  "coding",
  "debugging",
  "ai-fundamentals",
  "evals",
  "rag",
  "agent-design",
  "security",
  "fintech-judgment",
  "production-reliability",
  "adoption",
  "productization",
  "executive-communication",
]);

// Numbers from CANON.md that missions must not contradict.
const CANON_NUMBERS = [
  { label: "median cycle time", good: "9.4", bad: /\b9\.[0-35-9]\s*day/g },
  { label: "underwriter hands-on", good: "41 minutes", bad: /\b4[02-9]\s*minutes of underwrit/gi },
  { label: "stuck applications", good: "214", bad: /\b2[0-9][0-9] applications (?:got |became |were )?stuck/g },
];

/* ------------------------------------------------------------- utilities */

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) return walk(full);
    return e.name.endsWith(".md") ? [full] : [];
  });
}

function splitFrontmatter(raw) {
  if (!raw.startsWith("---")) return { fm: null, body: raw, offset: 0 };
  const end = raw.indexOf("\n---", 3);
  if (end === -1) return { fm: null, body: raw, offset: 0 };
  const fm = raw.slice(4, end);
  const body = raw.slice(end + 4);
  const offset = fm.split("\n").length + 2;
  return { fm, body, offset };
}

/**
 * Fenced code blocks are evidence. Real logs and real Slack messages can contain
 * anything, so style rules only apply to prose.
 */
function stripCodeBlocks(body) {
  const lines = body.split("\n");
  let inFence = false;
  return lines.map((line) => {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence;
      return "";
    }
    return inFence ? "" : line;
  });
}

/* ---------------------------------------------------------------- checks */

function checkStyle(file, body) {
  const rel = path.relative(ROOT, file);
  const lines = stripCodeBlocks(body);

  lines.forEach((line, i) => {
    const n = i + 1;

    if (line.includes("\u2014")) {
      err(rel, n, "em dash found. Use a period, comma, colon, or parentheses.");
    }
    // En dash used as punctuation between spaces.
    if (/\s\u2013\s/.test(line)) {
      err(rel, n, "en dash used as punctuation.");
    }

    const lower = line.toLowerCase();
    for (const word of BANNED_WORDS) {
      if (lower.includes(word)) {
        err(rel, n, `banned phrase: "${word}"`);
      }
    }

    for (const { re, msg } of BANNED_PATTERNS) {
      re.lastIndex = 0;
      if (re.test(line)) err(rel, n, msg);
    }

    // Emoji outside evidence blocks.
    if (/[\u{1F300}-\u{1FAFF}\u{2700}-\u{27BF}]/u.test(line)) {
      warn(rel, n, "emoji in prose. Only allowed inside realistic evidence.");
    }

    // Sentence length. Long sentences break the eighth grade rule.
    const prose = line.replace(/^[#>\-*\d.\s|]+/, "").trim();
    if (prose && !prose.startsWith(":::") && !prose.includes("|")) {
      for (const sentence of prose.split(/(?<=[.!?])\s+/)) {
        const words = sentence.trim().split(/\s+/).length;
        if (words > 32) {
          warn(rel, n, `sentence is ${words} words. Split it.`);
        }
      }
    }
  });
}

function checkCanon(file, body) {
  const rel = path.relative(ROOT, file);
  const text = stripCodeBlocks(body).join("\n");

  for (const { label, bad } of CANON_NUMBERS) {
    bad.lastIndex = 0;
    const m = bad.exec(text);
    if (m) {
      warn(rel, 0, `possible canon conflict on ${label}: "${m[0].trim()}"`);
    }
  }
}

/**
 * A colon inside an unquoted YAML scalar breaks the whole build, and the error message
 * points at the parser rather than the file. Catch it here where it is obvious.
 */
function checkYamlSafety(file, fm) {
  if (!fm) return;
  const rel = path.relative(ROOT, file);

  fm.split("\n").forEach((line, i) => {
    const m = /^([a-zA-Z_]+):\s+(.+)$/.exec(line);
    if (!m) return;

    const value = m[2].trim();
    const quoted = /^["'].*["']$/.test(value);
    const isList = value.startsWith("[");

    if (!quoted && !isList && /:\s/.test(value)) {
      err(rel, i + 2, `unquoted colon in "${m[1]}". Wrap the value in quotes.`);
    }
    if (!quoted && !isList && /^[>|@`%*&!]/.test(value)) {
      err(rel, i + 2, `"${m[1]}" starts with a YAML control character. Quote it.`);
    }
  });
}

function checkMissionFrontmatter(file, fm) {
  const rel = path.relative(ROOT, file);
  if (!fm) {
    err(rel, 1, "missing frontmatter");
    return;
  }

  const get = (key) => {
    const m = new RegExp(`^${key}:\\s*(.*)$`, "m").exec(fm);
    return m ? m[1].trim() : null;
  };

  for (const field of REQUIRED_MISSION_FIELDS) {
    if (!new RegExp(`^${field}:`, "m").test(fm)) {
      err(rel, 1, `frontmatter missing "${field}"`);
    }
  }

  const id = get("id");
  const slug = get("slug");
  const base = path.basename(file, ".md");

  if (id && !/^M\d{2}$/.test(id)) {
    err(rel, 1, `id "${id}" should look like M07`);
  }
  if (id && slug && base !== `${id.toLowerCase()}-${slug}`) {
    err(rel, 1, `filename should be ${id.toLowerCase()}-${slug}.md`);
  }

  const status = get("status");
  if (status && !["stub", "draft", "complete"].includes(status)) {
    err(rel, 1, `status "${status}" is not stub, draft, or complete`);
  }

  const difficulty = Number(get("difficulty"));
  if (difficulty < 1 || difficulty > 5) {
    err(rel, 1, `difficulty ${difficulty} must be 1 to 5`);
  }

  // Competency names have to match the certification rubric.
  const compBlock = /competencies:\s*\[([^\]]*)\]/.exec(fm);
  const listed = compBlock
    ? compBlock[1].split(",").map((s) => s.trim().replace(/^["']|["']$/g, ""))
    : (fm.match(/^competencies:\n((?:\s+-\s+.*\n?)+)/m)?.[1] ?? "")
        .split("\n")
        .map((s) => s.replace(/^\s*-\s*/, "").trim())
        .filter(Boolean);

  for (const c of listed) {
    if (c && !VALID_COMPETENCIES.has(c)) {
      err(rel, 1, `unknown competency "${c}". See competency-matrix.md`);
    }
  }
}

function checkMissionStructure(file, body) {
  const rel = path.relative(ROOT, file);

  const required = [
    { name: "stopandthink", re: /:::stopandthink/ },
    { name: "task", re: /:::task/ },
    { name: "judgment", re: /:::judgment/ },
    { name: "dialogue", re: /:::dialogue/ },
  ];

  for (const { name, re } of required) {
    if (!re.test(body)) {
      err(rel, 0, `mission is missing a :::${name} block`);
    }
  }

  if (!/:::spoiler/.test(body)) {
    warn(rel, 0, "no :::spoiler block. Certification practice should be gated.");
  }

  // The learner must decide before the answer appears.
  const think = body.indexOf(":::stopandthink");
  const spoiler = body.indexOf(":::spoiler");
  if (think > -1 && spoiler > -1 && spoiler < think) {
    warn(rel, 0, "a :::spoiler appears before the first :::stopandthink");
  }

  // Directive blocks must be closed.
  const opens = (body.match(/^:::[a-z]/gm) ?? []).length;
  const closes = (body.match(/^:::\s*$/gm) ?? []).length;
  if (opens !== closes) {
    err(rel, 0, `unbalanced directives: ${opens} opened, ${closes} closed`);
  }

  const words = body.split(/\s+/).length;
  if (words < 1200) {
    warn(rel, 0, `only ${words} words. Missions should be substantial.`);
  }
}

/* ------------------------------------------------------------------ main */

const missionFiles = walk(path.join(COURSE, "missions"));
const otherFiles = [
  ...walk(path.join(COURSE, "phases")),
  ...walk(path.join(COURSE, "certification")),
  ...walk(path.join(COURSE, "reference")),
];
const rootDocs = ["README.md", "CANON.md", "COURSE_ARCHITECTURE.md", "COURSE_STATUS.md"]
  .map((f) => path.join(ROOT, f))
  .filter((f) => fs.existsSync(f));

for (const file of missionFiles) {
  const raw = fs.readFileSync(file, "utf8");
  const { fm, body } = splitFrontmatter(raw);
  checkYamlSafety(file, fm);
  checkMissionFrontmatter(file, fm);
  checkMissionStructure(file, body);
  checkStyle(file, body);
  checkCanon(file, body);
}

for (const file of [...otherFiles, ...rootDocs]) {
  const raw = fs.readFileSync(file, "utf8");
  const { fm, body } = splitFrontmatter(raw);
  checkYamlSafety(file, fm);
  // The style guide quotes bad examples on purpose.
  if (path.basename(file) === "STYLE_GUIDE.md") continue;
  checkStyle(file, body);
}

/* --------------------------------------------------------------- report */

const byFile = (list) => {
  const grouped = new Map();
  for (const item of list) {
    if (!grouped.has(item.file)) grouped.set(item.file, []);
    grouped.get(item.file).push(item);
  }
  return grouped;
};

if (WARNINGS.length) {
  console.log(`\n${WARNINGS.length} warnings\n`);
  for (const [file, items] of byFile(WARNINGS)) {
    console.log(`  ${file}`);
    for (const i of items.slice(0, 8)) {
      console.log(`    ${i.line ? `line ${i.line}: ` : ""}${i.msg}`);
    }
    if (items.length > 8) console.log(`    ...and ${items.length - 8} more`);
  }
}

if (ERRORS.length) {
  console.log(`\n${ERRORS.length} errors\n`);
  for (const [file, items] of byFile(ERRORS)) {
    console.log(`  ${file}`);
    for (const i of items.slice(0, 12)) {
      console.log(`    ${i.line ? `line ${i.line}: ` : ""}${i.msg}`);
    }
    if (items.length > 12) console.log(`    ...and ${items.length - 12} more`);
  }
  console.log(
    `\nFailed. ${missionFiles.length} missions checked. Fix the errors above.\n`
  );
  process.exit(1);
}

console.log(
  `\nContent check passed. ${missionFiles.length} missions, ${otherFiles.length} other pages, ${WARNINGS.length} warnings.\n`
);
