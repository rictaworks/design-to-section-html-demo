class CreateSessions < ActiveRecord::Migration[8.1]
  def change
    create_table :sessions, id: false do |t|
      t.string :session_id, primary_key: true, null: false
      t.string :user_agent_class, null: false, default: "unknown"
      t.datetime :last_seen_at, null: false

      t.timestamps
    end
  end
end
