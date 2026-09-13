class Band < ApplicationRecord
  STATES = %w[detected overridden removed replaced].freeze

  serialize :features, coder: JSON, type: Hash

  belongs_to :conversion
  has_many :band_crops, dependent: :destroy
  has_many :notices, dependent: :nullify

  validates :session_id, presence: true
  validates :position, presence: true, numericality: { only_integer: true, greater_than_or_equal_to: 0 }
  validates :top_y, :bottom_y, presence: true, numericality: { only_integer: true }
  validates :detected_kind, presence: true, inclusion: { in: SectionKinds::ALL }
  validates :user_kind, inclusion: { in: SectionKinds::ALL }, allow_nil: true
  validates :confidence, presence: true, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 1 }
  validates :variant, presence: true
  validates :state, presence: true, inclusion: { in: STATES }
  validate :bottom_after_top

  # 組み立て対象（削除済み・置換済みを除く）
  scope :assemblable, -> { where.not(state: %w[removed replaced]).order(:position) }
  # 一覧表示対象（利用者が復元できるよう削除済みは含め、置換済みのみ除く）
  scope :listed, -> { where.not(state: "replaced").order(:position) }

  def kind
    user_kind.presence || detected_kind
  end

  def height
    bottom_y - top_y
  end

  private

  def bottom_after_top
    return if top_y.nil? || bottom_y.nil?
    errors.add(:bottom_y, "must be greater than top_y") if bottom_y <= top_y
  end
end
