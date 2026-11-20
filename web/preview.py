"""Local preview of the public site.

Builds the site and serves it on this computer with the headers of the public site. The two
relays that the Worker of the site runs from web/functions/api are answered here by the same
rules, so that the page behaves as it does when it is published: record.js asks the catalogue
of the portal for one dataset, reading.js passes a request of the second reading to the model.

Usage:
    python web/preview.py
    python web/preview.py --port 8790

Environment variables:
    DATAGOVGR_BASE_URL   address of the portal (default https://data.gov.gr)
    TYPESAFE_API_URL     address of the model of the second reading (default: the address in aiready/jev.py)
"""

import argparse
import functools
import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiready import jev  # noqa: E402
from aiready.identifier import NAME_PATTERN, UUID_PATTERN  # noqa: E402
from aiready.portal import USER_AGENT  # noqa: E402
from web import build  # noqa: E402

DEFAULT_PORT = 8788
RELAY_TIMEOUT_SECONDS = 20
MODEL_VARIABLE = "TYPESAFE_API_URL"
MODEL_TIMEOUT_SECONDS = 30
MAX_BODY_CHARACTERS = 60000                 # body of a request of the second reading
MAX_BODY_BYTES = 4 * MAX_BODY_CHARACTERS    # a character takes at most four bytes
MAX_TEXT_CHARACTERS = 8000                  # one text of the state
MAX_STATEMENT_CHARACTERS = 2000             # the instructions or one criterion of a question
MAX_QUESTIONS = 12
MAX_OPTIONS = 10                            # options of a question of choice
MAX_COLUMNS = 100                           # names of columns in the state
MAX_COLUMN_CHARACTERS = 300                 # the name of a column with its dictionary
MAX_TABLES = 3                              # tables whose columns one request may ask for
MAX_TABLE_COLUMNS = 100                     # columns passed on for one table
KEY_PATTERN = re.compile(r"[\x21-\x7e]{8,300}")
MODEL_PATTERN = re.compile(r"jev-[a-z0-9.]{1,20}")
QUESTION_NAME_PATTERN = re.compile(r"[a-z][a-z_]{0,29}")
JSON_TYPE = "application/json; charset=utf-8"
FILE_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript",
    ".json": "application/json", ".wasm": "application/wasm", ".zip": "application/zip", ".svg": "image/svg+xml",
    ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8",
}


SEARCH_SIGNS = re.compile(r'[+!(){}\[\]^"~*?:\\/&|]')   # signs of the search language of the portal
MIN_SEARCH_CHARACTERS, MAX_SEARCH_CHARACTERS = 2, 100
MAX_SEARCH_ROWS, DEFAULT_SEARCH_ROWS = 20, 8


def search_request(query: dict[str, list[str]]) -> tuple[str, int] | None:
    """Words and number of datasets of a search of the relay; None unless the request is a search and nothing
    else. The signs of the search language of the portal are left out of the words."""
    words, rows = query.get("q", []), query.get("rows", [])
    if len(words) != 1 or len(rows) > 1 or "name" in query or "id" in query or len(words[0]) > MAX_SEARCH_CHARACTERS:
        return None
    text = " ".join(SEARCH_SIGNS.sub(" ", words[0]).split())
    count = int(rows[0]) if rows and rows[0].isdigit() else (DEFAULT_SEARCH_ROWS if not rows else 0)
    if len(text) < MIN_SEARCH_CHARACTERS or not 1 <= count <= MAX_SEARCH_ROWS:
        return None
    return text, count


