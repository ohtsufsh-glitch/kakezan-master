# PR-2 九九・数値回答（v0.2.0）

## 基準と範囲

- 開始main：`cae2ce434b65eb5a0c48a79b77cc435bc7937782`、アプリv0.1.0。
- GitHub PR #2（PR-1）のマージを確認。関連するopen Issueなし。新Issue作成なし。開始mainコミットのActions実行一覧は空。PR-1先頭`a7c1c34…`ではApp isolation／App version／Runner iframe layoutが成功済みと最終確認。今回のCI合格とは扱わない。
- `AGENTS.md`、`docs/REQUIREMENTS.md`、`docs/DECISIONS_AND_TESTS.md`を確認し、最新mainから`feat/pr-2-multiplication`を作成。
- 主な変更：`index.html`、数値学習試験`tests/multiplication_test.py`、コイン試験`tests/positive_coin_reward_test.py`、保存分離・ゲーム試験のfixtureと版期待値、Actions、README、本報告。
- `runner/game.js`と`runner/index.html`は配信URLの版0.1.0→0.2.0だけ。物理・ステージ・キャラ・画像・抽選は変更しない。

## 学習と画面

81問を段`T01`〜`T09`、問題`MULT:T01:01`〜`MULT:T09:09`として生成する。IDの左数は段、末尾は右数で、ともに2桁固定。以後変更しない。3×4と4×3は別ID。区切りの`:`は旧版の取り込みIDで禁止されていた文字なので、任意の旧取り込み問題ともIDが衝突しない。各段9問、全問`basic`。式・正解は左数・右数の乗算で生成し、問題配列と各問題をfreeze。編集・追加・非表示・教材インポートの入口を閉じ、書込み関数でも変更を拒否。出題対象は常に生成81問で、旧取り込み問題の設定は九九に作用しない。

画面内の0〜9と「けす」で最大2桁、先頭0禁止。input要素は使わず、outputのライブ領域で入力を表示。キーは高さ52px。空欄は採点不可、入力中は保存・採点しない。「こたえあわせ」で数値を比較し、誤答でも1回の回答として保存。正しい式を2remで表示し、正解までの解き直し・自動遷移なし。セットの最終問も「つぎへ」を押すまで採点結果に留まる。

- 段別：全9段を初期開放、回答数制限なし。既存pickQuestionの基本重み×未習得10／習得済み1、原則直近3問を回避。
- 全段ミックス：全81問から既存sampleStudyEntriesで10問、非復元抽出。基本重みだけを使い、未習得10倍や段ごとの均等配分はしない。
- 苦手克服：過去誤答あり・現在未習得の候補から最大10問、重複なし。未回答候補を再開時に再検証する既存方式を維持。
- 基本重み：未回答5、既回答`1+4*(1-(correct+1)/(attempts+2))`。
- 3モードは問題IDとプロフィール単位のprogress／answers／受領記録を共有。2連続正解で習得、誤答でstreak=0と習得解除。回答イベントを切り捨てず、通算正答率を使用。
- 初正解2枚・初習得3枚、既習得の復習報酬・残高補完報酬を維持。claimを問題ID×プロフィール×段階で重複防止。
- 回答、習得、セッション、回答イベント、受領・報酬を既存の単一IndexedDBトランザクションで保存。セッションとprogressの期待値を照合し、別タブ・重複確定を拒否。
- 保護者の回答イベント閲覧は読み取り専用で維持。student／testを選択でき、旧回答は旧版と表示。81問別の正答率一覧・並べ替えはPR-3。

## 保存・互換性

| 項目 | 今回 |
|---|---|
| アプリ版 | v0.2.0 |
| DB名 | `kakezan-master-v1`（固定） |
| DBスキーマ版 | 10→11、17ストアを維持 |
| バックアップ識別子 | `kakezan-master-backup`（固定） |
| バックアップ版 | 10→11 |
| 数値回答 | `answerType:"number"`, `answer:整数1〜99` |
| 未採点／完了セット | `answer:null` |
| 段別セッションキー | `student:T03`等 |
| 新セットキー | `student:numeric:mix`／`student:numeric:weak`等 |

DB版更新は旧選択肢アプリの開いている接続をversionchangeで閉じ、意味の異なる書込みの並走を防ぐため。ストア追加・削除・既存レコードの初期化はしない。旧版v0.1.0への直接ダウングレードはDB版不一致で開けない。データを消して戻す処理は実装しない。

