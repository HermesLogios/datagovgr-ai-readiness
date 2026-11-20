"""Stand-in for the address of Jev on this computer, for the tests of the trial and of the relays."""

import contextlib
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

LOCAL_ADDRESSES = {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}


class ModelStub(BaseHTTPRequestHandler):
    """Answers from the list prepared by a test and keeps the headers and the body of what it received.

    Without a prepared reply it answers every statement of the request with a fixed probability: 0.9 for the
    statement contents and 0.1 for the others.
    """

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.received.append((dict(self.headers.items()), body))
        if self.server.replies:
            status, headers, reply = self.server.replies.pop(0)
        else:
            answers = {}
            for key, question in body["questions"].items():
                if question.get("type") == "choice":
                    options = list(question["criteria"])
                    answers[key] = {"type": "choice", "choice": options[0], "confidence": 0.8,
                                    "probabilities": {option: 0.8 if option == options[0] else 0.0 for option in options}}
                else:
                    answers[key] = {"type": "noul", "noul": 0.9 if key == "contents" else 0.1}
            status, headers, reply = 200, {}, {"model": body["model"], "answers": answers, "usage": {"input_tokens": 700}}
        content = reply.encode("utf-8") if isinstance(reply, str) else json.dumps(reply).encode("utf-8")
        self.answer(status, headers, content)

    def do_OPTIONS(self):
        headers = {"Access-Control-Allow-Origin": self.server.page_origin} if self.server.page_origin else {}
        self.answer(204, headers, b"")

    def answer(self, status: int, headers: dict, content: bytes) -> None:
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *arguments) -> None:
        pass


@contextlib.contextmanager
def model_stub(replies=(), page_origin=""):
    """Server of the stand-in and its address; calls to this computer bypass any proxy while it runs."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelStub)
    server.replies, server.received, server.page_origin = list(replies), [], page_origin
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with mock.patch.dict(os.environ, LOCAL_ADDRESSES):
            yield server, f"http://127.0.0.1:{server.server_port}/v1/systemone"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
