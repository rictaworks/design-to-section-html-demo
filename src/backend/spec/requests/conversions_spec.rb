require "rails_helper"

RSpec.describe "Conversions API", type: :request do
  def upload(bytes = png_bytes(width: 400, height: 1000), filename: "design.png", content_type: "image/png", extra: {})
    file = Rack::Test::UploadedFile.new(StringIO.new(bytes), content_type, original_filename: filename)
    post "/conversions", params: { file: file, **extra }
  end

  describe "POST /conversions" do
    it "creates a conversion and returns a ready document on success" do
      stub_analysis_success

      upload

      expect(response).to have_http_status(:created)
      body = JSON.parse(response.body)
      expect(body["state"]).to eq("ready")
      expect(body["bands"].size).to eq(3)
      expect(body["output"]["html"]).to include("<h1")
      expect(Conversion.count).to eq(1)
    end

    it "does not create a record when the honeypot field is filled" do
      stub_analysis_success

      upload(extra: { website: "http://spam.example" })

      expect(response).to have_http_status(:created)
      expect(Conversion.count).to eq(0)
    end

    it "rejects an unsupported format" do
      post "/conversions", params: {
        file: Rack::Test::UploadedFile.new(StringIO.new("GIF89a" + ("\x00" * 20)), "image/gif", original_filename: "a.gif")
      }
      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("unsupported_format")
      expect(Conversion.count).to eq(0)
    end

    it "marks the conversion failed when analysis times out" do
      stub_request(:post, %r{/v1/analyze}).to_timeout
      upload
      expect(response).to have_http_status(:created)
      body = JSON.parse(response.body)
      expect(body["state"]).to eq("failed")
      expect(body["failed_reason"]).to eq("analysis_timeout")
    end

    it "marks the conversion failed when the analysis service is unreachable" do
      stub_request(:post, %r{/v1/analyze}).to_raise(Errno::ECONNREFUSED)
      upload
      body = JSON.parse(response.body)
      expect(body["failed_reason"]).to eq("analysis_unreachable")
    end

    it "rejects a new conversion once 2 are already active for the same session" do
      stub_analysis_success
      upload # 最初のリクエストでセッションCookieを確立する（この時点でstateはready）
      owner_session = Conversion.last.session

      # 疑似的に処理中の変換を2件仕込む（同期実装のため実運用でReady/Failed以外に長時間留まることは
      # ほぼ無いが、上限チェック自体はDBの状態のみで判定されるためこの形で検証する）
      create(:conversion, session: owner_session, state: "analyzing")
      create(:conversion, session: owner_session, state: "assembling")

      upload
      expect(response).to have_http_status(:unprocessable_content)
      expect(JSON.parse(response.body)["error"]).to eq("too_many_active")
    end
  end

  describe "GET /conversions/:id and session isolation" do
    it "returns not_found for another session's conversion" do
      stub_analysis_success
      upload
      id = JSON.parse(response.body)["id"]

      other = open_session
      other.get "/conversions/#{id}"
      expect(other.response).to have_http_status(:not_found)
      expect(JSON.parse(other.response.body)["error"]).to eq("not_found")
    end

    it "returns the conversion detail for the owning session" do
      stub_analysis_success
      upload
      id = JSON.parse(response.body)["id"]

      get "/conversions/#{id}"
      expect(response).to have_http_status(:ok)
      expect(JSON.parse(response.body)["id"]).to eq(id)
    end
  end

  describe "GET /conversions/:id/source_image" do
    it "streams the original bytes with the correct content type" do
      stub_analysis_success
      bytes = png_bytes(width: 400, height: 1000)
      upload(bytes)
      id = JSON.parse(response.body)["id"]

      get "/conversions/#{id}/source_image"
      expect(response).to have_http_status(:ok)
      expect(response.content_type).to eq("image/png")
      expect(response.body.bytesize).to eq(bytes.bytesize)
    end
  end

  describe "DELETE /conversions/:id" do
    it "deletes the conversion and its dependent records" do
      stub_analysis_success
      upload
      id = JSON.parse(response.body)["id"]

      delete "/conversions/#{id}"
      expect(response).to have_http_status(:no_content)
      expect(Conversion.exists?(id)).to be false
    end
  end
end