新しいanswers、sessions、studySetsとセット内resultsには選択肢番号selectedやoptionOrderを保存しない。未採点の入力はメモリだけに置き、ホーム往復・履歴移動・再読み込み時は同じ問題を空欄で復元。採点済みは保存数値・報酬から復元する。setId・position・progress・セッション期待値の照合は維持する。

**v0.1.0のデータは消さない。** 旧サンプル定義と旧取り込み問題は履歴・報酬・バックアップ参照用として保持する。旧progress、answers、sessions、studySets、awards、coinClaims、coinEvents、reviewEvents、設定・指摘、全ゲームストアは起動時に書き換えない。旧学習は九九の成績へ算入しない。旧学習セッションと旧セットは保存のみ継続し、九九として再開しない。旧weakキーと新numeric:weakキーを分け、九九のセット開始で旧セットを上書きしない。旧コインは既存残高の一部として引き続きゲームで使用可能。

バックアップv11は旧記録と新しい数値記録を両方収録するため版を上げた。新アプリのv10は旧選択肢形式として検証・受入し、九九データの混入を拒否する。書出しは常にv11。v11の数値回答・セット参照・重複・プロフィール・正誤一致・数値範囲・選択肢フィールド不在を検証する。旧指摘のスナップショットは旧時代定義で検証。歴史アプリ形式、v1〜9、未来版、ストア不足は拒否。ゲーム検証は既存方式を維持。復元は検査→プレビュー→確認→全17ストアを単一トランザクションで置換し、自動マージはしない。

旧データ保持は同アプリの架空fixtureと、実際にv10で作成したDBのv11アップグレードで確認する。歴史マスターの利用者データ・実バックアップは使用しない。歴史版DBに接続しない同一オリジンsentinel試験も継続する。

## テスト変更の理由

- `multiplication_test`：81問、入力・明示的遷移、セット、抽選、習得共有、プロフィール、再開、競合、不正復元、旧版保持を新規自動化。
- `positive_coin_reward_test`：選択肢・変更可能な難易度・単一の取り込み歴史問題という前提を、固定した基礎の九九へ置換。初正解・初習得・再習得・復習・補完・競合・トランザクションabort・旧0枚結果・バックアップ・プロフィールの検証目的を継続。九九で獲得した131枚からランナー30枚とクレーン100枚を使う試験も追加。
- `plush_test`：履歴fixtureの非表示IDはLEGACY_QUESTIONSを使用。現行書出し期待値を11へ変更。fixtureのコイン・景品は削減しない。
- `app_isolation_test`：DB／backup／app版と未来版拒否の期待値を更新。
- `runner_storage_test`：現行書出し期待値だけ11へ更新。旧v10の読込み検証も継続。
- 拡張ランナー／bear／retire／canvas／spike試験：現行DB版・バックアップ版11と配信URL版0.2.0の期待値を更新。旧v10の架空データを検証する呼出しは互換試験として残す。
- `runner_integration_test`：確認ダイアログのキャンセル後、runnerStarting解除と選択UIの有効化を待つ。click後の非同期confirm前に次のonceハンドラーまで登録され、同じダイアログを二重処理する競合が再現したため。ゲームの仕様変更・試験省略ではない。
- ActionsのApp isolationに九九と数値コイン試験を追加。無条件skipや試験目的の削除なし。歴史教材編集・時代カードそのものを対象にした過去の専用試験は、現行UIの受入スイートとは区別して保存する。

## 検証結果

Chromiumでの一括受入・回帰試験：**73件合格（125.081秒）**。永続IDを旧インポートと衝突しない形式へ確定した後、影響する九九・数値コイン試験**18件も全合格（52.608秒）**。重複実行を合算しない。

拡張ランナーの版期待値に関係する10件は、初回9合格・リタイア結果配列内の版期待値が1失敗。残った期待値を11へ更新し、**10件すべて合格（37.621秒）**。

静的検査、Pythonコンパイル、差分空白、アプリ版検査は合格。版検査は最新origin/mainを再取得してv0.1.0→v0.2.0を確認。AGENTS／要求仕様／設計判断の既存3文書はmainとの差分なし。

追加ブラウザ計測：375×812、844×390、820×1180、507×768で全テンキーが44px以上、横はみ出しなし。375pxのスクリーンショットを目視確認。保護者の旧問題変更・旧カード画像UIが非表示であることを確認。実機Safari確認ではない。

このPRのGitHub CIはドラフト作成後に起動するため、ここでは合格と報告しない。

