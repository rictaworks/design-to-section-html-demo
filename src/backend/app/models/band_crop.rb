class BandCrop < ApplicationRecord
  SHAPES = %w[rect circle].freeze

  belongs_to :band

  validates :session_id, presence: true
  validates :left_x, :top_y, :width, :height, presence: true, numericality: { only_integer: true }
  validates :shape, presence: true, inclusion: { in: SHAPES }
end
