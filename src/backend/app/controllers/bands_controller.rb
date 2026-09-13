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

    refeatured = call_refeature([ range ])
    return if performed?

    ActiveRecord::Base.transaction do
      first.update!(state: "replaced")
      second.update!(state: "replaced")
      shift_positions_after(second.position, by: -1)
      ConversionPipeline.persist_bands(@conversion, refeatured, position_offset: first.position)
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
    refeatured = call_refeature(ranges)
    return if performed?

    ActiveRecord::Base.transaction do
      @band.update!(state: "replaced")
      shift_positions_after(@band.position, by: 1)
      ConversionPipeline.persist_bands(@conversion, refeatured, position_offset: @band.position)
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
  end

  def shift_positions_after(position, by:)
    @conversion.bands.where("position > ?", position).find_each do |b|
      b.update!(position: b.position + by)
    end
  end

  def call_refeature(ranges)
    source_image = @conversion.source_image
    response = AnalysisClient.new.refeature(
      image_bytes: source_image.body, work_scale: source_image.work_scale, ranges: ranges
    )
    ConversionPipeline.persist_notices(@conversion, response[:notices] || [])
    response[:bands] || []
  rescue AnalysisClient::TimeoutError
    render json: { error: ErrorCodes::ANALYSIS_TIMEOUT }, status: :unprocessable_content
  rescue AnalysisClient::UnreachableError, AnalysisClient::DecodeFailedError
    render json: { error: ErrorCodes::ANALYSIS_UNREACHABLE }, status: :unprocessable_content
  end
end
