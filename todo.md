# telegram_diary TODO

## 0. 推奨順序
- [ ] 1) リポジトリ + CI セットアップ
- [ ] 2) Telegram Bot セットアップ
- [ ] 3) 本番環境（Ubuntu + runner + CD）
- [ ] 4) 取り込み: state_store + fetcher + dedup
- [ ] 5) 日次生成: journal_writer + summarizer + tagger
- [ ] 6) 信頼性: リトライ + ログ + ヘルスチェック
- [ ] 7) 運用: ポーリング + cron + 運用手順書
- [ ] 8) 結合: E2E テスト + 最終リファクタ
- [ ] 9) LLM 連携（任意）: feature flag + pipe 実行

## 1. リポジトリ + CI セットアップ
- [ ] GitHub リポジトリ作成 + `pyproject.toml` / `.gitignore` 初期コミット
- [ ] CI ワークフロー作成 (`.github/workflows/ci.yml`: ruff + pytest)
- [ ] ブランチ保護ルール設定（CI パス必須）
- [ ] Copilot code review 有効化

## 2. Telegram Bot セットアップ
- [ ] BotFather で Bot 作成、トークン取得
- [ ] 専用プライベートチャンネル作成
- [ ] Bot をチャンネルに読み取り権限で追加、`chat_id` を確認
- [ ] 環境変数を設定（`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`）

## 3. 本番環境セットアップ
- [ ] Ubuntu に self-hosted runner をセットアップ
- [ ] CD ワークフロー作成 (`.github/workflows/deploy.yml`)
- [ ] systemd ユニットファイル作成 (`telegram-diary.service`)

## 4. 取り込み（Ingestion）
- [ ] テスト: `state_store` の保存/読み込み/破損時の挙動
- [ ] 実装: `state_store`
- [ ] テスト: `message_id` による重複排除
- [ ] 実装: dedup
- [ ] テスト: `fetcher` のモックベース契約テスト（正常/エラー/空レスポンス）
- [ ] 実装: 差分取得 (`getUpdates` + offset)
- [ ] 実装: ポーリング間隔設定（デフォルト5分）
- [ ] テスト: 取得 → 正規化 → state 更新の結合テスト
- [ ] リファクタ: 必要に応じて整理
- [ ] レビュー: PR 作成 → セルフレビュー → マージ

## 5. 日次生成（Daily Build）
- [ ] テスト: JST 日付境界の分割ロジック
- [ ] テスト: `journal_writer` の出力順序と冪等性
- [ ] 実装: 日次 Markdown 生成 (`daily/YYYY-MM-DD.md`, JST)
- [ ] 実装: 簡潔要約の生成
- [ ] 実装: 時系列原文の追記
- [ ] 実装: タグの生成
- [ ] テスト: ルールベース `summarizer` / `tagger` のスナップショットテスト
- [ ] リファクタ: 必要に応じて整理
- [ ] レビュー: PR 作成 → セルフレビュー → マージ

## 6. 信頼性（Reliability）
- [ ] テスト: API エラー時のリトライ挙動
- [ ] 実装: リトライ/バックオフ
- [ ] 実装: ログ出力 (`logs/YYYY-MM-DD.log`)
- [ ] 実装: ヘルスチェックコマンド
- [ ] レビュー: PR 作成 → セルフレビュー → マージ

## 7. 運用（Ops）
- [ ] ポーリングジョブのスケジュール設定
- [ ] 日次確定ジョブのスケジュール設定 (cron)
- [ ] 運用手順書の作成
- [ ] レビュー: PR 作成 → セルフレビュー → マージ

## 8. 結合（Integration）
- [ ] テスト: 取得 → 正規化 → 書き出しの E2E テスト
- [ ] リファクタ: 全体通しての最終リファクタ
- [ ] レビュー: PR 作成 → セルフレビュー → マージ

## 9. LLM 連携（任意）
- [ ] feature flag の追加（LLM モード）
- [ ] ルールベースモードをデフォルトに維持
- [ ] プロンプトファイル作成 (`prompts/daily_summary.txt`, `prompts/tags.txt`)
- [ ] pipe 実行の実装（タイムライン → LLM コマンド → 要約/タグ）
- [ ] LLM/API 失敗時のルールベースへのフォールバック
- [ ] LLM 出力フォーマットの検証
- [ ] レビュー: PR 作成 → セルフレビュー → マージ
