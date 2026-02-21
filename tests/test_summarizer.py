from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import Attachment, Message
from src.summarizer import summarize

JST = ZoneInfo("Asia/Tokyo")
_DT = datetime(2026, 2, 21, 9, 0, 0, tzinfo=JST)


def _msg(text: str, message_id: int = 1, attachments=None) -> Message:
    return Message(
        message_id=message_id,
        timestamp=_DT,
        text=text,
        source_chat=-100,
        attachments=attachments or [],
    )


# --------------------------------------------------------------------------
# 基本動作
# --------------------------------------------------------------------------


class TestSummarize:
    def test_empty_messages(self):
        assert summarize([]) == []

    def test_single_short_message(self):
        assert summarize([_msg("アイデアを思いついた")]) == ["アイデアを思いついた"]

    def test_long_message_truncated(self):
        long = "あ" * 60
        result = summarize([_msg(long)])
        assert len(result) == 1
        assert result[0].endswith("...")
        assert len(result[0]) <= 53  # 50 chars + "..."

    def test_multiple_messages(self):
        msgs = [_msg("メモA", 1), _msg("メモB", 2), _msg("メモC", 3)]
        assert summarize(msgs) == ["メモA", "メモB", "メモC"]

    def test_attachment_only_message(self):
        att = Attachment(file_id="x", file_name="photo_x.jpg", media_type="photo")
        result = summarize([_msg("", attachments=[att])])
        assert result == ["[添付: photo]"]

    def test_empty_text_no_attachment_skipped(self):
        assert summarize([_msg("")]) == []

    def test_text_with_attachment(self):
        att = Attachment(file_id="x", file_name="photo_x.jpg", media_type="photo")
        result = summarize([_msg("写真撮った", attachments=[att])])
        assert result == ["写真撮った"]

    def test_strips_whitespace(self):
        assert summarize([_msg("  メモ  ")]) == ["メモ"]


# --------------------------------------------------------------------------
# スナップショット
# --------------------------------------------------------------------------


class TestSummarizeSnapshot:
    # 51文字（>50）なので切り詰められる
    _LONG = (
        "今日の買い物リスト：牛乳、卵、パン、バター、チーズ、ヨーグルト、りんご、バナナ、みかん、ぶどう、いちご"
    )

    def test_snapshot(self):
        msgs = [
            _msg("今日はアイデアを思いついた", 1),
            _msg("タスクを整理した", 2),
            _msg("", 3),  # empty → skipped
            _msg(self._LONG, 4),
        ]
        expected = [
            "今日はアイデアを思いついた",
            "タスクを整理した",
            self._LONG[:50] + "...",
        ]
        assert summarize(msgs) == expected
