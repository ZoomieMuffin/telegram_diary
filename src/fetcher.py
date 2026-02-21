import httpx

from src.models import Message
from src.normalizer import normalize


class FetchError(Exception):
    pass


def fetch(bot_token: str, chat_id: int, offset: int) -> list[Message]:
    """Telegram getUpdates API を呼び出し、chat_id に一致するメッセージを返す。"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    try:
        response = httpx.get(url, params={"offset": offset}, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise FetchError(str(exc)) from exc

    if not data.get("ok"):
        raise FetchError(data.get("description", "API returned ok=false"))

    messages = []
    for update in data["result"]:
        msg = normalize(update)
        if msg is not None and msg.source_chat == chat_id:
            messages.append(msg)

    return messages
