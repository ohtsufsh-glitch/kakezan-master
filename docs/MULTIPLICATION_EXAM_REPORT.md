# かけざんテスト 検証報告（v0.4.6候補）

## 基準・範囲

- 基準main：`a99dadbafa3bff6df611770e267cd6d2c71b938a`、アプリv0.4.5。PR #10のマージをGitHub APIと取得したmainで確認。開始時open PRなし。新Issueは作成しない。
- ブランチ：`codex/multiplication-test-20`。候補v0.4.6。
- AGENTS.md、REQUIREMENTS、DECISIONS_AND_TESTSを確認。今回のユーザー確定指示に従い、旧mix10問・実績重みの仕様を置き換える。
- 変更はindex.htmlのmix抽選・ホーム・進捗・結果・数値セット検証・APP_VERSIONと関連テスト／文書。runner/**・assets/**の差分なし。歴史マスター・Pages設定には触れない。

## 実装と保存互換性

ホームの旧表示領域全体を標準button 1個へ置換。ピンク／桜色、20問、100点満点、開始案内を表示し、子のspan/strongを含む全領域で同じclickを受ける。Enter／Spaceは標準buttonの動作を使う。aria-labelは開始／再開／結果再表示を区別する。

`sampleStudyEntries`を再利用。mixは残り候補すべての重みを1として1問ずつ取り除きながら20問抽選し、既存のFisher–Yatesで順序もシャッフルする。履歴の重みも段配分の調整も加えない。弱点候補・実績重み・最大10問と段別抽選は維持。

進捗は「かけざんテスト 3 / 20もん」。採点・テンキー・正誤は既存どおり。20問目の採点後に「けっかをみる！」を押して初めて結果へ進む。得点は保存済み`set.results`の正解数×5。別の得点レコードや追加コインを作らない。大きい中央の得点、正解数、温かいメッセージと再挑戦・ホーム操作を用意。結果イラスト・成績一覧は追加しない。

DB名・schema12／backup12／17ストア・キー・フィールドは不変。中断時の問題・順序・進捗・結果をそのまま再開する。完了mixをホームから開いた場合も同じ結果を表示し、「もういちどテスト」で新しく20問を抽選する。結果再表示で採点・報酬処理を呼ばない。

旧数値mix（従来の検証で許容される0〜10問）を保持。「以前の10問セット」と区別し、ホームでも20問／100点満点表示を旧セット案内へ替える。残りを回答でき、完了結果は回答数・正解数・正答率を表示。100点満点の得点は出さず、次に新20問へ移行できる。11〜19問や21問以上、weakの11問以上、重複問題・結果・欠落・誤った採点は引き続き拒否する。

v10は数値回答非対応という従来制約を維持し、旧v10の非数値バックアップとv11／v12を受け入れる。**新20問セットを含むバックアップはv0.4.5以前へ復元できない。復元にはv0.4.6以降を使う。** 既存データの自動変換・削除や破壊的な保存形式変更は行わない。

学習履歴・習得・段別固定コイン（1/1/3/3/3/4/4/5/5）・プロフィール分離・二重保存防止トランザクションを維持。100点ボーナス・テスト独自報酬なし。保護者用テストモードの変更なし。

## ローカル試験

最終の関連試験は **19固有ID合格、失敗0、skip 0、43.378秒**。画面証拠の撮り直し後、同じlayout IDのみ再実行し合格（9.892秒）。再実行を固有件数へ加算しない。全テストの一括実行や実機Safari合格を意味しない。

```sh
KAKEZAN_EXAM_EVIDENCE=docs/exam-evidence PYTHONPATH=tests python -m unittest -fv \
  multiplication_exam_test multiplication_test \
  table_coin_reward_test.TableCoinRewardTest.test_fixed_rewards_in_mix_weak_and_both_profiles \
  table_coin_reward_test.TableCoinRewardTest.test_replayed_reward_token_rolls_back_in_every_mode \
  app_isolation_test.AppIsolationTest.test_same_origin_isolation_reload_and_new_database_only
python scripts/check_static.py
python -m compileall -q tests/multiplication_exam_test.py tests/multiplication_test.py tests/app_isolation_test.py
git diff --check
python scripts/check_app_version.py --base origin/main --head HEAD
```

- 追加7件：81の等幅乱数区間での抽選・履歴非依存・重複なし・順序シャッフル、苦手最大10と重み維持、0/10/17/20問正解の0/50/85/100点、1〜20問の進捗と明示的次へ、再読込／ホーム後の結果不変・新セットID。
- カードの見出し・説明・100点表示・開始表示・補足の各部分を実クリック。ネストした操作要素なし、aria-label、Enter／Space、touch contextのカード余白tapを確認。
- 途中2問の正誤後に再読込・バックアップ復元で同一entries／position／phase／全ストアを確認。同時タブ・連打・再読込で回答・コインの二重計上なし。
- 旧10問セットをv11／v12バックアップとして検証・復元し、保存不変・途中再開・10問完了・得点非表示・新20問への移行を確認。非対応の数値v10は拒否する。
- 既存九九9件：81問のID・積、テンキー、習得共有、旧非数値v10バックアップとDB更新、重み・苦手候補、未採点／採点済み再開、不正バックアップ、同時タブ等。20問化に対応する期待値だけ更新。
- 報酬2件：全9段×mix/weak×student/testで固定報酬、各モードで重複tokenの原子的ロールバック。分離1件：同一オリジンの旧アプリDB不変、12/12/v0.4.6/17ストア、リロード不変。
- 静的JavaScript／HTML参照、Python構文、差分空白も合格。版検査はコミット後に実施し、PR本文に結果を記録する。

初期検証ではsandbox内のHTTPサーバー起動が拒否され0件だったため、同じ試験をsandbox外で実行。実装途中のイベント登録順の起動エラー、試験のv10数値セット期待値と寸法記録キー不備を修正後、上記を完走した。assert削除・skip・保存検証条件の不当な緩和は行わない。

環境：Linux、Python3.12、Node24.22.3、Playwright1.62.0、Chromium156.0.8078.79。一時contextと架空データのみ。

## 画面寸法・スクリーンショット

390×844／844×390（iPhone縦横）、768×1024／1024×768（iPad縦横）、320×568／375×667／507×768／820×1180の8サイズ × CSS文字100%／200% × ホームカード／結果の **32条件**。横方向の文書はみ出し、対象内の要素のはみ出しなし。得点文字は通常48〜96px。狭い画面は縦スクロールで操作する。文字200%はOS文字拡大の実機確認の代用にはしない。

[寸法JSON](exam-evidence/metrics.json)。開始画像は空の一時DBでホーム上部からカードまでを撮影。結果画像は架空の17/20問正解＝85点でページ全体を撮影する。

| ChromiumのCSS画面サイズ | 開始画面 | 結果画面 |
|---|---|---|
| iPhone縦相当 390×844 | [画像](exam-evidence/home-390x844.png) | [画像](exam-evidence/result-390x844.png) |
| iPhone横相当 844×390 | [画像](exam-evidence/home-844x390.png) | [画像](exam-evidence/result-844x390.png) |
| iPad縦相当 768×1024 | [画像](exam-evidence/home-768x1024.png) | [画像](exam-evidence/result-768x1024.png) |
| iPad横相当 1024×768 | [画像](exam-evidence/home-1024x768.png) | [画像](exam-evidence/result-1024x768.png) |

## CI・未実施

既存必須Actionsは維持し、App isolationに追加局所試験7件を登録。ドラフトPR作成後の当該headの実行状況をPR本文へ記録する。ローカル19件の成功をCIの結果として報告しない。

iPhone／iPad Safari実機、WebKit、VoiceOver、実タップ、Safe Area実値、実アドレスバー伸縮、OS文字拡大、Split Viewの実操作、アプリ切替／BFCacheは未確認。実機ではカードの読み上げと縦横のタッチ、再開・採点・結果・再挑戦、文字拡大とスクロールを確認してほしい。

クレーン／ランナーの物理や無関係な画面の大規模回帰はローカルで実施しない。過去報告の既知不合格を今回解消済みとは扱わない。main直接push・マージ・タグ作成・Pages公開設定変更・歴史マスター変更をせず、ドラフトPRで停止する。
