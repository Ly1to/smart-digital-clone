def test_auth_status_starts_uninitialized(anonymous_client) -> None:
    response = anonymous_client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {"initialized": False, "registration_enabled": True}


def test_protected_routes_require_login(anonymous_client) -> None:
    for path in ("/api/schedules", "/api/staging", "/api/auto-sources/github/status"):
        response = anonymous_client.get(path)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_setup_login_and_me_flow(anonymous_client) -> None:
    setup = anonymous_client.post(
        "/api/auth/setup",
        json={"username": "owner", "password": "strong-password-123"},
    )
    assert setup.status_code == 201
    setup_data = setup.json()
    token = setup_data["access_token"]
    assert setup_data["token_type"] == "bearer"
    assert setup_data["user"]["username"] == "owner"

    me = anonymous_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "owner"

    duplicate = anonymous_client.post(
        "/api/auth/setup",
        json={"username": "second", "password": "another-password-123"},
    )
    assert duplicate.status_code == 409

    wrong = anonymous_client.post(
        "/api/auth/login",
        json={"username": "owner", "password": "wrong-password"},
    )
    assert wrong.status_code == 401

    login = anonymous_client.post(
        "/api/auth/login",
        json={"username": "owner", "password": "strong-password-123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["username"] == "owner"


def test_invalid_token_is_rejected(anonymous_client) -> None:
    response = anonymous_client.get(
        "/api/schedules",
        headers={"Authorization": "Bearer not-a-token"},
    )

    assert response.status_code == 401


def test_setup_validates_password_length(anonymous_client) -> None:
    response = anonymous_client.post(
        "/api/auth/setup",
        json={"username": "owner", "password": "short"},
    )

    assert response.status_code == 422


def test_register_creates_account_and_returns_token(anonymous_client) -> None:
    setup = anonymous_client.post(
        "/api/auth/setup",
        json={"username": "owner", "password": "strong-password-123"},
    )
    assert setup.status_code == 201

    response = anonymous_client.post(
        "/api/auth/register",
        json={"username": "second", "password": "another-password-123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == "second"

    me = anonymous_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "second"


def test_register_rejects_duplicate_username(anonymous_client) -> None:
    anonymous_client.post(
        "/api/auth/setup",
        json={"username": "owner", "password": "strong-password-123"},
    )

    response = anonymous_client.post(
        "/api/auth/register",
        json={"username": "owner", "password": "another-password-123"},
    )

    assert response.status_code == 409
    assert "已被使用" in response.json()["detail"]


def test_register_can_be_disabled(anonymous_client, monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "allow_registration", False)

    response = anonymous_client.post(
        "/api/auth/register",
        json={"username": "second", "password": "another-password-123"},
    )

    assert response.status_code == 403
    assert "未开放注册" in response.json()["detail"]


def test_users_only_see_their_own_schedules(client) -> None:
    created = client.post(
        "/api/schedules",
        json={
            "title": "管理员日程",
            "category": "work",
            "start_at": "2026-11-05T09:00:00Z",
            "end_at": "2026-11-05T10:00:00Z",
        },
    )
    assert created.status_code == 201
    schedule_id = created.json()["id"]

    registered = client.post(
        "/api/auth/register",
        json={"username": "second", "password": "another-password-123"},
    )
    assert registered.status_code == 201
    other_headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}

    listing = client.get("/api/schedules", headers=other_headers)
    assert listing.json() == []

    detail = client.get(f"/api/schedules/{schedule_id}", headers=other_headers)
    assert detail.status_code == 404

    deletion = client.delete(f"/api/schedules/{schedule_id}", headers=other_headers)
    assert deletion.status_code == 404
