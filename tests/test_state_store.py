import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.models import State
from src.state_store import StateStore

JST = ZoneInfo("Asia/Tokyo")
_DT = datetime(2026, 2, 21, 12, 0, 0, tzinfo=JST)


@pytest.fixture
def store(tmp_path):
    return StateStore(state_file=tmp_path / "state.json")


class TestLoad:
    def test_default_when_no_file(self, store):
        state = store.load()
        assert state.last_update_id == 0

    def test_save_and_load_last_update_id(self, store):
        store.save(State(last_update_id=42, last_run_at=_DT))
        assert store.load().last_update_id == 42

    def test_save_and_load_last_run_at(self, store):
        store.save(State(last_update_id=0, last_run_at=_DT))
        assert store.load().last_run_at == _DT

    def test_load_from_backup_when_main_corrupted(self, store, tmp_path):
        store.save(State(last_update_id=10, last_run_at=_DT))
        store.save(State(last_update_id=20, last_run_at=_DT))  # 10 → .bak
        (tmp_path / "state.json").write_text("not valid json")

        assert store.load().last_update_id == 10

    def test_default_when_both_corrupted(self, store, tmp_path):
        (tmp_path / "state.json").write_text("bad")
        (tmp_path / "state.json.bak").write_text("bad")

        assert store.load().last_update_id == 0

    def test_load_from_backup_when_main_missing(self, store, tmp_path):
        bak = tmp_path / "state.json.bak"
        bak.write_text(json.dumps({"last_update_id": 99, "last_run_at": _DT.isoformat()}))

        assert store.load().last_update_id == 99


class TestSave:
    def test_creates_state_file(self, store, tmp_path):
        store.save(State(last_update_id=1, last_run_at=_DT))
        assert (tmp_path / "state.json").exists()

    def test_creates_backup_on_second_save(self, store, tmp_path):
        store.save(State(last_update_id=10, last_run_at=_DT))
        store.save(State(last_update_id=20, last_run_at=_DT))

        bak = tmp_path / "state.json.bak"
        assert bak.exists()
        assert json.loads(bak.read_text())["last_update_id"] == 10

    def test_no_backup_on_first_save(self, store, tmp_path):
        store.save(State(last_update_id=1, last_run_at=_DT))
        assert not (tmp_path / "state.json.bak").exists()
