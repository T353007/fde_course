import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getDoc } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";
import { DocView } from "@/components/doc-view";

export const metadata: Metadata = {
  title: "Capstone · Meridian Financial",
  description:
    "A cold engagement with a new lender. A folder of messy artifacts, no hints, and no stated right answer.",
};

export default async function CapstonePage() {
  const doc = getDoc("certification", "capstone-meridian");
  if (!doc) notFound();
  const html = await renderMarkdown(doc.body);

  return (
    <DocView
      eyebrow="Capstone · scored on 15 competencies"
      title={doc.title}
      subtitle={doc.subtitle}
      html={html}
      backHref="/certification"
      backLabel="Certification"
    />
  );
}
