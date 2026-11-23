# 段別コイン報酬・ホーム表示の検証（v0.4.3候補）

基準main：`f770ad066bfba7e61bbe1b32f12735dff29a3f05`、アプリv0.4.2。PR #7はマージ済み。開始・終了前のGitHub確認でmainは同一。open Issueは0件、新Issueは作成していない。専用ブランチ `codex/table-coin-rewards`、候補アプリ版v0.4.3。AGENTS.md、要求仕様、設計判断を着手時に確認した。

## 変更内容と記録方式

| 対象 | 旧仕様 | 今回の回答から |
|---|---|---|
| 九九正解 | 初正解2枚、初習得追加3枚、復習・補完2枚 | 左側の段で1/1/3/3/3/4/4/5/5枚 |
| 初習得・再習得・復習 | 受領状況や習得状態に依存 | 正解1回の固定報酬だけ |
| 不正解・カード追加報酬 | 0枚 | 0枚 |
| 結果説明 | 初正解／初習得等のボーナス説明 | 保存した額の「コインをN枚獲得！」 |
| ホームの段カード | 報酬なし | 段名右側に金貨17pxと枚数、習得数は次行 |

既存coinClaimsは問題×段階の一度限りの記録なので、繰り返し正解の固定報酬へ転用すると互換性・受領管理が複雑になる。旧COIN_REWARDS・coinClaims・coinEventsを維持し、新報酬のみ既存reviewEventsに回答単位で保存する方法を選択した。新キーは `table:<profile>:<answer token>`、旧キーは `review:<profile>:<UUID>`。フィールド追加・ストア追加・DB upgrade・履歴変換・遡及支給は行わない。

新キーには固定九九問題、左側の段による正確な金額、basic、同一プロフィールの正解回答token・問題・時刻が必要。旧金額を新金額の許容値と混ぜない。旧coinEventsは旧first/master額、旧reviewEventsは旧first額で検証する。重複イベント、重複回答token、同じtokenの新旧reviewの二重計上も拒否する。旧回答でtokenがないレコードは保持可能。

回答時は既存セッション・進捗・問題の照合と単一readwriteトランザクションを維持し、カード・コイン・回答・進捗・セッションが同時に確定する。報酬イベントのaddが重複・失敗すれば全体が中断される。起動・再読み込み・旧結果表示・カード授与だけでは報酬を追加しない。

## 保存互換性

- DB名 `kakezan-master-v1`、schema12、17ストア、backup識別子 `kakezan-master-backup`、backupVersion12を維持。
- 新アプリの旧v10（旧問題）／v11／v12バックアップを検証・復元。旧報酬の残高・履歴・claimはそのまま保持し、新規回答だけ固定額を追加する。
- v12の旧九九報酬（2+3+復習2=7枚）を復元し、次の3の段正解で3枚だけ追加、10枚になることを検証。旧イベントとclaimの一致を確認。
- 新旧混在バックアップの書き出し→検証→置換復元→再読み込みで全ストアが一致。
- **新tableイベントを含むバックアップを旧アプリv0.4.2以前で復元する方向は非対応**。旧検証は新キーを拒否する。更新後のバックアップ復元には本候補版以降を使う。
- 歴史マスターのバックアップ・不正額・他プロフィール／問題／時刻・重複・正解回答のない新報酬は拒否する。

## 実施結果

**ローカル95固有ID合格、不合格0、skip 0。** 全リポジトリの全テスト合格を意味しない。[ID別CSV](table-coin-evidence/test-results.csv)。

| 実行（すべて `PYTHONPATH=tests python -m unittest -v`） | 件数・結果 |
|---|---|
| `positive_coin_reward_test multiplication_test progress_cards_test` | 29件合格、49.123秒 |
| `table_coin_reward_test`（最終構成） | 6件合格、14.379秒 |
| `app_isolation_test app_version_test locked_card_test mobile_regression_test quiz_prompt_test runner_storage_test runner_session_test runner_test_mode_test plush_test` | 60件合格、162.895秒 |

