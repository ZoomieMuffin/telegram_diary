from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from src.main import (
    _dict_to_msg,
    _load_day_messages,
    _merge_messages,
    _msg_to_dict,
    _save_day_messages,
    generate_daily,
    poll_once,
)
from src.models import Message, State

JST = ZoneInfo("Asia/Tokyo")
_DT = datetime(2026, 2, 22, 12, 0, tzinfo=JST)


def _msg(message_id=1, text="hello", dt=_DT, chat_id=-1001234):
    return Message(
        message_id=message_id,
        timestamp=dt,
        text=text,
        source_chat=chat_id,
        attachments=[],
    )


def _make_store(offset=0):
    store = MagicMock()
    store.load.return_value = State(last_update_id=offset, last_run_at=_DT)
    return store


# --------------------------------------------------------------------------
# シリアライズ
# --------------------------------------------------------------------------


class TestMsgSerialization:
    def test_roundtrip(self):
        msg = _msg()
        assert _dict_to_msg(_msg_to_dict(msg)) == msg

    def test_timestamp_preserves_timezone(self):
        msg = _msg()
        restored = _dict_to_msg(_msg_to_dict(msg))
        assert restored.timestamp == msg.timestamp


# --------------------------------------------------------------------------
# メッセージ永続化
# --------------------------------------------------------------------------


class TestDayMessages:
    def test_load_returns_empty_when_no_file(self, tmp_path):
        assert _load_day_messages("2026-02-22", tmp_path) == []

    def test_save_and_load_roundtrip(self, tmp_path):
        msgs = [_msg(1), _msg(2, text="world")]
        _save_day_messages("2026-02-22", msgs, tmp_path)
        loaded = _load_day_messages("2026-02-22", tmp_path)
        assert len(loaded) == 2
        assert loaded[0].message_id == 1
        assert loaded[1].message_id == 2

    def test_save_creates_directory(self, tmp_path):
        messages_dir = tmp_path / "messages"
        _save_day_messages("2026-02-22", [_msg()], messages_dir)
        assert messages_dir.exists()


# --------------------------------------------------------------------------
# マージ
# --------------------------------------------------------------------------


class TestMergeMessages:
    def test_dedup_by_message_id_keeps_last(self):
        merged = _merge_messages([], [_msg(1, "first"), _msg(1, "edited")])
        assert len(merged) == 1
        assert merged[0].text == "edited"

    def test_new_overwrites_existing(self):
        merged = _merge_messages([_msg(1, "old")], [_msg(1, "new")])
        assert len(merged) == 1
        assert merged[0].text == "new"

    def test_sorted_by_timestamp(self):
        dt1 = datetime(2026, 2, 22, 10, 0, tzinfo=JST)
        dt2 = datetime(2026, 2, 22, 12, 0, tzinfo=JST)
        merged = _merge_messages([_msg(2, dt=dt2)], [_msg(1, dt=dt1)])
        assert [m.message_id for m in merged] == [1, 2]

    def test_combines_existing_and_new(self):
        merged = _merge_messages([_msg(1)], [_msg(2)])
        assert len(merged) == 2


# --------------------------------------------------------------------------
# poll_once
# --------------------------------------------------------------------------


class TestPollOnce:
    def test_fetches_and_writes_journal(self, tmp_path):
        store = _make_store(offset=100)
        writer = MagicMock()
        logger = MagicMock()

        with patch("src.main.fetch", return_value=([_msg()], 101)):
            poll_once("token", -1001234, store, writer, tmp_path, logger)

        writer.write.assert_called_once()
        store.save.assert_called_once()

    def test_empty_fetch_saves_state_without_writing_journal(self, tmp_path):
        store = _make_store(offset=100)
        writer = MagicMock()
        logger = MagicMock()

        with patch("src.main.fetch", return_value=([], 100)):
            poll_once("token", -1001234, store, writer, tmp_path, logger)

        writer.write.assert_not_called()
        store.save.assert_called_once()

    def test_merges_with_existing_messages(self, tmp_path):
        _save_day_messages("2026-02-22", [_msg(1, "old")], tmp_path)
        store = _make_store()
        writer = MagicMock()
        logger = MagicMock()

        with patch("src.main.fetch", return_value=([_msg(2, "new")], 101)):
            poll_once("token", -1001234, store, writer, tmp_path, logger)

        written = writer.write.call_args[0][0]
        assert len(written.messages) == 2

    def test_saves_next_offset(self, tmp_path):
        store = _make_store(offset=100)
        writer = MagicMock()
        logger = MagicMock()

        with patch("src.main.fetch", return_value=([_msg()], 200)):
            poll_once("token", -1001234, store, writer, tmp_path, logger)

        saved_state = store.save.call_args[0][0]
        assert saved_state.last_update_id == 200

    def test_persists_messages_to_disk(self, tmp_path):
        store = _make_store()
        writer = MagicMock()
        logger = MagicMock()

        with patch("src.main.fetch", return_value=([_msg(42)], 101)):
            poll_once("token", -1001234, store, writer, tmp_path, logger)

        saved = _load_day_messages("2026-02-22", tmp_path)
        assert len(saved) == 1
        assert saved[0].message_id == 42


# --------------------------------------------------------------------------
# generate_daily
# --------------------------------------------------------------------------


class TestGenerateDaily:
    def test_writes_journal_when_messages_exist(self, tmp_path):
        _save_day_messages("2026-02-22", [_msg()], tmp_path)
        writer = MagicMock()
        logger = MagicMock()

        generate_daily("2026-02-22", writer, tmp_path, logger)

        writer.write.assert_called_once()

    def test_skips_write_when_no_messages(self, tmp_path):
        writer = MagicMock()
        logger = MagicMock()

        generate_daily("2026-02-22", writer, tmp_path, logger)

        writer.write.assert_not_called()

    def test_daily_summary_has_correct_date(self, tmp_path):
        _save_day_messages("2026-02-22", [_msg()], tmp_path)
        writer = MagicMock()
        logger = MagicMock()

        generate_daily("2026-02-22", writer, tmp_path, logger)

        written = writer.write.call_args[0][0]
        assert written.date == "2026-02-22"
