class Output < ApplicationRecord
  belongs_to :conversion

  validates :session_id, presence: true
  validates :version, presence: true, numericality: { only_integer: true, greater_than: 0 }
  validates :html, presence: true
  validates :byte_size, presence: true, numericality: { greater_than: 0 }
  validates :generated_at, presence: true
end
