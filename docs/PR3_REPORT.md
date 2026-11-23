# PR-3 学習進捗・達成カード・保護者用正答率（v0.3.0）

## 基準と変更範囲

- 作業開始時のGitHub最新main：`b81cbac7a108bec259ee7493ab046a53a9fd517c`、アプリ版v0.2.0。PR #3（PR-2）のマージを確認。open Issueなし、新Issue作成なし。
- `AGENTS.md`、`docs/REQUIREMENTS.md`、`docs/DECISIONS_AND_TESTS.md`を読み、最新mainから`feat/pr-3-progress-cards`を作成。
- アプリ版はv0.3.0。九九81問の内容・永続ID、テンキー、抽選、2連続習得、コイン、ゲームの物理・確率・キャラ・ステージを変更しない。ランナーはiframe方式を維持。歴史マスターへの書込み・機能追加なし。

変更ファイル：

- `index.html`：9段レーダー、10枚の仮カード、原子的授与・補完、保護者の読取専用一覧、バックアップ検証、版更新。
- `tests/progress_cards_test.py`：計算・授与・集計・競合・復元・互換性・画面サイズの新規試験。
- `tests/locked_card_test.py`：旧歴史画像・裏面の試験を、画像未制作の仮カードと獲得詳細・プロフィール・プレビューの試験へ置換。
- `tests/multiplication_test.py`、`tests/app_isolation_test.py`：現行版・未来版拒否の期待値を更新。
- `tests/plush_test.py`：現行バックアップ期待値を12へ更新。手動再開試験の待機時間を、設定上約6.1秒の演出＋非同期描画余裕に合わせる（完了・無課金・重複なしの検査は維持）。
- `tests/runner_bear_test.py`、`tests/runner_crumbling_test.py`、`tests/runner_density_test.py`、`tests/runner_phase1_test.py`、`tests/runner_phase2a_test.py`、`tests/runner_retire_test.py`、`tests/runner_storage_test.py`、`tests/runner_tuning_test.py`、`tests/runner_vertical_test.py`：現行DB／backup版の期待値のみ更新。ゲーム・コース・snapshot版と試験目的は維持。
- `.github/workflows/app-isolation.yml`：新規進捗・カードUI試験を追加。
- `README.md`、`docs/REQUIREMENTS.md`、`docs/DECISIONS_AND_TESTS.md`、本報告：実装状況・画像制作待ち・保存判断・検証記録を更新。

## 理解度と通算正答率

理解度は `(習得済み問題数 + 0.5 × 連続正解1回の問題数) ÷ 対象問題数 × 100`。各段9問、総合81問。計算には丸め前の値を使い、百分率の表示は整数切り捨て。誤答で習得が解除された状態を再読込し、ホームで再計算する。9本の軸には「1の段」〜「9の段」を表示し、歴史固有のラベル・称号は除去。role=imgのラベルには9段それぞれの理解度を含める。student/testのprogressを分ける。

保護者一覧は固定81問のIDに一致するanswersのみを全期間で集計。正答率は通算正解数÷通算回答数、表示は整数四捨五入。通算回答数・通算正解数・現在の習得状態も表示する。未回答は「—（0回）」、正答率の昇降どちらでも末尾に置く。同率は問題ID順、並べ替えには丸め前の比率を使う。全81問／段、student/testを切り替え可能。○×履歴は展開時に全件描画し、保存・集計を20回等で打ち切らない。回答とprogressは同一readonlyトランザクションで読む。旧歴史回答は別の回答履歴画面とバックアップに保持し、九九の集計には含めない。

固定問題の追加・編集・削除・インポートは従来どおり不可。保護者テスト、バックアップ、初期化は維持する。

## 10枚のカード

| ID | 条件 | questionCountAtEarn |
|---|---|---:|
| T01 | 1の段の9問を同時点で全習得 | 9 |
| T02 | 2の段の9問を同時点で全習得 | 9 |
| T03 | 3の段の9問を同時点で全習得 | 9 |
| T04 | 4の段の9問を同時点で全習得 | 9 |
| T05 | 5の段の9問を同時点で全習得 | 9 |
| T06 | 6の段の9問を同時点で全習得 | 9 |
| T07 | 7の段の9問を同時点で全習得 | 9 |
| T08 | 8の段の9問を同時点で全習得 | 9 |
| T09 | 9の段の9問を同時点で全習得 | 9 |
| ALL81 | 現在の81問すべてを同時点で全習得 | 81 |

