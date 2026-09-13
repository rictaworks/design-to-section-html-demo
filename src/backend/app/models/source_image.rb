class SourceImage < ApplicationRecord
  FORMATS = %w[png jpeg webp].freeze

  belongs_to :conversion

  validates :session_id, presence: true
  validates :format, presence: true, inclusion: { in: FORMATS }
  validates :width, :height, :byte_size, presence: true, numericality: { greater_than: 0 }
  validates :body, presence: true
  validates :work_scale, presence: true, numericality: { greater_than: 0, less_than_or_equal_to: 1 }
end
