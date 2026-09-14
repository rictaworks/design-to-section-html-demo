import type { NextConfig } from "next";
import { buildContentSecurityPolicy } from "./lib/csp";

// CSP の方針と各ディレクティブの理由は lib/csp.ts を参照。
const SECURITY_HEADERS = [
  {
    key: "Content-Security-Policy",
    value: buildContentSecurityPolicy(process.env.NEXT_PUBLIC_BACKEND_URL),
  },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: SECURITY_HEADERS,
      },
    ];
  },
};

export default nextConfig;
