"use strict";
/**
 * PR #2 ユーザーテスト手順の実ブラウザ確認（Playwright）。
 * API経由の確認は test_pr2_api.py で行っているため、ここではAPIだけでは
 * 確認できない「見た目・実際の操作」に絞る:
 *   - 手順1: アップロード→帯オーバーレイ・帯一覧（種別名・信頼度・バリアント）表示
 *   - 手順2: 非対応画像アップロード時のエラーメッセージ表示（画面が固まらない）
 *   - 手順3: 種別変更操作でプレビューの版が進む
 *   - 手順4: モバイル/タブレット/デスクトップ幅の切り替え
 *   - 手順7: ダウンロードしたHTMLをfile://で単体表示できる
 *
 * 実行: node browser_pr2.cjs <fixtures_dir>
 * 前提: フロントエンド開発サーバー(:3000)・アプリケーション層(:3001)・
 * 解析層(:8001)が起動していること。fixtures_dir は gen_fixtures.py の出力先。
 */
const path = require("path");
const fs = require("fs");
const { FRONTEND_URL, check, assert, withBrowser, summary } = require(
  path.join(__dirname, "..", "support", "pw_helpers.cjs")
);

const fixturesDir = process.argv[2];
if (!fixturesDir) {
  console.error("usage: node browser_pr2.cjs <fixtures_dir>");
  process.exit(2);
}

