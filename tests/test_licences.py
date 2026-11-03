"""What the public copies may hold: photo credits, tables left out of the download, layers not copied."""
import gzip
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bidb import config, dendro_add, image_credits, setup


class Credits(unittest.TestCase):
    def test_title(self):
        page = "https://commons.wikimedia.org/wiki/File:The_Red_Tower_on_York_city_walls_%281%29.JPG"
        self.assertEqual(image_credits.title(page), "File:The Red Tower on York city walls (1).JPG")
        self.assertIsNone(image_credits.title("https://example.org/a.jpg"))
        self.assertIsNone(image_credits.title(None))

    def test_plain(self):
        self.assertEqual(image_credits.plain('<a href="//x">Jane&nbsp;Doe</a>\n (talk)'), "Jane Doe (talk)")
        self.assertEqual(len(image_credits.plain("x" * 300)), 120)

    def test_credit(self):
        conn = sqlite3.connect(":memory:")
        self.assertIsNone(image_credits.credit(conn, "p"))            # no table yet
        conn.execute("CREATE TABLE image_credits (page TEXT PRIMARY KEY, artist TEXT, licence TEXT, licence_url TEXT)")
        conn.executemany("INSERT INTO image_credits VALUES (?, ?, ?, ?)",
                         [("a", "Jane Doe", "CC BY-SA 4.0", ""), ("b", "", "Public domain", ""), ("c", "", "", "")])
        self.assertEqual(image_credits.credit(conn, "a"), "Jane Doe · CC BY-SA 4.0")
        self.assertEqual(image_credits.credit(conn, "b"), "Public domain")
        self.assertIsNone(image_credits.credit(conn, "c"))
        self.assertIsNone(image_credits.credit(conn, "missing"))
        self.assertEqual(image_credits.credits(conn), {"a": "Jane Doe · CC BY-SA 4.0", "b": "Public domain"})


class LocalOnly(unittest.TestCase):
    def test_package_leaves_out_local_tables(self):
        self.assertIn("dendro", config.LOCAL_ONLY_TABLES)
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "db.sqlite"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE buildings (id)")
            conn.execute("CREATE TABLE dendro (record_id, location)")
            conn.execute("INSERT INTO dendro VALUES ('Q1', 'Somewhere, Barn')")
            conn.commit()
            conn.close()
            bundled = Path(tmp) / "out.sqlite.gz"
            with mock.patch.object(config, "db_path", return_value=db), mock.patch.object(setup, "BUNDLED", bundled):
                setup.package(log=lambda *_: None)
            out = Path(tmp) / "unpacked.sqlite"
            out.write_bytes(gzip.decompress(bundled.read_bytes()))
            tables = {r[0] for r in sqlite3.connect(out).execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            self.assertEqual(tables, {"buildings"})
            self.assertEqual(sqlite3.connect(db).execute("SELECT COUNT(*) FROM dendro").fetchone()[0], 1)

    def test_items_file_holds_no_vag_text(self):
        self.assertRegex(dendro_add.key("Deal, Victoria Road, Deal Castle"), r"^[0-9a-f]{12}$")
        import json
        data = json.loads(dendro_add.ITEMS.read_text())
        for v in data.values():
            for e in v["entries"]:
                self.assertRegex(e, r"^[0-9a-f]{12}$")

    def test_roy_not_copied(self):
        from app.historic_layers import LAYERS
        roy = next(l for l in LAYERS if l["key"] == "roy")
        self.assertIsNone(roy["bundle"])


if __name__ == "__main__":
    unittest.main()
