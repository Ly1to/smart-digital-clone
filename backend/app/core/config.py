import secrets
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


class Settings(BaseSettings):
    """应用配置，全部可通过环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "个人日程系统 API"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{DATA_DIR / 'schedules.db'}"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    app_timezone: str = "Asia/Shanghai"

    github_username: str = ""
    github_token: str | None = None
    github_lookback_days: int = Field(default=14, ge=1, le=90)
    github_api_url: str = "https://api.github.com"
    github_auto_sync_minutes: int = Field(default=360, ge=0, le=1440)

    gitee_username: str = ""
    gitee_access_token: str | None = None
    gitee_lookback_days: int = Field(default=14, ge=1, le=90)
    gitee_api_url: str = "https://gitee.com/api/v5"
    gitee_auto_sync_minutes: int = Field(default=360, ge=0, le=1440)

    auto_schedule_duration_minutes: int = Field(default=30, ge=15, le=240)
    auto_schedule_day_start_hour: int = Field(default=9, ge=0, le=23)
    auto_schedule_day_end_hour: int = Field(default=22, ge=1, le=24)

    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    access_token_expire_minutes: int = Field(default=7 * 24 * 60, ge=5, le=365 * 24 * 60)
    auth_bootstrap_username: str = ""
    auth_bootstrap_password: str = ""
    allow_registration: bool = True

    # 对话机器人：Phase 1 只提供 /api/bot/chat 调试接口，QQ 接入在后续阶段启用。
    qq_bot_enabled: bool = False
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    bot_llm_timeout_seconds: float = Field(default=30.0, ge=5, le=120)
    bot_history_turns: int = Field(default=6, ge=0, le=20)
    bot_max_tool_rounds: int = Field(default=4, ge=1, le=8)
    onebot_ws_url: str = ""
    onebot_access_token: str = ""
    qq_bot_allowed_users: str = ""
    qq_bot_allowed_groups: str = ""
    qq_bot_reply_chunk_size: int = Field(default=1200, ge=200, le=4000)
    qq_bind_code_ttl_seconds: int = Field(default=600, ge=60, le=3600)

    @field_validator("app_timezone")
    @classmethod
    def _validate_app_timezone(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("APP_TIMEZONE 不能为空")
        try:
            ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"无效的时区名称：{name}") from exc
        return name


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
