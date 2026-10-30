import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output keeps the production Docker image small.
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
