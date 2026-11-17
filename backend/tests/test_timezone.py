from datetime import UTC, datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from app.core import time as core_time
from app.core.config import Settings
from app.services import staging_service
from pydantic import ValidationError


def test_invalid_app_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError, match="无效的时区名称"):
        Settings(app_timezone="Mars/Olympus_Mons")


def test_local_now_uses_app_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_time.settings, "app_timezone", "America/New_York")
    core_time.app_timezone.cache_clear()
    try:
        assert core_time.local_now().tzinfo == ZoneInfo("America/New_York")
    finally:
        core_time.app_timezone.cache_clear()


def test_day_bounds_follow_app_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_time, "app_timezone", lambda: ZoneInfo("Asia/Shanghai"))

    start, end = staging_service._day_bounds(datetime(2026, 1, 1, 1, 0, tzinfo=UTC), 9, 22)

    # 上海时间 09:00–22:00 对应 UTC 01:00–14:00。
    assert start == datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    assert end == datetime(2026, 1, 1, 14, 0, tzinfo=UTC)


def test_all_day_interval_uses_local_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_time, "app_timezone", lambda: ZoneInfo("Asia/Shanghai"))
    staged = SimpleNamespace(start_at=None, end_at=None)

    # UTC 2026-01-01 17:00 已是上海时间 01-02 01:00。
    interval = staging_service._all_day_interval(
        staged,
        datetime(2026, 1, 1, 17, 0, tzinfo=UTC),
    )

    assert interval.start == datetime(2026, 1, 2, tzinfo=UTC)
    assert interval.end == datetime(2026, 1, 2, 23, 59, 59, 999999, tzinfo=UTC)
