from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, auto_sources, bot, health, schedules, staging
from app.bot.exceptions import (
    BotNotConfiguredError,
    BotResponseError,
    BotUpstreamError,
)
from app.bot.onebot import run_qq_bot
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import auth_service, gitee_service, github_service
from app.services.exceptions import (
    GithubApiError,
    GithubConfigurationError,
    NoFreeSlotError,
    ScheduleNotFoundError,
    ScheduleTimeRangeError,
    StagedScheduleNotFoundError,
    StagedScheduleStateError,
    StagedScheduleTimeError,
)

logger = logging.getLogger(__name__)


def _format_validation_errors(exc: RequestValidationError) -> str:
    messages = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in {"body", "query", "path"}]
        field = ".".join(location) or "请求参数"
        message = error["msg"].removeprefix("Value error, ")
        messages.append(f"{field}: {message}")
    return "；".join(messages) or "请求参数不合法"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # 表结构由 Alembic 管理，应用启动时不自动建表。
    if settings.auth_bootstrap_username and settings.auth_bootstrap_password:
        with SessionLocal() as db:
            if auth_service.count_users(db) == 0:
                try:
                    auth_service.create_user(
                        db,
                        settings.auth_bootstrap_username,
                        settings.auth_bootstrap_password,
                    )
                    logger.info("已创建初始管理员账号：%s", settings.auth_bootstrap_username)
                except ValueError as exc:
                    logger.warning("创建初始管理员账号失败：%s", exc)

    background_tasks: list[asyncio.Task] = []
    if (
        settings.github_username or settings.github_token
    ) and settings.github_auto_sync_minutes > 0:
        background_tasks.append(asyncio.create_task(github_service.auto_sync_loop()))
    if (settings.gitee_username) and settings.gitee_auto_sync_minutes > 0:
        background_tasks.append(asyncio.create_task(gitee_service.auto_sync_loop()))
    if settings.qq_bot_enabled:
        background_tasks.append(asyncio.create_task(run_qq_bot()))

    yield

    for task in background_tasks:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="单用户、需要登录的个人日程系统 API。",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(schedules.router, prefix=settings.api_prefix)
    app.include_router(staging.router, prefix=settings.api_prefix)
    app.include_router(auto_sources.router, prefix=settings.api_prefix)
    app.include_router(auto_sources.gitee_router, prefix=settings.api_prefix)
    app.include_router(bot.router, prefix=settings.api_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/docs"}

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": _format_validation_errors(exc)},
        )

    @app.exception_handler(ScheduleNotFoundError)
    async def schedule_not_found_handler(
        request: Request, exc: ScheduleNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ScheduleTimeRangeError)
    async def time_range_handler(request: Request, exc: ScheduleTimeRangeError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(StagedScheduleNotFoundError)
    async def staged_not_found_handler(
        request: Request, exc: StagedScheduleNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(StagedScheduleStateError)
    async def staged_state_handler(request: Request, exc: StagedScheduleStateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(StagedScheduleTimeError)
    async def staged_time_handler(request: Request, exc: StagedScheduleTimeError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NoFreeSlotError)
    async def no_free_slot_handler(request: Request, exc: NoFreeSlotError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(GithubConfigurationError)
    async def github_config_handler(
        request: Request, exc: GithubConfigurationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(GithubApiError)
    async def github_api_handler(request: Request, exc: GithubApiError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(BotNotConfiguredError)
    async def bot_not_configured_handler(
        request: Request, exc: BotNotConfiguredError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(BotUpstreamError)
    async def bot_upstream_handler(request: Request, exc: BotUpstreamError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(BotResponseError)
    async def bot_response_handler(request: Request, exc: BotResponseError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app


app = create_app()