`python scripts/check_static.py`、`python -m compileall -q tests scripts`、`git diff --check`合格。`python scripts/check_app_version.py --base origin/main --head HEAD` も合格（v0.4.2→v0.4.3、アプリ変更1ファイル）。

- 全81問を実際に回答・保存し、対応する段の額と結果文を確認。3×8は3枚、8×3は5枚。
- 全9段×ミックス／苦手克服×両プロフィールの36回答を検証。共通の固定額、student/testそれぞれ58枚で分離。
- 初正解・誤答・初習得・復習・再習得の9回答をリロード込みで検証。不正解0、新しい正解は1イベントだけ。
- 採点連打、別タブ競合、全モードの回答UUID再利用、報酬／カード書き込み後の失敗時ロールバックと再試行を確認。
- 未受領の旧報酬を持たない結果も残高を変えず表示し、次の回答だけ固定額を追加。
- カード10種の条件・所有保持・画像、レーダー、履歴、抽選重み、数値入力、保存中断・再開の回帰を実施。
- 両ゲームの支払い（クレーン100、ランナー30、test無料）、プロフィール分離、二重決済防止、途中状態、バックアップ、景品・画像、ゲームUIの関連回帰を実施。runner/**とassets/**の変更なし。

## UIの証拠とアクセシビリティ

Chromiumの12画面サイズ（320×568、568×320、375×667、667×375、390×844、844×390、768×1024、1024×768、820×1180、1180×820、507×768、320×1024）×CSS文字100%／200%×student/test＝48条件で9段すべて検査。カード内横あふれなし、段名と報酬の重なりなし、金貨幅17px、カード44px以上、進捗・称号・習得数と段選択を確認した。200%の狭幅で既存称号があふれたため、段カード内に限定して折返しを許可した。

報酬は `role="img"` と「正解でコインN枚」のアクセシブル名でまとまり、画像と見た目の枚数は読み上げ重複を避けるため装飾扱い。Playwrightのアクセシビリティスナップショットで名前を確認。ミックス／苦手克服には固定報酬枚数を付けない。

- [iPhone相当320px・通常文字](table-coin-evidence/home-320x568-100.png)
- [iPhone相当320px・CSS文字200%](table-coin-evidence/home-320x568-200.png)
- [iPad横相当1024px・通常文字](table-coin-evidence/home-1024x768-100.png)
- [全48条件の寸法・表示値](table-coin-evidence/metrics.json)

実行環境：Linux、Python3.12、Playwright1.62、Chromium。一時コンテキストと架空データのみ。最初のsandbox内実行はHTTPサーバーのsocket作成で拒否され0件実行となったため、許可されたsandbox外実行で上記を完了。UI試験の初回で発見した称号のはみ出しは修正し、最終6件で再検証済み。

## CI・未実施・既知の不合格

GitHub ActionsのApp isolationに新しい6件を追加。ドラフトPR作成前のため当該PRのActions結果は未実施で、CI合格とは扱わない。作成後の結果はPR本文に記録する。

iPhone／iPad実機Safari・WebKit・VoiceOver実機は未実施。縦横、Split View、OS文字拡大、ピンチ、アドレスバー伸縮、Safe Area、読み上げ順と実タップは実機で確認が必要。CSS文字拡大やアクセシビリティ名の自動検査と区別する。

今回の選択した95件に既知の不合格はない。既存全件を再実行したわけではなく、[PR-4報告](PR4_REPORT.md)の旧UI・非対応v5/v6受入・旧ステージ前提等の既知不合格は解消済みとしない。既存試験を削除・skipせず、九九報酬の期待値とアプリ版の期待値を更新した。

main直接push・マージ・タグ・Pages設定・歴史マスターの変更は行わず、ドラフトPRで停止する。
