# Claude Safety Rules

## 削除系コマンドの禁止（重要）

以下のルールはこのワークスペース内のすべての会話で絶対に守られる：

- Claude はファイルまたはディレクトリを削除するコマンドを一切生成してはならない。
  例：rm, rm -rf, rm *, rmdir, unlink, cache --delete,
      lftp mirror --delete, rsync --delete, git clean -df, find -delete 等。

- 削除が必要な場合でも、Claude は削除コマンドを提案せず、
  「手動で削除してください」といった説明に留めること。

- 削除の推奨・削除操作の自動判断も禁止。

- ssh / lftp / デプロイ系スクリプトを生成する場合でも、
  削除コマンドの生成は禁止。

これらはすべての会話・コード生成に適用される。

## シークレット管理（重要）

- `config/master.key` など機密ファイルを `git add` するコードを生成してはならない
- デプロイスクリプト・セットアップ手順でも同様
- シークレットは必ず環境変数（RAILS_MASTER_KEY 等）で渡すこと
- `.gitignore` への追加を確認する手順を必ずコードに含めること
- 初回コミット前に `git status` でステージング確認を促すこと

---

# CLAUDE.md

## 概要

デザイン画像（1ページ分のカンプ・PNG/JPEG/WebP）をアップロードすると、規則に基づく画像処理（OpenCV）でページを横方向の帯に分割し、各帯を定型セクション部品（ヘッダー・ヒーロー・特徴一覧・料金表・FAQ・ギャラリー等の12種）に対応付けて、レスポンシブなHTML初稿を1ファイルに組み立てて出力するデモ版展示物。

- AI・OCRは一切使用しない。判定はすべて決定的な規則ベース（同一画像から同一出力）
- 生成物は**初稿**であり、デザインの忠実な再現を目的としない。文字はプレースホルダ、装飾は対象外
- 判定には必ず信頼度を付与し、迷いがある箇所は注意事項として利用者に明示する
- 詳細仕様は [`requirements.md`](requirements.md) が正。本ファイルと矛盾する場合は requirements.md を優先する

## アーキテクチャ

| 層 | 技術 | デプロイ先 | 役割 |
|---|---|---|---|
| フロントエンド | Next.js（TypeScript） | Vercel（無料） | アップロード画面・変換結果画面・プレビュー・帯編集 |
| アプリケーション | Rails 8 API | Railway（無料） | セッション・変換レコード・帯編集・部品組み立て・SQLite管理 |
| 解析 | FastAPI（Python・OpenCV） | Railway（無料） | 正規化・帯分割・特徴抽出・種別判定・切り出し |

- 解析層（FastAPI）は状態を持たない。画像と指示を受け取り結果を返すのみ
- アプリケーション層と解析層の通信は自システム内通信であり、外部APIには該当しない
- DBはSQLite（Rails管理）。PostgreSQLは使用しない（requirements.md 2.3・13章）
- 認証・認可は設計に組み込まない。セッションキー（Cookie）をオーナーキーとして全テーブルに付与し、セッションをまたいだ参照・操作を一切許可しない（requirements.md 11章・21章）
- ドメイン：`design-to-section-html-demo.rictaworks.jp`（バックエンドは `*.up.railway.app` の隠しドメインのまま運用し、フロントの環境変数経由で参照する）
- 日次リセット：JST 03:00に全テーブル・画像・生成物を削除する（requirements.md 22章）

## 開発環境

**開発の正はWSL2（本人指定・2026-09-13）。** `~/github/rictaworks/design-to-section-html-demo` で作業する。Windows側 `D:\github\rictaworks\design-to-section-html-demo` はリポジトリ作成時（bootstrap）に生成したのみで、以降は未使用の想定（デプロイ作業等で必要になった場合のみ再利用する）。

- Rails・FastAPI・Next.jsをローカルのWSL2上で直接起動して開発する（他リポジトリのようなdocker-compose devコンテナが必要かは規模を見て判断する。現時点では未確定のため、実装着手時に構成を決める）
- テストはTDD厳守（plan > red test > coding > green test）
  - Rails: RSpec
  - FastAPI: pytest
  - Next.js: Vitest
  - フロントの手動確認はcurl・`wget --mirror`・Playwrightで行う
