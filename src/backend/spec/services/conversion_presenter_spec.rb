require "rails_helper"

RSpec.describe ConversionPresenter do
  describe ".detail" do
    it "includes each notice's id, so the frontend has a stable React key" do
      conversion = create(:conversion)
      band = create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::HEADER,
        variant: "without_button")
      notice = conversion.notices.create!(
        session_id: conversion.session_id, band: band,
        notice_type: NoticeTypes::LOW_CONFIDENCE_KIND, detail: { "kind" => SectionKinds::HEADER }
      )

      json = described_class.detail(conversion.reload)

      expect(json[:notices].first[:id]).to eq(notice.id)
    end

    it "rounds work_height the same way normalize.py rounds the actual work image height (round-half-to-even), " \
       "so the frontend overlay divides by the exact height bands were measured against" do
      conversion = create(:conversion)
      create(:source_image, conversion: conversion, height: 641, work_scale: 0.5) # 641 * 0.5 == 320.5

      json = described_class.detail(conversion.reload)

      # Python: round(320.5) == 320 (banker's rounding). Ruby's plain Float#round would give 321.
      expect(json[:source_image][:work_height]).to eq(320)
    end
  end
end
