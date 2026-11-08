from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class TimeInterval:
    start: datetime
    end: datetime


def _merge_intervals(intervals: Iterable[TimeInterval]) -> list[TimeInterval]:
    ordered = sorted(
        (interval for interval in intervals if interval.end > interval.start),
        key=lambda interval: interval.start,
    )
    merged: list[TimeInterval] = []
    for interval in ordered:
        if merged and interval.start <= merged[-1].end:
            merged[-1] = TimeInterval(merged[-1].start, max(merged[-1].end, interval.end))
        else:
            merged.append(interval)
    return merged


def _ceil_to_granularity(
    value: datetime,
    *,
    anchor: datetime,
    granularity_minutes: int,
) -> datetime:
    elapsed_minutes = (value - anchor).total_seconds() / 60
    steps = math.ceil(elapsed_minutes / granularity_minutes)
    return anchor + timedelta(minutes=steps * granularity_minutes)


def find_free_slot(
    busy: Iterable[TimeInterval],
    *,
    day_start: datetime,
    day_end: datetime,
    duration: timedelta,
    not_before: datetime | None = None,
    granularity_minutes: int = 5,
) -> TimeInterval | None:
    """在 [day_start, day_end) 内寻找第一个可用时段。"""
    if duration <= timedelta(0) or day_end <= day_start:
        return None

    candidate = max(day_start, not_before or day_start)
    if candidate >= day_end:
        return None
    candidate = _ceil_to_granularity(
        candidate,
        anchor=day_start,
        granularity_minutes=granularity_minutes,
    )

    intervals = [
        TimeInterval(max(interval.start, day_start), min(interval.end, day_end))
        for interval in busy
        if interval.end > day_start and interval.start < day_end
    ]

    for interval in _merge_intervals(intervals):
        if interval.end <= candidate:
            continue
        if interval.start - candidate >= duration:
            return TimeInterval(candidate, candidate + duration)
        candidate = max(candidate, interval.end)

    if candidate + duration <= day_end:
        return TimeInterval(candidate, candidate + duration)
    return None
