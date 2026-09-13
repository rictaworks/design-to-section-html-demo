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
      notices: conversion.notices.map { |n| notice_json(n) },
      output: output && { html: output.html, byte_size: output.byte_size, version: output.version },
      source_image: source_image && {
        width: source_image.width,
        height: source_image.height,
        work_height: (source_image.height * source_image.work_scale).round
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

  def notice_json(notice)
    { notice_type: notice.notice_type, band_id: notice.band_id, detail: notice.detail }
  end
end
