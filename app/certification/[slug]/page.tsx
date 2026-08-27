import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getDoc, getDocs, formatDuration } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";
import { DocView } from "@/components/doc-view";

export function generateStaticParams() {
  return getDocs("certification").map((d) => ({ slug: d.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = getDoc("certification", slug);
  if (!doc) return {};
  return { title: doc.title, description: doc.subtitle };
}

export default async function CertificationDocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = getDoc("certification", slug);
  if (!doc) notFound();

  const html = await renderMarkdown(doc.body);
  const eyebrow = [
    doc.kind === "exam" ? "Practical exam" : "Certification",
    doc.duration ? formatDuration(doc.duration) : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <DocView
      eyebrow={eyebrow}
      title={doc.title}
      subtitle={doc.subtitle}
      html={html}
      backHref="/certification"
      backLabel="All exams"
    />
  );
}
