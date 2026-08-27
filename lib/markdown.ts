import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkDirective from "remark-directive";
import remarkRehype from "remark-rehype";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import rehypePrettyCode from "rehype-pretty-code";
import rehypeStringify from "rehype-stringify";
import { visit } from "unist-util-visit";
import type { Node, Parent } from "unist";

type UnifiedPlugin = (options: Record<string, unknown>) => (tree: Node) => void;

/**
 * Course prose uses a small set of container directives so that a mission reads as a
 * transcript of an engagement rather than a textbook chapter. The directives are:
 *
 *   :::dialogue{title="Kickoff call"}   speaker-attributed conversation
 *   :::evidence{type=log label="..."}   raw artifacts: logs, SQL, HTTP, tickets, traces
 *   :::stopandthink                     gated questions; the reader must commit first
 *   :::judgment                         the durable FDE lesson
 *   :::commslab                         how to say it to each audience
 *   :::spoiler{label="Answer key"}      collapsed by default
 *   :::note / :::warning / :::danger    inline callouts
 *   :::task                             the concrete thing to go do
 *   :::files                            file tree / artifact manifest
 */

type DirectiveNode = Node & {
  name: string;
  attributes?: Record<string, string>;
  children: Node[];
  data?: {
    hName?: string;
    hProperties?: Record<string, unknown>;
  };
};

const CONTAINERS = new Set([
  "dialogue",
  "evidence",
  "stopandthink",
  "judgment",
  "commslab",
  "spoiler",
  "note",
  "warning",
  "danger",
  "task",
  "files",
  "objectives",
  "timeline",
  "grid",
  "card",
]);

/** Extract plain text from a phrasing-content subtree. */
function nodeText(node: Node): string {
  const n = node as Node & { value?: string; children?: Node[] };
  if (typeof n.value === "string") return n.value;
  if (Array.isArray(n.children)) return n.children.map(nodeText).join("");
  return "";
}

/**
 * Inside a :::dialogue block, a paragraph beginning with a bolded name becomes a
 * speaker turn. `**Renee:** We don't use that number.` renders as an attributed line.
 * Everything else in the block (stage directions, narration) passes through.
 */
function transformDialogue(node: DirectiveNode) {
  const turns: Node[] = [];

  for (const child of node.children) {
    const para = child as Parent & { type: string };

    if (para.type !== "paragraph" || !para.children?.length) {
      turns.push(child);
      continue;
    }

    const [first, ...rest] = para.children as Node[];
    const isStrong = (first as Node & { type: string }).type === "strong";
    if (!isStrong) {
      turns.push({
        type: "paragraph",
        children: para.children,
        data: { hProperties: { className: "dlg-narration" } },
      } as Node);
      continue;
    }

    const rawSpeaker = nodeText(first).replace(/:\s*$/, "").trim();
    // Strip a leading colon left behind in the remaining text.
    const body = [...rest];
    if (body.length) {
      const head = body[0] as Node & { type: string; value?: string };
      if (head.type === "text" && typeof head.value === "string") {
        head.value = head.value.replace(/^\s*:\s*/, "").replace(/^\s+/, " ");
      }
    }

    const speakerKey = rawSpeaker.toLowerCase().split(/[\s(]/)[0];
    const initials = rawSpeaker
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w[0])
      .join("")
      .toUpperCase();

    turns.push({
      type: "paragraph",
      data: {
        hName: "div",
        hProperties: {
          className: "dlg-turn",
          "data-speaker": speakerKey,
        },
      },
      children: [
        {
          type: "paragraph",
          data: {
            hName: "div",
            hProperties: { className: "dlg-avatar", "data-speaker": speakerKey },
          },
          children: [{ type: "text", value: initials }],
        },
        {
          type: "paragraph",
          data: { hName: "div", hProperties: { className: "dlg-body" } },
          children: [
            {
              type: "paragraph",
              data: { hName: "div", hProperties: { className: "dlg-speaker" } },
              children: [{ type: "text", value: rawSpeaker }],
            },
            {
              type: "paragraph",
              data: { hName: "div", hProperties: { className: "dlg-text" } },
              children: body,
            },
          ],
        },
      ],
    } as Node);
  }

  node.children = turns;
}

