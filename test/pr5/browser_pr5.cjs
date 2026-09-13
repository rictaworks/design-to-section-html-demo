"use strict";
/**
 * PR #5（マージ済み・01.01.03リリース）で直した「見た目に関わる修正」が、現在のmasterの
 * 実サーバー・実ブラウザ（Playwright）で正しく表示され続けているかの最終確認。
 * 単体テスト（RSpec/pytest/Vitest）では検出できない視覚的な不具合の有無だけを見る
 * （tester サブエージェントの最終チェック依頼）。
 *
 * 確認する4項目:
 *   1. 証言(testimonials)セクションの円形切り出し画像が壊れたアイコンにならず表示される
 *      （image/jpeg宣言修正・crops配列参照修正の確認）
 *   2. CTA帯のダーク/ライト両バリアントで文字色と背景色のコントラストが十分ある
 *      （共通配色ヘルパー(text_color_class)への統一の副作用確認）
 *   3. フッターセクションが画面中央に適切な余白を持つ（グリッドCSS崩れ修正の確認）
 *   4. 帯編集（種別変更）を3〜4回連続で行っても注意事項欄が壊れず、件数が異常に
 *      増え続けない（variant_mismatch_fallback重複蓄積バグの回帰確認）
 *
 * 実行: node browser_pr5.cjs <fixtures_dir>
 * 前提: フロントエンド(:3000)・アプリケーション層(:3001)・解析層(:8001)が起動していること。
 * fixtures_dir は gen_fixtures_pr5.py の出力先（testimonials_page.png を含む）。
 *
 * .claude/TEST-HARNESS-SAFETY.md (TH1-TH5) に従い、このスクリプトは自分自身や
 * 開発サーバー起動コマンドを再帰的に呼び出さない。
 */
const path = require("path");
const { FRONTEND_URL, check, assert, withBrowser, summary } = require(
  path.join(__dirname, "..", "support", "pw_helpers.cjs")
);

const BACKEND_URL = process.env.D2H_BACKEND_URL || "http://localhost:3001";

async function fetchConversion(page, conversionId) {
  return page.evaluate(
    async ({ backendUrl, conversionId }) => {
      const res = await fetch(`${backendUrl}/conversions/${conversionId}`, { credentials: "include" });
      return res.json();
    },
    { backendUrl: BACKEND_URL, conversionId }
  );
}

