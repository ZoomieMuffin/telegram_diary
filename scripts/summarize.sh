#!/bin/bash
# 前日の日記ファイルをLLMで要約・タグ付けする
# cron例: 5 0 * * * /path/to/scripts/summarize.sh
#
# LLM_CMD: LLMコマンドをフルで指定（デフォルト: claude --print）
#   例: LLM_CMD="claude --print" または LLM_CMD="gemini"
#   コマンドはstdinを受け取りstdoutに出力すること

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_DIR="${REPO_DIR}/daily"
PROMPT_FILE="${REPO_DIR}/prompts/daily_summary.txt"
LLM_CMD="${LLM_CMD:-claude --print}"

DATE=$(date -d "yesterday" +%Y-%m-%d)
FILE="${DAILY_DIR}/${DATE}.md"
DONE_MARKER="${FILE}.done"

if [[ ! -f "$FILE" ]]; then
    echo "$(date): No file for ${DATE}, skipping." >&2
    exit 0
fi

if [[ -f "$DONE_MARKER" ]]; then
    echo "$(date): ${DATE} already processed, skipping." >&2
    exit 0
fi

echo "$(date): Summarizing ${FILE}..." >&2

{ cat "$PROMPT_FILE"; printf '\n\n'; cat "$FILE"; } \
    | bash -c "$LLM_CMD" \
    > "${FILE}.tmp" \
    && mv "${FILE}.tmp" "$FILE" \
    && touch "$DONE_MARKER"

echo "$(date): Done." >&2
