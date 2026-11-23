# PR-4 総合回帰・既知不具合調査・Safari品質確認

## 基準と範囲

- 開始時main：`1ed09dff5946ed48ef808a6d4cd3210a5396ba2d`、APP_VERSION **v0.4.0**。GitHub PR #5のマージをAPIとcloneで確認。開始時・調査中のopen PR／Issue検索は0件。新Issueなし。ブランチ `codex/pr4-regression-safari` をmainから作成。
- 候補：**v0.4.1**。正式カード画像10枚は既にmain実装済み。過去報告の未公開・画像制作待ち等は当時の記録として冒頭に案内を追加した。現在の公開URLの配信版を確認した、という意味ではない。
- 新機能開発は行わない。実行コードの変更は狭幅ヘッダーの文字折返しと版だけ。DB `kakezan-master-v1`／12、backup `kakezan-master-backup`／12、全17ストア、新旧所有記録を変更しない。歴史マスターへの書込みなし。
- GitHubのPR番号と工程名は別。工程PR-4は、カード正式化のGitHub PR #5より後に実施する。

## 変更内容と不変条件

| 対象 | 変更・理由 |
|---|---|
| index.html | 430px以下のh1の `white-space:nowrap` を外し `overflow-wrap:anywhere` を指定。320px＋CSS文字200%でタイトルが管理ボタンと重なりdocument幅360pxになる問題を修正。修正後320px、文字は改行して読める。APP_VERSION v0.4.0→v0.4.1。 |
| runner_animation_test | 画像404完了待ちのポーリングを手動rAFから実時間50msへ変更。条件と既存5秒上限は同一。 |
| arcade_board_test | current export版12の期待値。3/7景品の途中プレイは維持し、fixtureを全17ストアと整合する盤面へ修正。 |
| plush_test／plush_popup_test／secret_plush_test | 現行DB・バックアップ12の期待値へ更新。全ストア一致、確率・画像・秘密非開示・復元等の検査内容は保持。 |
| app_isolation_test | APP_VERSIONの期待値だけv0.4.1へ。DB12・backup12・17ストアの検査を保持。 |
| runner_characters_test／runner_hit_feedback_test | 非表示になった旧selectの操作を表示中のキャラ選択カードのclickへ更新。48通りの旧版コース完走と被弾描画の条件は保持。ハートの読み上げ期待値を現行文言へ合わせる。 |
| mobile_regression_test（新規2件） | 12画面サイズ、可変高さ、文字200%、81問一覧、テンキー領域、ダイアログのキーボードとフォーカスを自動検査。 |
| App isolation workflow | 既存49件へ新UI2件を追加。旧歴史UI成功をCIへ無条件に足さない。 |
| 文書・証跡 | 本報告、55ファイル分類、実機チェックシート、計測JSON、代表画面2枚。過去報告は本文を残す。 |

81問と固定ID、抽選重み・重複防止、2連続正解／誤答解除、コイン報酬・消費、カード10枚の条件・画像・所有保持、クレーン物理／確率／速度、ランナーiframe／物理／キャラ／ステージを変更していない。配信画像・runner配信コードの差分はゼロ。保存データ変換・移行・DB版更新・バックアップ形式変更もない。

## 55ファイルの調査と集計方針

[全55ファイルの分類・件数・対応方針](PR4_TEST_INVENTORY.md)。A（現行で合格）40、B（現行回帰群に不合格あり）4、H（旧歴史学習前提）5、O（現行では対象外の公開機能）3、M（現行と旧前提の混在）3。Bにも旧形式fixture等を含み、各テストの適用性は表で区別する。

既存は633固有test ID。通常discoverの639呼出しには、importされたRunnerCharacterUITest 6件の重複が含まれる。追加ファイル2件は別記し、最終リポジトリは56個の `*_test.py`。幅／景品／各フレームのサブケース数をテスト件数へ加算しない。

前回PRの49件、52件、14件、108件、クレーン10件等は過去の結果として参照し、今回の件数に足さない。今回の個別再実行・重複バッチも同じIDを重複計上しない。作業中の探索実行と、現行群の実行、修正後の個別結果を区別する。

## 実行コマンド・実測件数・合否