function relLuminance([r, g, b]) {
  const chan = (c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  const [rl, gl, bl] = [chan(r), chan(g), chan(b)];
  return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
}

function parseRgb(str) {
  const m = str.match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const parts = m[1].split(",").map((s) => parseFloat(s.trim()));
  return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
}

function contrastRatio(rgbA, rgbB) {
  const lA = relLuminance([rgbA.r, rgbA.g, rgbA.b]);
  const lB = relLuminance([rgbB.r, rgbB.g, rgbB.b]);
  const [lighter, darker] = lA >= lB ? [lA, lB] : [lB, lA];
  return (lighter + 0.05) / (darker + 0.05);
}

const fixturesDir = process.argv[2];
if (!fixturesDir) {
  console.error("usage: node browser_pr5.cjs <fixtures_dir>");
  process.exit(2);
}

async function main() {
  await withBrowser(async (context) => {
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(e.message));
    let conversionUrl = null;
    let conversionId = null;

    await check("前提: 証言セクション付きデザイン画像をアップロードし、変換結果画面に到達する", async () => {
      await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
      await page.locator("#design-image").setInputFiles(path.join(fixturesDir, "testimonials_page.png"));
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/conversions\//, { timeout: 20000 });
      conversionUrl = page.url();
      conversionId = conversionUrl.split("/").pop();

      // stateがready(assembled)になり、outputが生成されるまで待つ。
      await page.waitForFunction(
        async ({ backendUrl, conversionId }) => {
          const res = await fetch(`${backendUrl}/conversions/${conversionId}`, { credentials: "include" });
          const data = await res.json();
          return data.state === "ready" && !!data.output;
        },
        { backendUrl: BACKEND_URL, conversionId },
        { timeout: 30000 }
      );

      const conv = await fetchConversion(page, conversionId);
      const kinds = conv.bands.map((b) => b.kind);
      assert(kinds.includes("testimonials"), `証言帯(testimonials)が検出されていること (got kinds=${kinds.join(",")})`);
      assert(kinds.includes("cta"), `行動喚起帯(cta)が検出されていること (got kinds=${kinds.join(",")})`);
      assert(kinds.includes("footer"), `フッター帯(footer)が検出されていること (got kinds=${kinds.join(",")})`);
    });

    await check(
      "項目1: 証言セクションの円形切り出し画像が壊れたアイコンにならず実際に表示される",
      async () => {
        await page.reload({ waitUntil: "networkidle" });
        const frame = page.frameLocator('iframe[title*="デスクトップ"]');
        const avatars = frame.locator(".d2h-testimonials__avatar");
        const count = await avatars.count();
        assert(count >= 1, `証言セクションのアバター画像がプレビューDOM内に存在すること (got ${count})`);

        for (let i = 0; i < count; i += 1) {
          const img = avatars.nth(i);
          const src = await img.getAttribute("src");
          assert(src && src.startsWith("data:image/jpeg;base64,"), `avatar[${i}]のsrcがdata:image/jpeg;base64,で始まること: ${src && src.slice(0, 30)}`);

          const dims = await img.evaluate((el) => {
            return new Promise((resolve) => {
              if (el.complete) {
                resolve({ naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight });
                return;
              }
              el.addEventListener("load", () =>
                resolve({ naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight })
              );
              el.addEventListener("error", () => resolve({ naturalWidth: 0, naturalHeight: 0 }));
            });
          });
          assert(
            dims.naturalWidth > 0 && dims.naturalHeight > 0,
            `avatar[${i}]がブラウザで実際にデコードできる画像であること（壊れたアイコンでないこと）: naturalWidth=${dims.naturalWidth} naturalHeight=${dims.naturalHeight}`
          );
        }
      }
    );

    await check(
      "項目2: CTA帯のダーク/ライト両バリアントで文字色と背景色のコントラストが十分ある",
      async () => {
        const frame = page.frameLocator('iframe[title*="デスクトップ"]');

        const onDark = frame.locator('.d2h-cta[class*="--on-dark"]');
        const onLight = frame.locator('.d2h-cta[class*="--on-light"]');
        const onDarkCount = await onDark.count();
        const onLightCount = await onLight.count();
        assert(onDarkCount >= 1, `on-darkのCTA帯が1つ以上存在すること (got ${onDarkCount})`);
        assert(onLightCount >= 1, `on-lightのCTA帯が1つ以上存在すること (got ${onLightCount})`);

        async function checkContrast(locator, label) {
          const { bg, fg } = await locator.evaluate((el) => {
            function resolveBg(node) {
              let cur = node;
              while (cur) {
                const c = getComputedStyle(cur).backgroundColor;
                const m = c.match(/rgba?\(([^)]+)\)/);
                if (m) {
                  const parts = m[1].split(",").map((s) => parseFloat(s.trim()));
                  if (!(parts.length > 3 && parts[3] === 0)) return c;
                }
                cur = cur.parentElement;
              }
              return "rgb(255,255,255)";
            }
            const style = getComputedStyle(el);
            return { bg: resolveBg(el), fg: style.color };
          });
          const bgRgb = parseRgb(bg);
          const fgRgb = parseRgb(fg);
          assert(bgRgb && fgRgb, `${label}: 背景色・文字色が取得できること (bg=${bg}, fg=${fg})`);
          const ratio = contrastRatio(bgRgb, fgRgb);
          assert(
            ratio >= 4.5,
            `${label}: 背景色(${bg})と文字色(${fg})のコントラスト比がWCAG AA相当(4.5)以上であること (got ${ratio.toFixed(2)})`
          );
        }

        await checkContrast(onDark.first(), "CTA(on-dark)");
        await checkContrast(onLight.first(), "CTA(on-light)");
      }
    );

    await check(
      "項目3: フッターセクションが画面中央に適切な余白を持って表示される",
      async () => {
        const frame = page.frameLocator('iframe[title*="デスクトップ"]');
        const columns = frame.locator(".d2h-footer__columns");
        await columns.first().waitFor({ state: "attached" });

        const metrics = await columns.first().evaluate((el) => {
          const style = getComputedStyle(el);
          const rect = el.getBoundingClientRect();
          const viewportWidth = document.documentElement.clientWidth;
          return {
            display: style.display,
            maxWidth: style.maxWidth,
            marginLeft: style.marginLeft,
            marginRight: style.marginRight,
            paddingLeft: style.paddingLeft,
            paddingRight: style.paddingRight,
            left: rect.left,
            right: rect.right,
            viewportWidth,
          };
        });

        assert(metrics.display === "grid", `フッター列がgrid表示であること (got ${metrics.display})`);
        assert(metrics.maxWidth === "1200px", `max-width:1200pxが効いていること (got ${metrics.maxWidth})`);
        assert(
          parseFloat(metrics.paddingLeft) > 0 && parseFloat(metrics.paddingRight) > 0,
          `左右にpaddingがあり、画面端にべったりくっついていないこと (paddingLeft=${metrics.paddingLeft}, paddingRight=${metrics.paddingRight})`
        );
        // margin:0 auto による中央寄せ: デスクトップ幅(1280px) > max-width(1200px)なので
        // 左右に余白ができ、その余白がほぼ等しいはず（中央寄せの確認）。
        const leftGap = metrics.left;
        const rightGap = metrics.viewportWidth - metrics.right;
        assert(
          Math.abs(leftGap - rightGap) <= 2,
          `フッター列が画面中央に寄っていること（左右の余白がほぼ等しいこと）: leftGap=${leftGap.toFixed(1)} rightGap=${rightGap.toFixed(1)}`
        );
      }
    );

    let toggleBandId = null;
    const noticeCountHistory = [];
    const variantMismatchCountHistory = [];

    await check(
      "項目4準備: 帯編集を繰り返す対象の帯を選ぶ",
      async () => {
        const conv = await fetchConversion(page, conversionId);
        const bands = [...conv.bands].sort((a, b) => a.position - b.position);
        // 先頭・末尾(header/footer)以外の帯を選ぶ。種別変更を繰り返しても
        // ページ構造(h1が1つ等)が壊れないようにするため。
        const target = bands.find((b) => b.position !== 0 && b.position !== bands.length - 1);
        assert(target, "種別変更対象にできる中間の帯が必要");
        toggleBandId = target.id;
      }
    );

    await check(
      "項目4: 帯編集（種別変更）を4回連続で行っても、注意事項欄が壊れたり件数が異常に増え続けたりしない",
      async () => {
        assert(pageErrors.length === 0, `帯編集の前提としてページがクラッシュしていないこと: ${pageErrors.join(" / ")}`);
        const kindsToCycle = ["gallery", "features", "gallery", "features"];

        for (let i = 0; i < kindsToCycle.length; i += 1) {
          const kind = kindsToCycle[i];
          const select = page.locator(`#kind-${toggleBandId}`);
          await select.selectOption(kind);

          await page.waitForFunction(
            async ({ backendUrl, conversionId, bandId, kind }) => {
              const res = await fetch(`${backendUrl}/conversions/${conversionId}`, { credentials: "include" });
              const data = await res.json();
              const band = data.bands.find((b) => b.id === bandId);
              return band && band.kind === kind && data.output;
            },
            { backendUrl: BACKEND_URL, conversionId, bandId: toggleBandId, kind },
            { timeout: 15000 }
          );

          assert(pageErrors.length === 0, `種別変更(${i + 1}回目: ${kind})後もページがクラッシュしないこと: ${pageErrors.join(" / ")}`);

          const conv = await fetchConversion(page, conversionId);
          const ids = conv.notices.map((n) => n.id);
          const uniqueIds = new Set(ids);
          assert(
            uniqueIds.size === ids.length,
            `注意事項一覧に重複したidが無いこと(${i + 1}回目): ids=${JSON.stringify(ids)}`
          );

          noticeCountHistory.push(conv.notices.length);
          variantMismatchCountHistory.push(
            conv.notices.filter((n) => n.notice_type === "variant_mismatch_fallback").length
          );

          // NoticeListが実際に描画され続けていること(DOM上でクラッシュしていないこと)の確認。
          await page.waitForSelector("h2:text-is('注意事項')", { timeout: 5000 });
        }

        console.log(`    notices.length の推移: ${noticeCountHistory.join(" -> ")}`);
        console.log(`    variant_mismatch_fallback件数の推移: ${variantMismatchCountHistory.join(" -> ")}`);

        // 同じ2つの種別を往復しているだけなので、注意事項の総数は最終的に頭打ちになり、
        // 操作のたびに際限なく増え続けてはいけない(PR #5で修正されたバグの回帰確認)。
        const last = noticeCountHistory[noticeCountHistory.length - 1];
        const secondLast = noticeCountHistory[noticeCountHistory.length - 2];
        assert(
          last <= secondLast,
          `同じ操作(種別変更の往復)を繰り返しても注意事項の総数が増え続けないこと: ${JSON.stringify(noticeCountHistory)}`
        );

        const vmLast = variantMismatchCountHistory[variantMismatchCountHistory.length - 1];
        const vmSecondLast = variantMismatchCountHistory[variantMismatchCountHistory.length - 2];
        assert(
          vmLast <= vmSecondLast,
          `variant_mismatch_fallback注意事項が重複蓄積しないこと: ${JSON.stringify(variantMismatchCountHistory)}`
        );
      }
    );

    await page.close();
  });
}

main()
  .then(() => process.exit(summary("PR5 final visual check (Playwright)")))
  .catch((err) => {
    console.error("browser_pr5.cjs crashed:", err);
    process.exit(1);
  });
