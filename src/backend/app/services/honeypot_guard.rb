# Bot対策（reCAPTCHA不使用。requirements.md 6.2・12.1・21章）。
# 指定フィールドに値がある送信は、成功と同じ応答を返しつつレコードを作成しない。
class HoneypotGuard
  FIELD_NAME = :website

  def self.triggered?(params)
    params[FIELD_NAME].present?
  end
end
