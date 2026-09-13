require "rails_helper"
require "ripper"

# 文字列リテラル（日本語の利用者向け文言）は config/*.yml に分離し、app/配下のRubyソースに
# ハードコードしないことを検証する（CLAUDE.md）。コメント（説明文）は対象外とする。
#
# コメント除去は行内最初の "#" 以降を切り捨てる単純な実装だと、文字列内挿 "#{...}" を含む行
# （例: "#{p}__nav"）で内挿より後ろの内容まで誤って切り捨ててしまう。Ripperで実際のコメント
# トークン（:on_comment）だけを取り除くことで、内挿の中身は保持する。
RSpec.describe "hardcoded Japanese strings" do
  JAPANESE_PATTERN = /[\p{Hiragana}\p{Katakana}\p{Han}]/

  def strip_comments(source)
    Ripper.lex(source).each_with_object(+"") do |token, buffer|
      _, event, text, = token
      buffer << text unless event == :on_comment
    end
  end

  it "actually strips only real comments, not text following a string interpolation" do
    source = <<~RUBY
      p = "x"
      value = "\#{p}__nav_日本語"
      # 日本語のコメント
    RUBY

    result = strip_comments(source)

    expect(result).to include("日本語") # 内挿の中身は保持される
    expect(result).not_to include("コメント") # 実コメントは除去される
  end

  Dir.glob(Rails.root.join("app/**/*.rb")).each do |path|
    relative = Pathname.new(path).relative_path_from(Rails.root).to_s

    it "does not hardcode Japanese text in #{relative}" do
      code_only = strip_comments(File.read(path))
      expect(code_only).not_to match(JAPANESE_PATTERN),
        "#{relative} contains a Japanese string literal outside of config/*.yml"
    end
  end
end
