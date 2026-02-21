from src.models import Message

_MAX_CHARS = 50


def summarize(messages: list[Message]) -> list[str]:
    """メッセージリストからルールベースの要約（箇条書き）を生成する。"""
    result = []
    for msg in messages:
        text = msg.text.strip()
        if text:
            if len(text) > _MAX_CHARS:
                text = text[:_MAX_CHARS] + "..."
            result.append(text)
        elif msg.attachments:
            result.append(f"[添付: {msg.attachments[0].media_type}]")
    return result
