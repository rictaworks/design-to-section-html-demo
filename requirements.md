# デザイン画像→レスポンシブHTML初稿 変換ツール（デモ版）仕様書

リポジトリ名：**`design-to-section-html-demo`**

---

## 1. 概要

### 1.1 課題

ランディングページやコーポレートサイトの 1 ページ分のデザイン画像（カンプ）をアップロードすると、ページを横方向の帯に分割し、各帯を定型セクション部品（ヘッダー・ヒーロー・特徴一覧・料金表・FAQ・フッター等）に対応付け、レスポンシブな HTML 初稿を 1 ファイルとして組み上げる。

デザインから HTML を手組みする作業は、セクション構造の把握と骨組みづくりに時間の大半が費やされる。本成果物は、画像の解析を規則に基づく画像処理で行い、部品カタログの組み合わせで初稿を生成することで、着手の壁を下げる体験を展示するものである。

### 1.2 対象エディション

**デモ版（アイデアの視覚化）**

技術と UX を体験させる展示物として、安全・手軽に動かせることを最優先する。デザイン・測定・保守・監視は対象外とする。

### 1.3 生成物の位置づけ

生成物は **初稿** であり、デザインの忠実な再現を目的としない。文字はプレースホルダ、画像は元画像からの切り出し、細部の装飾は対象外とし、利用者による手直しを前提とする。判定には必ず信頼度を付与し、判定に迷いがある箇所は注意事項として明示する。

---

## 2. プラットフォーム選定

### 2.1 ターゲットの判別

成果物を直接操作し、生成物を閲覧・取得するのは**人間**である。よってターゲットは人間向けとする。

### 2.2 プラットフォーム

**ウェブ** を選択する。

- 画像を入力し、解析結果と手直しに応じて出力が変わる動的処理であるため、電子書籍・動画は該当しない
- 生成物が HTML であり、ブラウザ内で即座にプレビューできることが提供価値の中核である
- インストール不要で展示物として手軽に体験できる
- デスクトップ＋ローカル LLM も検討したが、既定のローカルモデルは画像入力を持たず、かつ本課題は規則に基づく画像処理で成立するため LLM を要しない

### 2.3 構成方針

デモ版の簡略構成（Cloudflare 一本化）は **選択しない**。画像解析を伴うため、CRUD・表示が主体の構成に該当しないためである。

Next + Rails を基本とし、解析・画像加工を担う層として FastAPI を追加する。

| 層 | 技術 | デプロイ先 | 役割 |
|---|---|---|---|
| フロントエンド | Next.js（TypeScript） | Vercel（無料） | アップロード画面・変換結果画面・プレビュー |
| アプリケーション | Rails | Railway（無料） | セッション・変換レコード・帯編集・部品組み立て・SQLite の管理 |
| 解析 | FastAPI（Python・OpenCV） | Railway（無料） | 正規化・帯分割・特徴抽出・種別判定・切り出し |

解析層は状態を持たず、画像と指示を受け取り結果を返すのみとする。解析層とアプリケーション層の通信は自システム内の通信であり、外部 API に該当しない。AI サービス・OCR サービス等のネットワーク越しの呼び出しは行わない。

DB は SQLite とし、Rails のみが保持する。

---

## 3. 用語定義

| 用語 | 定義 |
|---|---|
| デザイン画像 | 利用者がアップロードする 1 ページ分のカンプ画像 |
| 作業画像 | デザイン画像を作業幅へ縮小した解析用の画像 |
| 帯 | ページを横方向に区切った領域。1 帯が 1 セクションに対応する |
| 区切り | 帯と帯の境界となる行位置 |
| ブロブ | 作業画像内で背景と区別される連結領域 |
| 帯特徴 | 帯ごとに算出する列数・反復項目数・画像位置・整列・背景色等の値の集合 |
| セクション種別 | 帯に割り当てる定型分類。部品カタログの 12 種のいずれか |
| 部品 | セクション種別ごとに用意された HTML/CSS のテンプレート |
| バリアント | 部品の中で列数・画像位置等により切り替わる形 |
| 外殻レイアウト | ページ全体の骨格。単一カラムとサイドバーの 2 種 |
| 切り出し画像 | 画像状ブロブの領域をデザイン画像から切り出した画像 |
| 初稿 | 組み立てられた単一の HTML ファイル |
| 版 | 初稿の世代。帯編集のたびに進む |
| 信頼度 | 種別判定の確からしさ。0 から 1 |
| 注意事項 | 判定や生成に迷い・妥協があった箇所を利用者へ伝える記録 |
| セッションキー | ブラウザごとに発行される不透明識別子。DB レコードのオーナーキー |

---

## 4. スコープ

### 4.1 対象

- 単一ページ・縦スクロール型のデザイン画像（PNG・JPEG・WebP）の受入
- 帯分割・帯特徴抽出・セクション種別判定
- 部品カタログによる HTML 初稿の組み立てと、単一ファイルとしてのダウンロード
- 3 つの幅でのプレビュー
- 帯の種別変更・結合・分割・削除と再組み立て
- ライト／ダーク両テーマ、デスクトップ幅／モバイル幅の両デザイン

### 4.2 対象外

- 文字の読み取り（OCR）。文字は長さ区分に応じたプレースホルダとする
- AI による判定・生成
- ピクセル単位での忠実な再現、装飾の再現
- 複数ページ・複数画面の一括変換
- 生成物内の JavaScript 動作、外部リソースの参照
- 画像・生成物の永続保存（日次リセットで消去する）
- ユーザー認証・認可

---

## 5. システム構成

