require "net/http"
require "uri"
require "json"
require "stringio"
require "base64"

# 解析層（FastAPI）とのHTTPクライアント（requirements.md 5章・9章・10章・20章）。
# 解析層は状態を持たず、画像と指示を受け取り結果を返すのみ。呼び出しは30秒でタイムアウトする。
class AnalysisClient
  class TimeoutError < StandardError; end
  class UnreachableError < StandardError; end
  class DecodeFailedError < StandardError; end

  def initialize(
    base_url: ENV.fetch("ANALYSIS_SERVICE_URL", "http://localhost:8001"),
    timeout: Rails.application.config.x.pipeline[:analysis_timeout_seconds]
  )
    @base_url = base_url
    @timeout = timeout
  end

  def analyze(bytes:, filename:, content_type:)
    uri = URI.join(@base_url, "/v1/analyze")
    request = Net::HTTP::Post.new(uri)
    request.set_form(
      [ [ "file", StringIO.new(bytes), filename: filename, content_type: content_type ] ],
      "multipart/form-data"
    )
    perform(uri, request)
  end

  def refeature(image_bytes:, work_scale:, ranges:, is_first_band: true, is_last_band: true)
    uri = URI.join(@base_url, "/v1/refeature")
    request = Net::HTTP::Post.new(uri)
    request["Content-Type"] = "application/json"
    request.body = {
      image_base64: Base64.strict_encode64(image_bytes),
      work_scale: work_scale,
      ranges: ranges,
      is_first_band: is_first_band,
      is_last_band: is_last_band
    }.to_json
    perform(uri, request)
  end

  private

  def perform(uri, request)
    response = Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == "https",
                                open_timeout: @timeout, read_timeout: @timeout) do |http|
      http.request(request)
    end

    case response
    when Net::HTTPSuccess
      JSON.parse(response.body, symbolize_names: true)
    when Net::HTTPUnprocessableEntity
      raise DecodeFailedError, "analysis service could not decode the image"
    else
      raise UnreachableError, "analysis service returned #{response.code}"
    end
  rescue Net::OpenTimeout, Net::ReadTimeout
    raise TimeoutError, "analysis service timed out after #{@timeout}s"
  rescue SocketError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, EOFError => e
    raise UnreachableError, e.message
  end
end
