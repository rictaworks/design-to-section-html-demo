import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import Link from "next/link";
import { config } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCommentDots } from "@fortawesome/free-solid-svg-icons";
import { messages } from "@/lib/messages";
import "@fortawesome/fontawesome-svg-core/styles.css";
import "./globals.css";

// next.config.ts の CSP は script-src 'self' のみを許可するため、Font Awesome が実行時に
// スタイルを動的注入する挙動（autoAddCss）を止め、上の CSS import でビルド時にバンドルする。
config.autoAddCss = false;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: messages.site.title,
  description: messages.site.description,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ja"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/* アンバーバナー（デモ版であることの明示・全デモ共通） */}
        <div className="w-full bg-amber-600 px-4 py-1.5 text-center text-xs font-medium text-white">
          {messages.demo.banner}
        </div>

        <nav className="border-b border-zinc-200 bg-white">
          <div className="mx-auto flex h-14 max-w-2xl items-center justify-between px-6">
            <Link href="/" className="text-sm font-semibold text-zinc-900">
              {messages.demo.brandName}
            </Link>
            <a
              href="https://rictaworks.jp/#demos"
              className="border-l border-zinc-300 pl-4 text-xs text-zinc-500 hover:text-zinc-700"
            >
              {messages.demo.backToList}
            </a>
          </div>
        </nav>

        <div className="flex-1">{children}</div>

        <footer className="border-t border-zinc-200 px-6 py-4 text-center text-xs text-zinc-500">
          <Link href="/legal" className="hover:text-zinc-700">
            {messages.demo.legalLink}
          </Link>
          <span className="mx-2">|</span>
          <span>{messages.demo.copyright}</span>
        </footer>

        {/* 右下固定「ご相談はこちら」ボタン（全デモ共通） */}
        <a
          href="https://rictaworks.jp/"
          target="_blank"
          rel="noopener noreferrer"
          className="fixed right-6 bottom-6 z-50 flex items-center gap-2 rounded-full bg-zinc-900 px-4 py-2.5 text-xs font-semibold whitespace-nowrap text-white shadow-lg"
        >
          <FontAwesomeIcon icon={faCommentDots} />
          {messages.demo.consult}
        </a>

        {/* GA4（全デモ共通タグ） */}
        <Script src="https://www.googletagmanager.com/gtag/js?id=G-C04W1XKS16" strategy="afterInteractive" />
        <Script id="ga4-init" strategy="afterInteractive">{`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-C04W1XKS16');
        `}</Script>
      </body>
    </html>
  );
}