```mermaid
flowchart LR
  subgraph BR["ブラウザ"]
    UP["アップロード画面"]
    RS["変換結果画面"]
    PV["プレビュー（3幅）"]
    ED["帯編集"]
  end

  subgraph APP["アプリケーション（Rails / Railway）"]
    API["変換 API"]
    ASM["部品組み立て"]
    CAT["部品カタログ"]
    VAL["生成物検証"]
    DB[("SQLite")]
  end

  subgraph ANA["解析（FastAPI / Railway）"]
    NRM["正規化"]
    SEG["帯分割"]
    FEA["特徴抽出"]
    CLS["種別判定"]
    CRP["切り出し"]
  end

  UP -->|"画像 + ハニーポット"| API
  ED -->|"種別変更 / 結合 / 分割 / 削除"| API
  API -->|"画像 / 帯範囲"| NRM
  NRM --> SEG --> FEA --> CLS --> CRP
  CRP -->|"帯・特徴・種別・切り出し"| API
  API --> ASM
  CAT --> ASM
  ASM --> VAL
  VAL --> API
  API --- DB
  API -->|"帯一覧・注意事項・初稿"| RS
  RS --> PV
```

---

## 6. 変換パイプライン仕様

### 6.1 全体方針

- 判定はすべて規則に基づき、同一の画像から同一の出力を得られること（決定性）
- 判定結果には必ず信頼度を付与し、迷いがある場合は注意事項を残すこと。黙って推測しないこと
- 解析層は画像と指示のみを受け取り、状態を持たないこと
- 生成物は外部リソースを一切参照せず、1 ファイルで完結すること

### 6.2 受入検証

| 項目 | 要件 |
|---|---|
| 形式 | PNG・JPEG・WebP のみ。SVG・GIF・PDF・その他は拒否する |
| アニメーション | 複数フレームを持つ画像は拒否する |
| ファイルサイズ | 上限 10 MB |
| 画素数 | 短辺 320 px 以上、幅 8000 px 以下、高さ 20000 px 以下 |
| 回転 | EXIF の回転情報を適用してから解析する |
| 透過 | 透過は白へ合成する |
| 破損 | 復号に失敗した場合は拒否する |
| Bot 対策 | ハニーポット項目に値がある送信は、成功と同じ応答を返しつつレコードを作成しない |

### 6.3 正規化

- 作業幅を 1200 px とし、幅がこれを超える場合のみ縦横比を保って縮小する。拡大は行わない
- 作業画像の四辺の縁の画素から最頻の輝度を求め、テーマ（ライト／ダーク）を判定する。以降の「背景」はこの値を基準とする
- 幅が高さの 0.7 倍未満の画像はモバイル幅デザインとみなし、その旨を注意事項に記録する。処理系統は同一とする

### 6.4 帯分割

**行プロファイル**

作業画像の各行について、内容率（背景と異なる画素の割合）・平均色・エッジ量を算出し、平滑化する。

**区切り候補**

| 候補 | 条件 |
|---|---|
| 空白帯 | 内容率が閾値未満の行が最小連続長以上続く区間 |
| 背景色の急変 | 平均色の行方向の変化量が閾値を超え、変化後の色が最小連続長以上持続する行。緩やかな連続変化（グラデーション）は区切りとしない |
| 画像下端 | 画像状ブロブの下端で、その直後に内容の性質が変わる行 |

**要件**

- 最小帯高は作業座標で 48 px とし、これを下回る帯は隣接する帯へ結合すること。高さ比ではなく絶対値で定義すること
- 帯の上限は 40 とし、超過する場合は最も低い帯を隣接帯へ順に結合し、その旨を注意事項に記録すること
- 区切りが 1 つも検出できない場合は画像全体を 1 帯とし、その旨を注意事項に記録すること
- 先頭帯の上部に、小さな文字状ブロブが横一列に並ぶ領域があり、その領域の高さが作業高さの 8% 以下である場合、その領域をヘッダーとして分離すること（透過ヘッダーがヒーローに重なるデザインへの対処）
- 高さの 80% を超えて縦に貫く区切りが、幅の 30% 未満の位置に存在する場合、外殻レイアウトをサイドバーとし、サイドバー領域を除いた残りの領域に対して帯分割を行うこと。この場合、簡易対応である旨を注意事項に記録すること

### 6.5 帯特徴抽出

**ブロブ分類**

| 分類 | 条件 |
|---|---|
| 文字状 | 高さが小さく、横に長く、同じ高さの塊が同一の基準線上に並ぶ |
| 画像状 | 面積が大きく、内部の色分散が大きい |
| 円形画像状 | 画像状のうち、外形が円に近い |
| ボタン状 | 中程度の大きさの矩形で、背景と対照的な塗りを持ち、内部に文字状ブロブを 1 つ含む |
| アイコン状 | 小さくほぼ正方形で、単色または少数色 |

**帯特徴**

| 特徴 | 算出方法 |
|---|---|
| 列数 | 内容を横軸へ投影し、一定幅以上の空白で区切られた塊の数（1 から 4） |
| 反復項目数 | 大きさと構成が近い塊が等間隔で並ぶ場合の個数 |
| 画像位置 | 画像状ブロブの位置。左・右・上・全面・なし |
| 整列 | 文字状ブロブの重心の横位置。左寄せ・中央 |
| 見出し規模 | 最大の文字状ブロブの高さと、帯内の文字状ブロブの高さの中央値との比 |
| 背景色 | 帯内で最頻の色と、その輝度 |
| アクセント色 | ボタン状ブロブの塗りのうち最も彩度の高い色 |
| 高さ比 | 帯の高さと作業高さの比 |
| 位置 | 先頭・末尾・その他 |

