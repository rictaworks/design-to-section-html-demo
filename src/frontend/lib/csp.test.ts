import { describe, expect, it } from "vitest";
import { buildContentSecurityPolicy } from "./csp";

// 本番で default-src 'self' だけだと backend への fetch が connect-src で遮断され
// 「通信に失敗しました」になる（Issue #20・本番で securitypolicyviolation を実測）。
describe("buildContentSecurityPolicy", () => {
  it("allows fetch to the configured backend origin via connect-src", () => {
    const csp = buildContentSecurityPolicy("https://backend.example.test/");
    expect(csp).toMatch(/(^|; )connect-src [^;]*https:\/\/backend\.example\.test/);
  });

  it("allows blob: images so the fetched source image can be displayed", () => {
    const csp = buildContentSecurityPolicy("https://backend.example.test");
    expect(csp).toMatch(/(^|; )img-src 'self' data: blob:(;|$)/);
  });

  it("falls back to connect-src 'self' when the backend URL is not configured", () => {
    const csp = buildContentSecurityPolicy(undefined);
    expect(csp).toMatch(/(^|; )connect-src 'self'( |;|$)/);
  });

  it("allows loading and reporting to the shared GA4 tag (all demos)", () => {
    const csp = buildContentSecurityPolicy("https://backend.example.test");
    expect(csp).toMatch(/script-src [^;]*https:\/\/www\.googletagmanager\.com/);
    expect(csp).toMatch(/connect-src [^;]*https:\/\/www\.google-analytics\.com/);
    expect(csp).toMatch(/connect-src [^;]*https:\/\/analytics\.google\.com/);
  });

  it("keeps the restrictive baseline directives", () => {
    const csp = buildContentSecurityPolicy("https://backend.example.test");
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("form-action 'self'");
  });
});
