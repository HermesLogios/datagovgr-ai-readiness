r"""
05_resource_download.py
Phase 3, step 2: download test of the resources of the sample (criterion Q1, availability).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one or the
     one given with --snapshot) and the sample (data/processed/sample.csv).
  2. Downloads every resource of the 36 datasets of the sample, except the automatic
     "download all" ZIP bundle of the portal (DECISIONS.md #13), into
     data/raw/resources/<sample id>/, one file per resource. These files belong to the
     publishing organisations, may contain personal data and are never added to the
     repository (.gitignore; DECISIONS.md #29).
  3. Checks every downloaded file: HTTP status, size, type recognised from its first bytes
     (signature), an attempt to open it, and whether the type is the one declared in the
     metadata.
  4. Writes:
        data/processed/resource_downloads_YYYY-MM-DD.csv   one row per resource: address, result
                                                            of each attempt, size, SHA-256
                                                            checksum, type, outcome
        outputs/resources_YYYY-MM-DD/downloads.md          the result per dataset and the
                                                            proposed score of Q1
     The date in the names is the date of the snapshot, so that the downloads stay paired with
     the metadata they come from; the date of each attempt is recorded in the rows. Neither
     file contains any content of the downloaded files.

Rules of Q1 (DECISIONS.md #37):
  - A resource is available when its address answers with HTTP 2xx (after redirects) with a file
    that is not empty and opens. A web page or an error page instead of the declared file fails.
    A data file of another type than the declared one (e.g. a ZIP archive declared as RAR, zipped
    CSV files declared as CSV) is available; the difference is recorded in the reason and counts
    in Q6, where the real format of the files is scored.
  - A link declared as a file that returns a web page fails. A link declared as a web page
    (format URL, HTML, LINK or none) is available when the page opens; that it is not a file is
    scored by M6.
  - A map or feature service request (WMS, WFS) is tested as it is: available when it answers
    with the declared type; an exception report of the service fails. The bare address of a
    service (declared WMS, WFS, WMTS or WCS, without a request) is tested with the standard
    GetCapabilities request, and the answer of the bare address is recorded as well.
  - An answer of a service without any record (an OAI-PMH list without records, which the
    protocol signals with the error noRecordsMatch) counts as an empty file and fails.
  - A resource without an address fails. An active DataStore table of the portal without an
    address is downloaded from the DataStore dump of the portal.
  - A failure is recorded only after a second attempt on another day (option --retry).
  - Proposed score per dataset: every resource available 2; at least one available and at least
    one failed 1; none available 0. While a failure awaits its second attempt, the score is
    provisional.

How a file "opens": a ZIP archive (Excel, Word and OpenDocument files are ZIP packages too)
passes an integrity test of all its members; a JSON file is parsed; an XML file (GML, KML, RDF,
capabilities documents) is parsed; a PDF has its header and its end marker; a text file (CSV,
TSV, Turtle) decodes as UTF-8, UTF-16 or Greek (Windows-1253, ISO 8859-7); older Office files
(XLS, DOC), images and RAR, GZIP or 7z archives are recognised by their signature. The full
reading of the contents is done in the next script of step 2.

Certificates of the servers are checked through the trust store of the operating system when
the package truststore is installed (requirements.txt), as a web browser does; otherwise
through the certificates bundled with requests.

Usage (from the project root, with the .venv activated):
    python scripts\05_resource_download.py                first attempt, all datasets
    python scripts\05_resource_download.py --only S06     one dataset only (test run)
    python scripts\05_resource_download.py --retry        second attempt of the failures, on another day
    python scripts\05_resource_download.py --report       check the downloaded files again and rebuild the outcomes
                                                          and the report, without downloading
An interrupted run continues where it stopped when it is started again.

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import re
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree

try:
    import truststore
    truststore.inject_into_ssl()
    CERTIFICATES = "trust store of the operating system"
except ImportError:
    CERTIFICATES = "certificates bundled with requests"

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RESOURCES_DIR = RAW_DIR / "resources"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
PORTAL = "https://data.gov.gr"
DATASET_URL = PORTAL + "/dataset/"

HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}
TIMEOUT_SECONDS = (30, 180)      # connection, and waiting time between two parts of the answer
TRIES_PER_RUN = 3                # tries within one run against network errors and server errors
WAIT_BETWEEN_TRIES = (10, 30)    # seconds before the second and the third try
PAUSE_SECONDS = 0.5              # pause between two downloads
CHUNK_BYTES = 1 << 20
HEAD_BYTES = 65536               # first part of a file, read to recognise its type

# Declared formats that do not promise a file type: the link may lead to a page.
PAGE_FORMATS = {"", "URL", "HTML", "HTM", "LINK", "WEB", "WEBPAGE", "WEB PAGE", "ΙΣΤΟΣΕΛΙΔΑ", "UNKNOWN",
                "PHP", "ASP", "ASPX", "ASHX", "JSP", "TASK-FLOW"}
SERVICE_FORMATS = {"WMS", "WFS", "WMTS", "WCS"}
# Types that a declared format accepts: specific types or families (see TYPE_FAMILY).
EXPECTED_TYPES = {
    "CSV": {"text"}, "TSV": {"text"}, "TXT": {"text"}, "RTF": {"text"},
    "JSON": {"json"}, "GEOJSON": {"json"}, "TOPOJSON": {"json"}, "JSON_LD": {"json"}, "JSONLD": {"json"},
    "XML": {"xml"}, "GML": {"xml"}, "GML2": {"xml"}, "GML3": {"xml"}, "ATOM": {"xml"}, "RSS": {"xml"},
    "KML": {"xml", "kmz"}, "KMZ": {"kmz", "zip"}, "RDF": {"xml", "text"}, "RDF_XML": {"xml"},
    "TTL": {"text"}, "TURTLE": {"text"}, "RDF_TURTLE": {"text"}, "N3": {"text"},
    "WMS": {"xml", "image"}, "WMTS": {"xml", "image"}, "WFS": {"xml", "json", "text", "zip"}, "WCS": {"xml", "image"},
    "CSW": {"xml"}, "ESRI REST": {"json"}, "ARCGIS GEOSERVICES REST API": {"json"},
    "XLS": {"ole2", "xlsx"}, "XLSX": {"xlsx", "ole2"}, "EXCEL": {"ole2", "xlsx"}, "ODS": {"ods"},
    "DOC": {"ole2", "docx"}, "DOCX": {"docx", "ole2"}, "ODT": {"odt"}, "PDF": {"pdf"},
    "ZIP": {"zip"}, "RAR": {"rar"}, "7Z": {"7z"}, "GZ": {"gzip"}, "GZIP": {"gzip"},
    "SHP": {"zip"}, "SHP ZIP": {"zip"}, "SHAPE-ZIP": {"zip"}, "SHAPEZIP": {"zip"}, "SHAPEFILE": {"zip"},
    "PNG": {"png"}, "JPEG": {"jpeg"}, "JPG": {"jpeg"}, "GIF": {"gif"}, "TIF": {"tiff"}, "TIFF": {"tiff"},
    "GEOTIFF": {"tiff"}, "DWG": {"dwg"},
}
TYPE_FAMILY = {
    "xlsx": "zip", "docx": "zip", "ods": "zip", "odt": "zip", "kmz": "zip", "shapefile": "zip", "gtfs": "zip",
    "zip": "zip", "png": "image", "jpeg": "image", "gif": "image", "tiff": "image", "turtle": "text",
}
SIGNATURES = [
    (b"%PDF", "pdf"), (b"PK\x03\x04", "zip"), (b"PK\x05\x06", "zip"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "ole2"), (b"Rar!\x1a\x07", "rar"), (b"\x1f\x8b", "gzip"),
    (b"7z\xbc\xaf\x27\x1c", "7z"), (b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"), (b"II*\x00", "tiff"), (b"MM\x00*", "tiff"), (b"AC10", "dwg"),
]
TEXT_ENCODINGS = ("utf-8-sig", "utf-16", "cp1253", "iso-8859-7")
IRI_START = re.compile(r"<(?:https?|urn|ftp|file):", re.IGNORECASE)
OAI_ERROR = re.compile(r"<(?:\w+:)?error\s+code=")        # error answer of an OAI-PMH service
OAI_LIST = re.compile(r"<(?:\w+:)?(?:listrecords|listidentifiers)[\s>/]")
EXTENSIONS = {
    "pdf": "pdf", "zip": "zip", "xlsx": "xlsx", "docx": "docx", "ods": "ods", "odt": "odt", "kmz": "kmz",
    "shapefile": "zip", "gtfs": "zip", "rar": "rar", "gzip": "gz", "7z": "7z", "png": "png", "jpeg": "jpg",
    "gif": "gif", "tiff": "tif", "dwg": "dwg", "html": "html", "xml": "xml", "service-error": "xml",
    "json": "json", "turtle": "ttl", "text": "txt", "no-records": "xml", "unknown": "bin",
}

FIELDS = [
    "sample_id", "dataset", "resource_id", "position", "resource", "declared_format", "address", "address_source",
    "attempt_1_date", "attempt_1_http_status", "attempt_1_bytes", "attempt_1_type", "attempt_1_opens",
    "attempt_1_note", "attempt_1_result", "attempt_1_reason",
    "attempt_2_date", "attempt_2_http_status", "attempt_2_bytes", "attempt_2_type", "attempt_2_opens",
    "attempt_2_note", "attempt_2_result", "attempt_2_reason",
    "endpoint_as_is", "outcome", "reason", "final_host", "content_type", "bytes", "sha256", "detected_type", "file",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def relative(path: Path) -> str:
    """A path relative to the project root, with forward slashes on every operating system."""
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


def newest_snapshot() -> Path:
    candidates = sorted(p for p in RAW_DIR.glob("catalog_*.jsonl.gz") if "_test" not in p.name)
    if not candidates:
        raise SystemExit("No snapshot found in data/raw. Run 01_snapshot.py first.")
    return candidates[-1]


def snapshot_date(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if not match:
        raise SystemExit(f"The file name {path.name} does not contain a date (YYYY-MM-DD).")
    return match.group(1)


def declared_format(resource: dict) -> str:
    return str(resource.get("format") or "").strip().upper().strip(".")


def is_bundle(resource: dict) -> bool:
    """The automatic "download all" ZIP bundle generated by the portal (DECISIONS.md #13)."""
    return bool(resource.get("downloadall_datapackage_hash"))


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def service_endpoint(url: str, declared: str) -> bool:
    """The bare address of a map or feature service: declared as a service, without a request."""
    if declared not in SERVICE_FORMATS:
        return False
    keys = {key.lower() for key, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True)}
    return "request" not in keys


