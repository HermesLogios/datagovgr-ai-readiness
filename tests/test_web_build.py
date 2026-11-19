"""Checks of the build of the static site, with the downloads served from a folder of the test.

Usage:
    python -m unittest discover -s tests
"""

import functools
import hashlib
import io
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from aiready.texts import load_texts
from web import build

ENGINE_TEXT = "engine file "
PAGES = (("index.html", "el"), ("second-opinion/index.html", "el"), ("guide/index.html", "el"),
         ("criteria/index.html", "el"), ("terms/index.html", "el"), ("404.html", "el"), ("en/index.html", "en"),
         ("en/second-opinion/index.html", "en"), ("en/guide/index.html", "en"), ("en/criteria/index.html", "en"),
         ("en/terms/index.html", "en"))
BARE_RUN = """
import json, sys
sys.path[:0] = [sys.argv[1] + "/web/shims", sys.argv[1]]
from web import browser
answer = json.loads(browser.assess_example(open(sys.argv[2], encoding="utf-8").read(), "el", "2026-10-24"))
reader = sys.modules["pandas"].__file__.replace("\\\\", "/")
statements = json.loads(browser.reading_request())["questions"]
print(answer["ok"], answer["title"], len(browser.report_text("md")) > 1000, reader.endswith("web/shims/pandas.py"), len(statements))
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CountingHandler(SimpleHTTPRequestHandler):
    requests: list[str] = []

    def do_GET(self):
        type(self).requests.append(self.path)
        super().do_GET()

    def log_message(self, *arguments):
        pass


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.base = Path(cls.folder.name)
        served = cls.base / "served"
        served.mkdir()
        engine = io.BytesIO()
        with tarfile.open(fileobj=engine, mode="w:gz") as archive:
            for name in build.ENGINE_FILES + ("README.md",):
                data = (ENGINE_TEXT + name).encode("utf-8")
                member = tarfile.TarInfo(f"package/{name}")
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        files = {"engine.tgz": engine.getvalue()}
        for package in ("openpyxl", "et_xmlfile"):
            wheel = io.BytesIO()
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr(f"{package}/__init__.py", f"NAME = '{package}'\n")
            files[f"{package}.whl"] = wheel.getvalue()
        for name, data in files.items():
            (served / name).write_bytes(data)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(CountingHandler, directory=str(served)))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        address = f"http://127.0.0.1:{cls.server.server_port}"
        cls.downloads = build.Downloads(
            engine=build.Download("engine.tgz", f"{address}/engine.tgz", sha256(files["engine.tgz"])),
            wheels=tuple(build.Download(f"{package}.whl", f"{address}/{package}.whl", sha256(files[f"{package}.whl"]))
                         for package in ("openpyxl", "et_xmlfile")),
        )
        cls.cache = cls.base / "cache"
        cls.site = build.build_site(cls.base / "dist", cls.cache, cls.downloads)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.folder.cleanup()

    def text_of(self, path: str, site: Path | None = None) -> str:
        return ((site or self.site) / path).read_text(encoding="utf-8")

    def test_every_page_is_written_in_its_language(self):
        for path, language in PAGES:
            with self.subTest(path=path):
                self.assertIn(f'<html lang="{language}">', self.text_of(path))

    def test_page_of_the_criteria_holds_every_criterion_of_the_criteria_file(self):
        from aiready.criteria import load_criteria
        for path in ("criteria/index.html", "en/criteria/index.html"):
            page = self.text_of(path)
            for code in load_criteria():
                self.assertIn(f'<section class="criterion" id="{code}"', page, path)

    def test_home_page_holds_the_example_and_what_the_script_needs(self):
        home = self.text_of("index.html")
        self.assertIn('<template id="example-result"><article class="result"', home)
        for attribute in ('data-language="el"', 'data-portal="https://data.gov.gr"', 'data-proxy="/api/record"',
                          'data-reading="/api/reading"', f'data-engine="/engine/{build.ENGINE_VERSION}/"',
                          'data-example-date="2026-10-24"'):
            self.assertIn(attribute, home)
        for name in ("progress-preparing", "progress-loading", "error-engine", "error-portal"):
            self.assertIn(f'<template id="{name}">', home)
        self.assertIn(load_texts("en").text("result.example_note"), self.text_of("en/index.html"))

    def test_assets_and_the_example_record_are_copied(self):
        for path in ("assets/style.css", "assets/app.js", "assets/favicon.svg", "assets/fonts/manrope-greek-wght-normal.woff2",
                     "example/troxaia-atyxhmata.json"):
            self.assertTrue((self.site / path).is_file(), path)

    def test_engine_files_come_from_the_archive_and_nothing_else(self):
        folder = self.site / "engine" / build.ENGINE_VERSION
        self.assertEqual(sorted(path.name for path in folder.iterdir()), sorted(build.ENGINE_FILES))
        self.assertEqual((folder / "pyodide.mjs").read_text(encoding="utf-8"), ENGINE_TEXT + "pyodide.mjs")

    def test_excel_bundle_joins_the_two_libraries(self):
        with zipfile.ZipFile(self.site / "engine" / "excel.zip") as archive:
            self.assertEqual(sorted(archive.namelist()), ["et_xmlfile/__init__.py", "openpyxl/__init__.py"])

    def test_checks_bundle_runs_with_the_standard_library_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            with zipfile.ZipFile(self.site / "engine" / "checks.zip") as archive:
                names = archive.namelist()
                archive.extractall(folder)
            self.assertNotIn("aiready/portal.py", names)
            self.assertNotIn("aiready/jev_trial.py", names)
            for name in ("aiready/jev.py", "aiready/second_reading.py", "web/release.py"):
                self.assertIn(name, names)
            done = subprocess.run(
                [sys.executable, "-S", "-X", "utf8", "-c", BARE_RUN, folder, str(build.EXAMPLE_RECORD)],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(done.stdout.strip(), "True Τροχαία ατυχήματα True True 5", done.stderr)

    def test_headers_allow_only_the_site_and_the_portal_and_keep_search_engines_out(self):
        headers = self.text_of("_headers")
        self.assertIn("connect-src 'self' https://data.gov.gr;", headers)
        self.assertIn("X-Robots-Tag: noindex", headers)
        self.assertIn(f"/engine/{build.ENGINE_VERSION}/*", headers)
        self.assertIn('<meta name="robots" content="noindex">', self.text_of("index.html"))

    def test_second_build_reads_the_cache(self):
        before = len(CountingHandler.requests)
        build.build_site(self.base / "dist-again", self.cache, self.downloads)
        self.assertEqual(len(CountingHandler.requests), before)

    def test_file_that_differs_from_its_hash_is_refused_and_not_kept(self):
        wrong = build.Download("engine-other.tgz", self.downloads.engine.url, "0" * 64)
        with self.assertRaises(RuntimeError):
            build.cached_download(wrong, self.cache)
        self.assertFalse((self.cache / "engine-other.tgz").exists())

    def test_public_site_with_another_portal_address(self):
        site = build.build_site(self.base / "dist-public", self.cache, self.downloads, portal="http://127.0.0.1:9", indexing=True)
        home = self.text_of("index.html", site)
        self.assertIn('data-portal="http://127.0.0.1:9"', home)
        self.assertNotIn('name="robots"', home)
        headers = self.text_of("_headers", site)
        self.assertIn("connect-src 'self' http://127.0.0.1:9;", headers)
        self.assertNotIn("X-Robots-Tag", headers)
        self.assertIn('name="robots"', self.text_of("404.html", site))


if __name__ == "__main__":
    unittest.main()
