#!/usr/bin/env python3
"""Read a local music playlist and serve random personal-daily recommendations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import parse_qs, unquote, urlparse


AUDIO_EXTENSIONS = {
    ".aac",
    ".aiff",
    ".alac",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
    ".wma",
}


class PlaylistError(ValueError):
    """Raised when a playlist cannot be read or contains no supported tracks."""


@dataclass(frozen=True)
class Song:
    title: str
    artist: str = "未知艺术家"
    album: str = ""
    duration: str = ""
    file: str = ""

    @property
    def id(self) -> str:
        identity = "\0".join((self.artist, self.title, self.file))
        return hashlib.sha1(identity.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "file": self.file,
        }


@dataclass(frozen=True)
class Playlist:
    name: str
    source: str
    songs: tuple[Song, ...]

    def summary(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source": self.source,
            "total": len(self.songs),
        }


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1")


def _format_duration(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        total = max(0, int(value))
        return f"{total // 60}:{total % 60:02d}"
    duration = str(value).strip()
    if duration.startswith("-"):
        return ""
    if duration.isdigit():
        total = int(duration)
        return f"{total // 60}:{total % 60:02d}"
    return duration


def _split_display_name(value: str, fallback: str = "") -> tuple[str, str]:
    display = value.strip()
    if " - " in display:
        artist, title = display.split(" - ", 1)
        return artist.strip() or "未知艺术家", title.strip() or fallback
    return "未知艺术家", display or fallback


def _title_from_file(value: str) -> str:
    parsed_path = urlparse(value).path if "://" in value else value
    return Path(unquote(parsed_path)).stem.strip()


def _song_from_mapping(item: dict[str, object]) -> Song:
    file_value = str(
        item.get("file")
        or item.get("path")
        or item.get("url")
        or item.get("location")
        or ""
    ).strip()
    display = str(
        item.get("display")
        or item.get("track")
        or item.get("song")
        or ""
    ).strip()
    fallback_title = _title_from_file(file_value) if file_value else "未命名歌曲"
    display_artist, display_title = _split_display_name(display, fallback_title)

    title = str(
        item.get("title")
        or item.get("name")
        or display_title
        or fallback_title
    ).strip()
    artist = str(
        item.get("artist")
        or item.get("creator")
        or item.get("author")
        or display_artist
        or "未知艺术家"
    ).strip()
    return Song(
        title=title or "未命名歌曲",
        artist=artist or "未知艺术家",
        album=str(item.get("album") or "").strip(),
        duration=_format_duration(item.get("duration") or item.get("length")),
        file=file_value,
    )


def _load_directory(path: Path) -> tuple[Song, ...]:
    songs = []
    for audio_file in sorted(path.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not audio_file.is_file() or audio_file.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        songs.append(
            Song(
                title=audio_file.stem,
                artist=audio_file.parent.name if audio_file.parent != path else "本地曲库",
                file=str(audio_file),
            )
        )
    return tuple(songs)


def _load_m3u(path: Path) -> tuple[Song, ...]:
    songs: list[Song] = []
    pending_duration = ""
    pending_display = ""

    for raw_line in _read_text(path).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper().startswith("#EXTINF:"):
            metadata = line.split(":", 1)[1]
            duration, _, display = metadata.partition(",")
            pending_duration = _format_duration(duration.strip())
            pending_display = display.strip()
            continue
        if line.startswith("#"):
            continue

        fallback = _title_from_file(line)
        artist, title = _split_display_name(pending_display, fallback)
        songs.append(
            Song(
                title=title,
                artist=artist,
                duration=pending_duration,
                file=line,
            )
        )
        pending_duration = ""
        pending_display = ""
    return tuple(songs)


def _load_pls(path: Path) -> tuple[Song, ...]:
    entries: dict[str, dict[str, str]] = {}
    for raw_line in _read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        if key.startswith("file"):
            number = key[4:]
            entries.setdefault(number, {})["file"] = value.strip()
        elif key.startswith("title"):
            number = key[5:]
            entries.setdefault(number, {})["display"] = value.strip()
        elif key.startswith("length"):
            number = key[6:]
            entries.setdefault(number, {})["duration"] = value.strip()

    return tuple(
        _song_from_mapping(entry)
        for _, entry in sorted(entries.items(), key=lambda item: item[0])
        if entry.get("file") or entry.get("display")
    )


def _load_json(path: Path) -> tuple[Song, ...]:
    data = json.loads(_read_text(path))
    if isinstance(data, dict):
        tracks = data.get("tracks") or data.get("songs") or data.get("items") or []
    elif isinstance(data, list):
        tracks = data
    else:
        raise PlaylistError("JSON 歌单必须是数组，或包含 tracks/songs/items 数组的对象。")

    songs = []
    for item in tracks:
        if isinstance(item, str):
            artist, title = _split_display_name(item)
            songs.append(Song(title=title, artist=artist))
        elif isinstance(item, dict):
            songs.append(_song_from_mapping(item))
    return tuple(songs)


def _load_csv(path: Path) -> tuple[Song, ...]:
    rows = csv.DictReader(io.StringIO(_read_text(path)))
    return tuple(
        _song_from_mapping(
            {str(key).strip().lower(): value for key, value in row.items()}
        )
        for row in rows
    )


def _load_text(path: Path) -> tuple[Song, ...]:
    songs = []
    for raw_line in _read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        artist, title = _split_display_name(line, _title_from_file(line))
        songs.append(Song(title=title, artist=artist, file=line))
    return tuple(songs)


def load_playlist(source: str | Path) -> Playlist:
    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise PlaylistError(f"歌单路径不存在：{path}")

    if path.is_dir():
        songs = _load_directory(path)
    else:
        suffix = path.suffix.lower()
        if suffix in {".m3u", ".m3u8"}:
            songs = _load_m3u(path)
        elif suffix == ".pls":
            songs = _load_pls(path)
        elif suffix == ".json":
            songs = _load_json(path)
        elif suffix == ".csv":
            songs = _load_csv(path)
        else:
            songs = _load_text(path)

    if not songs:
        raise PlaylistError(f"歌单中没有可读取的歌曲：{path}")
    return Playlist(name=path.stem, source=str(path), songs=songs)


def pick_random_song(
    songs: Sequence[Song],
    avoid_id: str = "",
    rng: random.Random | random.SystemRandom | None = None,
) -> Song:
    if not songs:
        raise PlaylistError("歌单中没有可推荐的歌曲。")
    alternatives = [song for song in songs if song.id != avoid_id]
    candidates = alternatives or list(songs)
    return (rng or random.SystemRandom()).choice(candidates)


def recommendation_payload(
    playlist: Playlist,
    avoid_id: str = "",
) -> dict[str, object]:
    song = pick_random_song(playlist.songs, avoid_id=avoid_id)
    return {
        "recommendation": song.to_dict(),
        "playlist": playlist.summary(),
        "recommended_at": datetime.now(timezone.utc).isoformat(),
    }


class MusicRequestHandler(BaseHTTPRequestHandler):
    server_version = "OrbitMusic/1.0"

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        request = urlparse(self.path)
        playlist_path = getattr(self.server, "playlist_path")
        try:
            playlist = load_playlist(playlist_path)
            if request.path == "/api/recommendation":
                avoid_id = parse_qs(request.query).get("avoid", [""])[0]
                self._send_json(200, recommendation_payload(playlist, avoid_id))
                return
            if request.path == "/api/playlist":
                self._send_json(200, playlist.summary())
                return
            if request.path == "/health":
                self._send_json(
                    200,
                    {"status": "ok", "playlist": playlist.summary()},
                )
                return
            self._send_json(404, {"error": "Not found"})
        except (PlaylistError, json.JSONDecodeError, OSError) as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args: object) -> None:
        print(f"[music-api] {self.address_string()} - {format % args}")


def serve(playlist_path: str, host: str, port: int) -> None:
    playlist = load_playlist(playlist_path)
    server = ThreadingHTTPServer((host, port), MusicRequestHandler)
    server.playlist_path = playlist_path
    print(
        f"Music API: http://{host}:{port}\n"
        f"Playlist: {playlist.name} ({len(playlist.songs)} tracks)\n"
        "Press Ctrl+C to stop."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping music API.")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="读取本地歌单并随机推荐一首歌。",
    )
    parser.add_argument(
        "--playlist",
        default=os.environ.get("MUSIC_PLAYLIST", "playlists/daily.m3u"),
        help="歌单文件或音乐目录，也可通过 MUSIC_PLAYLIST 环境变量设置。",
    )
    parser.add_argument("--serve", action="store_true", help="启动本地 HTTP API。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--avoid", default="", help="避免重复推荐的上一次歌曲 ID。")
    parser.add_argument("--list", action="store_true", help="输出歌单中的全部歌曲。")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.serve:
        serve(args.playlist, args.host, args.port)
        return 0

    try:
        playlist = load_playlist(args.playlist)
    except (PlaylistError, json.JSONDecodeError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1

    if args.list:
        payload = {
            "playlist": playlist.summary(),
            "songs": [song.to_dict() for song in playlist.songs],
        }
    else:
        payload = recommendation_payload(playlist, avoid_id=args.avoid)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
