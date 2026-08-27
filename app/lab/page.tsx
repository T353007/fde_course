import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getDoc } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";
import { DocView } from "@/components/doc-view";

export const metadata: Metadata = {
  title: "The Lab",
  description:
    "Bring up the Northstar system on your laptop. Java services, Postgres, Kafka, Redis, fake vendors, and a model layer that needs no API key.",
};

export default async function LabPage() {
  const doc = getDoc("reference", "lab-setup");
  if (!doc) notFound();
  const html = await renderMarkdown(doc.body);

  return (
    <DocView
      eyebrow="Setup · do this before Mission 02"
      title={doc.title}
      subtitle={doc.subtitle}
      html={html}
      backHref="/missions"
      backLabel="All missions"
    />
  );
}