段別カード9枚の所有だけではALL81を授与しない。獲得後の誤答では所有を取り消さない。追加コインなし。awardsのキーは`student:T01`などでtestと分離する。

`saveAnswer()`の既存readwriteトランザクション内で、保存直前の全progress＋今回の回答から全カード条件を判定する。同じトランザクションで既得キーを読み、未授与のみaddする。最後の回答で段別とALL81を同時授与できる。獲得日時は回答日時。補完処理もprogress/awardsを単一readwriteトランザクションでロックするため、別タブ・再読込・補完の競合で二重授与や日時上書きが起きない。失敗時はカード・回答・セッション・コインすべてロールバックする。

旧版で既に条件を満たす未授与記録は起動／復元時に安全に補完する。補完日時は対象問題の最終回答日時の最大値を使用する。既存カードの日時は維持する。

ホームには常に10枚を表示し、ALL81は全幅・枠で区別。未獲得は鍵と残り習得数、獲得済みは名称と獲得状態を表示し、タップで詳細を確認できる。条件説明を児童向けに表示する。

**画像は未完成。** 旧歴史カード画像を読み込まず、仮アイコンと「画像は制作待ち」を使用。具体的なキャラクター名称・モチーフ・イラストは決定も生成もしていない。10枚それぞれ異なるキャラクターにする確定要件は維持し、ユーザーとの意匠確定後の別PRで完成させる。

## 保存・旧データ互換性

| 項目 | 今回の扱い |
|---|---|
| DB名 | `kakezan-master-v1`を維持 |
| DBスキーマ版 | 11→12、17ストア維持、レコード変換・削除なし |
| バックアップ識別子 | `kakezan-master-backup`を維持 |
| バックアップ版 | 書出し12、読込み10/11/12 |
| awards最大件数 | 20→40（旧10＋新10、student/test各20） |
| 旧カードE01〜E10 | 保存・復元継続、50問以上を検証、九九の表示枚数には含めない |
| 新カード | 段別9問／ALL81は81問ちょうどを検証、v12専用 |

DB版更新は新カード非対応のv0.1.0/v0.2.0タブの接続をversionchangeで閉じ、旧版保存との並走を防ぐため。ストア構造の変更のためではない。バックアップ版更新は旧版で検証できないカードID・件数条件を識別するため。新カードに旧50問条件を適用しない。旧バックアップの履歴・コイン・景品・ゲーム途中状態・旧カードを保持する。履歴の自動変換・切り捨てはしない。

新旧の形式混入、不正ID、件数不正、重複、未来版、ストア不足、歴史マスターのバックアップ形式は拒否。現在未習得でも、正しく獲得済みのカードは復元する。復元は内容検証→プレビュー→確認→全17ストアの原子的置換。自動マージなし。v0.1.0/v0.2.0への直接ダウングレードはDB版不一致で不可であり、戻すためのデータ削除は行わない。

## 検証結果

使用ブラウザはChromium（`KAKEZAN_MASTER_BROWSER=/usr/bin/chromium`）。すべて架空データ・一時ブラウザコンテキストで実行。

| 実行コマンド（`PYTHONPATH=tests python -m unittest -v`に続ける） | 結果 |
|---|---|
| `progress_cards_test locked_card_test multiplication_test positive_coin_reward_test app_isolation_test app_version_test` | 最終45件すべて合格、247.764秒 |
| `runner_retire_test runner_phase1_test runner_phase2a_test runner_tuning_test runner_density_test runner_vertical_test runner_ascent_test runner_balance_test runner_crumbling_test runner_fall_test runner_session_test runner_storage_test` | 全122件合格、899.103秒。旧コース・30/60/120Hz・毎フレーム復元・支払い・途中保存・終了を含む |
| Runner iframe layoutの「Targeted formal runner tests」と同じコマンド | 52件実行、51件合格・画像遅延試験1件失敗、584.341秒。該当1件は単独再実行で合格（9.696秒） |
| `progress_cards_test locked_card_test` | プレビュー修正後14件すべて合格、102.923秒。一括45件にも含むため重複加算しない |
| `crane_timing_test`＋下記クレーン7件 | 初回11件中9件合格、位置計測の6サブケース失敗、手動再開1件タイムアウト。詳細は下記 |
| `plush_test.PlushTest.test_legacy_aiming_and_new_resolving_require_manual_resume_without_charge_or_duplicate_prize` | 待機時間修正後1件合格、19.271秒 |

