from enum import StrEnum


class ScheduleCategory(StrEnum):
    """MVP 固定的三类日程。"""

    work = "work"
    outing = "outing"
    private = "private"


class ScheduleStatus(StrEnum):
    """日程状态，默认待进行。"""

    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class StagedStatus(StrEnum):
    """自动来源暂存日程的确认状态。"""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


CATEGORY_LABELS: dict[ScheduleCategory, str] = {
    ScheduleCategory.work: "工作",
    ScheduleCategory.outing: "外出",
    ScheduleCategory.private: "私人时间",
}

STATUS_LABELS: dict[ScheduleStatus, str] = {
    ScheduleStatus.pending: "待进行",
    ScheduleStatus.completed: "已完成",
    ScheduleStatus.cancelled: "已取消",
}