環境：Python 3.12.14、Node v24.19.0、Playwright 1.62.0、システムChromium 154.0.8037.57、Linux。localhostと一時context、架空データのみ。標準sandbox内ではsocket作成が拒否されたため、許可された環境側でサーバー／Chromiumを実行した。起動失敗の0件は実行件数へ含めない。

**全635固有ID（既存633＋新規2）を実行し、最終観測は453合格／182不合格。** これは全件を単一バッチで再実行した結果ではなく、次の調査・バッチ・対象再実行をIDで照合した結果。failとerrorを固有ID単位の「不合格」にまとめる。途中のassertで終了し、後続assertへ未到達の試験も含む。最終head上の全探索合格を意味しない。

| 区分 | 実行・結果 | 数え方 |
|---|---|---|
| 現行44ファイル＋追加UI（45ファイル） | 427呼出し、1732.979秒。固有421件は405合格／16不合格。unittestの表示はfailures=32, errors=19（サブケースとimport重複を含む） | 6重複を除去。作業版v0.4.1、開始時にloadした修正前fixtureを含む |
| 上の失敗に対する対象再実行 | 9固有IDを修正後合格へ。現行群の最終観測 **414合格／7不合格** | 421へ追加計上しない。427件全体の再実行ではない |
| 旧UI・混在11ファイル | 探索前半の6ファイル108件（30合格／78不合格）＋残り5ファイル106件（9合格／97不合格、664.810秒） | **214固有件：39合格／175不合格**。現行受入の合格数へ足さない |
| 最初の既知2件（変更前） | クレーン合格、ランナー画像待機失敗、126.543秒 | 上の固有IDと重複。追加合格数なし |
| runner_animation単独モジュール（修正後） | 6件合格、15.046秒 | 現行群との重複 |
| 新UI2件（修正後） | 2件合格、51.522秒 | 現行群との重複 |

[635行のID別CSV](pr4-evidence/test-results.csv)、[機械可読集計／ファイル別合否](pr4-evidence/summary.json)、[55ファイル一覧](PR4_TEST_INVENTORY.md)。CSVのcurrent_batchとtargeted_retestを分け、古い試験の失敗を覆い隠さない。

実際の主コマンド（リポジトリルート）：

```sh
PYTHONPATH=tests python -m unittest -v arcade_board_test.ArcadeBoardTest.test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes runner_animation_test.RunnerAnimationTest.test_delayed_and_failed_new_sprites_keep_input_and_same_character
PYTHONPATH=tests python -m unittest discover -s tests -p '*_test.py' -v
PYTHONPATH=tests python /tmp/pr4-run-current.py
PYTHONPATH=tests python /tmp/pr4-run-legacy.py
PYTHONPATH=tests python -m unittest -v runner_animation_test
PYTHONPATH=tests python -m unittest -fv mobile_regression_test
```

全探索は旧UIを含めて着手したが、question_feedbackの途中で中断し、後半を現行群と旧群に分割した。未完了メソッドは旧群バッチで実行し直した。探索中にヘッダー修正等も行ったため、探索は単一固定revisionの受入バッチではない。ここから採用した旧6ファイルのソースは変更していない。中断時の残り・現行群との重複を成功へ算入しない。全探索1コマンドの完走とは報告しない。

実行したバッチスクリプトと同じ内容を [run-current.py](pr4-evidence/run-current.py)／[run-legacy.py](pr4-evidence/run-legacy.py) に保存。コマンドの `/tmp/pr4-run-*.py` をこのパスへ置き換えると同じ選択を再現できる（テストソースはこのPRの最終版になる）。JSONL出力は `/tmp/pr4-current-results.jsonl`／`/tmp/pr4-legacy-results.jsonl`。元のログは `/tmp/pr4-*.log` に保存し、公開用CSVにはtest ID・結果だけを格納した。

修正後の対象再実行コマンド：

