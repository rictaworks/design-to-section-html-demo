class Notice < ApplicationRecord
  serialize :detail, coder: JSON, type: Hash

  belongs_to :conversion
  belongs_to :band, optional: true

  validates :session_id, presence: true
  validates :notice_type, presence: true, inclusion: { in: NoticeTypes::ALL }
end
