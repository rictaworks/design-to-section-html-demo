require "erb"

# セクション部品カタログ（requirements.md 7章）。12種のセクション部品をHTML文字列として組み立てる。
# 各部品はクラス名に固有の接頭辞を持ち、部品間で衝突しない。imgには必ずaltを付与する。
# 生成物は初稿であり装飾は対象外のため、レイアウトは最小限のCSSクラスで表現する（YAGNI/KISS）。
module ComponentCatalog
  class UnknownKindError < StandardError; end

  PREFIXES = {
    SectionKinds::HEADER => "d2h-header",
    SectionKinds::HERO => "d2h-hero",
    SectionKinds::FEATURES => "d2h-features",
    SectionKinds::IMAGE_WITH_TEXT => "d2h-imgtext",
    SectionKinds::CTA => "d2h-cta",
    SectionKinds::PRICING => "d2h-pricing",
    SectionKinds::TESTIMONIALS => "d2h-testimonials",
    SectionKinds::FAQ => "d2h-faq",
    SectionKinds::GALLERY => "d2h-gallery",
    SectionKinds::LOGOS => "d2h-logos",
    SectionKinds::GENERIC_TEXT => "d2h-generic",
    SectionKinds::FOOTER => "d2h-footer"
  }.freeze

  module_function

  def render(kind, params)
    method_name = "render_#{kind}"
    raise UnknownKindError, kind unless respond_to?(method_name, true)
    send(method_name, params)
  end

  # --- 共通ヘルパ ---

  def h(text)
    ERB::Util.html_escape(text.to_s)
  end

  def image_tag(data_uri, alt, css_class: nil)
    cls = css_class ? %( class="#{h(css_class)}") : ""
    %(<img src="#{data_uri}" alt="#{h(alt)}"#{cls}>)
  end

  def placeholder_image_tag(alt, css_class: nil)
    # 埋め込み予算超過時のプレースホルダ（requirements.md 6.7）：無地のdata URIを用いる
    data_uri = "data:image/svg+xml;utf8,#{ERB::Util.url_encode('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="3"/>')}"
    image_tag(data_uri, alt, css_class: css_class)
  end

  def crop_image_tag(crop, css_class: nil)
    if crop.nil? || crop[:placeholder]
      placeholder_image_tag(ParameterExtractor.static(:image_alt), css_class: css_class)
    else
      image_tag(crop[:data_uri], ParameterExtractor.static(:image_alt), css_class: css_class)
    end
  end

  def heading_tag(level, css_class, text)
    %(<#{level} class="#{h(css_class)}">#{h(text)}</#{level}>)
  end

  # --- 各部品 ---

  def render_header(params)
    p = PREFIXES[SectionKinds::HEADER]
    nav_count = [ [ params[:repeat_count].to_i, 3 ].max, 6 ].min
    nav_items = Array.new(nav_count) { %(<li class="#{p}__nav-item">#{h(ParameterExtractor.static(:nav_item))}</li>) }.join

    button = params[:variant] == "with_button" ? %(<a class="#{p}__button" href="#">#{h(ParameterExtractor.placeholder(:button, params[:features], size: :short))}</a>) : ""

    <<~HTML.strip
      <header class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        <div class="#{p}__inner">
          <span class="#{p}__logo">#{h(ParameterExtractor.static(:nav_item))}</span>
          <nav class="#{p}__nav" aria-label="#{h(ParameterExtractor.static(:nav_aria_label))}">
            <ul class="#{p}__nav-list">#{nav_items}</ul>
          </nav>
          #{button}
        </div>
      </header>
    HTML
  end

  def render_hero(params)
    p = PREFIXES[SectionKinds::HERO]
    image = params[:variant] == "no_image" ? "" : %(<div class="#{p}__media">#{crop_image_tag(params[:primary_crop], css_class: "#{p}__image")}</div>)

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        <div class="#{p}__inner">
          <div class="#{p}__content">
            #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
            <p class="#{p}__body">#{h(ParameterExtractor.placeholder(:body, params[:features]))}</p>
            <div class="#{p}__actions">
              <a class="#{p}__button #{p}__button--primary" href="#">#{h(ParameterExtractor.placeholder(:button, params[:features], size: :short))}</a>
            </div>
          </div>
          #{image}
        </div>
      </section>
    HTML
  end

  def render_features(params)
    p = PREFIXES[SectionKinds::FEATURES]
    count = params[:variant].split("_").last.to_i
    items = Array.new(count) do
      <<~ITEM
        <li class="#{p}__item">
          #{crop_image_tag(nil, css_class: "#{p}__icon")}
          #{heading_tag('h3', "#{p}__item-title", ParameterExtractor.placeholder(:subheading, params[:features]))}
          <p class="#{p}__item-body">#{h(ParameterExtractor.placeholder(:body, params[:features]))}</p>
        </li>
      ITEM
    end.join

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_image_with_text(params)
    p = PREFIXES[SectionKinds::IMAGE_WITH_TEXT]

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        <div class="#{p}__media">#{crop_image_tag(params[:primary_crop], css_class: "#{p}__image")}</div>
        <div class="#{p}__content">
          #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
          <p class="#{p}__body">#{h(ParameterExtractor.placeholder(:body, params[:features]))}</p>
          <a class="#{p}__button" href="#">#{h(ParameterExtractor.placeholder(:button, params[:features], size: :short))}</a>
        </div>
      </section>
    HTML
  end

  def render_cta(params)
    p = PREFIXES[SectionKinds::CTA]

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features], size: :short))}
        <p class="#{p}__body">#{h(ParameterExtractor.placeholder(:body, params[:features], size: :short))}</p>
        <a class="#{p}__button" href="#">#{h(ParameterExtractor.placeholder(:button, params[:features], size: :short))}</a>
      </section>
    HTML
  end

  def render_pricing(params)
    p = PREFIXES[SectionKinds::PRICING]
    count = params[:variant].split("_").last.to_i
    emphasized_index = count == 3 ? 1 : nil
    items = Array.new(count) do |i|
      emphasized = i == emphasized_index
      <<~ITEM
        <li class="#{p}__plan #{emphasized ? "#{p}__plan--emphasized" : ""}">
          #{heading_tag('h3', "#{p}__plan-name", ParameterExtractor.static(:pricing_plan_name))}
          <p class="#{p}__plan-price">#{h(ParameterExtractor.static(:pricing_price))}</p>
          <ul class="#{p}__plan-features">
            <li>#{h(ParameterExtractor.static(:pricing_feature))}</li>
            <li>#{h(ParameterExtractor.static(:pricing_feature))}</li>
            <li>#{h(ParameterExtractor.static(:pricing_feature))}</li>
          </ul>
          <a class="#{p}__plan-button" href="#">#{h(ParameterExtractor.placeholder(:button, params[:features], size: :short))}</a>
        </li>
      ITEM
    end.join

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_testimonials(params)
    p = PREFIXES[SectionKinds::TESTIMONIALS]
    count = params[:variant].split("_").last.to_i
    items = Array.new(count) do
      <<~ITEM
        <li class="#{p}__item">
          #{crop_image_tag(nil, css_class: "#{p}__avatar")}
          <blockquote class="#{p}__quote">#{h(ParameterExtractor.placeholder(:body, params[:features]))}</blockquote>
          <p class="#{p}__name">#{h(ParameterExtractor.static(:testimonial_name))}</p>
          <p class="#{p}__role">#{h(ParameterExtractor.static(:testimonial_role))}</p>
        </li>
      ITEM
    end.join

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_faq(params)
    p = PREFIXES[SectionKinds::FAQ]
    count = [ [ params[:repeat_count].to_i, 2 ].max, 6 ].min
    items = Array.new(count) do
      <<~ITEM
        <li class="#{p}__item">
          #{heading_tag('h3', "#{p}__question", ParameterExtractor.static(:faq_question))}
          <p class="#{p}__answer">#{h(ParameterExtractor.static(:faq_answer))}</p>
        </li>
      ITEM
    end.join

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_gallery(params)
    p = PREFIXES[SectionKinds::GALLERY]
    cols = params[:variant].split("_").last.to_i
    count = [ [ params[:repeat_count].to_i, cols ].max, 12 ].min
    crops = params[:crops] || []
    items = Array.new(count) { |i| %(<li class="#{p}__item">#{crop_image_tag(crops[i], css_class: "#{p}__image")}</li>) }.join

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_logos(params)
    p = PREFIXES[SectionKinds::LOGOS]
    count = [ [ params[:repeat_count].to_i, 4 ].max, 8 ].min
    crops = params[:crops] || []
    items = Array.new(count) { |i| %(<li class="#{p}__item">#{crop_image_tag(crops[i], css_class: "#{p}__logo")}</li>) }.join

    <<~HTML.strip
      <section class="#{p} #{text_color_class(p, params)}">
        <ul class="#{p}__list">#{items}</ul>
      </section>
    HTML
  end

  def render_generic_text(params)
    p = PREFIXES[SectionKinds::GENERIC_TEXT]

    <<~HTML.strip
      <section class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        #{heading_tag(params[:heading_tag], "#{p}__title", ParameterExtractor.placeholder(:heading, params[:features]))}
        <p class="#{p}__body">#{h(ParameterExtractor.placeholder(:body, params[:features]))}</p>
      </section>
    HTML
  end

  def render_footer(params)
    p = PREFIXES[SectionKinds::FOOTER]
    cols = params[:variant].split("_").last.to_i
    columns = Array.new(cols) do
      links = Array.new(3) { %(<li><a href="#">#{h(ParameterExtractor.static(:footer_link))}</a></li>) }.join
      <<~COL
        <div class="#{p}__column">
          #{heading_tag('h3', "#{p}__column-title", ParameterExtractor.static(:footer_column_heading))}
          <ul class="#{p}__links">#{links}</ul>
        </div>
      COL
    end.join

    <<~HTML.strip
      <footer class="#{p} #{p}--#{params[:variant]} #{text_color_class(p, params)}">
        <div class="#{p}__columns">#{columns}</div>
        <p class="#{p}__copyright">#{h(ParameterExtractor.static(:footer_copyright))}</p>
      </footer>
    HTML
  end

  def text_color_class(prefix, params)
    "#{prefix}--#{params[:text_color] == 'light' ? 'on-dark' : 'on-light'}"
  end
end
