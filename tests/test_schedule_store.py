import json
import tempfile
import unittest
from pathlib import Path

from schedule_store import ScheduleError, ScheduleStore


class ScheduleStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "schedules.json"
        self.seed_path = self.root / "schedules.seed.json"
        self.seed_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "items": [
                        {
                            "id": "work-1",
                            "type": "work",
                            "title": "项目同步",
                            "date": "2026-10-21",
                            "startTime": "09:00",
                            "durationMinutes": 45,
                        },
                        {
                            "id": "leisure-1",
                            "type": "leisure",
                            "title": "朋友晚餐",
                            "date": "2026-10-22",
                            "startTime": "18:30",
                            "durationMinutes": 90,
                        },
                        {
                            "id": "personal-1",
                            "type": "personal",
                            "title": "夜跑",
                            "date": "2026-10-23",
                            "startTime": "19:00",
                            "durationMinutes": 30,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initializes_database_from_seed(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)

        self.assertTrue(self.database_path.exists())
        self.assertEqual(store.summary()["total"], 3)
        self.assertEqual(
            store.summary()["types"],
            {"work": 1, "leisure": 1, "personal": 1},
        )

    def test_create_update_and_reload(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)
        created = store.create(
            {
                "type": "personal",
                "title": "整理书桌",
                "date": "2026-10-24",
                "startTime": "16:00",
                "durationMinutes": 20,
                "description": "生活整理",
            }
        )
        store.update(created.id, {"startTime": "17:00", "status": "done"})

        reloaded_store = ScheduleStore(self.database_path, self.seed_path)
        reloaded = reloaded_store.get(created.id)

        self.assertEqual(reloaded.start_time, "17:00")
        self.assertEqual(reloaded.status, "done")
        self.assertEqual(reloaded.description, "生活整理")

    def test_deadline_can_be_set_and_cleared(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)
        created = store.create(
            {
                "type": "work",
                "title": "提交方案",
                "date": "2026-10-24",
                "startTime": "10:00",
                "durationMinutes": 60,
                "deadline": "2026-10-24T18:30",
            }
        )

        self.assertEqual(created.deadline, "2026-10-24T18:30")

        cleared = store.update(created.id, {"deadline": None})
        self.assertIsNone(cleared.deadline)
        self.assertIsNone(store.get(created.id).deadline)

    def test_rejects_invalid_deadline(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)

        with self.assertRaises(ScheduleError):
            store.create(
                {
                    "type": "work",
                    "title": "错误截止时间",
                    "date": "2026-10-24",
                    "startTime": "10:00",
                    "durationMinutes": 60,
                    "deadline": "10/24/2026",
                }
            )

    def test_rejects_unknown_schedule_type(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)

        with self.assertRaises(ScheduleError):
            store.create(
                {
                    "type": "meeting",
                    "title": "错误分类",
                    "date": "2026-10-24",
                    "startTime": "10:00",
                    "durationMinutes": 30,
                }
            )

    def test_rejects_invalid_time(self) -> None:
        store = ScheduleStore(self.database_path, self.seed_path)

        with self.assertRaises(ScheduleError):
            store.create(
                {
                    "type": "work",
                    "title": "错误时间",
                    "date": "2026-10-24",
                    "startTime": "25:90",
                    "durationMinutes": 30,
                }
            )


if __name__ == "__main__":
    unittest.main()
