# telegram_diary 仕様メモ

## 1. 目的
- Telegram に投げたメモを更新ごとに取り込み、Markdown 日記として保存する。
- 思考ログを検索可能・再利用可能な資産にする。

## 2. スコープ
- 対象: 自分専用の Telegram 専用チャンネル（private）
- 出力: 日次の `.md` ファイル
- 非対象: 公開配信、チーム向け通知、リアルタイム要約

## 3. MVP 要件
- Telegram から新着メッセージを継続取得できる
- 取得したメッセージを時系列で並べる
- 1日1ファイルで保存する（例: `YYYY-MM-DD.md`）
- 再実行時に同じメッセージを重複保存しない
- 実行ログを残す（成功/失敗、取得件数）
- 出力順を `簡潔要約 -> 時系列原文 -> タグ` に固定する

## 4. 出力フォーマット
```md
# 2026-02-15 日記

## 要約
- 要約1
- 要約2

## タイムライン
- 09:12 メモ1
- 11:45 メモ2

## タグ
- #idea
- #task
```

## 5. ディレクトリ構成
```
telegram_diary/
├── src/                  # アプリケーションコード
│   ├── __init__.py
│   ├── fetcher.py
│   ├── normalizer.py
│   ├── state_store.py
│   ├── journal_writer.py
│   ├── summarizer.py
│   ├── tagger.py
│   └── logger.py
├── tests/                # テストコード
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_normalizer.py
│   ├── test_state_store.py
│   ├── test_journal_writer.py
│   ├── test_summarizer.py
│   └── test_tagger.py
├── prompts/              # LLM プロンプト（任意）
├── daily/                # 生成物: YYYY-MM-DD.md
├── logs/                 # 生成物: YYYY-MM-DD.log
├── state.json            # 生成物: 実行状態
├── .env                  # 機密: トークン等
├── .gitignore
├── pyproject.toml
└── README.md
```

### .gitignore 対象
- `.env` — 機密情報
- `state.json` / `state.json.bak` — 実行状態（ローカル固有）
- `daily/` — 生成物
- `logs/` — 生成物
- `__pycache__/` / `.pytest_cache/` — Python 生成物

### 保存先ルール
- 日次: `daily/YYYY-MM-DD.md`
- 状態管理: `state.json`（最終取得IDなど）
- ログ: `logs/YYYY-MM-DD.log`

## 6. 同期・実行方針
- 取り込み方式: 短間隔ポーリング（軽量運用を優先）
- 取り込み頻度: 5分ごと（設定で調整可能）
- 日次生成頻度: 1日1回（手動 or cron）
- 取得方式: Telegram Bot API（`getUpdates` / offset管理）
- 制約: `getUpdates` は未取得分を24時間しか保持しない。24時間以内に1回は実行すること
- 冪等性: `message_id` ベースで重複防止
- 編集メッセージ: `edited_message` を検知し、同一 `message_id` のテキストを最新版に上書き
- 日付境界: JST 固定
- チャンネル要件: Bot を専用チャンネルへ追加し、メッセージ閲覧可能な権限を付与

## 7. 非機能要件
- セキュリティ:
  - トークンをファイル直書きしない（環境変数 / `.env`）
  - Bot はチャンネルに一般メンバーとして追加（管理者権限は付与しない）
  - トークン漏洩時: BotFather で `/revoke` → 新トークンを `.env` に差し替え
- 可観測性: 失敗時に原因が追えるログ
- 可搬性: Mac / Linux 両方で動作

## 8. CI/CD

### 8.1 CI（PR 時: `.github/workflows/ci.yml`）
- トリガー: PR 作成 / 更新時
- ステップ:
  1. `actions/checkout`
  2. Python + uv セットアップ
  3. `uv sync`
  4. `ruff check .`（lint）
  5. `pytest`（テスト）
- ブランチ保護: CI パスしないとマージ不可

### 8.2 コードレビュー
- GitHub Copilot code review（リポジトリ設定で有効化）
- PR 作成時に自動でレビューコメントが付く
- Copilot Pro プラン（月500回）で運用

### 8.3 CD（main マージ後: `.github/workflows/deploy.yml`）
- 実行環境: Ubuntu サーバー上の self-hosted runner（ポート開放不要）
- トリガー: main ブランチへの push
- ステップ:
  1. `actions/checkout`（runner 上でリポジトリ更新）
  2. `uv sync`
  3. `sudo systemctl restart telegram-diary`

### 8.4 本番構成（Ubuntu）
- プロセス管理: systemd (`telegram-diary.service`)
- 環境変数: `.env` をサーバー上に直接配置（リポジトリには含めない）
- ログ: `journalctl -u telegram-diary` + アプリ独自ログ (`logs/`)
- self-hosted runner: `actions-runner` を systemd で常駐

### 8.5 PR → デプロイの流れ
```
feature ブランチで開発
  → PR 作成
  → CI（lint + テスト）自動実行
  → Copilot code review 自動実行
  → セルフレビュー
  → main にマージ
  → CD: self-hosted runner がデプロイ実行
```

## 9. 未決事項
- タグ語彙の管理方法（固定リストか自由入力か）

