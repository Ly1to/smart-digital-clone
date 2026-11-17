from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.bot import binding as binding_service
from app.bot.llm import LLMProvider, get_llm_provider
from app.bot.onebot import is_connected
from app.bot.pipeline import run_chat
from app.core.config import settings
from app.db.session import get_db
from app.schemas.bot import (
    BindCodeResponse,
    BotChatRequest,
    BotChatResponse,
    BotStatusResponse,
    QqBindingRead,
)

router = APIRouter(prefix="/bot", tags=["bot"])

DbSession = Annotated[Session, Depends(get_db)]
Provider = Annotated[LLMProvider, Depends(get_llm_provider)]


@router.get("/status", response_model=BotStatusResponse)
def bot_status(_current_user: CurrentUser) -> BotStatusResponse:
    return BotStatusResponse(
        configured=bool(settings.deepseek_api_key.strip()),
        provider="deepseek",
        model=settings.deepseek_model,
        qq_enabled=settings.qq_bot_enabled,
        qq_connected=is_connected(),
    )


@router.post("/chat", response_model=BotChatResponse)
async def bot_chat(
    payload: BotChatRequest,
    db: DbSession,
    current_user: CurrentUser,
    provider: Provider,
) -> BotChatResponse:
    conversation_id = payload.conversation_id or secrets.token_hex(8)
    reply, tools_used = await run_chat(
        db,
        user_id=current_user.id,
        message=payload.message,
        conversation_key=f"user:{current_user.id}:{conversation_id}",
        provider=provider,
    )
    return BotChatResponse(
        conversation_id=conversation_id,
        reply=reply,
        tools_used=tools_used,
    )


@router.post(
    "/bind-code",
    response_model=BindCodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bind_code(_current_user: CurrentUser) -> BindCodeResponse:
    result = binding_service.create_bind_code(_current_user.id)
    return BindCodeResponse(
        code=result.code,
        expires_at=result.expires_at,
        expires_in_seconds=settings.qq_bind_code_ttl_seconds,
    )


@router.get("/bindings", response_model=list[QqBindingRead])
def list_bindings(db: DbSession, current_user: CurrentUser) -> list:
    return binding_service.list_bindings(db, current_user.id)


@router.delete("/bindings/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_binding(binding_id: int, db: DbSession, current_user: CurrentUser) -> None:
    if not binding_service.delete_binding(
        db,
        user_id=current_user.id,
        binding_id=binding_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="绑定不存在",
        )
