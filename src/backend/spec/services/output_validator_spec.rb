require "rails_helper"

RSpec.describe OutputValidator do
  def wrap(body)
    <<~HTML
      <!doctype html><html lang="ja"><head><meta charset="utf-8"><title>t</title></head>
      <body>#{body}</body></html>
    HTML
  end

  it "accepts a clean, valid document" do
    result = described_class.validate(wrap('<h1>t</h1><img src="data:image/png;base64,AA==" alt="a">'))
    expect(result).to be_valid
  end

  it "rejects a document containing an http(s) reference" do
    result = described_class.validate(wrap('<h1>t</h1><a href="https://example.com">x</a><img src="x" alt="a">'))
    expect(result).not_to be_valid
    expect(result.reasons).to include("external_reference")
  end

  it "rejects a document containing a script element" do
    result = described_class.validate(wrap('<h1>t</h1><script>alert(1)</script><img src="x" alt="a">'))
    expect(result).not_to be_valid
    expect(result.reasons).to include("script_present")
  end

  it "rejects a document containing an inline event attribute" do
    result = described_class.validate(wrap('<h1>t</h1><div onclick="x()"></div><img src="x" alt="a">'))
    expect(result).not_to be_valid
    expect(result.reasons).to include("script_present")
  end

  it "rejects a document without exactly one h1" do
    result = described_class.validate(wrap('<h1>a</h1><h1>b</h1><img src="x" alt="a">'))
    expect(result).not_to be_valid
    expect(result.reasons).to include("h1_count_invalid")
  end

  it "rejects a document with an img missing alt" do
    result = described_class.validate(wrap('<h1>t</h1><img src="x">'))
    expect(result).not_to be_valid
    expect(result.reasons).to include("img_missing_alt")
  end

  it "rejects a document exceeding 6MB" do
    big = "a" * 7.megabytes
    result = described_class.validate(wrap(%(<h1>t</h1><img src="x" alt="a"><!--#{big}-->)))
    expect(result).not_to be_valid
    expect(result.reasons).to include("byte_size_exceeded")
  end
end
