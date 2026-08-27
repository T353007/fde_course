import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "The Forward Deployed Engineer Field Manual",
    template: "%s · FDE Field Manual",
  },
  description:
    "A hands-on lab that trains engineers to ship AI into messy fintech production systems. One long customer engagement, 40 missions, a running Java and Python lab, and a capstone.",
  keywords: [
    "forward deployed engineer",
    "AI engineering",
    "fintech",
    "LLM evals",
    "RAG",
    "production AI",
  ],
  openGraph: {
    title: "The Forward Deployed Engineer Field Manual",
    description:
      "Work one messy fintech engagement from discovery to production. 40 missions, a running lab, and a capstone.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
