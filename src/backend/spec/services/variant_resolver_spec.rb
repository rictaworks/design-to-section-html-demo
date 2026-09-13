require "rails_helper"

RSpec.describe VariantResolver do
  it "resolves header with_button when a button blob is present" do
    r = described_class.resolve(SectionKinds::HEADER, { "button_blob_count" => 1 })
    expect(r.variant).to eq("with_button")
    expect(r.mismatch).to be false
  end

  it "resolves hero variant from image_position" do
    r = described_class.resolve(SectionKinds::HERO, { "image_position" => "right" })
    expect(r.variant).to eq("image_right")
  end

  it "falls back to the default variant and flags mismatch for pricing with column_count 1" do
    r = described_class.resolve(SectionKinds::PRICING, { "column_count" => 1 })
    expect(r.variant).to eq(VariantResolver::DEFAULTS[SectionKinds::PRICING])
    expect(r.mismatch).to be true
  end

  it "clamps testimonials repeat_count into 1..3" do
    r = described_class.resolve(SectionKinds::TESTIMONIALS, { "repeat_count" => 9 })
    expect(r.variant).to eq("col_3")
  end
end
