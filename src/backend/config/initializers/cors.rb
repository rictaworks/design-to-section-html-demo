# Be sure to restart your server when you modify this file.

# フロントエンド（Next.js / Vercel）からのクロスオリジンAjaxを許可する。
# session_id をCookieでやり取りするため credentials を有効化する。
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins ENV.fetch("FRONTEND_ORIGIN", "http://localhost:3000")

    resource "*",
      headers: :any,
      methods: [ :get, :post, :patch, :delete, :options ],
      credentials: true
  end
end
