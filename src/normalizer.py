from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import Attachment, Message

_JST = ZoneInfo("Asia/Tokyo")
_MESSAGE_KEYS = ("message", "edited_message", "channel_post", "edited_channel_post")


def normalize(update: dict) -> Message | None:
    """Telegram Update dict を Message に変換する。対応するメッセージがなければ None を返す。"""
    raw = next((update[k] for k in _MESSAGE_KEYS if k in update), None)
    if raw is None:
        return None
    return Message(
        message_id=raw["message_id"],
        timestamp=datetime.fromtimestamp(raw["date"], tz=_JST),
        text=raw.get("text") or raw.get("caption") or "",
        source_chat=raw["chat"]["id"],
        attachments=_extract_attachments(raw),
    )


def _extract_attachments(raw: dict) -> list[Attachment]:
    """生メッセージから添付ファイルリストを抽出する。"""
    result = []

    if "photo" in raw:
        largest = max(raw["photo"], key=lambda p: p.get("file_size", 0))
        result.append(Attachment(
            file_id=largest["file_id"],
            file_name=f"photo_{largest['file_id']}.jpg",
            media_type="photo",
        ))

    for media_type in ("video", "document", "audio", "voice"):
        if media_type in raw:
            obj = raw[media_type]
            result.append(Attachment(
                file_id=obj["file_id"],
                file_name=obj.get("file_name", f"{media_type}_{obj['file_id']}"),
                media_type=media_type,
            ))

    return result