### 6.6 種別判定

各セクション種別について、下表の条件をどれだけ満たすかを重み付きで採点し、信頼度とする。

| 種別 | 主な条件 |
|---|---|
| ヘッダー | 先頭、高さ比 8% 以下、小さな文字状ブロブが横一列、左端に小さな画像状またはアイコン状ブロブ |
| ヒーロー | ヘッダーを除く先頭から 2 帯以内、高さ比 25% 以上または大きな画像状ブロブ、見出し規模が 2 以上、ボタン状ブロブを含む |
| 特徴一覧 | 列数 2 から 4、反復項目数が列数と一致、各項目にアイコン状ブロブと文字状ブロブ |
| 画像と文章 | 画像状ブロブが幅の 35% から 65% を占め、その左右に文字状ブロブが並ぶ |
| 行動喚起帯 | 高さ比 15% 以下、中央整列、見出し規模 1.5 以上、ボタン状ブロブを 1 つ含む、背景が前後の帯と対照的 |
| 料金表 | 列数 2 から 4、各列にボタン状ブロブ、各列に大きく短い文字状ブロブ、列を囲む矩形の枠 |
| 証言 | 反復項目、各項目に円形画像状ブロブと複数行の文字状ブロブ |
| FAQ | 列数 1、高さの近い行が縦に反復、各行の右端にアイコン状ブロブ |
| ギャラリー | 画像状ブロブが 4 つ以上格子状に並び、文字状ブロブが少ない |
| ロゴ帯 | 高さ比 10% 以下、小さな画像状ブロブが 4 から 8 個横一列 |
| フッター | 末尾、小さな文字状ブロブが 2 列以上、または背景がページの背景より暗い |
| 汎用テキスト | 上記のいずれにも該当しない場合の退避先 |

**要件**

- 信頼度が最大の種別を採用すること。最大値が 0.6 以上であれば通常採用とする
- 最大値が 0.4 以上 0.6 未満の場合は採用しつつ、低信頼度である旨を注意事項に記録すること
- 最大値が 0.4 未満の場合は汎用テキストとし、その旨を注意事項に記録すること
- 上位 2 種別の信頼度の差が 0.05 以内の場合は、次点の種別名を注意事項に記録すること
- 料金表と特徴一覧は「各列にボタン状ブロブ」「各項目にアイコン状ブロブ」の有無で区別し、いずれの必須条件も欠く場合はどちらも採用しないこと
- ヘッダーは先頭帯以外に、フッターは末尾帯以外に採用しないこと

### 6.7 パラメータ抽出

- 帯特徴からバリアント（列数・画像位置・整列・テーマ）を決定すること。種別に対して不整合な特徴（例：列数 1 の料金表）の場合は種別の既定バリアントを用い、その旨を注意事項に記録すること
- 帯の背景輝度から帯ごとの文字色（濃・淡）を決定すること
- アクセント色はボタン状ブロブから取得し、存在しない帯はページ全体で最初に得られたアクセント色を用いること
- 文字状ブロブは幅と高さから文字数の区分（見出し・小見出し・本文・ボタン）を推定し、区分に応じたプレースホルダ文言を割り当てること。文字の読み取りは行わないこと
- 画像状ブロブは、作業座標をデザイン画像の座標へ戻して切り出し、長辺 800 px 以下に縮小して生成物へ埋め込むこと
- 切り出し画像の埋め込み合計は 4 MB を上限とすること。上限に達する場合は長辺 400 px までを段階的に縮小し、なお超過する分は無地のプレースホルダに置き換え、その旨を注意事項に記録すること

### 6.8 部品組み立て

**要件**

- 外殻レイアウトを選び、帯の順序どおりに部品を並べること。並べ替えは行わないこと
- 生成物は HTML 1 ファイルとし、CSS はファイル内に記述すること。JavaScript を含めないこと
- 外部リソース（フォント・CSS・スクリプト・画像）を参照しないこと。フォントはシステムフォントの列挙とし、画像はデータ URI で埋め込むこと
- 見出しの階層は h1 を 1 つ（ヒーロー、なければ最初の見出しを持つ帯）とし、以降の帯の見出しは h2、項目の見出しは h3 とすること
- `header`・`main`・`section`・`footer`・`nav` の意味付け要素を用いること
- クラス名は部品ごとに接頭辞を持たせ、部品間で衝突しないこと
- すべての `img` に代替文言を付与すること
- 生成物内に、デザイン画像から読み取った文字を含めないこと（プレースホルダのみ）

### 6.9 生成物検証

組み立て後、下記を機械検査し、いずれかに失敗した場合は生成物を採用せず変換を失敗とすること。

| 項目 | 条件 |
|---|---|
| 外部参照 | `http://` および `https://` を含む属性値が存在しない |
| スクリプト | `script` 要素・イベント属性が存在しない |
| 見出し | h1 がちょうど 1 つ |
| 代替文言 | すべての `img` に `alt` がある |
| サイズ | 6 MB 以下 |
| 構造 | 生成した開始タグと終了タグが対応している |

---

## 7. セクション部品カタログ

