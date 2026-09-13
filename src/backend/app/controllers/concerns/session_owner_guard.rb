# session_id（オーナーキー）をCookieで発行・保持し、全リクエストで解決する。
# 他セッションのレコードは参照・更新・削除できない（requirements.md 11章・21章）。
module SessionOwnerGuard
  extend ActiveSupport::Concern

  SESSION_COOKIE_KEY = :design_to_html_session_id

  included do
    before_action :resolve_current_session
  end

  def current_session_id
    @current_session_id
  end

  # 他セッションのIDを指定された場合は、存在の有無を区別せず「見つからない」とする（11章）。
  def find_owned!(relation, id)
    record = relation.find_by(id: id, session_id: current_session_id)
    raise ActiveRecord::RecordNotFound, "not found for current session" if record.nil?
    record
  end

  private

  def resolve_current_session
    session_id = cookies.signed[SESSION_COOKIE_KEY]

    unless session_id && Session.exists?(session_id: session_id)
      session_id = SecureRandom.urlsafe_base64(32)
      Session.create!(
        session_id: session_id,
        user_agent_class: classify_user_agent,
        last_seen_at: Time.current
      )
      cookies.signed[SESSION_COOKIE_KEY] = {
        value: session_id,
        same_site: :none,
        secure: Rails.env.production?,
        httponly: true
      }
    else
      Session.where(session_id: session_id).update_all(last_seen_at: Time.current)
    end

    @current_session_id = session_id
  end

  def classify_user_agent
    ua = request.user_agent.to_s
    return "mobile" if ua.match?(/Mobile|Android|iPhone/)
    return "unknown" if ua.blank?
    "desktop"
  end
end
