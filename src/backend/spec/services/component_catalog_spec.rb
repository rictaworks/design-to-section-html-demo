require "rails_helper"

RSpec.describe ComponentCatalog do
  base_features = {
    "column_count" => 3, "repeat_count" => 4, "image_position" => "left",
    "alignment" => "left", "bg_luminance" => 0.9, "accent_color_hex" => "#ff0000",
    "button_blob_count" => 1
  }

  SectionKinds::ALL.each do |kind|
    it "renders valid, well-formed HTML for #{kind} with every img having alt" do
      variant = VariantResolver.resolve(kind, base_features).variant
      html = described_class.render(kind, {
        variant: variant, features: base_features, text_color: "dark",
        heading_tag: "h2", repeat_count: 4, crops: [], primary_crop: nil
      })

      fragment = Nokogiri::HTML5.fragment(html)
      expect(fragment.errors).to be_empty
      fragment.css("img").each { |img| expect(img["alt"]).to be_present }
      expect(html).not_to include("http://")
      expect(html).not_to include("https://")
      expect(html.downcase).not_to include("<script")
    end
  end

  it "prefixes classes distinctly per kind so components never collide" do
    prefixes = ComponentCatalog::PREFIXES.values
    expect(prefixes.uniq.size).to eq(prefixes.size)
  end

  it "renders the footer with its column-count variant class, and the stylesheet defines a matching responsive rule" do
    html = described_class.render(SectionKinds::FOOTER, {
      variant: "col_3", features: base_features, text_color: "dark",
      heading_tag: "h2", repeat_count: 3, crops: [], primary_crop: nil
    })
    expect(html).to include("d2h-footer--col_3")
    expect(StylesheetBuilder::CSS).to include(".d2h-footer--col_3 .d2h-footer__columns")
  end

  it "keeps the shared wrapper padding/margin for .d2h-footer__columns instead of it being overridden by the list-reset rule" do
    css = StylesheetBuilder::CSS
    wrapper_rule = css[/\.d2h-shell__content,\s*\.d2h-header__inner,\s*\.d2h-footer__columns\s*\{[^}]*\}/]
    expect(wrapper_rule).to include("padding: 1.5rem 1rem")

    list_reset_rule = css[/\.d2h-features__list,[^{]*\{[^}]*\}/]
    expect(list_reset_rule).not_to include(".d2h-footer__columns")
  end

  it "renders CTA using the shared text_color_class mechanism, like every other section" do
    html = described_class.render(SectionKinds::CTA, {
      variant: "dark", features: base_features, text_color: "light",
      heading_tag: "h2", repeat_count: nil, crops: [], primary_crop: nil
    })
    expect(html).to include("d2h-cta--on-dark")
  end

  it "renders as many gallery items as repeat_count, like the other repeating components" do
    html_with_6 = described_class.render(SectionKinds::GALLERY, {
      variant: "cols_3", features: base_features, text_color: "dark",
      heading_tag: "h2", repeat_count: 6, crops: [], primary_crop: nil
    })
    html_with_9 = described_class.render(SectionKinds::GALLERY, {
      variant: "cols_3", features: base_features, text_color: "dark",
      heading_tag: "h2", repeat_count: 9, crops: [], primary_crop: nil
    })

    count = ->(html) { Nokogiri::HTML5.fragment(html).css("li").size }
    expect(count.call(html_with_6)).to eq(6)
    expect(count.call(html_with_9)).to eq(9)
  end
end
