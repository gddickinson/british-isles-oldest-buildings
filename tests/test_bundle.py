"""bidb.bundle release: draft reuse, upload retries, half-uploaded assets removed (no network)."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests

from bidb import bundle

API = "https://api.github.com/repos/o/r/releases"


class Release(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "db.sqlite.gz"
        self.path.write_bytes(b"x" * 1000)
        self.digest = "sha256:" + bundle.sha256(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_draft_of_today_is_reused(self):
        rels = [{"tag_name": "db-2026-10-24", "draft": True, "id": 7}, {"tag_name": "db-2026-10-23", "draft": False}]
        with mock.patch.object(bundle, "_github", return_value=rels) as gh:
            self.assertEqual(bundle._draft("o/r", "t", "2026-10-24", "notes", lambda m: None)["id"], 7)
        gh.assert_called_once()                                     # no new release created

    def test_new_tag_avoids_published_ones(self):
        calls = []

        def gh(method, url, token, **kw):
            calls.append((method, kw.get("json")))
            return [{"tag_name": "db-2026-10-24", "draft": False}] if method == "GET" else {"id": 8}
        with mock.patch.object(bundle, "_github", side_effect=gh):
            bundle._draft("o/r", "t", "2026-10-24", "notes", lambda m: None)
        self.assertEqual(calls[1][1]["tag_name"], "db-2026-10-24-2")
        self.assertTrue(calls[1][1]["draft"])

    def test_upload_retries_and_removes_partial_asset(self):
        log, state = [], {"posts": 0, "deleted": []}

        def gh(method, url, token, **kw):
            if method == "GET":                                     # a stalled asset left by the first attempt
                return [{"name": self.path.name, "state": "starter", "size": 10, "url": "A1"}] if state["posts"] else []
            if method == "DELETE":
                state["deleted"].append(url)
                return None
            state["posts"] += 1
            kw["data"].read(10_000)
            if state["posts"] == 1:
                raise requests.HTTPError("408 Upload body timed out due to inactivity")
            return {"url": "A2", "size": 1000}
        with mock.patch.object(bundle, "_github", side_effect=gh), mock.patch.object(bundle.time, "sleep"), \
                mock.patch.object(bundle.progress, "items"):
            got = bundle._upload("o/r", {"id": 7, "tag_name": "db-x"}, "t", self.path, self.digest, log.append)
        self.assertEqual(got["url"], "A2")
        self.assertEqual(state["deleted"], ["A1"])
        self.assertTrue(any("attempt 2 of" in m for m in log))

    def test_matching_asset_is_not_uploaded_again(self):
        done = [{"name": self.path.name, "state": "uploaded", "size": 1000, "digest": self.digest, "url": "A"}]
        with mock.patch.object(bundle, "_github", return_value=done) as gh:
            self.assertEqual(bundle._upload("o/r", {"id": 7, "tag_name": "db-x"}, "t", self.path, self.digest,
                                            lambda m: None)["url"], "A")
        gh.assert_called_once()

    def test_reader_has_a_length(self):
        r = bundle._Reader(self.path)
        with mock.patch.object(bundle.progress, "items"):
            self.assertEqual((len(r), len(r.read()), r.done), (1000, 1000, 1000))
        r.close()


if __name__ == "__main__":
    unittest.main()