```sh
PYTHONPATH=tests python -m unittest -v arcade_board_test.ArcadeBoardTest.test_v7_download_preview_restore_reload_preserves_nulls_and_profiles secret_plush_test.SecretPlushTest.test_secret_award_history_profiles_reload_backup_stay_consistent secret_plush_test.SecretPlushTest.test_v7_download_preview_restore_preserves_all_secret_ids_pending_and_fourteen_stores
# 3件合格、15.531秒
PYTHONPATH=tests python -m unittest -v arcade_board_test.ArcadeBoardTest.test_old_three_and_seven_slot_aiming_resolving_resume_once
# 1件（4サブケース）合格、22.662秒
PYTHONPATH=tests python -m unittest -v plush_test.PlushTest.test_definitions_paths_decoded_images_and_equal_probability_seven_slots plush_popup_test.PlushPopupTest.test_open_close_preserves_all_fourteen_stores_for_both_profiles
# 2件合格、15.941秒
PYTHONPATH=tests python -m unittest -v runner_characters_test.RunnerCharactersTest.test_preview_controls_clear_all_48_character_stage_frame_rate_combinations runner_hit_feedback_test.RunnerHitFeedbackTest.test_feedback_draws_expires_and_freezes_with_jump_and_shield
# 2件中1合格（48通りの完走）、1不合格（柴犬以外の6サブケースのprobe KeyError）、186.690秒
PYTHONPATH=tests python -m unittest -v runner_hit_feedback_test.RunnerHitFeedbackTest.test_feedback_draws_expires_and_freezes_with_jump_and_shield
# probe修正後1件合格（4キャラ×2条件）、11.399秒
PYTHONPATH=tests python -m unittest -v runner_stages_test.RunnerStagesTest.test_collision_preserves_motion_support_events_and_star_scoring
# 1件合格（10サブケース）、2.108秒
```

原因診断（テスト件数へ足さない）：

```sh
mkdir -p /tmp/pr4-evidence
PYTHONPATH=tests python /tmp/pr4-diagnose.py
node docs/pr4-evidence/runner-unattended.mjs
```

`pr4-diagnose.py` の内容は [diagnose.py](pr4-evidence/diagnose.py) に保存。新UI試作時にはヘッダー200%幅の不合格と、再開済み結果の試験待機／未定義補助名の不備があり、試験側の操作順を修正してから最終2件を実行した。途中で中断した試作バッチを完走・合格に数えない。

静的検査 `python scripts/check_static.py`、`python -m compileall -q scripts tests`、`git diff --check` は合格。アプリ版検査は最終コミットを取得済み最新mainに対して実行し、結果をPR本文へ記録する。


## クレーン：今回の観測と原因未確定の残件

対象 `ArcadeBoardTest.test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes`。

1. **変更前の対象試験は今回合格**。幅375、390、430、640、641、759、760、768、1024 × star／secret_koryun、計18サブケース。厳密opacity文字列 `'0'`、下降時の大きさ・位置（1px）、ツメ先（1.5px）、全保持フレームの中心同期（1px）、持上げ80px超・輸送50px超、秘密画像非開示、保存不変を保持。
2. 別診断で同じ18組合せのreturn時に `getComputedStyle(toy).opacity`、`toy.getAnimations()` のproperty／currentTime／playState／durationを採取し、`Animation.finished` 前後も比較した。全18回でreturn時opacity=0、進行中toy transition=0、待機差は約0〜0.1ms。[実測JSON](pr4-evidence/crane-return.json)。これは診断18回であり、別の18テスト合格として足さない。
3. `CRANE_CONFIG.releaseMs=480`、CSS deliveredのtransition-durationも同じ設定。JSの待機はsetTimeout、描画待ちは二重rAF、opacityにはCSS ease補間がある。過去の0.0004〜0.0054は補間終端近くの値と整合するが、今回再現できず、描画時計のずれ・丸め・特定エンジンのいずれが原因かは確定できない。
4. 下降／持上げ／輸送／落下／取得はarcade_boardとcrane_timingで検査する。幅640/641と759/760のCSS境界、通常と秘密の画像、miss／dropも維持。取得の確定・二重付与・トランザクションabort・手動再開は別の保存試験で検査する。
5. **過去6組合せの発生原因は未解決**：375/secret_koryun、640/star、641/star・secret_koryun、759/star・secret_koryun。今回合格をもって過去事象を修正済みとはしない。検査を削除・skipせず、opacity閾値も緩和しない。アニメーション本体は変更しない。

再発時は同じreturnでtransition状態とtimestampを採取し、transitionend後に厳密0へ到達するかを確認する。終了待ちの試験修正を提案するには、この因果確認が必要。位置検査の1px／1.5pxは元からのCSSピクセル精度で今回変更なし。

