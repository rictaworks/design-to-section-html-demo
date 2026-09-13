require "rails_helper"

# 文字列リテラル（日本語の利用者向け文言）は config/*.yml に分離し、app/配下のRubyソースに
# ハードコードしないことを検証する（CLAUDE.md）。コメント（説明文）は対象外とする。
RSpec.describe "hardcoded Japanese strings" do
  JAPANESE_PATTERN = /[\p{Hiragana}\p{Katakana}\p{Han}]/

  def strip_comments(source)
    source.lines.map { |line| line.sub(/#.*/, "") }.join
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
