require "rails_helper"

RSpec.describe "Bands API", type: :request do
  def create_ready_conversion
    stub_analysis_success
    file = Rack::Test::UploadedFile.new(StringIO.new(png_bytes(width: 400, height: 1000)), "image/png", original_filename: "d.png")
    post "/conversions", params: { file: file }
    JSON.parse(response.body)
  end

  describe "PATCH /conversions/:id/bands/:band_id (update_kind)" do
    it "sets the user-specified kind, bumps the version, and reassembles" do
      body = create_ready_conversion
      band_id = body["bands"].first["id"]
      version_before = body["version"]

      patch "/conversions/#{body['id']}/bands/#{band_id}", params: { kind: SectionKinds::FAQ }

      expect(response).to have_http_status(:ok)
      updated = JSON.parse(response.body)
      expect(updated["version"]).to eq(version_before + 1)
      band = updated["bands"].find { |b| b["id"] == band_id }
      expect(band["kind"]).to eq(SectionKinds::FAQ)
      expect(band["state"]).to eq("overridden")
    end

    it "rejects an unknown kind" do
      body = create_ready_conversion
      band_id = body["bands"].first["id"]

      patch "/conversions/#{body['id']}/bands/#{band_id}", params: { kind: "not_a_kind" }
      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("invalid_kind")
    end
  end

  describe "POST .../merge" do
    it "rejects merging non-adjacent bands" do
      body = create_ready_conversion
      first_id = body["bands"][0]["id"]
      last_id = body["bands"][2]["id"]

      post "/conversions/#{body['id']}/bands/#{first_id}/merge", params: { with: last_id }
      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("non_adjacent_merge_rejected")
    end

    it "merges two adjacent bands via refeature and reassembles" do
      body = create_ready_conversion
      a_id = body["bands"][0]["id"]
      b_id = body["bands"][1]["id"]

      stub_refeature_success(bands: [
        { top_y: 0, bottom_y: 800, detected_kind: SectionKinds::HERO, confidence: 0.8,
          runner_up_kind: nil, features: { image_position: "none" }, crops: [] }
      ])

      post "/conversions/#{body['id']}/bands/#{a_id}/merge", params: { with: b_id }
      expect(response).to have_http_status(:ok)
      updated = JSON.parse(response.body)
      expect(updated["bands"].map { |b| b["id"] }).not_to include(a_id, b_id)
      expect(updated["bands"].size).to eq(2) # merged band + footer
    end
  end

  describe "POST .../split" do
    it "rejects a split position too close to the band edge" do
      body = create_ready_conversion
      hero_id = body["bands"][1]["id"] # top_y 80, bottom_y 800

      post "/conversions/#{body['id']}/bands/#{hero_id}/split", params: { y: 90 }
      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("split_too_close_to_edge")
    end

    it "splits a band into two via refeature and reassembles" do
      body = create_ready_conversion
      hero_id = body["bands"][1]["id"]

      stub_refeature_success(bands: [
        { top_y: 80, bottom_y: 400, detected_kind: SectionKinds::HERO, confidence: 0.8,
          runner_up_kind: nil, features: { image_position: "none" }, crops: [] },
        { top_y: 400, bottom_y: 800, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
          runner_up_kind: nil, features: { alignment: "left" }, crops: [] }
      ])

      post "/conversions/#{body['id']}/bands/#{hero_id}/split", params: { y: 400 }
      expect(response).to have_http_status(:ok)
      updated = JSON.parse(response.body)
      expect(updated["bands"].size).to eq(4)
    end
  end

  describe "POST .../remove and .../restore" do
    it "removes a band, excludes it from assembly, then restores it" do
      body = create_ready_conversion
      footer_id = body["bands"][2]["id"]

      post "/conversions/#{body['id']}/bands/#{footer_id}/remove"
      expect(response).to have_http_status(:ok)
      after_remove = JSON.parse(response.body)
      removed = after_remove["bands"].find { |b| b["id"] == footer_id }
      expect(removed["state"]).to eq("removed")
      expect(after_remove["output"]["html"]).not_to include("<footer")

      post "/conversions/#{body['id']}/bands/#{footer_id}/restore"
      expect(response).to have_http_status(:ok)
      after_restore = JSON.parse(response.body)
      restored = after_restore["bands"].find { |b| b["id"] == footer_id }
      expect(restored["state"]).to eq("detected")
      expect(after_restore["output"]["html"]).to include("<footer")
    end
  end

  describe "operating on a replaced band" do
    it "rejects further edits on a band that was replaced by a merge, instead of silently no-op'ing" do
      body = create_ready_conversion
      a_id = body["bands"][0]["id"]
      b_id = body["bands"][1]["id"]

      stub_refeature_success(bands: [
        { top_y: 0, bottom_y: 800, detected_kind: SectionKinds::HERO, confidence: 0.8,
          runner_up_kind: nil, features: { image_position: "none" }, crops: [] }
      ])
      post "/conversions/#{body['id']}/bands/#{a_id}/merge", params: { with: b_id }
      expect(response).to have_http_status(:ok)
      expect(Band.find(a_id).state).to eq("replaced")

      patch "/conversions/#{body['id']}/bands/#{a_id}", params: { kind: SectionKinds::FAQ }

      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("band_replaced")
    end
  end
end
