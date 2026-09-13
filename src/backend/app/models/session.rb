class Session < ApplicationRecord
  self.primary_key = "session_id"

  has_many :conversions, foreign_key: :session_id, inverse_of: :session, dependent: :destroy

  validates :session_id, presence: true
  validates :user_agent_class, presence: true
  validates :last_seen_at, presence: true
end
