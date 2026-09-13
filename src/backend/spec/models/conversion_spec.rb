require "rails_helper"

RSpec.describe Conversion, type: :model do
  it "is valid with default factory" do
    expect(build(:conversion)).to be_valid
  end

  it "rejects an unknown state" do
    expect(build(:conversion, state: "bogus")).not_to be_valid
  end

  describe "#active?" do
    it "is true while analyzing/assembling/reassembling" do
      expect(build(:conversion, state: "analyzing")).to be_active
      expect(build(:conversion, state: "ready")).not_to be_active
    end
  end

  describe ".for_session" do
    it "scopes to the given session_id only" do
      mine = create(:conversion)
      create(:conversion)
      expect(Conversion.for_session(mine.session_id)).to contain_exactly(mine)
    end
  end
end
