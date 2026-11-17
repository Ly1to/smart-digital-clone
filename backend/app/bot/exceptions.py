class BotError(Exception):
    """对话机器人的基础异常。"""


class BotNotConfiguredError(BotError):
    def __init__(self, message: str = "未配置 DEEPSEEK_API_KEY，对话机器人不可用") -> None:
        super().__init__(message)


class BotUpstreamError(BotError):
    """模型服务不可用或返回错误状态。"""


class BotResponseError(BotError):
    """模型返回了无法处理的内容。"""
