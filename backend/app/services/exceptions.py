class ScheduleNotFoundError(Exception):
    def __init__(self, schedule_id: int) -> None:
        self.schedule_id = schedule_id
        super().__init__(f"日程 {schedule_id} 不存在")


class ScheduleTimeRangeError(ValueError):
    def __init__(self, message: str = "结束时间必须晚于开始时间") -> None:
        super().__init__(message)


class StagedScheduleNotFoundError(Exception):
    def __init__(self, staged_id: int) -> None:
        self.staged_id = staged_id
        super().__init__(f"暂存日程 {staged_id} 不存在")


class StagedScheduleStateError(ValueError):
    """暂存日程已确认或已忽略，不能再次操作。"""


class StagedScheduleTimeError(ValueError):
    """暂存日程的日期时间不合法。"""


class NoFreeSlotError(ValueError):
    def __init__(self, message: str = "今天没有足够的空闲时间插入这条日程") -> None:
        super().__init__(message)


class GithubConfigurationError(ValueError):
    def __init__(
        self,
        message: str = "未配置 GITHUB_USERNAME，无法同步 GitHub 仓库更新",
    ) -> None:
        super().__init__(message)


class GithubApiError(RuntimeError):
    pass


class AuthAlreadyInitializedError(ValueError):
    def __init__(self, message: str = "系统已经创建过管理员账号") -> None:
        super().__init__(message)


class AuthInvalidCredentialsError(ValueError):
    def __init__(self, message: str = "用户名或密码不正确") -> None:
        super().__init__(message)


class AuthUsernameTakenError(ValueError):
    def __init__(self, message: str = "用户名已被使用") -> None:
        super().__init__(message)
