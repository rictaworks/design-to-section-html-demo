# 生成物に埋め込む単一CSS（requirements.md 6.8・8章）。
# 外部フォント／外部スタイルシートを参照せず、システムフォントを列挙する。
module StylesheetBuilder
  SYSTEM_FONTS =
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Hiragino Sans", ' \
    '"Noto Sans JP", "Yu Gothic", Meiryo, sans-serif'

  CSS = <<~CSS
    :root { color-scheme: light dark; }
    * { box-sizing: border-box; }
    body.d2h-body {
      margin: 0;
      font-family: #{SYSTEM_FONTS};
      line-height: 1.6;
      overflow-wrap: break-word;
    }
    .d2h-theme--light { background: #ffffff; color: #1a1a1a; }
    .d2h-theme--dark { background: #121212; color: #f2f2f2; }

    img { max-width: 100%; height: auto; display: block; }

    .d2h-shell__content, .d2h-header__inner, .d2h-footer__columns {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.5rem 1rem;
    }

    .d2h-shell--sidebar { display: flex; flex-direction: column; }
    @media (min-width: 1024px) {
      .d2h-shell--sidebar { flex-direction: row; align-items: flex-start; }
      .d2h-shell--sidebar .d2h-shell__content { flex: 3; }
      .d2h-shell--sidebar .d2h-shell__aside { flex: 1; }
    }

    [class*="--on-dark"] { background: #1f2933; color: #f5f7fa; }
    [class*="--on-light"] { background: transparent; color: inherit; }

    h1, h2, h3 { font-weight: 700; line-height: 1.3; }
    h1 { font-size: clamp(1.75rem, 4vw + 1rem, 3rem); }
    h2 { font-size: clamp(1.4rem, 3vw + 1rem, 2.25rem); }
    h3 { font-size: clamp(1.1rem, 1.5vw + 1rem, 1.5rem); }

    .d2h-visually-hidden {
      position: absolute; width: 1px; height: 1px; overflow: hidden;
      clip: rect(0 0 0 0); white-space: nowrap;
    }

    .d2h-header__inner, .d2h-hero__inner, .d2h-imgtext {
      display: flex; flex-wrap: wrap; align-items: center; gap: 1.5rem;
    }
    .d2h-header__inner { justify-content: space-between; }
    .d2h-header__nav-list { list-style: none; display: flex; gap: 1rem; padding: 0; margin: 0; flex-wrap: wrap; }

    .d2h-hero--image_left .d2h-hero__inner, .d2h-imgtext--image_left { flex-direction: row; }
    .d2h-hero--image_right .d2h-hero__inner, .d2h-imgtext--image_right { flex-direction: row-reverse; }
    .d2h-hero__content, .d2h-hero__media, .d2h-imgtext__content, .d2h-imgtext__media { flex: 1 1 320px; }

    @media (max-width: 599px) {
      .d2h-hero__inner, .d2h-imgtext { flex-direction: column-reverse; }
    }

    .d2h-features__list, .d2h-pricing__list, .d2h-testimonials__list,
    .d2h-gallery__list, .d2h-footer__columns {
      display: grid; gap: 1.5rem; list-style: none; padding: 0; margin: 0;
      grid-template-columns: 1fr;
    }
    @media (min-width: 600px) {
      .d2h-features--col_2 .d2h-features__list, .d2h-pricing--col_2 .d2h-pricing__list,
      .d2h-testimonials--col_2 .d2h-testimonials__list, .d2h-gallery--col_2 .d2h-gallery__list,
      .d2h-features--col_3 .d2h-features__list, .d2h-pricing--col_3 .d2h-pricing__list,
      .d2h-testimonials--col_3 .d2h-testimonials__list, .d2h-gallery--col_3 .d2h-gallery__list,
      .d2h-features--col_4 .d2h-features__list, .d2h-pricing--col_4 .d2h-pricing__list,
      .d2h-gallery--col_4 .d2h-gallery__list {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    @media (min-width: 1024px) {
      .d2h-features--col_3 .d2h-features__list, .d2h-pricing--col_3 .d2h-pricing__list,
      .d2h-testimonials--col_3 .d2h-testimonials__list, .d2h-gallery--col_3 .d2h-gallery__list {
        grid-template-columns: repeat(3, 1fr);
      }
      .d2h-features--col_4 .d2h-features__list, .d2h-pricing--col_4 .d2h-pricing__list,
      .d2h-gallery--col_4 .d2h-gallery__list {
        grid-template-columns: repeat(4, 1fr);
      }
    }

    .d2h-logos__list {
      list-style: none; display: flex; flex-wrap: wrap; gap: 1.5rem;
      padding: 1.5rem 1rem; margin: 0; justify-content: center;
    }
    .d2h-logos__logo { max-width: 96px; }

    .d2h-faq__list { list-style: none; padding: 1.5rem 1rem; margin: 0; max-width: 1200px; margin-inline: auto; }
    .d2h-faq__item { padding-block: 0.75rem; border-bottom: 1px solid currentColor; }

    .d2h-generic, .d2h-cta { padding: 1.5rem 1rem; max-width: 1200px; margin: 0 auto; }
    .d2h-generic--center { text-align: center; }
    .d2h-cta { text-align: center; }
    .d2h-cta--dark { background: #111827; color: #f9fafb; }
    .d2h-cta--light { background: #f3f4f6; color: #111827; }

    a[class*="__button"] {
      display: inline-block; padding: 0.6rem 1.2rem; border-radius: 0.375rem;
      background: #2563eb; color: #ffffff; text-decoration: none; font-weight: 600;
    }

    .d2h-pricing__plan, .d2h-testimonials__item, .d2h-features__item {
      border: 1px solid rgba(127, 127, 127, 0.3); border-radius: 0.5rem; padding: 1.5rem;
    }
    .d2h-pricing__plan--emphasized { border-width: 2px; }

    .d2h-footer { padding-block: 2rem; }
    .d2h-footer__links { list-style: none; padding: 0; margin: 0.5rem 0 0; }
    .d2h-footer__copyright { text-align: center; padding-top: 1.5rem; font-size: 0.875rem; }
  CSS

  def self.build
    CSS
  end
end
