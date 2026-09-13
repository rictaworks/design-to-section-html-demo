# APIサーバー（config.api_only = true）はJSONのみを返す想定で、ブラウザで直接HTMLとして
# 表示されるページを持たない。念のため最も厳格なCSPを既定とする（release-security-gate 工程E対応）。
#
# ActionDispatch::ContentSecurityPolicy::Middleware はapi_only構成のミドルウェアスタックに
# 含まれないため（config.content_security_policy ブロックだけでは反映されない）、
# 他の既定セキュリティヘッダ（X-Frame-Options等）と同様に config.action_dispatch.default_headers
# へ直接追加する。
Rails.application.configure do
  config.action_dispatch.default_headers["Content-Security-Policy"] =
    "default-src 'none'; frame-ancestors 'none'"
end
