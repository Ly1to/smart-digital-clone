from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ScheduleCategory, StagedStatus
from app.models.staging import StagedSchedule
from app.services import staging_service
from app.services.exceptions import GithubApiError, GithubConfigurationError
from app.services.sync_lock import synchronized

GITHUB_API_VERSION = "2022-11-28"
USER_AGENT = "digital-clone-schedule/0.1"
MAX_PAGES = 3
logger = logging.getLogger(__name__)


@dataclass
class RepoUpdate:
    repo: str
    html_url: str
    latest_at: datetime
    latest_key: str
    commit_count: int = 0
    commits: list[str] = field(default_factory=list)
    pull_requests: list[str] = field(default_factory=list)
    releases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    event_count: int = 0

    @property
    def source_ref(self) -> str:
        return f"github:{self.repo}:{self.latest_key}"[:255]

    @property
    def title(self) -> str:
        return f"GitHub 更新：{self.repo}"[:200]

    def description(self, lookback_days: int) -> str:
        lines = [f"GitHub 最近 {lookback_days} 天动态："]
        if self.commit_count:
            lines.append(f"- 提交：{self.commit_count} 次")
        if self.commits:
            lines.append("最近提交：")
            lines.extend(f"- {message}" for message in self.commits[:8])
        if self.pull_requests:
            lines.append("Pull Request：")
            lines.extend(f"- {item}" for item in self.pull_requests[:3])
        if self.releases:
            lines.append("发布：")
            lines.extend(f"- {item}" for item in self.releases[:3])
        if self.tags:
            lines.append("标签：")
            lines.extend(f"- {item}" for item in self.tags[:3])
        return "\n".join(lines)[:5000]

    def source_meta(self, lookback_days: int) -> dict:
        return {
            "repo": self.repo,
            "commit_count": self.commit_count,
            "latest_key": self.latest_key,
            "event_count": self.event_count,
            "lookback_days": lookback_days,
        }


@dataclass
class GithubSyncResult:
    scanned_events: int
    created: int
    updated: int
    skipped: int
    no_slot: int

    @property
    def message(self) -> str:
        if self.scanned_events == 0:
            return "最近没有可用的 GitHub 动态"
        if self.created == 0 and self.updated == 0 and self.skipped == 0:
            return "最近没有新的仓库动态"
        message = (
            f"已扫描 {self.scanned_events} 条 GitHub 动态："
            f"新增 {self.created} 条，更新 {self.updated} 条"
        )
        if self.skipped:
            message += f"，已处理过 {self.skipped} 条"
        if self.no_slot:
            message += f"，{self.no_slot} 条今天没有空闲时间"
        return message


def _parse_github_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_events(
    *,
    username: str,
    token: str | None,
    lookback_days: int,
    api_url: str,
    now: datetime,
    client: httpx.Client | None = None,
) -> list[dict]:
    if not username and not token:
        raise GithubConfigurationError()

    cutoff = now - timedelta(days=lookback_days)
    endpoint = "/user/events" if token else f"/users/{username}/events/public"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    owns_client = client is None
    http_client = client or httpx.Client(timeout=15)
    events: list[dict] = []
    try:
        for page in range(1, MAX_PAGES + 1):
            try:
                response = http_client.get(
                    f"{api_url.rstrip('/')}{endpoint}",
                    headers=headers,
                    params={"per_page": 100, "page": page},
                )
            except httpx.HTTPError as exc:
                raise GithubApiError(f"无法连接 GitHub API：{exc}") from exc

            if response.status_code == 401:
                raise GithubApiError("GitHub Token 无效或已过期")
            if response.status_code == 404:
                raise GithubApiError(f"GitHub 用户不存在：{username}")
            if response.status_code == 403:
                raise GithubApiError("GitHub API 访问受限，请检查 Token 权限或稍后重试")
            if response.status_code >= 400:
                raise GithubApiError(f"GitHub API 请求失败（{response.status_code}）")

            page_events = response.json()
            if not isinstance(page_events, list):
                raise GithubApiError("GitHub API 返回了无法识别的数据")
            events.extend(page_events)
            if len(page_events) < 100:
                break
            oldest = min(
                (_parse_github_time(event["created_at"]) for event in page_events),
                default=now,
            )
            if oldest < cutoff:
                break
    finally:
        if owns_client:
            http_client.close()

    return [event for event in events if _parse_github_time(event["created_at"]) >= cutoff]


