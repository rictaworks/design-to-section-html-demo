class CreateBandCrops < ActiveRecord::Migration[8.1]
  def change
    create_table :band_crops do |t|
      t.string :session_id, null: false
      t.references :band, null: false, foreign_key: true
      t.integer :left_x, null: false
      t.integer :top_y, null: false
      t.integer :width, null: false
      t.integer :height, null: false
      t.string :shape, null: false, default: "rect"
      t.binary :body
      t.boolean :placeholder, null: false, default: false

      t.timestamps
    end

    add_index :band_crops, :session_id
  end
end
