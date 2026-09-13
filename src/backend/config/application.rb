require_relative "boot"

require "rails"
# Pick the frameworks you want:
# 本デモはメール・添付ファイル・リッチテキスト・WebSocketを使用しないため、
# 該当フレームワークは読み込まない（YAGNI・攻撃面の縮小）
require "active_model/railtie"
require "active_job/railtie"
require "active_record/railtie"
require "action_controller/railtie"
# require "rails/test_unit/railtie"

# Require the gems listed in Gemfile, including any gems
# you've limited to :test, :development, or :production.
Bundler.require(*Rails.groups)

module Backend
  class Application < Rails::Application
    # Initialize configuration defaults for originally generated Rails version.
    config.load_defaults 8.1

    # Please, add to the `ignore` list any other `lib` subdirectories that do
    # not contain `.rb` files, or that should not be reloaded or eager loaded.
    # Common ones are `templates`, `generators`, or `middleware`, for example.
    config.autoload_lib(ignore: %w[assets tasks])

    # Configuration for the application, engines, and railties goes here.
    #
    # These settings can be overridden in specific environments using the files
    # in config/environments, which are processed later.
    #
    config.time_zone = "Tokyo"
    # config.eager_load_paths << Rails.root.join("extras")

    # Only loads a smaller set of middleware suitable for API only apps.
    # Middleware like session, flash, cookies can be added back manually.
    # Skip views, helpers and assets when generating a new resource.
    config.api_only = true

    # session_id（オーナーキー）をCookieで発行・保持するため、APIオンリーでも
    # Cookie/Sessionミドルウェアを個別に有効化する。
    # フロントエンド（Vercel）とアプリケーション層（Railway）は別オリジンなので
    # クロスサイトCookie送受信のため same_site: :none とし、本番はSecure必須とする
    config.session_store :cookie_store,
      key: "_design_to_html_session",
      same_site: :none,
      secure: Rails.env.production?
    config.middleware.use ActionDispatch::Cookies
    config.middleware.use config.session_store, config.session_options
  end
end