def plain_title(value) -> str:
    """A title of the portal, which may be given in more than one language."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return next((text for text in (value.get("el"), value.get("en"), *value.values()) if isinstance(text, str) and text), "")
    return ""


def found_datasets(reply) -> dict | None:
    """The datasets of a reply of the search, each with the five facts that the list of the page shows."""
    result = reply.get("result") if isinstance(reply, dict) and reply.get("success") is True else None
    if not isinstance(result, dict) or not isinstance(result.get("results"), list):
        return None
    datasets = []
    for item in result["results"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        organization = item.get("organization")
        resources = item.get("num_resources")
        datasets.append({
            "name": item["name"],
            "title": plain_title(item.get("title")) or item["name"],
            "organization": plain_title(organization.get("title")) if isinstance(organization, dict) else "",
            "modified": item["metadata_modified"] if isinstance(item.get("metadata_modified"), str) else "",
            "resources": resources if isinstance(resources, int) and not isinstance(resources, bool)
            else len(item["resources"]) if isinstance(item.get("resources"), list) else 0,
        })
    count = result.get("count")
    return {"count": count if isinstance(count, int) and not isinstance(count, bool) else len(datasets), "results": datasets}


def catalogue_filter(query: dict[str, list[str]]) -> str | None:
    """Filter of the catalogue search for a request of the relay; None unless it names one dataset."""
    names, identifiers = query.get("name", []), query.get("id", [])
    if len(names) == 1 and not identifiers and NAME_PATTERN.fullmatch(names[0]):
        return f'name:"{names[0]}"'
    if len(identifiers) == 1 and not names and UUID_PATTERN.fullmatch(identifiers[0]):
        return f'id:"{identifiers[0]}"'
    return None


def is_text(value, limit: int) -> bool:
    return isinstance(value, str) and len(value) <= limit


def is_statement(value) -> bool:
    return is_text(value, MAX_STATEMENT_CHARACTERS) and len(value) > 0


def model_state(state) -> dict | None:
    """The texts of a dataset as the page sends them, or None."""
    if not isinstance(state, dict):
        return None
    title, description, resources = state.get("title"), state.get("description"), state.get("resource_descriptions")
    if (not is_text(title, MAX_TEXT_CHARACTERS) or not is_text(description, MAX_TEXT_CHARACTERS)
            or not isinstance(resources, list) or len(resources) > jev.MAX_RESOURCE_DESCRIPTIONS
            or not all(is_text(text, MAX_TEXT_CHARACTERS) for text in resources)):
        return None
    clean = {"title": title, "description": description, "resource_descriptions": resources}
    if "columns" not in state:
        return clean
    columns = state["columns"]
    if (not isinstance(columns, list) or len(columns) > MAX_COLUMNS
            or not all(is_text(text, MAX_COLUMN_CHARACTERS) for text in columns)):
        return None
    return {**clean, "columns": columns}


def choice_options(options) -> dict | None:
    """The options of a question of choice, each a name with what it covers, or None."""
    if (not isinstance(options, dict) or not 2 <= len(options) <= MAX_OPTIONS
            or not all(QUESTION_NAME_PATTERN.fullmatch(name) and is_statement(text) for name, text in options.items())):
        return None
    return dict(options)


def model_questions(questions) -> dict | None:
    """The questions of a request, each a statement whose probability is asked for or a question of choice with
    its options, or None."""
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        return None
    clean = {}
    for name, question in questions.items():
        if (not QUESTION_NAME_PATTERN.fullmatch(name) or not isinstance(question, dict)
                or not is_statement(question.get("instructions"))):
            return None
        if question.get("type") == "choice":
            options = choice_options(question.get("criteria"))
            if options is None:
                return None
            clean[name] = {"type": "choice", "instructions": question["instructions"], "criteria": options}
            continue
        if question.get("type") != "noul":
            return None
        clean[name] = {"type": "noul", "instructions": question["instructions"]}
        if "criteria" in question:
            criteria = question["criteria"]
            if not isinstance(criteria, dict) or not is_statement(criteria.get("true")) or not is_statement(criteria.get("false")):
                return None
            clean[name]["criteria"] = {"true": criteria["true"], "false": criteria["false"]}
    return clean


def model_request(request) -> dict | None:
    """The request for the model with the fields that the page sends and no other, or None."""
    if not isinstance(request, dict) or not isinstance(request.get("model"), str) or not MODEL_PATTERN.fullmatch(request["model"]):
        return None
    state, questions = model_state(request.get("state")), model_questions(request.get("questions"))
    if state is None or questions is None:
        return None
    return {"model": request["model"], "state": state, "questions": questions}


def table_columns(reply) -> list[dict]:
    """Name, type, label and notes of each column of a reply of the DataStore, without its internal column _id."""
    result = reply.get("result") if isinstance(reply, dict) and reply.get("success") is True else None
    fields = result.get("fields") if isinstance(result, dict) and isinstance(result.get("fields"), list) else []
    columns = []
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("id"), str) or field["id"] == "_id":
            continue
        info = field.get("info") if isinstance(field.get("info"), dict) else {}
        columns.append({key: value[:MAX_COLUMN_CHARACTERS] if isinstance(value, str) else ""
                        for key, value in (("id", field["id"]), ("type", field.get("type")),
                                           ("label", info.get("label")), ("notes", info.get("notes")))})
    return columns[:MAX_TABLE_COLUMNS]


def sent_by_the_page(body: bytes) -> tuple[str, dict] | None:
    """Key and request of the body of a POST request of the page, or None for anything else."""
    try:
        text = body.decode("utf-8")
        sent = json.loads(text) if len(text) <= MAX_BODY_CHARACTERS else None
    except ValueError:
        return None
    if not isinstance(sent, dict) or not isinstance(sent.get("key"), str) or not KEY_PATTERN.fullmatch(sent["key"]):
        return None
    request = model_request(sent.get("request"))
    return (sent["key"], request) if request else None


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serves the files of the site and answers the three relays."""

    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, **FILE_TYPES}

    def __init__(self, *arguments, site: Path, portal: str, model: str, **options):
        self.site = site
        self.portal = portal
        self.model = model
        super().__init__(*arguments, directory=str(site), **options)

    def do_GET(self):
        parts = urlsplit(self.path)
        if parts.path == build.PROXY_PATH:
            self.relay(parse_qs(parts.query))
        elif parts.path == build.FIELDS_PATH:
            self.relay_fields(parse_qs(parts.query))
        elif parts.path == build.READING_PATH:
            self.refuse_method("POST")
        else:
            super().do_GET()

    def do_POST(self):
        body = self.sent_body()
        if urlsplit(self.path).path == build.READING_PATH:
            self.relay_reading(body)
        else:
            self.refuse_method("GET")

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

    def answer_error(self, status: int, code: str) -> None:
        self.answer(status, JSON_TYPE, json.dumps({"error": code}).encode("utf-8"))

    def sent_body(self) -> bytes:
        """Body of a POST request; nothing when it is longer than a request of the page can be.

        The body is read before any answer is given, so that the connection closes without unread data.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return b""
        return self.rfile.read(length) if 0 < length <= MAX_BODY_BYTES else b""

    def refuse_method(self, allowed: str) -> None:
        self.send_response(405)
        self.send_header("Allow", allowed)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def relay(self, query: dict[str, list[str]]) -> None:
        """Asks the catalogue for one dataset and passes its reply on, or searches it by words and passes on the five
        facts of each dataset found; nothing is kept."""
        if "q" in query:
            self.relay_search(query)
            return
        wanted = catalogue_filter(query)
        if wanted is None:
            self.answer_error(400, "request")
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
            self.answer_error(502, "portal")
            return
        self.answer(200, JSON_TYPE, reply.content)

    def relay_search(self, query: dict[str, list[str]]) -> None:
        search = search_request(query)
        if search is None:
            self.answer_error(400, "request")
            return
        words, count = search
        try:
            reply = requests.get(
                self.portal + "/api/3/action/package_search", params={"q": words, "rows": count},
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=RELAY_TIMEOUT_SECONDS,
            )
            found = found_datasets(reply.json()) if reply.status_code == 200 else None
            if found is None:
                raise ValueError(f"HTTP {reply.status_code}")
        except (requests.RequestException, ValueError):
            self.answer_error(502, "portal")
            return
        self.answer(200, JSON_TYPE, json.dumps(found, ensure_ascii=False).encode("utf-8"))

    def relay_fields(self, query: dict[str, list[str]]) -> None:
        """Asks the DataStore for the structure of at most three tables and passes on their columns, never a row."""
        tables = query.get("resource", [])
        if (not 1 <= len(tables) <= MAX_TABLES or len(set(tables)) != len(tables)
                or not all(UUID_PATTERN.fullmatch(table) for table in tables)):
            self.answer_error(400, "request")
            return
        columns = {}
        for table in tables:
            try:
                reply = requests.get(
                    self.portal + "/api/3/action/datastore_search", params={"resource_id": table, "limit": 0},
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=RELAY_TIMEOUT_SECONDS,
                )
                columns[table] = table_columns(reply.json()) if reply.status_code == 200 else []
            except (requests.RequestException, ValueError):
                columns[table] = []
        self.answer(200, JSON_TYPE, json.dumps({"columns": columns}, ensure_ascii=False).encode("utf-8"))

    def relay_reading(self, body: bytes) -> None:
        """Passes a request of the second reading to the model with the key of the visitor; nothing is kept."""
        sent = sent_by_the_page(body) if body and self.headers.get_content_type() == "application/json" else None
        if sent is None:
            self.answer_error(400, "request")
            return
        key, request = sent
        try:
            reply = requests.post(
                self.model, json=request, timeout=MODEL_TIMEOUT_SECONDS,
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json", "User-Agent": USER_AGENT},
            )
            if reply.status_code in (401, 403):
                self.answer_error(401, "key")
                return
            if reply.status_code == 429:
                self.answer_error(429, "limit")
                return
            if reply.status_code != 200:
                raise ValueError(f"HTTP {reply.status_code}")
            reply.json()
        except (requests.RequestException, ValueError):
            self.answer_error(502, "service")
            return
        self.answer(200, JSON_TYPE, reply.content)

    def log_message(self, format, *arguments):
        return


def preview_server(site: Path, port: int = DEFAULT_PORT, portal: str | None = None,
                   model: str | None = None) -> ThreadingHTTPServer:
    """Server of the site on this computer only; port 0 picks a free port."""
    portal = (portal or os.environ.get(build.PORTAL_VARIABLE) or build.DEFAULT_PORTAL).rstrip("/")
    model = model or os.environ.get(MODEL_VARIABLE) or jev.API_URL
    handler = functools.partial(PreviewHandler, site=site, portal=portal, model=model)
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


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
