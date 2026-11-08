from datetime import UTC, datetime, timedelta, timezone

import httpx
import pytest
from app.core.config import settings
from app.core.time import to_utc
from app.models.enums import ScheduleCategory, ScheduleStatus
from app.models.schedule import Schedule
from app.models.staging import StagedSchedule
from app.services import gitee_service, staging_service
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
        "repo": {"full_name": repo, "url": f"https://gitee.com/{repo}"},
        "payload": payload,
    }


@pytest.fixture
def events() -> list[dict]:
    return [
        event(
            "101",
            "PushEvent",
            "oschina/demo",
            "2026-11-08T00:50:00Z",
            {
                "head": "gitee123",
                "commits": [
                    {"message": "feat: support gitee"},
                    {"message": "fix: event payload"},
                ],
            },
        ),
        event(
            "102",
            "MergeRequestEvent",
            "oschina/demo",
            "2026-11-08T00:40:00Z",
            {
                "action": "merge",
                "merge_request": {"title": "Add Gitee source"},
            },
        ),
        event(
            "103",
            "ReleaseEvent",
            "oschina/demo",
            "2026-11-08T00:30:00Z",
            {"release": {"name": "v2.0.0"}},
        ),
        event(
            "104",
            "PushEvent",
            "oschina/other",
            "2026-11-08T00:20:00Z",
            {"head": "gitee456", "commits": [{"message": "chore: sync"}]},
        ),
    ]


def test_group_gitee_events(events: list[dict]) -> None:
    updates = gitee_service.group_events(events)

    assert [update.repo for update in updates] == ["oschina/demo", "oschina/other"]
    demo = updates[0]
    assert demo.latest_key == "gitee123"
    assert demo.commit_count == 2
    assert demo.html_url == "https://gitee.com/oschina/demo"
    description = demo.description(14)
    assert "提交：2 次" in description
    assert "合并：Add Gitee source" in description
    assert "v2.0.0" in description


def test_fetch_gitee_events_uses_public_endpoint(events: list[dict]) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=events)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = gitee_service.fetch_events(
        username="oschina",
        access_token=None,
        lookback_days=14,
        api_url="https://gitee.com/api/v5",
        now=FIXED_NOW,
        client=client,
    )

    assert len(result) == 4
    assert requests[0].url.path == "/api/v5/users/oschina/events/public"
    assert requests[0].url.params["limit"] == "100"


def test_fetch_gitee_events_uses_token(events: list[dict]) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=events)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gitee_service.fetch_events(
        username="oschina",
        access_token="secret",
        lookback_days=14,
        api_url="https://gitee.com/api/v5",
        now=FIXED_NOW,
        client=client,
    )

    assert requests[0].url.path == "/api/v5/users/oschina/events"
    assert requests[0].url.params["access_token"] == "secret"


def test_fetch_gitee_empty_404_returns_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "404 Not Found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = gitee_service.fetch_events(
        username="oschina",
        access_token=None,
        lookback_days=14,
        api_url="https://gitee.com/api/v5",
        now=FIXED_NOW,
        client=client,
    )

    assert result == []


def test_sync_gitee_creates_staged_items(
    db: Session,
    events: list[dict],
    monkeypatch,
) -> None:
    monkeypatch.setattr(gitee_service, "fetch_events", lambda **kwargs: events)
    db.add(
        Schedule(
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

    result = gitee_service.sync_gitee(
        db,
        username="oschina",
        access_token=None,
        lookback_days=14,
        api_url="https://gitee.com/api/v5",
        duration_minutes=30,
        day_start_hour=9,
        day_end_hour=22,
        now=FIXED_NOW,
    )

    assert result.scanned_events == 4
    assert result.created == 2
    assert result.no_slot == 0

    staged = list(db.scalars(select(StagedSchedule).order_by(StagedSchedule.id)))
    assert [item.source for item in staged] == ["gitee", "gitee"]
    assert [item.source_ref for item in staged] == [
        "gitee:oschina/demo:gitee123",
        "gitee:oschina/other:gitee456",
    ]
    assert [to_utc(item.start_at) for item in staged if item.start_at] == [
        datetime(2026, 11, 8, 2, 0, tzinfo=UTC),
        datetime(2026, 11, 8, 2, 30, tzinfo=UTC),
    ]


def test_sync_gitee_is_idempotent(
    db: Session,
    events: list[dict],
    monkeypatch,
) -> None:
    monkeypatch.setattr(gitee_service, "fetch_events", lambda **kwargs: events)
    kwargs = {
        "db": db,
        "username": "oschina",
        "access_token": None,
        "lookback_days": 14,
        "api_url": "https://gitee.com/api/v5",
        "duration_minutes": 30,
        "day_start_hour": 9,
        "day_end_hour": 22,
        "now": FIXED_NOW,
    }

    first = gitee_service.sync_gitee(**kwargs)
    second = gitee_service.sync_gitee(**kwargs)

    assert first.created == 2
    assert second.created == 0
    assert second.updated == 2
    assert len(list(db.scalars(select(StagedSchedule)))) == 2


def test_sync_gitee_skips_approved(
    db: Session,
    events: list[dict],
    monkeypatch,
) -> None:
    monkeypatch.setattr(gitee_service, "fetch_events", lambda **kwargs: events)
    kwargs = {
        "db": db,
        "username": "oschina",
        "access_token": None,
        "lookback_days": 14,
        "api_url": "https://gitee.com/api/v5",
        "duration_minutes": 30,
        "day_start_hour": 9,
        "day_end_hour": 22,
        "now": FIXED_NOW,
    }
    gitee_service.sync_gitee(**kwargs)
    demo = db.scalar(
        select(StagedSchedule).where(StagedSchedule.source_ref.like("gitee:oschina/demo:%"))
    )
    assert demo is not None
    staging_service.approve_staged(db, demo.id, now=FIXED_NOW)

    result = gitee_service.sync_gitee(**kwargs)

    assert result.skipped == 1
    assert result.updated == 1
    assert result.created == 0


def test_gitee_status_and_sync_endpoint(
    client,
    events: list[dict],
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "gitee_username", "oschina")
    monkeypatch.setattr(settings, "gitee_access_token", None)
    monkeypatch.setattr(settings, "gitee_lookback_days", 14)
    monkeypatch.setattr(gitee_service, "fetch_events", lambda **kwargs: events)

    status_response = client.get("/api/auto-sources/gitee/status")
    assert status_response.status_code == 200
    assert status_response.json() == {
        "configured": True,
        "username": "oschina",
        "lookback_days": 14,
        "token_configured": False,
    }

    sync_response = client.post("/api/auto-sources/gitee/sync")
    assert sync_response.status_code == 200
    data = sync_response.json()
    assert data["configured"] is True
    assert data["created"] == 2
    assert "Gitee" in data["message"]


def test_gitee_sync_requires_configuration(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "gitee_username", "")
    monkeypatch.setattr(settings, "gitee_access_token", None)

    response = client.post("/api/auto-sources/gitee/sync")

    assert response.status_code == 400
    assert "GITEE_USERNAME" in response.json()["detail"]