def group_events(events: list[dict]) -> list[RepoUpdate]:
    updates: dict[str, RepoUpdate] = {}

    for event in events:
        repo_info = event.get("repo") or {}
        repo = repo_info.get("name")
        if not repo:
            continue
        created_at = _parse_github_time(event["created_at"])
        update = updates.get(repo)
        if update is None:
            update = RepoUpdate(
                repo=repo,
                html_url=f"https://github.com/{repo}",
                latest_at=created_at,
                latest_key=str(event.get("id", created_at.isoformat())),
            )
            updates[repo] = update
        if created_at >= update.latest_at:
            update.latest_at = created_at
            payload = event.get("payload") or {}
            if event.get("type") == "PushEvent":
                update.latest_key = payload.get("head") or update.latest_key
        update.event_count += 1

        event_type = event.get("type")
        payload = event.get("payload") or {}

        if event_type == "PushEvent":
            commits = payload.get("commits") or []
            update.commit_count += len(commits) or 1
            for commit in commits:
                message = (commit.get("message") or "").splitlines()[0].strip()
                if message and message not in update.commits:
                    update.commits.append(message)
            if payload.get("head"):
                update.latest_key = payload["head"]
        elif event_type == "PullRequestEvent":
            action = payload.get("action")
            pull_request = payload.get("pull_request") or {}
            title = pull_request.get("title")
            if not title:
                continue
            if action == "closed" and pull_request.get("merged"):
                update.pull_requests.append(f"合并：{title}")
            elif action in {"opened", "reopened", "closed"}:
                action_label = {"opened": "打开", "reopened": "重新打开", "closed": "关闭"}[action]
                update.pull_requests.append(f"{action_label}：{title}")
        elif event_type == "ReleaseEvent":
            release = payload.get("release") or {}
            name = release.get("name") or release.get("tag_name")
            if name:
                update.releases.append(name)
        elif event_type == "CreateEvent" and payload.get("ref_type") == "tag":
            ref = payload.get("ref")
            if ref:
                update.tags.append(ref)

    return sorted(updates.values(), key=lambda update: update.latest_at, reverse=True)


@synchronized
def sync_github(
    db: Session,
    *,
    username: str,
    token: str | None,
    lookback_days: int,
    api_url: str,
    duration_minutes: int,
    day_start_hour: int,
    day_end_hour: int,
    now: datetime | None = None,
    client: httpx.Client | None = None,
) -> GithubSyncResult:
    current = now or staging_service.local_now()
    events = fetch_events(
        username=username,
        token=token,
        lookback_days=lookback_days,
        api_url=api_url,
        now=current,
        client=client,
    )
    updates = group_events(events)

    created = 0
    updated = 0
    skipped = 0
    no_slot = 0

    for update in updates:
        existing_ref = db.scalar(
            select(StagedSchedule).where(
                StagedSchedule.source == "github",
                StagedSchedule.source_ref == update.source_ref,
            )
        )
        if existing_ref is not None and existing_ref.status != StagedStatus.pending:
            skipped += 1
            continue

        staged = existing_ref
        if staged is None:
            staged = db.scalar(
                select(StagedSchedule).where(
                    StagedSchedule.source == "github",
                    StagedSchedule.status == StagedStatus.pending,
                    StagedSchedule.source_ref.startswith(f"github:{update.repo}:", autoescape=True),
                )
            )

        if staged is None:
            staged = staging_service.new_staged(
                source="github",
                source_ref=update.source_ref,
                source_url=update.html_url or None,
                title=update.title,
                category=ScheduleCategory.work,
                description=update.description(lookback_days),
                all_day=False,
                location=None,
                source_meta=update.source_meta(lookback_days),
            )
            db.add(staged)
            created += 1
        else:
            updated += 1

        staged.source_ref = update.source_ref
        staged.source_url = update.html_url or None
        staged.title = update.title
        staged.category = ScheduleCategory.work
        staged.description = update.description(lookback_days)
        staged.all_day = False
        staged.location = None
        staged.source_meta = update.source_meta(lookback_days)
        db.flush()

        slot = staging_service.assign_slot(
            db,
            staged,
            now=current,
            duration_minutes=duration_minutes,
            day_start_hour=day_start_hour,
            day_end_hour=day_end_hour,
        )
        if slot is None:
            no_slot += 1
        db.flush()

    db.commit()
    return GithubSyncResult(
        scanned_events=len(events),
        created=created,
        updated=updated,
        skipped=skipped,
        no_slot=no_slot,
    )


def run_auto_sync_once() -> None:
    """在后台线程中执行一次同步，失败只记录日志。"""
    from app.core.config import settings
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        result = sync_github(
            db,
            username=settings.github_username,
            token=settings.github_token,
            lookback_days=settings.github_lookback_days,
            api_url=settings.github_api_url,
            duration_minutes=settings.auto_schedule_duration_minutes,
            day_start_hour=settings.auto_schedule_day_start_hour,
            day_end_hour=settings.auto_schedule_day_end_hour,
        )
    logger.info("GitHub 自动同步完成：%s", result.message)


async def auto_sync_loop() -> None:
    """每 N 分钟把 GitHub 更新同步到暂存区；0 表示关闭。"""
    from app.core.config import settings

    await asyncio.sleep(10)
    while True:
        try:
            await asyncio.to_thread(run_auto_sync_once)
        except Exception:
            logger.exception("GitHub 自动同步失败")
        await asyncio.sleep(max(60, settings.github_auto_sync_minutes * 60))
