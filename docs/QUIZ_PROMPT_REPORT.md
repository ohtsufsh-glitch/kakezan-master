# 問題文の拡大・中央表示・記号削除（v0.4.2候補）

- 基準main：`a104d7411e0a05c1737f6b6c1ebb359e29acd879`（v0.4.1、PR #6マージ済み）。
- 作業ブランチ：`codex/quiz-prompt-layout`。最新mainから作成。
- 候補版：v0.4.2。公開配信版の確認・公開操作は行わない。
- 着手前にAGENTS.md、要求仕様書、設計判断を確認。open Issue／PR検索はいずれも0件。

## 変更内容・影響範囲

学習画面の描画文字列を `3 × 4 = ?` から `3 × 4` に変更。左右の数字をそのまま使い、×を維持する。内部の問題文字列 `q.q` は保護者一覧等でも使うため変更しない。

CSSは `#quiz #question-text` のみに適用。中央寄せ、1行表示、`clamp(2.5rem, 10vw, 4rem)` で拡大し、行高1.25・最小高さ1.6emの領域内で縦方向も中央に配置。通常18.4pxから40〜64pxへ拡大した。画面全体の縦中央固定は行わない。短い縦画面・横画面は縦スクロールしてテンキー・ボタンへ到達する。全操作を1画面内に収める変更ではない。

実行コードの差分は、このCSS、描画文字列、APP_VERSIONのみ。数字入力欄・テンキーの配置と動作、こたえあわせ、出題、81問のID／正解／revision、履歴・習得・報酬、ミニゲーム、DB名／schema12／17ストア、バックアップ形式／version12は維持。結果の正答式 `3 × 4 = 12`、保護者一覧の問題文字列とレイアウトも維持する。

## 変更前後の画面

同じLinux Chromium、同じ問題（3×4）、架空の新規データで取得。画像はページ全体のキャプチャであり、縦スクロール分を含む。beforeは基準main、afterは本変更。

| CSS画面サイズ | 変更前 | 変更後 | 問題文の文字サイズ |
|---|---|---|---|
| 320×568（狭幅縦） | [before](quiz-prompt-evidence/before-320x568.png) | [after](quiz-prompt-evidence/after-320x568.png) | 18.4→40px |
| 667×375（横） | [before](quiz-prompt-evidence/before-667x375.png) | [after](quiz-prompt-evidence/after-667x375.png) | 18.4→64px |
| 768×1024（タブレット縦） | [before](quiz-prompt-evidence/before-768x1024.png) | [after](quiz-prompt-evidence/after-768x1024.png) | 18.4→64px |
| 1024×768（タブレット横） | [before](quiz-prompt-evidence/before-1024x768.png) | [after](quiz-prompt-evidence/after-1024x768.png) | 18.4→64px |

実測値：[before](quiz-prompt-evidence/before-metrics.json) ／ [after](quiz-prompt-evidence/after-metrics.json)。4サイズとも横方向のdocument.scrollWidthは画面幅と一致。

## テスト

環境：Linux、Python 3.12.14、Node v24.22.3、Playwright 1.62.0、Chromium 156.0.8078.79。一時contextと架空のデータのみを使用。

- `PYTHONPATH=tests python -m unittest -v quiz_prompt_test`：3件合格（14.492秒）。81通りの表示と内部カタログ・ストア不変、児童／テストの2プロフィール×12サイズで中心位置・1行・文字サイズ・操作部の非重複・横あふれなし・テンキー44px以上、実際のテンキー入力／正誤採点／次へ／入力クリア／保護者81件一覧を確認。
- 上の12サイズ：320×568、568×320、375×667、667×375、390×844、844×390、768×1024、1024×768、820×1180、1180×820、507×768、320×1024。各サイズの採点後・次の問題も確認。
- CSS文字200%：320×568、667×375、507×768、1024×768で1行・中央・非重複・横あふれなしを確認。OSの文字拡大確認とは区別する。
- `PYTHONPATH=tests python -m unittest -v multiplication_test progress_cards_test locked_card_test positive_coin_reward_test app_isolation_test app_version_test mobile_regression_test`：51件合格（178.541秒）。九九生成・採点・中断再開・二重回答・抽選・プロフィール分離・バックアップ／DB維持、カード・報酬・保護者一覧、ホーム／結果／両ゲームの12サイズ画面回帰を確認。専用3件と合わせて54件合格。リポジトリ全テストの合格を意味しない。
- `python scripts/check_static.py`、`python -m compileall -q tests scripts`、`git diff --check`：合格。
- `python scripts/check_app_version.py --base origin/main --head HEAD`：合格（v0.4.1→v0.4.2、アプリ変更1ファイル）。終了前のmain再取得でも基準SHAは同一。GitHub Actionsの結果は未確認。追加3件を既存App isolationワークフローへ登録した。

## 未実施・レビューでの実機確認

iPhone／iPad実機SafariおよびWebKitは未実施。既存55ファイル全件の再実行は行わず、前PRの既知失敗・未解決事項を解消済みとは扱わない。

- iPhoneの狭幅縦・横で式が大きく中央の1行に収まり、スクロールして全テンキー・こたえあわせ・つぎへを押せること。
- iPadの縦・横・Split Viewで余白と問題文サイズが自然で、問題文・入力欄・テンキー・ボタンが重ならないこと。
- アドレスバー伸縮、Safe Area、OS文字拡大、ピンチ拡大、VoiceOverで欠け・読み上げ・操作への影響がないこと。
- 児童／テスト双方で採点・次へが動き、正答結果の「= 正解の数字」と保護者一覧の既存表示が保たれること。

main直接push、マージ、タグ作成、Pages設定／公開、歴史マスター側の変更は行わず、ドラフトPR作成で停止する。