async function main() {
  await withBrowser(async (context) => {
    const page = await context.newPage();
    let conversionUrl = null;

    // このセッション中に発生したクライアント側の未捕捉例外を記録する。
    // NoticeList のバグ（下記）に一度でも遭遇すると、そのページ全体が
    // React的に壊れ、以降の帯一覧・プレビュー確認が続けられなくなるため、
    // 「なぜタイムアウトしたか」を後続チェックでも明示できるようにしておく。
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(e.message));

    await check("手順1: PNGアップロードで帯分割・種別名・信頼度・バリアントが表示される", async () => {
      await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
      await page.locator("#design-image").setInputFiles(path.join(fixturesDir, "multi_band.png"));
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/conversions\//, { timeout: 20000 });
      conversionUrl = page.url();

      try {
        await page.waitForSelector("text=信頼度", { timeout: 8000 });
      } catch (timeoutErr) {
        if (pageErrors.length > 0) {
          throw new Error(
            "変換結果ページがクライアント側の例外でクラッシュし、帯一覧が表示されない。" +
              `検出した例外: ${pageErrors.join(" / ")}` +
              "（原因調査: components/NoticeList.tsx が notice.detail をそのままJSXの子要素として" +
              "描画しているが、実際のAPIレスポンスの notice.detail はオブジェクト" +
              '（例: {"kind":"header"}）であり文字列ではない。lib/types.ts の Notice.detail: string 型・' +
              "NoticeList.test.tsx のモックは文字列のdetailを前提にしており、この型不一致が" +
              "テスト側では検出されていなかった。通知が1件でも存在する変換では、" +
              "変換結果ページ全体が描画できなくなる重大な不具合。)"
          );
        }
        throw timeoutErr;
      }

      const bandCount = await page.locator("li:has-text('信頼度')").count();
      assert(bandCount >= 1, `帯が1つ以上表示されること (got ${bandCount})`);
      const variantLabelCount = await page.locator("text=バリアント").count();
      assert(variantLabelCount >= 1, "バリアント（見た目の型）ラベルが表示されること");

      // 帯オーバーレイ（デザイン画像に重なる帯の区切り・名前表示）
      const overlayImg = await page.locator('img[alt="デザイン画像"]').count();
      assert(overlayImg >= 1, "デザイン画像のオーバーレイ表示があること");
    });

    await check("手順2: GIF（非対応形式）アップロードでエラーメッセージが日本語で表示される", async () => {
      await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
      await page.locator("#design-image").setInputFiles(path.join(fixturesDir, "design.gif"));
      await page.locator('button[type="submit"]').click();
      await page.waitForSelector("text=対応していないファイル形式です", { timeout: 10000 });

      const bodyText = (await page.locator("body").innerText()).trim();
      assert(bodyText.length > 0, "画面が真っ白にならないこと");
      assert(page.url() === FRONTEND_URL || page.url() === `${FRONTEND_URL}/`, "アップロード画面に留まること");
    });

    await check("手順3: 帯の種別を変更するとプレビューの版が進み、内容が変わる", async () => {
      assert(conversionUrl, "手順1で変換結果ページのURLを取得できていること");
      if (pageErrors.length > 0) {
        throw new Error(
          "手順1で検出したページクラッシュ（NoticeListの不具合）により、この変換結果ページは" +
            "帯編集操作を試せる状態まで到達できない（上記手順1のFAILを参照）"
        );
      }
      await page.goto(conversionUrl, { waitUntil: "networkidle" });
      await page.waitForSelector("text=版", { timeout: 10000 });

      const versionTextBefore = await page.locator("h2:has-text('版')").first().innerText();

      const firstSelect = page.locator("select").first();
      const currentValue = await firstSelect.inputValue();
      const optionValues = await firstSelect.locator("option").evaluateAll((els) => els.map((e) => e.value));
      const nextValue = optionValues.find((v) => v !== currentValue);
      assert(nextValue, "現在と異なる種別が選べること");
      await firstSelect.selectOption(nextValue);

      await page.waitForFunction(
        (prevText) => {
          const h2s = Array.from(document.querySelectorAll("h2"));
          const target = h2s.find((h) => h.textContent && h.textContent.includes("版"));
          return target && target.textContent !== prevText;
        },
        versionTextBefore,
        { timeout: 15000 }
      );
      const versionTextAfter = await page.locator("h2:has-text('版')").first().innerText();
      assert(versionTextAfter !== versionTextBefore, "種別変更のたびに版番号が進むこと");
    });

    await check("手順4: モバイル/タブレット/デスクトップの3幅でプレビュー表示が切り替わる", async () => {
      assert(conversionUrl, "変換結果ページのURLが必要");
      if (pageErrors.length > 0) {
        throw new Error("手順1で検出したページクラッシュにより、プレビュー幅切替が試せない");
      }
      await page.goto(conversionUrl, { waitUntil: "networkidle" });
      await page.waitForSelector("iframe", { timeout: 15000 });

      const widths = { モバイル: "375", タブレット: "768", デスクトップ: "1280" };
      for (const [label, px] of Object.entries(widths)) {
        await page.getByRole("button", { name: label, exact: true }).click();
        await page.waitForFunction(() => document.querySelectorAll("iframe").length === 1, { timeout: 5000 });
        const style = await page.locator("iframe").first().getAttribute("style");
        assert(style && style.includes(`${px}px`), `${label}選択時、iframe幅が${px}pxであること: ${style}`);
      }

      await page.getByRole("button", { name: "プレビュー", exact: true }).click();
      await page.waitForFunction(() => document.querySelectorAll("iframe").length === 3, { timeout: 5000 });
    });

    await check("手順7: HTMLをダウンロードし、file://で単体表示すると外部参照・scriptなしで開ける", async () => {
      assert(conversionUrl, "変換結果ページのURLが必要");
      if (pageErrors.length > 0) {
        throw new Error("手順1で検出したページクラッシュにより、ダウンロード操作が試せない");
      }
      await page.goto(conversionUrl, { waitUntil: "networkidle" });
      await page.waitForSelector("text=HTMLファイルをダウンロード", { timeout: 10000 });

      const downloadPromise = page.waitForEvent("download");
      await page.getByRole("button", { name: "HTMLファイルをダウンロード" }).click();
      const download = await downloadPromise;
      const savePath = path.join(fixturesDir, "pr2_downloaded.html");
      await download.saveAs(savePath);

      const html = fs.readFileSync(savePath, "utf-8");
      assert(!/<script/i.test(html), "script要素が含まれないこと");
      assert(!/https?:\/\//.test(html), "http(s)://への外部参照が含まれないこと");
      assert((html.match(/<h1[ >]/gi) || []).length === 1, "h1が1つだけであること");
      assert(/プレースホルダー/.test(html), "文言がプレースホルダーであること（実データを写し取らない）");

      const filePage = await context.newPage();
      const fileErrors = [];
      filePage.on("pageerror", (e) => fileErrors.push(e.message));
      await filePage.goto("file://" + path.resolve(savePath));
      const h1Count = await filePage.locator("h1").count();
      assert(h1Count === 1, "file://で開いた単体HTMLにh1が1つ表示されること");
      assert(fileErrors.length === 0, `ページ内エラーが出ないこと: ${fileErrors.join(", ")}`);
      await filePage.close();
    });

    await page.close();
  });
}

main()
  .then(() => process.exit(summary("PR2 browser (Playwright)")))
  .catch((err) => {
    console.error("browser_pr2.cjs crashed:", err);
    process.exit(1);
  });
