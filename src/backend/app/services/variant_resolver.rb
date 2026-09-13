# 帯特徴からバリアントを決定する（requirements.md 6.7・7章）。
# 種別に対して不整合な特徴の場合は種別の既定バリアントを用い、呼び出し側で注意事項を記録する。
class VariantResolver
  Resolution = Struct.new(:variant, :mismatch, keyword_init: true)

  DEFAULTS = {
    SectionKinds::HEADER => "without_button",
    SectionKinds::HERO => "no_image",
    SectionKinds::FEATURES => "col_3",
    SectionKinds::IMAGE_WITH_TEXT => "image_left",
    SectionKinds::CTA => "light",
    SectionKinds::PRICING => "col_3",
    SectionKinds::TESTIMONIALS => "col_1",
    SectionKinds::FAQ => "col_1",
    SectionKinds::GALLERY => "col_3",
    SectionKinds::LOGOS => "default",
    SectionKinds::GENERIC_TEXT => "left",
    SectionKinds::FOOTER => "col_3"
  }.freeze

  IMAGE_POSITION_TO_HERO_VARIANT = {
    "left" => "image_left", "right" => "image_right",
    "top" => "image_bottom", "full" => "full_image", "none" => "no_image"
  }.freeze

  def self.resolve(kind, features)
    new(kind, features).resolve
  end

  def initialize(kind, features)
    @kind = kind
    @features = features.symbolize_keys
  end

  def resolve
    variant = compute
    if variant.nil?
      Resolution.new(variant: DEFAULTS.fetch(@kind, "default"), mismatch: true)
    else
      Resolution.new(variant: variant, mismatch: false)
    end
  end

  private

  def compute
    case @kind
    when SectionKinds::HEADER
      @features[:button_blob_count].to_i > 0 ? "with_button" : "without_button"
    when SectionKinds::HERO
      IMAGE_POSITION_TO_HERO_VARIANT[@features[:image_position]]
    when SectionKinds::FEATURES, SectionKinds::GALLERY, SectionKinds::FOOTER
      col = @features[:column_count].to_i
      col.between?(2, 4) ? "col_#{col}" : nil
    when SectionKinds::IMAGE_WITH_TEXT
      pos = @features[:image_position]
      %w[left right].include?(pos) ? "image_#{pos}" : nil
    when SectionKinds::CTA
      luminance = @features[:bg_luminance]
      luminance.nil? ? nil : (luminance < 0.5 ? "dark" : "light")
    when SectionKinds::PRICING
      col = @features[:column_count].to_i
      col.between?(2, 4) ? "col_#{col}" : nil
    when SectionKinds::TESTIMONIALS
      count = [ [ @features[:repeat_count].to_i, 1 ].max, 3 ].min
      "col_#{count}"
    when SectionKinds::FAQ
      "col_1"
    when SectionKinds::LOGOS
      "default"
    when SectionKinds::GENERIC_TEXT
      %w[left center].include?(@features[:alignment]) ? @features[:alignment] : nil
    end
  end
end