function remarkCourseDirectives() {
  return (tree: Node) => {
    visit(tree, (node, index, parent) => {
      const n = node as DirectiveNode;
      if (
        n.type !== "containerDirective" &&
        n.type !== "leafDirective" &&
        n.type !== "textDirective"
      ) {
        return;
      }

      /**
       * remark-directive treats every `:something` as a directive. Times like
       * `6:40 AM`, ratios like `1:1`, and ports like `localhost:8081` become
       * empty tags and look like line breaks. We only use container directives
       * (`:::dialogue`, `:::evidence`, ...), so restore text and leaf forms
       * as literal characters.
       */
      if (n.type === "textDirective" || n.type === "leafDirective") {
        if (typeof index === "number" && parent && Array.isArray((parent as Parent).children)) {
          const colon = n.type === "leafDirective" ? "::" : ":";
          let value = `${colon}${n.name}`;
          const attrs = n.attributes ?? {};
          const keys = Object.keys(attrs);
          if (keys.length > 0) {
            const body = keys
              .map((k) => {
                const v = attrs[k];
                if (v === "" || v == null) return k;
                return `${k}="${v}"`;
              })
              .join(" ");
            value += `{${body}}`;
          }
          const label = nodeText(n);
          if (label) value += `[${label}]`;
          (parent as Parent).children[index] = { type: "text", value } as Node;
        }
        return;
      }

      if (!CONTAINERS.has(n.name)) {
        // Unknown :::container: leave it alone rather than inventing a card.
        return;
      }

      const attrs = n.attributes ?? {};
      const data = (n.data ??= {});
      const props: Record<string, unknown> = {};

      switch (n.name) {
        case "dialogue": {
          transformDialogue(n);
          data.hName = "div";
          props.className = "cd cd-dialogue";
          if (attrs.title) props["data-title"] = attrs.title;
          if (attrs.channel) props["data-channel"] = attrs.channel;
          break;
        }
        case "evidence": {
          data.hName = "figure";
          props.className = "cd cd-evidence";
          props["data-kind"] = attrs.type ?? "artifact";
          if (attrs.label) props["data-label"] = attrs.label;
          if (attrs.source) props["data-source"] = attrs.source;
          break;
        }
        case "stopandthink": {
          data.hName = "section";
          props.className = "cd cd-stopandthink";
          props["data-title"] = attrs.title ?? "Stop and think";
          break;
        }
        case "spoiler": {
          data.hName = "details";
          props.className = "cd cd-spoiler";
          props["data-label"] = attrs.label ?? "Reveal";
          break;
        }
        case "judgment": {
          data.hName = "section";
          props.className = "cd cd-judgment";
          props["data-title"] = attrs.title ?? "FDE judgment";
          break;
        }
        case "commslab": {
          data.hName = "section";
          props.className = "cd cd-commslab";
          props["data-title"] = attrs.title ?? "Communication lab";
          break;
        }
        case "task": {
          data.hName = "section";
          props.className = "cd cd-task";
          props["data-title"] = attrs.title ?? "Your task";
          if (attrs.time) props["data-time"] = attrs.time;
          break;
        }
        default: {
          data.hName = "div";
          props.className = `cd cd-${n.name}`;
          if (attrs.title) props["data-title"] = attrs.title;
          if (attrs.label) props["data-label"] = attrs.label;
          break;
        }
      }

      data.hProperties = props;
    });
  };
}

/**
 * A :::spoiler becomes <details>, which needs a <summary> as its first child or the
 * browser invents one reading "Details". Injected after directive transformation.
 */
function rehypeSpoilerSummary() {
  return (tree: Node) => {
    visit(tree, "element", (node: Node) => {
      const el = node as Node & {
        tagName?: string;
        properties?: Record<string, unknown>;
        children?: unknown[];
      };
      if (el.tagName !== "details") return;
      const label = (el.properties?.["data-label"] as string) ?? "Reveal";
      el.children = [
        {
          type: "element",
          tagName: "summary",
          properties: { className: "cd-spoiler-summary" },
          children: [{ type: "text", value: label }],
        },
        ...(el.children ?? []),
      ] as never[];
    });
  };
}

const prettyCodeOptions = {
  theme: { dark: "github-dark-dimmed", light: "github-light" },
  keepBackground: false,
  defaultLang: { block: "text", inline: "text" },
};

const processor = unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkDirective)
  .use(remarkCourseDirectives)
  .use(remarkRehype, { allowDangerousHtml: true })
  .use(rehypeSlug)
  // These two plugins ship option types that do not line up with the generic
  // `.use()` tuple signature. The casts keep the chain typed end to end.
  .use(rehypeAutolinkHeadings as unknown as UnifiedPlugin, {
    behavior: "wrap",
    properties: { className: "heading-anchor" },
  })
  .use(rehypePrettyCode as unknown as UnifiedPlugin, prettyCodeOptions)
  .use(rehypeSpoilerSummary)
  .use(rehypeStringify, { allowDangerousHtml: true });

export async function renderMarkdown(source: string): Promise<string> {
  const file = await processor.process(source);
  return String(file);
}

export type TocEntry = { depth: number; text: string; id: string };

/** Build a table of contents from h2/h3 without re-parsing the rendered HTML. */
export function extractToc(source: string): TocEntry[] {
  const entries: TocEntry[] = [];
  const lines = source.split("\n");
  let inFence = false;

  for (const line of lines) {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;

    const m = /^(#{2,3})\s+(.*)$/.exec(line);
    if (!m) continue;

    const text = m[2]
      .replace(/`/g, "")
      .replace(/\*\*/g, "")
      .replace(/\[(.*?)\]\(.*?\)/g, "$1")
      .trim();

    const id = text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-");

    entries.push({ depth: m[1].length, text, id });
  }

  return entries;
}
