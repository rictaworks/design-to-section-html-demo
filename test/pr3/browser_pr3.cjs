"use strict";
/**
 * PR #3 ユーザーテスト手順の実ブラウザ確認（Playwright）。
 * API経由の確認は test_pr3_api.py で行っているため、ここではAPIだけでは
 * 確認できない「見た目・実際の操作」に絞る:
 *   - 手順1: セッションCookieが保存され、再読み込みしても同じ変換が表示され続ける
 *   - 手順2: 非対応画像アップロード時のエラーメッセージ表示（回帰確認）
 *   - 手順3・6: 帯を実際にUI操作で分割し、新しくできた帯に注意事項が
 *     正しく紐付くこと（置換済みの旧帯を指さないこと）
 *   - 手順3: 種別変更操作でバリアント表示（見た目の型）が更新されること
 *   - 手順7: 一覧⇄詳細を行き来しても壊れない
 *
 * 更新履歴: 以前はここで components/NoticeList.tsx が notice.detail
 * （オブジェクト）をそのままJSXへ描画し、通知が1件でもある変換では変換結果
 * ページ全体がクラッシュする重大な不具合（PR #4で修正済み）のため、手順3〜6を
 * 「ページが描画できるかどうか」の前提確認に留めていた。PR #4適用後の今回は
 * 実際の帯編集操作まで踏み込んで確認する。
 *
 * 実行: node browser_pr3.cjs <fixtures_dir>
 * 前提: フロントエンド開発サーバー(:3000)・アプリケーション層(:3001)・
 * 解析層(:8001)が起動していること。fixtures_dir は gen_fixtures.py の出力先。
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

const MIN_BAND_HEIGHT_PX = 48;

// 注意: 単純な li:has-text('信頼度') は NoticeList側の文言（例:「種別判定の
// 信頼度がやや低いため…」）にも部分一致してしまうため、帯一覧セクションに
// 限定したロケータを使う。
function bandListItems(page) {
  return page.locator("section:has(h2:text-is('帯一覧')) li");
}

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

    let splitReplacedBandId = null;
    let splitNewBandIds = null;

    await check(
      "手順3・6: 中間の帯をUI操作で分割すると、新しくできた帯が一覧に現れ、注意事項が" +
        "置換済みの旧帯ではなく実在する帯を指す",
      async () => {
        assert(conversionUrl, "変換結果ページのURLが必要");
        await page.goto(conversionUrl, { waitUntil: "networkidle" });
        await page.waitForSelector("text=信頼度", { timeout: 8000 });
        assert(pageErrors.length === 0, `帯編集の前提としてページがクラッシュしていないこと: ${pageErrors.join(" / ")}`);

        const before = await fetchConversion(page, conversionUrl.split("/").pop());
        const beforeNoticeIds = new Set(before.notices.map((n) => n.id));
        const bands = [...before.bands].sort((a, b) => a.position - b.position);
        const lastPosition = bands[bands.length - 1].position;
        const candidates = bands.filter(
          (b) =>
            b.position !== 0 &&
            b.position !== lastPosition &&
            b.bottom_y - b.top_y > MIN_BAND_HEIGHT_PX * 2 + 4
        );
        assert(candidates.length > 0, "分割制約(帯端48px)を満たす十分な高さの中間帯が必要");
        const target = candidates.reduce((a, b) => (b.bottom_y - b.top_y > a.bottom_y - a.top_y ? b : a));
        const targetIndex = bands.findIndex((b) => b.id === target.id);
        const midY = Math.floor((target.top_y + target.bottom_y) / 2);
        splitReplacedBandId = target.id;

        const bandLis = bandListItems(page);
        const beforeCount = await bandLis.count();
        const targetLi = bandLis.nth(targetIndex);
        await targetLi.locator('input[type="number"]').fill(String(midY));
        await targetLi.getByRole("button", { name: "分割", exact: true }).click();

        await page.waitForFunction(
          (prevCount) => {
            const heading = Array.from(document.querySelectorAll("h2")).find(
              (h) => h.textContent === "帯一覧"
            );
            const section = heading ? heading.closest("section") : null;
            const bandLisNow = section ? section.querySelectorAll("li").length : 0;
            return bandLisNow === prevCount + 1;
          },
          beforeCount,
          { timeout: 15000 }
        );
        assert(pageErrors.length === 0, `分割操作後もページがクラッシュしないこと: ${pageErrors.join(" / ")}`);

        const afterCount = await bandLis.count();
        assert(afterCount === beforeCount + 1, `分割で帯が1つ増えること (got ${beforeCount} -> ${afterCount})`);

        const after = await fetchConversion(page, conversionUrl.split("/").pop());
        const afterIds = new Set(after.bands.map((b) => b.id));
        assert(!afterIds.has(splitReplacedBandId), "分割元の帯は一覧(bands)から消えている(state=replaced)こと");

        const beforeIds = new Set(bands.map((b) => b.id));
        splitNewBandIds = after.bands.filter((b) => !beforeIds.has(b.id)).map((b) => b.id);
        assert(splitNewBandIds.length === 2, `分割で新しく2つの帯が作られること (got ${splitNewBandIds.length})`);

        // PR #4修正の核心部分: refeature応答由来の「新規」注意事項(=分割操作で今回
        // 初めて作られたもの)が、position重複によって置換済みの旧帯を指してしまわない
        // こと。分割前から存在していた注意事項(その帯が作られた当初からの
        // low_confidence_kind等)は対象外にする(下の別checkで扱う)。
        const newNotices = after.notices.filter((n) => !beforeNoticeIds.has(n.id));
        const newStaleNotices = newNotices.filter((n) => n.band_id === splitReplacedBandId);
        assert(
          newStaleNotices.length === 0,
          "分割操作で新規に発行された注意事項が、置換済みで一覧から消えた旧帯を指してしまって" +
            `いないこと(position重複によるnotice/band紐付け誤りの修正確認): ${JSON.stringify(newStaleNotices)}`
        );
        for (const notice of newNotices) {
          if (notice.band_id !== null) {
            assert(
              afterIds.has(notice.band_id),
              `分割操作で新規に発行された注意事項のband_idは、実在するこの変換内の帯を指すこと (band_id=${notice.band_id})`
            );
          }
        }
      }
    );

    await check(
      "手順6（PR #5の回帰テスト）: 分割前から存在していた注意事項が、置換された旧帯を指したまま一覧に残り続けないこと",
      async () => {
        // test/pr3/test_pr3_api.py の
        // test_step6_split_notices_reference_the_new_child_band_not_the_replaced_original
        // と同じ観点。分割対象の帯が元々持っていた注意事項(その帯の初回作成時に
        // band_idで直接紐付けたもの)は、帯がstate=replacedになった後も一覧に
        // 残り続けることがあったが、PR #5（conversion_presenter.rbのpresentable_notices）
        // で修正済み。このcheckが失敗する場合はPR #5の退行を意味する。
        assert(splitReplacedBandId, "直前のcheckで分割操作が行われている必要がある");
        const after = await fetchConversion(page, conversionUrl.split("/").pop());
        const orphanedNotices = after.notices.filter((n) => n.band_id === splitReplacedBandId);
        assert(
          orphanedNotices.length === 0,
          "置換済みで一覧から消えた旧帯を指す注意事項が残っていないこと: " + JSON.stringify(orphanedNotices)
        );
      }
    );

    await check(
      "手順3: 帯の種別を変更するとバリアント表示（見た目の型）も更新される",
      async () => {
        assert(conversionUrl, "変換結果ページのURLが必要");
        assert(pageErrors.length === 0, "帯編集の前提としてページがクラッシュしていないこと");

        const current = await fetchConversion(page, conversionUrl.split("/").pop());
        const bands = [...current.bands].sort((a, b) => a.position - b.position);
        const lastIndex = bands.length - 1;

        const bandLis = bandListItems(page);
        const targetLi = bandLis.nth(lastIndex);
        const variantBefore = (await targetLi.locator("text=バリアント").innerText()).trim();

        await targetLi.locator("select").selectOption("footer");

        await page.waitForFunction(
          (prevText) => {
            const heading = Array.from(document.querySelectorAll("h2")).find(
              (h) => h.textContent === "帯一覧"
            );
            const section = heading ? heading.closest("section") : null;
            const lis = section ? Array.from(section.querySelectorAll("li")) : [];
            const target = lis[lis.length - 1];
            if (!target) return false;
            const variantSpan = Array.from(target.querySelectorAll("span")).find(
              (s) => s.textContent && s.textContent.includes("バリアント")
            );
            return variantSpan && variantSpan.textContent !== prevText;
          },
          variantBefore,
          { timeout: 15000 }
        );

        const variantAfter = (await bandLis.nth(lastIndex).locator("text=バリアント").innerText()).trim();
        assert(variantAfter !== variantBefore, `種別変更後にバリアント表示が更新されること (${variantBefore} -> ${variantAfter})`);
        assert(
          variantAfter.includes("col_"),
          `footerへの種別変更後は列数バリアント(col_N)が表示されること: ${variantAfter}`
        );
        assert(pageErrors.length === 0, "種別変更後もページがクラッシュしないこと");
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
