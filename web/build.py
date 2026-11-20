"""Builds the public site into web/dist.

The pages are written for both languages, the Python files of the checks are packed for the
browser, and two things are fetched once and kept in web/.cache: the Python runtime for the
browser (Pyodide) and the library of the Excel report. Every fetched file is checked against
its SHA-256 before it is used. The build needs only the standard library of Python.

Usage:
    python web/build.py

Environment variables:
    DATAGOVGR_BASE_URL   address of the portal that the page calls (default https://data.gov.gr)
    SITE_PUBLIC          set to 1 to let search engines list the site
"""

import hashlib
import json
import os
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIST = WEB / "dist"
CACHE = WEB / ".cache"
ASSETS = WEB / "assets"
EXAMPLE_RECORD = WEB / "example" / "troxaia-atyxhmata.json"
EXAMPLE_DATE = "2026-10-24"                       # day of the catalogue snapshot that holds the example record
DEFAULT_PORTAL = "https://data.gov.gr"
PORTAL_VARIABLE = "DATAGOVGR_BASE_URL"
PUBLIC_VARIABLE = "SITE_PUBLIC"
PROXY_PATH = "/api/record"                        # relay of the site to the catalogue of the portal
READING_PATH = "/api/reading"                     # relay of the site to the model of the second reading
FIELDS_PATH = "/api/fields"                       # relay of the site to the columns of the tables in the DataStore
ENGINE_VERSION = "314.0.8"
ENGINE_FILES = ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
USER_AGENT = "datagovgr-ai-readiness/0.1 (site build)"
DOWNLOAD_TIMEOUT_SECONDS = 120
ARCHIVE_TIME = (2026, 1, 1, 0, 0, 0)              # one fixed time for every archived file, so that equal content gives equal bytes
LONG_CACHE = "public, max-age=31536000, immutable"

# Files that the checks need inside the browser, with their place in the repository.
CHECK_FILES = (
    "aiready/__init__.py", "aiready/assessment.py", "aiready/criteria.py", "aiready/identifier.py", "aiready/jev.py",
    "aiready/metadata_checks.py", "aiready/plain_language.py", "aiready/records.py", "aiready/report.py",
    "aiready/report_excel.py", "aiready/second_reading.py", "aiready/texts.py", "aiready/locales/el.json",
    "aiready/locales/en.json",
    "scripts/04_metadata_checks.py", "criteria/criteria.csv", "data/reference/eu_file_type.csv",
    "web/__init__.py", "web/browser.py", "web/icons.py", "web/pages.py", "web/release.py", "web/shims/pandas.py",
)


@dataclass(frozen=True)
class Download:
    name: str      # file name in the cache
    url: str
    sha256: str


@dataclass(frozen=True)
class Downloads:
    engine: Download                 # archive of the Pyodide package
    wheels: tuple[Download, ...]     # wheels of the Excel library


DOWNLOADS = Downloads(
    engine=Download(
        f"pyodide-{ENGINE_VERSION}.tgz",
        f"https://registry.npmjs.org/pyodide/-/pyodide-{ENGINE_VERSION}.tgz",
        "9a52704e0ae5b07aaacb8e4fed9f1658e8024694a078695ea45ac79dee4cefcb",
    ),
    wheels=(
        Download(
            "openpyxl-3.1.5-py2.py3-none-any.whl",
            "https://files.pythonhosted.org/packages/c0/da/977ded879c29cbd04de313843e76868e6e13408a94ed6b987245dc7c8506/"
            "openpyxl-3.1.5-py2.py3-none-any.whl",
            "5282c12b107bffeef825f4617dc029afaf41d0ea60823bbb665ef3079dc79de2",
        ),
        Download(
            "et_xmlfile-2.0.0-py3-none-any.whl",
            "https://files.pythonhosted.org/packages/c1/8b/5fe2cc11fee489817272089c4203e679c63b570a5aaeb18d852ae3cbba6a/"
            "et_xmlfile-2.0.0-py3-none-any.whl",
            "7a91720bc756843502c3b7504c77b8fe44217c85c537d85037f0f536151b2caa",
        ),
    ),
)