def capabilities_url(url: str, declared: str) -> str:
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key.lower() not in ("service", "request")]
    query += [("service", declared), ("request", "GetCapabilities")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def without_fragment(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


# ---------------------------------------------------------------------------
# Recognising and opening a file
# ---------------------------------------------------------------------------

def decode(data: bytes, partial: bool = False) -> str | None:
    """The text of a file, or None when it is not text. With partial=True the data are the first part of a
    file, which may end in the middle of a character: an incomplete character at the end is ignored."""
    for encoding in TEXT_ENCODINGS:
        if encoding == "utf-16" and not data.startswith((b"\xff\xfe", b"\xfe\xff")):
            continue
        try:
            return data.decode(encoding)
        except UnicodeDecodeError as error:
            if partial and encoding == "utf-8-sig" and error.start >= len(data) - 3:
                try:
                    return data[:error.start].decode(encoding)
                except UnicodeDecodeError:
                    continue
    return None


def zip_type(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            lower = [name.lower() for name in names]
            if "[content_types].xml" in lower and any(name.startswith("xl/") for name in lower):
                return "xlsx"
            if "[content_types].xml" in lower and any(name.startswith("word/") for name in lower):
                return "docx"
            if "mimetype" in lower:
                kind = archive.read(names[lower.index("mimetype")])[:100]
                if b"spreadsheet" in kind:
                    return "ods"
                if b"opendocument.text" in kind:
                    return "odt"
            if any(name.endswith(".kml") for name in lower):
                return "kmz"
            if any(name.endswith(".shp") for name in lower):
                return "shapefile"
            if {"stops.txt", "routes.txt"} <= {name.rsplit("/", 1)[-1] for name in lower}:
                return "gtfs"
    except (zipfile.BadZipFile, OSError, KeyError):
        pass
    return "zip"


def detect_type(path: Path) -> str:
    """The type of a downloaded file, from its first bytes."""
    with open(path, "rb") as handle:
        head = handle.read(HEAD_BYTES)
    if not head:
        return "empty"
    for signature, kind in SIGNATURES:
        if head.startswith(signature):
            return zip_type(path) if kind == "zip" else kind
    text = decode(head, partial=len(head) == HEAD_BYTES)
    if text is None:
        return "unknown"
    start = text.lstrip("\ufeff \t\r\n")
    lower = start[:4096].lower()
    if IRI_START.match(start):
        return "turtle"            # Turtle or N-Triples that begin with a full IRI, e.g. <http://...>
    if start.startswith("<"):
        if "<html" in lower or "<!doctype html" in lower:
            return "html"
        if "serviceexceptionreport" in lower or "exceptionreport" in lower or OAI_ERROR.search(lower):
            return "service-error"
        if OAI_LIST.search(lower) and "<record" not in lower and "<header" not in lower and "resumptiontoken" not in lower:
            return "no-records"    # an OAI-PMH list without any record, instead of the error noRecordsMatch
        return "xml"
    if start.startswith(("{", "[")):
        return "json"
    if start.startswith(("@prefix", "@base", "PREFIX", "BASE")) or re.match(r"<https?://", start):
        return "turtle"
    return "text"


def service_error_detail(path: Path) -> str:
    """The code or the message of an error answer of a service (OGC exception report, OAI-PMH error)."""
    with open(path, "rb") as handle:
        text = decode(handle.read(HEAD_BYTES), partial=True) or ""
    code = re.search(r"(?:exceptionCode|code)\s*=\s*[\"']([^\"']+)[\"']", text)
    message = re.search(r"<(?:\w+:)?(?:ServiceException|ExceptionText|error)[^>]*>\s*([^<]{1,150})", text)
    parts = [code.group(1) if code else "", message.group(1).strip() if message else ""]
    return ": ".join(part for part in parts if part)


def opens(path: Path, kind: str) -> tuple[bool, str]:
    """An attempt to open the file with a program for its type: (opens, note)."""
    try:
        if TYPE_FAMILY.get(kind) == "zip" or kind == "zip":
            with zipfile.ZipFile(path) as archive:
                damaged = archive.testzip()
            return (damaged is None, f"damaged member {damaged}" if damaged else "")
        if kind == "json":
            raw = path.read_bytes()
            text = decode(raw)
            if text is None:
                return False, "not readable as text"
            json.loads(text)
            return True, ""
        if kind in ("xml", "service-error", "no-records"):
            for _ in ElementTree.iterparse(str(path)):
                pass
            return True, service_error_detail(path) if kind == "service-error" else ""
        if kind == "pdf":
            with open(path, "rb") as handle:
                handle.seek(max(0, path.stat().st_size - 2048))
                tail = handle.read()
            return (b"%%EOF" in tail, "" if b"%%EOF" in tail else "no end marker: the PDF is incomplete")
        if kind in ("text", "turtle", "html"):
            with open(path, "rb") as handle:
                data = handle.read()
            return (decode(data) is not None, "" if decode(data) is not None else "not readable as text")
        if kind == "unknown":
            return False, "type not recognised"
        return True, ""          # recognised by its signature: XLS, DOC, images, RAR, GZIP, 7z
    except (zipfile.BadZipFile, ElementTree.ParseError, json.JSONDecodeError, OSError, ValueError) as error:
        return False, f"{type(error).__name__}: {str(error)[:120]}"


def judge(declared: str, endpoint: bool, status, size, kind: str, opened, note: str) -> tuple[str, str]:
    """The result of one attempt, from what was recorded: ("available" or "failed", reason)."""
    if status in (None, ""):
        return "failed", note or "no answer"
    status = int(float(status))
    if not 200 <= status < 300:
        return "failed", f"HTTP {status}"
    if int(float(size or 0)) == 0 or kind == "empty":
        return "failed", "empty file"
    if kind == "no-records":
        return "failed", "the service answered with an empty list: no records"
    if kind == "service-error":
        what = "capabilities" if endpoint else "data"
        return "failed", f"error answer of the service instead of the declared {what}" + (f" ({note})" if note else "")
    page_allowed = declared in PAGE_FORMATS
    if kind == "html" and not page_allowed:
        target = "service" if declared in SERVICE_FORMATS or declared in ("ESRI REST", "ARCGIS GEOSERVICES REST API") else "file"
        return "failed", f"web page instead of the declared {target}"
    if str(opened) not in ("True", "true", "1"):
        return "failed", f"the file does not open ({note})" if note else "the file does not open"
    if kind == "html":
        return "available", "web page, as declared"
    expected = EXPECTED_TYPES.get(declared)
    if expected and not page_allowed and kind not in expected and TYPE_FAMILY.get(kind) not in expected:
        return "available", f"data file of another type than the declared one: declared {declared}, found {kind}"
    return "available", ""


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------

def extension_for(kind: str, declared: str) -> str:
    """The file extension of a downloaded file, from its type and its declared format."""
    if kind == "ole2":
        return "doc" if declared in ("DOC", "DOCX") else "xls"
    if kind == "text" and declared in ("CSV", "TSV"):
        return declared.lower()
    if kind == "json" and declared == "GEOJSON":
        return "geojson"
    if kind == "xml" and declared in ("GML", "KML", "RDF"):
        return declared.lower()
    return EXTENSIONS.get(kind, "bin")


def download(session: requests.Session, url: str, target_stem: Path, declared: str) -> dict:
    """Downloads one address into target_stem.<extension>: the facts of the attempt."""
    part = target_stem.with_suffix(".part")
    last_error = ""
    for try_number in range(1, TRIES_PER_RUN + 1):
        try:
            with session.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS, stream=True, allow_redirects=True) as answer:
                status = answer.status_code
                if status in (429, 500, 502, 503, 504) and try_number < TRIES_PER_RUN:
                    last_error = f"HTTP {status}"
                    time.sleep(WAIT_BETWEEN_TRIES[try_number - 1])
                    continue
                digest = hashlib.sha256()
                size = 0
                total = int(answer.headers.get("Content-Length") or 0) or None
                part.parent.mkdir(parents=True, exist_ok=True)
                with open(part, "wb") as handle, tqdm(total=total, unit="B", unit_scale=True, leave=False,
                                                       disable=(total or 0) < 5_000_000) as bar:
                    for chunk in answer.iter_content(CHUNK_BYTES):
                        handle.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                        bar.update(len(chunk))
                kind = detect_type(part)
                for old in target_stem.parent.glob(target_stem.name + ".*"):
                    if old != part:
                        old.unlink()
                final = target_stem.with_suffix("." + extension_for(kind, declared))
                part.replace(final)
                opened, note = opens(final, kind)
                return {
                    "http_status": status, "bytes": size, "type": kind, "opens": opened, "note": note,
                    "final_host": urlsplit(answer.url).netloc, "content_type": answer.headers.get("Content-Type", ""),
                    "sha256": digest.hexdigest(), "file": relative(final),
                }
        except requests.exceptions.SSLError as error:
            last_error = f"certificate error: {str(error)[:150]}"
        except requests.exceptions.Timeout:
            last_error = "no answer within the time limit"
        except requests.exceptions.TooManyRedirects:
            last_error = "too many redirects"
            break
        except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema):
            last_error = "invalid address"
            break
        except requests.exceptions.RequestException as error:
            last_error = f"connection error: {type(error).__name__}"
        if part.exists():
            part.unlink()
        if try_number < TRIES_PER_RUN:
            time.sleep(WAIT_BETWEEN_TRIES[try_number - 1])
    return {"http_status": "", "bytes": 0, "type": "", "opens": False, "note": last_error,
            "final_host": "", "content_type": "", "sha256": "", "file": ""}


def address_of(resource: dict) -> tuple[str, str]:
    """The address to download and its source: the url of the resource, the DataStore dump, or none."""
    url = str(resource.get("url") or "").strip()
    if url:
        return url, "url"
    if resource.get("datastore_active"):
        return f"{PORTAL}/datastore/dump/{resource.get('id')}?format=csv", "DataStore dump"
    return "", "none"


def attempt(session: requests.Session, row: dict, number: int, today: str) -> None:
    """One attempt for one resource: downloads, checks and records it in the row."""
    declared = row["declared_format"]
    prefix = f"attempt_{number}_"
    row[prefix + "date"] = today
    if row["address_source"] == "none":
        row.update({prefix + "http_status": "", prefix + "bytes": 0, prefix + "type": "", prefix + "opens": False,
                    prefix + "note": "no address", prefix + "result": "failed", prefix + "reason": "no address"})
        return
    target = RESOURCES_DIR / row["sample_id"] / f"r{int(row['position']):03d}_{row['resource_id'][:8]}"
    url = without_fragment(row["address"])
    endpoint = service_endpoint(url, declared)
    if endpoint:
        as_is = download(session, url, target.with_name(target.name + "_as_is"), declared)
        row["endpoint_as_is"] = (f"HTTP {as_is['http_status']}, {as_is['type']}" if as_is["http_status"] != ""
                                 else as_is["note"])
        time.sleep(PAUSE_SECONDS)
        url = capabilities_url(url, declared)
    facts = download(session, url, target, declared)
    result, reason = judge(declared, endpoint, facts["http_status"], facts["bytes"], facts["type"], facts["opens"], facts["note"])
    row.update({prefix + "http_status": facts["http_status"], prefix + "bytes": facts["bytes"],
                prefix + "type": facts["type"], prefix + "opens": facts["opens"], prefix + "note": facts["note"],
                prefix + "result": result, prefix + "reason": reason})
    if facts["file"]:
        row.update({key: facts[key] for key in ("final_host", "content_type", "sha256", "file")})
        row["bytes"] = facts["bytes"]
        row["detected_type"] = facts["type"]


def settle(row: dict) -> None:
    """The outcome of a resource from its attempts (rule: a failure needs a second attempt on another day)."""
    first, second = row.get("attempt_1_result", ""), row.get("attempt_2_result", "")
    if second:
        row["outcome"], row["reason"] = second, row.get("attempt_2_reason", "")
        if second == "available" and first == "failed":
            row["reason"] = f"failed on the first day ({row.get('attempt_1_reason', '')}), available on the second"
    elif first == "available":
        row["outcome"], row["reason"] = "available", row.get("attempt_1_reason", "")
    elif first == "failed":
        if row.get("attempt_1_reason") == "no address":
            row["outcome"], row["reason"] = "failed", "no address"
        else:
            row["outcome"], row["reason"] = "pending", row.get("attempt_1_reason", "")
    else:
        row["outcome"], row["reason"] = "", ""


def recheck(row: dict) -> None:
    """Recognises and opens again the file of the latest attempt that saved one (option --report)."""
    path = ROOT / row["file"] if row.get("file") else None
    if not path or not path.exists():
        return
    number = 2 if row.get("attempt_2_date") and str(row.get("attempt_2_bytes") or "0") not in ("", "0") else 1
    kind = detect_type(path)
    opened, note = opens(path, kind)
    prefix = f"attempt_{number}_"
    if str(row.get(prefix + "http_status") or "") == "":
        return
    row[prefix + "type"], row[prefix + "opens"], row[prefix + "note"] = kind, opened, note
    row["detected_type"] = kind
    extension = extension_for(kind, row["declared_format"])
    if path.suffix != "." + extension:          # a file saved under the extension of an earlier recognition
        renamed = path.with_suffix("." + extension)
        path.replace(renamed)
        row["file"] = relative(renamed)


def rejudge(row: dict) -> None:
    """Applies the rules again to the recorded facts of the attempts (option --report)."""
    endpoint = bool(row.get("endpoint_as_is"))
    for number in (1, 2):
        prefix = f"attempt_{number}_"
        if row.get(prefix + "date") and row.get("address_source") != "none":
            result, reason = judge(row["declared_format"], endpoint, row.get(prefix + "http_status"),
                                   row.get(prefix + "bytes"), row.get(prefix + "type", ""),
                                   row.get(prefix + "opens"), row.get(prefix + "note", ""))
            row[prefix + "result"], row[prefix + "reason"] = result, reason
    settle(row)


# ---------------------------------------------------------------------------
# Reading and writing
# ---------------------------------------------------------------------------

def load_sample(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise SystemExit(f"{relative(path)} not found. Run 03_sample.py first.")
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def sample_resources(snapshot: Path, sample: dict[str, dict]) -> list[dict]:
    """One row per own resource of the sample datasets, in the order of the sample and of the resources."""
    rows = []
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("id") not in sample:
                continue
            own = [r for r in record.get("resources") or [] if isinstance(r, dict) and not is_bundle(r)]
            for position, resource in enumerate(own, start=1):
                address, source = address_of(resource)
                rows.append({
                    "sample_id": sample[record["id"]]["sample_id"], "dataset": record.get("name", ""),
                    "resource_id": resource.get("id", ""), "position": position,
                    "resource": re.sub(r"\s+", " ", str(resource.get("name") or "")).strip(),
                    "declared_format": declared_format(resource), "address": address, "address_source": source,
                })
    return sorted(rows, key=lambda row: (row["sample_id"], int(row["position"])))


def read_log(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return {row["resource_id"]: row for row in csv.DictReader(handle)}


def write_log(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def q1_proposal(results: Counter) -> tuple[str, str]:
    available, failed, pending, waiting = results["available"], results["failed"], results["pending"], results[""]
    total = available + failed + pending + waiting
    if total == 0:
        return "0", "no resources"
    if waiting:
        return "-", f"{waiting} of {total} resources not attempted yet"
    if available == total:
        return "2", "every resource available"
    if available == 0:
        score = "0"
        reason = "no resource available"
    else:
        score = "1"
        reason = f"{failed + pending} of {total} resources not available"
    if pending:
        return f"{score} (provisional)", f"{reason}; {pending} awaiting a second attempt"
    return score, reason


def write_report(path: Path, rows: list[dict], date: str, titles: dict[str, str]) -> None:
    by_dataset: dict[str, list[dict]] = {}
    for row in rows:
        by_dataset.setdefault(row["sample_id"], []).append(row)
    outcomes = Counter(row.get("outcome", "") for row in rows)
    dates = sorted({row.get(f"attempt_{n}_date", "") for row in rows for n in (1, 2)} - {""})
    lines = [
        f"# Download test of the resources of the sample: snapshot of {date}",
        "",
        f"Resources of the 36 datasets, without the automatic ZIP bundle of the portal: {len(rows)}. "
        f"Available: {outcomes['available']}; failed: {outcomes['failed']}; awaiting a second attempt: "
        f"{outcomes['pending']}; not attempted yet: {outcomes['']}. Dates of the attempts: "
        f"{', '.join(dates) if dates else 'none'}. The downloaded files are kept outside the repository; this "
        "report contains no content of them. Proposed scores of Q1 follow DECISIONS.md #37 and are confirmed or "
        "corrected in the manual assessment.",
        "",
        "| ID | Dataset | Resources | Available | Failed | Awaiting | Proposed Q1 | Reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    proposals = Counter()
    for sample_id in sorted(by_dataset):
        items = by_dataset[sample_id]
        results = Counter(row.get("outcome", "") for row in items)
        score, reason = q1_proposal(results)
        proposals[score] += 1
        failures = Counter(row.get("reason", "") for row in items if row.get("outcome") in ("failed", "pending"))
        if failures:
            reason += ": " + "; ".join(f"{text} ({count})" if count > 1 else text for text, count in failures.most_common())
        name = items[0]["dataset"]
        lines.append(f"| {sample_id} | [{md_cell(titles.get(sample_id, name))}]({DATASET_URL}{name}) | {len(items)} | "
                     f"{results['available']} | {results['failed']} | {results['pending']} | {score} | {md_cell(reason)} |")
    lines += ["", "Proposed scores: " + ", ".join(f"{score}: {count}" for score, count in sorted(proposals.items())) + "."]
    reasons = Counter(row.get("reason", "") for row in rows if row.get("outcome") in ("failed", "pending"))
    if reasons:
        lines += ["", "| Reason of the failures | Resources |", "| --- | ---: |"]
        for text, count in reasons.most_common():
            lines.append(f"| {md_cell(text)} | {count} |")
    types = Counter(row.get("detected_type", "") for row in rows if row.get("detected_type"))
    if types:
        lines += ["", "| Type found in the downloaded files | Resources |", "| --- | ---: |"]
        for text, count in types.most_common():
            lines.append(f"| {text} | {count} |")
    endpoints = [row for row in rows if row.get("endpoint_as_is")]
    if endpoints:
        lines += ["", f"Bare service addresses tested with GetCapabilities: {len(endpoints)}. Answer of the bare "
                  "address, as a visitor who clicks the link receives it: " + "; ".join(
                      f"{text} ({count})" for text, count in Counter(row["endpoint_as_is"] for row in endpoints).most_common()) + "."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Download test of the resources of the sample (criterion Q1).")
    parser.add_argument("--snapshot", type=Path, default=None, help="catalogue snapshot (default: the newest in data/raw)")
    parser.add_argument("--sample", type=Path, default=SAMPLE_FILE, help="sample file (default: data/processed/sample.csv)")
    parser.add_argument("--only", nargs="+", metavar="ID", help="sample ids to download, e.g. S06 (test run)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--retry", action="store_true", help="second attempt of the failures, on another day")
    mode.add_argument("--report", action="store_true",
                      help="check the downloaded files again and rebuild the outcomes and the report, without downloading")
    args = parser.parse_args()

    snapshot = args.snapshot or newest_snapshot()
    if not snapshot.exists():
        raise SystemExit(f"{relative(snapshot)} not found.")
    date = snapshot_date(snapshot)
    sample = load_sample(args.sample)
    titles = {row["sample_id"]: row.get("title", "") for row in sample.values()}
    log_file = PROCESSED_DIR / f"resource_downloads_{date}.csv"
    report_file = OUT_DIR / f"resources_{date}" / "downloads.md"
    today = dt.date.today().isoformat()

    rows = sample_resources(snapshot, sample)
    recorded = read_log(log_file)
    for row in rows:
        row.update({key: value for key, value in recorded.get(row["resource_id"], {}).items()
                    if key not in ("sample_id", "dataset", "resource_id", "position", "resource", "declared_format",
                                   "address", "address_source")})
    wanted = {item.upper() for item in args.only} if args.only else None
    unknown = (wanted or set()) - {row["sample_id"] for row in rows}
    if unknown:
        raise SystemExit(f"Not in the sample: {', '.join(sorted(unknown))}.")

    print(f"Snapshot: {relative(snapshot)}")
    print(f"Resources of the sample (without the automatic ZIP bundle): {len(rows)}")
    print(f"Certificates checked through the {CERTIFICATES}.")

    if args.report:
        print("Checking the downloaded files again, without downloading.")
        for row in rows:
            recheck(row)
            rejudge(row)
    else:
        number = 2 if args.retry else 1
        todo, too_early = [], 0
        for row in rows:
            if wanted and row["sample_id"] not in wanted:
                continue
            if number == 1 and not row.get("attempt_1_result"):
                todo.append(row)
            elif number == 2 and row.get("outcome") == "pending":
                if row.get("attempt_1_date") == today:
                    too_early += 1
                    continue
                todo.append(row)
        if too_early:
            print(f"{too_early} failures were attempted for the first time today ({today}); the second attempt must be "
                  "made on another day: run --retry again tomorrow.")
        print(f"Attempt {number}: {len(todo)} resources to download into {relative(RESOURCES_DIR)}" + ("" if todo else " (nothing to do)"))
        with requests.Session() as session:
            for index, row in enumerate(todo, start=1):
                label = f"[{index}/{len(todo)}] {row['sample_id']} r{int(row['position']):03d} {row['declared_format'] or '-'}"
                print(f"{label}: {row['resource'][:60]}", flush=True)
                attempt(session, row, number, today)
                settle(row)
                write_log(log_file, rows)
                size = int(float(row.get(f"attempt_{number}_bytes") or 0))
                print(f"    {row[f'attempt_{number}_result']}"
                      + (f", {size / 1e6:.1f} MB" if size >= 100_000 else f", {size:,} bytes" if size else "")
                      + (f", {row[f'attempt_{number}_type']}" if row.get(f"attempt_{number}_type") else "")
                      + (f": {row[f'attempt_{number}_reason']}" if row.get(f"attempt_{number}_reason") else ""), flush=True)
                time.sleep(PAUSE_SECONDS)
    for row in rows:
        settle(row)
    write_log(log_file, rows)
    write_report(report_file, rows, date, titles)

    outcomes = Counter(row.get("outcome", "") for row in rows)
    print(f"Available: {outcomes['available']}; failed: {outcomes['failed']}; awaiting a second attempt: "
          f"{outcomes['pending']}; not attempted yet: {outcomes['']}")
    if outcomes["pending"]:
        print("The failures are attempted again on another day with: python scripts\\05_resource_download.py --retry")
    print("Files:")
    for path in (log_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
