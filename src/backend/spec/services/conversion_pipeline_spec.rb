require "rails_helper"

RSpec.describe ConversionPipeline do
  describe ".persist_notices" do
    it "resolves band_id directly when the notice already carries one (SectionAssembler's notices)" do
      conversion = create(:conversion)
      band = create(:band, conversion: conversion)

      described_class.persist_notices(conversion, [
        { notice_type: NoticeTypes::VARIANT_MISMATCH_FALLBACK, band_id: band.id, detail: {} }
      ])

      notice = conversion.notices.last
      expect(notice.band_id).to eq(band.id)
    end

    it "resolves band_id from band_position when the notice carries a position (analysis layer's notices)" do
      conversion = create(:conversion)
      band = create(:band, conversion: conversion, position: 3)

      described_class.persist_notices(conversion, [
        { notice_type: NoticeTypes::LOW_CONFIDENCE_KIND, band_position: 3, detail: {} }
      ])

      notice = conversion.notices.last
      expect(notice.band_id).to eq(band.id)
    end

    it "leaves band_id nil for a conversion-level notice with neither band_id nor band_position" do
      conversion = create(:conversion)

      described_class.persist_notices(conversion, [
        { notice_type: NoticeTypes::NO_SEPARATOR_FOUND, detail: {} }
      ])

      expect(conversion.notices.last.band_id).to be_nil
    end
  end
end