| 種別 | スロット | バリアント | 幅 600 px 未満での崩し |
|---|---|---|---|
| ヘッダー | ロゴ・ナビ項目（3 から 6）・ボタン（任意） | ボタン有／無 | ロゴを 1 行目、ナビを折り返して 2 行目以降 |
| ヒーロー | 見出し・本文・ボタン（1 から 2）・画像（任意） | 画像右／画像左／画像下／全面画像／画像なし | 画像を上、文章を下に縦積み |
| 特徴一覧 | 項目（アイコン・小見出し・本文）× n | 2 列／3 列／4 列 | 1 列 |
| 画像と文章 | 画像・見出し・本文・ボタン（任意） | 画像左／画像右 | 画像を上に縦積み |
| 行動喚起帯 | 見出し・本文（任意）・ボタン | ライト／ダーク | そのまま（縦の余白を縮小） |
| 料金表 | プラン（名称・価格・箇条書き・ボタン）× n | 2 列／3 列／4 列、強調列あり／なし | 1 列 |
| 証言 | 項目（円形画像・引用・氏名欄）× n | 1 列／2 列／3 列 | 1 列 |
| FAQ | 質問と回答 × n | 1 列 | そのまま |
| ギャラリー | 画像 × n | 2 列／3 列／4 列 | 2 列 |
| ロゴ帯 | 画像 × n | 4 から 8 個 | 折り返し |
| 汎用テキスト | 見出し・本文段落 × n | 左寄せ／中央 | そのまま |
| フッター | 列（見出し・リンク × n）× m・著作権表示欄 | 2 列／3 列／4 列 | 1 列 |

- 証言の氏名欄・フッターの著作権表示欄はプレースホルダ文言とし、実在の氏名・組織名を生成しないこと
- 外殻レイアウトは「単一カラム」と「サイドバー」の 2 種とする。サイドバーは幅 1024 px 未満で本文の上に縦積みする

---

## 8. レスポンシブ規則

| 項目 | 要件 |
|---|---|
| ブレークポイント | 600 px 未満（モバイル）、600 px 以上 1024 px 未満（タブレット）、1024 px 以上（デスクトップ）の 3 段階 |
| 記述方針 | モバイル幅を基準に記述し、広い幅で列を増やす |
| 格子の崩し | 4 列は 1024 px 未満で 2 列、600 px 未満で 1 列。3 列は 600 px 未満で 1 列。2 列は 600 px 未満で 1 列 |
| 画像と文章 | 600 px 未満では画像位置の左右に関わらず画像を上に置く |
| 画像 | 幅の上限を親要素幅とし、縦横比を保つ |
| 文字 | 見出しの文字サイズは幅に応じて段階的に変え、長い語は強制改行して溢れさせない |
| 最大幅 | 内容の最大幅を 1200 px とし、中央に配置する |
| 文字色 | 帯の背景輝度に応じて濃・淡を切り替え、視認できる対比を保つ |

---

## 9. 帯編集仕様

| 操作 | 内容 | 制約 |
|---|---|---|
| 種別変更 | 帯のセクション種別を利用者が指定する | 12 種のいずれか。ヘッダー・フッターは位置の制約を外して指定可とする |
| 結合 | 隣接する 2 帯を 1 帯にする | 非隣接の結合は拒否する。結合後は特徴を再抽出し種別を再判定する |
| 分割 | 帯を指定の行位置で 2 帯にする | 分割位置が帯の上下端から 48 px（作業座標）以内の場合は拒否する。分割後は両帯の特徴を再抽出し種別を再判定する |
| 削除 | 帯を生成対象から外す | すべての帯を削除した場合は生成物を空のページとし、その旨を表示する |
| 復元 | 削除した帯を戻す | 元の位置へ戻す |

**要件**

- 編集のたびに版を 1 つ進め、再組み立てを行うこと。過去の版の生成物は保持しないこと
- 利用者が指定した種別は、再抽出・再判定によって上書きしないこと（結合・分割で新たに生じた帯を除く）
- 結合・分割で特徴の再抽出が必要な場合、解析層へデザイン画像と帯範囲を渡して行うこと

---

## 10. 異常検知と対処

| 事象 | 検知 | 動作 |
|---|---|---|
| 非対応形式・破損・上限超過 | 受入検証 | 受け付けず、理由を表示する |
| ダーク系デザイン | 縁の最頻輝度が低い | 背景基準を切り替えて処理を継続し、注意事項に記録する |
| 区切りが検出できない | 区切り候補が皆無 | 1 帯として処理し、注意事項に記録する |
| 帯数の超過 | 40 を超える | 最も低い帯から結合し、注意事項に記録する |
| サイドバー型 | 縦に貫く区切り | 外殻をサイドバーとし、簡易対応である旨を注意事項に記録する |
| モバイル幅デザイン | 幅が高さの 0.7 倍未満 | 同一の処理系統で継続し、注意事項に記録する |
| 判定の低信頼度・僅差 | 信頼度の閾値 | 採用または退避し、注意事項に記録する |
| 埋め込み予算の超過 | 切り出し合計が 4 MB 超 | 段階縮小し、超過分をプレースホルダにし、注意事項に記録する |
| 解析のタイムアウト | 解析が 30 秒を超える | 変換を失敗とし、理由を記録して表示する |
| 解析層への到達不能 | 接続失敗 | 変換を失敗とし、理由を記録して表示する |
| 生成物検証の失敗 | 6.9 の検査 | 変換を失敗とし、理由を記録して表示する |
| 解析中の日次リセット | リセットの開始 | 変換を中断とし、理由を記録する |
| 不正な編集操作 | 9 の制約 | 操作を拒否し、理由を表示する |

---

## 11. 排他制御と所有権

**要件**

