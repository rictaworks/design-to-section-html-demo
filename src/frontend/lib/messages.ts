import type { ConversionState, Notice, SectionKind } from "./types";

export const messages = {
  site: {
    title: "デザイン画像→HTML初稿 変換ツール",
    description: "デザイン画像をアップロードするとレスポンシブなHTML初稿を生成します。",
  },
  upload: {
    title: "デザイン画像をアップロード",
    fileLabel: "デザイン画像（PNG・JPEG・WebP）",
    requirements:
      "形式：PNG・JPEG・WebPのみ／サイズ上限：10MB／短辺320px以上・幅8000px以下・高さ20000px以下／複数フレーム画像（アニメーション）は不可",
    submit: "変換する",
    submitting: "送信中…",
    listTitle: "これまでの変換",
    listEmpty: "まだ変換がありません。",
    open: "結果を見る",
    honeypotLabel: "この項目は入力しないでください",
    delete: "削除",
    deleteConfirm: "この変換を削除しますか？",
    deleteConfirmYes: "削除する",
    deleteConfirmCancel: "キャンセル",
  },
  errors: {
    invalid_format: "対応していないファイル形式です。",
    unsupported_format: "対応していないファイル形式です（PNG・JPEG・WebPのみ）。",
    size_exceeded: "ファイルサイズが10MBの上限を超えています。",
    animated_rejected: "複数フレーム（アニメーション）を持つ画像は使用できません。",
    dimension_out_of_range:
      "画素数が対応範囲外です（短辺320px以上・幅8000px以下・高さ20000px以下）。",
    corrupted: "画像を読み込めませんでした（破損している可能性があります）。",
    too_many_active: "同時に処理できる変換は2件までです。しばらく待ってから再度お試しください。",
    not_found: "指定の変換が見つかりませんでした。",
    non_adjacent_merge_rejected: "隣接していない帯は結合できません。",
    split_too_close_to_edge: "帯の端に近すぎる位置では分割できません。",
    band_replaced: "この帯はすでに結合・分割により置き換えられており、操作できません。画面を更新してください。",
    reset_in_progress: "日次リセット中のため、しばらくしてから再度お試しください。",
    network: "通信に失敗しました。通信環境を確認して再度お試しください。",
    unknown: "処理に失敗しました。時間をおいて再度お試しください。",
  },
  overlay: {
    designImageAlt: "デザイン画像",
  },
  sectionKindLabels: {
    header: "ヘッダー",
    hero: "ヒーロー",
    features: "特徴一覧",
    image_with_text: "画像と文章",
    cta: "行動喚起帯",
    pricing: "料金表",
    testimonials: "証言",
    faq: "FAQ",
    gallery: "ギャラリー",
    logos: "ロゴ帯",
    generic_text: "汎用テキスト",
    footer: "フッター",
  } satisfies Record<SectionKind, string>,
  stateLabels: {
    uploaded: "受付済み",
    analyzing: "解析中",
    assembling: "組み立て中",
    ready: "準備完了",
    reassembling: "再組み立て中",
    failed: "失敗",
    interrupted: "中断",
    deleted: "削除済み",
  } satisfies Record<ConversionState, string>,
  result: {
    statusTitle: "状態",
    failedReasonPrefix: "理由：",
    bandsTitle: "帯一覧",
    confidenceLabel: "信頼度",
    variantLabel: "バリアント",
    changeKind: "種別を変更",
    merge: "次の帯と結合",
    split: "分割",
    splitPositionLabel: "分割位置（作業座標のy）",
    remove: "削除",
    restore: "復元",
    noticesTitle: "注意事項",
    noticesEmpty: "注意事項はありません。",
    previewTitle: "プレビュー",
    previewMobile: "モバイル",
    previewTablet: "タブレット",
    previewDesktop: "デスクトップ",
    download: "HTMLファイルをダウンロード",
    versionLabel: "版",
    removedBadge: "削除対象",
    sourceImageFetchFailed: "デザイン画像の取得に失敗しました。",
  },
  common: {
    close: "閉じる",
    confirm: "実行する",
    cancel: "キャンセル",
  },
  notices: {
    mobile_design_detected: "画像の縦横比から、モバイル幅のデザインとして処理しました。",
    dark_theme_detected: "背景色を暗い配色（ダークテーマ）と判定し、その基準で処理しました。",
    no_separator_found: "帯の区切りを検出できなかったため、画像全体を1つの帯として扱いました。",
    band_count_exceeded: "帯の数が上限（40）を超えたため、最も低い帯から隣接する帯へ結合しました。",
    sidebar_layout_detected:
      "縦に貫く区切りを検出したため、サイドバー構成として簡易対応しました（サイドバー内部は簡易表示です）。",
    header_split_from_hero: "先頭にある小さな要素の並びをヘッダーとして分離しました。",
    low_confidence_kind: "種別判定の信頼度がやや低いため、内容をご確認ください。",
    close_confidence_runner_up: "次点の種別「{{runner_up}}」とも僅差でした。",
    generic_text_fallback: "種別を十分な信頼度で判定できなかったため、汎用テキストとして扱いました。",
    variant_mismatch_fallback:
      "帯の特徴とこの種別の組み合わせが標準的でなかったため、既定のバリアントを使用しました。",
    embedding_budget_exceeded:
      "画像の埋め込み容量の上限に達したため、一部の画像を縮小またはプレースホルダに置き換えました。",
    analysis_timeout: "解析処理が30秒以内に完了しなかったため、変換を失敗として扱いました。",
    analysis_unreachable: "解析サービスに接続できなかったため、変換を失敗として扱いました。",
    daily_reset_interrupted: "日次リセットにより処理が中断されました。",
    unknown: "生成に関する注意事項があります。",
  } satisfies Record<string, string>,
} as const;

export function errorMessage(code: string): string {
  const table: Record<string, string> = messages.errors;
  return table[code] ?? messages.errors.unknown;
}

export function noticeText(notice: Pick<Notice, "notice_type" | "detail">): string {
  const table: Record<string, string> = messages.notices;
  const template = table[notice.notice_type] ?? messages.notices.unknown;
  const runnerUpKind = notice.detail?.runner_up_kind;
  if (
    notice.notice_type === "close_confidence_runner_up" &&
    typeof runnerUpKind === "string" &&
    runnerUpKind in messages.sectionKindLabels
  ) {
    const label = messages.sectionKindLabels[runnerUpKind as SectionKind];
    return template.replace("{{runner_up}}", label);
  }
  return template;
}
