# 帯特徴からレンダリングパラメータ（文字色・アクセント色・プレースホルダ文言）を決定する
# （requirements.md 6.7）。デザイン画像から読み取った実文字は使用しない。
class ParameterExtractor
  DEFAULT_ACCENT_COLOR = "#2563eb"

  def self.text_color(features)
    luminance = features["bg_luminance"] || features[:bg_luminance]
    luminance.nil? || luminance >= 0.5 ? "dark" : "light"
  end

  def self.accent_color(features, page_accent_color)
    features["accent_color_hex"] || features[:accent_color_hex] || page_accent_color || DEFAULT_ACCENT_COLOR
  end

  # category: :heading, :subheading, :body, :button
  def self.placeholder(category, features, size: nil)
    bucket = size || size_bucket(features)
    Rails.application.config.x.placeholders.dig(category, bucket) ||
      Rails.application.config.x.placeholders.dig(category, :medium) ||
      Rails.application.config.x.placeholders[category]
  end

  def self.static(key)
    Rails.application.config.x.placeholders.fetch(key)
  end

  def self.size_bucket(features)
    columns = (features["column_count"] || features[:column_count] || 1).to_i
    return :short if columns >= 4
    return :medium if columns >= 2
    :long
  end
end
