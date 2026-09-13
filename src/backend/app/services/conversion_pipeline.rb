# 変換パイプラインの状態遷移・帯永続化・部品組み立て・生成物検証を束ねる
# （requirements.md 6.7〜6.9・9章・10章・18章）。
class ConversionPipeline
  def self.pipeline_config
    Rails.application.config.x.pipeline
  end

  # 新規アップロード時：解析層を呼び出し、帯・切り出し・注意事項を保存し、組み立てる
  def self.run_initial_analysis(conversion, bytes:, filename:, content_type:)
    conversion.update!(state: "analyzing")
    record_event(conversion, "analysis_started")

    analysis = AnalysisClient.new.analyze(bytes: bytes, filename: filename, content_type: content_type)

    conversion.source_image&.update!(work_scale: analysis[:work_scale] || 1.0)

    conversion.update!(
      theme: analysis[:theme] || "light",
      mobile_design: !!analysis[:mobile_design],
      shell_layout: analysis[:shell_layout] || "single"
    )

    conversion.update!(state: "assembling")
    record_event(conversion, "analysis_succeeded")

    persist_bands(conversion, analysis[:bands] || [])
    persist_notices(conversion, analysis[:notices] || [])

    reassemble!(conversion)
  rescue AnalysisClient::TimeoutError
    fail_conversion!(conversion, NoticeTypes::ANALYSIS_TIMEOUT, "analysis_timeout")
  rescue AnalysisClient::UnreachableError, AnalysisClient::DecodeFailedError
    fail_conversion!(conversion, NoticeTypes::ANALYSIS_UNREACHABLE, "analysis_unreachable")
  end

  # 帯編集後：版を1つ進めて再組み立て・再検証する（requirements.md 9章）
  def self.reassemble!(conversion)
    result = SectionAssembler.assemble(conversion)
    persist_notices(conversion, result.notices)

    validation = OutputValidator.validate(result.html)
    if validation.valid?
      save_output!(conversion, result.html)
      conversion.update!(state: "ready", failed_reason: nil)
      record_event(conversion, "ready")
    else
      conversion.update!(state: "failed", failed_reason: ErrorCodes::OUTPUT_VALIDATION_FAILED)
      record_event(conversion, "output_validation_failed", reasons: validation.reasons)
    end
  end

  def self.save_output!(conversion, html)
    conversion.output&.destroy
    conversion.increment!(:version)
    conversion.create_output!(
      session_id: conversion.session_id, version: conversion.version,
      html: html, byte_size: html.bytesize, generated_at: Time.current
    )
  end

  def self.persist_bands(conversion, bands_data, position_offset: 0)
    bands_data.each_with_index do |b, idx|
      band = conversion.bands.create!(
        session_id: conversion.session_id,
        position: position_offset + idx,
        top_y: b[:top_y], bottom_y: b[:bottom_y],
        features: (b[:features] || {}).stringify_keys,
        detected_kind: b[:detected_kind], confidence: b[:confidence],
        runner_up_kind: b[:runner_up_kind], variant: b[:detected_kind],
        state: "detected"
      )
      (b[:crops] || []).each do |c|
        band.band_crops.create!(
          session_id: conversion.session_id,
          left_x: c[:left_x], top_y: c[:top_y], width: c[:width], height: c[:height],
          shape: c[:shape] || "rect",
          body: c[:placeholder] ? nil : Base64.decode64(c[:image_base64].to_s),
          placeholder: !!c[:placeholder]
        )
      end
      persist_band_notices(conversion, band, b[:notices] || [])
    end
  end

  def self.persist_notices(conversion, notices_data)
    notices_data.each do |n|
      conversion.notices.create!(
        session_id: conversion.session_id,
        band_id: resolve_band_id(conversion, n),
        notice_type: n[:notice_type] || n["notice_type"],
        detail: (n[:detail] || {}).stringify_keys
      )
    end
  end

  def self.persist_band_notices(conversion, band, notices_data)
    notices_data.each do |n|
      conversion.notices.create!(
        session_id: conversion.session_id, band: band,
        notice_type: n[:notice_type], detail: (n[:detail] || {}).stringify_keys
      )
    end
  end

  def self.resolve_band_id(conversion, notice)
    position = notice[:band_position]
    return nil if position.nil?
    conversion.bands.find_by(position: position)&.id
  end

  def self.fail_conversion!(conversion, notice_type, reason)
    conversion.notices.create!(session_id: conversion.session_id, notice_type: notice_type, detail: {})
    conversion.update!(state: "failed", failed_reason: reason)
    record_event(conversion, reason)
  end

  def self.record_event(conversion, event_type, detail = {})
    conversion.conversion_events.create!(
      session_id: conversion.session_id, occurred_at: Time.current,
      event_type: event_type, detail: detail.stringify_keys
    )
  end
end
