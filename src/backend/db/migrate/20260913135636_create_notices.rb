class CreateNotices < ActiveRecord::Migration[8.1]
  def change
    create_table :notices do |t|
      t.string :session_id, null: false
      t.references :conversion, null: false, foreign_key: true
      t.references :band, null: true, foreign_key: true
      t.string :notice_type, null: false
      t.text :detail, null: false, default: "{}"

      t.timestamps
    end

    add_index :notices, :session_id
  end
end
