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

    it "still recognizes the page's true last band after an earlier merge left a replaced band's stale position behind" do
      # hero(position1)とfooter(position2、末尾)を結合すると、footerはstate=replacedのまま
      # position=2に留まる。以後の帯（存在しない）へのshiftは発生しないため、置換済み帯の
      # 古いpositionが「見かけ上の最大position」として残り、後続操作のis_last_band判定を
      # 誤らせる可能性がある。
      body = create_ready_conversion
      hero_id = body["bands"][1]["id"]
      footer_id = body["bands"][2]["id"]

      stub_refeature_success(bands: [
        { top_y: 80, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.7,
          runner_up_kind: nil, features: { column_count: 1 }, crops: [] }
      ])
      post "/conversions/#{body['id']}/bands/#{hero_id}/merge", params: { with: footer_id }
      expect(response).to have_http_status(:ok)
      merged = JSON.parse(response.body)
      merged_band_id = (merged["bands"].map { |b| b["id"] } - [ body["bands"][0]["id"] ]).first

      stub_refeature_success(bands: [
        { top_y: 80, bottom_y: 500, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
          runner_up_kind: nil, features: { alignment: "left" }, crops: [] },
        { top_y: 500, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.6,
          runner_up_kind: nil, features: { column_count: 1 }, crops: [] }
      ])
      post "/conversions/#{body['id']}/bands/#{merged_band_id}/split", params: { y: 500 }
      expect(response).to have_http_status(:ok)

      expect(
        a_request(:post, %r{/v1/refeature}).with(
          body: hash_including("is_last_band" => true)
        )
      ).to have_been_made.at_least_once
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

    it "attaches a refeature notice to the correct newly-created band, not an unrelated band that happens to share the raw range index" do
      body = create_ready_conversion
      footer_id = body["bands"][2]["id"] # position 2 (last band, top_y 800, bottom_y 1000)

      stub_refeature_success(
        bands: [
          { top_y: 800, bottom_y: 900, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
            runner_up_kind: nil, features: { alignment: "left" }, crops: [] },
          { top_y: 900, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.6,
            runner_up_kind: nil, features: { column_count: 1 }, crops: [] }
        ],
        # band_position: 1 は「このsplitで渡した2レンジのうち2番目」であり、conversion全体の
        # 帯position 1（＝ヒーロー帯）とは無関係。全体でのposition 3（split後2番目の新しい帯）に
        # 正しく紐付くべき
        notices: [ { notice_type: NoticeTypes::LOW_CONFIDENCE_KIND, band_position: 1, detail: {} } ]
      )

      post "/conversions/#{body['id']}/bands/#{footer_id}/split", params: { y: 900 }
      expect(response).to have_http_status(:ok)

      new_second_band = Band.find_by(conversion_id: body["id"], position: 3)
      notice = Notice.find_by(conversion_id: body["id"], notice_type: NoticeTypes::LOW_CONFIDENCE_KIND)
      expect(notice.band_id).to eq(new_second_band.id)
    end

    it "drops a pre-existing notice that belonged to the now-replaced band instead of leaving it pointing at a hidden band" do
      stub_analysis_success(
        bands: default_bands,
        notices: [ { notice_type: NoticeTypes::LOW_CONFIDENCE_KIND, band_position: 1, detail: {} } ]
      )
      file = Rack::Test::UploadedFile.new(StringIO.new(png_bytes(width: 400, height: 1000)), "image/png", original_filename: "d.png")
      post "/conversions", params: { file: file }
      body = JSON.parse(response.body)
      hero_id = body["bands"][1]["id"] # position 1、事前にlow_confidence_kindのnoticeが付いている
      expect(body["notices"].map { |n| n["band_id"] }).to include(hero_id)

      stub_refeature_success(bands: [
        { top_y: 80, bottom_y: 400, detected_kind: SectionKinds::HERO, confidence: 0.8,
          runner_up_kind: nil, features: { image_position: "none" }, crops: [] },
        { top_y: 400, bottom_y: 800, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
          runner_up_kind: nil, features: { alignment: "left" }, crops: [] }
      ])
      post "/conversions/#{body['id']}/bands/#{hero_id}/split", params: { y: 400 }
      expect(response).to have_http_status(:ok)
      updated = JSON.parse(response.body)

      expect(updated["notices"].map { |n| n["band_id"] }).not_to include(hero_id)
    end

    it "attaches a refeature notice to the new band even when it lands on the same position the replaced band still occupies" do
      # 分割元の帯（末尾, position 2）はstate="replaced"になるだけでpositionは変わらず維持
      # されるため、position_offset(2)+0=2 の位置には「新しい先頭側の帯」と「置換済みの旧帯」
      # の2件が同じpositionで存在しうる。notice解決がstateを見ずにfind_byするとどちらが
      # 返るか不定・あるいは旧帯を誤って返す可能性がある。
      body = create_ready_conversion
      footer_id = body["bands"][2]["id"] # position 2（末尾の帯）

      stub_refeature_success(
        bands: [
          { top_y: 800, bottom_y: 900, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
            runner_up_kind: nil, features: { alignment: "left" }, crops: [] },
          { top_y: 900, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.6,
            runner_up_kind: nil, features: { column_count: 1 }, crops: [] }
        ],
        notices: [ { notice_type: NoticeTypes::LOW_CONFIDENCE_KIND, band_position: 0, detail: {} } ]
      )

      post "/conversions/#{body['id']}/bands/#{footer_id}/split", params: { y: 900 }
      expect(response).to have_http_status(:ok)

      new_first_band = Band.find_by(conversion_id: body["id"], position: 2, state: "detected")
      notice = Notice.find_by(conversion_id: body["id"], notice_type: NoticeTypes::LOW_CONFIDENCE_KIND)
      expect(notice.band_id).to eq(new_first_band.id)
      expect(Band.find(notice.band_id).state).not_to eq("replaced")
    end

    it "tells the analysis layer whether the split band is the page's true first/last band, not just first/last within the request" do
      body = create_ready_conversion
      hero_id = body["bands"][1]["id"] # position 1: page中間の帯（先頭でも末尾でもない）

      stub_refeature_success(bands: [
        { top_y: 80, bottom_y: 400, detected_kind: SectionKinds::HERO, confidence: 0.8,
          runner_up_kind: nil, features: { image_position: "none" }, crops: [] },
        { top_y: 400, bottom_y: 800, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
          runner_up_kind: nil, features: { alignment: "left" }, crops: [] }
      ])

      post "/conversions/#{body['id']}/bands/#{hero_id}/split", params: { y: 400 }
      expect(response).to have_http_status(:ok)

      expect(
        a_request(:post, %r{/v1/refeature}).with(
          body: hash_including("is_first_band" => false, "is_last_band" => false)
        )
      ).to have_been_made
    end

    it "marks is_last_band true when splitting the page's actual last band" do
      body = create_ready_conversion
      footer_id = body["bands"][2]["id"] # position 2: page末尾の帯

      stub_refeature_success(bands: [
        { top_y: 800, bottom_y: 900, detected_kind: SectionKinds::GENERIC_TEXT, confidence: 0.5,
          runner_up_kind: nil, features: { alignment: "left" }, crops: [] },
        { top_y: 900, bottom_y: 1000, detected_kind: SectionKinds::FOOTER, confidence: 0.6,
          runner_up_kind: nil, features: { column_count: 1 }, crops: [] }
      ])

      post "/conversions/#{body['id']}/bands/#{footer_id}/split", params: { y: 900 }
      expect(response).to have_http_status(:ok)

      expect(
        a_request(:post, %r{/v1/refeature}).with(
          body: hash_including("is_first_band" => false, "is_last_band" => true)
        )
      ).to have_been_made
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