## ランナー画像待機：原因と対応

変更前の2件バッチでクレーンは合格、対象画像試験は **`goldfish: pending images []`** で失敗した。PR #5のsalamander、PR-3のgoldfishと同じ症状。失敗直後に画像が未完了なのではなく、待機関数が条件を再評価できないことを調べた。

- `preview_runner()` は `MANUAL_FRAMES` を注入し、window.requestAnimationFrameを手動キューに置換する。ゲームの物理時間・フレームを試験から進めるための仕組み。
- Playwright `wait_for_function` の既定ポーリングはrAF。最初の評価がfalseで、その後に404応答が完了しても、この待機中には試験が手動フレームを進めない。完了条件がtrueになっているのに5秒で失敗する。最初から画像完了済みなら即合格する。
- 独立診断で同じ条件を100ms後にtrueへ変更。既定rAFは700msでタイムアウト（直後のflag=true、手動キュー1件）。50msポーリングは約103msで合格。[実測](pr4-evidence/runner-poll.json)。診断の700msは原因切分け用で、本試験の5秒を変更していない。
- 対応は当該待機1箇所の `polling=50`。`runnerImages.every(i=>i.complete)` を維持し、404時のnaturalWidth=0を正常画像と誤認しない描画fallback、同じキャラ、入力、移動、キャッシュ再利用を引き続き検査。skip・固定sleep・timeout延長なし。本番の画像処理・物理・ステージは変更しない。
- 修正後、画像試験を含むrunner_animation全6件は15.046秒で合格。総合バッチでの結果は上の集計を参照。

順序・環境：手動時計が各新contextへ注入されるため、前のテストの保存状態漏れを必要とせず発生する。ネットワーク完了が最初の条件評価の前か後かで成否が変わり、順序やCPU負荷は発生頻度を変え得る。今回、CIと同じPlaywright 1.62.0、ローカルはシステムChromium154、CIはPlaywright配布Chromiumなので実行バイナリは同一ではない。全順列・全エンジンの比較は未実施だが、差を仮定しなくても待機の停止を再現できた。

PR #5 head `ed5db1167f01a4d79b136dccdc6a0c5243868c56` のCIは今回APIで再確認し、App isolation／App version／Runner iframe layoutとも最終success。前回のローカル一時失敗がCIでも発生したと断定しない。今回のCIとは別。

## Safari向け画面検証

**Chromiumによる再現。実機Safari／WebKit実行ではない。** 画面サイズは320×568、568×320、375×667、667×375、390×844、844×390、768×1024、1024×768、820×1180、1180×820、507×768、320×1024。

- 新試験2件：各サイズでホーム・9軸、問題／結果、テンキー11個の44px以上、保護者81問一覧、編集管理非表示、クレーン、正式iframeランナー、横はみ出しを検査。高さ844→664→844→600とカード詳細の開閉／Enter／Escape／フォーカス復帰、CSS文字サイズ200%の4幅も検査。
- 既存locked_cardの10画面サイズ・全10画像表示、progress_cardsの9軸と81問一覧、runner_layout／header／safari等の画面・スクロール・拡大・ライフサイクル検査も実行。各ファイルの合否は結果表参照。
- スクリーンショットは `/tmp/kakezan-pr4-review/`（新試験の87枚、metrics.json）、既存カード試験は `/tmp/kakezan-pr5-review/`。一時ブラウザと架空データのみ。代表画面と幅計測は本PRの [文字200%ヘッダー](pr4-evidence/header-text200-320.png)、[横画面ランナー入場先頭](pr4-evidence/runner-landscape-667.png)、[変更前](pr4-evidence/ui-width-before.json)／[変更後](pr4-evidence/ui-width-after.json)、[タップ領域寸法](pr4-evidence/mobile-metrics.json) に保存。
- 320pxの問題、文字200%ホーム、667px横画面のランナー、カード詳細等を画像で確認。フルページスクリーンショットのstickyヘッダー位置は撮影時スクロール位置に依存するため、入場先頭のviewport画像を別保存した。縦に長い画面はスクロールを許す現行仕様。
- Safe Areaの実値、Safariの実アドレスバー伸縮、OSの文字拡大／ズーム、実VoiceOver、iOSファイル出力、BFCacheとOS終了時の保存は完全には再現できない。新試験の高さ変更やCSS200%をこれらの実機合格と扱わない。

