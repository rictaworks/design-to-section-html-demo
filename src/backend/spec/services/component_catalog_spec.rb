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
end
