class CreateOutputs < ActiveRecord::Migration[8.1]
  def change
    create_table :outputs do |t|
      t.string :session_id, null: false
      t.references :conversion, null: false, foreign_key: true
      t.integer :version, null: false
      t.text :html, null: false
      t.integer :byte_size, null: false
      t.datetime :generated_at, null: false

      t.timestamps
    end

    add_index :outputs, :session_id
    add_index :outputs, [ :conversion_id, :version ], unique: true
  end
end
