from datetime import UTC, datetime, timedelta

from app.services.scheduling import TimeInterval, find_free_slot


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 8, hour, minute, tzinfo=UTC)


def test_finds_first_free_slot() -> None:
    slot = find_free_slot(
        [],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=30),
        not_before=dt(9),
    )

    assert slot == TimeInterval(dt(9), dt(9, 30))


def test_skips_and_merges_busy_intervals() -> None:
    slot = find_free_slot(
        [
            TimeInterval(dt(9), dt(10)),
            TimeInterval(dt(9, 30), dt(10, 30)),
            TimeInterval(dt(12), dt(13)),
        ],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=45),
    )

    assert slot == TimeInterval(dt(10, 30), dt(11, 15))


def test_respects_not_before_and_five_minute_granularity() -> None:
    slot = find_free_slot(
        [TimeInterval(dt(9), dt(10))],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=30),
        not_before=dt(11, 3),
    )

    assert slot == TimeInterval(dt(11, 5), dt(11, 35))


def test_returns_none_when_day_is_full() -> None:
    slot = find_free_slot(
        [TimeInterval(dt(9), dt(18))],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=30),
    )

    assert slot is None


def test_ignores_busy_intervals_outside_the_day_window() -> None:
    slot = find_free_slot(
        [
            TimeInterval(dt(7), dt(9)),
            TimeInterval(dt(18), dt(20)),
        ],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=30),
    )

    assert slot == TimeInterval(dt(9), dt(9, 30))


def test_returns_none_when_not_before_is_after_day_end() -> None:
    slot = find_free_slot(
        [],
        day_start=dt(9),
        day_end=dt(18),
        duration=timedelta(minutes=30),
        not_before=dt(19),
    )

    assert slot is None
