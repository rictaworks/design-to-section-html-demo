class Conversion < ApplicationRecord
  STATES = %w[uploaded analyzing assembling ready reassembling failed interrupted deleted].freeze
  ACTIVE_STATES = %w[analyzing assembling reassembling].freeze
  SHELL_LAYOUTS = %w[single sidebar].freeze
  THEMES = %w[light dark].freeze

  belongs_to :session, foreign_key: :session_id, primary_key: :session_id, inverse_of: :conversions

  has_one :source_image, dependent: :destroy
  has_many :bands, -> { order(:position) }, dependent: :destroy, inverse_of: :conversion
  has_one :output, dependent: :destroy
  has_many :notices, dependent: :destroy
  has_many :conversion_events, dependent: :destroy

  validates :session_id, presence: true
  validates :state, presence: true, inclusion: { in: STATES }
  validates :shell_layout, presence: true, inclusion: { in: SHELL_LAYOUTS }
  validates :theme, presence: true, inclusion: { in: THEMES }
  validates :version, presence: true, numericality: { greater_than_or_equal_to: 0 }

  scope :for_session, ->(session_id) { where(session_id: session_id) }
  scope :active, -> { where(state: ACTIVE_STATES) }

  def active?
    ACTIVE_STATES.include?(state)
  end
end
