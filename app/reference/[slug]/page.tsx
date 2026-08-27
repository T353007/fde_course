import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getDoc, getDocs } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";
import { DocView } from "@/components/doc-view";

export function generateStaticParams() {
  return getDocs("reference").map((d) => ({ slug: d.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = getDoc("reference", slug);
  if (!doc) return {};
  return { title: doc.title, description: doc.subtitle };
}

export default async function ReferenceDocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = getDoc("reference", slug);
  if (!doc) notFound();

  const html = await renderMarkdown(doc.body);

  return (
    <DocView
      eyebrow={doc.kind ?? "Reference"}
      title={doc.title}
      subtitle={doc.subtitle}
      html={html}
      backHref="/reference"
      backLabel="All reference pages"
    />
  );
}
