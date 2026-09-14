import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import RootLayout from "./layout";
import { messages } from "@/lib/messages";

// next/script はテスト環境で <script> をそのまま描画しないため、要素の有無だけを検証できるよう
// 最小限のダミーに差し替える。
vi.mock("next/script", () => ({
  default: (props: { id?: string; src?: string }) => <script id={props.id} src={props.src} />,
}));

// next/font/google はNext.jsのビルドパイプライン（SWC変換）が無いと呼び出せないため、
// テスト環境ではフォントの読み込みそのものを検証対象外としてダミーに差し替える。
vi.mock("next/font/google", () => ({
  Geist: () => ({ variable: "--font-geist-sans" }),
  Geist_Mono: () => ({ variable: "--font-geist-mono" }),
}));

// LayoutProps<"/"> は params: Promise<{}> を要求する（App Router の型生成）。テストでは中身を
// 使わないので、要求されるだけの空 Promise を渡す。
const params = Promise.resolve({});

// 全デモ共通の必須4要素（.claude/agents/demo-common-ui.md）とGA4タグを検証する。
describe("RootLayout (demo-common-ui)", () => {
  it("shows the amber demo banner", () => {
    render(<RootLayout params={params}>{<div />}</RootLayout>);
    expect(screen.getByText(messages.demo.banner)).toBeInTheDocument();
  });

  it("links back to the demo list", () => {
    render(<RootLayout params={params}>{<div />}</RootLayout>);
    const link = screen.getByRole("link", { name: messages.demo.backToList });
    expect(link).toHaveAttribute("href", "https://rictaworks.jp/#demos");
  });

  it("shows a fixed consult button linking to rictaworks.jp", () => {
    render(<RootLayout params={params}>{<div />}</RootLayout>);
    const link = screen.getByRole("link", { name: new RegExp(messages.demo.consult) });
    expect(link).toHaveAttribute("href", "https://rictaworks.jp/");
  });

  it("links to the /legal page from the footer", () => {
    render(<RootLayout params={params}>{<div />}</RootLayout>);
    const link = screen.getByRole("link", { name: messages.demo.legalLink });
    expect(link).toHaveAttribute("href", "/legal");
  });

  it("loads the shared GA4 tag", () => {
    render(<RootLayout params={params}>{<div />}</RootLayout>);
    expect(document.querySelector('script[src*="googletagmanager.com/gtag/js?id=G-C04W1XKS16"]')).not.toBeNull();
  });
});
