# APIエラーコード（requirements.md 6.2・9章・11章・21章）。
# レスポンスは {"error": "<code>"} 形式。日本語文言への変換はフロントエンドが行う。
module ErrorCodes
  NOT_FOUND = "not_found"
  UNSUPPORTED_FORMAT = "unsupported_format"
  ANIMATED_REJECTED = "animated_rejected"
  SIZE_EXCEEDED = "size_exceeded"
  DIMENSION_OUT_OF_RANGE = "dimension_out_of_range"
  CORRUPTED = "corrupted"
  TOO_MANY_ACTIVE = "too_many_active"
  NON_ADJACENT_MERGE_REJECTED = "non_adjacent_merge_rejected"
  SPLIT_TOO_CLOSE_TO_EDGE = "split_too_close_to_edge"
  INVALID_KIND = "invalid_kind"
  ANALYSIS_TIMEOUT = "analysis_timeout"
  ANALYSIS_UNREACHABLE = "analysis_unreachable"
  ANALYSIS_DECODE_FAILED = "analysis_decode_failed"
  OUTPUT_VALIDATION_FAILED = "output_validation_failed"
  RESET_IN_PROGRESS = "reset_in_progress"
  BAND_REPLACED = "band_replaced"
end