- アイコンはFont Awesomeを使用。絵文字は使用しない
- ネイティブの `alert()` / `confirm()` / `prompt()` は使用禁止
- 環境変数は `.env` を参照する（`.env.example` を元に作成済み。値は各自が設定する）
- 文字列リテラルは設定ファイル（config等）に分離し、ハードコード検出テストを書く
- フォールバック・黙った例外握りつぶしを禁止し、例外処理を明示的に書く
- 日本語版のみ開発する（多言語対応はしない）
- 時刻はJST、エンコードはUTF-8

## ブランチ運用

- `src/**` の変更は必ずブランチを切り、`gh pr create` でPRを作成する。mainへの直接pushは禁止
- `src/**` 以外（CLAUDE.md・`requirements.md`・`DOCS/`・`SPEC/`・`TASKS/`等のドキュメント）はmainへの直接pushを許可する
- コミット前に必ずセキュリティレビューを行う
- マージ前に必ず `reviewer` と `pr-checker` サブエージェントを実行する

## リポジトリ構成（推奨）

- `src/` … 実装本体（frontend / backend / analysis の3ディレクトリを想定）
- `SPEC/` … 仕様書・ER図・DFD・シーケンス図・クラス図・状態遷移図・ユースケース図（`requirements.md` に集約済みのためMermaidの追補が必要な場合のみ追加）
- `TASKS/` … タスク管理
- `DEBUG/` … バグ報告
- `WORK/` … 作業報告
- `ENV/DEVELOPMENT.md` … 開発環境
- `ENV/PRODUCTION.md` … 本番環境
- README.md・SPEC/には未実装のものを書かない

## リリースフロー

**非機能要件（requirements.md 20章）により、1 issue のワンショットで実装する。**

```
issue → setting & coding → security review → add, commit, push
      → reviewer & pr-checker → merge
      → code-review → audit & security-gate → release → report → user test
```

- デモ版の簡略フロー（後半省略）は**採用しない**。本プロジェクトのVercel/Railwayへの反映は root CLAUDE.md の原則どおりデスクトップからの手動実行であり、merge即本番反映の構成ではないため、フル工程を適用する
- GitHub Releasesのバージョン番号：メジャー2桁.マイナー2桁.デバッグ2桁（`01.01.00` を初期値とする）。タグは最初から `git tag -a`（注釈付き）
- release後に `code-review` スキルを実施する
- 全PRのユーザーテストはClaude Desktopの sandbox > chrome を使用する

## AIモデル分担（デモ版）

| フェーズ | 担当モデル |
|---|---|
| Issue分割 | Sonnet |
| 実装 | Haiku |
| reviewer, pr-checker | Sonnet |
| Security Review | Opus |
| コンテンツライティング | GPT |
| ファクトチェック | Gemini |

PRに投稿するときはフッターにモデル名を記載すること。

## デプロイ

- Cloudflare / Vercel / Railway への反映は常にデスクトップから実行する（root CLAUDE.md の原則）。Codespaces/WSL内のヘッドレスCLIのみでは、失敗時のBuild Logs/Deploy Logsの調査ができないため
- デプロイ用トークンは `H:\マイドライブ\RictaWorks\.deploy.enc`（DPAPI暗号化）で管理する

## 参照ドキュメント

- `.claude/CC.md` — コンプライアンス10項目
- `.claude/OWASP10.md` — OWASP Top 10
- `.claude/QC10.md` — 品質管理10項目
- `DOCS/CRAP.md` — デザイン4原則
- `DOCS/DP.md` — 設計指針（YAGNI/KISS/DRY/SOLID）
- `DOCS/TM.md` — テストメソッド概要
- `.claude/TEST-HARNESS-SAFETY.md` — テストハーネス安全性
- `requirements.md` — 仕様の正（本ファイルと矛盾する場合はこちらを優先）

## 連絡先

個人名は使用しない。メールは `info@rictaworks.jp`。