- 1 セッションで同時に処理中の変換は 2 件までとし、超過分は受け付けず待機を促すこと
- 同一のデザイン画像を繰り返しアップロードした場合、それぞれ独立した変換として扱うこと
- **DB のすべてのテーブルにセッションキーを付与し、セッションキーが一致しないレコードの参照・更新・削除を一切行えないこと**
- 他セッションの変換 ID を指定された場合は、存在の有無を区別せず「見つからない」として応答すること
- 変換の削除は所有セッションのみが行え、削除時にデザイン画像・切り出し画像・生成物をすべて消去すること

---

## 12. 画面仕様

### 12.1 アップロード画面

| 領域 | 内容 |
|---|---|
| 入力 | ファイル選択またはドロップ。受入条件（形式・サイズ・画素数）を表示する |
| 送信 | 変換を開始する。ハニーポット項目を不可視で配置する |
| 一覧 | 自セッションの変換を状態とともに一覧し、結果画面へ遷移できる |

### 12.2 変換結果画面

| 領域 | 内容 |
|---|---|
| 画像と帯 | デザイン画像の上に帯の境界と種別名を重ねて表示する |
| 帯一覧 | 帯ごとに種別・信頼度・バリアントを表示し、種別変更・結合・分割・削除・復元を行う |
| プレビュー | 生成物をモバイル・タブレット・デスクトップの 3 幅で表示する。切替と同時表示を備える |
| 注意事項 | 生成に伴う注意事項を帯ごとに一覧する |
| 出力 | HTML ファイルのダウンロード。現在の版を表示する |
| 状態 | 変換の状態と、失敗・中断の場合はその理由を表示する |

**要件**

- プレビューは生成物を `srcdoc` として読み込む `iframe` に表示し、`sandbox` を付与すること
- 帯編集の操作中は、操作対象の帯を画像上で強調すること

---

## 13. データ設計

### 13.1 テーブル一覧

| テーブル | 用途 |
|---|---|
| sessions | ブラウザごとのセッション |
| conversions | 変換 1 件（状態・外殻レイアウト・テーマ・版） |
| source_images | デザイン画像の本体と寸法 |
| bands | 帯（範囲・特徴・判定種別・利用者指定種別・バリアント・削除の有無） |
| band_crops | 帯に属する切り出し画像 |
| outputs | 現在の版の生成物 |
| notices | 注意事項 |
| conversion_events | 変換中に発生した事象 |

すべてのテーブルは `session_id` を保持し、オーナーキーとして参照条件に必ず含める。

### 13.2 マスタデータ件数

| 区分 | 件数 |
|---|---|
| セクション種別 | 12 |
| バリアント（全種別合計） | 31 |
| 外殻レイアウト | 2 |
| ブレークポイント | 3 |
| ブロブ分類 | 5 |
| 判定規則 | 12 |
| 注意事項種別 | 14 |
| 変換状態 | 8 |
| 帯状態 | 4 |
| 受入形式 | 3 |
| プレースホルダ文言区分 | 4 |

---

## 14. ER図

```mermaid
erDiagram
  SESSIONS ||--o{ CONVERSIONS : "所有する"
  CONVERSIONS ||--|| SOURCE_IMAGES : "元とする"
  CONVERSIONS ||--o{ BANDS : "分割される"
  BANDS ||--o{ BAND_CROPS : "含む"
  CONVERSIONS ||--o| OUTPUTS : "生成する"
  CONVERSIONS ||--o{ NOTICES : "記録する"
  BANDS ||--o{ NOTICES : "対象となる"
  CONVERSIONS ||--o{ CONVERSION_EVENTS : "記録する"

  SESSIONS {
    string session_id PK "不透明識別子"
    datetime created_at
    datetime last_seen_at
    string user_agent_class "ブラウザ種別の分類のみ"
  }

  CONVERSIONS {
    string id PK
    string session_id FK "オーナーキー"
    string state "変換状態"
    string shell_layout "single/sidebar"
    string theme "light/dark"
    boolean mobile_design
    integer version "版"
    string failed_reason
    datetime created_at
    datetime updated_at
  }

  SOURCE_IMAGES {
    string id PK
    string session_id FK "オーナーキー"
    string conversion_id FK
    string format "png/jpeg/webp"
    integer width
    integer height
    integer byte_size
    blob body
    float work_scale "作業画像への縮小率"
  }

  BANDS {
    string id PK
    string session_id FK "オーナーキー"
    string conversion_id FK
    integer position "並び順"
    integer top_y "作業座標"
    integer bottom_y "作業座標"
    text features "帯特徴"
    string detected_kind "判定種別"
    float confidence
    string runner_up_kind "次点種別"
    string user_kind "利用者指定種別"
    string variant
    string state "帯状態"
  }

  BAND_CROPS {
    string id PK
    string session_id FK "オーナーキー"
    string band_id FK
    integer left_x
    integer top_y
    integer width
    integer height
    string shape "rect/circle"
    blob body "縮小済み"
    boolean placeholder "予算超過で無地化"
  }

  OUTPUTS {
    string id PK
    string session_id FK "オーナーキー"
    string conversion_id FK
    integer version
    text html
    integer byte_size
    datetime generated_at
  }

  NOTICES {
    string id PK
    string session_id FK "オーナーキー"
    string conversion_id FK
    string band_id FK "任意"
    string notice_type
    string detail
  }

  CONVERSION_EVENTS {
    string id PK
    string session_id FK "オーナーキー"
    string conversion_id FK
    datetime occurred_at
    string event_type
    string detail
  }
```

---

## 15. DFD

### 15.1 コンテキストレベル

```mermaid
flowchart LR
  US(["利用者"])
  CK(["システム時計"])

  P0["デザイン画像→HTML初稿 変換ツール"]

  US -->|"デザイン画像 / 帯編集操作"| P0
  P0 -->|"帯一覧 / 注意事項 / プレビュー / HTMLファイル"| US
  CK -->|"日次リセットの契機"| P0
```

