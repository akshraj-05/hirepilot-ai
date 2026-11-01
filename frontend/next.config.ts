import type { NextConfig } from "next";

// BACKEND_URL is a server-only variable used by the Next.js proxy rewrite.
// In Docker: set to http://backend:4000 (internal Docker network).
// In local dev: falls back to http://localhost:4000.
// Never expose this to the browser — use NEXT_PUBLIC_API_URL="" so
// browser fetch calls use relative /api/... paths and are proxied here.
const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000";

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins: ["10.50.14.231","10.50.14.252"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