[Safari実機チェックシート](SAFARI_DEVICE_CHECKLIST.md) にS01〜S30、A01〜A07、機種・OS・URL・候補SHA・縦横・Split View・結果欄を用意。実機の全項目は未実施。

## 機能別の対応試験と限界

| 項目 | 今回の主な確認先 |
|---|---|
| 固定81問・積・ID・段別／mix／weak・重み／重複・2連続／解除 | multiplication_test、positive_coin_reward_test |
| 中断再開・二重回答／別タブ・コインの原子的保存 | multiplication_test、positive_coin_reward_test、progress_cards_test |
| 9段／総合・10カード条件／所有保持・正式画像／非読込／プレビュー | progress_cards_test、locked_card_test、mobile_regression_test |
| 通算81問正答率・全回答○×・並べ替え・段／プロフィール | progress_cards_test（25回以上と旧履歴除外含む）、mobile_regression_test |
| 固定問題編集不可・テストモード・書出し／復元／拒否 | multiplication_test、progress_cards_test、app_isolation_test |
| クレーン100／test無料・通常／秘密・保存／競合／再開 | arcade_board_test、crane_timing_test、plush_test、plush_popup_test、secret_plush_test |
| ランナー30／test無料・キャラ／ステージ・iframe／保存・物理 | runner全32ファイル（分類表に内容を列挙） |
| 歴史DB非干渉・student/test・17ストア・v10/v11/v12 | app_isolation_test、multiplication_test、progress_cards_test、ゲーム保存群 |

旧歴史UIの試験が多く残っており、九九の基本経路の合格だけで旧群の全異常系を移植済みとは言わない。特にセット最終回答の競合／abort、復帰時の非同期残高表示などの旧シナリオを数値回答で補強する余地がある。

## GitHub Actionsと停止条件

残る旧S06の得点前提試験は現行ワークフローの対象外であり、CI成功でも55ファイル全件合格を意味しない。

PR作成前時点では当該headのActionsは未実施。App isolation（51件）、App version、Runner iframe layout（画像試験修正で対象）を維持。PR作成直後の状態・URL・対象headはドラフトPR本文に記載し、実行中を合格としない。本報告のローカル結果をCIへ流用しない。

最新mainの終了前再確認、最終変更ファイル一覧と版検査結果はPR本文へ記録。ドラフトPRを作成して停止。main直接push、マージ、タグ、Pages公開／設定変更は行わない。

## 残件と推奨順序

1. 実機チェックシートをiPhone／iPadの候補版で実施。合格機種・OSを明記するまで「Safari実機確認済み」にしない。
2. クレーン過去の微小opacityの発生原因は未確定。再発時のtransition時間採取を優先し、物理・演出を変えずに切り分ける。
3. H/O/M群を分類表の方針で移植する。編集・歴史教材・旧カード成功を現在の要件に戻さず、現行異常系と旧保存記録の保護を分ける。
4. このドラフトのCI完了確認とレビュー後、ユーザーがマージ・公開を判断する。今回それらの操作は行わない。

## 追加発見：旧S06の得点前提が残るランナー試験

`RunnerCharacterUITest.test_stage_and_character_are_independent_and_finished_change_resets` は、S06をジャンプせず終了したあと得点>0を要求し、今回5キャラ全て0点で失敗。現行のキャラ選択／再挑戦／リセットを検査する意図は有効だが、その前に終了するため以降のassertまで到達しない。

変更していない配信モデルを120Hzで動かした比較では、旧S06/stageVersion1は全5キャラ10点、現行version7は全5キャラ0点でcollision終了した。[実行可能な診断](pr4-evidence/runner-unattended.mjs)・[結果](pr4-evidence/runner-unattended.json)。コース変更後も旧コースの「無操作でも得点する」を前提にした試験と判断する。アプリが得点を失った証拠とは扱わない。

テストを合格させるための物理・キャラ・ステージ変更や得点assertの削除は行わない。現行の合法入力でスターを取得してから終了／再挑戦させるfixtureへ移し、非ゼロからのリセット検査を維持する対応を提案する。今回この試験は失敗のまま残す。runner_hit_feedback_testがimportした同クラスでも再実行されるが、同じ固有IDの失敗として1件と数える。


