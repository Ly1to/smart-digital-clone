import pytest


def create_schedule(client, **overrides) -> dict:
    payload = {
        "title": "测试日程",
        "category": "private",
        "start_at": "2026-11-05T09:00:00Z",
        "end_at": "2026-11-05T10:00:00Z",
        "all_day": False,
    }
    payload.update(overrides)
    response = client.post("/api/schedules", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_schedule_converts_time_to_utc(client, schedule_payload) -> None:
    response = client.post("/api/schedules", json=schedule_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "项目周会"
    assert data["category"] == "work"
    assert data["status"] == "pending"
    assert data["start_at"] == "2026-11-05T06:00:00Z"
    assert data["end_at"] == "2026-11-05T07:00:00Z"
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


def test_create_trims_title(client) -> None:
    data = create_schedule(client, title="  听音乐  ")

    assert data["title"] == "听音乐"


@pytest.mark.parametrize("title", ["", "   "])
def test_create_rejects_blank_title(client, title) -> None:
    response = client.post(
        "/api/schedules",
        json={
            "title": title,
            "category": "work",
            "start_at": "2026-11-05T09:00:00Z",
            "end_at": "2026-11-05T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert "标题" in response.json()["detail"]


def test_create_rejects_missing_category(client) -> None:
    response = client.post(
        "/api/schedules",
        json={
            "title": "没有分类",
            "start_at": "2026-11-05T09:00:00Z",
            "end_at": "2026-11-05T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert "category" in response.json()["detail"]


def test_create_rejects_invalid_category(client) -> None:
    response = client.post(
        "/api/schedules",
        json={
            "title": "非法分类",
            "category": "study",
            "start_at": "2026-11-05T09:00:00Z",
            "end_at": "2026-11-05T10:00:00Z",
        },
    )

    assert response.status_code == 422


def test_create_rejects_end_not_after_start(client) -> None:
    response = client.post(
        "/api/schedules",
        json={
            "title": "时间非法",
            "category": "work",
            "start_at": "2026-11-05T10:00:00Z",
            "end_at": "2026-11-05T10:00:00Z",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "结束时间必须晚于开始时间"


def test_all_day_is_normalized_to_inclusive_dates(client) -> None:
    data = create_schedule(
        client,
        all_day=True,
        start_at="2026-11-05T00:00:00Z",
        end_at="2026-11-06T00:00:00Z",
    )

    assert data["all_day"] is True
    assert data["start_at"] == "2026-11-05T00:00:00Z"
    assert data["end_at"] == "2026-11-06T23:59:59.999999Z"


def test_all_day_rejects_reversed_dates(client) -> None:
    response = client.post(
        "/api/schedules",
        json={
            "title": "反向全天",
            "category": "outing",
            "all_day": True,
            "start_at": "2026-11-06T00:00:00Z",
            "end_at": "2026-11-05T00:00:00Z",
        },
    )

    assert response.status_code == 400


def test_get_schedule(client) -> None:
    created = create_schedule(client)

    response = client.get(f"/api/schedules/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_schedule(client) -> None:
    response = client.get("/api/schedules/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "日程 999 不存在"


def test_list_returns_all_schedules_ordered(client) -> None:
    create_schedule(
        client,
        title="第二个",
        start_at="2026-11-06T09:00:00Z",
        end_at="2026-11-06T10:00:00Z",
    )
    create_schedule(
        client,
        title="第一个",
        start_at="2026-11-05T09:00:00Z",
        end_at="2026-11-05T10:00:00Z",
    )

    response = client.get("/api/schedules")

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["第一个", "第二个"]


def test_list_filters_by_range_including_overlap(client) -> None:
    create_schedule(
        client,
        title="跨天",
        start_at="2026-11-05T23:00:00Z",
        end_at="2026-11-06T02:00:00Z",
    )
    create_schedule(
        client,
        title="范围外",
        start_at="2026-11-08T09:00:00Z",
        end_at="2026-11-08T10:00:00Z",
    )

    response = client.get(
        "/api/schedules",
        params={"start": "2026-11-06T00:00:00Z", "end": "2026-11-07T00:00:00Z"},
    )

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["跨天"]


def test_list_all_day_on_second_day_is_included(client) -> None:
    create_schedule(
        client,
        title="两天旅行",
        category="outing",
        all_day=True,
        start_at="2026-11-05T00:00:00Z",
        end_at="2026-11-06T00:00:00Z",
    )

    response = client.get(
        "/api/schedules",
        params={"start": "2026-11-06T00:00:00Z", "end": "2026-11-07T00:00:00Z"},
    )

    assert [item["title"] for item in response.json()] == ["两天旅行"]


def test_list_rejects_invalid_query_range(client) -> None:
    response = client.get(
        "/api/schedules",
        params={"start": "2026-11-07T00:00:00Z", "end": "2026-11-06T00:00:00Z"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "查询结束时间必须晚于开始时间"


def test_list_filters_by_categories(client) -> None:
    create_schedule(client, title="工作", category="work")
    create_schedule(client, title="外出", category="outing")
    create_schedule(client, title="私人", category="private")

    response = client.get("/api/schedules", params={"categories": "work,private"})

    assert [item["title"] for item in response.json()] == ["工作", "私人"]


def test_list_rejects_invalid_category_filter(client) -> None:
    response = client.get("/api/schedules", params={"categories": "work,study"})

    assert response.status_code == 422
    assert "study" in response.json()["detail"]


def test_list_filters_by_status(client) -> None:
    create_schedule(client, title="待进行")
    create_schedule(client, title="已完成", status="completed")
    create_schedule(client, title="已取消", status="cancelled")

    response = client.get("/api/schedules", params={"statuses": "completed,cancelled"})

    assert [item["title"] for item in response.json()] == ["已完成", "已取消"]


def test_list_filters_by_keyword_in_title_and_description(client) -> None:
    create_schedule(client, title="周会")
    create_schedule(client, title="学习", description="准备英语考试")
    create_schedule(client, title="旅行", description="去海边")

    title_hit = client.get("/api/schedules", params={"keyword": "周会"})
    description_hit = client.get("/api/schedules", params={"keyword": "英语"})

    assert [item["title"] for item in title_hit.json()] == ["周会"]
    assert [item["title"] for item in description_hit.json()] == ["学习"]


def test_list_keyword_ignores_only_whitespace(client) -> None:
    create_schedule(client, title="保留")

    response = client.get("/api/schedules", params={"keyword": "   "})

    assert len(response.json()) == 1


def test_list_keyword_treats_wildcards_literally(client) -> None:
    create_schedule(client, title="普通标题")
    create_schedule(client, title="100% 完成")

    response = client.get("/api/schedules", params={"keyword": "%"})

    assert [item["title"] for item in response.json()] == ["100% 完成"]


def test_patch_partial_update(client) -> None:
    created = create_schedule(client)

    response = client.patch(
        f"/api/schedules/{created['id']}",
        json={"title": "  已修改  ", "status": "completed"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "已修改"
    assert data["status"] == "completed"
    assert data["start_at"] == created["start_at"]
    assert data["end_at"] == created["end_at"]


def test_patch_validates_merged_time_range(client) -> None:
    created = create_schedule(client)

    response = client.patch(
        f"/api/schedules/{created['id']}",
        json={"end_at": "2026-11-05T08:00:00Z"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "结束时间必须晚于开始时间"


def test_patch_switch_to_all_day_normalizes_time(client) -> None:
    created = create_schedule(client)

    response = client.patch(
        f"/api/schedules/{created['id']}",
        json={"all_day": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["start_at"] == "2026-11-05T00:00:00Z"
    assert data["end_at"] == "2026-11-05T23:59:59.999999Z"


def test_patch_missing_schedule(client) -> None:
    response = client.patch("/api/schedules/999", json={"title": "不存在"})

    assert response.status_code == 404


def test_delete_schedule(client) -> None:
    created = create_schedule(client)

    response = client.delete(f"/api/schedules/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/schedules/{created['id']}").status_code == 404


def test_delete_missing_schedule(client) -> None:
    response = client.delete("/api/schedules/999")

    assert response.status_code == 404
