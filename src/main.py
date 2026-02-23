import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.fetcher import fetch
from src.journal_writer import JournalWriter
from src.logger import setup_logger
from src.models import Attachment, DailySummary, Message, State
from src.retry import with_retry
from src.state_store import StateStore
from src.summarizer import summarize
from src.tagger import tag

JST = ZoneInfo("Asia/Tokyo")
_DEFAULT_INTERVAL = 300  # 5 minutes


# --------------------------------------------------------------------------
# シリアライズ
# --------------------------------------------------------------------------


def _msg_to_dict(msg: Message) -> dict:
    """Message を JSON シリアライズ可能な dict に変換する。"""
    return {
        "message_id": msg.message_id,
        "timestamp": msg.timestamp.isoformat(),
        "text": msg.text,
        "source_chat": msg.source_chat,
        "attachments": [
            {"file_id": a.file_id, "file_name": a.file_name, "media_type": a.media_type}
            for a in msg.attachments
        ],
    }


def _dict_to_msg(d: dict) -> Message:
    """dict を Message に復元する。"""
    return Message(
        message_id=d["message_id"],
        timestamp=datetime.fromisoformat(d["timestamp"]),
        text=d["text"],
        source_chat=d["source_chat"],
        attachments=[
            Attachment(
                file_id=a["file_id"],
                file_name=a["file_name"],
                media_type=a["media_type"],
            )
            for a in d.get("attachments", [])
        ],
    )


# --------------------------------------------------------------------------
# メッセージ永続化
# --------------------------------------------------------------------------


def _load_day_messages(date_str: str, messages_dir: Path) -> list[Message]:
    """messages_dir/date_str.json からメッセージリストを読み込む。ファイルがなければ空リスト。"""
    path = messages_dir / f"{date_str}.json"
    if not path.exists():
        return []
    return [_dict_to_msg(d) for d in json.loads(path.read_text())]


def _save_day_messages(date_str: str, messages: list[Message], messages_dir: Path) -> None:
    """メッセージリストを messages_dir/date_str.json に保存する。"""
    messages_dir.mkdir(parents=True, exist_ok=True)
    path = messages_dir / f"{date_str}.json"
    path.write_text(
        json.dumps([_msg_to_dict(m) for m in messages], ensure_ascii=False, indent=2)
    )


# --------------------------------------------------------------------------
# マージ
# --------------------------------------------------------------------------


def _merge_messages(existing: list[Message], new: list[Message]) -> list[Message]:
    """既存と新規を message_id でマージし timestamp 順に返す。編集済みメッセージは上書き。"""
    by_id: dict[int, Message] = {m.message_id: m for m in existing}
    for msg in new:
        by_id[msg.message_id] = msg  # 編集済みメッセージは上書き
    return sorted(by_id.values(), key=lambda m: m.timestamp)


# --------------------------------------------------------------------------
# ポーリング
# --------------------------------------------------------------------------


def poll_once(
    bot_token: str,
    chat_id: int,
    store: StateStore,
    writer: JournalWriter,
    messages_dir: Path,
    logger: logging.Logger,
) -> None:
    state = store.load()
    new_messages, next_offset = with_retry(lambda: fetch(bot_token, chat_id, state.last_update_id))

    by_date: dict[str, list[Message]] = {}
    for msg in new_messages:
        d = msg.timestamp.astimezone(JST).date().isoformat()
        by_date.setdefault(d, []).append(msg)

    for date_str, msgs in by_date.items():
        existing = _load_day_messages(date_str, messages_dir)
        merged = _merge_messages(existing, msgs)
        _save_day_messages(date_str, merged, messages_dir)
        daily = DailySummary(
            date=date_str,
            summary=summarize(merged),
            tags=tag(merged),
            messages=merged,
        )
        writer.write(daily)

    if new_messages:
        logger.info(f"Fetched {len(new_messages)} new message(s)")
    else:
        logger.info("No new messages")

    store.save(State(last_update_id=next_offset, last_run_at=datetime.now(JST)))


def poll_loop(
    bot_token: str,
    chat_id: int,
    store: StateStore,
    writer: JournalWriter,
    messages_dir: Path,
    logger: logging.Logger,
    interval: int,
) -> None:
    logger.info(f"Starting polling loop (interval={interval}s)")
    while True:
        try:
            poll_once(bot_token, chat_id, store, writer, messages_dir, logger)
        except Exception as exc:
            logger.exception(f"Poll error: {exc}")
        time.sleep(interval)


# --------------------------------------------------------------------------
# 日次確定
# --------------------------------------------------------------------------


def generate_daily(
    date_str: str,
    writer: JournalWriter,
    messages_dir: Path,
    logger: logging.Logger,
) -> None:
    messages = _load_day_messages(date_str, messages_dir)
    if not messages:
        logger.info(f"No messages for {date_str}")
        return
    daily = DailySummary(
        date=date_str,
        summary=summarize(messages),
        tags=tag(messages),
        messages=messages,
    )
    path = writer.write(daily)
    logger.info(f"Generated {path}")


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------


def _today_jst() -> str:
    return datetime.now(JST).date().isoformat()


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Telegram Diary")
    parser.add_argument(
        "--generate-daily",
        metavar="DATE",
        nargs="?",
        const=_today_jst(),
        help="日次ジャーナルを生成する (YYYY-MM-DD)。省略時は当日。",
    )
    args = parser.parse_args()

    logger = setup_logger(Path("logs"))
    store = StateStore()
    writer = JournalWriter(Path("daily"))
    messages_dir = Path("messages")

    if args.generate_daily is not None:
        generate_daily(args.generate_daily, writer, messages_dir, logger)
    else:
        bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
        chat_id = int(os.environ["TELEGRAM_CHAT_ID"])
        interval = int(os.environ.get("POLL_INTERVAL_SECONDS", str(_DEFAULT_INTERVAL)))
        poll_loop(bot_token, chat_id, store, writer, messages_dir, logger, interval)


if __name__ == "__main__":
    main()