```sh
PYTHONPATH=tests python -m unittest -v multiplication_test positive_coin_reward_test app_isolation_test app_version_test runner_session_test runner_storage_test runner_integration_test home_arcade_test plush_test.PlushTest.test_student_cost_free_repeat_test_and_profile_separation plush_test.PlushTest.test_new_prizes_backup_download_preview_restore_and_reload_all_stores
python scripts/check_static.py
python -m compileall -q scripts tests
git diff --check
python scripts/check_app_version.py --base origin/main --head HEAD
```

途中結果：最初の九九5件は3合格・fixture順序1失敗・採点済み再開のテスト期待値1エラー。修正後の九九7件は全合格。保存・ランナーを含む30件は29合格、書出し版の期待値10が1失敗。続く56件は54合格・版期待値1失敗・テスト補助の関数代入呼出し1エラー。いずれも修正済み。続く72件は71合格、ランナー確認ダイアログの二重ハンドラーで1エラー。イベント取得後にacceptする試みはclick自体がconfirmでブロックして2件タイムアウトになったため取り下げ、既存の同期ハンドラーとキャンセル完了待ちを組み合わせた。該当2件は単独合格。同じイベント後accept方式の追加実行73件も、4件のconfirmクリックタイムアウトを確認した。方式取り下げ後の一括73件合格を最終結果とする。これらを最終一括結果へ加算しない。


最終IDでの再実行と、版期待値が変わった拡張試験：

```sh
PYTHONPATH=tests python -m unittest -v multiplication_test positive_coin_reward_test
PYTHONPATH=tests python -m unittest -v \
  runner_phase2a_test.RunnerPhase2ACompatibilityTest.test_version2_paid_s04_pause_resume_finish_history_scores_and_profiles \
  runner_crumbling_test.RunnerCrumblingCompatibilityTest.test_frozen_v6_paid_trajectories_and_v6_v7_mixed_backups \
  runner_bear_test.RunnerBearSaveTest.test_mixed_backup_old_backups_and_s05_s06_version7_resume \
  runner_vertical_test.RunnerVerticalCompatibilityTest.test_latest_purchases_save_reload_and_official_clear_three_stages \
  runner_spike_design_test.RunnerSpikeDesignTest.test_alpha_contact_collision_coverage_and_cache_identifier \
  runner_canvas_test.RunnerCanvasTest.test_spike_rock_image_loads_with_alpha_and_stays_grounded_in_phone_tablet_layouts \
  runner_density_test.RunnerDensityCompatibilityTest.test_density_paid_records_save_reload_and_official_clear_all_six_stages \
  runner_tuning_test.RunnerTuningCompatibilityTest.test_historical_v3_purchases_save_reload_and_official_clear_all_three_stages \
  runner_phase1_test.RunnerPhase1CompatibilityTest.test_mixed_v1_v2_complete_backup_download_validate_and_restore \
  runner_retire_test.RunnerRetireTest.test_v10_export_restore_reload_retire_record
```

## 残件・制限

- iPhone/iPad Safari実機は未実施。Chromium自動試験とは別。テンキーの実タップ・VoiceOver読み上げ・44px以上の領域・文字拡大・縦横・アドレスバー伸縮・iPad Split View・Safe Area、アプリ切替／BFCacheの採点前後、端末ファイルへのバックアップ書出し／復元、ゲームの実タップ・保存再開を確認する。
- PR-1からのクレーン位置計測（幅375px、star／secret_koryun等）の未完了事項は継続。今回解決済みとは扱わない。物理・抽選・景品は変更せず、未マージ参照元PRも取り込まない。
- 全テストdiscoverと全拡張ランナー全件の一括実行は今回未実施。拡張コースは版期待値が変わる試験を対象に、既存の軌道・保存・終了の検証を実行。旧歴史問題編集・旧時代カードを現行UIで期待する専用試験はそのまま受入結果に算入しない。
- PR-3：9段レーダー最終デザイン、段別9枚＋完全制覇1枚と画像、81問別の正答率一覧・並べ替え。旧カードの授与と表示は停止し、既存所有記録は保持。準備中を完成済みと表示しない。
- PR-4：総合回帰・Safari実機・保護者画面の追加整理。PWA、クラウド同期、ミニゲーム改良は実装しない。
- 新Issue・main直接push・マージ・タグ・公開・Pages設定変更・歴史マスターへの書込みなし。ドラフトPR作成で停止する。