def short_hash(*parts: bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part)
    return digest.hexdigest()[:10]


def cached_download(download: Download, cache: Path) -> Path:
    """Returns the file of a download from the cache, fetching it first when it is missing or altered.

    Raises RuntimeError when the file cannot be fetched or its SHA-256 is not the expected one;
    a file that fails the check is not kept.
    """
    target = cache / download.name
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == download.sha256:
        return target
    request = urllib.request.Request(download.url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"{download.url} could not be fetched ({error})") from error
    found = hashlib.sha256(data).hexdigest()
    if found != download.sha256:
        raise RuntimeError(f"{download.url} has SHA-256 {found}, expected {download.sha256}")
    cache.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def write_engine(archive: Path, folder: Path) -> None:
    """Writes the files of the Python runtime that the browser loads, out of the archive of its package."""
    folder.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as package:
        for name in ENGINE_FILES:
            try:
                member = package.extractfile(f"package/{name}")
            except KeyError:
                member = None
            if member is None:
                raise RuntimeError(f"{archive.name} holds no file {name}")
            (folder / name).write_bytes(member.read())


def archived(bundle: zipfile.ZipFile, name: str, data: bytes) -> None:
    entry = zipfile.ZipInfo(name, ARCHIVE_TIME)
    entry.compress_type = zipfile.ZIP_DEFLATED
    bundle.writestr(entry, data)


def write_checks_bundle(target: Path) -> None:
    """Packs the Python files of the checks, each under its path in the repository."""
    with zipfile.ZipFile(target, "w") as bundle:
        for name in CHECK_FILES:
            archived(bundle, name, (ROOT / name).read_bytes())


def write_excel_bundle(wheels: list[Path], target: Path) -> None:
    """Joins the wheels of the Excel library into one archive that the browser unpacks when a workbook is asked for."""
    with zipfile.ZipFile(target, "w") as bundle:
        for wheel in wheels:
            with zipfile.ZipFile(wheel) as source:
                for name in sorted(source.namelist()):
                    if not name.endswith("/"):
                        archived(bundle, name, source.read(name))


def ensure_table_reader() -> None:
    """Makes the name pandas importable for the checks: the installed library, or the reader of web/shims."""
    try:
        import pandas  # noqa: F401
    except ImportError:
        sys.path.insert(0, str(WEB / "shims"))


def response_headers(portal: str, indexing: bool) -> dict[str, str]:
    """Headers of every answer of the site: what the pages may load and call, and whether they may be listed."""
    policy = (
        "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' data:; "
        f"font-src 'self'; connect-src 'self' {portal}; object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'"
    )
    headers = {
        "Content-Security-Policy": policy,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Frame-Options": "DENY",
    }
    if not indexing:
        headers["X-Robots-Tag"] = "noindex"
    return headers


def headers_file_text(portal: str, indexing: bool) -> str:
    """Content of the _headers file of Cloudflare Pages."""
    lines = ["/*"] + [f"  {name}: {value}" for name, value in response_headers(portal, indexing).items()]
    for path in (f"/engine/{ENGINE_VERSION}/*", "/assets/fonts/*"):
        lines += [path, f"  Cache-Control: {LONG_CACHE}"]
    return "\n".join(lines) + "\n"


