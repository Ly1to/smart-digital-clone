"""Persistent active music source selected from the web UI."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from music_recommender import Playlist, PlaylistError, load_playlist


class MusicSourceError(ValueError):
    """Raised when a requested local music source is invalid."""


@dataclass(frozen=True)
class MusicSource:
    path: str
    playlist: Playlist

    def to_dict(self) -> dict[str, Any]:
        return {
            "activePath": self.path,
            "playlist": self.playlist.summary(),
        }


class MusicSourceStore:
    def __init__(
        self,
        config_path: str | Path,
        default_path: str | Path,
    ):
        self.config_path = Path(config_path).expanduser().resolve()
        self.default_path = Path(default_path).expanduser().resolve()
        self._lock = threading.RLock()

    def _stored_path(self) -> Path:
        if not self.config_path.exists():
            return self.default_path
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MusicSourceError(f"无法读取音乐库配置：{error}") from error
        active_path = str(payload.get("activePath") or "").strip()
        if not active_path:
            return self.default_path
        return Path(active_path).expanduser().resolve()

    def current(self) -> MusicSource:
        with self._lock:
            path = self._stored_path()
            try:
                playlist = load_playlist(path)
            except PlaylistError as error:
                raise MusicSourceError(str(error)) from error
            return MusicSource(path=str(path), playlist=playlist)

    def import_source(self, requested_path: str) -> MusicSource:
        with self._lock:
            candidate = str(requested_path or "").strip()
            if not candidate:
                raise MusicSourceError("请输入本地音乐目录或歌单文件路径。")
            path = Path(candidate).expanduser().resolve()
            try:
                playlist = load_playlist(path)
            except PlaylistError as error:
                raise MusicSourceError(str(error)) from error
            source = MusicSource(path=str(path), playlist=playlist)

            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "activePath": source.path,
                "playlist": playlist.summary(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f"{self.config_path.name}.",
                suffix=".tmp",
                dir=self.config_path.parent,
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
                    json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
                    temporary_file.write("\n")
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())
                os.replace(temporary_name, self.config_path)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)

            return source
