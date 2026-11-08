from __future__ import annotations

import threading
from collections.abc import Callable
from functools import wraps

# 单进程内串行化自动来源同步和暂存日程插入，避免两个来源把日程分配到同一空档。
_SYNC_LOCK = threading.RLock()


def synchronized[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with _SYNC_LOCK:
            return func(*args, **kwargs)

    return wrapper
