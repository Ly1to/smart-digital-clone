import json
import tempfile
import unittest
from pathlib import Path

from music_recommender import load_playlist, pick_random_song


class PlaylistReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_reads_m3u_metadata(self) -> None:
        playlist_path = self.root / "daily.m3u"
        playlist_path.write_text(
            "#EXTM3U\n"
            "#EXTINF:222,Ólafur Arnalds - Near Light\n"
            "music/01.mp3\n"
            "#EXTINF:-1,落日飞车 - My Jinji\n"
            "music/02.flac\n",
            encoding="utf-8",
        )

        playlist = load_playlist(playlist_path)

        self.assertEqual(len(playlist.songs), 2)
        self.assertEqual(playlist.songs[0].artist, "Ólafur Arnalds")
        self.assertEqual(playlist.songs[0].title, "Near Light")
        self.assertEqual(playlist.songs[0].duration, "3:42")
        self.assertEqual(playlist.songs[1].artist, "落日飞车")

    def test_reads_json_tracks(self) -> None:
        playlist_path = self.root / "mix.json"
        playlist_path.write_text(
            json.dumps(
                {
                    "name": "Night mix",
                    "tracks": [
                        {"title": "Looped", "artist": "Kiasmos", "duration": 198},
                        {"song": "The xx - Intro"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        playlist = load_playlist(playlist_path)

        self.assertEqual(len(playlist.songs), 2)
        self.assertEqual(playlist.songs[0].duration, "3:18")
        self.assertEqual(playlist.songs[1].artist, "The xx")
        self.assertEqual(playlist.songs[1].title, "Intro")

    def test_reads_audio_directory(self) -> None:
        album = self.root / "Quiet"
        album.mkdir()
        (album / "Near Light.mp3").touch()
        (album / "notes.txt").touch()

        playlist = load_playlist(self.root)

        self.assertEqual(len(playlist.songs), 1)
        self.assertEqual(playlist.songs[0].title, "Near Light")
        self.assertEqual(playlist.songs[0].artist, "Quiet")

    def test_reads_pls_tracks(self) -> None:
        playlist_path = self.root / "night.pls"
        playlist_path.write_text(
            "[playlist]\n"
            "File1=music/intro.mp3\n"
            "Title1=The xx - Intro\n"
            "Length1=231\n"
            "File2=music/looped.flac\n"
            "Title2=Kiasmos - Looped\n",
            encoding="utf-8",
        )

        playlist = load_playlist(playlist_path)

        self.assertEqual(len(playlist.songs), 2)
        self.assertEqual(playlist.songs[0].duration, "3:51")
        self.assertEqual(playlist.songs[1].title, "Looped")

    def test_reads_gb18030_csv(self) -> None:
        playlist_path = self.root / "chinese.csv"
        playlist_path.write_text(
            "title,artist,duration,file\n"
            "爱人错过,告五人,3:34,music/01.flac\n",
            encoding="gb18030",
        )

        playlist = load_playlist(playlist_path)

        self.assertEqual(playlist.songs[0].artist, "告五人")
        self.assertEqual(playlist.songs[0].title, "爱人错过")

    def test_random_pick_avoids_previous_song(self) -> None:
        playlist_path = self.root / "two.txt"
        playlist_path.write_text("Artist A - First\nArtist B - Second\n", encoding="utf-8")
        playlist = load_playlist(playlist_path)
        previous = playlist.songs[0]

        for _ in range(20):
            self.assertNotEqual(pick_random_song(playlist.songs, previous.id), previous)


if __name__ == "__main__":
    unittest.main()
