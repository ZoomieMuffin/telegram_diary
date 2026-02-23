# telegram_diary

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-orange?logo=anthropic)](https://claude.ai/claude-code)

Telegram に投げたメモを更新ごとに取り込み、Markdown 日記として保存するツール。

## 概要

- Telegram の専用プライベートチャンネルからメッセージを取得
- 日次の Markdown ファイル（`daily/YYYY-MM-DD.md`）として保存
- 思考ログを検索可能・再利用可能な資産にする

## セットアップ

```bash
cp .env.example .env
# .env にトークンを設定
uv sync
```

## 環境変数

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 実行

```bash
# ポーリング開始（5分ごとにメッセージ取得）
uv run python -m src.main

# 日次 Markdown を手動生成
uv run python -m src.main --generate-daily
```

## 本番環境セットアップ（Ubuntu）

### 1. self-hosted runner のインストール

GitHub リポジトリの Settings → Actions → Runners → **New self-hosted runner** から
トークンを取得し、以下を実行する。

```bash
export GITHUB_REPO="ZoomieMuffin/telegram_diary"
export RUNNER_TOKEN="<取得したトークン>"
bash scripts/setup_runner.sh
```

runner が systemd サービス `actions-runner` として登録・起動される。

```bash
# 状態確認
sudo systemctl status actions-runner
journalctl -u actions-runner -f
```

### 2. アプリケーションの初期設定

```bash
# リポジトリをクローン
git clone https://github.com/ZoomieMuffin/telegram_diary.git
cd telegram_diary

# 依存関係をインストール
uv sync

# 環境変数を設定
cp .env.example .env
vi .env  # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID を記入

# サービスユーザー（muffin）が読めるよう所有者を設定してからパーミッションを制限
chown muffin .env
chmod 600 .env
```

### 3. systemd サービスとして常駐

```bash
# ポーリングサービスを配置・起動
sudo cp scripts/telegram-diary.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-diary
sudo systemctl start telegram-diary

# 日次確定タイマーを配置・起動（23:55 JST に自動実行）
sudo cp scripts/telegram-diary-daily.service /etc/systemd/system/
sudo cp scripts/telegram-diary-daily.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-diary-daily.timer
```

## 運用手順

### ログ確認

```bash
# systemd ジャーナル（リアルタイム）
journalctl -u telegram-diary -f

# アプリログ（日付別）
cat logs/YYYY-MM-DD.log
```

### サービス再起動

```bash
sudo systemctl restart telegram-diary
```

### state.json リセット

offset をリセットしたい場合（メッセージを最初から取り直すなど）:

```bash
sudo systemctl stop telegram-diary
rm -f state.json state.json.bak
sudo systemctl start telegram-diary
```

> **注意:** リセット後は Telegram API の保持期間（24時間）内のメッセージのみ取得可能。

### Bot トークン漏洩時の対応

1. BotFather で `/revoke` を実行して旧トークンを無効化
2. 新しいトークンを取得
3. `.env` を更新して `chmod 600 .env`
4. サービスを再起動

```bash
vi .env  # TELEGRAM_BOT_TOKEN を新しいトークンに更新
chmod 600 .env
sudo systemctl restart telegram-diary
```

## 開発

```bash
uv sync
uv run ruff check .
uv run pytest
```

## 開発環境

このプロジェクトは [Claude Code](https://claude.ai/claude-code) を使って開発しています。設計・実装・テスト・CI/CD 構成のすべてに Claude を活用しています。詳細は [CLAUDE.md](CLAUDE.md) を参照してください。

## ディレクトリ構成

```
telegram_diary/
├── src/                  # アプリケーションコード
│   ├── main.py           # エントリポイント（ポーリング・日次生成）
│   ├── fetcher.py        # Telegram API からメッセージ取得
│   ├── normalizer.py     # 生データを Message に変換
│   ├── state_store.py    # 実行状態の永続化
│   ├── journal_writer.py # Markdown 日記の書き出し
│   ├── summarizer.py     # 要約生成（ルールベース）
│   ├── tagger.py         # タグ生成（ルールベース）
│   └── logger.py         # ログ出力
├── scripts/              # systemd ユニットファイル・ツール
├── tests/                # テストコード
├── daily/                # 生成物: YYYY-MM-DD.md（.gitignore）
├── logs/                 # 生成物: YYYY-MM-DD.log（.gitignore）
├── messages/             # 生成物: 日次メッセージキャッシュ（.gitignore）
├── state.json            # 実行状態（.gitignore）
└── .env                  # 機密情報（.gitignore）
```
