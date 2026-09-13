module AnalysisStub
  def stub_analysis_success(bands: default_bands, notices: [], work_scale: 0.5, shell_layout: "single")
    stub_request(:post, %r{\A#{Regexp.escape(ENV.fetch('ANALYSIS_SERVICE_URL', 'http://localhost:8001'))}/v1/analyze})
      .to_return(
        status: 200,
        body: {
          theme: "light", mobile_design: false, shell_layout: shell_layout,
          work_scale: work_scale, work_width: 1200, work_height: 3000,
          bands: bands, notices: notices
        }.to_json,
        headers: { "Content-Type" => "application/json" }
      )
  end

  def stub_refeature_success(bands:, notices: [])
    stub_request(:post, %r{\A#{Regexp.escape(ENV.fetch('ANALYSIS_SERVICE_URL', 'http://localhost:8001'))}/v1/refeature})
      .to_return(status: 200, body: { bands: bands, notices: notices }.to_json,
                 headers: { "Content-Type" => "application/json" })
  end

  def default_bands
    [
      { position: 0, top_y: 0, bottom_y: 80, detected_kind: SectionKinds::HEADER, confidence: 0.9,
        runner_up_kind: nil, features: { button_blob_count: 0 }, crops: [] },
      { position: 1, top_y: 80, bottom_y: 800, detected_kind: SectionKinds::HERO, confidence: 0.85,
        runner_up_kind: nil, features: { image_position: "none", bg_luminance: 0.9 }, crops: [] },
      { position: 2, top_y: 800, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.7,
        runner_up_kind: nil, features: { column_count: 2 }, crops: [] }
    ]
  end
end

RSpec.configure { |c| c.include AnalysisStub }
