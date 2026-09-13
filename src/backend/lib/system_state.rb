# システム全体の一時的な状態（requirements.md 16.4・22章 日次リセット）。
# DailyResetJobが新規受付を停止している間、ConversionsController#createはこれを見て拒否する。
#
# Rails.cacheではなくプロセス内のAtomicBooleanで保持する。理由は二つ：
# (1) DailyResetJobのpurge_all（Session.destroy）で消えてはならない一時フラグであること
#     （sessions等のドメインテーブルとは無関係でなければならない）
# (2) test環境のcache_storeが:null_store（Rails既定。テスト間のキャッシュ汚染防止のため）であり、
#     Rails.cache経由だとフラグが常にno-opになってテストできないこと
# デモ版は単一プロセス運用を前提（KISS/YAGNI）とし、複数プロセス間の共有は行わない。
module SystemState
  @reset_in_progress = Concurrent::AtomicBoolean.new(false)

  module_function

  def reset_in_progress?
    @reset_in_progress.true?
  end

  def begin_reset!
    @reset_in_progress.make_true
  end

  def end_reset!
    @reset_in_progress.make_false
  end
end
