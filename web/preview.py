"""Local preview of the public site.

Builds the site and serves it on this computer with the headers of the public site. The relay
to the catalogue, which Cloudflare Pages runs from web/functions/api/record.js, is answered
here by the same rules, so that the page behaves as it does when it is published.

Usage:
    python web/preview.py
    python web/preview.py --port 8790
"""

import argparse
import functools
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiready.identifier import NAME_PATTERN, UUID_PATTERN  # noqa: E402
from aiready.portal import USER_AGENT  # noqa: E402
from web import build  # noqa: E402

DEFAULT_PORT = 8788
RELAY_TIMEOUT_SECONDS = 20
FILE_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript",
    ".json": "application/json", ".wasm": "application/wasm", ".zip": "application/zip", ".svg": "image/svg+xml",
    ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8",
}


def catalogue_filter(query: dict[str, list[str]]) -> str | None:
    """Filter of the catalogue search for a request of the relay; None unless it names one dataset."""
    names, identifiers = query.get("name", []), query.get("id", [])
    if len(names) == 1 and not identifiers and NAME_PATTERN.fullmatch(names[0]):
        return f'name:"{names[0]}"'
    if len(identifiers) == 1 and not names and UUID_PATTERN.fullmatch(identifiers[0]):
        return f'id:"{identifiers[0]}"'
    return None


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serves the files of the site and answers the relay."""

    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, **FILE_TYPES}

    def __init__(self, *arguments, site: Path, portal: str, **options):
        self.site = site
        self.portal = portal
        super().__init__(*arguments, directory=str(site), **options)

    def do_GET(self):
        parts = urlsplit(self.path)
        if parts.path == build.PROXY_PATH:
            self.relay(parse_qs(parts.query))
        else:
            super().do_GET()

    def end_headers(self):
        for name, value in build.response_headers(self.portal, indexing=False).items():
            self.send_header(name, value)
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        page = self.site / "404.html"
        if code == 404 and page.is_file():
            self.answer(404, "text/html; charset=utf-8", page.read_bytes())
        else:
            super().send_error(code, message, explain)

    def answer(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def relay(self, query: dict[str, list[str]]) -> None:
        """Asks the catalogue for one dataset and passes its reply on; nothing is kept."""
        wanted = catalogue_filter(query)
        if wanted is None:
            self.answer(400, "application/json; charset=utf-8", json.dumps({"error": "request"}).encode("utf-8"))
            return
        try:
            reply = requests.get(
                self.portal + "/api/3/action/package_search", params={"fq": wanted, "rows": 1},
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=RELAY_TIMEOUT_SECONDS,
            )
            if reply.status_code != 200:
                raise ValueError(f"HTTP {reply.status_code}")
            reply.json()
        except (requests.RequestException, ValueError):
            self.answer(502, "application/json; charset=utf-8", json.dumps({"error": "portal"}).encode("utf-8"))
            return
        self.answer(200, "application/json; charset=utf-8", reply.content)

    def log_message(self, format, *arguments):
        return


def preview_server(site: Path, port: int = DEFAULT_PORT, portal: str | None = None) -> ThreadingHTTPServer:
    """Server of the site on this computer only; port 0 picks a free port."""
    portal = (portal or os.environ.get(build.PORTAL_VARIABLE) or build.DEFAULT_PORTAL).rstrip("/")
    return ThreadingHTTPServer(("127.0.0.1", port), functools.partial(PreviewHandler, site=site, portal=portal))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Builds the public site and serves it on this computer.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port of the preview (default {DEFAULT_PORT})")
    arguments = parser.parse_args(argv)
    try:
        site = build.build_site()
    except RuntimeError as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    server = preview_server(site, arguments.port)
    print(f"Preview at http://localhost:{server.server_port} (Ctrl+C stops it)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Preview stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
