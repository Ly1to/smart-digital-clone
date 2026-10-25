"""Track public GitHub repository activity as persisted work schedules."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from schedule_store import Schedule, ScheduleStore


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
LOOKBACK_DAYS = 21
DEFAULT_MAX_REPOSITORIES = 30


class GitHubTrackingError(RuntimeError):
    """Raised when GitHub profile or repository activity cannot be read."""


def parse_github_profile(profile: str | None) -> str:
    value = str(profile or "").strip().lstrip("@")
    if not value:
        raise GitHubTrackingError("请输入 GitHub 用户名或主页地址。")

    username = value
    if "://" in value:
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise GitHubTrackingError("仅支持 github.com 的个人主页。")
        username = parsed.path.strip("/").split("/", 1)[0]
    elif value.lower().startswith(("github.com/", "www.github.com/")):
        username = value.split("/", 2)[1]

    if not USERNAME_PATTERN.fullmatch(username):
        raise GitHubTrackingError("GitHub 用户名格式无效。")
    return username


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _local_zone() -> ZoneInfo:
    zone_name = os.environ.get("ORBIT_TIMEZONE", "Asia/Shanghai")
    try:
        return ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 12,
        opener: Callable[..., Any] = urlopen,
    ):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.base_url = (
            base_url or os.environ.get("GITHUB_API_URL", "https://api.github.com")
        ).rstrip("/")
        self.timeout = timeout
        self.opener = opener
        self.rate_limit_remaining: int | None = None

    def get_json(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Orbit-Schedule-Tracker",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"{self.base_url}{path}{query}", headers=headers)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining is not None:
                    self.rate_limit_remaining = int(remaining)
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            status_code = error.code
            error.close()
            if status_code == 404:
                raise GitHubTrackingError("未找到对应的 GitHub 用户或仓库。") from error
            if status_code in {403, 429}:
                raise GitHubTrackingError(
                    "GitHub API 请求受限。请稍后重试，或由后端设置 GITHUB_TOKEN。"
                ) from error
            raise GitHubTrackingError(
                f"GitHub API 请求失败（HTTP {status_code}）。"
            ) from error
        except (URLError, TimeoutError) as error:
            raise GitHubTrackingError("无法连接 GitHub API，请检查网络。") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GitHubTrackingError("GitHub API 返回了无效响应。") from error


@dataclass(frozen=True)
class TrackedRepository:
    schedule: Schedule
    full_name: str
    html_url: str
    commit_count: int
    latest_commit_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "scheduleId": self.schedule.id,
            "fullName": self.full_name,
            "htmlUrl": self.html_url,
            "commitCount": self.commit_count,
            "latestCommitAt": self.latest_commit_at,
        }


class GitHubTracker:
    def __init__(
        self,
        client: GitHubClient | None = None,
        lookback_days: int = LOOKBACK_DAYS,
        max_repositories: int | None = None,
        now: Callable[[], datetime] | None = None,
    ):
        self.client = client or GitHubClient()
        self.lookback_days = lookback_days
        self.max_repositories = max_repositories or int(
            os.environ.get("GITHUB_MAX_REPOSITORIES", DEFAULT_MAX_REPOSITORIES)
        )
        self.now = now or (lambda: datetime.now(timezone.utc))

    def discover(self, profile: str) -> dict[str, object]:
        username = parse_github_profile(profile)
        user = self.client.get_json(f"/users/{quote(username)}")
        if not isinstance(user, dict) or not user.get("login"):
            raise GitHubTrackingError("GitHub 用户信息无效。")
        canonical_login = str(user["login"])

        now = self.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        cutoff = now.astimezone(timezone.utc) - timedelta(days=self.lookback_days)
        repositories = self.client.get_json(
            f"/users/{quote(canonical_login)}/repos",
            {
                "type": "owner",
                "sort": "pushed",
                "direction": "desc",
                "per_page": 100,
            },
        )
        if not isinstance(repositories, list):
            raise GitHubTrackingError("GitHub 仓库列表格式无效。")

        candidates = []
        for repository in repositories:
            if not isinstance(repository, dict) or repository.get("private"):
                continue
            pushed_at = repository.get("pushed_at")
            if not pushed_at:
                continue
            try:
                if _parse_timestamp(str(pushed_at)) < cutoff:
                    continue
            except ValueError:
                continue
            candidates.append(repository)

        candidate_count = len(candidates)
        selected = candidates[: self.max_repositories]
        tracked: list[TrackedRepository] = []
        local_zone = _local_zone()
        target_workday = now.astimezone(local_zone)
        while target_workday.weekday() >= 5:
            target_workday -= timedelta(days=1)

        for index, repository in enumerate(selected):
            full_name = str(repository.get("full_name") or "")
            repo_id = repository.get("id")
            if not full_name or repo_id is None:
                continue
            commits = self.client.get_json(
                f"/repos/{quote(full_name, safe='/')}/commits",
                {
                    "author": canonical_login,
                    "since": cutoff.isoformat(),
                    "per_page": 100,
                },
            )
            if not isinstance(commits, list) or not commits:
                continue

            latest = commits[0]
            commit_data = latest.get("commit", {}) if isinstance(latest, dict) else {}
            committed_at = (
                commit_data.get("committer", {}).get("date")
                or commit_data.get("author", {}).get("date")
            )
            if not committed_at:
                continue
            try:
                local_commit_time = _parse_timestamp(str(committed_at)).astimezone(
                    local_zone
                )
            except ValueError:
                continue

            message = str(commit_data.get("message") or "").splitlines()[0][:100]
            repo_name = str(repository.get("name") or full_name.split("/")[-1])
            schedule = Schedule.from_dict(
                {
                    "id": f"github-{repo_id}",
                    "type": "work",
                    "title": repo_name,
                    "date": target_workday.date().isoformat(),
                    "startTime": local_commit_time.strftime("%H:%M"),
                    "durationMinutes": 60,
                    "description": (
                        f"GitHub · 最近提交 {local_commit_time:%m-%d %H:%M}"
                        f" · 近{self.lookback_days}天 {len(commits)} 次提交"
                        + (f" · {message}" if message else "")
                    )[:240],
                    "status": "planned",
                    "featured": False,
                    "source": "github",
                    "sourceUrl": str(repository.get("html_url") or ""),
                },
                allow_missing_id=True,
            )
            tracked.append(
                TrackedRepository(
                    schedule=schedule,
                    full_name=full_name,
                    html_url=str(repository.get("html_url") or ""),
                    commit_count=len(commits),
                    latest_commit_at=str(committed_at),
                )
            )

        return {
            "profile": {
                "login": canonical_login,
                "htmlUrl": str(user.get("html_url") or f"https://github.com/{canonical_login}"),
                "avatarUrl": str(user.get("avatar_url") or ""),
            },
            "lookbackDays": self.lookback_days,
            "candidateCount": candidate_count,
            "scannedCount": len(selected),
            "truncated": candidate_count > len(selected),
            "repositories": tracked,
            "rateLimitRemaining": self.client.rate_limit_remaining,
        }


def sync_github_schedules(
    tracker: GitHubTracker,
    store: ScheduleStore,
    profile: str,
) -> dict[str, object]:
    discovery = tracker.discover(profile)
    tracked_repositories: list[TrackedRepository] = discovery["repositories"]  # type: ignore[assignment]
    existing = {schedule.id: schedule for schedule in store.list()}
    discovered_ids: set[str] = set()
    created = 0
    updated = 0

    for tracked in tracked_repositories:
        discovered_ids.add(tracked.schedule.id)
        previous = existing.get(tracked.schedule.id)
        if previous is None:
            store.create(tracked.schedule.to_dict())
            created += 1
            continue
        updates = tracked.schedule.to_dict()
        updates.pop("createdAt", None)
        updates.pop("updatedAt", None)
        store.update(tracked.schedule.id, updates)
        updated += 1

    removed = 0
    for schedule in existing.values():
        if schedule.source == "github" and schedule.id not in discovered_ids:
            store.delete(schedule.id)
            removed += 1

    return {
        "profile": discovery["profile"],
        "lookbackDays": discovery["lookbackDays"],
        "candidateCount": discovery["candidateCount"],
        "scannedCount": discovery["scannedCount"],
        "truncated": discovery["truncated"],
        "rateLimitRemaining": discovery["rateLimitRemaining"],
        "created": created,
        "updated": updated,
        "removed": removed,
        "repositories": [
            repository.to_dict() for repository in tracked_repositories
        ],
    }
