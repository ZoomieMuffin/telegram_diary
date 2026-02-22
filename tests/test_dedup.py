from datetime import datetime
from zoneinfo import ZoneInfo

from src.dedup import deduplicate
from src.models import Message

JST = ZoneInfo("Asia/Tokyo")


def _msg(message_id: int) -> Message:
    return Message(
        message_id=message_id,
        timestamp=datetime(2026, 2, 21, 12, 0, 0, tzinfo=JST),
        text=f"msg {message_id}",
        source_chat=100,
    )


class TestDeduplicate:
    def test_empty_messages(self):
        assert deduplicate([], seen_ids=set()) == []

    def test_no_duplicates(self):
        msgs = [_msg(1), _msg(2), _msg(3)]
        assert deduplicate(msgs, seen_ids=set()) == msgs

    def test_all_duplicates(self):
        msgs = [_msg(1), _msg(2)]
        assert deduplicate(msgs, seen_ids={1, 2}) == []

    def test_mixed(self):
        msgs = [_msg(1), _msg(2), _msg(3)]
        result = deduplicate(msgs, seen_ids={1, 3})
        assert [m.message_id for m in result] == [2]

    def test_preserves_order(self):
        msgs = [_msg(5), _msg(3), _msg(7)]
        result = deduplicate(msgs, seen_ids=set())
        assert [m.message_id for m in result] == [5, 3, 7]

    def test_empty_seen_ids_returns_all(self):
        msgs = [_msg(10), _msg(20)]
        assert deduplicate(msgs, seen_ids=set()) == msgs
