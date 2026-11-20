"""Local stand-in for the catalogue API of the portal, used by the tests.

It answers the action package_search on 127.0.0.1 with prepared replies, so that the code that
calls the portal is exercised without any call to data.gov.gr.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


class FakePortal:
    """Serves prepared replies, keyed by the value of the fq parameter of the request, or by q= and the words of a
    search."""

    def __init__(self, replies: dict[str, tuple[int, str]]):
        self.replies = replies
        self.requests: list[dict] = []
        portal = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parts = urlsplit(self.path)
                query = {key: values[0] for key, values in parse_qs(parts.query).items()}
                portal.requests.append({"path": parts.path, "query": query, "user_agent": self.headers.get("User-Agent")})
                key = query["fq"] if "fq" in query else f"q={query.get('q', '')}"
                status, body = portal.replies.get(key, (200, found_reply([])))
                payload = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc_info):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


def found_reply(records: list[dict]) -> str:
    """Body of a successful package_search reply that holds the given records."""
    return json.dumps({"success": True, "result": {"count": len(records), "results": records}}, ensure_ascii=False)
