from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.journal_writer import JournalWriter
from src.models import Attachment, DailySummary, Message

JST = ZoneInfo("Asia/Tokyo")


def _msg(message_id: int, hour: int, text: str, attachments=None) -> Message:
    return Message(
        message_id=message_id,
        timestamp=datetime(2026, 2, 21, hour, 0, 0, tzinfo=JST),
        text=text,
        source_chat=-1001234,
        attachments=attachments or [],
    )


def _summary(**kwargs) -> DailySummary:
    defaults = dict(
        date="2026-02-21", messages=[_msg(1, 9, "メモ1")]
    )
    return DailySummary(**{**defaults, **kwargs})


@pytest.fixture
def writer(tmp_path) -> JournalWriter:
    return JournalWriter(daily_dir=tmp_path / "daily")


# --------------------------------------------------------------------------
# ファイル生成
# --------------------------------------------------------------------------


class TestWrite:
    def test_creates_file_at_correct_path(self, writer, tmp_path):
        writer.write(_summary(date="2026-02-21"))
        assert (tmp_path / "daily" / "2026-02-21.md").exists()

    def test_creates_daily_dir_if_missing(self, tmp_path):
        w = JournalWriter(daily_dir=tmp_path / "new" / "daily")
        w.write(_summary())
        assert (tmp_path / "new" / "daily" / "2026-02-21.md").exists()

    def test_returns_path(self, writer, tmp_path):
        path = writer.write(_summary())
        assert path == tmp_path / "daily" / "2026-02-21.md"


# --------------------------------------------------------------------------
# 出力内容
# --------------------------------------------------------------------------


class TestOutputOrder:
    def test_heading_contains_date(self, writer):
        content = writer.write(_summary(date="2026-02-21")).read_text()
        assert "# 2026-02-21 日記" in content

    def test_timeline_section_present(self, writer):
        content = writer.write(_summary()).read_text()
        assert "## タイムライン" in content

    def test_timeline_shows_hhmm(self, writer):
        msgs = [_msg(1, 9, "朝"), _msg(2, 21, "夜")]
        content = writer.write(_summary(messages=msgs)).read_text()
        assert "- 09:00 朝" in content
        assert "- 21:00 夜" in content


# --------------------------------------------------------------------------
# 冪等性
# --------------------------------------------------------------------------


class TestIdempotency:
    def test_same_content_on_repeated_write(self, writer):
        summary = _summary()
        first = writer.write(summary).read_text()
        second = writer.write(summary).read_text()
        assert first == second

    def test_does_not_overwrite_llm_processed_file(self, writer, tmp_path):
        path = writer.write(_summary())
        llm_content = path.read_text() + "\n## Summary\n- LLM generated\n"
        path.write_text(llm_content)
        writer.write(_summary(messages=[_msg(2, 12, "新しいメモ")]))
        assert path.read_text() == llm_content

    def test_duplicate_message_ids_written_once(self, writer):
        msgs = [_msg(1, 9, "original"), _msg(1, 9, "duplicate")]
        content = writer.write(_summary(messages=msgs)).read_text()
        assert content.count("09:00") == 1


# --------------------------------------------------------------------------
# メッセージ順序
# --------------------------------------------------------------------------


class TestMessageOrder:
    def test_messages_sorted_by_timestamp(self, writer):
        msgs = [_msg(2, 15, "午後"), _msg(1, 9, "午前"), _msg(3, 21, "夜")]
        content = writer.write(_summary(messages=msgs)).read_text()
        pos_morning = content.index("09:00")
        pos_afternoon = content.index("15:00")
        pos_night = content.index("21:00")
        assert pos_morning < pos_afternoon < pos_night


# --------------------------------------------------------------------------
# 添付ファイル
# --------------------------------------------------------------------------


class TestAttachments:
    def test_photo_placeholder(self, writer):
        att = Attachment(file_id="abc123", file_name="photo_abc123.jpg", media_type="photo")
        msgs = [_msg(1, 9, "", attachments=[att])]
        content = writer.write(_summary(messages=msgs)).read_text()
        assert "[画像: photo_abc123.jpg]" in content

    def test_text_and_attachment(self, writer):
        att = Attachment(file_id="x", file_name="doc.pdf", media_type="document")
        msgs = [_msg(1, 9, "メモ", attachments=[att])]
        content = writer.write(_summary(messages=msgs)).read_text()
        assert "メモ" in content
        assert "[ファイル: doc.pdf]" in content


# --------------------------------------------------------------------------
# 空ケース
# --------------------------------------------------------------------------


class TestEmptyCases:
    def test_empty_messages(self, writer):
        content = writer.write(_summary(messages=[])).read_text()
        assert "## タイムライン" in content
