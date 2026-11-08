from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.auth import (
    AuthStatusResponse,
    LoginRequest,
    SetupRequest,
    TokenResponse,
    UserRead,
)
from app.services import auth_service
from app.services.exceptions import (
    AuthAlreadyInitializedError,
    AuthInvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(db: DbSession) -> AuthStatusResponse:
    return AuthStatusResponse(initialized=auth_service.count_users(db) > 0)


@router.post("/setup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def setup_account(payload: SetupRequest, db: DbSession) -> TokenResponse:
    try:
        user = auth_service.create_user(db, payload.username, payload.password)
    except AuthAlreadyInitializedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(
        access_token=auth_service.create_access_token(user),
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    try:
        user = auth_service.authenticate(db, payload.username, payload.password)
    except AuthInvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(
        access_token=auth_service.create_access_token(user),
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, current_user: CurrentUser) -> None:
    # JWT 无服务端会话，客户端删除 Token 即可；保留接口便于前端统一调用。
    response.status_code = status.HTTP_204_NO_CONTENT