## 10. 次アクション
- Bot を作成しトークンを発行
- 専用チャンネルを作成し、対象 `chat_id` を確定
- 最小実装（取得 → md 保存）を1本作る
- 1週間運用して不足要件を洗い出す
- LLM 非使用モード（ルールベース）で先行運用し、必要なら LLM モードを追加する

## 11. コンポーネント

### 11.0 共通型定義（Python / JST 固定）
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Attachment:
    file_id: str             # Telegram file_id（ダウンロード用）
    file_name: str           # ファイル名（例: "photo_123.jpg"）
    media_type: str          # "photo" | "video" | "document" | "audio" | "voice"

@dataclass
class Message:
    message_id: int          # Telegram message_id（重複排除キー）
    timestamp: datetime      # JST (tzinfo=ZoneInfo("Asia/Tokyo"))
    text: str                # メッセージ本文（メディアのみの場合は空文字列）
    source_chat: int         # chat_id
    attachments: list[Attachment]  # メディア添付（なければ空リスト）

@dataclass
class State:
    last_update_id: int      # 次回 getUpdates の offset (last + 1)
    last_run_at: datetime    # JST 最終実行日時

@dataclass
class DailySummary:
    date: str                # "YYYY-MM-DD"
    summary: list[str]       # 要約の箇条書き
    tags: list[str]          # "#idea", "#task" など
    messages: list[Message]  # 時系列順
```

### 11.1 fetcher（取得）
- 責務: Bot API を使って Telegram の新着メッセージを取得する。
- 入力: `bot_token: str`, `chat_id: int`, `offset: int`
- 出力: `list[Message]`
- エラー: `FetchError`（ネットワーク/API エラー）

### 11.2 normalizer（正規化）
- 責務: Telegram API の生データを `Message` に変換する。
- 入力: `dict`（Telegram Update オブジェクト）
- 出力: `Message`
- メディア処理:
  - `file_id`, ファイル名, `media_type` を `Attachment` として保持
  - テキストがない場合は `text=""`
  - MVP: 日記には `[画像: photo_123.jpg]` 等のプレースホルダを出力
  - 将来: `img/YYYY-MM-DD/` にダウンロード + `![](img/...)` リンクに差し替え

### 11.3 state_store（状態管理）
- 責務: `State` の永続化と読み込み。
- ファイル: `state.json` / `state.json.bak`
- 入出力: `State`
- `save(state: State) -> None` — 書き込み前に既存を `.bak` へコピー
- `load() -> State` — `state.json` が破損時は `.bak` から復元。両方ダメならデフォルト値
- 排他制御: なし（ポーリングのみが state を更新する設計で競合しない）

### 11.4 journal_writer（日記書き出し）
- 責務: 日次 Markdown ファイルの書き出し。
- 入力: `DailySummary`
- 出力: `daily/YYYY-MM-DD.md` へ書き込み
- 動作: `message_id` ベースで冪等。再実行しても重複しない。

### 11.5 summarizer（要約）
- 責務: 日次要約の生成。
- 入力: `list[Message]`
- 出力: `list[str]`（箇条書き）
- 備考: デフォルトはルールベース。LLM 連携は任意。

### 11.6 tagger（タグ付け）
- 責務: 日次タグの生成。
- 入力: `list[Message]`
- 出力: `list[str]`（タグリスト）
- 備考: デフォルトはルールベース。LLM 連携は任意。

### 11.7 logger（ログ）
- 責務: 実行ログとエラーの記録。
- パス: `logs/YYYY-MM-DD.log`
- レベル: `INFO` / `ERROR`

## 12. LLM API 要否
- 必須ではない。MVP はルールベースで完結可能。
- 要約品質やタグ精度を上げたい場合のみ、任意で LLM API を有効化する。

### 12.1 LLM 実行方式（任意）
- 実行方式: タイムラインを標準入力で LLM コマンドへ渡す（pipe 方式）。
- プロンプト管理: プロンプト文は `prompts/daily_summary.txt` など外部ファイルで管理し、コード直書きしない。
- 失敗時挙動: API 失敗や出力形式不正時は、ルールベース要約へフォールバックする。
- 出力検証: 行数と見出し形式を検証してから要約セクションへ反映する。

```bash
cat /tmp/timeline.txt \
  | llm summarize --prompt-file prompts/daily_summary.txt \
  > /tmp/summary.txt
```

## 13. テスト方針（TDD）
- 基本方針: コアコンポーネントは TDD（Red → Green → Refactor）で実装する。
- 優先して TDD する対象:
  - `state_store`: `last_update_id` の保存/復元、破損データ時の挙動
  - `dedup` ロジック: `message_id` 重複除去の保証
  - 日次分割: JST 境界で `YYYY-MM-DD.md` に正しく振り分ける
  - `journal_writer`: 出力順（要約 → 時系列 → タグ）と冪等更新
- `fetcher` は外部 API 依存のため、モック中心の契約テストを行う。
- `summarizer` / `tagger` はルールベースの期待出力をスナップショットで確認する。
- 結合テストとして「取得 → 整形 → 出力」までを固定 fixture で1本通す。
