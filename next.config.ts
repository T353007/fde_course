import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Course prose lives in /course as plain Markdown and is read at build time.
  // Tracing it explicitly keeps the files present in the serverless bundle.
  outputFileTracingIncludes: {
    "/**": ["./course/**/*"],
  },
  experimental: {
    optimizePackageImports: ["shiki"],
  },
};

export default nextConfig;
