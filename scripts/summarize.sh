#!/bin/bash
# 前日の日記ファイルをLLMで要約・タグ付けする
# cron例: 5 0 * * * /path/to/scripts/summarize.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_DIR="${REPO_DIR}/daily"
PROMPT_FILE="${REPO_DIR}/prompts/daily_summary.txt"
LLM_CMD="${LLM_CMD:-claude}"

DATE=$(date -d "yesterday" +%Y-%m-%d)
FILE="${DAILY_DIR}/${DATE}.md"

if [[ ! -f "$FILE" ]]; then
    echo "$(date): No file for ${DATE}, skipping." >&2
    exit 0
fi

echo "$(date): Summarizing ${FILE}..." >&2

{ cat "$PROMPT_FILE"; printf '\n\n'; cat "$FILE"; } \
    | "$LLM_CMD" --print \
    > "${FILE}.tmp" \
    && mv "${FILE}.tmp" "$FILE"

echo "$(date): Done." >&2
