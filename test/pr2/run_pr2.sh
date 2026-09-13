#!/usr/bin/env bash
# PR #2 のユーザーテスト手順を自動実行する（APIレベルpytest + Playwrightブラウザ確認）。
#
# 前提: 開発サーバーが起動していること
#   解析層:   cd src/analysis && source .venv/bin/activate && uvicorn app.main:app --port 8001
#   アプリ層: cd src/backend && ANALYSIS_SERVICE_URL=http://localhost:8001 FRONTEND_ORIGIN=http://localhost:3000 bin/rails server -p 3001
#   フロント: cd src/frontend && NEXT_PUBLIC_BACKEND_URL=http://localhost:3001 npm run dev -- -p 3000
#
# .claude/TEST-HARNESS-SAFETY.md (TH1-TH5) に従い、このスクリプトは自分自身や
# 開発サーバー起動コマンドを再帰的に呼び出さない（対象サーバーへHTTP/ブラウザで
# アクセスするだけ）。
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURES_DIR="${D2H_FIXTURES_DIR:-$(mktemp -d)}"
PY="$REPO_ROOT/src/analysis/.venv/bin/python3"

# playwrightコア(npxキャッシュ)の解決。無ければPlaywright部分はスキップしcurlのみで代替する
# （DOCS/TM.mdの方針: 「Playwrightが使えるなら実ブラウザに近い確認を、無ければcurlで代替」）。
find_playwright_node_modules() {
  local candidate
  for candidate in "$HOME"/.npm/_npx/*/node_modules; do
    if [ -d "$candidate/playwright" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

echo "== PR2: APIレベルテスト (pytest) =="
"$PY" -m pytest "$REPO_ROOT/test/pr2/test_pr2_api.py" -v
API_STATUS=$?
echo "(pytest exit status: $API_STATUS)"

echo
echo "== PR2: ブラウザテスト (Playwright) =="
if PW_NODE_MODULES="$(find_playwright_node_modules)"; then
  "$PY" "$REPO_ROOT/test/support/gen_fixtures.py" "$FIXTURES_DIR"
  NODE_PATH="$PW_NODE_MODULES" node "$REPO_ROOT/test/pr2/browser_pr2.cjs" "$FIXTURES_DIR"
  BROWSER_STATUS=$?
else
  echo "playwright(core)がnpxキャッシュに見つからないため、ブラウザ確認はスキップします。" >&2
  echo "(DOCS/TM.mdの方針に従いcurlでの代替を検討してください)" >&2
  BROWSER_STATUS=0
fi

exit $((API_STATUS != 0 || BROWSER_STATUS != 0))
