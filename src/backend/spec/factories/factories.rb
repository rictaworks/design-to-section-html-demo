FactoryBot.define do
  factory :session do
    sequence(:session_id) { |n| "sess_#{n}_#{SecureRandom.hex(4)}" }
    user_agent_class { "desktop" }
    last_seen_at { Time.current }
  end

  factory :conversion do
    session
    state { "uploaded" }
    shell_layout { "single" }
    theme { "light" }
    mobile_design { false }
    version { 0 }
  end

  factory :source_image do
    conversion
    session_id { conversion.session_id }
    format { "png" }
    width { 1200 }
    height { 3000 }
    byte_size { 12_345 }
    body { "\x89PNG\r\n".b }
    work_scale { 1.0 }
  end

  factory :band do
    conversion
    session_id { conversion.session_id }
    sequence(:position) { |n| n }
    top_y { 0 }
    bottom_y { 200 }
    features { {} }
    detected_kind { SectionKinds::HERO }
    confidence { 0.8 }
    variant { "default" }
    state { "detected" }
  end

  factory :band_crop do
    band
    session_id { band.session_id }
    left_x { 0 }
    top_y { 0 }
    width { 100 }
    height { 100 }
    shape { "rect" }
    body { "\xFF\xD8\xFF".b }
    placeholder { false }
  end

  factory :output do
    conversion
    session_id { conversion.session_id }
    version { 1 }
    html { "<!doctype html><html><head><title>t</title></head><body><h1>t</h1></body></html>" }
    byte_size { 100 }
    generated_at { Time.current }
  end

  factory :notice do
    conversion
    session_id { conversion.session_id }
    notice_type { NoticeTypes::MOBILE_DESIGN_DETECTED }
    detail { {} }
  end

  factory :conversion_event do
    conversion
    session_id { conversion.session_id }
    occurred_at { Time.current }
    event_type { "created" }
    detail { {} }
  end
end
