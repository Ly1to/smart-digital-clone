from __future__ import annotations

from collections.abc import Generator

import app.models  # noqa: F401  注册 ORM 模型
import pytest
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

TEST_USERNAME = "test-admin"
TEST_PASSWORD = "test-password-123"


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Generator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient]:
    monkeypatch.setattr(settings, "auth_bootstrap_username", "")
    monkeypatch.setattr(settings, "auth_bootstrap_password", "")
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-at-least-32-bytes-long")
    monkeypatch.setattr(settings, "github_username", "")
    monkeypatch.setattr(settings, "github_token", None)
    monkeypatch.setattr(settings, "github_auto_sync_minutes", 0)
    monkeypatch.setattr(settings, "gitee_username", "")
    monkeypatch.setattr(settings, "gitee_access_token", None)
    monkeypatch.setattr(settings, "gitee_auto_sync_minutes", 0)

    def override_get_db() -> Generator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        setup = test_client.post(
            "/api/auth/setup",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        assert setup.status_code == 201, setup.text
        test_client.headers.update({"Authorization": f"Bearer {setup.json()['access_token']}"})
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient]:
    monkeypatch.setattr(settings, "auth_bootstrap_username", "")
    monkeypatch.setattr(settings, "auth_bootstrap_password", "")
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-at-least-32-bytes-long")
    monkeypatch.setattr(settings, "github_username", "")
    monkeypatch.setattr(settings, "github_token", None)
    monkeypatch.setattr(settings, "github_auto_sync_minutes", 0)
    monkeypatch.setattr(settings, "gitee_username", "")
    monkeypatch.setattr(settings, "gitee_access_token", None)
    monkeypatch.setattr(settings, "gitee_auto_sync_minutes", 0)

    def override_get_db() -> Generator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def schedule_payload() -> dict:
    return {
        "title": "项目周会",
        "category": "work",
        "description": "讨论本周进度",
        "start_at": "2026-11-05T14:00:00+08:00",
        "end_at": "2026-11-05T15:00:00+08:00",
        "all_day": False,
        "location": "线上",
    }
