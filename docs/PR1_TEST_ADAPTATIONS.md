# PR-1 テスト移植の記録

旧形式の受入・参照元Git履歴に依存する以下の試験は、旧形式拒否と現行形式の往復復元に変更。無条件skipは追加しない。

- `arcade_board_test.py:test_legacy_backups_v1_through_v6_restore_without_previous_board_leaks`
- `arcade_board_test.py:test_db6_upgrade_keeps_thirteen_stores_migrates_latest_layout_once`
- `runner_retire_test.py:test_v10_export_restore_reload_and_old_app_rollback_limit`
- `plush_test.py:test_v3_to_v6_restore_preserves_legacy_records_and_three_seven_layouts`
- `runner_storage_test.py:test_v9_upgrade_preserves_all_sixteen_stores_and_balance`
- `runner_storage_test.py:test_legacy_all_versions_and_runner_spend_injection`
- `runner_storage_test.py:test_v9_crane_mismatched_spend_time_survives_upgrade_export_and_restore`
- `study_modes_test.py:test_v9_roundtrip_and_v1_to_v8_discard_only_sets`
- `study_modes_test.py:test_v8_upgrade_adds_only_new_store_and_is_repeatable`
- `study_coin_integration_test.py:test_pr36_v8_bonus_migrates_and_legacy_restore_keeps_reward`

壁描画の物理比較用に、元の基準 d2d2f431afc5f467a3cc1def8e671558b6522eca の runner/game.js を fixtures/runner-wall-base.js に保持。実行アプリは指定4132cf7のまま。歴史問題・選択肢・時代カードの試験はPR-2/3で変更する。

- question_feedback_test の旧v1〜v7指摘保持試験は、旧v1〜v9拒否・ローカル指摘不変の試験に変更。
- 副次的な破損データ試験は現行BACKUP_VERSIONで実行し、版違いで早期拒否されるだけの試験にしない。
- クレーン再開fixtureには現行形式で必須の盤面を含める。ホーム間隔試験は既存arcade-home-gridのDOM階層に追従。
- ui_cleanupのDB/backup期待値9は参照元現行の10に修正。

- spikeデザイン回帰が参照する比較画像3枚のみを元docsからtests/fixtures/runner137-imagesへ移動して保持（履歴文書・公開用レビュー画像は除外）。

- リタイアの現行v10書出し→復元→リロード確認は独立した試験として保持し、歴史版へのロールバック試験のみ拒否試験へ置換。
