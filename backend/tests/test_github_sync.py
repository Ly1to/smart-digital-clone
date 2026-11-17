from datetime import UTC, datetime, timedelta, timezone

import httpx
import pytest
from app.core.config import settings
from app.core.time import to_utc
from app.models.enums import ScheduleCategory, ScheduleStatus, StagedStatus
from app.models.schedule import Schedule
from app.models.staging import StagedSchedule
from app.services import github_service, staging_service
from sqlalchemy import select
from sqlalchemy.orm import Session

TZ = timezone(timedelta(hours=8))
FIXED_NOW = datetime(2026, 11, 8, 9, 0, tzinfo=TZ)


def event(
    event_id: str,
    event_type: str,
    repo: str,
    created_at: str,
    payload: dict,
) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "created_at": created_at,
        "repo": {"name": repo, "url": f"https://api.github.com/repos/{repo}"},
        "payload": payload,
    }


@pytest.fixture
def events() -> list[dict]:
    return [
        event(
            "1",
            "PushEvent",
            "octo/demo",
            "2026-11-08T00:50:00Z",
            {
                "head": "abc123",
                "commits": [
                    {"message": "feat: add staging"},
                    {"message": "fix: handle slots\n\nlong body"},
                ],
            },
        ),
        event(
            "2",
            "PullRequestEvent",
            "octo/demo",
            "2026-11-08T00:40:00Z",
            {
                "action": "closed",
                "pull_request": {"title": "Add auto source", "merged": True},
            },
        ),
        event(
            "3",
            "ReleaseEvent",
            "octo/demo",
            "2026-11-08T00:30:00Z",
            {"release": {"name": "v1.0.0", "tag_name": "v1.0.0"}},
        ),
        event(
            "4",
            "PushEvent",
            "octo/other",
            "2026-11-08T00:20:00Z",
            {"head": "def456", "commits": [{"message": "chore: update"}]},
        ),
    ]


def test_group_events_summarizes_repositories(events: list[dict]) -> None:
    updates = github_service.group_events(events)

    assert [update.repo for update in updates] == ["octo/demo", "octo/other"]
    demo = updates[0]
    assert demo.latest_key == "abc123"
    assert demo.commit_count == 2
    assert demo.html_url == "https://github.com/octo/demo"
    description = demo.description(14)
    assert "提交：2 次" in description
    assert "合并：Add auto source" in description
    assert "v1.0.0" in description
    assert "feat: add staging" in description


def test_fetch_events_uses_public_endpoint(events: list[dict]) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=events)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = github_service.fetch_events(
        username="octo",
        token=None,
        lookback_days=14,
        api_url="https://api.github.com",
        now=FIXED_NOW,
        client=client,
    )

    assert len(result) == 4
    assert requests[0].url.path == "/users/octo/events/public"
    assert requests[0].headers["accept"] == "application/vnd.github+json"


def test_fetch_events_uses_token_endpoint(events: list[dict]) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=events)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    github_service.fetch_events(
        username="octo",
        token="secret",
        lookback_days=14,
        api_url="https://api.github.com",
        now=FIXED_NOW,
        client=client,
    )

    assert requests[0].url.path == "/user/events"
    assert requests[0].headers["authorization"] == "Bearer secret"


def test_fetch_events_reports_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(github_service.GithubApiError):
        github_service.fetch_events(
            username="octo",
            token="bad",
            lookback_days=14,
            api_url="https://api.github.com",
            now=FIXED_NOW,
            client=client,
        )


