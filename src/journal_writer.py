from pathlib import Path

from src.models import Attachment, DailySummary, Message

_MEDIA_LABELS = {
    "photo": "画像",
    "video": "動画",
    "audio": "音声",
    "voice": "音声",
    "document": "ファイル",
}


class JournalWriter:
    def __init__(self, daily_dir: Path = Path("daily")):
        self.daily_dir = daily_dir

    def write(self, summary: DailySummary) -> Path:
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        path = self.daily_dir / f"{summary.date}.md"
        path.write_text(self._render(summary), encoding="utf-8")
        return path

    def _render(self, summary: DailySummary) -> str:
        messages = _dedup_by_id(summary.messages)
        messages = sorted(messages, key=lambda m: m.timestamp)

        lines: list[str] = []

        lines += [f"# {summary.date} 日記", ""]

        lines += ["## 要約", ""]
        for item in summary.summary:
            lines.append(f"- {item}")
        lines.append("")

        lines += ["## タイムライン", ""]
        for msg in messages:
            lines.append(f"- {_format_message(msg)}")
        lines.append("")

        lines += ["## タグ", ""]
        for tag in summary.tags:
            lines.append(f"- {tag}")
        lines.append("")

        return "\n".join(lines)


def _dedup_by_id(messages: list[Message]) -> list[Message]:
    seen: set[int] = set()
    result = []
    for msg in messages:
        if msg.message_id not in seen:
            seen.add(msg.message_id)
            result.append(msg)
    return result


def _format_message(msg: Message) -> str:
    time_str = msg.timestamp.strftime("%H:%M")
    parts = [time_str]
    if msg.text:
        parts.append(msg.text)
    for att in msg.attachments:
        parts.append(_format_attachment(att))
    return " ".join(parts)


def _format_attachment(att: Attachment) -> str:
    label = _MEDIA_LABELS.get(att.media_type, "ファイル")
    return f"[{label}: {att.file_name}]"
