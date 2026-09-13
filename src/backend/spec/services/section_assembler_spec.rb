require "rails_helper"

RSpec.describe SectionAssembler do
  it "assembles a full document that passes OutputValidator" do
    conversion = create(:conversion, shell_layout: "single", theme: "light")
    create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::HEADER,
      variant: "without_button", features: { "button_blob_count" => 0 })
    hero = create(:band, conversion: conversion, position: 1, detected_kind: SectionKinds::HERO,
      variant: "no_image", features: { "image_position" => "none", "bg_luminance" => 0.9 })
    create(:band_crop, band: hero, shape: "rect", body: "\xFF\xD8\xFF".b)
    create(:band, conversion: conversion, position: 2, detected_kind: SectionKinds::FEATURES,
      variant: "col_3", features: { "column_count" => 3, "repeat_count" => 3 })
    create(:band, conversion: conversion, position: 3, detected_kind: SectionKinds::FOOTER,
      variant: "col_3", features: { "column_count" => 3 })

    result = described_class.assemble(conversion.reload)

    validation = OutputValidator.validate(result.html)
    expect(validation).to be_valid, -> { validation.reasons.inspect }
    expect(result.html.scan("<h1").size).to eq(1)
    expect(result.html).to include(">") # sanity: non-empty markup produced
  end

  it "assigns h1 to the hero band even when it is not first" do
    conversion = create(:conversion)
    create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::HEADER, variant: "without_button")
    create(:band, conversion: conversion, position: 1, detected_kind: SectionKinds::HERO, variant: "no_image",
      features: { "image_position" => "none" })

    html = described_class.assemble(conversion.reload).html
    expect(html.scan("<h1").size).to eq(1)
    expect(html).to match(%r{<h1[^>]*class="d2h-hero__title"})
  end

  it "falls back to a hidden h1 when no band would otherwise render a heading" do
    conversion = create(:conversion)
    create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::HEADER, variant: "without_button")
    create(:band, conversion: conversion, position: 1, detected_kind: SectionKinds::FOOTER, variant: "col_2",
      features: { "column_count" => 2 })

    html = described_class.assemble(conversion.reload).html
    expect(html.scan("<h1").size).to eq(1)
    expect(html).to include("d2h-visually-hidden")
  end

  it "records a variant_mismatch_fallback notice when features are inconsistent with the kind" do
    conversion = create(:conversion)
    create(:band, conversion: conversion, position: 0, detected_kind: SectionKinds::PRICING,
      variant: "col_3", features: { "column_count" => 1 })

    result = described_class.assemble(conversion.reload)
    expect(result.notices.map { |n| n[:notice_type] }).to include(NoticeTypes::VARIANT_MISMATCH_FALLBACK)
  end
end
