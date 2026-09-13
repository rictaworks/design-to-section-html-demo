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

  describe ".reassemble!" do
    it "does not duplicate a variant_mismatch_fallback notice each time an unrelated edit re-triggers reassembly for a still-mismatched band" do
      conversion = create(:conversion)
      create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::PRICING,
        variant: "col_3", features: { "column_count" => 1 })

      described_class.reassemble!(conversion)
      described_class.reassemble!(conversion)

      expect(conversion.notices.where(notice_type: NoticeTypes::VARIANT_MISMATCH_FALLBACK).count).to eq(1)
    end

    it "clears a stale variant_mismatch_fallback notice once the band no longer mismatches" do
      conversion = create(:conversion)
      band = create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::PRICING,
        variant: "col_3", features: { "column_count" => 1 })

      described_class.reassemble!(conversion)
      expect(conversion.notices.where(notice_type: NoticeTypes::VARIANT_MISMATCH_FALLBACK).count).to eq(1)

      band.update!(features: { "column_count" => 3 })
      described_class.reassemble!(conversion)

      expect(conversion.notices.where(notice_type: NoticeTypes::VARIANT_MISMATCH_FALLBACK).count).to eq(0)
    end
  end
end
