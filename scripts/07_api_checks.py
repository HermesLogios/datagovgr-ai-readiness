r"""
07_api_checks.py
Phase 3, step 3: test of the means of programmatic access to the high-value datasets of the sample (criterion M10,
API and bulk download; Regulation (EU) 2023/138, Article 3).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one), the sample
     (data/processed/sample.csv), the download log of 05_resource_download.py, the file profiles of
     06_file_checks.py and the organisation of the files (criteria/file_organisation.csv).
  2. Finds, for every high-value dataset of the sample, the resources that declare an API: an active DataStore
     table of the portal, a WFS request of a publisher, an ArcGIS REST service or portal item; and the addresses of
     WFS requests and of ArcGIS REST services written in the description of the dataset or of its resources.
  3. Calls every API anonymously, without an account, a cookie or a key, and asks only for what describes the
     service and for the number of its records, never for the records themselves:
        DataStore   datastore_search with limit=0: whether the table exists, its fields, its number of records
        WFS         GetCapabilities (title, fees, access constraints, provider, whether the layer is listed) and
                    GetFeature with resultType=hits (number of features)
        ArcGIS      the item of the portal (public or not, kind, address of the service, terms of use), the
                    description of the service (layers and tables) and the number of records of each of them
  4. Compares the number of records that each API gives with the number of records of the downloaded file of the
     same resource (file profiles), within the rows that the reader of the files leaves out (totals, titles,
     sub-headings, notes, empty rows). An ArcGIS service belongs to the dataset as a whole: its largest layer or
     table is compared with all the examined files of the dataset together.
  5. Reads the observations made by hand on the pages of the providers whose terms of use and documentation are not
     part of the answer of the service (criteria/api_providers.csv: the portal, for its DataStore).
  6. Writes:
        data/processed/api_endpoints_YYYY-MM-DD.csv    one row per API tested: address, answer, records through the
                                                        API and in the file, documentation, terms of use
        data/processed/api_checks_YYYY-MM-DD.csv       one row per dataset of the sample: API, bulk download,
                                                        documentation and terms, proposed score of M10
        outputs/api_YYYY-MM-DD/api_checks.md           the same per dataset, with the three columns of the table
                                                        of compliance of the high-value datasets (DECISIONS.md #28)
     The date in the names is the date of the snapshot; the date of each call is recorded in the rows. None of the
     files contains records of the data.

Rules of M10 (DECISIONS.md #45):
  - The criterion applies to the high-value datasets only; the datasets of the comparison group score n/a.
  - An API is a service that answers queries with the data themselves: a WFS, an ArcGIS feature service, the
    DataStore of the portal, an API of the publisher. A map view (WMS), which delivers an image, the API of the
    catalogue, which delivers metadata, and a plain link to a file are not APIs.
  - An API belongs to a dataset when the dataset declares it: as a resource, or as the address of the service
    written in the description of the dataset or of a resource. The pages of maps and applications are not tested.
  - An API counts when it answers anonymously. It serves the dataset completely when it gives at least as many
    records as the examined file of the same resource: at least one examined resource when the files are formats
    or editions of the same data, every examined resource when they are parts of the data. More records than the
    file are recorded (a newer upload, or lines that the reader of the files does not count as records) and do not
    make the API incomplete; fewer records, or one table of a file that holds several, do. A flag of the catalogue
    (active DataStore) proves nothing by itself.
  - Documentation of the API is a public description in a recognised open format: the capabilities document of a
    WFS and the description of an ArcGIS service count; for the DataStore, a page of the portal. Terms of use are a
    published text on the use of the API: the fields Fees and AccessConstraints of a WFS, the terms of use of an
    ArcGIS item, a page of the provider; the licence of the data is not enough.
  - A bulk download is one or more files that give the complete dataset: files of the publisher behind direct
    links, the complete export of a layer through WFS, and the export of the complete list from an application.
    The automatic "download all" ZIP bundle of the portal is not counted (DECISIONS.md #13).
  - Proposed score: 2 for an API that answers anonymously, serves the dataset completely and has documentation and
    terms of use, together with a bulk download; 1 for only one of the two means, or for an API without
    documentation and terms, or one that does not serve the dataset completely; 0 for neither. In the columns of
    the compliance table the API reads yes, partly (it works but does not serve the dataset completely) or no.
  - Exceptions of the Annex of the Regulation (model data of numerical weather prediction through an API only;
    historical versions of Earth observation and environment datasets through an API or a bulk download): no
    dataset of the sample is scored through them.

Certificates of the servers are checked through the trust store of the operating system when the package
truststore is installed (requirements.txt); otherwise through the certificates bundled with requests.

Usage (from the project root, with the .venv activated):
    python scripts\07_api_checks.py                  calls the APIs of all the high-value datasets of the sample
    python scripts\07_api_checks.py --only S10 S18   these datasets only (test run); the rows of the others are kept
    python scripts\07_api_checks.py --report         rebuilds the scores and the report from the recorded answers,
                                                     without calling any service (after a change of
                                                     criteria\api_providers.csv)

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit
from xml.etree import ElementTree

try:
    import truststore
    truststore.inject_into_ssl()
    CERTIFICATES = "trust store of the operating system"
except ImportError:
    CERTIFICATES = "certificates bundled with requests"

import requests

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
ORGANISATION_FILE = ROOT / "criteria" / "file_organisation.csv"
PROVIDERS_FILE = ROOT / "criteria" / "api_providers.csv"
PORTAL = "https://data.gov.gr"

HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}
TIMEOUT_SECONDS = (30, 120)      # connection, and waiting time for the answer
TRIES_PER_CALL = 3               # tries against network errors and server errors
WAIT_BETWEEN_TRIES = (5, 15)     # seconds before the second and the third try
PAUSE_SECONDS = 0.5              # pause between two calls
MAX_LAYERS = 50                  # layers and tables of an ArcGIS service whose records are counted

COMPARISON_GROUP = "comparison"
DATASTORE, WFS, ARCGIS = "DataStore of the portal", "WFS", "ArcGIS REST"

# Types of downloaded files (download log) that deliver data or documents, as opposed to pages, images and the
# capabilities documents of the services.
FILE_TYPES = {"gtfs", "json", "ole2", "xlsx", "pdf", "rar", "shapefile", "text", "turtle", "zip", "7z", "gzip", "ods",
              "docx", "doc"}
XML_DATA_FORMATS = {"KML", "GML", "RDF", "GEOJSON", "XML DATA"}

ENDPOINT_FIELDS = [
    "sample_id", "dataset", "kind", "position", "resource_id", "address", "tested_on", "http_status", "anonymous",
    "works", "answer", "records_api", "records_file", "tables_file", "comparison", "documentation",
    "documentation_evidence", "terms", "terms_evidence", "notes",
]
CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "api_declared", "api_kinds", "api_works", "api_complete",
    "api_documentation", "api_terms", "bulk_download", "bulk_evidence", "m10_score", "m10_reason", "hvd_api",
    "hvd_bulk_download", "hvd_api_terms_and_documentation", "notes",
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


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def is_bundle(resource: dict) -> bool:
    """The automatic "download all" ZIP bundle generated by the portal (DECISIONS.md #13)."""
    return bool(resource.get("downloadall_datapackage_hash"))


def plain_text(value) -> str:
    """A text without HTML tags and repeated spaces."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()


def number(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def with_noun(count: int, noun: str) -> str:
    """A number with its noun, in the singular or in the plural."""
    return f"{count:,} {noun}{'' if count == 1 else 's'}"


def load_datasets(snapshot: Path, sample: dict[str, dict]) -> dict[str, dict]:
    """The records of the snapshot of the datasets of the sample, by sample id."""
    by_id = {row["id"]: row["sample_id"] for row in sample.values()}
    found: dict[str, dict] = {}
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("id") in by_id:
                found[by_id[record["id"]]] = record
    return found


# ---------------------------------------------------------------------------
# Calls
# ---------------------------------------------------------------------------

def call(session: requests.Session, url: str, kind: str) -> dict:
    """One anonymous call: the HTTP status, the parsed answer (JSON object or XML root) and the error, if any."""
    last_error = ""
    for try_number in range(1, TRIES_PER_CALL + 1):
        try:
            answer = session.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS, allow_redirects=True)
            status = answer.status_code
            if status in (429, 500, 502, 503, 504) and try_number < TRIES_PER_CALL:
                last_error = f"HTTP {status}"
                time.sleep(WAIT_BETWEEN_TRIES[try_number - 1])
                continue
            body, error = None, ""
            try:
                body = answer.json() if kind == "json" else ElementTree.fromstring(answer.content)
            except (ValueError, ElementTree.ParseError):
                error = f"the answer is not {'JSON' if kind == 'json' else 'XML'}"
            time.sleep(PAUSE_SECONDS)
            return {"status": status, "body": body, "error": error}
        except requests.exceptions.SSLError as error:
            last_error = f"certificate error: {str(error)[:120]}"
        except requests.exceptions.Timeout:
            last_error = "no answer within the time limit"
        except requests.exceptions.RequestException as error:
            last_error = f"connection error: {type(error).__name__}"
        if try_number < TRIES_PER_CALL:
            time.sleep(WAIT_BETWEEN_TRIES[try_number - 1])
    return {"status": "", "body": None, "error": last_error}


def test_datastore(session: requests.Session, resource: dict) -> dict:
    """The DataStore table of a resource: asked for its fields and the number of its records, not for records."""
    address = f"{PORTAL}/api/3/action/datastore_search?resource_id={resource.get('id')}&limit=0"
    facts = call(session, address, "json")
    row = {"kind": DATASTORE, "address": address, "http_status": facts["status"], "works": "no", "anonymous": "no",
           "documentation": "", "terms": "", "notes": ""}
    body = facts["body"] if isinstance(facts["body"], dict) else {}
    if facts["status"] == 200 and body.get("success") is True:
        result = body.get("result") or {}
        fields = [field for field in result.get("fields") or [] if (field or {}).get("id") != "_id"]
        row.update(works="yes", anonymous="yes", records_api=result.get("total"),
                   answer=f"table with {with_noun(len(fields), 'field')}")
        if result.get("total_was_estimated"):
            row["notes"] = "the number of records is an estimate of the service"
    else:
        message = ""
        if isinstance(body.get("error"), dict):
            message = str(body["error"].get("message") or body["error"].get("__type") or "")[:120]
        row["answer"] = "; ".join(part for part in (f"HTTP {facts['status']}" if facts["status"] else "",
                                                    message, facts["error"]) if part) or "no answer"
        if facts["status"] in (401, 403):
            row["notes"] = "the service asks for authorisation"
    return row


def wfs_request(resource: dict) -> tuple[str, str] | None:
    """The endpoint and the layer of a WFS GetFeature request, or None when the address is not one."""
    url = str(resource.get("url") or "").strip()
    parts = urlsplit(url)
    query = {key.lower(): value for key, value in parse_qsl(parts.query, keep_blank_values=True)}
    if query.get("service", "").lower() != "wfs" or query.get("request", "").lower() != "getfeature":
        return None
    layer = query.get("typenames") or query.get("typename") or ""
    if not layer:
        return None
    return f"{parts.scheme}://{parts.netloc}{parts.path}", layer


def test_wfs(session: requests.Session, endpoint: str, layer: str) -> dict:
    """A WFS layer: the capabilities document of the service and the number of features of the layer."""
    capabilities = f"{endpoint}?service=WFS&request=GetCapabilities&version=2.0.0"
    row = {"kind": WFS, "address": f"{endpoint}?typeNames={layer}", "works": "no", "anonymous": "no",
           "documentation": "no", "terms": "no", "notes": ""}
    facts = call(session, capabilities, "xml")
    row["http_status"] = facts["status"]
    root = facts["body"]
    if facts["status"] != 200 or root is None or "capabilities" not in local_name(root.tag):
        row["answer"] = "; ".join(part for part in (f"HTTP {facts['status']}" if facts["status"] else "",
                                                    facts["error"], "no capabilities document") if part)
        return row
    texts: dict[str, str] = {}
    layers = []
    for element in root.iter():
        name = local_name(element.tag)
        if name in ("fees", "accessconstraints", "providername") and name not in texts:
            texts[name] = (element.text or "").strip()
        elif name == "featuretype":
            for child in element:
                if local_name(child.tag) == "name":
                    layers.append((child.text or "").strip())
    listed = layer in layers or layer.split(":")[-1] in {item.split(":")[-1] for item in layers}
    row.update(documentation="yes",
               documentation_evidence=f"capabilities document of the service ({with_noun(len(layers), 'layer')}"
                                      + (", the layer among them)" if listed else ", the layer is not listed)"))
    fees, constraints = texts.get("fees", ""), texts.get("accessconstraints", "")
    if fees and constraints:
        row.update(terms="yes", terms_evidence=f"capabilities: Fees \"{fees[:60]}\", AccessConstraints "
                                               f"\"{constraints[:60]}\"")
    else:
        row["terms_evidence"] = "capabilities: " + ", ".join(
            f"{label} {'empty' if not value else 'stated'}" for label, value in (("Fees", fees),
                                                                                 ("AccessConstraints", constraints)))
    if texts.get("providername"):
        row["notes"] = f"provider: {texts['providername'][:80]}"
    hits = call(session, f"{endpoint}?service=WFS&version=2.0.0&request=GetFeature&typeNames={quote(layer, safe=':')}"
                         "&resultType=hits", "xml")
    root = hits["body"]
    matched = ""
    if hits["status"] == 200 and root is not None:
        matched = root.attrib.get("numberMatched") or root.attrib.get("numberOfFeatures") or ""
    if str(matched).isdigit():
        row.update(works="yes", anonymous="yes", records_api=int(matched), answer="number of features of the layer")
    else:
        row["answer"] = "; ".join(part for part in (
            f"HTTP {hits['status']}" if hits["status"] else "", hits["error"],
            "the service did not give the number of features") if part)
        if hits["status"] in (401, 403):
            row["notes"] = "the service asks for authorisation"
    return row


def arcgis_address(resource: dict) -> dict | None:
    """What an address of ArcGIS points to: an item of a portal or a service, or None when it is neither."""
    url = str(resource.get("url") or "").strip()
    declared = str(resource.get("format") or "").strip().upper()
    lowered = url.lower()
    service = re.search(r"^(.*?/rest/services/.+?/(?:FeatureServer|MapServer))", url, flags=re.IGNORECASE)
    if service:
        return {"service": service.group(1)}
    item = re.search(r"[0-9a-f]{32}", lowered)
    if item and ("ESRI" in declared or "ARCGIS" in declared or "/apps/" in lowered or "item.html" in lowered):
        parts = urlsplit(url)
        segments = [segment for segment in parts.path.split("/") if segment]
        base = f"{parts.scheme}://{parts.netloc}"
        for marker in ("apps", "home"):
            if marker in segments:
                prefix = "/".join(segments[:segments.index(marker)])
                return {"portal": f"{base}/{prefix}" if prefix else base, "item": item.group(0)}
        return {"portal": base, "item": item.group(0)}
    return None


def test_arcgis(session: requests.Session, target: dict) -> dict:
    """An ArcGIS item or service: whether it is public, its description, its terms and the records it holds."""
    row = {"kind": ARCGIS, "works": "no", "anonymous": "no", "documentation": "no", "terms": "no", "notes": ""}
    service = target.get("service", "")
    notes = []
    if target.get("item"):
        address = f"{target['portal']}/sharing/rest/content/items/{target['item']}?f=json"
        row["address"] = address
        facts = call(session, address, "json")
        row["http_status"] = facts["status"]
        body = facts["body"] if isinstance(facts["body"], dict) else {}
        if "error" in body or facts["status"] != 200 or not body:
            error = body.get("error") if isinstance(body.get("error"), dict) else {}
            row["answer"] = "; ".join(part for part in (
                f"HTTP {facts['status']}" if facts["status"] else "",
                f"error {error.get('code')}" if error.get("code") else "",
                str(error.get("message") or "")[:120], facts["error"]) if part) or "no answer"
            if error.get("code") in (401, 403, 498, 499) or facts["status"] in (401, 403):
                row["notes"] = "the item is not shared with everyone: the portal asks for an account with permission"
            return row
        service = str(body.get("url") or "")
        notes.append(f"item of kind {body.get('type')}, access {body.get('access')}")
        terms = plain_text(body.get("licenseInfo"))
        if terms:
            row.update(terms="yes", terms_evidence=f"terms of use of the item: \"{terms[:80]}\"")
        else:
            row["terms_evidence"] = "the item states no terms of use"
        if not service:
            row["answer"] = "public item without a service address"
            row["notes"] = "; ".join(notes)
            return row
    else:
        row["address"] = service
    row["service"] = service
    facts = call(session, f"{service}?f=json", "json")
    row["http_status"] = row.get("http_status") or facts["status"]
    body = facts["body"] if isinstance(facts["body"], dict) else {}
    if facts["status"] != 200 or "error" in body or not body:
        error = body.get("error") if isinstance(body.get("error"), dict) else {}
        row["answer"] = "; ".join(part for part in (
            f"HTTP {facts['status']}" if facts["status"] else "",
            f"error {error.get('code')}" if error.get("code") else "", str(error.get("message") or "")[:120],
            facts["error"], "the service gave no description") if part)
        if error.get("code") in (401, 403, 498, 499) or facts["status"] in (401, 403):
            notes.append("the service is not open to everyone: it asks for a token or an account with permission")
        row["notes"] = "; ".join(notes)
        return row
    members = [(item.get("id"), "layer") for item in body.get("layers") or []] + \
              [(item.get("id"), "table") for item in body.get("tables") or []]
    described = (f"{with_noun(len(body.get('layers') or []), 'layer')}, "
                 f"{with_noun(len(body.get('tables') or []), 'table')}")
    row.update(documentation="yes", documentation_evidence=f"description of the service ({described})")
    if not row.get("terms_evidence"):
        row["terms_evidence"] = "the service states no terms of use"
    total, counted, counts = 0, 0, []
    for member, kind in members[:MAX_LAYERS]:
        answer = call(session, f"{service}/{member}/query?where=1%3D1&returnCountOnly=true&f=json", "json")
        count = (answer["body"] or {}).get("count") if isinstance(answer["body"], dict) else None
        if isinstance(count, int):
            total += count
            counted += 1
            counts.append(f"{kind} {member}: {count:,}")
    if counted:
        row.update(works="yes", anonymous="yes", records_api=total,
                   answer=f"records of {counted} of {len(members)} layers and tables")
        notes.append("records per layer or table: " + ", ".join(counts))
    else:
        row["answer"] = "the service did not give the number of its records"
    if len(members) > MAX_LAYERS:
        notes.append(f"only the first {MAX_LAYERS} layers and tables were counted")
    row["notes"] = "; ".join(notes)
    return row


# ---------------------------------------------------------------------------
# Files of the datasets (download log and file profiles)
# ---------------------------------------------------------------------------

def file_facts(profiles: list[dict]) -> dict[str, dict]:
    """Per resource id: the records of its data tables, how many tables it holds, the rows that the reader of the
    files left out, whether the resource is examined and the records of its examined tables."""
    facts: dict[str, dict] = {}
    for profile in profiles:
        if profile.get("data_file") != "True":
            continue
        entry = facts.setdefault(profile["resource_id"], {"records": 0, "tables": 0, "extra": 0, "examined": False,
                                                          "examined_records": 0, "position": profile["position"]})
        entry["records"] += number(profile.get("rows"))
        if profile.get("examined") == "True":
            entry["examined_records"] += number(profile.get("rows"))
        entry["tables"] += 1
        entry["extra"] += sum(number(profile.get(key)) for key in (
            "title_rows", "totals_rows", "subheading_rows", "notes_below", "blank_rows_inside", "repeated_headers"))
        entry["extra"] += max(number(profile.get("header_rows")) - 1, 0)
        entry["examined"] = entry["examined"] or profile.get("examined") == "True"
    return facts


def compare(records_api, entry: dict | None) -> str:
    """The records of an API against the records of the file of the same resource: complete (as many records as
    the file, within the rows that the reader of the files leaves out), more records (all the records of the file
    and more: a newer upload, or lines that the reader does not count as records), fewer records, or partial (one
    table of a file that holds several)."""
    if not isinstance(records_api, int) or entry is None:
        return "not comparable"
    if entry["tables"] > 1:
        return "partial" if records_api < entry["records"] else "complete"
    if entry["records"] <= records_api <= entry["records"] + entry["extra"]:
        return "complete"
    return "fewer records" if records_api < entry["records"] else "more records"


SERVED = ("complete", "more records")       # comparisons that mean: the API gives all the records of the file


def largest_member(notes: str) -> int | None:
    """The records of the largest layer or table of an ArcGIS service, read from the notes of its row."""
    counts = [int(text.replace(",", "")) for text in re.findall(r"(?:layer|table) \S+: ([\d,]+)", notes or "")]
    return max(counts) if counts else None


def bulk_download(sample_id: str, log_rows: list[dict], organisation: dict) -> tuple[str, str]:
    """Whether the complete dataset can be downloaded as files, and the evidence."""
    files = [row for row in log_rows if row.get("outcome") == "available" and (
        row.get("detected_type") in FILE_TYPES
        or (row.get("detected_type") == "xml" and row.get("declared_format", "").upper() in XML_DATA_FORMATS))]
    exports = sum(1 for row in files if "request=getfeature" in row.get("address", "").lower())
    if files:
        text = f"{len(files)} file{'s' if len(files) != 1 else ''} behind direct links"
        if exports:
            text += f" ({exports} of them complete exports of a layer through WFS)"
        return "yes", text
    if "_manual" in organisation.get("examined", ""):
        return "yes", "export of the complete list from an application, by hand: " + organisation.get("note", "")[:120]
    return "no", "no file of the dataset could be downloaded (download test)"


# ---------------------------------------------------------------------------
# Tests and scores of the datasets
# ---------------------------------------------------------------------------

def described_addresses(dataset: dict, positions: dict[str, str]) -> list[tuple[str, str, str]]:
    """The addresses written in the description of the dataset and in the descriptions of its resources: where each
    one was found (description of the dataset, or the position of the resource), the id of the resource, if any,
    and the address."""
    texts = [("description", "", dataset.get("notes"))]
    for resource in dataset.get("resources") or []:
        if isinstance(resource, dict) and not is_bundle(resource):
            resource_id = str(resource.get("id") or "")
            texts.append((positions.get(resource_id, "") or resource_id, resource_id, resource.get("description")))
    found = []
    for place, resource_id, text in texts:
        for address in re.findall(r"https?://[^\s\"'<>]+", html.unescape(str(text or ""))):
            address = address.rstrip(".,;)")
            if (place, resource_id, address) not in found:
                found.append((place, resource_id, address))
    return found


def endpoints_of(session: requests.Session, sample_id: str, dataset: dict, positions: dict[str, str],
                 today: str) -> list[dict]:
    """Calls every API that a dataset declares, in its resources or as an address of a service written in its
    descriptions: the rows of the endpoints."""
    rows, seen = [], set()

    def record(found: list[dict], position: str, resource_id: str, origin: str = "") -> None:
        for row in found:
            if row.get("service"):
                seen.add((("service", row["service"]),))
            if origin:
                row["notes"] = "; ".join(part for part in (origin, row.get("notes", "")) if part)
            row.update(sample_id=sample_id, dataset=dataset.get("name", ""), position=position,
                       resource_id=resource_id, tested_on=today)
            rows.append(row)

    for resource in dataset.get("resources") or []:
        if not isinstance(resource, dict) or is_bundle(resource):
            continue
        resource_id = str(resource.get("id") or "")
        position = positions.get(resource_id, "")
        found = []
        if resource.get("datastore_active"):
            print(f"    {position or resource_id}: DataStore", flush=True)
            found.append(test_datastore(session, resource))
        request = wfs_request(resource)
        if request and request not in seen:
            seen.add(request)
            print(f"    {position or resource_id}: WFS {request[1]}", flush=True)
            found.append(test_wfs(session, *request))
        target = arcgis_address(resource)
        key = tuple(sorted(target.items())) if target else None
        if target and key not in seen:
            seen.add(key)
            print(f"    {position or resource_id}: ArcGIS", flush=True)
            found.append(test_arcgis(session, target))
        record(found, position, resource_id)

    # addresses of services written in the descriptions: a WFS request or an ArcGIS REST service counts as declared;
    # the pages of maps and applications do not (a map view is not an API)
    for place, resource_id, address in described_addresses(dataset, positions):
        written = {"url": address}
        origin = "address written in the description of the " + ("resource" if resource_id else "dataset")
        found = []
        request = wfs_request(written)
        if request and request not in seen:
            seen.add(request)
            print(f"    {place}: WFS {request[1]} (address in the description)", flush=True)
            found.append(test_wfs(session, *request))
        target = arcgis_address(written)
        key = tuple(sorted(target.items())) if target else None
        if target and "service" in target and key not in seen:
            seen.add(key)
            print(f"    {place}: ArcGIS (address in the description)", flush=True)
            found.append(test_arcgis(session, target))
        record(found, place, resource_id, origin)
    return rows


def settle_comparisons(rows: list[dict], facts: dict[str, dict]) -> None:
    """Fills, in the rows of the endpoints of one dataset, the records of the files and the comparison with them.
    A DataStore table and a WFS layer are compared with the file of their own resource; an ArcGIS service, which
    belongs to the dataset as a whole, with all the examined files together: it serves them when one of its layers
    or tables holds at least as many records."""
    for row in rows:
        if row["kind"] == ARCGIS:
            together = sum(item["examined_records"] for item in facts.values())
            largest = largest_member(row.get("notes", ""))
            row.update(records_file="", tables_file="", comparison="")
            if row.get("works") == "yes" and together and largest is not None:
                row.update(records_file=together, tables_file=sum(1 for item in facts.values() if item["examined"]),
                           comparison="complete" if largest >= together else "fewer records")
            elif row.get("works") == "yes":
                row["comparison"] = "not comparable"
        else:
            entry = facts.get(row.get("resource_id", ""))
            row.update(records_file=entry["records"] if entry else "", tables_file=entry["tables"] if entry else "",
                       comparison=compare(row.get("records_api"), entry) if row.get("works") == "yes" else "")


def judge(sample_id: str, info: dict, dataset: dict, endpoints: list[dict], log_rows: list[dict], organisation: dict,
          facts: dict[str, dict], providers: dict[str, dict]) -> dict:
    """The proposed score of M10 of a dataset and the three columns of the compliance table."""
    check = {"sample_id": sample_id, "dataset": info.get("name", ""), "group": info.get("group", ""),
             "category": info.get("category", ""), "notes": ""}
    if info.get("group") == COMPARISON_GROUP:
        check.update(m10_score="n/a", m10_reason="dataset of the comparison group: the criterion applies to the "
                                                 "high-value datasets only",
                     hvd_api="-", hvd_bulk_download="-", hvd_api_terms_and_documentation="-")
        return check
    bulk, bulk_evidence = bulk_download(sample_id, log_rows, organisation)
    working = [row for row in endpoints if row.get("works") == "yes"]
    kinds = list(dict.fromkeys(row["kind"] for row in endpoints))

    # documentation and terms: from the answer of the service, or from the observations made by hand
    for row in endpoints:
        if row["kind"] == DATASTORE:
            provider = providers.get(urlsplit(PORTAL).netloc, {}) if row.get("works") == "yes" else None
            if provider is None:
                row.update(documentation="", documentation_evidence="", terms="", terms_evidence="")
                continue
            row["documentation"] = provider.get("documentation") or "not checked"
            row["documentation_evidence"] = provider.get("documentation_address") or provider.get("note", "")
            row["terms"] = provider.get("terms") or "not checked"
            row["terms_evidence"] = provider.get("terms_address") or provider.get("note", "")

    # completeness: the examined resources that an API serves with all their records
    examined = {resource_id for resource_id, entry in facts.items() if entry["examined"]}
    served = set()
    for row in working:
        if row["kind"] == DATASTORE and row.get("comparison") in SERVED:
            served.add(row["resource_id"])
        elif row["kind"] == ARCGIS and row.get("comparison") in SERVED:
            served |= examined
        elif row["kind"] == WFS and row.get("comparison") in SERVED:
            endpoint, layer = row["address"].split("?typeNames=")
            for resource in dataset.get("resources") or []:
                if wfs_request(resource) == (endpoint, layer):
                    served.add(str(resource.get("id")))
    needs_all = organisation.get("combine") == "worst"
    if not working:
        complete = ""
    elif any(row.get("comparison") == "not comparable" for row in working) and not served:
        complete = "not comparable"
    elif examined and (examined <= served if needs_all else bool(examined & served)):
        complete = "yes"
    elif not examined and served:
        complete = "yes"
    else:
        complete = "no"

    def best(field: str) -> str:
        values = {row.get(field) or "no" for row in working}
        return "yes" if "yes" in values else "not checked" if "not checked" in values else "no"

    documentation = best("documentation") if working else ""
    terms = best("terms") if working else ""
    check.update(api_declared="yes" if endpoints else "no", api_kinds="; ".join(kinds),
                 api_works="yes" if working else "no", api_complete=complete, api_documentation=documentation,
                 api_terms=terms, bulk_download=bulk, bulk_evidence=bulk_evidence)

    parts = []
    if not endpoints:
        parts.append("no API")
    for row in endpoints:
        if row.get("works") == "yes":
            text = f"{row['kind']} answers anonymously"
            if isinstance(row.get("records_api"), int):
                text += f" with {with_noun(row['records_api'], 'record')}"
                if row["kind"] == ARCGIS and largest_member(row.get("notes", "")) is not None:
                    text += f", {largest_member(row['notes']):,} of them in its largest layer or table"
                if row["kind"] == ARCGIS and row.get("records_file") not in ("", None):
                    text += f" (examined files of the dataset: {number(row['records_file']):,})"
                elif row.get("records_file") not in ("", None):
                    text += f" (file: {number(row['records_file']):,}" + \
                            (f" in {row['tables_file']} tables" if number(row.get("tables_file")) > 1 else "") + ")"
        else:
            text = f"{row['kind']} declared but not usable: {row.get('answer') or 'no answer'}"
        if text not in parts:
            parts.append(text)
    if working:
        parts.append(f"serves the dataset completely: {complete}")
        parts.append(f"documentation of the API: {documentation}; terms of use of the API: {terms}")
    parts.append(f"bulk download: {bulk_evidence}" if bulk == "yes" else "no bulk download")

    if working and bulk == "yes" and documentation == "yes" and terms == "yes" and complete == "yes":
        score = "2"
    elif working or bulk == "yes":
        score = "1"
    else:
        score = "0"
    pending = [label for label, value in (("documentation", documentation), ("terms of use", terms))
               if value == "not checked"]
    if complete == "not comparable":
        pending.append("completeness of the API")
    if pending and score == "1" and working and bulk == "yes" and complete in ("yes", "not comparable"):
        check["notes"] = "to be settled by hand: " + ", ".join(pending)
    both = documentation == "yes" and terms == "yes"
    check.update(m10_score=score, m10_reason="; ".join(parts),
                 hvd_api="no" if not working else "partly" if complete == "no" else "yes", hvd_bulk_download=bulk,
                 hvd_api_terms_and_documentation="-" if not working else "yes" if both else
                 "not checked" if "not checked" in (documentation, terms) else "no")
    return check


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], endpoints: list[dict], date: str, titles: dict[str, str]) -> None:
    high_value = [row for row in checks if row["m10_score"] != "n/a"]
    scores = Counter(row["m10_score"] for row in high_value)
    lines = [
        f"# API and bulk download of the high-value datasets of the sample (M10), snapshot of {date}",
        "",
        "Produced by `scripts/07_api_checks.py`. Every API was called anonymously and asked only for its description "
        "and for the number of its records; this report contains no records of the data. The scores are proposals, "
        "reviewed and recorded in `DECISIONS.md`.",
        "",
        f"High-value datasets: {len(high_value)}. Proposed M10: " + ", ".join(
            f"{score}: {scores[score]}" for score in ("0", "1", "2") if scores[score]) + ".",
        "",
        "## Compliance columns (Regulation (EU) 2023/138, Article 3; DECISIONS.md #28)",
        "",
        "| Dataset | Category | API | Bulk download | Terms of use and documentation of the API | M10 |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in high_value:
        title = md_cell(titles.get(row["sample_id"], "")[:60])
        lines.append(f"| {row['sample_id']} {title} | {md_cell(row['category'])} | {row['hvd_api']} | "
                     f"{row['hvd_bulk_download']} | {row['hvd_api_terms_and_documentation']} | {row['m10_score']} |")
    lines += ["", "## Proposed scores", "", "| Dataset | M10 | Reason | Notes |", "| --- | ---: | --- | --- |"]
    for row in high_value:
        lines.append(f"| {row['sample_id']} | {row['m10_score']} | {md_cell(row['m10_reason'])} | "
                     f"{md_cell(row.get('notes', ''))} |")
    lines += ["", "## APIs tested", "",
              "| Dataset | Resource | Kind | Tested on | Works anonymously | Answer | Records through the API | "
              "Records of the file | Comparison | Documentation | Terms of use | Notes |",
              "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |"]
    for row in endpoints:
        documentation = " ".join(part for part in (row.get("documentation", ""),
                                                  f"({row['documentation_evidence']})"
                                                  if row.get("documentation_evidence") else "") if part)
        terms = " ".join(part for part in (row.get("terms", ""), f"({row['terms_evidence']})"
                                           if row.get("terms_evidence") else "") if part)
        lines.append(f"| {row['sample_id']} | {row.get('position', '')} | {row['kind']} | {row.get('tested_on', '')} | "
                     f"{row.get('works', '')} | {md_cell(row.get('answer', ''))} | {row.get('records_api', '')} | "
                     f"{row.get('records_file', '')} | {row.get('comparison', '')} | {md_cell(documentation)} | "
                     f"{md_cell(terms)} | {md_cell(row.get('notes', ''))} |")
    if not endpoints:
        lines.append("| - | - | - | - | - | no API declared | | | | | | |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Test of the APIs of the high-value datasets of the sample "
                                                 "(criterion M10).")
    parser.add_argument("--only", nargs="+", metavar="ID", help="sample ids to test, e.g. S10 (test run)")
    parser.add_argument("--report", action="store_true",
                        help="rebuild the scores and the report from the recorded answers, without calling any service")
    args = parser.parse_args()

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    log_file = PROCESSED_DIR / f"resource_downloads_{date}.csv"
    profiles_file = PROCESSED_DIR / f"file_profiles_{date}.csv"
    for needed, script in ((log_file, "05_resource_download.py"), (profiles_file, "06_file_checks.py")):
        if not needed.exists():
            raise SystemExit(f"{relative(needed)} not found. Run {script} first.")
    log = read_csv(log_file)
    profiles = read_csv(profiles_file)
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    providers = {row["provider"].strip().lower(): row for row in read_csv(PROVIDERS_FILE)} \
        if PROVIDERS_FILE.exists() else {}
    datasets = load_datasets(snapshot, sample)
    endpoints_file = PROCESSED_DIR / f"api_endpoints_{date}.csv"
    checks_file = PROCESSED_DIR / f"api_checks_{date}.csv"
    report_file = OUT_DIR / f"api_{date}" / "api_checks.md"
    today = dt.date.today().isoformat()

    high_value = sorted(key for key, row in sample.items() if row.get("group") != COMPARISON_GROUP)
    wanted = {item.upper() for item in args.only} if args.only else set(high_value)
    unknown = wanted - set(sample)
    if unknown:
        raise SystemExit(f"Not in the sample: {', '.join(sorted(unknown))}.")
    recorded = read_csv(endpoints_file) if endpoints_file.exists() else []
    for row in recorded:
        for key in ("records_api", "records_file", "tables_file"):
            row[key] = int(row[key]) if str(row.get(key, "")).isdigit() else row.get(key, "")

    print(f"Snapshot: {relative(snapshot)}")
    print(f"High-value datasets of the sample: {len(high_value)}")
    endpoints: list[dict] = []
    if args.report:
        print("Rebuilding the scores and the report from the recorded answers, without calling any service.")
        endpoints = recorded
    else:
        print(f"Certificates checked through the {CERTIFICATES}.")
        endpoints = [row for row in recorded if row["sample_id"] not in wanted]
        with requests.Session() as session:
            for sample_id in sorted(wanted & set(high_value)):
                dataset = datasets.get(sample_id) or {}
                positions = {row["resource_id"]: f"r{number(row['position']):03d}" for row in log
                             if row["sample_id"] == sample_id}
                facts = file_facts([row for row in profiles if row["sample_id"] == sample_id])
                print(f"{sample_id}:", flush=True)
                found = endpoints_of(session, sample_id, dataset, positions, today)
                settle_comparisons(found, facts)
                if not found:
                    print("    no API declared", flush=True)
                for row in found:
                    print(f"        {row['kind']}: {'works' if row['works'] == 'yes' else 'does not work'}: "
                          f"{row.get('answer', '')}"
                          + (f"; records {row['records_api']:,}" if isinstance(row.get("records_api"), int) else "")
                          + (f" (file {number(row['records_file']):,}, {row['comparison']})"
                             if row.get("comparison") and row.get("records_file") not in ("", None) else ""),
                          flush=True)
                endpoints += found
    endpoints.sort(key=lambda row: (row["sample_id"], row.get("position", ""), row["kind"]))

    checks = []
    for sample_id in sorted(sample):
        facts = file_facts([row for row in profiles if row["sample_id"] == sample_id])
        settle_comparisons([row for row in endpoints if row["sample_id"] == sample_id], facts)
        check = judge(sample_id, sample[sample_id], datasets.get(sample_id) or {},
                      [row for row in endpoints if row["sample_id"] == sample_id],
                      [row for row in log if row["sample_id"] == sample_id], organisation.get(sample_id, {}), facts,
                      providers)
        checks.append(check)
    write_csv(endpoints_file, ENDPOINT_FIELDS, endpoints)
    write_csv(checks_file, CHECK_FIELDS, checks)
    write_report(report_file, checks, endpoints, date, titles)

    for check in checks:
        if check["m10_score"] != "n/a":
            print(f"{check['sample_id']} M10 {check['m10_score']}: {check['m10_reason'][:150]}")
    scores = Counter(check["m10_score"] for check in checks)
    print("Proposed M10: " + ", ".join(f"{score}: {scores[score]}" for score in ("0", "1", "2", "n/a")
                                       if scores[score]))
    print("Files:")
    for path in (endpoints_file, checks_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
