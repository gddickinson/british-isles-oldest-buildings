"""bidb.backup: snapshot, skip when unchanged, keep the newest N, nothing when the drive is missing."""
import gzip
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from bidb import backup


class Backup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "british_isles_buildings.sqlite"
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE buildings (id)")
        conn.executemany("INSERT INTO buildings VALUES (?)", [("Q1",), ("Q2",)])
        conn.commit()
        conn.close()
        self.dest = root / "drive" / "backups"
        (root / "drive").mkdir()
        self.patches = [mock.patch.object(backup, "db_path", lambda: self.db),
                        mock.patch.object(backup, "backup_dir", lambda: self.dest),
                        mock.patch.object(backup, "SETTINGS_FILE", root / "settings.json"),
                        mock.patch.object(backup, "ROOT", root)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_snapshot_skip_and_keep(self):
        made = backup.run(log=lambda *a: None)
        manifest = json.loads((made / "MANIFEST.json").read_text())
        self.assertEqual(manifest["counts"], {"buildings": 2})
        copy = Path(self.tmp.name) / "copy.sqlite"
        copy.write_bytes(gzip.open(made / (self.db.name + ".gz")).read())
        self.assertEqual(sqlite3.connect(copy).execute("SELECT COUNT(*) FROM buildings").fetchone()[0], 2)
        self.assertIsNone(backup.run(log=lambda *a: None))                 # unchanged: skipped
        with mock.patch.object(backup.time, "strftime", side_effect=lambda f: f"x{time.monotonic_ns()}"):
            for _ in range(3):
                self.assertIsNotNone(backup.run(force=True, keep=2, log=lambda *a: None))
        self.assertEqual(len(backup.backups(self.dest)), 2)

    def test_drive_missing(self):
        with mock.patch.object(backup, "backup_dir", lambda: Path(self.tmp.name) / "gone" / "backups"):
            self.assertIsNone(backup.run(log=lambda *a: None))


if __name__ == "__main__":
    unittest.main()
