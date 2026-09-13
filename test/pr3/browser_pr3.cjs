"use strict";
/**
 * PR #3 ユーザーテスト手順の実ブラウザ確認（Playwright）。
 * API経由の確認は test_pr3_api.py で行っているため、ここではAPIだけでは
 * 確認できない「見た目・実際の操作」に絞る:
 *   - 手順1: セッションCookieが保存され、再読み込みしても同じ変換が表示され続ける
 *   - 手順2: 非対応画像アップロード時のエラーメッセージ表示（回帰確認）
 *   - 手順7: 一覧⇄詳細を行き来しても壊れない
 *
 * 注記: test/pr2/browser_pr2.cjs の手順1で、components/NoticeList.tsx が
 * notice.detail（オブジェクト）をそのままJSXへ描画しており、通知が1件でも
 * ある変換では変換結果ページ全体がクラッシュする重大な不具合を発見した。
 * このバグはPR #3の変更範囲外だが、PR #3手順3(帯の分割・結合結果の確認)・
 * 手順4(フッター列数の確認)・手順5(プレビュー幅)・手順6(注意事項一覧)は
 * いずれも変換結果ページの描画に依存するため、同じ理由で実ブラウザでは
 * 検証できないことがある。該当する場合はその旨を明示して記録する
 * （modify・修正はここでは行わない）。
 *
 * 実行: node browser_pr3.cjs <fixtures_dir>
 * 前提: フロントエンド開発サーバー(:3000)・アプリケーション層(:3001)・
 * 解析層(:8001)が起動していること。fixtures_dir は gen_fixtures.py の出力先。
 */
const path = require("path");
const { FRONTEND_URL, check, assert, withBrowser, summary } = require(
  path.join(__dirname, "..", "support", "pw_helpers.cjs")
);

const fixturesDir = process.argv[2];
if (!fixturesDir) {
  console.error("usage: node browser_pr3.cjs <fixtures_dir>");
  process.exit(2);
}

async function main() {
  await withBrowser(async (context) => {
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(e.message));
    let conversionUrl = null;

    await check("手順1: アップロードが最後まで終わり、Cookieでセッションが保存される", async () => {
      await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
      await page.locator("#design-image").setInputFiles(path.join(fixturesDir, "multi_band.png"));
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/conversions\//, { timeout: 20000 });
      conversionUrl = page.url();

      const cookies = await context.cookies();
      const sessionCookie = cookies.find((c) => c.name === "design_to_html_session_id");
      assert(sessionCookie, "セッションCookieが発行されていること");
      assert(sessionCookie.sameSite === "Lax", `開発環境ではSameSite=Laxで発行されること (got ${sessionCookie.sameSite})`);
      assert(sessionCookie.secure === false, "開発環境ではSecure属性が付かないこと");
    });

    await check("手順1: ブラウザの再読み込みをしても同じ変換結果が表示され続ける（Cookie永続化）", async () => {
      assert(conversionUrl, "手順1のアップロードで変換結果ページに到達できていること");
      const beforeReloadCookies = await context.cookies();
      const sessionBefore = beforeReloadCookies.find((c) => c.name === "design_to_html_session_id")?.value;

      await page.reload({ waitUntil: "networkidle" });
      assert(page.url() === conversionUrl, "再読み込み後も同じURL(同じ変換)のままであること");

      const afterReloadCookies = await context.cookies();
      const sessionAfter = afterReloadCookies.find((c) => c.name === "design_to_html_session_id")?.value;
      assert(sessionAfter === sessionBefore, "再読み込みをしてもセッションCookieの値が変わらないこと");
    });

    await check("手順2: 対応していない画像を送った場合に、理由がわかるメッセージが表示される", async () => {
      await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
      await page.locator("#design-image").setInputFiles(path.join(fixturesDir, "design.gif"));
      await page.locator('button[type="submit"]').click();
      await page.waitForSelector("text=対応していないファイル形式です", { timeout: 10000 });
    });

    await check(
      "手順3〜6（帯編集・フッター列数・プレビュー幅・注意事項）: 変換結果ページが描画できる前提の確認",
      async () => {
        assert(conversionUrl, "変換結果ページのURLが必要");
        if (pageErrors.length > 0) {
          throw new Error(
            "test/pr2/browser_pr2.cjs 手順1で発見したNoticeListのクラッシュ不具合" +
              "（notice.detail がオブジェクトなのに文字列として描画しようとして例外になる）" +
              "により、通知を含むこの変換結果ページはブラウザ上で描画できず、帯の分割・結合結果や" +
              "フッター列数、プレビュー幅切替をここで実機確認することができない。" +
              "API経由の確認は test/pr3/test_pr3_api.py 側で別途実施済み。"
          );
        }
        await page.goto(conversionUrl, { waitUntil: "networkidle" });
        await page.waitForSelector("text=信頼度", { timeout: 8000 });
      }
    );

    await check("手順7: 一覧⇄詳細画面を行き来しても壊れない（HTTPレベルでの往復確認）", async () => {
      assert(conversionUrl, "変換結果ページのURLが必要");
      for (let i = 0; i < 3; i += 1) {
        const listResp = await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
        assert(listResp && listResp.ok(), `一覧画面の応答が正常であること (iteration ${i})`);

        const detailResp = await page.goto(conversionUrl, { waitUntil: "networkidle" });
        assert(detailResp && detailResp.ok(), `詳細画面の応答が正常であること (iteration ${i})`);
      }
    });

    await page.close();
  });
}

main()
  .then(() => process.exit(summary("PR3 browser (Playwright)")))
  .catch((err) => {
    console.error("browser_pr3.cjs crashed:", err);
    process.exit(1);
  });
