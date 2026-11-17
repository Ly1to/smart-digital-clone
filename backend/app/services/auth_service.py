from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schedule import Schedule
from app.models.staging import StagedSchedule
from app.models.user import User
from app.services.exceptions import (
    AuthAlreadyInitializedError,
    AuthInvalidCredentialsError,
    AuthUsernameTakenError,
)

SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
MIN_PASSWORD_LENGTH = 8


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"密码至少需要 {MIN_PASSWORD_LENGTH} 个字符")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_b64decode(expected)),
        )
        return hmac.compare_digest(digest, _b64decode(expected))
    except ValueError, TypeError:
        return False


def count_users(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)


def _claim_orphan_records(db: Session, user_id: int) -> None:
    """把启用登录功能前创建、尚未归属任何账号的数据交给第一个账号。"""
    db.execute(update(Schedule).where(Schedule.user_id.is_(None)).values(user_id=user_id))
    db.execute(
        update(StagedSchedule).where(StagedSchedule.user_id.is_(None)).values(user_id=user_id)
    )


def _commit_new_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    try:
        db.flush()
        _claim_orphan_records(db, user.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AuthUsernameTakenError() from exc
    db.refresh(user)
    return user


def create_user(db: Session, username: str, password: str) -> User:
    username = username.strip()
    if not username:
        raise ValueError("用户名不能为空")
    if count_users(db) > 0:
        raise AuthAlreadyInitializedError()

    return _commit_new_user(db, username, password)


def register_user(db: Session, username: str, password: str) -> User:
    username = username.strip()
    if not username:
        raise ValueError("用户名不能为空")
    if db.scalar(select(User.id).where(User.username == username)) is not None:
        raise AuthUsernameTakenError()

    return _commit_new_user(db, username, password)


def get_first_user(db: Session) -> User | None:
    return db.scalar(select(User).order_by(User.id.asc()).limit(1))


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username.strip()))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthInvalidCredentialsError()
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_access_token(user: User) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expire_at,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
