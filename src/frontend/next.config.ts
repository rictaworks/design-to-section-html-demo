import type { NextConfig } from "next";

// Next.js 16 (Turbopack) は script-src へのnonce自動付与に対応していないため、
// strict-dynamic/nonce方式ではなくscript-src 'unsafe-inline'を許容する（フレームワーク自身の
// hydrationスクリプトが動作しなくなるため）。他の各ディレクティブは既定で 'self' に制限し、
// object-src・frame-ancestors相当（frame-src）等でクリックジャッキング・プラグイン起動を防ぐ。
const SECURITY_HEADERS = [
  {
    key: "Content-Security-Policy",
    value:
      "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'",
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
