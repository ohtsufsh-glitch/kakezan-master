# PR-5 正式達成カード画像の組み込み

> 過去工程時点の記録。PR #5はmainへマージ済み（v0.4.0、正式カード10枚実装済み）。現在の検証結果・残件は [PR-4総合報告](PR4_REPORT.md) を参照。公開配信版とSafari実機の確認は別項目です。


## 基準・公開状況

- 作業開始時・終了前再確認のmain：`f267cc52f14aac9e7fef6458b8aef0b3ebb1f291`、アプリv0.3.0。GitHub PR #4（工程名PR-3）のマージを確認。開始時open PRは0件。新Issueは作成しない。
- mainから `codex/pr5-official-achievement-cards` を作成。この未マージPRの候補版はv0.4.0。mainのカードは仮表示、このブランチでは正式画像を表示する。
- リポジトリにはPagesがあるが、公開URLの取得は環境の通信制限（CONNECT 403）で未確認。mainの状態と公開中の配信版を同一と断定せず、v0.4.0を公開済みとも報告しない。Pagesの公開操作・設定変更なし。
- DB `kakezan-master-v1`、schema 12、backup `kakezan-master-backup`／12、17ストアを維持。カードID・達成条件・所有記録、九九、抽選、2連続正解、履歴、コイン、ゲーム処理は変更しない。

## 正本画像

ユーザー添付ZIPから次の10枚だけを `assets/cards/` へ展開。画像のデザイン変更・再生成・再圧縮なし。全ファイルがZIPエントリと完全一致することを確認。旧 `E01.webp`〜`E10.webp` は変更・削除しない。

ZIP SHA-256：`21a30bd8eb0396eb7030b02d62a118cc964c9bd7b98108fa68acd8caaa7b9e4f`

全10枚 **WebP、1086×1448px、縦横比3:4**。合計 **4,028,866 bytes（約3.84 MiB）**。

| ファイル | 達成内容 | 動物 | bytes |
|---|---|---|---:|
| `T01.webp` | 1の段 | うさぎ | 367,248 |
| `T02.webp` | 2の段 | くま | 443,174 |
| `T03.webp` | 3の段 | リス | 450,588 |
| `T04.webp` | 4の段 | ペンギン | 424,706 |
| `T05.webp` | 5の段 | パンダ | 400,012 |
| `T06.webp` | 6の段 | コアラ | 360,156 |
| `T07.webp` | 7の段 | キツネ | 400,656 |
| `T08.webp` | 8の段 | ひつじ | 350,356 |
| `T09.webp` | 9の段 | 鹿 | 346,030 |
| `ALL81.webp` | 九九完全制覇 | 王冠をかぶった猫 | 485,940 |

Pillowで形式・寸法・全デコードを確認し、全10枚のコンタクトシートで段と動物の対応を目視した。テストにも承認済み画像のSHA-256を固定し、ファイル取り違え・加工・破損を検出する。Chromiumでも実画像のデコードと自然寸法を検証。

## カード表示

- `cardArt()`：未獲得なら従来同様のロック表示だけを生成し、画像URL・img・CSS背景・preloadは作らない。画像表示を共通化し、ホームの獲得済みカード、詳細ダイアログ、獲得通知にIDと同名のWebPを表示する。
- 保護者プレビューは明示的に展開したときだけ全10枚を生成。プレビューを閉じる／管理画面を離れるとDOMを除去。詳細を閉じると詳細画像も除去し、画面遷移時は前の獲得通知も除去。プレビューによるawards等への書き込みなし。
- 3:4と `object-fit:contain` で画像全体を表示。詳細は幅と画面高でサイズを制限し、横画面でも上下の文字・顔を保持する。画像の上へ文字を重ねる旧CSSは削除。
- 画像エラーはカード名付きの代替表示。画像外のカード名・段・獲得状態・残り問題数も維持。
- 空alt＋アートのaria-hiddenで重複読み上げを抑え、外側の意味のあるテキストと獲得済みボタンのラベルでカード名・段・所有状態を伝える。詳細dialogはタイトルと段・状態をaria-labelledby／aria-describedbyで参照。キーボードEnter、Escape、フォーカス復帰、タッチによる詳細表示をテスト。実機VoiceOverは未実施。

## 検証結果

Python 3.12、Node v24.19.0、Playwright 1.62.0、システムChromium。ブラウザは一時コンテキスト・架空データのみ。実機Safari確認ではない。

### 正式画像・画面

`PYTHONPATH=tests python -m unittest -v locked_card_test`

