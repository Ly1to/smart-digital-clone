import tempfile
import unittest
from pathlib import Path

from music_source import MusicSourceError, MusicSourceStore


class MusicSourceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.default_playlist = self.root / "default.m3u"
        self.default_playlist.write_text(
            "#EXTM3U\n#EXTINF:180,Default Artist - Default Song\n01.mp3\n",
            encoding="utf-8",
        )
        self.config_path = self.root / "music-source.json"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_uses_default_source_before_import(self) -> None:
        store = MusicSourceStore(self.config_path, self.default_playlist)

        source = store.current()

        self.assertEqual(source.playlist.name, "default")
        self.assertEqual(source.playlist.songs[0].title, "Default Song")

    def test_imports_and_persists_directory(self) -> None:
        library = self.root / "My Music"
        library.mkdir()
        (library / "Near Light.mp3").touch()
        (library / "Night Walk.flac").touch()
        store = MusicSourceStore(self.config_path, self.default_playlist)

        imported = store.import_source(str(library))
        reloaded = MusicSourceStore(self.config_path, self.default_playlist).current()

        self.assertEqual(len(imported.playlist.songs), 2)
        self.assertEqual(reloaded.path, str(library.resolve()))
        self.assertEqual(reloaded.playlist.name, "My Music")

    def test_rejects_missing_path(self) -> None:
        store = MusicSourceStore(self.config_path, self.default_playlist)

        with self.assertRaises(MusicSourceError):
            store.import_source(str(self.root / "missing"))
