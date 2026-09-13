class CreateConversionEvents < ActiveRecord::Migration[8.1]
  def change
    create_table :conversion_events do |t|
      t.string :session_id, null: false
      t.references :conversion, null: false, foreign_key: true
      t.datetime :occurred_at, null: false
      t.string :event_type, null: false
      t.text :detail, null: false, default: "{}"

      t.timestamps
    end

    add_index :conversion_events, :session_id
  end
end