def test_sync_creates_staged_items_in_today_free_slots(
    db: Session,
    events: list[dict],
    test_user,
    monkeypatch,
) -> None:
    monkeypatch.setattr(github_service, "fetch_events", lambda **kwargs: events)
    db.add(
        Schedule(
            user_id=test_user.id,
            title="已占用",
            category=ScheduleCategory.work,
            start_at=datetime(2026, 11, 8, 1, 0, tzinfo=UTC),
            end_at=datetime(2026, 11, 8, 2, 0, tzinfo=UTC),
            all_day=False,
            status=ScheduleStatus.pending,
            source="manual",
        )
    )
    db.commit()

    result = github_service.sync_github(
        db,
        user_id=test_user.id,
        username="octo",
        token=None,
        lookback_days=14,
        api_url="https://api.github.com",
        duration_minutes=30,
        day_start_hour=9,
        day_end_hour=22,
        now=FIXED_NOW,
    )

    assert result.scanned_events == 4
    assert result.created == 2
    assert result.updated == 0
    assert result.no_slot == 0

    staged = list(db.scalars(select(StagedSchedule).order_by(StagedSchedule.id)))
    assert [item.source_ref for item in staged] == [
        "github:octo/demo:abc123",
        "github:octo/other:def456",
    ]
    assert [to_utc(item.start_at) for item in staged if item.start_at] == [
        datetime(2026, 11, 8, 2, 0, tzinfo=UTC),
        datetime(2026, 11, 8, 2, 30, tzinfo=UTC),
    ]
    assert "feat: add staging" in (staged[0].description or "")


def test_sync_is_idempotent_and_updates_pending_items(
    db: Session,
    events: list[dict],
    test_user,
    monkeypatch,
) -> None:
    monkeypatch.setattr(github_service, "fetch_events", lambda **kwargs: events)
    kwargs = {
        "db": db,
        "user_id": test_user.id,
        "username": "octo",
        "token": None,
        "lookback_days": 14,
        "api_url": "https://api.github.com",
        "duration_minutes": 30,
        "day_start_hour": 9,
        "day_end_hour": 22,
        "now": FIXED_NOW,
    }

    first = github_service.sync_github(**kwargs)
    second = github_service.sync_github(**kwargs)

    assert first.created == 2
    assert second.created == 0
    assert second.updated == 2
    assert len(list(db.scalars(select(StagedSchedule)))) == 2


def test_sync_skips_already_approved_updates(
    db: Session,
    events: list[dict],
    test_user,
    monkeypatch,
) -> None:
    monkeypatch.setattr(github_service, "fetch_events", lambda **kwargs: events)
    kwargs = {
        "db": db,
        "user_id": test_user.id,
        "username": "octo",
        "token": None,
        "lookback_days": 14,
        "api_url": "https://api.github.com",
        "duration_minutes": 30,
        "day_start_hour": 9,
        "day_end_hour": 22,
        "now": FIXED_NOW,
    }
    github_service.sync_github(**kwargs)
    demo = db.scalar(
        select(StagedSchedule).where(StagedSchedule.source_ref.like("github:octo/demo:%"))
    )
    assert demo is not None
    staging_service.approve_staged(db, demo.id, user_id=test_user.id, now=FIXED_NOW)

    result = github_service.sync_github(**kwargs)

    assert result.created == 0
    assert result.skipped == 1
    assert result.updated == 1
    assert db.get(StagedSchedule, demo.id).status == StagedStatus.approved


def test_github_status_and_sync_endpoint(
    client,
    events: list[dict],
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "github_username", "octo")
    monkeypatch.setattr(settings, "github_token", None)
    monkeypatch.setattr(settings, "github_lookback_days", 14)
    monkeypatch.setattr(github_service, "fetch_events", lambda **kwargs: events)

    status_response = client.get("/api/auto-sources/github/status")
    assert status_response.status_code == 200
    assert status_response.json() == {
        "configured": True,
        "username": "octo",
        "lookback_days": 14,
        "token_configured": False,
    }

    sync_response = client.post("/api/auto-sources/github/sync")
    assert sync_response.status_code == 200
    data = sync_response.json()
    assert data["configured"] is True
    assert data["created"] == 2
    assert "扫描" in data["message"]


def test_github_sync_requires_configuration(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "github_username", "")
    monkeypatch.setattr(settings, "github_token", None)

    response = client.post("/api/auto-sources/github/sync")

    assert response.status_code == 400
    assert "GITHUB_USERNAME" in response.json()["detail"]
