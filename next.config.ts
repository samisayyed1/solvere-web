import type { NextConfig } from "next";

// Static export per docs/BRIEF.md §3.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true }, // required when output: 'export'
  trailingSlash: false,
  reactStrictMode: true,
};

export default nextConfig;
