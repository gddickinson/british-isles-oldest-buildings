import unittest

from app.lan import blocked, is_local


class Guard(unittest.TestCase):
    def test_loopback_is_local(self):
        for a in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
            self.assertTrue(is_local(a), a)
        for a in ("192.168.1.50", "10.0.0.2", "", "nonsense"):
            self.assertFalse(is_local(a), a)

    def test_other_computers_read_only(self):
        self.assertFalse(blocked("GET", "/api/search", False))
        self.assertFalse(blocked("GET", "/building/Q1", False))
        for method, path in (("POST", "/api/override/Q1"), ("DELETE", "/api/override/Q1"), ("POST", "/api/jobs/start"),
                             ("POST", "/api/route"), ("GET", "/api/settings"), ("GET", "/api/settings/browse"),
                             ("GET", "/api/screenshot"), ("GET", "/_shot"), ("GET", "/setup"), ("GET", "/api/share"),
                             ("GET", "/api/street_tiles")):
            self.assertTrue(blocked(method, path, False), (method, path))

    def test_this_computer_unrestricted(self):
        for method, path in (("POST", "/api/override/Q1"), ("GET", "/api/settings"), ("POST", "/api/share")):
            self.assertFalse(blocked(method, path, True))

    def test_settings_page_itself_viewable(self):
        self.assertFalse(blocked("GET", "/settings", False))     # browser preferences live in the browser


class Requests(unittest.TestCase):
    def setUp(self):
        from app.server import app
        self.client = app.test_client()

    def test_remote_post_refused(self):
        r = self.client.post("/api/override/Q1", json={"name": "x"}, environ_base={"REMOTE_ADDR": "192.168.1.50"})
        self.assertEqual(r.status_code, 403)
        r = self.client.get("/api/settings/browse?path=/", environ_base={"REMOTE_ADDR": "192.168.1.50"})
        self.assertEqual(r.status_code, 403)

    def test_remote_pages_hide_edit_controls(self):
        r = self.client.get("/settings", environ_base={"REMOTE_ADDR": "192.168.1.50"})
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('data-here="0"', html)
        self.assertNotIn('id="sharing"', html)
        self.assertNotIn('id="data" class="set-card"', html)
        r = self.client.get("/settings")                     # the test client is this computer
        self.assertIn('data-here="1"', r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()


class ShareCodes(unittest.TestCase):
    def test_access_levels(self):
        from app.lan import access
        none, code, both = {}, {"share_code": "ABC234"}, {"share_code": "ABC234", "share_trusted_code": "XYZ789"}
        self.assertEqual(access(False, None, none), "read")
        self.assertEqual(access(True, None, both), "full")
        self.assertIsNone(access(False, None, code))
        self.assertIsNone(access(False, "WRONG1", code))
        self.assertEqual(access(False, "abc234 ", code), "read")         # typed in lower case, with a space
        self.assertEqual(access(False, "XYZ789", both), "full")
        self.assertEqual(access(False, "XYZ789", {"share_trusted_code": "XYZ789"}), "full")
        self.assertEqual(access(False, None, {"share_trusted_code": "XYZ789"}), "read")   # no viewer code: open

    def test_requests_with_codes(self):
        from unittest import mock
        from app import lan
        from app.server import app
        client, far = app.test_client(), {"REMOTE_ADDR": "192.168.1.50"}
        settings = {"share_code": "ABC234", "share_trusted_code": "XYZ789"}
        with mock.patch.object(lan.config, "load_settings", return_value=settings), mock.patch.object(lan.time, "sleep"):
            self.assertEqual(client.get("/api/stats", environ_base=far).status_code, 401)
            r = client.get("/help", environ_base=far)
            self.assertEqual(r.status_code, 401)
            self.assertIn(b"share code", r.data)
            self.assertEqual(client.get("/help?code=NOPE22", environ_base=far).status_code, 401)
            r = client.get("/help?code=abc234", environ_base=far)
            self.assertEqual(r.status_code, 200)
            self.assertIn("bidb_share=ABC234", r.headers.get("Set-Cookie", ""))
            self.assertNotEqual(client.get("/api/stats", environ_base=far).status_code, 401)   # the cookie now
            self.assertEqual(client.get("/api/settings/browse?path=/", environ_base=far).status_code, 403)
            client.get("/help?code=XYZ789", environ_base=far)
            self.assertEqual(client.get("/api/share", environ_base=far).status_code, 200)    # trusted: full access
