# PR-1 独立化・初期移植の報告

## 開始条件と版

- PR-0 #1 は 2026-11-23 01:26 UTC にmainへマージ済みとGitHub APIで確認してから着手。
- 開始時 `kakezan-master/main`: `82bb1321954cc7e5ce23acb9b5b9a85dbbbe7e22`。アプリ本体・APP_VERSIONは未定義。
- 最新mainから `feat/pr-1-independent-app` を作成。PR-0ブランチは使用しない。
- 参照元main・移植コミット: `4132cf78e29d2f33c4587b16b58e48f7ef3e17d9` / v1.7.56。両者の差分はゼロ。未マージ #144、#30、#1 は含めない。参照元へ書込み・設定変更・PR作成なし。
- 新アプリ版: **v0.1.0**。DBスキーマ版 **10**、バックアップ構造版 **10** は別々の定数で管理。数値10の継承は17ストアの現行構造を表し、歴史版との互換性を意味しない。
- 版検証スクリプトは、mainにindex.htmlが存在しない初回移植を許可する。存在するがAPP_VERSIONが欠損したmainは引き続き拒否し、その後は最新mainより大きい版を要求。
- AGENTS.md、REQUIREMENTS.md、DECISIONS_AND_TESTS.mdは読み込み済み・無変更。READMEは実装状況と実行手順のみ更新。

## ファイル

[全ファイルのコピー・変更・除外一覧](PR1_FILES.md)、[テスト変更理由](PR1_TEST_ADAPTATIONS.md)を参照。index.html、runner一式、参照画像、既存テスト、開発スクリプト、PR時の検証Actionsを移植。過去リリース記録・歴史固有文書・公開用資料は除外。比較試験で必要な画像3枚だけをテストfixtureへ配置。

## アプリ識別・データ分離

| 項目 | 新アプリ |
|---|---|
| IndexedDB | `kakezan-master-v1` / schema 10 / 17ストア |
| バックアップ形式 | `kakezan-master-backup` / version 10のみ |
| バックアップ名 | `kakezan-master-backup-YYYY-MM-DD.json` |
| history.state.app | `kakezan-master` / route version 1 |
| コイン移行完了キー | `kakezan-master-rewards-seeded-v1` |
| 問題更新・指摘・改善依頼の形式とファイル名 | `kakezan-master-…` の接頭辞 |
| 配信URLの版 | 親HTML、iframe、JS/CSS、トゲ画像を0.1.0へ同期 |
| ブラウザテスト環境変数 | `KAKEZAN_MASTER_BROWSER` / `KAKEZAN_MASTER_ENGINE` |

実行コードは旧DB名に接続しない。新DBは新規生成し、初回起動で新DB内にコイン初期化マーカーと景品盤面を作る。旧DBの探索・読出し・自動移行は行わない。localStorage/sessionStorage/Cache APIの使用は実行コードで検出なし。PWA・同期・外部サービス依存は追加なし。

バックアップは17ストアを検査し、プロフィール、問題参照、重複、コインと景品・プレイの対応、ランナー途中状態を従来通り検証。検査→プレビュー→ユーザー確認→単一トランザクションで置換する。旧歴史形式v1〜v10は全拒否。新識別子でも旧v1〜v9、未来版、ストア欠落は拒否し、旧形式の配列補完・報酬再構成はしない。

## 維持した機能と仮の学習内容

クレーン通常100枚、ランナー通常30枚、test無料。景品・キャラクター・秘密キャラ権限・ステージ選択・中断再開・履歴・最高点・コイン決済は親側に保持。ランナーはiframeのまま。runner/game.jsの差分は配信URLの版のみで、物理・当たり判定・抽選・能力・ステージ構造は変更しない。

**学習内容はまだ歴史サンプル9問・旧選択肢UI・旧時代進捗/カードの仮状態。九九学習は未実装。** ホームとREADMEに明示。既存の保護者向け問題編集・インポート等も暫定移植であり、完成した九九仕様とは扱わない。

PR-2以降へ残すもの: 81問生成、安定した九九ID、数値入力・採点・回答履歴・復元、段別/全段ミックス/苦手克服の九九対応、9軸レーダー、段別9枚＋完全制覇1枚と画像制作、81問別正答率、保護者画面整理。仮のE01〜E10・サンプル問題IDは新DB内にのみ存在し、PR-2/3で置換する。

## 保存分離を検証した方法

`tests/app_isolation_test.py` は一時Chromiumコンテキストの同一オリジンに旧名DBを作り、架空のコイン123・履歴・activeランナーをsentinelストアへ保存。新アプリを再読込みし、IDBFactory.openを監視して新アプリの接続先が `kakezan-master-v1` だけであること、旧DBに置いた値が変化しないことを確認。新DBの学習・コイン・景品fixtureを保存し、リロード後の全17ストア一致も確認する。

実際の歴史マスター利用者DB・実バックアップは使用しない。両アプリを実機で並行運用した確認とは区別する。student/testは別残高を確認し、既存試験で支払い・履歴・権限・別タブの競合も検査する。

## 自動テスト

Python 3.12、Node v24.22.3、Playwright 1.62.0、Chromium使用。Safari実機確認ではない。

主要受入コマンド（最終状態）:

```sh
PYTHONPATH=tests python -m unittest -v app_isolation_test app_version_test runner_session_test runner_storage_test runner_integration_test runner_bear_test home_arcade_test positive_coin_reward_test
```

**66件すべて合格（196.937秒）**。起動、新DB/17ストア、旧DBの非干渉、リロード、バックアップ入出力・形式拒否・確認、student/test、学習報酬、二重回答/複数タブ、30枚支払い、iframe保存再開、権限、クマ3ハート、全111画像のデコードを含む。

