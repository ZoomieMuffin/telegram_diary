import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_JST = ZoneInfo("Asia/Tokyo")
_FMT = "%(asctime)s %(levelname)s %(message)s"


def setup_logger(logs_dir: Path = Path("logs")) -> logging.Logger:
    """JST 日付のログファイルにハンドラを設定したロガーを返す。"""
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=_JST).strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.log"

    logger = logging.getLogger("telegram_diary")
    logger.setLevel(logging.INFO)

    # 既存ハンドラがなければ追加（重複防止）
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_FMT))
        logger.addHandler(file_handler)

    return logger
