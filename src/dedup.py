from src.models import Message


def deduplicate(messages: list[Message], seen_ids: set[int]) -> list[Message]:
    """seen_ids に含まれない message_id のメッセージだけ返す。"""
    return [m for m in messages if m.message_id not in seen_ids]


def dedup_by_id(messages: list[Message]) -> list[Message]:
    """リスト内で message_id が重複するメッセージを排除し、最後の出現（最新版）を保持する。

    _merge_messages の上書き方針と一致させるため、同一 ID が複数ある場合は
    最後に出現したもの（編集済みの最新版）を採用する。
    逆順イテレーションにより、値・位置ともに最後の出現を正しく反映する。
    """
    seen: set[int] = set()
    result = []
    for msg in reversed(messages):
        if msg.message_id not in seen:
            seen.add(msg.message_id)
            result.append(msg)
    result.reverse()
    return result
