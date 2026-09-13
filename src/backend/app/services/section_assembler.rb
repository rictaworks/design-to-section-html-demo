require "base64"

# 部品組み立て（requirements.md 6.8・7章・8章）。
# 帯の順序どおりに部品を並べ、単一HTMLファイルとして組み立てる。並べ替えは行わない。
class SectionAssembler
  Result = Struct.new(:html, :notices, keyword_init: true)

  NO_HEADING_KINDS = [ SectionKinds::HEADER, SectionKinds::FOOTER, SectionKinds::LOGOS ].freeze

  def self.assemble(conversion)
    new(conversion).assemble
  end

  def initialize(conversion)
    @conversion = conversion
    @bands = conversion.bands.assemblable.includes(:band_crops).to_a
    @notices = []
  end

  def assemble
    page_accent_color = @bands.lazy.map { |b| b.features["accent_color_hex"] }.reject(&:blank?).first
    h1_band = pick_h1_band

    sections = @bands.map do |band|
      render_band(band, heading_tag: (band.equal?(h1_band) ? "h1" : "h2"), page_accent_color: page_accent_color)
    end

    body = build_body(sections, h1_band.nil?)
    html = build_document(body)

    Result.new(html: html, notices: @notices)
  end

  private

  def pick_h1_band
    @bands.find { |b| b.kind == SectionKinds::HERO } ||
      @bands.find { |b| !NO_HEADING_KINDS.include?(b.kind) }
  end

  def render_band(band, heading_tag:, page_accent_color:)
    features = band.features
    resolution = VariantResolver.resolve(band.kind, features)
    if resolution.mismatch
      @notices << { notice_type: NoticeTypes::VARIANT_MISMATCH_FALLBACK, band_id: band.id,
                     detail: { kind: band.kind } }
    end

    crops = band.band_crops.map { |c| crop_param(c) }

    ComponentCatalog.render(band.kind, {
      variant: resolution.variant,
      features: features,
      text_color: ParameterExtractor.text_color(features),
      heading_tag: heading_tag,
      repeat_count: features["repeat_count"],
      crops: crops,
      primary_crop: crops.first
    })
  end

  def crop_param(crop)
    return { placeholder: true } if crop.placeholder? || crop.body.blank?

    mime = crop.shape == "circle" ? "image/png" : "image/jpeg"
    { placeholder: false, data_uri: "data:#{mime};base64,#{Base64.strict_encode64(crop.body)}" }
  end

  def build_body(sections, need_fallback_h1)
    fallback_h1 = need_fallback_h1 ? %(<h1 class="d2h-visually-hidden">#{ComponentCatalog.h(ParameterExtractor.static(:heading_fallback))}</h1>) : ""

    if @conversion.shell_layout == "sidebar" && sections.size > 1
      aside = sections.pop
      <<~HTML
        #{fallback_h1}
        <div class="d2h-shell d2h-shell--sidebar">
          <main class="d2h-shell__content">#{sections.join}</main>
          <aside class="d2h-shell__aside">#{aside}</aside>
        </div>
      HTML
    else
      "#{fallback_h1}<main class=\"d2h-shell__content\">#{sections.join}</main>"
    end
  end

  def build_document(body)
    <<~HTML
      <!doctype html>
      <html lang="ja">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>#{ComponentCatalog.h(ParameterExtractor.static(:document_title))}</title>
        <style>#{StylesheetBuilder.build}</style>
      </head>
      <body class="d2h-body d2h-theme--#{@conversion.theme}">
      #{body}
      </body>
      </html>
    HTML
  end
end
