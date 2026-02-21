import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.models import State

_DEFAULT_DT = datetime(2000, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo"))


class StateStore:
    def __init__(self, state_file: Path = Path("state.json")):
        self.state_file = state_file
        self.backup_file = state_file.parent / (state_file.name + ".bak")

    def save(self, state: State) -> None:
        if self.state_file.exists():
            shutil.copy2(self.state_file, self.backup_file)
        data = {
            "last_update_id": state.last_update_id,
            "last_run_at": state.last_run_at.isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def load(self) -> State:
        state = self._try_load(self.state_file)
        if state is not None:
            return state
        state = self._try_load(self.backup_file)
        if state is not None:
            return state
        return State(last_update_id=0, last_run_at=_DEFAULT_DT)

    def _try_load(self, path: Path) -> State | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return State(
                last_update_id=data["last_update_id"],
                last_run_at=datetime.fromisoformat(data["last_run_at"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
