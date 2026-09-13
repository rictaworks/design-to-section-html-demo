require "rails_helper"

RSpec.describe IntakeValidator do
  it "accepts a valid PNG within bounds" do
    result = described_class.validate(png_bytes(width: 400, height: 400))
    expect(result).to be_ok
    expect(result.format).to eq("png")
    expect(result.width).to eq(400)
    expect(result.height).to eq(400)
  end

  it "accepts a valid JPEG" do
    result = described_class.validate(jpeg_bytes(width: 400, height: 400))
    expect(result).to be_ok
    expect(result.format).to eq("jpeg")
  end

  it "accepts a valid WebP" do
    result = described_class.validate(webp_bytes(width: 400, height: 400))
    expect(result).to be_ok
    expect(result.format).to eq("webp")
  end

  it "rejects an unsupported format (e.g. GIF)" do
    result = described_class.validate("GIF89a".b + "\x00" * 20)
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::UNSUPPORTED_FORMAT)
  end

  it "rejects an animated PNG" do
    result = described_class.validate(png_bytes(width: 400, height: 400, animated: true))
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::ANIMATED_REJECTED)
  end

  it "rejects an animated WebP" do
    result = described_class.validate(webp_bytes(width: 400, height: 400, animated: true))
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::ANIMATED_REJECTED)
  end

  it "rejects a WebP whose VP8X animation flag bit is set, even without an ANIM chunk" do
    result = described_class.validate(vp8x_only_animation_flag_webp_bytes(width: 400, height: 400))
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::ANIMATED_REJECTED)
  end

  it "rejects a file exceeding 10MB" do
    huge = png_bytes(width: 10, height: 10) + ("\x00" * 11.megabytes)
    result = described_class.validate(huge)
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::SIZE_EXCEEDED)
  end

  it "rejects an image whose short edge is below 320px" do
    result = described_class.validate(png_bytes(width: 100, height: 500))
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::DIMENSION_OUT_OF_RANGE)
  end

  it "rejects an image wider than 8000px" do
    result = described_class.validate(png_bytes(width: 8001, height: 400))
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::DIMENSION_OUT_OF_RANGE)
  end

  it "rejects a corrupted/undecodable file" do
    result = described_class.validate(corrupted_png_bytes)
    expect(result).not_to be_ok
    expect(result.error_code).to eq(ErrorCodes::CORRUPTED)
  end
end
