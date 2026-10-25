#!/usr/bin/env python3
"""Local API for persistent schedules and music recommendations."""

from __future__ import annotations

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote, urlparse

from music_recommender import PlaylistError, recommendation_payload
from music_source import MusicSourceError, MusicSourceStore
from github_tracker import (
    GitHubClient,
    GitHubTracker,
    GitHubTrackingError,
    sync_github_schedules,
)
from schedule_store import ScheduleError, ScheduleNotFound, ScheduleStore


def load_local_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("\"'")


class OrbitRequestHandler(BaseHTTPRequestHandler):
    server_version = "OrbitAPI/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as error:
            raise ScheduleError("Content-Length 无效。") from error
        if length <= 0 or length > 1_000_000:
            raise ScheduleError("请求体不能为空或超过 1 MB。")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ScheduleError("请求体必须是有效的 UTF-8 JSON。") from error
        if not isinstance(payload, dict):
            raise ScheduleError("请求体必须是 JSON 对象。")
        return payload

    def _schedule_id(self, path: str) -> str | None:
        prefix = "/api/schedules/"
        if not path.startswith(prefix):
            return None
        schedule_id = unquote(path[len(prefix) :]).strip("/")
        return schedule_id or None

    def _music_playlist(self):
        return getattr(self.server, "music_source_store").current().playlist

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        store = getattr(self.server, "schedule_store")
        try:
            if request.path == "/api/schedules":
                self._send_json(
                    200,
                    {
                        "items": [schedule.to_dict() for schedule in store.list()],
                        "storage": store.summary(),
                    },
                )
                return

            schedule_id = self._schedule_id(request.path)
            if schedule_id:
                self._send_json(200, store.get(schedule_id).to_dict())
                return

            if request.path == "/api/recommendation":
                avoid_id = parse_qs(request.query).get("avoid", [""])[0]
                self._send_json(
                    200,
                    recommendation_payload(self._music_playlist(), avoid_id),
                )
                return

            if request.path == "/api/music/source":
                source = getattr(self.server, "music_source_store").current()
                self._send_json(200, source.to_dict())
                return

            if request.path == "/api/playlist":
                self._send_json(200, self._music_playlist().summary())
                return

            if request.path == "/health":
                try:
                    music_status: dict[str, Any] = {
                        "status": "ok",
                        "playlist": self._music_playlist().summary(),
                    }
                except (PlaylistError, MusicSourceError) as error:
                    music_status = {"status": "error", "error": str(error)}
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "schedules": store.summary(),
                        "music": music_status,
                        "github": {
                            "tokenConfigured": bool(os.environ.get("GITHUB_TOKEN")),
                        },
                    },
                )
                return

            self._send_json(404, {"error": "Not found"})
        except ScheduleNotFound as error:
            self._send_json(404, {"error": str(error)})
        except ScheduleError as error:
            self._send_json(400, {"error": str(error)})
        except PlaylistError as error:
            self._send_json(500, {"error": str(error)})
        except MusicSourceError as error:
            self._send_json(500, {"error": str(error)})
        except OSError as error:
            self._send_json(500, {"error": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        if request.path == "/api/github/sync":
            store = getattr(self.server, "schedule_store")
            try:
                payload = self._read_json()
                profile = str(payload.get("profile") or "").strip()
                token = str(payload.get("token") or "").strip()
                tracker = GitHubTracker(client=GitHubClient(token=token or None))
                with getattr(self.server, "github_sync_lock"):
                    result = sync_github_schedules(tracker, store, profile)
                self._send_json(
                    200,
                    {
                        **result,
                        "schedules": [item.to_dict() for item in store.list()],
                    },
                )
            except GitHubTrackingError as error:
                self._send_json(502, {"error": str(error)})
            except ScheduleError as error:
                self._send_json(400, {"error": str(error)})
            except OSError as error:
                self._send_json(500, {"error": str(error)})
            return

        if request.path == "/api/music/source":
            try:
                payload = self._read_json()
                source = getattr(
                    self.server, "music_source_store"
                ).import_source(str(payload.get("path") or ""))
                self._send_json(200, source.to_dict())
            except MusicSourceError as error:
                self._send_json(400, {"error": str(error)})
            except ScheduleError as error:
                self._send_json(400, {"error": str(error)})
            except OSError as error:
                self._send_json(500, {"error": str(error)})
            return

        if request.path != "/api/schedules":
            self._send_json(404, {"error": "Not found"})
            return
        store = getattr(self.server, "schedule_store")
        try:
            schedule = store.create(self._read_json())
            self._send_json(201, schedule.to_dict())
        except ScheduleError as error:
            self._send_json(400, {"error": str(error)})
        except OSError as error:
            self._send_json(500, {"error": str(error)})

    def do_PATCH(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        schedule_id = self._schedule_id(request.path)
        if not schedule_id:
            self._send_json(404, {"error": "Not found"})
            return
        store = getattr(self.server, "schedule_store")
        try:
            schedule = store.update(schedule_id, self._read_json())
            self._send_json(200, schedule.to_dict())
        except ScheduleNotFound as error:
            self._send_json(404, {"error": str(error)})
        except ScheduleError as error:
            self._send_json(400, {"error": str(error)})
        except OSError as error:
            self._send_json(500, {"error": str(error)})

    def do_DELETE(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        schedule_id = self._schedule_id(request.path)
        if not schedule_id:
            self._send_json(404, {"error": "Not found"})
            return
        store = getattr(self.server, "schedule_store")
        try:
            store.delete(schedule_id)
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except ScheduleNotFound as error:
            self._send_json(404, {"error": str(error)})
        except ScheduleError as error:
            self._send_json(400, {"error": str(error)})
        except OSError as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args: object) -> None:
        print(f"[orbit-api] {self.address_string()} - {format % args}")


def serve(
    playlist_path: str,
    music_config_path: str,
    schedule_path: str,
    seed_path: str,
    host: str,
    port: int,
) -> None:
    store = ScheduleStore(schedule_path, seed_path)
    server = ThreadingHTTPServer((host, port), OrbitRequestHandler)
    server.schedule_store = store
    server.music_source_store = MusicSourceStore(music_config_path, playlist_path)
    server.github_sync_lock = threading.Lock()

    try:
        source = server.music_source_store.current()
        music_summary = (
            f"{source.playlist.name} ({len(source.playlist.songs)} tracks) "
            f"from {source.path}"
        )
    except (PlaylistError, MusicSourceError) as error:
        music_summary = f"unavailable: {error}"

    summary = store.summary()
    print(
        f"Orbit API: http://{host}:{port}\n"
        f"Schedules: {summary['total']} ({schedule_path})\n"
        f"Music: {music_summary}\n"
        f"GitHub token: {'configured' if os.environ.get('GITHUB_TOKEN') else 'not configured'}\n"
        "Press Ctrl+C to stop."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Orbit API.")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orbit 本地日程与歌单 API。")
    parser.add_argument(
        "--playlist",
        default=os.environ.get("MUSIC_PLAYLIST", "playlists/daily.m3u"),
    )
    parser.add_argument(
        "--music-config",
        default=os.environ.get("MUSIC_SOURCE_CONFIG", "data/music-source.json"),
    )
    parser.add_argument(
        "--schedule-db",
        default=os.environ.get("SCHEDULE_DB", "data/schedules.json"),
    )
    parser.add_argument(
        "--schedule-seed",
        default=os.environ.get("SCHEDULE_SEED", "data/schedules.seed.json"),
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--serve", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    load_local_env()
    args = build_parser().parse_args(argv)
    if args.serve:
        serve(
            args.playlist,
            args.music_config,
            args.schedule_db,
            args.schedule_seed,
            args.host,
            args.port,
        )
        return 0

    store = ScheduleStore(args.schedule_db, args.schedule_seed)
    print(
        json.dumps(
            {
                "schedules": store.summary(),
                "items": [item.to_dict() for item in store.list()],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
