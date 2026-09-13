Rails.application.config.x.pipeline = Rails.application.config_for(:pipeline)
Rails.application.config.x.placeholders =
  YAML.load_file(Rails.root.join("config/placeholders.yml")).deep_symbolize_keys.fetch(:ja)
