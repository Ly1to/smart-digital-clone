from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.time import serialize_utc


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
    qq_connected: bool = False


class BindCodeResponse(BaseModel):
    code: str
    expires_at: datetime
    expires_in_seconds: int

    @field_serializer("expires_at")
    def serialize_expires_at(self, value: datetime) -> str:
        return serialize_utc(value) or ""


class QqBindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    external_id: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc(value) or ""
