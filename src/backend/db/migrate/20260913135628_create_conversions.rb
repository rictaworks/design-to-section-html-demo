class CreateConversions < ActiveRecord::Migration[8.1]
  def change
    create_table :conversions do |t|
      t.string :session_id, null: false
      t.string :state, null: false, default: "uploaded"
      t.string :shell_layout, null: false, default: "single"
      t.string :theme, null: false, default: "light"
      t.boolean :mobile_design, null: false, default: false
      t.integer :version, null: false, default: 0
      t.string :failed_reason

      t.timestamps
    end

    add_index :conversions, :session_id
    add_index :conversions, [ :session_id, :state ]
  end
end
