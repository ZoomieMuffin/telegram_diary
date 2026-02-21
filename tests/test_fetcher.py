from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.fetcher import FetchError, fetch
from src.normalizer import normalize

# --------------------------------------------------------------------------
# テスト用 fixture
# --------------------------------------------------------------------------

_DATE = 1740139200  # 2026-02-21 12:00:00 UTC = 21:00 JST


def _raw_update(update_id=100, message_id=1, chat_id=-1001234, text="hello", **extra):
    msg = {"message_id": message_id, "chat": {"id": chat_id}, "date": _DATE, "text": text}
    msg.update(extra)
    return {"update_id": update_id, "message": msg}


def _ok_response(updates: list):
    mock = MagicMock()
    mock.json.return_value = {"ok": True, "result": updates}
    mock.raise_for_status.return_value = None
    return mock


# --------------------------------------------------------------------------
# normalizer のユニットテスト
# --------------------------------------------------------------------------


class TestNormalize:
    def test_text_message(self):
        msg = normalize(_raw_update())
        assert msg is not None
        assert msg.message_id == 1
        assert msg.text == "hello"
        assert msg.source_chat == -1001234
        assert msg.attachments == []

    def test_timestamp_is_jst(self):
        from zoneinfo import ZoneInfo

        msg = normalize(_raw_update(date=_DATE))
        assert msg.timestamp.tzinfo == ZoneInfo("Asia/Tokyo")
        assert msg.timestamp.hour == 21  # UTC 12:00 → JST 21:00

    def test_message_without_text(self):
        update = {"update_id": 1, "message": {"message_id": 2, "chat": {"id": -100}, "date": _DATE}}
        msg = normalize(update)
        assert msg.text == ""

    def test_channel_post(self):
        update = {
            "update_id": 1,
            "channel_post": {
                "message_id": 3, "chat": {"id": -1001234}, "date": _DATE, "text": "ch"
            },
        }
        msg = normalize(update)
        assert msg is not None
        assert msg.text == "ch"

    def test_edited_message(self):
        update = {
            "update_id": 1,
            "edited_message": {
                "message_id": 4,
                "chat": {"id": -1001234},
                "date": _DATE,
                "text": "edited",
            },
        }
        msg = normalize(update)
        assert msg is not None
        assert msg.text == "edited"

    def test_unknown_update_returns_none(self):
        assert normalize({"update_id": 1}) is None

    def test_photo_attachment(self):
        update = _raw_update()
        del update["message"]["text"]
        update["message"]["photo"] = [
            {"file_id": "small", "file_unique_id": "u1", "width": 100, "height": 100, "file_size": 1000},  # noqa: E501
            {"file_id": "large", "file_unique_id": "u2", "width": 800, "height": 600, "file_size": 80000},  # noqa: E501
        ]
        msg = normalize(update)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].file_id == "large"
        assert msg.attachments[0].media_type == "photo"

    def test_document_attachment(self):
        update = _raw_update()
        update["message"]["document"] = {"file_id": "doc123", "file_name": "note.pdf"}
        msg = normalize(update)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].file_id == "doc123"
        assert msg.attachments[0].file_name == "note.pdf"
        assert msg.attachments[0].media_type == "document"


# --------------------------------------------------------------------------
# fetcher のモックテスト
# --------------------------------------------------------------------------


class TestFetch:
    def test_returns_messages(self):
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response([_raw_update()])
            msgs = fetch("token", chat_id=-1001234, offset=0)
        assert len(msgs) == 1
        assert msgs[0].message_id == 1

    def test_empty_result(self):
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response([])
            msgs = fetch("token", chat_id=-1001234, offset=0)
        assert msgs == []

    def test_filters_by_chat_id(self):
        updates = [
            _raw_update(update_id=1, message_id=1, chat_id=-1001234, text="mine"),
            _raw_update(update_id=2, message_id=2, chat_id=-9999, text="other"),
        ]
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(updates)
            msgs = fetch("token", chat_id=-1001234, offset=0)
        assert len(msgs) == 1
        assert msgs[0].message_id == 1

    def test_passes_offset_to_api(self):
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response([])
            fetch("token", chat_id=-1001234, offset=42)
        assert mock_get.call_args.kwargs["params"]["offset"] == 42

    def test_raises_fetch_error_on_api_error(self):
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response([])
            mock_get.return_value.json.return_value = {"ok": False, "description": "Unauthorized"}
            with pytest.raises(FetchError):
                fetch("token", chat_id=-1001234, offset=0)

    def test_raises_fetch_error_on_network_error(self):
        with patch("src.fetcher.httpx.get", side_effect=httpx.ConnectError("timeout")):
            with pytest.raises(FetchError):
                fetch("token", chat_id=-1001234, offset=0)

    def test_raises_fetch_error_on_http_status_error(self):
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(FetchError):
                fetch("token", chat_id=-1001234, offset=0)
