#!/bin/bash
# 前日の日記ファイルをLLMで要約・タグ付けする
# cron例: 5 0 * * * /path/to/scripts/summarize.sh
#
# LLM_CMD: LLMコマンドをフルで指定（デフォルト: claude --print）
#   例: LLM_CMD="claude --print" または LLM_CMD="gemini"
#   コマンドはstdinを受け取りstdoutに出力すること
#   注意: LLM_CMDには信頼できる値のみ設定すること（外部入力を渡さないこと）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_DIR="${REPO_DIR}/daily"
PROMPT_FILE="${REPO_DIR}/prompts/daily_summary.txt"
LLM_CMD="${LLM_CMD:-claude --print}"

# JST固定で前日の日付を取得（GNU/BSD両対応）
DATE=$(TZ=Asia/Tokyo python3 -c "from datetime import date, timedelta; print(date.today() - timedelta(days=1))")
FILE="${DAILY_DIR}/${DATE}.md"
DONE_MARKER="${FILE}.done"

# LLM失敗時に一時ファイルを確実に削除
trap 'rm -f "${FILE}.tmp"' EXIT

if [[ ! -f "$FILE" ]]; then
    echo "$(date): No file for ${DATE}, skipping." >&2
    exit 0
fi

if [[ -f "$DONE_MARKER" ]]; then
    echo "$(date): ${DATE} already processed, skipping." >&2
    exit 0
fi

echo "$(date): Summarizing ${FILE}..." >&2

# LLM_CMDを配列に分割して実行（bash -c によるインジェクションを回避）
read -ra LLM_ARRAY <<< "$LLM_CMD"

NOTES_DIR="${NOTES_DIR:-/home/muffin/dev/notes/200_Personal/Diary}"

{ cat "$PROMPT_FILE"; printf '\n\n'; cat "$FILE"; } \
    | "${LLM_ARRAY[@]}" \
    > "${FILE}.tmp" \
    && mv "${FILE}.tmp" "$FILE" \
    && touch "$DONE_MARKER"

cp -f "$FILE" "$NOTES_DIR/"
echo "$(date): Done. Copied to ${NOTES_DIR}." >&2
