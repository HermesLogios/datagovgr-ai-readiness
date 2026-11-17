"""Checks of the local preview of the site: files, headers and the relay to the catalogue.

Usage:
    python -m unittest discover -s tests
"""

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from fake_portal import FakePortal, found_reply
from web import preview

REPLY = found_reply([{"name": "troxaia-atyxhmata", "type": "dataset"}])


def answer_of(address: str):
    """Status, headers and body of the answer to a GET request."""
    try:
        with urllib.request.urlopen(address, timeout=10) as reply:
            return reply.status, reply.headers, reply.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        with error:
            return error.code, error.headers, error.read().decode("utf-8")


class PreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        site = Path(cls.folder.name)
        (site / "index.html").write_text("<p>home</p>", encoding="utf-8")
        (site / "404.html").write_text("<p>no such page</p>", encoding="utf-8")
        (site / "assets").mkdir()
        (site / "assets" / "app.js").write_text("export {};", encoding="utf-8")
        cls.portal = FakePortal({'name:"troxaia-atyxhmata"': (200, REPLY), 'name:"portal-in-trouble"': (503, "busy")})
        cls.portal.__enter__()
        cls.server = preview.preview_server(site, port=0, portal=cls.portal.url)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.address = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.portal.__exit__(None, None, None)
        cls.folder.cleanup()

    def test_pages_come_with_the_headers_of_the_public_site(self):
        status, headers, body = answer_of(self.address + "/")
        self.assertEqual((status, body), (200, "<p>home</p>"))
        self.assertIn(f"connect-src 'self' {self.portal.url};", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_scripts_are_served_as_javascript(self):
        _, headers, _ = answer_of(self.address + "/assets/app.js")
        self.assertEqual(headers["Content-Type"], "text/javascript")

    def test_unknown_address_gets_the_page_of_the_site(self):
        status, _, body = answer_of(self.address + "/no/such/page")
        self.assertEqual((status, body), (404, "<p>no such page</p>"))

    def test_relay_asks_the_portal_once_and_passes_its_reply_on(self):
        before = len(self.portal.requests)
        status, headers, body = answer_of(self.address + "/api/record?name=troxaia-atyxhmata")
        self.assertEqual((status, body), (200, REPLY))
        self.assertEqual(headers["Cache-Control"], "no-store")
        asked = self.portal.requests[before:]
        self.assertEqual(len(asked), 1)
        self.assertEqual(asked[0]["path"], "/api/3/action/package_search")
        self.assertEqual(asked[0]["query"], {"fq": 'name:"troxaia-atyxhmata"', "rows": "1"})

    def test_relay_refuses_anything_but_one_name_or_identifier(self):
        before = len(self.portal.requests)
        for query in ("", "name=Two%20Words", "name=a%22%20OR%20name:b", "id=not-an-identifier",
                      "name=troxaia-atyxhmata&id=0f0f0f0f-0f0f-0f0f-0f0f-0f0f0f0f0f0f"):
            with self.subTest(query=query):
                self.assertEqual(answer_of(f"{self.address}/api/record?{query}")[0], 400)
        self.assertEqual(len(self.portal.requests), before)

    def test_trouble_at_the_portal_is_reported_as_a_bad_gateway(self):
        status, _, body = answer_of(self.address + "/api/record?name=portal-in-trouble")
        self.assertEqual((status, body), (502, '{"error": "portal"}'))


if __name__ == "__main__":
    unittest.main()
