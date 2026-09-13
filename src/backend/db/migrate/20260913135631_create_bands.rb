class CreateBands < ActiveRecord::Migration[8.1]
  def change
    create_table :bands do |t|
      t.string :session_id, null: false
      t.references :conversion, null: false, foreign_key: true
      t.integer :position, null: false
      t.integer :top_y, null: false
      t.integer :bottom_y, null: false
      t.text :features, null: false, default: "{}"
      t.string :detected_kind, null: false
      t.float :confidence, null: false
      t.string :runner_up_kind
      t.string :user_kind
      t.string :variant, null: false
      t.string :state, null: false, default: "detected"

      t.timestamps
    end

    add_index :bands, :session_id
    add_index :bands, [ :conversion_id, :position ]
  end
end