## 旧ランナーUI試験の最小移植

`runner_characters_test` の48通りのコース完走試験と、`runner_hit_feedback_test` の被弾描画試験は、現在非表示の `#runner-character-select` にPlaywright select_optionを要求し、可視性の5秒待機で失敗した。現在の公開操作は `#runner-character-cards [data-choice=...]`。両方をそのカードのclickへ変更し、キャラ・ステージ・得点・入力・残機・位置・停止等のassertを残した。前者は元からlegacy_catalog=Trueで旧v1の48経路を固定しており、その入力・コース版を変更しない。読み上げの期待値は現在の「ハートはあと…」へ合わせる。

これは非表示部品をforce操作して通す対応ではない。再実行結果はテスト結果欄に記載する。現行S06で無操作の非ゼロ得点を仮定する別試験にはこの修正を広げず、失敗として残す。


## 残した7固有IDの内訳（現行44ファイルのバッチ）

| 対象（クラス内test_接頭辞を省略） | 実測・判断・推奨 |
|---|---|
| RunnerCharacterUITest.stage_and_character_are_independent_and_finished_change_resets | 現行S06を無操作では0点。旧v1の非ゼロ得点前提。上の比較診断参照。 |
| RunnerHitFeedbackTest.portrait_stack_scroll_and_landscape_unchanged | 試遊URL、844×390でジャンプy=170.640625、開始y=226.640625。試験は同じyを要求するが、現在のCSSは試遊の操作を縦に並べる。正式iframeのレイアウト試験は合格。新しい横並び要件を独断で実装せず、試遊UIの期待配置をレビューしてから試験を移植する。 |
| RunnerPreviewTest.all_six_options_show_metadata_and_select_actual_courses | 旧S05/S06期待値。現行v7はS05の岩4・足場19、S06の足場21等。期待カタログとの版を揃える必要あり。 |
| RunnerPreviewTest.clear_with_one_life_retries_same_course_with_two_lives | 再挑戦直後objects=[]を期待するが現行は負のatの初期イベント3件を生成。コース版に対応した初期状態の独立fixtureが必要。 |
| RunnerPreviewTest.running_and_paused_reject_changes_and_retry_keeps_stage | S05を無操作で6秒進めた後も走行中と仮定。配信モデルでは約距離626.67でcollision終了しており、選択が有効になるのは終了後の通常動作。走行／停止中を確実に作る合法入力fixtureを推奨。 |
| RunnerPreviewTest.two_lives_auto_continue_and_immunity_freeze_at_60_and_120_hz | 再挑戦のobjects=[]前提。同じ初期spawnの不一致。 |
| SecretPlushTest.legacy_backup_generation_uses_restored_prizes_without_local_unlock_leaks | バックアップv5/v6を受入し、欠落arcadeBoardsを生成する旧仕様。現行の確定要件は新アプリv10/v11/v12・全17ストア必須であり、この拒否は仕様どおり。旧形式の拒否／保存不変と現行形式の秘密景品復元へ試験を分離する提案。 |

これらは削除・skip・閾値緩和せず不合格のまま記録した。7件を7個の製品バグと数えない。旧UI／履歴群の175件も分類表とCSVに残し、全635件合格とは報告しない。

## 被弾の状態比較試験

runner_stagesの10サブケースでは、被弾あり／なしのcheckpoint比較に `hitFeedbackRemaining` と `hitPoint` が含まれていた。診断で差分が被弾演出・ハート・無敵時間・岩の除去だけと確認した。[差分の記録](pr4-evidence/collision-fields.json)。物理・スター・イベント等は同じであり、演出状態まで同一を要求するのは不適切。

修正では動き／イベントの厳密一致を維持したまま、被弾演出を別に検査する。被弾時の0.24秒からの進行と座標3値、対照側の演出0／座標nullを追加assert。検査削除・物理変更ではない。対象1件（5状態×60/120Hz）は修正後2.108秒で合格。

被弾描画試験の計測probeも `/plush/` または柴犬だけを捕捉していたため、選択キャラの全スプライトを捕捉するよう修正。柴犬以外でxが存在しないKeyErrorを解消し、4キャラ×動き軽減ON/OFFの元の位置・停止・消滅assertを維持。対象1件は修正後11.399秒で合格。
