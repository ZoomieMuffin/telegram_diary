from src.models import Message

_RULES: list[tuple[str, list[str]]] = [
    ("#idea", ["アイデア", "idea", "思いつき"]),
    ("#memo", ["メモ", "memo"]),
    ("#question", ["かな", "どうする", "どうしよう", "？", "?"]),
    ("#task", ["タスク", "task", "todo", "やること"]),
]


def tag(messages: list[Message]) -> list[str]:
    """メッセージリストからルールベースのタグリストを生成する。"""
    if not messages:
        return []
    all_text = " ".join(m.text for m in messages).lower()
    tags = {
        tag_name
        for tag_name, keywords in _RULES
        if any(kw.lower() in all_text for kw in keywords)
    }
    return sorted(tags)
