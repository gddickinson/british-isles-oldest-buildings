"""Settings, data location and exports: .venv/bin/python -m unittest discover tests"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bidb import config
from app import data_location, export_api


class SettingsFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "settings.json"
        self.patch = mock.patch.object(config, "SETTINGS_FILE", self.file)
        self.patch.start()
        config._settings.update(mtime=None, value={})

    def tearDown(self):
        self.patch.stop()
        config._settings.update(mtime=None, value={})
        self.tmp.cleanup()

    def test_defaults_without_file(self):
        self.assertEqual(config.cache_dir(), config.DEFAULT_CACHE_DIR)
        self.assertEqual(config.db_path(), config.DEFAULT_DB_PATH)

    def test_roundtrip_and_removal(self):
        config.save_settings({"cache_dir": self.tmp.name})
        self.assertEqual(config.cache_dir(), Path(self.tmp.name))
        config.save_settings({"cache_dir": None})
        self.assertEqual(json.loads(self.file.read_text()), {})

    def test_missing_drive_stops_builds(self):
        config.save_settings({"cache_dir": "/Volumes/NO_SUCH_DRIVE/cache"})
        with self.assertRaises(config.DataLocationMissing):
            config.require_locations()

    def test_suggest_and_validate(self):
        dest = data_location.suggest(self.tmp.name, "cache")
        self.assertEqual(dest, Path(self.tmp.name) / "UK_BUILDINGS_DATA" / "cache")
        self.assertEqual(data_location.suggest(config.ROOT, "cache"), config.DEFAULT_CACHE_DIR)
        inside = data_location.validate("cache", config.cache_dir() / "sub")
        self.assertTrue(any("inside" in p for p in inside))
        self.assertTrue(data_location.validate("cache", "relative/path"))


class Exports(unittest.TestCase):
    rows = [{"id": "Q1", "name": 'A "quoted", name', "lat": 51.0, "lon": -1.0, "year_start": 1100},
            {"id": "Q2", "name": "No position", "lat": None, "lon": None}]

    def test_csv_quoting(self):
        out = export_api.to_csv(self.rows, ["id", "name"])
        self.assertIn('"A ""quoted"", name"', out)

    def test_geojson_skips_unlocated(self):
        fc = json.loads(export_api.to_geojson(self.rows, ["id", "name"]))
        self.assertEqual(len(fc["features"]), 1)
        self.assertEqual(fc["features"][0]["geometry"]["coordinates"], [-1.0, 51.0])

    def test_kml(self):
        kml = export_api.to_kml(self.rows, ["id", "name", "year_start"], "t")
        self.assertIn("<coordinates>-1.0,51.0</coordinates>", kml)
        self.assertEqual(kml.count("<Placemark>"), 1)


if __name__ == "__main__":
    unittest.main()
