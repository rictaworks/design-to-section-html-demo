require "rails_helper"

RSpec.describe Session, type: :model do
  it "is valid with a session_id" do
    expect(build(:session)).to be_valid
  end

  it "requires session_id" do
    session = build(:session, session_id: nil)
    expect(session).not_to be_valid
  end

  it "destroys dependent conversions when destroyed" do
    session = create(:session)
    create(:conversion, session: session, session_id: session.session_id)
    expect { session.destroy }.to change(Conversion, :count).by(-1)
  end
end
