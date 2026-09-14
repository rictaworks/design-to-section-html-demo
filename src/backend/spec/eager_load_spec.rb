require "rails_helper"

# 本番は config.eager_load = true で app/ 配下を全て読み込む。開発・テストは遅延読み込みのため、
# 「require していないフレームワークを参照する残骸ファイル」（例: Action Mailer を require していない
# のに雛形の ApplicationMailer が残る）が見つからず、本番の起動時に初めて NameError になる。
# ここで全読み込みを再現し、その種の参照切れをテストで捕まえる。
RSpec.describe "eager loading" do
  it "loads every constant under app/ without error" do
    expect { Rails.application.eager_load! }.not_to raise_error
  end
end
