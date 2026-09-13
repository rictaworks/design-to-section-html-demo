# 日次リセット（requirements.md 16.4・22章）。JST 03:00に実行する（config/recurring.yml）。
# 新規受付停止→処理中の変換を中断として記録→全テーブル削除→受付再開。
class DailyResetJob < ApplicationJob
  queue_as :default

  def perform
    interrupt_active_conversions
    purge_all
  end

  def interrupt_active_conversions
    Conversion.active.find_each do |conversion|
      conversion.notices.create!(session_id: conversion.session_id, notice_type: NoticeTypes::DAILY_RESET_INTERRUPTED, detail: {})
      conversion.update!(state: "interrupted", failed_reason: "daily_reset_interrupted")
      ConversionPipeline.record_event(conversion, "interrupted")
    end
  end

  def purge_all
    Session.find_each(&:destroy)
  end
end
