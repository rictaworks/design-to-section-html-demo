class RelaxJsonColumnConstraints < ActiveRecord::Migration[8.1]
  # ActiveRecord::Coders::ColumnSerializer は空のHash（デフォルト値相当）をNULLとして
  # 保存し読み込み時にHash.newへ復元する仕様のため、NOT NULL制約と共存できない。
  def change
    change_column_null :bands, :features, true
    change_column_default :bands, :features, from: "{}", to: nil

    change_column_null :notices, :detail, true
    change_column_default :notices, :detail, from: "{}", to: nil

    change_column_null :conversion_events, :detail, true
    change_column_default :conversion_events, :detail, from: "{}", to: nil
  end
end
