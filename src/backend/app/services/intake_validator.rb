require "stringio"

# 受入検証（requirements.md 6.2）。
# 形式・サイズ・画素数・破損を検証し、逸脱するものは保存前に拒否する。
class IntakeValidator
  Result = Struct.new(:ok, :error_code, :format, :width, :height, :byte_size, keyword_init: true) do
    def ok?
      ok
    end
  end

  MAX_BYTES = 10.megabytes
  MIN_SHORT_EDGE = 320
  MAX_WIDTH = 8000
  MAX_HEIGHT = 20_000

  PNG_SIGNATURE = "\x89PNG\r\n\x1a\n".b
  JPEG_SIGNATURE = "\xFF\xD8\xFF".b

  def self.validate(bytes)
    new(bytes).validate
  end

  def initialize(bytes)
    @bytes = bytes.to_s.b
  end

  def validate
    return reject(ErrorCodes::SIZE_EXCEEDED) if @bytes.bytesize > MAX_BYTES

    format = detect_format
    return reject(ErrorCodes::UNSUPPORTED_FORMAT) if format.nil?
    return reject(ErrorCodes::ANIMATED_REJECTED) if animated?(format)

    dimensions = FastImage.size(StringIO.new(@bytes))
    return reject(ErrorCodes::CORRUPTED) if dimensions.nil?

    width, height = dimensions
    short_edge = [ width, height ].min
    if short_edge < MIN_SHORT_EDGE || width > MAX_WIDTH || height > MAX_HEIGHT
      return reject(ErrorCodes::DIMENSION_OUT_OF_RANGE)
    end

    Result.new(
      ok: true, error_code: nil, format: format,
      width: width, height: height, byte_size: @bytes.bytesize
    )
  end

  private

  def detect_format
    return "png" if @bytes.start_with?(PNG_SIGNATURE)
    return "jpeg" if @bytes.start_with?(JPEG_SIGNATURE)
    return "webp" if @bytes[0, 4] == "RIFF" && @bytes[8, 4] == "WEBP"
    nil
  end

  def animated?(format)
    case format
    when "png"
      @bytes.include?("acTL")
    when "webp"
      # ANIMチャンクの存在、またはVP8X拡張ヘッダーのアニメーションフラグ(bit1)
      @bytes.include?("ANIM") || vp8x_animation_flag?
    else
      false
    end
  end

  def vp8x_animation_flag?
    idx = @bytes.index("VP8X")
    return false if idx.nil?
    flags_offset = idx + 8
    return false if @bytes.bytesize <= flags_offset
    flags_byte = @bytes.getbyte(flags_offset)
    (flags_byte & 0b00000010) != 0
  end

  def reject(error_code)
    Result.new(ok: false, error_code: error_code, format: nil, width: nil, height: nil, byte_size: @bytes.bytesize)
  end
end
