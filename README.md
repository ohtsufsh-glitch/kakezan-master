# かけざんマスター

小学校低学年向けの、九九（1×1〜9×9）を楽しく練習する日本語Webアプリです。iPhone・iPadのSafariで使うことを想定し、既存の「歴史マスター」の学習・報酬・ミニゲームの仕組みをできるだけ活用します。

> **PR-3 v0.3.0（未公開）：** 9段レーダー、段別9枚＋九九完全制覇1枚の授与と仮表示、保護者用81問別の通算正答率・全回答履歴を実装。10種類のキャラクター画像・名称・モチーフは制作待ちです。

## 特長

- 1の段〜9の段、左側の数を固定した段別学習と全段ミックス
- 全81問の自動生成、画面内テンキーによる数値回答と採点
- 苦手優先の出題、2回連続正解での習得、習得済み問題の復習
- 9段の進捗レーダーと総合理解度、81問別の通算正答率を保護者画面に表示
- 段別9枚＋九九完全制覇1枚、合計10枚の達成カード
- コイン、ぬいぐるみキャッチャー、わくわくランナー
- 保護者用テストモード、保存・再開、手動バックアップ・復元
- 歴史マスターから完全に分離した保存データ

## 開発文書

- [要求仕様書](docs/REQUIREMENTS.md)：確定済みの学習仕様、追加する機能、受入条件
- [設計判断とテスト方針](docs/DECISIONS_AND_TESTS.md)：設計決定、実装上の差分、テスト計画
- [Codex開発指示](AGENTS.md)：実装手順、データ保護、変更禁止事項

## 参照元と独立性

- 参照元：[歴史マスター](https://github.com/ohtsufsh-glitch/history-master)
- 初期移植検討で調査した基準コミット：`4132cf78e29d2f33c4587b16b58e48f7ef3e17d9`（アプリv1.7.56）
- 本リポジトリは独立プロジェクト。歴史マスターのソース・学習データ・DB・バックアップ・ゲーム保存を変更しません。
- ランナーの iframe 方式やミニゲームの物理・確率は原則維持します。

## 開発ロードマップ

| 段階 | 内容 | 状態 |
|---|---|---|
| PR-0 | 仕様書・開発ルールの整備 | mainマージ済み |
| PR-1 | 参照元の移植・新アプリの独立化 | mainマージ済み |
| PR-2 | 九九81問、数字入力、学習モード | mainマージ済み |
| PR-3 | 9段の進捗、10枚の達成カード、保護者の正答率表示 | ドラフトレビュー対象（画像は制作待ち） |
| PR-4 | 総合回帰試験、iPhone・iPad Safari向け調整 | 未着手 |

各作業はブランチとドラフトPRで確認し、ユーザー承認前にmainへマージ・公開しません。

## 開発・テストの現状

移植基準は `4132cf78e29d2f33c4587b16b58e48f7ef3e17d9`（v1.7.56）。アプリ版v0.3.0、DB `kakezan-master-v1`（schema 12・17ストア）、バックアップ `kakezan-master-backup`（version 12）。新アプリの旧v10/v11バックアップは検証後に復元できます。歴史版の形式、v1〜9、未来版は拒否します。旧問題の履歴・コイン・ゲームは保持し、九九とは別IDで扱います。旧学習セッションは保存のみ継続し、九九として再開しません。v0.1.0/v0.2.0への直接ダウングレードはDB版のためできません。

ローカル起動：`python3 -m http.server 8000` を実行し `http://localhost:8000/` を開きます。外部サービス不要。自動テストはPython 3.12、Node.js、Playwright、Chromiumを使用します。

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
PYTHONPATH=tests python3 -m unittest -v progress_cards_test locked_card_test multiplication_test positive_coin_reward_test app_isolation_test app_version_test runner_session_test runner_storage_test runner_integration_test runner_bear_test home_arcade_test
python3 scripts/check_static.py
```

システムChromiumの指定には `KAKEZAN_MASTER_BROWSER` を使用できます。ブラウザ試験は一時コンテキストと架空データのみ使用します。生成画像は `/tmp/kakezan-review` 等に保存し、公開GitHubへ実利用データを入れません。

コピー・変更・除外一覧は [移植マニフェスト](docs/PR1_FILES.md)、検証結果・Safari残件は [PR-1報告](docs/PR1_REPORT.md)、旧形式テストの変更理由は [テスト移植記録](docs/PR1_TEST_ADAPTATIONS.md) を参照してください。Pages公開・公開設定変更・マージは行っていません。

PR-2の保存互換方針・検証結果・後続作業は [PR-2報告](docs/PR2_REPORT.md) を参照してください。

PR-3の計算方法・カード条件・互換性・テスト結果は [PR-3報告](docs/PR3_REPORT.md) を参照してください。旧歴史カード20件＋九九カード20件（両プロフィール）を保存・復元できます。回答履歴の切り捨て・旧データの自動変換は行いません。Safari実機とクレーン位置計測の残件はPR-4へ引き継ぎます。
