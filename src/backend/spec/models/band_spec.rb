require "rails_helper"

RSpec.describe Band, type: :model do
  it "is valid with default factory" do
    expect(build(:band)).to be_valid
  end

  it "rejects bottom_y <= top_y" do
    band = build(:band, top_y: 100, bottom_y: 100)
    expect(band).not_to be_valid
  end

  describe "#kind" do
    it "prefers user_kind over detected_kind" do
      band = build(:band, detected_kind: SectionKinds::HERO, user_kind: SectionKinds::FAQ)
      expect(band.kind).to eq(SectionKinds::FAQ)
    end

    it "falls back to detected_kind when user_kind is absent" do
      band = build(:band, detected_kind: SectionKinds::HERO, user_kind: nil)
      expect(band.kind).to eq(SectionKinds::HERO)
    end
  end

  it "serializes features as a hash round-trip" do
    band = create(:band, features: { "column_count" => 3 })
    expect(band.reload.features).to eq("column_count" => 3)
  end
end
