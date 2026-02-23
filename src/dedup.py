from src.models import Message


def deduplicate(messages: list[Message], seen_ids: set[int]) -> list[Message]:
    """seen_ids に含まれない message_id のメッセージだけ返す。"""
    return [m for m in messages if m.message_id not in seen_ids]


def dedup_by_id(messages: list[Message]) -> list[Message]:
    """リスト内で message_id が重複するメッセージを排除し、最初の出現を保持する。"""
    seen: set[int] = set()
    result = []
    for msg in messages:
        if msg.message_id not in seen:
            seen.add(msg.message_id)
            result.append(msg)
    return result
