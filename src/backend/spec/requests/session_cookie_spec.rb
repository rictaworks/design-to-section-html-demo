require "rails_helper"

# ブラウザのCookie仕様上、SameSite=None のCookieは Secure 属性が無いと拒否される
# （production以外は secure:false のため、SameSite=None のままだとローカル開発で
#   セッションCookieが一切保存されず、オーナーキーの仕組みが機能しなくなる）。
RSpec.describe "session cookie attributes", type: :request do
  it "does not combine SameSite=None with a non-secure cookie outside production" do
    get "/conversions"

    set_cookie = response.headers["Set-Cookie"].to_s
    expect(set_cookie).to include("design_to_html_session_id")

    if set_cookie.match?(/samesite=none/i)
      expect(set_cookie).to match(/secure/i)
    end
  end
end
