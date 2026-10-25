import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from github_tracker import (
    GitHubClient,
    GitHubTracker,
    GitHubTrackingError,
    parse_github_profile,
    sync_github_schedules,
)
from schedule_store import ScheduleStore


class FakeGitHubClient:
    def __init__(self) -> None:
        self.rate_limit_remaining = 42

    def get_json(self, path: str, params=None):
        if path == "/users/octocat":
            return {
                "login": "octocat",
                "html_url": "https://github.com/octocat",
                "avatar_url": "https://example.com/avatar.png",
            }
        if path == "/users/octocat/repos":
            return [
                {
                    "id": 1001,
                    "name": "active-project",
                    "full_name": "octocat/active-project",
                    "html_url": "https://github.com/octocat/active-project",
                    "pushed_at": "2026-10-24T08:00:00Z",
                },
                {
                    "id": 1002,
                    "name": "old-project",
                    "full_name": "octocat/old-project",
                    "html_url": "https://github.com/octocat/old-project",
                    "pushed_at": "2026-09-01T08:00:00Z",
                },
            ]
        if path == "/repos/octocat/active-project/commits":
            return [
                {
                    "commit": {
                        "message": "Improve schedule parser",
                        "committer": {"date": "2026-10-23T03:30:00Z"},
                    }
                }
            ]
        raise AssertionError(f"Unexpected GitHub path: {path}")


class GitHubTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.store = ScheduleStore(self.root / "schedules.json")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_parses_profile_url_and_username(self) -> None:
        self.assertEqual(parse_github_profile("https://github.com/octocat/"), "octocat")
        self.assertEqual(parse_github_profile("@octocat"), "octocat")
        with self.assertRaises(GitHubTrackingError):
            parse_github_profile("https://example.com/octocat")

    def test_discovers_recent_public_repository_commits(self) -> None:
        tracker = GitHubTracker(
            client=FakeGitHubClient(),
            now=lambda: datetime(2026, 10, 25, tzinfo=timezone.utc),
        )

        result = tracker.discover("https://github.com/octocat")

        self.assertEqual(result["candidateCount"], 1)
        self.assertEqual(len(result["repositories"]), 1)
        repository = result["repositories"][0]
        self.assertEqual(repository.full_name, "octocat/active-project")
        self.assertEqual(repository.schedule.type, "work")
        self.assertEqual(repository.schedule.source, "github")
        self.assertEqual(repository.schedule.date, "2026-10-23")

    def test_sync_is_idempotent_and_removes_stale_github_items(self) -> None:
        tracker = GitHubTracker(
            client=FakeGitHubClient(),
            now=lambda: datetime(2026, 10, 25, tzinfo=timezone.utc),
        )
        stale = {
            "id": "github-stale",
            "type": "work",
            "title": "stale",
            "date": "2026-10-20",
            "startTime": "09:00",
            "durationMinutes": 30,
            "source": "github",
        }
        self.store.create(stale)

        first = sync_github_schedules(tracker, self.store, "octocat")
        second = sync_github_schedules(tracker, self.store, "octocat")

        self.assertEqual(first["created"], 1)
        self.assertEqual(first["removed"], 1)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["updated"], 1)
        self.assertEqual(len(self.store.list()), 1)

    def test_client_reports_rate_limit(self) -> None:
        from urllib.error import HTTPError

        def limited_opener(*args, **kwargs):
            raise HTTPError(
                url="https://api.github.com",
                code=403,
                msg="rate limited",
                hdrs=None,
                fp=None,
            )

        client = GitHubClient(opener=limited_opener)
        with self.assertRaisesRegex(GitHubTrackingError, "请求受限"):
            client.get_json("/users/octocat")

    def test_client_sends_frontend_token_to_github(self) -> None:
        captured_headers = {}

        class FakeResponse:
            headers = {"X-RateLimit-Remaining": "4999"}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"{}"

        def opener(request, timeout):
            captured_headers.update(request.headers)
            return FakeResponse()

        client = GitHubClient(token="github_pat_frontend", opener=opener)

        client.get_json("/user")

        self.assertEqual(
            captured_headers["Authorization"],
            "Bearer github_pat_frontend",
        )


if __name__ == "__main__":
    unittest.main()
