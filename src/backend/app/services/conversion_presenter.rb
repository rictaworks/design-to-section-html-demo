# レスポンスJSONの組み立て（フロントエンドとの契約）。
module ConversionPresenter
  module_function

  def detail(conversion)
    source_image = conversion.source_image
    output = conversion.output

    {
      id: conversion.id,
      state: conversion.state,
      shell_layout: conversion.shell_layout,
      theme: conversion.theme,
      mobile_design: conversion.mobile_design,
      version: conversion.version,
      failed_reason: conversion.failed_reason,
      created_at: conversion.created_at,
      bands: conversion.bands.listed.map { |b| band_json(b) },
      notices: presentable_notices(conversion).map { |n| notice_json(n) },
      output: output && { html: output.html, byte_size: output.byte_size, version: output.version },
      source_image: source_image && {
        width: source_image.width,
        height: source_image.height,
        # src/analysis/app/normalize.py の work_height = max(1, round(height * work_scale)) と
        # 同じ丸め方（round-half-to-even）に揃える。Rubyの既定（round-half-up）のままだと、
        # height*work_scaleがちょうど.5になる画像でPythonの実際のwork画像高さと1px食い違い、
        # フロントの帯オーバーレイがその分ずれる。
        work_height: [ 1, (source_image.height * source_image.work_scale).round(half: :even) ].max
      }
    }
  end

  def summary(conversion)
    {
      id: conversion.id, state: conversion.state,
      version: conversion.version, created_at: conversion.created_at
    }
  end

  def band_json(band)
    {
      id: band.id, position: band.position, top_y: band.top_y, bottom_y: band.bottom_y,
      kind: band.kind, detected_kind: band.detected_kind, user_kind: band.user_kind,
      confidence: band.confidence, runner_up_kind: band.runner_up_kind,
      variant: band.variant, state: band.state
    }
  end

  # 置換済み(state=replaced)の帯に紐づく注意事項は、結合・分割で既に再判定済みの新しい帯へ
  # 引き継がれない限り、古い評価として残さない（requirements.md 9章：帯編集のたびに再判定する）。
  def presentable_notices(conversion)
    live_band_ids = conversion.bands.listed.pluck(:id)
    conversion.notices.select { |n| n.band_id.nil? || live_band_ids.include?(n.band_id) }
  end

  def notice_json(notice)
    { id: notice.id, notice_type: notice.notice_type, band_id: notice.band_id, detail: notice.detail }
  end
end
