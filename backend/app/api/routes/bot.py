from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.bot.llm import LLMProvider, get_llm_provider
from app.bot.pipeline import run_chat
from app.core.config import settings
from app.db.session import get_db
from app.schemas.bot import BotChatRequest, BotChatResponse, BotStatusResponse

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
