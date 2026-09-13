class ConversionsController < ApplicationController
  CONTENT_TYPES = { "png" => "image/png", "jpeg" => "image/jpeg", "webp" => "image/webp" }.freeze

  # 同時アクティブ件数チェックと作成の間のTOCTOUを防ぐ、セッションごとのプロセス内ロック。
  # SQLiteはSELECT ... FOR UPDATEを解釈しないため、DBロックではなくプロセス内Mutexで直列化する
  # （単一プロセスのデモ運用を前提としたKISSな対策。同一セッション内の競合のみが対象）。
  # セッションごとにエントリが増え続け明示的な削除は行わない。日次リセットでプロセスごと
  # 再起動される運用を前提としたデモ版のトレードオフとして許容する（YAGNI）。
  ACTIVE_COUNT_MUTEXES = Concurrent::Map.new

  class ActiveConversionLimitExceeded < StandardError; end

  def index
    conversions = Conversion.for_session(current_session_id).order(created_at: :desc)
    render json: conversions.map { |c| ConversionPresenter.summary(c) }
  end

  def create
    if HoneypotGuard.triggered?(params)
      return render json: { id: SecureRandom.uuid, state: "uploaded" }, status: :created
    end

    if SystemState.reset_in_progress?
      return render json: { error: ErrorCodes::RESET_IN_PROGRESS }, status: :unprocessable_content
    end

    upload = params[:file]
    return render json: { error: ErrorCodes::UNSUPPORTED_FORMAT }, status: :unprocessable_content if upload.blank?

    bytes = upload.read
    validation = IntakeValidator.validate(bytes)
    unless validation.ok?
      return render json: { error: validation.error_code }, status: :unprocessable_content
    end

    conversion = nil
    begin
      conversion = create_conversion_with_image_if_under_limit(bytes, validation)
    rescue ActiveConversionLimitExceeded
      return render json: { error: ErrorCodes::TOO_MANY_ACTIVE }, status: :unprocessable_content
    end
    ConversionPipeline.run_initial_analysis(
      conversion, bytes: bytes, filename: upload.original_filename, content_type: upload.content_type
    )

    render json: ConversionPresenter.detail(conversion.reload), status: :created
  end

  def show
    conversion = find_owned!(Conversion, params[:id])
    render json: ConversionPresenter.detail(conversion)
  end

  def destroy
    conversion = find_owned!(Conversion, params[:id])
    conversion.destroy!
    head :no_content
  end

  def source_image
    conversion = find_owned!(Conversion, params[:id])
    image = conversion.source_image
    raise ActiveRecord::RecordNotFound if image.nil?
    send_data image.body, type: CONTENT_TYPES.fetch(image.format, "application/octet-stream"), disposition: "inline"
  end

  private

  def create_conversion_with_image_if_under_limit(bytes, validation)
    mutex = ACTIVE_COUNT_MUTEXES.compute_if_absent(current_session_id) { Mutex.new }
    mutex.synchronize do
      active_count = Conversion.for_session(current_session_id).active.count
      max_active = ConversionPipeline.pipeline_config[:max_active_conversions_per_session]
      raise ActiveConversionLimitExceeded if active_count >= max_active

      create_conversion_with_image(bytes, validation)
    end
  end

  def create_conversion_with_image(bytes, validation)
    conversion = nil
    ActiveRecord::Base.transaction do
      conversion = Conversion.create!(session_id: current_session_id, state: "uploaded")
      SourceImage.create!(
        session_id: current_session_id, conversion: conversion,
        format: validation.format, width: validation.width, height: validation.height,
        byte_size: validation.byte_size, body: bytes, work_scale: 1.0
      )
    end
    ConversionPipeline.record_event(conversion, "created")
    conversion
  end
end
