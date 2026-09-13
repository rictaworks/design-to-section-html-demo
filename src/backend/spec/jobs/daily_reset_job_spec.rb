require "rails_helper"

RSpec.describe DailyResetJob do
  describe "#interrupt_active_conversions" do
    it "marks analyzing/assembling/reassembling conversions as interrupted with a notice and event" do
      active = create(:conversion, state: "analyzing")
      ready = create(:conversion, state: "ready")

      described_class.new.interrupt_active_conversions

      expect(active.reload.state).to eq("interrupted")
      expect(active.notices.pluck(:notice_type)).to include(NoticeTypes::DAILY_RESET_INTERRUPTED)
      expect(active.conversion_events.pluck(:event_type)).to include("interrupted")
      expect(ready.reload.state).to eq("ready")
    end
  end

  describe "#purge_all" do
    it "deletes every session and its dependent records" do
      create(:conversion)
      expect { described_class.new.purge_all }.to change(Session, :count).to(0)
        .and change(Conversion, :count).to(0)
    end
  end

  describe "#perform" do
    it "interrupts active conversions and then purges everything" do
      create(:conversion, state: "analyzing")
      described_class.new.perform
      expect(Session.count).to eq(0)
      expect(Conversion.count).to eq(0)
    end

    it "stops new intake for the duration of the run and resumes it afterwards" do
      expect(SystemState.reset_in_progress?).to be(false)

      seen_in_progress = false
      job = described_class.new
      allow(job).to receive(:purge_all).and_wrap_original do |original|
        seen_in_progress = SystemState.reset_in_progress?
        original.call
      end

      job.perform

      expect(seen_in_progress).to be(true)
      expect(SystemState.reset_in_progress?).to be(false)
    end

    it "waits for the configured grace period between interrupting and purging" do
      job = described_class.new
      allow(job).to receive(:grace_period_seconds).and_return(5)
      expect(job).to receive(:sleep).with(5)

      job.perform
    end

    it "clears the in-progress flag even if purging raises" do
      job = described_class.new
      allow(job).to receive(:purge_all).and_raise("boom")

      expect { job.perform }.to raise_error("boom")
      expect(SystemState.reset_in_progress?).to be(false)
    end
  end
end
