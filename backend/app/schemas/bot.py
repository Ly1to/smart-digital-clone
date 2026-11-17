from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class BotChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("消息不能为空")
        return value


class BotChatResponse(BaseModel):
    conversation_id: str
    reply: str
    tools_used: list[str] = Field(default_factory=list)


class BotStatusResponse(BaseModel):
    configured: bool
    provider: str
    model: str
    qq_enabled: bool
