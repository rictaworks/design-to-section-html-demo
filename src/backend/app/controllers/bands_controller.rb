# 帯編集（requirements.md 9章）。編集のたびに版を1つ進め、再組み立てを行う。
# 利用者が指定した種別は、再抽出・再判定によって上書きしない（結合・分割で新たに生じた帯を除く）。
class BandsController < ApplicationController
  before_action :set_conversion
  before_action :set_band

  def update_kind
    kind = params[:kind]
    return render json: { error: ErrorCodes::INVALID_KIND }, status: :unprocessable_content unless SectionKinds::ALL.include?(kind)

    @band.update!(user_kind: kind, state: "overridden")
    ConversionPipeline.reassemble!(@conversion)
    render json: ConversionPresenter.detail(@conversion.reload)
  end

  def merge
    other = @conversion.bands.assemblable.find_by(id: params[:with])
    unless other && (other.position - @band.position).abs == 1
      return render json: { error: ErrorCodes::NON_ADJACENT_MERGE_REJECTED }, status: :unprocessable_content
    end

    first, second = [ @band, other ].sort_by(&:position)
    range = { top_y: first.top_y, bottom_y: second.bottom_y }

    refeatured = call_refeature(
      [ range ],
      is_first_band: first.position.zero?,
      is_last_band: second.position == max_band_position
    )
    return if performed?

    ActiveRecord::Base.transaction do
      first.update!(state: "replaced")
      second.update!(state: "replaced")
      shift_positions_after(second.position, by: -1)
      ConversionPipeline.persist_bands(@conversion, refeatured[:bands], position_offset: first.position)
      ConversionPipeline.persist_notices_with_offset(@conversion, refeatured[:notices], first.position)
    end

    ConversionPipeline.reassemble!(@conversion.reload)
    render json: ConversionPresenter.detail(@conversion.reload)
  end

  def split
    y = params[:y].to_i
    min_height = ConversionPipeline.pipeline_config[:min_band_height_px]
    if y <= @band.top_y + min_height || y >= @band.bottom_y - min_height
      return render json: { error: ErrorCodes::SPLIT_TOO_CLOSE_TO_EDGE }, status: :unprocessable_content
    end

    ranges = [ { top_y: @band.top_y, bottom_y: y }, { top_y: y, bottom_y: @band.bottom_y } ]
    refeatured = call_refeature(
      ranges,
      is_first_band: @band.position.zero?,
      is_last_band: @band.position == max_band_position
    )
    return if performed?

    ActiveRecord::Base.transaction do
      @band.update!(state: "replaced")
      shift_positions_after(@band.position, by: 1)
      ConversionPipeline.persist_bands(@conversion, refeatured[:bands], position_offset: @band.position)
      ConversionPipeline.persist_notices_with_offset(@conversion, refeatured[:notices], @band.position)
    end

    ConversionPipeline.reassemble!(@conversion.reload)
    render json: ConversionPresenter.detail(@conversion.reload)
  end

  def remove
    @band.update!(state: "removed")
    ConversionPipeline.reassemble!(@conversion)
    render json: ConversionPresenter.detail(@conversion.reload)
  end

  def restore
    @band.update!(state: @band.user_kind.present? ? "overridden" : "detected")
    ConversionPipeline.reassemble!(@conversion)
    render json: ConversionPresenter.detail(@conversion.reload)
  end

  private

  def set_conversion
    @conversion = find_owned!(Conversion, params[:conversion_id])
  end

  def set_band
    @band = @conversion.bands.find_by(id: params[:band_id])
    raise ActiveRecord::RecordNotFound if @band.nil?

    if @band.state == "replaced"
      render json: { error: ErrorCodes::BAND_REPLACED }, status: :unprocessable_content
    end
  end

  def shift_positions_after(position, by:)
    @conversion.bands.where("position > ?", position).find_each do |b|
      b.update!(position: b.position + by)
    end
  end

  # 結合・分割で対象になる帯（複数の場合はすべて）が、conversion全体の先頭／末尾の帯
  # でもあるかどうか。replaced帯はpositionを変えずに残る（shift_positions_after参照）ため、
  # 除外しないと置換済みの古いpositionを最大値として拾ってしまうことがある。
  def max_band_position
    @conversion.bands.listed.maximum(:position)
  end

  def call_refeature(ranges, is_first_band:, is_last_band:)
    source_image = @conversion.source_image
    response = AnalysisClient.new.refeature(
      image_bytes: source_image.body, work_scale: source_image.work_scale, ranges: ranges,
      is_first_band: is_first_band, is_last_band: is_last_band
    )
    # response[:notices]のband_positionは「このrangesの中でのindex」であり、conversion全体
    # での帯位置ではない。persist_bandsで新しい帯を作りposition_offsetが確定してから、
    # persist_notices_with_offsetで同じoffsetを使って解決する（呼び出し元で行う）。
    { bands: response[:bands] || [], notices: response[:notices] || [] }
  rescue AnalysisClient::TimeoutError
    render json: { error: ErrorCodes::ANALYSIS_TIMEOUT }, status: :unprocessable_content
  rescue AnalysisClient::UnreachableError
    render json: { error: ErrorCodes::ANALYSIS_UNREACHABLE }, status: :unprocessable_content
  rescue AnalysisClient::DecodeFailedError
    render json: { error: ErrorCodes::ANALYSIS_DECODE_FAILED }, status: :unprocessable_content
  end
end
