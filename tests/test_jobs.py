"""Jobs, progress, refresh and first-run setup: .venv/bin/python -m unittest tests.test_jobs"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from bidb import config, progress, refresh, setup


class Refresh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "x.json"
        self.file.write_text("{}")
        self.env = os.environ.get("BIDB_REFRESH")

    def tearDown(self):
        refresh.set_rule()
        if self.env is not None:
            os.environ["BIDB_REFRESH"] = self.env
        self.tmp.cleanup()

    def age(self, days):
        t = time.time() - days * 86400
        os.utime(self.file, (t, t))

    def test_off_by_default(self):
        refresh.set_rule()
        self.assertFalse(refresh.stale(self.file, "https://query.wikidata.org/sparql"))
        self.assertNotIn("BIDB_REFRESH", os.environ)

    def test_days(self):
        refresh.set_rule(days=30)
        self.age(40)
        self.assertTrue(refresh.stale(self.file, "https://en.wikipedia.org/w/api.php"))
        self.age(5)
        self.assertFalse(refresh.stale(self.file, "https://en.wikipedia.org/w/api.php"))

    def test_sources_only_refetches_files_from_before_the_refresh(self):
        self.age(1)
        refresh.set_rule(sources=["wikidata"])
        self.assertTrue(refresh.stale(self.file, "https://query.wikidata.org/sparql"))
        self.assertFalse(refresh.stale(self.file, "https://api.postcodes.io/x"))
        self.file.write_text("{}")                  # fetched again during this refresh
        self.assertFalse(refresh.stale(self.file, "https://query.wikidata.org/sparql"))

    def test_sources_and_days(self):
        refresh.set_rule(days=10, sources=["osm"])
        self.age(20)
        self.assertTrue(refresh.stale(self.file, "overpass-api.de"))
        self.assertFalse(refresh.stale(self.file, "https://www.wikidata.org/w/api.php"))

    def test_environment_carries_the_rule(self):
        refresh.set_rule(days=7, sources=["commons", "wikipedia"])
        env = os.environ["BIDB_REFRESH"]
        self.assertIn("days=7", env)
        self.assertIn("sources=commons,wikipedia", env)
        self.assertIn("since=", env)

    def test_unknown_source(self):
        with self.assertRaises(ValueError):
            refresh.set_rule(sources=["nonsense"])

    def test_source_of_hosts(self):
        self.assertEqual(refresh.source_of("services-eu1.arcgis.com"), "registers")
        self.assertEqual(refresh.source_of("en.wiktionary.org"), "wikipedia")
        self.assertIsNone(refresh.source_of("example.com"))


class Progress(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        runs = Path(self.tmp.name)
        self.patches = [mock.patch.object(progress, "RUNS", runs),
                        mock.patch.object(progress, "STATUS", runs / "job_status.json"),
                        mock.patch.object(progress, "TIMES", runs / "stage_times.json")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        progress._state = None
        self.tmp.cleanup()

    def test_stages_items_and_times(self):
        seen = []

        def one():
            progress.items(5, 10)
            progress.count(from_cache=True)
            progress.count(from_cache=False)
            seen.append(json.loads(progress.STATUS.read_text())["index"])
        progress.run_stages("t", [("A", one), ("B", lambda: None)])
        st = progress.read()
        self.assertEqual(st["state"], "finished")
        self.assertEqual([s["name"] for s in st["stages"]], ["A", "B"])
        self.assertTrue(all(s["took"] is not None for s in st["stages"]))
        self.assertEqual((st["cached"], st["downloads"]), (1, 1))
        self.assertEqual(seen, [0])
        times = json.loads(progress.TIMES.read_text())["t"]
        self.assertEqual(set(times), {"A", "B"})
        progress.begin("t", ["A", "B"])                 # the next run expects last run's times
        self.assertEqual(progress.read()["stages"][0]["expected"], times["A"])

    def test_failure_and_stop(self):
        def boom():
            raise RuntimeError("no network")
        with self.assertRaises(RuntimeError):
            progress.run_stages("t", [("A", boom)])
        st = progress.read()
        self.assertEqual(st["state"], "failed")
        self.assertIn("no network", st["message"])

        def stop():
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            progress.run_stages("t", [("A", stop)])
        self.assertEqual(progress.read()["message"], "Stopped.")

    def test_died_when_process_gone(self):
        progress.placeholder("t", 99999999, ["A"])
        self.assertEqual(progress.read()["state"], "died")
        progress.placeholder("t", os.getpid(), ["A"])
        self.assertEqual(progress.read()["state"], "running")

    def test_no_status(self):
        self.assertEqual(progress.read(), {"state": "none"})


class Setup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch = mock.patch.object(config, "SETTINGS_FILE", self.root / "settings.json")
        self.patch.start()
        config._settings.update(mtime=None, value={})

    def tearDown(self):
        self.patch.stop()
        config._settings.update(mtime=None, value={})
        self.tmp.cleanup()

    def test_find_existing_data(self):
        base = self.root / "Drive" / setup.FOLDER
        (base / "cache" / "basemap").mkdir(parents=True)
        (base / "database").mkdir()
        (base / "database" / config.DB_NAME).write_bytes(b"")
        found = setup.find_data(self.root / "Drive")
        self.assertEqual(found, {"cache": base / "cache", "database": base / "database"})
        setup.use_data(str(self.root / "Drive"))
        self.assertEqual(config.cache_dir(), base / "cache")
        self.assertEqual(config.db_path(), base / "database" / config.DB_NAME)

    def test_new_cache_on_empty_drive_keeps_database_local(self):
        drive = self.root / "Empty"
        drive.mkdir()
        lines = setup.use_data(str(drive))
        self.assertTrue((drive / setup.FOLDER / "cache").is_dir())
        self.assertEqual(config.cache_dir(), drive / setup.FOLDER / "cache")
        self.assertEqual(config.db_path(), config.DEFAULT_DB_PATH)
        self.assertIn("new folder", lines[0])

    def test_missing_drive_is_reported_not_created(self):
        gone = self.root / "Unplugged" / "cache"
        config.save_settings({"cache_dir": str(gone)})
        self.assertTrue(setup.check())
        self.assertFalse(gone.exists())
        with self.assertRaises(ValueError):
            setup.use_data(str(self.root / "Unplugged"))


class Bundle(unittest.TestCase):
    def setUp(self):
        from bidb import bundle
        self.bundle = bundle
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.patches = [mock.patch.object(bundle, "MANIFEST", d / "bundled.json"),
                        mock.patch.object(bundle, "BUNDLED", d / "db.sqlite.gz")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_local_copy_checked_against_manifest(self):
        b = self.bundle
        b.BUNDLED.write_bytes(b"abc")
        self.assertTrue(b.is_current())                  # no manifest: any local copy will do
        b.MANIFEST.write_text(json.dumps({"bytes": 3, "sha256": b.sha256(b.BUNDLED)}))
        self.assertTrue(b.is_current())
        b.BUNDLED.write_bytes(b"abd")
        self.assertFalse(b.is_current())

    def test_fetch_without_manifest(self):
        with self.assertRaises(FileNotFoundError):
            self.bundle.fetch(log=lambda m: None)


if __name__ == "__main__":
    unittest.main()
