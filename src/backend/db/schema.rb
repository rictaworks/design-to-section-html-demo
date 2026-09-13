# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_09_13_141331) do
  create_table "band_crops", force: :cascade do |t|
    t.integer "band_id", null: false
    t.binary "body"
    t.datetime "created_at", null: false
    t.integer "height", null: false
    t.integer "left_x", null: false
    t.boolean "placeholder", default: false, null: false
    t.string "session_id", null: false
    t.string "shape", default: "rect", null: false
    t.integer "top_y", null: false
    t.datetime "updated_at", null: false
    t.integer "width", null: false
    t.index ["band_id"], name: "index_band_crops_on_band_id"
    t.index ["session_id"], name: "index_band_crops_on_session_id"
  end

  create_table "bands", force: :cascade do |t|
    t.integer "bottom_y", null: false
    t.float "confidence", null: false
    t.integer "conversion_id", null: false
    t.datetime "created_at", null: false
    t.string "detected_kind", null: false
    t.text "features"
    t.integer "position", null: false
    t.string "runner_up_kind"
    t.string "session_id", null: false
    t.string "state", default: "detected", null: false
    t.integer "top_y", null: false
    t.datetime "updated_at", null: false
    t.string "user_kind"
    t.string "variant", null: false
    t.index ["conversion_id", "position"], name: "index_bands_on_conversion_id_and_position"
    t.index ["conversion_id"], name: "index_bands_on_conversion_id"
    t.index ["session_id"], name: "index_bands_on_session_id"
  end

  create_table "conversion_events", force: :cascade do |t|
    t.integer "conversion_id", null: false
    t.datetime "created_at", null: false
    t.text "detail"
    t.string "event_type", null: false
    t.datetime "occurred_at", null: false
    t.string "session_id", null: false
    t.datetime "updated_at", null: false
    t.index ["conversion_id"], name: "index_conversion_events_on_conversion_id"
    t.index ["session_id"], name: "index_conversion_events_on_session_id"
  end

  create_table "conversions", force: :cascade do |t|
    t.datetime "created_at", null: false
    t.string "failed_reason"
    t.boolean "mobile_design", default: false, null: false
    t.string "session_id", null: false
    t.string "shell_layout", default: "single", null: false
    t.string "state", default: "uploaded", null: false
    t.string "theme", default: "light", null: false
    t.datetime "updated_at", null: false
    t.integer "version", default: 0, null: false
    t.index ["session_id", "state"], name: "index_conversions_on_session_id_and_state"
    t.index ["session_id"], name: "index_conversions_on_session_id"
  end

  create_table "notices", force: :cascade do |t|
    t.integer "band_id"
    t.integer "conversion_id", null: false
    t.datetime "created_at", null: false
    t.text "detail"
    t.string "notice_type", null: false
    t.string "session_id", null: false
    t.datetime "updated_at", null: false
    t.index ["band_id"], name: "index_notices_on_band_id"
    t.index ["conversion_id"], name: "index_notices_on_conversion_id"
    t.index ["session_id"], name: "index_notices_on_session_id"
  end

  create_table "outputs", force: :cascade do |t|
    t.integer "byte_size", null: false
    t.integer "conversion_id", null: false
    t.datetime "created_at", null: false
    t.datetime "generated_at", null: false
    t.text "html", null: false
    t.string "session_id", null: false
    t.datetime "updated_at", null: false
    t.integer "version", null: false
    t.index ["conversion_id", "version"], name: "index_outputs_on_conversion_id_and_version", unique: true
    t.index ["conversion_id"], name: "index_outputs_on_conversion_id"
    t.index ["session_id"], name: "index_outputs_on_session_id"
  end

  create_table "sessions", primary_key: "session_id", id: :string, force: :cascade do |t|
    t.datetime "created_at", null: false
    t.datetime "last_seen_at", null: false
    t.datetime "updated_at", null: false
    t.string "user_agent_class", default: "unknown", null: false
  end

  create_table "source_images", force: :cascade do |t|
    t.binary "body", null: false
    t.integer "byte_size", null: false
    t.integer "conversion_id", null: false
    t.datetime "created_at", null: false
    t.string "format", null: false
    t.integer "height", null: false
    t.string "session_id", null: false
    t.datetime "updated_at", null: false
    t.integer "width", null: false
    t.float "work_scale", null: false
    t.index ["conversion_id"], name: "index_source_images_on_conversion_id"
    t.index ["session_id"], name: "index_source_images_on_session_id"
  end

  add_foreign_key "band_crops", "bands"
  add_foreign_key "bands", "conversions"
  add_foreign_key "conversion_events", "conversions"
  add_foreign_key "notices", "bands"
  add_foreign_key "notices", "conversions"
  add_foreign_key "outputs", "conversions"
  add_foreign_key "source_images", "conversions"
end
