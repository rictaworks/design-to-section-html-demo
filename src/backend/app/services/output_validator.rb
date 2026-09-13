require "nokogiri"

# 生成物検証（requirements.md 6.9）。いずれか失敗した場合は生成物を採用しない。
class OutputValidator
  Result = Struct.new(:valid, :reasons, keyword_init: true) do
    def valid?
      valid
    end
  end

  MAX_BYTES = 6.megabytes
  EVENT_ATTR_PATTERN = /\Aon[a-z]+\z/i

  def self.validate(html)
    new(html).validate
  end

  def initialize(html)
    @html = html
  end

  def validate
    reasons = []
    reasons << "byte_size_exceeded" if @html.bytesize > MAX_BYTES

    doc = Nokogiri::HTML5.parse(@html)

    reasons << "external_reference" if external_reference?(doc)
    reasons << "script_present" if script_present?(doc)
    reasons << "h1_count_invalid" unless doc.css("h1").size == 1
    reasons << "img_missing_alt" if doc.css("img").any? { |img| img["alt"].blank? }
    reasons << "unbalanced_tags" unless balanced_tags?(doc)

    Result.new(valid: reasons.empty?, reasons: reasons)
  end

  private

  def external_reference?(doc)
    doc.css("*").any? do |node|
      node.attributes.values.any? { |attr| attr.value.to_s.match?(%r{https?://}) }
    end
  end

  def script_present?(doc)
    return true if doc.css("script").any?
    doc.css("*").any? do |node|
      node.attributes.keys.any? { |name| name.match?(EVENT_ATTR_PATTERN) }
    end
  end

  MISMATCH_PATTERN = /unexpected end tag|stray end tag|expected closing tag|unexpected-end-tag/i

  def balanced_tags?(doc)
    doc.errors.none? { |e| e.to_s.match?(MISMATCH_PATTERN) }
  end
end