### 15.2 詳細レベル

```mermaid
flowchart TB
  US(["利用者"])
  CK(["システム時計"])

  P1["1. 受入検証"]
  P2["2. 正規化"]
  P3["3. 帯分割"]
  P4["4. 特徴抽出"]
  P5["5. 種別判定"]
  P6["6. パラメータ抽出・切り出し"]
  P7["7. 部品組み立て"]
  P8["8. 生成物検証"]
  P9["9. 帯編集"]
  P10["10. 変換レコード管理"]
  P11["11. 日次リセット"]

  D1[("D1 変換レコード")]
  D2[("D2 デザイン画像")]
  D3[("D3 帯・切り出し")]
  D4[("D4 生成物")]
  D5[("D5 注意事項・事象")]
  D6[("D6 部品カタログ")]

  US -->|"画像"| P1
  P1 -->|"受理画像"| P2
  P1 --> D2
  P2 -->|"作業画像 / テーマ"| P3
  P3 -->|"帯範囲"| P4
  P4 -->|"帯特徴"| P5
  P5 -->|"種別 / 信頼度"| P6
  P6 -->|"帯・バリアント・切り出し"| D3
  D3 --> P7
  D6 --> P7
  P7 -->|"HTML"| P8
  P8 -->|"合格した生成物"| D4
  D4 -->|"プレビュー / ダウンロード"| US

  US -->|"種別変更 / 結合 / 分割 / 削除"| P9
  P9 --> D3
  P9 -->|"再抽出要求"| P4
  P9 -->|"再組み立て要求"| P7

  P1 --> P10
  P5 --> P10
  P6 --> P10
  P8 --> P10
  P9 --> P10
  P10 --> D1
  P10 --> D5
  P10 -->|"状態 / 注意事項"| US

  CK --> P11
  P11 -->|"中断"| P10
  P11 -->|"削除"| D1
  P11 -->|"削除"| D2
  P11 -->|"削除"| D3
  P11 -->|"削除"| D4
  P11 -->|"削除"| D5
```

---

## 16. シーケンス図

### 16.1 アップロードから初稿生成

```mermaid
sequenceDiagram
  actor US as 利用者
  participant FE as フロントエンド
  participant AP as アプリケーション
  participant AN as 解析

  US->>FE: 画像を選択して送信
  FE->>AP: 変換の作成（画像・セッションキー・ハニーポット）
  AP->>AP: ハニーポットと受入検証
  alt 受入不可
    AP-->>FE: 理由
    FE-->>US: 受け付けない旨を表示
  else 受入可
    AP->>AP: 変換レコードと画像を保存
    AP-->>FE: 変換ID（解析中）
    FE-->>US: 解析中を表示
    AP->>AN: 解析要求（画像）
    AN->>AN: 正規化・帯分割・特徴抽出・種別判定・切り出し
    AN-->>AP: 帯・特徴・種別・信頼度・切り出し・注意事項
    AP->>AP: 帯と切り出しを保存
    AP->>AP: 部品組み立て
    AP->>AP: 生成物検証
    alt 検証に失敗
      AP->>AP: 失敗として記録
      FE->>AP: 状態を照会
      AP-->>FE: 失敗と理由
      FE-->>US: 失敗を表示
    else 検証に合格
      AP->>AP: 生成物を保存（版1）
      FE->>AP: 状態を照会
      AP-->>FE: 準備完了・帯一覧・注意事項・生成物
      FE-->>US: 結果画面を表示
    end
  end
```

### 16.2 帯編集と再組み立て

```mermaid
sequenceDiagram
  actor US as 利用者
  participant FE as フロントエンド
  participant AP as アプリケーション
  participant AN as 解析

  US->>FE: 帯を分割（位置を指定）
  FE->>AP: 分割要求（変換ID・帯ID・位置）
  AP->>AP: 所有権と制約を確認
  alt 制約に違反
    AP-->>FE: 拒否と理由
    FE-->>US: 理由を表示
  else 受理
    AP->>AN: 再抽出要求（画像・2つの帯範囲）
    AN-->>AP: 各帯の特徴・種別・信頼度・切り出し
    AP->>AP: 帯を置き換え、版を進める
    AP->>AP: 部品組み立て・生成物検証
    AP->>AP: 生成物を保存
    AP-->>FE: 更新後の帯一覧・注意事項・生成物
    FE-->>US: 画面を更新
  end

  US->>FE: 帯の種別を変更
  FE->>AP: 種別変更要求
  AP->>AP: 所有権を確認し、利用者指定種別を保存
  AP->>AP: 版を進め、再組み立て・検証・保存
  AP-->>FE: 更新後の生成物
  FE-->>US: 画面を更新
```

### 16.3 プレビューとダウンロード

```mermaid
sequenceDiagram
  actor US as 利用者
  participant FE as フロントエンド
  participant AP as アプリケーション

  US->>FE: 結果画面を開く
  FE->>AP: 生成物を取得（変換ID・セッションキー）
  AP->>AP: 所有権を確認
  alt 所有権なし
    AP-->>FE: 見つからない
    FE-->>US: 見つからない旨を表示
  else 所有権あり
    AP-->>FE: 現在の版のHTML
    FE->>FE: srcdoc と sandbox で3幅に表示
    FE-->>US: プレビューを表示
    US->>FE: ダウンロード
    FE-->>US: HTMLファイル
  end
```

### 16.4 日次リセット

