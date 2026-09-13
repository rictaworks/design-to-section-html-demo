class CreateSourceImages < ActiveRecord::Migration[8.1]
  def change
    create_table :source_images do |t|
      t.string :session_id, null: false
      t.references :conversion, null: false, foreign_key: true
      t.string :format, null: false
      t.integer :width, null: false
      t.integer :height, null: false
      t.integer :byte_size, null: false
      t.binary :body, null: false
      t.float :work_scale, null: false

      t.timestamps
    end

    add_index :source_images, :session_id
  end
end
