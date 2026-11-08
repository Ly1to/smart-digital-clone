def test_auth_status_starts_uninitialized(anonymous_client) -> None:
    response = anonymous_client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {"initialized": False}


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