追加実行（重複を含むため合算しない）:

| コマンド（`PYTHONPATH=tests python -m unittest -v` に続ける） | 結果 |
|---|---|
| `runner_layout_test` | 5件合格。9画面サイズ×10状態を含む |
| `runner_header_test` | 7件合格。横画面の見切れ、残高、購入/再開 |
| `runner_spike_design_test` | 4件合格。元軌道の全フレーム比較、画像/404代替 |
| `app_isolation_test.AppIsolationTest.test_all_delivered_images_decode runner_integration_test.RunnerIntegrationTest.test_home_spacing_and_choices_below_game runner_wall_design_test` | 5件合格。壁描画と30/60/120Hzの元軌道比較 |
| `plush_test.PlushTest.test_new_prizes_backup_download_preview_restore_and_reload_all_stores plush_test.PlushTest.test_student_cost_free_repeat_test_and_profile_separation` | 2件合格 |
| `plush_test.PlushTest.test_legacy_aiming_and_new_resolving_require_manual_resume_without_charge_or_duplicate_prize admin_menu_hierarchy_test.AdminMenuHierarchyTest.test_backup_restore_still_requires_confirmation_and_cancel_is_safe admin_menu_hierarchy_test.AdminMenuHierarchyTest.test_close_group_during_restore_keeps_single_execution` | 3件合格 |
| `question_feedback_test.QuestionFeedbackTest.test_backup_v1_through_v9_rejected_without_changing_feedback` | 1件合格 |
| `runner_retire_test.RunnerRetireTest.test_legacy_rejected_for_v10_export_restore_reload_and_old_app_rollback_limit` | 修正後1件合格 |
| `runner_retire_test.RunnerRetireTest.test_v10_export_restore_reload_retire_record` | 元の現行版往復試験1件合格 |

`runner-iframe.yml` の Targeted formal runner tests をローカル実行した初回52件は2失敗・3エラー。欠落した比較画像3枚と共通ヘッダー注記による2画面試験が原因。fixtureを補いホーム内へ注記を移した後、spike・layout・headerを上表の通り再実行して合格。全52件を一括再実行したという意味ではない。

拡張コース回帰:

```sh
PYTHONPATH=tests python -m unittest -v runner_retire_test runner_phase1_test runner_phase2a_test runner_tuning_test runner_density_test runner_vertical_test runner_ascent_test runner_balance_test runner_crumbling_test runner_fall_test runner_session_test runner_storage_test
```

121件実行（500.636秒）、120件合格・1件エラー。エラーは旧版拒否へ変えたリタイア試験が、残高境界用の簡易reviewEventsを現行バックアップとして使ったfixture不整合（復習コイン履歴不正）。有効な公開用架空fixtureへ修正し、該当1件は単独再実行で合格。追加で元の現行リタイア結果の書出し/復元/リロード試験も1件合格。121件を修正後に全再実行したとは扱わない。旧ステージ版・鳥・高低差・崩れる足場・穴・30/60/120Hz・全フレーム再開・課金競合を含む。

runner Actionsは実測したローカルの連続実行が合計10分を超えるためtimeoutを20分へ拡張。テスト内容を減らして通す変更は行わない。

静的検査: `python scripts/check_static.py`、`python -m compileall -q scripts tests`、`git diff --cached --check`、`python scripts/check_app_version.py --base origin/main --head HEAD` 合格。親/runner全JS構文、HTMLのローカル参照、module参照、旧アプリ識別子の不使用、初回v0.1.0を検証。AGENTS/要求仕様/設計判断のmainとの差分ゼロを確認。

## 失敗・未実施・次への引継ぎ

- 全件探索 `PYTHONPATH=tests python -m unittest discover -s tests -p '*_test.py' -v` はクレーン演出の位置計測で失敗し、長時間の画面計測を含むため中断。`ArcadeBoardTest.test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes` の幅375px・star/secret_koryunを確認した時点で全件合格とはしない。原因は未確定。描画/物理は変更せず、未マージ#30も取り込まない。最終のホーム注記移動後、この演出の全組合せは再実行していないため残件とする。
- 初回のテスト補助の不足、旧形式受入前提、欠落していた比較画像、無効なfixture、古いDOM前提、共通ヘッダーに置いた注記の横画面圧迫は修正し、該当試験を再実行。存在しないテスト名 `PlushTest.test_backup_roundtrip` を含めた実行はローダーエラーになったため合格数に含めない。正しいクレーン試験を別途実行。
- 未実施の全探索対象には、歴史固有の編集・カード・旧DB内アップグレードの試験も含む。既存テストを無条件skipせず保存し、今回必要な旧バックアップ受入試験は拒否試験へ更新。PR-2/3では歴史問題・選択肢・時代カード前提を実装と一緒に更新する。
- GitHub Actionsのワークフローは設定したが、GitHub上のCI合格を確認したという報告ではない。
- **iPhone/iPad Safari実機未確認**: 縦横回転、アドレスバー伸縮、Safe Area、Split View、文字拡大、VoiceOver、実タップのクレーン下降/掴み位置、ランナージャンプ、アプリ切替/BFCacheと保存、端末ファイルへのバックアップ書出し/選択/復元、無料再開と二重課金なしを別途確認する。
- 後続の九九変換で保存形式・バックアップ検証・問題/段/カードIDが変わる。アプリ版・DB版・backup版を必要に応じ個別に更新し、今回の暫定保存の扱いを明記する。
- 新Issue作成なし。main直接push・マージ・タグ・Pages公開/設定変更なし。ドラフトPR作成で停止。
