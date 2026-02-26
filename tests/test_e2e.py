"""
E2E テスト（PRV-34）

固定 fixture を使って「取得 → 正規化 → 書き出し」を1本通す結合テスト。
httpx.get のみをモックし、それ以外は実コンポーネントを使用する。
"""
import logging
from unittest.mock import MagicMock, patch

import pytest

from src.journal_writer import JournalWriter
from src.logger import setup_logger
from src.main import _load_day_messages, poll_once
from src.state_store import StateStore


@pytest.fixture(autouse=True)
def clean_handlers():
    yield
    logger = logging.getLogger("telegram_diary")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def _get_section(content: str, heading: str) -> str:
    """Markdown から指定見出しのセクション本文のみを抽出する。"""
    lines = content.splitlines()
    result: list[str] = []
    in_section = False
    for line in lines:
        if line == f"## {heading}":
            in_section = True
        elif in_section and line.startswith("## "):
            break
        elif in_section:
            result.append(line)
    if not in_section:
        raise ValueError(f"セクション '{heading}' が見つかりません")
    return "\n".join(result)

# --------------------------------------------------------------------------
# 固定 fixture
# 2026-02-21 21:00〜23:00 JST (UTC 12:00〜14:00)
# --------------------------------------------------------------------------

_T0 = 1771675200  # 2026-02-21 12:00:00 UTC = 21:00 JST
_CHAT_ID = -1001234

_FIXTURE_UPDATES = [
    {
        "update_id": 100,
        "message": {
            "message_id": 1,
            "chat": {"id": _CHAT_ID},
            "date": _T0,
            "text": "今日のアイデア：新しいプロジェクトを始める",
        },
    },
    {
        "update_id": 101,
        "message": {
            "message_id": 2,
            "chat": {"id": _CHAT_ID},
            "date": _T0 + 3600,  # 22:00 JST
            "text": "#task 明日のミーティングの準備",
        },
    },
    {
        "update_id": 102,
        "message": {
            "message_id": 3,
            "chat": {"id": _CHAT_ID},
            "date": _T0 + 7200,  # 23:00 JST
            "text": "#idea 自動化スクリプトのアイデア",
        },
    },
]


def _ok_response(updates: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"ok": True, "result": updates}
    mock.raise_for_status.return_value = None
    return mock


# --------------------------------------------------------------------------
# E2E テスト
# --------------------------------------------------------------------------


class TestE2EPipeline:
    def test_full_pipeline_creates_daily_file(self, tmp_path):
        """fetch → normalize → journal_writer まで通して daily/*.md が生成される。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        daily_file = tmp_path / "daily" / "2026-02-21.md"
        assert daily_file.exists(), "daily/2026-02-21.md が生成されていない"

    def test_daily_file_contains_required_sections(self, tmp_path):
        """生成された Markdown にタイムラインセクションが含まれる。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        content = (tmp_path / "daily" / "2026-02-21.md").read_text(encoding="utf-8")
        assert "## タイムライン" in content

    def test_timeline_messages_in_chronological_order(self, tmp_path):
        """タイムラインが時系列順（21:00 → 22:00 → 23:00）になっている。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        content = (tmp_path / "daily" / "2026-02-21.md").read_text(encoding="utf-8")
        timeline = _get_section(content, "タイムライン")
        pos_21 = timeline.index("21:00")
        pos_22 = timeline.index("22:00")
        pos_23 = timeline.index("23:00")
        assert pos_21 < pos_22 < pos_23

    def test_timeline_contains_original_message_text(self, tmp_path):
        """タイムラインに元のメッセージテキストが保持されている。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        content = (tmp_path / "daily" / "2026-02-21.md").read_text(encoding="utf-8")
        timeline = _get_section(content, "タイムライン")
        assert "新しいプロジェクトを始める" in timeline
        assert "ミーティングの準備" in timeline

    def test_state_updated_with_next_offset(self, tmp_path):
        """ポーリング後に state.json の offset が更新される。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        state = store.load()
        assert state.last_update_id == 103  # max(update_id=102) + 1

    def test_messages_persisted_to_disk(self, tmp_path):
        """取得したメッセージが messages/YYYY-MM-DD.json に保存される。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        saved = _load_day_messages("2026-02-21", messages_dir)
        assert len(saved) == 3
        assert {m.message_id for m in saved} == {1, 2, 3}

    def test_idempotent_on_rerun(self, tmp_path):
        """同じメッセージで2回実行しても daily/*.md に重複が生じない。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(_FIXTURE_UPDATES)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        # 2回目: 新規メッセージなし（offset が進んでいるため空レスポンス）
        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response([])
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        content = (tmp_path / "daily" / "2026-02-21.md").read_text(encoding="utf-8")
        # タイムラインセクションに 21:00 が1回だけ出現
        assert _get_section(content, "タイムライン").count("21:00") == 1

    def test_other_chat_messages_filtered_out(self, tmp_path):
        """対象外の chat_id からのメッセージは取り込まれない。"""
        store = StateStore(tmp_path / "state.json")
        writer = JournalWriter(tmp_path / "daily")
        messages_dir = tmp_path / "messages"
        logger = setup_logger(tmp_path / "logs")

        updates_with_noise = _FIXTURE_UPDATES + [
            {
                "update_id": 103,
                "message": {
                    "message_id": 99,
                    "chat": {"id": -9999},  # 別チャット
                    "date": _T0,
                    "text": "別チャットのメッセージ",
                },
            }
        ]

        with patch("src.fetcher.httpx.get") as mock_get:
            mock_get.return_value = _ok_response(updates_with_noise)
            poll_once("dummy_token", _CHAT_ID, store, writer, messages_dir, logger)

        saved = _load_day_messages("2026-02-21", messages_dir)
        assert all(m.source_chat == _CHAT_ID for m in saved)
        assert len(saved) == 3
