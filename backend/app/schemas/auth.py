from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.time import serialize_utc, to_utc


class AuthStatusResponse(BaseModel):
    initialized: bool
    registration_enabled: bool = True


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("用户名不能为空")
        return value


class SetupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("用户名至少需要 3 个字符")
        return value


class RegisterRequest(SetupRequest):
    pass


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        return to_utc(value)

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return serialize_utc(value) or ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