```mermaid
sequenceDiagram
  participant CK as システム時計
  participant AP as アプリケーション
  participant FE as フロントエンド

  CK->>AP: JST 03:00 到達
  AP->>AP: 新規の変換受付を停止
  AP->>AP: 解析中・組み立て中の変換を中断として記録
  AP->>AP: 猶予時間の経過を待つ
  AP->>AP: 全テーブルを削除
  AP->>AP: 受付を再開
  FE->>AP: 状態を照会
  AP-->>FE: 見つからない
  FE-->>FE: リセット済みである旨を表示
```

---

## 17. クラス図

```mermaid
classDiagram
  direction LR

  class UploadForm {
    +file: File
    +submit()
    +showRejection(reason)
  }

  class ConversionPage {
    +conversionId: string
    +poll()
    +render()
  }

  class BandOverlay {
    +bands: BandList
    +highlight(bandId)
    +pickSplitPosition() int
  }

  class BandEditor {
    +changeKind(bandId, kind)
    +merge(bandId, nextBandId)
    +split(bandId, y)
    +remove(bandId)
    +restore(bandId)
  }

  class PreviewFrame {
    +widths: WidthSet
    +load(html)
    +switchWidth(width)
  }

  class NoticeList {
    +render(notices)
  }

  class ConversionsController {
    +create()
    +show()
    +destroy()
  }

  class BandsController {
    +updateKind()
    +merge()
    +split()
    +remove()
    +restore()
  }

  class HoneypotGuard {
    +check(params) bool
  }

  class IntakeValidator {
    +validate(file) IntakeResult
  }

  class SessionOwnerGuard {
    +scope(sessionKey) Query
    +verify(sessionKey, conversionId) bool
  }

  class ConversionRepository {
    +create(sessionKey, image) Conversion
    +updateState(id, state)
    +replaceBands(id, bands)
    +saveOutput(id, html, version)
    +appendNotice(notice)
    +appendEvent(event)
    +purgeAll()
  }

  class AnalysisClient {
    +analyze(image) AnalysisResult
    +refeature(image, ranges) BandResultList
  }

  class SectionAssembler {
    +assemble(conversion, bands) string
  }

  class ComponentCatalog {
    +kinds: KindList
    +find(kind) SectionComponent
  }

  class SectionComponent {
    +kind: string
    +variants: VariantList
    +render(params) string
  }

  class VariantResolver {
    +resolve(kind, features) Variant
  }

  class OutputValidator {
    +validate(html) ValidationResult
  }

  class DailyResetJob {
    +run()
    +interruptActive()
    +purgeAll()
  }

  class AnalyzeService {
    +analyze(image) AnalysisResult
    +refeature(image, ranges) BandResultList
  }

  class ImageNormalizer {
    +normalize(image) WorkImage
    +detectTheme(workImage) Theme
  }

  class RowProfiler {
    +profile(workImage) RowProfile
  }

  class BandSegmenter {
    +segment(profile, blobs) BandRangeList
    +detectSidebar(workImage) SidebarRange
    +splitHeader(range) BandRangeList
  }

  class BlobExtractor {
    +extract(workImage, range) BlobList
    +classify(blob) BlobKind
  }

  class BandFeatureExtractor {
    +extract(blobs, range) BandFeatures
  }

  class SectionClassifier {
    +rules: RuleSet
    +classify(features, position) Classification
  }

  class RuleSet {
    +score(kind, features) float
  }

  class ParameterExtractor {
    +extract(features, kind) Params
  }

  class CropExtractor {
    +budget: int
    +crop(image, blobs) CropList
  }

  UploadForm --> ConversionsController
  ConversionPage --> BandOverlay
  ConversionPage --> BandEditor
  ConversionPage --> PreviewFrame
  ConversionPage --> NoticeList
  BandEditor --> BandsController
  ConversionsController --> HoneypotGuard
  ConversionsController --> IntakeValidator
  ConversionsController --> SessionOwnerGuard
  BandsController --> SessionOwnerGuard
  ConversionsController --> ConversionRepository
  BandsController --> ConversionRepository
  ConversionsController --> AnalysisClient
  BandsController --> AnalysisClient
  ConversionsController --> SectionAssembler
  BandsController --> SectionAssembler
  SectionAssembler --> ComponentCatalog
  ComponentCatalog o-- SectionComponent
  SectionAssembler --> VariantResolver
  SectionAssembler --> OutputValidator
  DailyResetJob --> ConversionRepository
  AnalysisClient ..> AnalyzeService : HTTP
  AnalyzeService --> ImageNormalizer
  AnalyzeService --> RowProfiler
  AnalyzeService --> BandSegmenter
  AnalyzeService --> BlobExtractor
  AnalyzeService --> BandFeatureExtractor
  AnalyzeService --> SectionClassifier
  SectionClassifier --> RuleSet
  AnalyzeService --> ParameterExtractor
  AnalyzeService --> CropExtractor
```

---

## 18. 状態遷移図

### 18.1 変換

```mermaid
stateDiagram-v2
  [*] --> Uploaded : 受入検証に合格

  Uploaded --> Analyzing : 解析を要求
  Analyzing --> Assembling : 解析結果を受領
  Analyzing --> Failed : タイムアウト / 到達不能
  Assembling --> Ready : 生成物検証に合格
  Assembling --> Failed : 生成物検証に失敗

  Ready --> Reassembling : 帯編集
  Reassembling --> Ready : 再組み立てと検証が完了
  Reassembling --> Failed : 再抽出または検証に失敗

  Analyzing --> Interrupted : 日次リセット
  Assembling --> Interrupted : 日次リセット
  Reassembling --> Interrupted : 日次リセット

  Ready --> Deleted : 利用者が削除
  Failed --> Deleted : 利用者が削除
  Interrupted --> Deleted : 利用者が削除
  Deleted --> [*]

  note right of Ready
    現在の版の生成物を保持する。
    版は編集のたびに進む。
  end note
```

