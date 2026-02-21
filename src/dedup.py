from src.models import Message


def deduplicate(messages: list[Message], seen_ids: set[int]) -> list[Message]:
    """seen_ids に含まれない message_id のメッセージだけ返す。"""
    return [m for m in messages if m.message_id not in seen_ids]
