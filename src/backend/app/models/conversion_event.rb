class ConversionEvent < ApplicationRecord
  EVENT_TYPES = %w[
    created intake_rejected analysis_started analysis_succeeded analysis_timeout
    analysis_unreachable analysis_decode_failed assembled output_validation_failed ready reassembled
    band_updated interrupted deleted
  ].freeze

  serialize :detail, coder: JSON, type: Hash

  belongs_to :conversion

  validates :session_id, presence: true
  validates :occurred_at, presence: true
  validates :event_type, presence: true, inclusion: { in: EVENT_TYPES }
end