クレーン7件は `plush_test.PlushTest` の `test_new_prizes_backup_download_preview_restore_and_reload_all_stores`、`test_student_cost_free_repeat_test_and_profile_separation`、`test_legacy_aiming_and_new_resolving_require_manual_resume_without_charge_or_duplicate_prize` と、`arcade_board_test.ArcadeBoardTest` の `test_transactions_serialize_purchase_swap_and_stale_confirmation`、`test_two_tabs_cannot_replace_an_active_board`、`test_atomic_completion_rolls_back_all_on_error_and_retries_once`、`test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes`。

追加計測：375×667、667×375、390×844、844×390、768×1024、1024×768、820×1180、1180×820、507×768でレーダーの9軸ラベルがSVGの表示範囲内にあり、ホーム／保護者一覧に横はみ出しがないことを自動確認。390pxのカード・保護者一覧と1024pxのレーダーをスクリーンショットで目視確認。画像は架空データで`/tmp`に保存し、コミットしない。

静的検査：`python scripts/check_static.py`、`python -m compileall -q scripts tests`、`git diff --check` 合格。最新mainを再取得し、`python scripts/check_app_version.py --base origin/main --head HEAD`でv0.2.0→v0.3.0を検査。

Runner画面試験で失敗した `runner_animation_test.RunnerAnimationTest.test_delayed_and_failed_new_sprites_keep_input_and_same_character` は、goldfish画像完了の5秒待機でタイムアウトしたが、直後の未完了画像一覧は空だった。単独再実行は合格。ランナー本体・当該試験の待機時間やassertは変更していない。52件全体を再実行したという意味ではない。

初期失敗と修正・残件：

- 初回の巻き戻し試験は、ネイティブaddメソッドの復元式をPlaywrightが関数として呼び出すテスト補助の不備で1エラー。復元を関数内の代入に直し、新規14件を再実行して全合格。旧版の起動処理がカードプレビューを非表示にする点も修正し、仮カードのプレビュー試験に合格。
- クレーン11件の一括実行は9件合格、手動再開1件で7秒タイムアウト、位置計測1件の6サブケースで失敗（240.384秒）。位置計測の失敗は終了時opacityが厳密な0ではなく約0.0004〜0.0054となる点。該当サブケースは幅375/secret_koryun、640/star、641/star・secret_koryun、759/star・secret_koryun。掴み位置・持上げ同期のassertではなく末尾の透明度assertで失敗した。ゲームコード・描画・物理・検証閾値は変更せず、PR-1からの残件としてPR-4で継続調査する。
- 手動再開は元の待機時間で単独再実行もタイムアウト。変更前mainの隔離worktreeでは同試験1件合格（15.374秒）。現行コードの追加診断ではタイムアウト直後にbusy=false/status=finished、notice空で完了済み。既存の7秒待機に描画・保存の余裕が少ないため、演出設定時間＋5秒の待機に変更し、同試験1件合格（19.271秒）。課金・保存・重複チェックは変更しない。11件全体を修正後に再実行したという意味ではない。

GitHub Actions：App isolationに新規試験を追加。Runner iframe layoutとApp versionも既存設定を維持。これらはpull_request起動のため、この報告を記載するPR作成前時点では当該PRの結果は未実施／未確認。ローカル合格をCI合格とは扱わず、ドラフトPR作成で停止する指示に従い、GitHub上の結果確認は次のレビューへ引き継ぐ。

## Safari実機・PR-4への引継ぎ

- iPhone/iPad Safari実機は未確認。縦横回転、アドレスバー伸縮、Safe Area、iPad Split View、文字拡大、VoiceOverの各段理解度・カード詳細・履歴展開、実タップ、ファイル書出し／復元を確認する。ブラウザ自動試験を実機合格とは扱わない。
- 10種類の異なるキャラクターの意匠・名称・モチーフ・画像をユーザーと確定後、別PRで制作・表示検査する。
- PR-1からのクレーン位置計測の残件を引き継ぐ。今回もゲーム物理・描画方式・抽選を勝手に変更しない。
- 歴史教材編集等を前提とする旧専用試験は全探索合格扱いにせず、PR-4で保護者UIと試験の整理を続ける。
- 新Issue作成、mainへの直接push、PRマージ、タグ作成、Pages公開／設定変更、歴史マスターへの書込みは行わない。ドラフトPR作成後に停止する。
