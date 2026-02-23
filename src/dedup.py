from src.models import Message


def deduplicate(messages: list[Message], seen_ids: set[int]) -> list[Message]:
    """seen_ids に含まれない message_id のメッセージだけ返す。"""
    return [m for m in messages if m.message_id not in seen_ids]


def dedup_by_id(messages: list[Message]) -> list[Message]:
    """リスト内で message_id が重複するメッセージを排除し、最後の出現（最新版）を保持する。

    _merge_messages の上書き方針と一致させるため、同一 ID が複数ある場合は
    最後に出現したもの（編集済みの最新版）を採用する。
    """
    by_id: dict[int, Message] = {}
    for msg in messages:
        by_id[msg.message_id] = msg
    return list(by_id.values())