### 18.2 帯

```mermaid
stateDiagram-v2
  [*] --> Detected : 帯分割で生成
  Detected --> Overridden : 利用者が種別を指定
  Detected --> Removed : 削除
  Overridden --> Removed : 削除
  Removed --> Detected : 復元（指定種別なし）
  Removed --> Overridden : 復元（指定種別あり）
  Detected --> Replaced : 結合 / 分割の対象になる
  Overridden --> Replaced : 結合 / 分割の対象になる
  Replaced --> [*]

  note right of Replaced
    結合・分割で新たに生じた帯は
    Detected として再判定される。
  end note
```

---

## 19. ユースケース図

```mermaid
flowchart LR
  US(["利用者"])
  CK(["システム時計"])

  subgraph SYS["デザイン画像→HTML初稿 変換ツール（デモ版）"]
    U1(["デザイン画像を送信する"])
    U2(["帯と種別を確認する"])
    U3(["初稿を3幅でプレビューする"])
    U4(["注意事項を確認する"])
    U5(["帯の種別を変更する"])
    U6(["帯を結合する"])
    U7(["帯を分割する"])
    U8(["帯を削除・復元する"])
    U9(["HTMLファイルを取得する"])
    U10(["変換を削除する"])
    U11(["日次リセットを実行する"])
    U12(["受入検証を通過する"])
    U13(["再組み立てする"])
    U14(["特徴を再抽出する"])
  end

  US --> U1
  US --> U2
  US --> U3
  US --> U4
  US --> U5
  US --> U6
  US --> U7
  US --> U8
  US --> U9
  US --> U10
  CK --> U11

  U1 -.->|"include"| U12
  U5 -.->|"include"| U13
  U6 -.->|"include"| U14
  U7 -.->|"include"| U14
  U8 -.->|"include"| U13
  U14 -.->|"include"| U13
  U3 -.->|"extend"| U2
```

---

## 20. 非機能要件

| 区分 | 要件 |
|---|---|
| 実装方式 | 1 issue のワンショットで実装する |
| 外部通信 | 外部サービスへのネットワーク越しの呼び出しを行わない。資格情報を必要とする通信を持たない |
| 決定性 | 同一の画像と同一の編集操作から同一の生成物を得ること |
| 応答 | 解析は 30 秒で打ち切り、失敗として扱うこと |
| 生成物 | 1 ファイル・6 MB 以下・外部参照なし・JavaScript なし |
| 資源 | 画像・切り出し・生成物は変換の寿命内のみ保持し、削除または日次リセットで消去すること |
| 同時性 | 1 セッションあたり同時処理中の変換は 2 件まで |

---

## 21. セキュリティ・個人情報

**セキュリティ**

- 認証・認可を設計に組み込まない
- セッション管理（Cookie ＋ SQLite）を用い、セッションキーをオーナーキーとして全テーブルに付与する
- セッションをまたいだ DB レコードの参照・操作を行えないこと。他セッションの ID は存在の有無を区別せず「見つからない」とすること
- Bot 対策はハニーポット方式で行う。reCAPTCHA を用いない
- アップロードされたファイルは形式・サイズ・画素数・復号可否を検証し、逸脱するものは保存せず拒否すること
- 生成物のプレビューは `sandbox` 付きの `iframe` で行い、アプリケーションの文脈で実行しないこと

**個人情報**

| 項目 | 扱い |
|---|---|
| 氏名・ニックネーム | 使用しない。生成物の氏名欄・組織名欄はプレースホルダとする |
| メールアドレス | 使用しない |
| 生年月日・住所・電話番号 | 使用しない |
| セッションキー | 端末識別子として扱う |
| デザイン画像 | 文字の読み取りを行わず、レイアウトの解析にのみ用いる。変換の寿命内のみ保持し、共有・公開しない |
| 切り出し画像 | 生成物への埋め込みにのみ用いる。デザイン画像と同じ寿命で消去する |

---

## 22. 運用要件

| 項目 | 内容 |
|---|---|
| DB | SQLite。デプロイ先を問わず SQLite を用いる |
| 日次リセット | JST 03:00 に全テーブルを削除する。実行前に新規受付を停止し、処理中の変換を中断として記録し、猶予時間の経過後に削除する |
| 画像の保持 | 変換レコードと同じ寿命とし、削除と日次リセットで消去する |
| 部品カタログ | コードとして管理し、DB に保持しない |
| 測定 | 行わない |
| 保守・監視 | 行わない |

---

## 23. 対応環境と制約

| 項目 | 内容 |
|---|---|
| 対応ブラウザ | 最新世代のデスクトップ向けブラウザ。モバイルブラウザでも閲覧・ダウンロードは可能とする |
| 対応するデザイン | 単一ページ・縦スクロール型。デスクトップ幅・モバイル幅の両方 |
| 簡易対応となるデザイン | サイドバー型（外殻の切替のみ。サイドバー内部は汎用テキストとする） |
| 対応しないデザイン | 要素が重なり合う絶対配置主体のレイアウト、斜め・曲線の帯境界、横スクロール型。これらは帯分割の精度が下がるため、注意事項と帯編集で補うことを前提とする |
| 生成物の前提 | 初稿であり、文字・装飾・細部は利用者が手直しすること |
| 前提 | 利用者がデザイン画像の利用権を有していること |
