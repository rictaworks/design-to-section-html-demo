# 注意事項種別コード（requirements.md 6章・10章・13.2）。
# 日本語文言はフロントエンド側の設定でこのコードから解決する。
module NoticeTypes
  MOBILE_DESIGN_DETECTED = "mobile_design_detected"
  DARK_THEME_DETECTED = "dark_theme_detected"
  NO_SEPARATOR_FOUND = "no_separator_found"
  BAND_COUNT_EXCEEDED = "band_count_exceeded"
  SIDEBAR_LAYOUT_DETECTED = "sidebar_layout_detected"
  HEADER_SPLIT_FROM_HERO = "header_split_from_hero"
  LOW_CONFIDENCE_KIND = "low_confidence_kind"
  CLOSE_CONFIDENCE_RUNNER_UP = "close_confidence_runner_up"
  GENERIC_TEXT_FALLBACK = "generic_text_fallback"
  VARIANT_MISMATCH_FALLBACK = "variant_mismatch_fallback"
  EMBEDDING_BUDGET_EXCEEDED = "embedding_budget_exceeded"
  ANALYSIS_TIMEOUT = "analysis_timeout"
  ANALYSIS_UNREACHABLE = "analysis_unreachable"
  DAILY_RESET_INTERRUPTED = "daily_reset_interrupted"

  ALL = [
    MOBILE_DESIGN_DETECTED, DARK_THEME_DETECTED, NO_SEPARATOR_FOUND, BAND_COUNT_EXCEEDED,
    SIDEBAR_LAYOUT_DETECTED, HEADER_SPLIT_FROM_HERO, LOW_CONFIDENCE_KIND, CLOSE_CONFIDENCE_RUNNER_UP,
    GENERIC_TEXT_FALLBACK, VARIANT_MISMATCH_FALLBACK, EMBEDDING_BUDGET_EXCEEDED,
    ANALYSIS_TIMEOUT, ANALYSIS_UNREACHABLE, DAILY_RESET_INTERRUPTED
  ].freeze
end
