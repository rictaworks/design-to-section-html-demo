require "rails_helper"

RSpec.describe HoneypotGuard do
  it "is not triggered when the field is blank" do
    expect(described_class.triggered?(ActionController::Parameters.new(website: ""))).to be false
  end

  it "is triggered when the field has a value" do
    expect(described_class.triggered?(ActionController::Parameters.new(website: "http://spam.example"))).to be true
  end
end
