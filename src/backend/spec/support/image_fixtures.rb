require "zlib"

# テスト用に最小構成のPNG/JPEG/WebPバイト列を決定的に生成する。
# 外部の画像ファイル・ネットワークに依存しない。
module ImageFixtures
  module_function

  def png_bytes(width: 10, height: 10, color: [ 255, 0, 0 ], animated: false)
    signature = "\x89PNG\r\n\x1a\n".b
    ihdr = [ width, height, 8, 2, 0, 0, 0 ].pack("N2C5")
    row = ([ 0 ] + color * width).pack("C*")
    raw = row * height
    idat = Zlib::Deflate.deflate(raw)

    chunks = +""
    chunks << png_chunk("IHDR", ihdr)
    chunks << png_chunk("acTL", [ 2, 0 ].pack("N2")) if animated
    chunks << png_chunk("IDAT", idat)
    chunks << png_chunk("IEND", "")

    signature + chunks
  end

  def png_chunk(type, data)
    [ data.bytesize ].pack("N") + type + data + [ Zlib.crc32(type + data) ].pack("N")
  end

  def jpeg_bytes(width: 10, height: 10)
    soi = "\xFF\xD8".b
    # APP0(JFIF)
    app0 = ("\xFF\xE0".b + [ 16 ].pack("n").b + "JFIF\x00".b + "\x01\x01\x00\x00\x01\x00\x01\x00\x00".b)
    # SOF0（ベースライン）：解像度をwidth/heightに設定
    sof0 = ("\xFF\xC0".b + [ 11 ].pack("n").b + [ 8 ].pack("C").b + [ height, width ].pack("n2").b + "\x01\x01\x11\x00".b)
    eoi = "\xFF\xD9".b
    (soi + app0 + sof0 + eoi).b
  end

  # animated: trueの場合、VP8X拡張ヘッダーのANIMATIONフラグ(bit1)とANIMチャンクの両方を
  # 付与する。vp8x_only_animation_flag_webp_bytesはANIMチャンクを付けずVP8Xフラグのみを
  # 立てる（IntakeValidator#vp8x_animation_flag?のビット判定単体を検証するため）。
  def webp_bytes(width: 10, height: 10, animated: false)
    flags = animated ? 0b00000010 : 0b00000000 # bit1: ANIMATION
    vp8x = "VP8X".b + [ 10 ].pack("V").b +
      [ flags ].pack("C").b + "\x00\x00\x00".b +
      [ width - 1 ].pack("V").b[0, 3] + [ height - 1 ].pack("V").b[0, 3]
    payload = vp8x
    payload += "ANIM".b + [ 4 ].pack("V").b + [ 0x000000 ].pack("V").b if animated

    ("RIFF".b + [ payload.bytesize + 4 ].pack("V").b + "WEBP".b + payload).b
  end

  def vp8x_only_animation_flag_webp_bytes(width: 10, height: 10)
    flags = 0b00000010 # bit1: ANIMATION（ANIMチャンクは付けない）
    vp8x = "VP8X".b + [ 10 ].pack("V").b +
      [ flags ].pack("C").b + "\x00\x00\x00".b +
      [ width - 1 ].pack("V").b[0, 3] + [ height - 1 ].pack("V").b[0, 3]
    ("RIFF".b + [ vp8x.bytesize + 4 ].pack("V").b + "WEBP".b + vp8x).b
  end

  def corrupted_png_bytes
    # PNGシグネチャの直後を意図的に破損させ、IHDRチャンクとして解釈できないようにする
    ("\x89PNG\r\n\x1a\n".b + "\x00\x00\x00\x0d".b + "IHDR".b + "\x00\x00".b)
  end
end

RSpec.configure do |config|
  config.include ImageFixtures
end
