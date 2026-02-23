import json
from pathlib import Path
from typing import TypedDict

import httpx


class HealthResult(TypedDict):
    api: bool
    state: bool
    ok: bool
    bot_username: str | None
    last_update_id: int | None


def check(bot_token: str, state_file: Path = Path("state.json")) -> HealthResult:
    """システムの健全性を確認し、結果を dict で返す。

    Keys:
        api (bool): Telegram API に到達できるか
        state (bool): state.json が読み込めるか
        ok (bool): すべて正常か
        bot_username (str | None): Bot のユーザー名（API 正常時）
        last_update_id (int | None): 最後の update_id（state 正常時）
    """
    result: HealthResult = {"api": False, "state": False, "ok": False,
                            "bot_username": None, "last_update_id": None}

    # --- Telegram API 疎通確認 ---
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            result["api"] = True
            result["bot_username"] = data["result"].get("username")
    except (httpx.HTTPError, KeyError):
        pass

    # --- state.json 読み込み確認 ---
    try:
        if not state_file.exists():
            raise FileNotFoundError
        raw = json.loads(state_file.read_text())
        result["last_update_id"] = raw["last_update_id"]
        result["state"] = True
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

    result["ok"] = result["api"] and result["state"]
    return result
