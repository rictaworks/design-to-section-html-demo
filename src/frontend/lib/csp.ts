// Content-Security-Policy の組み立て。next.config.ts から使う純粋関数として切り出し、テスト可能にする。
//
// Next.js 16 (Turbopack) は script-src へのnonce自動付与に対応していないため、strict-dynamic/nonce
// 方式ではなく script-src 'unsafe-inline' を許容する（フレームワーク自身の hydration スクリプトが
// 動作しなくなるため）。他は 'self' に制限し、object-src・frame-src 等でプラグイン起動や
// クリックジャッキングを防ぐ。
//
// フロントエンドはブラウザから別オリジンの backend（NEXT_PUBLIC_BACKEND_URL）へ直接 fetch し、
// 元画像は fetch した Blob を URL.createObjectURL で表示する。そのため connect-src に backend の
// オリジン、img-src に blob: が必要（無いと本番で全通信が遮断され「通信に失敗しました」になる）。
export function buildContentSecurityPolicy(backendUrl: string | undefined): string {
  const backendOrigin = backendUrl ? new URL(backendUrl).origin : undefined;
  const connectSrc = ["'self'", backendOrigin].filter(Boolean).join(" ");

  return [
    "default-src 'self'",
    "img-src 'self' data: blob:",
    "style-src 'self' 'unsafe-inline'",
    "script-src 'self' 'unsafe-inline'",
    `connect-src ${connectSrc}`,
    "frame-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}
