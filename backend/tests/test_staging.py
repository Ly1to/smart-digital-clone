from datetime import UTC, datetime, timedelta, timezone

import pytest
from app.models.enums import ScheduleCategory, ScheduleStatus, StagedStatus
from app.models.schedule import Schedule
from app.models.staging import StagedSchedule
from app.services import staging_service
from sqlalchemy.orm import Session

TZ = timezone(timedelta(hours=8))
FIXED_NOW = datetime(2026, 11, 8, 9, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch) -> None:
    monkeypatch.setattr(staging_service, "local_now", lambda: FIXED_NOW)


def create_staged(db: Session, ref: str, **overrides) -> StagedSchedule:
    values = {
        "source": "github",
        "source_ref": f"github:octo/demo:{ref}",
        "source_url": "https://github.com/octo/demo",
        "source_meta": {"repo": "octo/demo"},
        "title": "GitHub 更新：octo/demo",
        "category": ScheduleCategory.work,
        "description": "最近提交",
        "all_day": False,
        "status": StagedStatus.pending,
    }
    values.update(overrides)
    staged = StagedSchedule(**values)
    db.add(staged)
    db.commit()
    db.refresh(staged)
    return staged


def test_list_defaults_to_pending(client, db: Session) -> None:
    pending = create_staged(db, "a")
    create_staged(db, "b", status=StagedStatus.approved)

    response = client.get("/api/staging")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [pending.id]
    assert response.json()[0]["status"] == "pending"


def test_update_staged_fields(client, db: Session) -> None:
    staged = create_staged(db, "update")
    start = FIXED_NOW + timedelta(hours=1)
    end = start + timedelta(minutes=45)

    response = client.patch(
        f"/api/staging/{staged.id}",
        json={
            "title": "  调整后的仓库更新  ",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "调整后的仓库更新"
    assert data["start_at"] == start.astimezone(UTC).isoformat().replace("+00:00", "Z")
    assert data["end_at"] == end.astimezone(UTC).isoformat().replace("+00:00", "Z")


def test_update_rejects_invalid_time_range(client, db: Session) -> None:
    staged = create_staged(db, "invalid")
    start = FIXED_NOW + timedelta(hours=1)

    response = client.patch(
        f"/api/staging/{staged.id}",
        json={
            "start_at": start.isoformat(),
            "end_at": (start - timedelta(minutes=30)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert "结束时间" in response.json()["detail"]


def test_reject_staged_removes_it_from_pending(client, db: Session) -> None:
    staged = create_staged(db, "reject")

    response = client.post(f"/api/staging/{staged.id}/reject")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert client.get("/api/staging").json() == []


def test_approve_staged_creates_schedule_and_marks_approved(client, db: Session) -> None:
    start = datetime(2026, 11, 8, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)
    staged = create_staged(db, "approve", start_at=start, end_at=end)

    response = client.post(f"/api/staging/{staged.id}/approve")

    assert response.status_code == 200
    data = response.json()
    assert data["staged"]["status"] == "approved"
    assert data["schedule"]["title"] == staged.title
    assert data["schedule"]["source"] == "github"
    assert data["schedule"]["source_url"] == "https://github.com/octo/demo"
    assert data["schedule"]["start_at"] == "2026-11-08T02:00:00Z"
    assert data["schedule"]["end_at"] == "2026-11-08T02:30:00Z"

    repeated = client.post(f"/api/staging/{staged.id}/approve")
    assert repeated.status_code == 409


def test_approve_rejects_when_no_free_slot(client, db: Session, monkeypatch) -> None:
    staged = create_staged(db, "full")
    monkeypatch.setattr(
        staging_service,
        "local_now",
        lambda: datetime(2026, 11, 8, 21, 45, tzinfo=TZ),
    )

    response = client.post(f"/api/staging/{staged.id}/approve")

    assert response.status_code == 409
    assert "空闲时间" in response.json()["detail"]


def test_approve_all_assigns_sequential_slots(client, db: Session) -> None:
    first = create_staged(db, "first")
    second = create_staged(db, "second")

    response = client.post("/api/staging/approve-all")

    assert response.status_code == 200
    data = response.json()
    assert [item["start_at"] for item in data["approved"]] == [
        "2026-11-08T01:00:00Z",
        "2026-11-08T01:30:00Z",
    ]
    assert data["skipped"] == []
    assert client.get("/api/staging").json() == []

    db.expire_all()
    assert db.get(StagedSchedule, first.id).status == StagedStatus.approved
    assert db.get(StagedSchedule, second.id).status == StagedStatus.approved


def test_approve_avoids_existing_schedule(client, db: Session) -> None:
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
    staged = create_staged(db, "busy")

    response = client.post(f"/api/staging/{staged.id}/approve")

    assert response.status_code == 200
    assert response.json()["schedule"]["start_at"] == "2026-11-08T02:00:00Z"


def test_missing_staged_returns_404(client) -> None:
    assert client.post("/api/staging/999/approve").status_code == 404
    assert client.post("/api/staging/999/reject").status_code == 404
