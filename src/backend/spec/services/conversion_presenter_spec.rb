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
  end
end
