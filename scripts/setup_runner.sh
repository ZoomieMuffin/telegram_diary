#!/bin/bash
# GitHub Actions Self-Hosted Runner セットアップスクリプト
# Ubuntu 向け。ポート開放不要（runner からGitHub へのアウトバウンド接続のみ）。
#
# 使い方:
#   export GITHUB_REPO="ZoomieMuffin/telegram_diary"
#   export RUNNER_TOKEN="<GitHub から取得したトークン>"
#   bash scripts/setup_runner.sh
#
# RUNNER_TOKEN の取得方法:
#   GitHub リポジトリ → Settings → Actions → Runners → New self-hosted runner
#   表示された "Configure" セクションの --token の値を使う（60分で失効）

set -euo pipefail

# ---- 設定 ----------------------------------------------------------------
RUNNER_VERSION="${RUNNER_VERSION:-2.322.0}"
RUNNER_DIR="${RUNNER_DIR:-${HOME}/actions-runner}"
GITHUB_REPO="${GITHUB_REPO:?GITHUB_REPO を設定してください (例: ZoomieMuffin/telegram_diary)}"
RUNNER_TOKEN="${RUNNER_TOKEN:?RUNNER_TOKEN を設定してください}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,Linux,X64}"
SERVICE_NAME="actions-runner"
# --------------------------------------------------------------------------

RUNNER_ARCHIVE="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_ARCHIVE}"

echo "==> actions-runner v${RUNNER_VERSION} を ${RUNNER_DIR} にセットアップします"

# 1. ダウンロード & 展開
mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

if [[ ! -f "${RUNNER_ARCHIVE}" ]]; then
  echo "==> runner をダウンロード中..."
  curl -fsSL -o "${RUNNER_ARCHIVE}" "${RUNNER_URL}"
fi

echo "==> 展開中..."
tar -xzf "${RUNNER_ARCHIVE}"
rm -f "${RUNNER_ARCHIVE}"

# 2. 依存ライブラリのインストール（初回のみ）
if [[ -f bin/installdependencies.sh ]]; then
  echo "==> 依存ライブラリをインストール中..."
  sudo bash bin/installdependencies.sh
fi

# 3. runner の設定
echo "==> runner を設定中..."
./config.sh \
  --url "https://github.com/${GITHUB_REPO}" \
  --token "${RUNNER_TOKEN}" \
  --name "${RUNNER_NAME}" \
  --labels "${RUNNER_LABELS}" \
  --unattended \
  --replace

# 4. systemd サービスファイルを配置
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
echo "==> systemd サービスを設定中..."
sudo tee "${SERVICE_FILE}" > /dev/null << EOF
[Unit]
Description=GitHub Actions Self-Hosted Runner (${GITHUB_REPO})
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${RUNNER_DIR}
ExecStart=${RUNNER_DIR}/bin/runsvc.sh
Restart=on-failure
RestartSec=10
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min
Environment=RUNNER_ALLOW_RUNASROOT=0

[Install]
WantedBy=multi-user.target
EOF

# 5. サービスを有効化・起動
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo ""
echo "==> セットアップ完了！"
echo ""
echo "確認コマンド:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
