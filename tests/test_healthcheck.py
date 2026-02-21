from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from src.healthcheck import check


def _api_ok():
    mock = MagicMock()
    mock.json.return_value = {"ok": True, "result": {"id": 1, "username": "testbot"}}
    mock.raise_for_status.return_value = None
    return mock


class TestCheck:
    def test_healthy_returns_true_flags(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 0, "last_run_at": "2026-02-21T00:00:00+09:00"}')
        with patch("src.healthcheck.httpx.get", return_value=_api_ok()):
            result = check(bot_token="token", state_file=state_file)
        assert result["api"] is True
        assert result["state"] is True
        assert result["ok"] is True

    def test_api_unreachable(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 0, "last_run_at": "2026-02-21T00:00:00+09:00"}')
        with patch("src.healthcheck.httpx.get", side_effect=httpx.ConnectError("timeout")):
            result = check(bot_token="token", state_file=state_file)
        assert result["api"] is False
        assert result["ok"] is False

    def test_state_missing(self):
        with patch("src.healthcheck.httpx.get", return_value=_api_ok()):
            result = check(bot_token="token", state_file=Path("/nonexistent/state.json"))
        assert result["state"] is False
        assert result["ok"] is False

    def test_state_corrupted(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text("not json")
        with patch("src.healthcheck.httpx.get", return_value=_api_ok()):
            result = check(bot_token="token", state_file=state_file)
        assert result["state"] is False

    def test_result_contains_bot_username_when_healthy(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 5, "last_run_at": "2026-02-21T00:00:00+09:00"}')
        with patch("src.healthcheck.httpx.get", return_value=_api_ok()):
            result = check(bot_token="token", state_file=state_file)
        assert result["bot_username"] == "testbot"

    def test_result_contains_last_update_id(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 42, "last_run_at": "2026-02-21T00:00:00+09:00"}')
        with patch("src.healthcheck.httpx.get", return_value=_api_ok()):
            result = check(bot_token="token", state_file=state_file)
        assert result["last_update_id"] == 42
