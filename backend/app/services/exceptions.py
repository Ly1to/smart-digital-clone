class ScheduleNotFoundError(Exception):
    def __init__(self, schedule_id: int) -> None:
        self.schedule_id = schedule_id
        super().__init__(f"日程 {schedule_id} 不存在")


class ScheduleTimeRangeError(ValueError):
    def __init__(self, message: str = "结束时间必须晚于开始时间") -> None:
        super().__init__(message)
