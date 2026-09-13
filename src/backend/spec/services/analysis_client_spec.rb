require "rails_helper"

RSpec.describe AnalysisClient do
  subject(:client) { described_class.new(base_url: "http://analysis.test") }

  describe "#analyze" do
    it "posts the image and parses the JSON result" do
      stub_request(:post, "http://analysis.test/v1/analyze")
        .to_return(
          status: 200,
          body: { theme: "light", bands: [], notices: [] }.to_json,
          headers: { "Content-Type" => "application/json" }
        )

      result = client.analyze(bytes: "fakebytes", filename: "a.png", content_type: "image/png")
      expect(result[:theme]).to eq("light")
    end

    it "raises TimeoutError when the analysis service times out" do
      stub_request(:post, "http://analysis.test/v1/analyze").to_timeout

      expect { client.analyze(bytes: "x", filename: "a.png", content_type: "image/png") }
        .to raise_error(AnalysisClient::TimeoutError)
    end

    it "raises UnreachableError when the analysis service is unreachable" do
      stub_request(:post, "http://analysis.test/v1/analyze").to_raise(Errno::ECONNREFUSED)

      expect { client.analyze(bytes: "x", filename: "a.png", content_type: "image/png") }
        .to raise_error(AnalysisClient::UnreachableError)
    end

    it "raises DecodeFailedError on 422" do
      stub_request(:post, "http://analysis.test/v1/analyze")
        .to_return(status: 422, body: { error: "decode_failed" }.to_json)

      expect { client.analyze(bytes: "x", filename: "a.png", content_type: "image/png") }
        .to raise_error(AnalysisClient::DecodeFailedError)
    end
  end

  describe "#refeature" do
    it "posts JSON with base64 image and ranges" do
      stub = stub_request(:post, "http://analysis.test/v1/refeature")
        .with { |req|
          body = JSON.parse(req.body)
          body["ranges"] == [ { "top_y" => 0, "bottom_y" => 100 } ] && body["work_scale"] == 0.5
        }
        .to_return(status: 200, body: { bands: [], notices: [] }.to_json)

      client.refeature(image_bytes: "abc", work_scale: 0.5, ranges: [ { top_y: 0, bottom_y: 100 } ])
      expect(stub).to have_been_requested
    end
  end
end
