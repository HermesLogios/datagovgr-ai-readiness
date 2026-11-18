"""Checks of the local preview of the site: files, headers and the two relays.

Usage:
    python -m unittest discover -s tests
"""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from aiready import jev
from fake_model import model_stub
from fake_portal import FakePortal, found_reply
from web import preview

REPLY = found_reply([{"name": "troxaia-atyxhmata", "type": "dataset"}])
KEY = "ts-trial-key-0123456789"


def answer_of(address: str, sent: dict | str | None = None):
    """Status, headers and body of the answer to a GET request, or to a POST request when something is sent."""
    data = None
    if sent is not None:
        data = (sent if isinstance(sent, str) else json.dumps(sent)).encode("utf-8")
    request = urllib.request.Request(address, data=data, headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(request, timeout=10) as reply:
            return reply.status, reply.headers, reply.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        with error:
            return error.code, error.headers, error.read().decode("utf-8")


def model_request() -> dict:
    record = {"title": "Στάσεις", "notes": "Οι στάσεις του δήμου.", "resources": [{"name": "Αρχείο", "description": "Οι στάσεις ανά γραμμή."}]}
    return jev.request_body(jev.publisher_texts(record))


class PreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site = Path(cls.enterClassContext(tempfile.TemporaryDirectory()))
        (site / "index.html").write_text("<p>home</p>", encoding="utf-8")
        (site / "404.html").write_text("<p>no such page</p>", encoding="utf-8")
        (site / "assets").mkdir()
        (site / "assets" / "app.js").write_text("export {};", encoding="utf-8")
        replies = {'name:"troxaia-atyxhmata"': (200, REPLY), 'name:"portal-in-trouble"': (503, "busy")}
        cls.portal = cls.enterClassContext(FakePortal(replies))
        cls.model, model_address = cls.enterClassContext(model_stub())
        cls.server = preview.preview_server(site, port=0, portal=cls.portal.url, model=model_address)
        cls.addClassCleanup(cls.server.server_close)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.addClassCleanup(cls.server.shutdown)
        cls.address = f"http://127.0.0.1:{cls.server.server_port}"

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

    def test_reading_relay_passes_the_request_to_the_model_with_the_key(self):
        before = len(self.model.received)
        status, headers, body = answer_of(self.address + "/api/reading", {"key": KEY, "request": model_request()})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body)["answers"]["contents"], {"type": "noul", "noul": 0.9})
        self.assertEqual(len(self.model.received), before + 1)
        received_headers, received = self.model.received[-1]
        self.assertEqual(received_headers["Authorization"], f"Bearer {KEY}")
        self.assertEqual(received, model_request())
        self.assertNotIn(KEY, body)

    def test_reading_relay_passes_on_only_the_fields_that_the_page_sends(self):
        request = model_request()
        request["assets"] = {"photo": "https://example.org/a.png"}
        request["state"]["maintainer"] = "someone@example.org"
        request["questions"]["contents"]["examples"] = ["extra"]
        answer_of(self.address + "/api/reading", {"key": KEY, "request": request, "note": "extra"})
        self.assertEqual(self.model.received[-1][1], model_request())

    def test_reading_relay_refuses_anything_but_a_request_of_the_page(self):
        def changed(change) -> dict:
            request = model_request()
            change(request)
            return {"key": KEY, "request": request}

        before = len(self.model.received)
        refused = [
            "not json", "[]", {"request": model_request()}, {"key": "short", "request": model_request()},
            {"key": "a key with spaces 0123456789", "request": model_request()}, {"key": KEY},
            changed(lambda request: request.update(model="other-model")),
            changed(lambda request: request.update(state="text")),
            changed(lambda request: request["state"].update(title=7)),
            changed(lambda request: request["state"].update(resource_descriptions=["text"] * 21)),
            changed(lambda request: request["state"].update(description="α" * 8001)),
            changed(lambda request: request.update(questions={})),
            changed(lambda request: request["questions"]["contents"].update(type="choice")),
            changed(lambda request: request["questions"]["contents"].update(instructions="")),
            changed(lambda request: request["questions"]["contents"].update(criteria={"true": "only one side"})),
            changed(lambda request: request["questions"].update({"Bad Name": request["questions"]["contents"]})),
            changed(lambda request: request["questions"].update({"__proto__": request["questions"]["contents"]})),
            changed(lambda request: request["questions"].update(
                {f"statement_{letter}": request["questions"]["contents"] for letter in "abcdefghij"})),
            {"key": KEY, "request": model_request(), "padding": "x" * 60000},
        ]
        for sent in refused:
            with self.subTest(sent=str(sent)[:60]):
                status, _, body = answer_of(self.address + "/api/reading", sent)
                self.assertEqual((status, body), (400, '{"error": "request"}'))
        self.assertEqual(len(self.model.received), before)

    def test_refused_key_and_limit_of_requests_are_told_apart_from_other_trouble(self):
        for reply, expected in (((401, {}, {"detail": "invalid key"}), (401, '{"error": "key"}')),
                                ((403, {}, "forbidden"), (401, '{"error": "key"}')),
                                ((429, {}, "slow down"), (429, '{"error": "limit"}')),
                                ((503, {}, "busy"), (502, '{"error": "service"}')),
                                ((422, {}, {"detail": "bad request"}), (502, '{"error": "service"}')),
                                ((200, {}, "<html>not json</html>"), (502, '{"error": "service"}'))):
            with self.subTest(status=reply[0]):
                self.model.replies.append(reply)
                status, _, body = answer_of(self.address + "/api/reading", {"key": KEY, "request": model_request()})
                self.assertEqual((status, body), expected)
                self.assertNotIn(KEY, body)

    def test_body_that_is_not_declared_as_json_is_refused(self):
        before = len(self.model.received)
        body = json.dumps({"key": KEY, "request": model_request()}).encode("utf-8")
        for content_type in ("text/plain", "application/x-www-form-urlencoded"):
            request = urllib.request.Request(self.address + "/api/reading", data=body, headers={"Content-Type": content_type})
            with self.assertRaises(urllib.error.HTTPError) as refused:
                urllib.request.urlopen(request, timeout=10)
            self.assertEqual(refused.exception.code, 400)
            refused.exception.close()
        self.assertEqual(len(self.model.received), before)

    def test_each_relay_answers_only_to_its_own_method(self):
        status, headers, _ = answer_of(self.address + "/api/reading")
        self.assertEqual((status, headers["Allow"]), (405, "POST"))
        status, headers, _ = answer_of(self.address + "/api/record?name=troxaia-atyxhmata", {"key": KEY})
        self.assertEqual((status, headers["Allow"]), (405, "GET"))


if __name__ == "__main__":
    unittest.main()
