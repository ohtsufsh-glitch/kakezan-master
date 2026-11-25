# Issue #15 結果表示・誤答一覧の検証

- 基準main：`762a0ef092b6b97526df681d742b61fb61d69803`、v0.4.7。開始時にfetchし、PR #11〜#13マージ済み・open PRなし、Issue #14／#15とコメントを確認。
- 候補：v0.4.8、ブランチ `codex/issue-15-exam-results`。Refs #15。満点専用画像・文言整理（Issue #14）は含めない。

## 実装・保存への影響

100点未満の20問テストだけ、重複する「20もんちゅう…」を隠す。得点・正解数・既存の励ましの後に、不正解すべての式と正答を表示する。小さい画面は1列、768px以上は2列、柔らかい桜色の枠で区切り、答えは太字と色で強調する。長い場合は自然な縦スクロールを使う。

保存済みstudySets.resultsをcorrect===falseで抽出し、position昇順に並べる。entriesの位置・questionId・revisionと81問カタログのID・revisionを照合してq.left／q.right／q.answerを使う。不整合の行は「この もんだいは ひょうじできません。」とし、式・答えを推測しない。結果配列を直接sortせず、再採点・報酬処理・保存を追加しない。

既存100点の星・背景・文言、旧10問mix・苦手克服の結果を維持。DBスキーマ12、バックアップ12、17ストアの構造・レコードは変更しない。抽選・採点・習得・コイン・ゲーム・iframe・歴史マスターへの変更なし。

## 局所テスト

Python 3.12.14、Playwright 1.62.0、Chromium 156.0.8078.79、Linux。一時コンテキストと架空データのみ。

```sh
KAKEZAN_EXAM_EVIDENCE=/tmp/issue-15-evidence PYTHONPATH=tests python -m unittest -fv \
  multiplication_exam_test \
  app_isolation_test.AppIsolationTest.test_same_origin_isolation_reload_and_new_database_only \
  multiplication_test.MultiplicationTest.test_mix_twenty_unique_and_explicit_next
python scripts/check_static.py
python -m compileall -q tests/multiplication_exam_test.py tests/app_isolation_test.py
git diff --check
python scripts/check_app_version.py --base origin/main --head HEAD
```

- **10件合格、失敗0、skip 0、46.236秒**。結果関連8件と既存の保存分離・満点結果各1件。
- 0／50／85／95／100点の得点・正解数・励ましを検査。0点20件、85点3件、95点1件、100点0件。式をテスト側で乗算して検算、正答のstrongと読み上げ名を確認する。
- 最初・途中・最後の誤答、results配列を逆順にした保存データでもposition順、正解混入なし。リロード・ホームからの再表示・backup12置換復元後に一覧一致・全17ストア一致。
- 不明ID／カタログと異なるrevision／entriesとresultsの不一致で、誤った式・答えを出さず、閲覧前後の全ストア一致。
- 旧10問・苦手克服の結果、満点演出と動きを減らす設定、明示的な再挑戦、既存の等確率抽選・中断再開・二重採点防止・バックアップ拒否条件も維持して検査。
- 390×844、844×390、768×1024、1024×768、320×568、375×667、507×768、820×1180。それぞれ文字100%／200%でホーム・85点・0点・100点の計64条件。横はみ出しなし、得点48px以上、操作44px以上。誤答全件と操作がスクロールでviewport内に入り、ボタンが有効でキーボードフォーカス可能なことを検査。長い一覧の追加に伴い、非満点の操作を初期viewport内に要求する旧検査を全件・操作への到達検査へ変更。100点の初期viewport検査は維持。
- 初回はローカルサーバー起動がサンドボックスで拒否され、0件実行。許可付き実行の初回は5件中、ホームから再表示直後の1件が未表示状態を読んで失敗。非同期の結果画面表示を待ってから厳密なassertを行うようテストを修正し、上記10件を完走。固定sleep・期待値緩和・skipなし。
- 静的検査・変更したPythonの構文検査・差分空白検査は合格。コミット後の版比較もv0.4.7→v0.4.8（アプリ変更1ファイル）で合格。

## 画面証拠

Chromiumの390×844 CSS px、文字100%、全ページ画像。実機Safariの撮影ではない。85点・0点とiPad相当0点画像を目視し、見出し・式・正答・全20件・操作を確認した。

- [85点・3件](issue15-evidence/result-85-390x844.png)
- [0点・20件](issue15-evidence/result-0-390x844.png)

## Actions・未確認事項

既存必須Actionsの設定は変更せず、既にApp isolationに登録済みのmultiplication_exam_testを拡張した。PR作成前の当該headのActionsは未実行。作成直後に確認した状態をPR本文へ記載する。ローカル10件合格をCI合格とは扱わない。

iPhone／iPad Safari実機・WebKit・VoiceOverは未確認。読み上げの発音・重複、縦横回転、アドレスバー伸縮、Safe Area、Split View、OS文字拡大、実タップ・ピンチ拡大を実機で確認する。CSS文字200%・アクセシビリティ属性の検査は実機確認の代わりではない。

ユーザーの指定に従い、無関係なゲーム物理・全テストスイートはローカルで実行しない。ドラフトPR作成で停止し、mainへの直接push・マージ・タグ・Pages設定変更は行わない。
