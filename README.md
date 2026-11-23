# かけざんマスター

小学校低学年向けの、九九（1×1〜9×9）を楽しく練習する日本語Webアプリです。iPhone・iPadのSafariで使うことを想定し、既存の「歴史マスター」の学習・報酬・ミニゲームの仕組みをできるだけ活用します。

> **PR-1移植版 v0.1.0（未公開）：** 独立した保存領域と既存ゲームを移植しました。学習内容はまだ仮の歴史サンプル問題・選択肢UIです。九九学習はPR-2以降で実装します。

## 特長（実装予定・合意済みの仕様）

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
| PR-1 | 参照元の移植・新アプリの独立化 | ドラフトレビュー対象 |
| PR-2 | 九九81問、数字入力、学習モード | 未着手 |
| PR-3 | 9段の進捗、10枚の達成カード、保護者の正答率表示 | 未着手 |
| PR-4 | 総合回帰試験、iPhone・iPad Safari向け調整 | 未着手 |

各作業はブランチとドラフトPRで確認し、ユーザー承認前にmainへマージ・公開しません。

## 開発・テストの現状

移植基準は `4132cf78e29d2f33c4587b16b58e48f7ef3e17d9`（v1.7.56）。アプリ版v0.1.0、DB `kakezan-master-v1`（schema 10）、バックアップ `kakezan-master-backup`（version 10）。歴史版バックアップv1〜v10と新形式の旧版は受理しません。

ローカル起動：`python3 -m http.server 8000` を実行し `http://localhost:8000/` を開きます。外部サービス不要。自動テストはPython 3.12、Node.js、Playwright、Chromiumを使用します。

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
PYTHONPATH=tests python3 -m unittest -v app_isolation_test app_version_test runner_session_test runner_storage_test runner_integration_test runner_bear_test home_arcade_test
python3 scripts/check_static.py
```

システムChromiumの指定には `KAKEZAN_MASTER_BROWSER` を使用できます。ブラウザ試験は一時コンテキストと架空データのみ使用します。生成画像は `/tmp/kakezan-review` 等に保存し、公開GitHubへ実利用データを入れません。

コピー・変更・除外一覧は [移植マニフェスト](docs/PR1_FILES.md)、検証結果・Safari残件は [PR-1報告](docs/PR1_REPORT.md)、旧形式テストの変更理由は [テスト移植記録](docs/PR1_TEST_ADAPTATIONS.md) を参照してください。Pages公開・公開設定変更・マージは行っていません。