- **7件すべて合格（最終再実行81.248秒）**。正本ハッシュ・WebP・全10枚デコード・寸法・3:4・カードID対応、未獲得画像の通信ゼロ、獲得済み10枚とプロフィール分離、一覧／詳細／全10通知、実際の回答でのT01／ALL81授与通知、保護者プレビュー前後の全17ストア一致を検証。
- 404時の一覧10枚・詳細10枚・通知・プレビューで代替表示とカード名を確認。旧重ね文字DOMがないことも検証。
- 320×568、375×667、667×375、390×844、844×390、768×1024、1024×768、820×1180、1180×820、507×768で全10枚の3:4表示と横はみ出しなし、T01／ALL81詳細の画像全体がviewport内にあることを検査。
- スクリーンショット31枚：`/tmp/kakezan-pr5-review/`（各画面の一覧10枚、詳細20枚、実際のALL81獲得通知1枚）。元画像コンタクトシートは `/tmp/card-contact-sheet.jpg`。iPhone相当の縦・横とiPad相当の詳細、iPhone相当の一覧、通知を目視確認し、画像内の文字とアプリ文字の重なり・顔や上下文字の切れがないことを確認。

### 九九・カード授与・履歴・保存

`PYTHONPATH=tests python -m unittest -v progress_cards_test multiplication_test positive_coin_reward_test app_isolation_test app_version_test`

**42件すべて合格（最終再実行149.676秒）**。81問の計算・数値回答・抽選・2連続習得・報酬、カード授与と既得保持・同時授与・別タブとabort、全期間履歴、student/test、v10/v11互換、全17ストアのバックアップ往復を確認。旧アプリとのDB分離、全配布画像デコード、アプリ版検査も合格。

### ミニゲーム回帰

既存 `.github/workflows/runner-iframe.yml` の以下3ステップと同じコマンドをローカルで実行した。

| 試験群 | 結果 |
|---|---|
| Targeted formal runner tests | 52件中51件合格・1件失敗（340.799秒）。失敗1件は変更なしの単独再実行で合格（11.022秒） |
| Retire confirmation and paid-play safety | 14件すべて合格（50.117秒） |
| Course physics and paid-play compatibility | 108件すべて合格（519.380秒） |

初回の失敗は `RunnerAnimationTest.test_delayed_and_failed_new_sprites_keep_input_and_same_character`。404画像を含む `runnerImages.every(i=>i.complete)` の5秒待機がタイムアウトし、その直後の診断では `salamander: pending images []`。同じテストをコード・待機閾値の変更なしで単独実行すると合格した。一時的な待機失敗と整合するが原因は断定しない。52件全体を再実行して合格したとは扱わない。ゲームコードや既存テストの検証内容は変更しない。

クレーン：`crane_timing_test` と、`PlushTest` のバックアップ全ストア往復・student100枚/test無料分離・手動再開、`ArcadeBoardTest` の購入/入替競合・別タブ・完了トランザクションabortの6件。

**10件すべて合格（76.094秒）**。演出タイミング、支払い・保存・プロフィール分離・手動再開・競合・ロールバックを検証。

PR-1からのクレーン透明度・位置計測テスト `test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes` は今回の表示変更と独立の既知残件として未再実行。PR-3時点では終了時opacityが厳密な0とならない6サブケースで失敗（幅375/secret_koryun、640/star、641・759/starとsecret_koryun）。閾値・描画・物理を変更して通す対応はしていない。クレーン全件合格とは報告しない。

### 静的検査・GitHub Actions

`python scripts/check_static.py`、`python -m compileall -q scripts tests`、`git diff --check` は合格。親／runnerの構文、HTML／module参照、アプリ識別子を検査。アプリ版比較は最終コミットを最新mainに対して検査し、PR説明へ結果を記録する。

この報告書の保存時点はドラフトPR作成前のため、当該headに対するGitHub Actionsは未実施。既存App isolation（新しい画像試験7件を含む）・App version・Runner iframe layoutを維持。PR作成後の実行結果はドラフトPRの説明へ記録し、ローカル結果をGitHub上のCI合格とは扱わない。

## Safari実機未確認・今後の残件

- iPhone/iPad SafariでWebPの実表示・読み込み失敗時表示・画像の鮮明さ、縦横回転、Safe Area、アドレスバー伸縮、iPad Split View、文字拡大を確認する。
- VoiceOverでカード名・段・獲得状態、重複読み上げ、詳細ダイアログのフォーカスと閉じる操作を確認する。Chromiumのアクセシビリティ属性／キーボード／タッチ試験は代替にならない。
- 実タップの学習・クレーン・ランナー、アプリ切替/BFCacheと保存、端末ファイルへのバックアップ書出し／選択／復元は別途確認。
- PR-1からのクレーン透明度・掴み位置・持上げ同期の全組合せ計測、旧歴史UI専用試験整理、工程PR-4の実機・総合確認残件を継続する。
- ドラフトPRで停止。main直接push、マージ、タグ作成、Pages設定変更、歴史マスターの変更は行わない。