def write_page(path: Path, document: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8", newline="\n")


def write_pages(output: Path, portal: str, indexing: bool, versions: dict[str, str]) -> None:
    """Writes the home page, the page of the second opinion, the guide, the page of the criteria and the terms in
    both languages, and the page of an unknown address."""
    from aiready.criteria import CRITERIA_VERSION, load_criteria
    from aiready.texts import DEFAULT_LANGUAGE, LANGUAGES, load_texts
    from web import browser, pages

    record = json.loads(EXAMPLE_RECORD.read_text(encoding="utf-8"))
    criteria = load_criteria()
    for language in LANGUAGES:
        texts = load_texts(language)
        _, example, _ = browser.explained(record, browser.example_source(EXAMPLE_DATE), language)
        templates = {
            "example-result": pages.result_html(example, texts, example=True),
            "progress-preparing": pages.progress_html(texts, "form.preparing"),
            "progress-loading": pages.progress_html(texts, "form.loading"),
            "error-engine": pages.error_html(texts, "engine"),
            "error-portal": pages.error_html(texts, "portal"),
        }
        home = pages.home_main_html(texts, example) + "".join(
            f'<template id="{name}">{content}</template>' for name, content in templates.items()
        )
        settings = {
            "language": language, "portal": portal, "proxy": PROXY_PATH, "reading": READING_PATH, "fields": FIELDS_PATH,
            "engine": f"/engine/{ENGINE_VERSION}/",
            "checks": f"/engine/checks.zip?v={versions['checks']}",
            "excel": f"/engine/excel.zip?v={versions['excel']}",
            "example-record": f"/example/{EXAMPLE_RECORD.name}",
            "example-date": EXAMPLE_DATE,
        }
        mains = {"home": home, pages.OPINION_PAGE: pages.opinion_main_html(texts), "guide": pages.guide_main_html(texts),
                 pages.CRITERIA_PAGE: pages.criteria_main_html(texts, criteria), "terms": pages.terms_main_html(texts)}
        for page, main in mains.items():
            document = pages.document_html(
                page, texts, main, criteria_version=CRITERIA_VERSION, assets_version=versions["assets"],
                indexing=indexing, settings=settings if page == "home" else {"language": language},
            )
            write_page(output / pages.page_path(page, language).lstrip("/") / "index.html", document)
        if language == DEFAULT_LANGUAGE:
            missing = pages.document_html(
                pages.MISSING_PAGE, texts, pages.missing_main_html(texts), criteria_version=CRITERIA_VERSION,
                assets_version=versions["assets"], settings={"language": language},
            )
            write_page(output / "404.html", missing)


def build_site(output: Path = DIST, cache: Path = CACHE, downloads: Downloads = DOWNLOADS,
               portal: str | None = None, indexing: bool | None = None) -> Path:
    """Writes the whole site into the output folder and returns the folder.

    The folder is emptied first; a folder that is not empty and was not written by an earlier
    build is left alone and RuntimeError is raised.
    """
    from web.icon_images import favicon_ico, touch_icon_png
    from web.icons import favicon_svg

    portal = (portal or os.environ.get(PORTAL_VARIABLE) or DEFAULT_PORTAL).rstrip("/")
    if indexing is None:
        indexing = os.environ.get(PUBLIC_VARIABLE) == "1"
    if output.exists():
        if any(output.iterdir()) and not (output / "_headers").is_file():
            raise RuntimeError(f"{output} is not empty and was not written by an earlier build")
        shutil.rmtree(output)
    engine_archive = cached_download(downloads.engine, cache)
    wheels = [cached_download(wheel, cache) for wheel in downloads.wheels]
    ensure_table_reader()

    shutil.copytree(ASSETS, output / "assets")
    (output / "assets" / "favicon.svg").write_text(favicon_svg(), encoding="utf-8", newline="\n")
    (output / "favicon.ico").write_bytes(favicon_ico())
    (output / "apple-touch-icon.png").write_bytes(touch_icon_png())
    (output / "example").mkdir()
    shutil.copyfile(EXAMPLE_RECORD, output / "example" / EXAMPLE_RECORD.name)
    engine = output / "engine"
    write_engine(engine_archive, engine / ENGINE_VERSION)
    write_checks_bundle(engine / "checks.zip")
    write_excel_bundle(wheels, engine / "excel.zip")
    versions = {
        "assets": short_hash((ASSETS / "style.css").read_bytes(), (ASSETS / "app.js").read_bytes()),
        "checks": short_hash((engine / "checks.zip").read_bytes()),
        "excel": short_hash((engine / "excel.zip").read_bytes()),
    }
    write_pages(output, portal, indexing, versions)
    (output / "_headers").write_text(headers_file_text(portal, indexing), encoding="utf-8", newline="\n")
    return output


def main() -> int:
    try:
        site = build_site()
    except RuntimeError as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    files = [path for path in site.rglob("*") if path.is_file()]
    megabytes = sum(path.stat().st_size for path in files) / 1_000_000
    print(f"Site written to {site.relative_to(ROOT).as_posix()}: {len(files)} files, {megabytes:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
