from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, schedules
from app.core.config import settings
from app.services.exceptions import ScheduleNotFoundError, ScheduleTimeRangeError


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
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="单用户、免登录的个人日程系统 API。",
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
    app.include_router(schedules.router, prefix=settings.api_prefix)

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

    return app


app = create_app()
