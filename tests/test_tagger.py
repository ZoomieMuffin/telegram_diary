from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import Message
from src.tagger import tag

JST = ZoneInfo("Asia/Tokyo")
_DT = datetime(2026, 2, 21, 9, 0, 0, tzinfo=JST)


def _msg(text: str, message_id: int = 1) -> Message:
    return Message(message_id=message_id, timestamp=_DT, text=text, source_chat=-100)


# --------------------------------------------------------------------------
# 基本動作
# --------------------------------------------------------------------------


class TestTag:
    def test_empty_messages(self):
        assert tag([]) == []

    def test_no_matching_keywords(self):
        assert tag([_msg("今日は晴れ")]) == []

    def test_idea_keyword(self):
        assert "#idea" in tag([_msg("面白いアイデアを思いついた")])

    def test_task_keyword(self):
        assert "#task" in tag([_msg("タスクを整理する")])

    def test_question_keyword(self):
        assert "#question" in tag([_msg("これはどうすればいいかな？")])

    def test_memo_keyword(self):
        assert "#memo" in tag([_msg("メモしておく")])

    def test_english_keywords_case_insensitive(self):
        assert "#idea" in tag([_msg("new idea for the project")])
        assert "#task" in tag([_msg("TODO: fix the bug")])

    def test_multiple_tags_from_multiple_messages(self):
        msgs = [_msg("アイデア", 1), _msg("タスクをやる", 2)]
        result = tag(msgs)
        assert "#idea" in result
        assert "#task" in result

    def test_multiple_tags_sorted(self):
        msgs = [_msg("タスクのアイデアをメモする")]
        result = tag(msgs)
        assert result == sorted(result)

    def test_no_duplicates(self):
        msgs = [_msg("アイデア", 1), _msg("別のアイデア", 2)]
        result = tag(msgs)
        assert result.count("#idea") == 1


# --------------------------------------------------------------------------
# スナップショット
# --------------------------------------------------------------------------


class TestTagSnapshot:
    def test_snapshot(self):
        msgs = [
            _msg("新しいアイデアを思いついた", 1),
            _msg("TODO: ドキュメントを書く", 2),
            _msg("これどうすればいいかな？", 3),
            _msg("今日は天気がいい", 4),
        ]
        result = tag(msgs)
        assert result == ["#idea", "#question", "#task"]
