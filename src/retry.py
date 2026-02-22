import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def with_retry(
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
) -> T:
    """指数バックオフで func を最大 max_attempts 回実行する。

    すべて失敗した場合は最後の例外を送出する。
    """
    last_exc: BaseException = RuntimeError("max_attempts must be >= 1")
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(base_delay * (backoff**attempt))
    raise last_exc
