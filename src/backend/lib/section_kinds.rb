# セクション種別コード（requirements.md 6.6・7章の12種）。
# 解析層(FastAPI)のレスポンスもこのコード体系を用いる前提。
module SectionKinds
  HEADER = "header"
  HERO = "hero"
  FEATURES = "features"
  IMAGE_WITH_TEXT = "image_with_text"
  CTA = "cta"
  PRICING = "pricing"
  TESTIMONIALS = "testimonials"
  FAQ = "faq"
  GALLERY = "gallery"
  LOGOS = "logos"
  GENERIC_TEXT = "generic_text"
  FOOTER = "footer"

  ALL = [
    HEADER, HERO, FEATURES, IMAGE_WITH_TEXT, CTA, PRICING,
    TESTIMONIALS, FAQ, GALLERY, LOGOS, GENERIC_TEXT, FOOTER
  ].freeze
end
