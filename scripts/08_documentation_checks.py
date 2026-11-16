r"""
08_documentation_checks.py
Phase 3, step 3: evidence on the documentation of the structure of the datasets of the sample (criterion AI2: is the
meaning, the unit and the coding of every field documented).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one), the sample
     (data/processed/sample.csv), the file profiles of 06_file_checks.py and the organisation of the files
     (criteria/file_organisation.csv).
  2. Counts, in the whole catalogue, the datasets that fill a metadata field meant for documentation or for a
     standard (conforms_to, documentation, page) at each level of the metadata: in the dataset, in one of its
     resources, or among the additional metadata (extras), the free entries outside the fields of the schema of
     the portal, which come mostly from harvesting. Counts also the datasets whose additional metadata list the
     columns of the data (columns, datastore_fields).
  3. Collects, for every dataset of the sample, the places where its fields could be explained:
        the description of the dataset and of its resources (length, whether it only repeats the title, that is
        adds fewer than 25 letters to it, units and standards that it names)
        the fields for documentation or for a standard that the dataset fills, with the level of each
        documents published next to the data files, and pages of the publisher that the metadata link to (the
        addresses of the filled fields first)
        the names of the columns of the examined files (file profiles): how many carry a unit, which look like
        codes or identifiers, tables without a header
  4. Compares the columns of the GTFS feeds with the fields of the GTFS Schedule Reference.
  5. Asks the portal, anonymously, for the data dictionary of every DataStore table of the sample (datastore_search
     with limit=0, and datastore_info): how many fields the table has and how many of them carry a label or a
     description written by the publisher. No record is asked for, and the names of the fields are not written.
  6. Proposes a score only where a rule decides without judgement (no fields, no file to compare, a declared
     standard); every other dataset is marked "by hand" and is judged in the review of the criterion.
  7. Writes:
        data/processed/documentation_checks_YYYY-MM-DD.csv     one row per dataset of the sample: the evidence and
                                                                the proposal
        data/processed/datastore_dictionaries_YYYY-MM-DD.csv   one row per DataStore table: fields, labels and
                                                                descriptions
        outputs/documentation_YYYY-MM-DD/documentation_checks.md   the same as a report
     The date in the names is the date of the snapshot; the date of each call is recorded in the rows. None of the
     files contains records of the data.

Rules of AI2 (DECISIONS.md #46):
  - An explanation of the fields counts wherever it is written: in the description of the dataset or of a resource,
    in a document published with the data, on a page of the publisher that the metadata link to, in a public
    standard that the dataset declares, or in the file itself (a header that carries the unit, a column with the
    label next to the code). The files judged are those examined for AI1 (criteria/file_organisation.csv).
  - Score 2: the meaning of every column, the unit of every measure and every code or abbreviation are explained in
    writing. Score 1: the columns are understood but something is missing, or only some of them are explained.
    Score 0: neither an explanation nor names that can be understood.
  - A declared standard explains the columns that belong to it: 2 when every column of the files is a field of the
    standard, 1 when the files also hold columns outside it that nothing explains.
  - The type of a column (number, text, date) is not required to be stated separately.
  - Datasets without fields (map images, documents of running text) score n/a; a table inside a document is judged
    by a look at the document.
  - Datasets whose files could not be obtained are judged on their metadata alone and cannot exceed 1: 1 when the
    metadata declare a standard or describe the fields, otherwise 0.
  - For the high-value datasets of the categories whose section of the Annex of Regulation (EU) 2023/138 asks for a
    complete and public documentation (points 2.2(c), 3.2(c), 4.2(c), 5.2(b) and 6.2(c)), the score fills a column
    of the table of compliance: yes (2), partly (1), no (0). The section on geospatial data asks for none.

Certificates of the servers are checked through the trust store of the operating system when the package
truststore is installed (requirements.txt); otherwise through the certificates bundled with requests.

Usage (from the project root, with the .venv activated):
    python scripts\08_documentation_checks.py                  all the datasets of the sample
    python scripts\08_documentation_checks.py --only S07 S10   calls the portal for these datasets only (test run);
                                                               the recorded answers of the others are kept
    python scripts\08_documentation_checks.py --report         rebuilds the evidence and the report from the recorded
                                                               answers, without calling the portal

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
import unicodedata
from collections import Counter
from pathlib import Path

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
PORTAL = "https://data.gov.gr"

HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}
TIMEOUT_SECONDS = (30, 120)      # connection, and waiting time for the answer
TRIES_PER_CALL = 3               # tries against network errors and server errors
WAIT_BETWEEN_TRIES = (5, 15)     # seconds before the second and the third try
PAUSE_SECONDS = 0.5              # pause between two calls

COMPARISON_GROUP = "comparison"
BY_HAND = "by hand"
TITLE_MARGIN = 25                # letters that a description may add to the title and still only repeat it

# Metadata fields of DCAT-AP meant for the documentation of a dataset or of a distribution and for the standard
# that it follows, under the names of the catalogue API. A dataset can fill them at three levels: in the dataset,
# in a resource, or among the additional metadata (extras): free entries outside the fields of the schema of the
# portal, where a harvested dataset carries what its source catalogue declares (entries harvest_...).
DOCUMENTATION_FIELDS = ("conforms_to", "documentation", "page")
FIELD_LEVELS = ("dataset", "resource", "additional metadata")

# Entries of the additional metadata under which a publisher lists the columns of the data.
COLUMN_LIST_FIELDS = ("columns", "datastore_fields")
PUBLISHERS_SHOWN = 5             # names of publishers written in the report for each count of the catalogue

# Formats of resources that are documents, as opposed to data files, pages and services.
DOCUMENT_FORMATS = {"PDF", "DOC", "DOCX", "ODT", "RTF", "TXT"}

# Standards, data models and classifications whose public specification explains fields or codes: the label and
# the pattern that finds the name in the title, the descriptions and the tags.
STANDARDS = [
    ("GTFS", re.compile(r"\bGTFS\b|General Transit Feed Specification", re.IGNORECASE)),
    ("NeTEx", re.compile(r"\bNeTEx\b", re.IGNORECASE)),
    ("EDM", re.compile(r"\bEDM\b|Europeana Data Model")),
    ("STIRData", re.compile(r"\bSTIRData\b", re.IGNORECASE)),
    ("CORINE", re.compile(r"\bCORINE\b", re.IGNORECASE)),
    ("INSPIRE", re.compile(r"\bINSPIRE\b")),
    ("SDMX", re.compile(r"\bSDMX\b")),
    ("COICOP", re.compile(r"\bCOICOP\b")),
    ("NACE", re.compile(r"\bNACE\b")),
    ("NUTS", re.compile(r"\bNUTS\b")),
]

# A unit of measurement alone in parentheses or brackets, e.g. (Kg), (€/Kg), (°C), (hPa): in a description, or in
# the name of a column, where a symbol (€, %, °C) or a suffix (area_ha) also counts.
UNIT = r"(?:kg|κιλά|€|ευρώ|%|°c|mm|cm|km/h|km|m/s|hpa|mbar|ha|στρ\.?|στρέμματα|τόνοι|tn|kwh|mwh|mw|kw|m2|m²|m3|m³|m|lt)"
UNIT_IN_TEXT = re.compile(rf"[(\[]\s*{UNIT}(?:\s*/\s*{UNIT})?\s*[)\]]", re.IGNORECASE)
UNIT_IN_NAME = re.compile(rf"{UNIT_IN_TEXT.pattern}|[€%]|°C|_(?:ha|km|kg|mm|m2|pct)$", re.IGNORECASE)
CODE_WORDS = {"id", "code", "fid", "cid", "objectid"}

# Fields of the files of a GTFS feed: GTFS Schedule Reference (gtfs.org/documentation/schedule/reference), revision
# of 27 April 2026, read on 10 November 2026.
GTFS_FIELDS = {
    "agency.txt": "agency_id agency_name agency_url agency_timezone agency_lang agency_phone agency_fare_url "
                  "agency_email cemv_support",
    "stops.txt": "stop_id stop_code stop_name tts_stop_name stop_desc stop_lat stop_lon zone_id stop_url "
                 "location_type parent_station stop_timezone wheelchair_boarding level_id platform_code stop_access",
    "routes.txt": "route_id agency_id route_short_name route_long_name route_desc route_type route_url route_color "
                  "route_text_color route_sort_order continuous_pickup continuous_drop_off network_id cemv_support",
    "trips.txt": "route_id service_id trip_id trip_headsign trip_short_name direction_id block_id shape_id "
                 "wheelchair_accessible bikes_allowed cars_allowed safe_duration_factor safe_duration_offset",
    "stop_times.txt": "trip_id arrival_time departure_time stop_id location_group_id location_id stop_sequence "
                      "stop_headsign start_pickup_drop_off_window end_pickup_drop_off_window pickup_type "
                      "drop_off_type continuous_pickup continuous_drop_off shape_dist_traveled timepoint "
                      "pickup_booking_rule_id drop_off_booking_rule_id",
    "calendar.txt": "service_id monday tuesday wednesday thursday friday saturday sunday start_date end_date",
    "calendar_dates.txt": "service_id date exception_type",
    "fare_attributes.txt": "fare_id price currency_type payment_method transfers agency_id transfer_duration",
    "fare_rules.txt": "fare_id route_id origin_id destination_id contains_id",
    "shapes.txt": "shape_id shape_pt_lat shape_pt_lon shape_pt_sequence shape_dist_traveled",
    "frequencies.txt": "trip_id start_time end_time headway_secs exact_times",
    "transfers.txt": "from_stop_id to_stop_id from_route_id to_route_id from_trip_id to_trip_id transfer_type "
                     "min_transfer_time",
    "pathways.txt": "pathway_id from_stop_id to_stop_id pathway_mode is_bidirectional length traversal_time "
                    "stair_count max_slope min_width signposted_as reversed_signposted_as",
    "levels.txt": "level_id level_index level_name",
    "translations.txt": "table_name field_name language translation record_id record_sub_id field_value",
    "feed_info.txt": "feed_publisher_name feed_publisher_url feed_lang default_lang feed_start_date feed_end_date "
                     "feed_version feed_contact_email feed_contact_url",
    "attributions.txt": "attribution_id agency_id route_id trip_id organization_name is_producer is_operator "
                        "is_authority attribution_url attribution_email attribution_phone",
}
GTFS_FIELDS = {name: set(fields.split()) for name, fields in GTFS_FIELDS.items()}

# Categories of high-value datasets whose section of the Annex asks for a complete and public documentation.
DOCUMENTATION_REQUIRED = {"Statistics", "Mobility", "Earth observation and environment", "Meteorological",
                          "Companies and company ownership"}

CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "fields_kind", "description_characters",
    "description_repeats_title", "resource_descriptions", "units_in_descriptions", "standards_named",
    "documentation_fields", "documents_next_to_data", "publisher_pages", "tables_examined", "column_sets",
    "columns", "columns_with_unit",
    "code_columns", "tables_without_header", "column_names_written", "gtfs_tables", "gtfs_columns",
    "gtfs_columns_outside_reference", "datastore_tables", "datastore_fields", "datastore_fields_described",
    "datastore_dictionary", "ai2_proposal", "ai2_reason", "hvd_documentation_required",
]
DICTIONARY_FIELDS = [
    "sample_id", "dataset", "position", "resource_id", "address", "tested_on", "http_status", "answer", "fields",
    "fields_with_label", "fields_with_description", "fields_described", "types", "notes",
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
    """The automatic "download all" ZIP bundle that the portal adds to every dataset (DECISIONS.md #13)."""
    return bool(resource.get("downloadall_datapackage_hash"))


def plain_text(value) -> str:
    """A text without HTML tags, character entities and repeated spaces."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))).strip()


def letters_only(value) -> str:
    """A text reduced to its letters and digits, without accents and in lower case, for comparisons."""
    text = unicodedata.normalize("NFD", plain_text(value).lower())
    text = "".join(character for character in text if unicodedata.category(character) != "Mn")
    return re.sub(r"[\W_]+", " ", text).strip()


def number(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def with_noun(count: int, noun: str) -> str:
    """A number with its noun, in the singular or in the plural."""
    return f"{count:,} {noun}{'' if count == 1 else 's'}"


def own_resources(dataset: dict) -> list[dict]:
    """The resources of a dataset, without the automatic bundle of the portal."""
    return [resource for resource in dataset.get("resources") or []
            if isinstance(resource, dict) and not is_bundle(resource)]


def has_content(value) -> bool:
    """Whether a metadata value holds anything: a list or a structure whose elements are all blank holds nothing."""
    if isinstance(value, dict):
        return any(has_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_content(item) for item in value)
    return value is not None and str(value).strip() != ""


def additional_metadata(dataset: dict) -> dict:
    """The filled entries of the additional metadata of a dataset (extras), by key. Lists and structures are
    stored there as JSON text and are read back."""
    entries = {}
    for item in dataset.get("extras") or []:
        if not isinstance(item, dict) or not item.get("key"):
            continue
        value = item.get("value")
        if isinstance(value, str) and value.strip().startswith(("[", "{")):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        if has_content(value):
            entries[str(item["key"])] = value
    return entries


def documentation_fields(dataset: dict, extras: dict) -> dict[str, dict[str, list]]:
    """The fields meant for documentation or for a standard that a dataset fills, by level of the metadata, each
    with the values that it holds."""
    resources = [item for item in dataset.get("resources") or [] if isinstance(item, dict)]
    levels: dict[str, dict[str, list]] = {level: {} for level in FIELD_LEVELS}
    for name in DOCUMENTATION_FIELDS:
        if has_content(dataset.get(name)):
            levels["dataset"][name] = [dataset[name]]
        values = [resource[name] for resource in resources if has_content(resource.get(name))]
        if values:
            levels["resource"][name] = values
        if name in extras:
            levels["additional metadata"][name] = [extras[name]]
    return levels


def addresses_in(value) -> list[str]:
    """The web addresses that a metadata value holds, whether it is a text, a list or a structure."""
    if isinstance(value, dict):
        return [address for item in value.values() for address in addresses_in(item)]
    if isinstance(value, (list, tuple)):
        return [address for item in value for address in addresses_in(item)]
    return re.findall(r"https?://[^\s\"'<>]+", str(value or ""))


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def read_catalogue(snapshot: Path, sample: dict[str, dict]) -> tuple[dict[str, dict], dict]:
    """The records of the datasets of the sample, by sample id, and the counts of the whole catalogue: the
    datasets that fill a field meant for documentation or for a standard, at each level of the metadata, and the
    datasets whose additional metadata list the columns of the data, with the publishers of both."""
    by_id = {row["id"]: row["sample_id"] for row in sample.values()}
    found: dict[str, dict] = {}
    counts = {"datasets": 0, "resources": 0, "datasets_with_extras": 0, "harvested": 0, "datasets_with_field": 0,
              "datasets_at_level": Counter(), "fields": {level: Counter() for level in FIELD_LEVELS},
              "publishers": {level: Counter() for level in FIELD_LEVELS},
              "datasets_with_column_list": 0, "column_list_publishers": Counter()}
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("id") in by_id:
                found[by_id[record["id"]]] = record
            if record.get("type") != "dataset":
                continue
            counts["datasets"] += 1
            counts["resources"] += sum(1 for item in record.get("resources") or [] if isinstance(item, dict))
            organisation = record.get("organization") if isinstance(record.get("organization"), dict) else {}
            publisher = str(organisation.get("name") or "not stated")
            extras = additional_metadata(record)
            counts["datasets_with_extras"] += bool(extras)
            counts["harvested"] += any(key.startswith("harvest_") for key in extras)
            levels = documentation_fields(record, extras)
            for level, filled in levels.items():
                if filled:
                    counts["datasets_at_level"][level] += 1
                    counts["fields"][level].update(list(filled))
                    counts["publishers"][level][publisher] += 1
            counts["datasets_with_field"] += any(levels.values())
            if any(name in extras for name in COLUMN_LIST_FIELDS):
                counts["datasets_with_column_list"] += 1
                counts["column_list_publishers"][publisher] += 1
    return found, counts


def publishers_text(publishers: Counter) -> str:
    """The publishers behind a count of the catalogue: how many they are and the names of the largest."""
    if not publishers:
        return ""
    names = [name for name, _ in sorted(publishers.items(), key=lambda item: (-item[1], item[0]))]
    shown = ", ".join(names[:PUBLISHERS_SHOWN])
    more = f", and {len(names) - PUBLISHERS_SHOWN} more" if len(names) > PUBLISHERS_SHOWN else ""
    return f"{with_noun(len(names), 'publisher')}: {shown}{more}"


# ---------------------------------------------------------------------------
# Evidence of the metadata
# ---------------------------------------------------------------------------

def metadata_evidence(dataset: dict, positions: dict[str, str], has_tables: bool) -> dict:
    """Where the metadata of a dataset could explain its fields: descriptions, documents, pages."""
    title = plain_text(dataset.get("title"))
    notes = plain_text(dataset.get("notes"))
    resources = own_resources(dataset)
    short_title, short_notes = letters_only(title), letters_only(notes)
    repeats = (not short_notes or short_notes == short_title or short_notes in short_title
               or (short_title in short_notes and len(short_notes) - len(short_title) < TITLE_MARGIN))
    descriptions = []
    for resource in resources:
        text = plain_text(resource.get("description"))
        if text and letters_only(text) not in (letters_only(resource.get("name")), short_title) \
                and text not in descriptions:
            descriptions.append(text)
    texts = [title, notes] + [plain_text(resource.get("name")) for resource in resources] + descriptions
    texts += [str(tag.get("name") or "") for tag in dataset.get("tags") or [] if isinstance(tag, dict)]
    everything = " | ".join(texts)
    units = []
    for match in UNIT_IN_TEXT.finditer(" | ".join([notes] + descriptions)):
        unit = re.sub(r"\s+", "", match.group(0))
        if unit not in units:
            units.append(unit)
    standards = [label for label, pattern in STANDARDS if pattern.search(everything)]
    documents = [f"{positions.get(str(resource.get('id') or ''), '')} "
                 f"{str(resource.get('format') or '').strip().upper()}".strip()
                 for resource in resources
                 if str(resource.get("format") or "").strip().upper() in DOCUMENT_FORMATS] if has_tables else []
    filled = documentation_fields(dataset, additional_metadata(dataset))
    documented = [address for level in FIELD_LEVELS for values in filled[level].values()
                  for address in addresses_in(values)]
    pages = []
    written = re.findall(r'href="([^"]+)"', str(dataset.get("notes") or "")) \
        + re.findall(r"https?://[^\s\"'<>]+", notes)
    declared = dataset.get("landing_page") or []
    declared = declared if isinstance(declared, list) else [declared]
    for address in [*documented, *declared, dataset.get("url"), *written]:
        address = html.unescape(str(address or "")).strip().rstrip(".,;)")
        if address.startswith("http") and address not in pages:
            pages.append(address)
    return {
        "description_characters": len(notes),
        "description_repeats_title": "yes" if repeats else "no",
        "resource_descriptions": len(descriptions),
        "units_in_descriptions": " ".join(units),
        "standards_named": ", ".join(standards),
        "documentation_fields": ", ".join(f"{name} ({level})" for level in FIELD_LEVELS for name in filled[level]),
        "documents_next_to_data": ", ".join(documents),
        "publisher_pages": " ; ".join(pages[:6]) + (f" ; and {len(pages) - 6} more" if len(pages) > 6 else ""),
    }


# ---------------------------------------------------------------------------
# Evidence of the files
# ---------------------------------------------------------------------------

def looks_like_code(name: str) -> bool:
    """A column name that announces a code or an identifier."""
    for word in re.split(r"[\s_./()\-]+", name.lower()):
        if word in CODE_WORDS or word.endswith("code") or word.startswith(("κωδ", "kwd")):
            return True
    return False


def column_evidence(profiles: list[dict]) -> dict:
    """What the names of the columns of the examined tables of a dataset show."""
    tables = [row for row in profiles if row.get("data_file") == "True" and row.get("examined") == "True"]
    names: list[str] = []
    withheld = without_header = 0
    for row in tables:
        text = row.get("column_names", "")
        if text.startswith("(no header recognised"):
            without_header += 1
        elif not text.strip() and number(row.get("columns")):
            withheld += 1
        else:
            names += [name.strip() for name in text.split(" | ") if name.strip() and name.strip() not in names]
    codes = [name for name in names if looks_like_code(name)]
    gtfs = [row for row in tables if row.get("kind") == "gtfs"]
    outside, unknown_files, gtfs_columns = [], [], 0
    for row in gtfs:
        file_name = row.get("member", "").rsplit("/", 1)[-1]
        columns = [name.strip() for name in row.get("column_names", "").split(" | ") if name.strip()]
        gtfs_columns += len(columns)
        if file_name not in GTFS_FIELDS:
            unknown_files.append(file_name)
            continue
        extra = [name for name in columns if name not in GTFS_FIELDS[file_name]]
        if extra:
            outside.append(f"{file_name}: {', '.join(extra)}")
    if unknown_files:
        outside.append("files that the list of the script does not hold: " + ", ".join(sorted(set(unknown_files))))
    return {
        "tables_examined": len(tables),
        "column_sets": len({row.get("column_names", "") for row in tables}),
        "columns": len(names) if not withheld else "",
        "columns_with_unit": sum(1 for name in names if UNIT_IN_NAME.search(name)) if not withheld else "",
        "code_columns": ", ".join(codes[:12]) + (f", and {len(codes) - 12} more" if len(codes) > 12 else ""),
        "tables_without_header": without_header,
        "column_names_written": "no: withheld in the file profiles (DECISIONS.md #29)" if withheld else
                                ("yes" if tables else ""),
        "gtfs_tables": len(gtfs) if gtfs else "",
        "gtfs_columns": gtfs_columns if gtfs else "",
        "gtfs_columns_outside_reference": ("; ".join(outside) if outside else "none") if gtfs else "",
        "all_gtfs": bool(gtfs) and len(gtfs) == len(tables),
    }


# ---------------------------------------------------------------------------
# Data dictionary of the DataStore
# ---------------------------------------------------------------------------

def call(session: requests.Session, url: str) -> dict:
    """One anonymous call: the HTTP status, the parsed JSON answer and the error, if any."""
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
                body = answer.json()
            except ValueError:
                error = "the answer is not JSON"
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


def fields_of(facts: dict) -> list[dict] | None:
    """The fields of a table in the answer of the DataStore, without the row number that the portal adds."""
    body = facts["body"] if isinstance(facts["body"], dict) else {}
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    if facts["status"] != 200 or body.get("success") is not True or not isinstance(result.get("fields"), list):
        return None
    return [field for field in result["fields"] if isinstance(field, dict) and field.get("id") != "_id"]


def read_dictionary(session: requests.Session, resource_id: str) -> dict:
    """The data dictionary of a DataStore table: how many fields carry a label or a description of the publisher.
    The table is asked for its fields in the two ways that the DataStore offers; no record is asked for."""
    address = f"{PORTAL}/api/3/action/datastore_search?resource_id={resource_id}&limit=0"
    facts = call(session, address)
    row = {"address": address, "http_status": facts["status"], "fields": "", "fields_with_label": "",
           "fields_with_description": "", "fields_described": "", "types": "", "notes": ""}
    fields = fields_of(facts)
    if fields is None:
        body = facts["body"] if isinstance(facts["body"], dict) else {}
        error = body.get("error") if isinstance(body.get("error"), dict) else {}
        row["answer"] = "; ".join(part for part in (
            f"HTTP {facts['status']}" if facts["status"] else "", str(error.get("message") or "")[:120],
            facts["error"], "the table gave no fields") if part)
        return row
    second_facts = call(session, f"{PORTAL}/api/3/action/datastore_info?id={resource_id}")
    second = fields_of(second_facts)
    second_body = second_facts["body"] if isinstance(second_facts["body"], dict) else {}
    if second is not None:
        second_note = "the same fields" if len(second) == len(fields) else with_noun(len(second), "field")
    elif second_facts["status"] == 200 and second_body.get("success") is True:
        second_note = "an answer without a list of fields"
    else:
        second_note = "; ".join(part for part in (f"HTTP {second_facts['status']}" if second_facts["status"] else "",
                                                 second_facts["error"]) if part) or "no answer"
    described_second = {str(field.get("id")): field.get("info") for field in second or []
                        if isinstance(field.get("info"), dict)}
    labels = descriptions = described = 0
    for field in fields:
        info = field.get("info") if isinstance(field.get("info"), dict) else {}
        info = info or described_second.get(str(field.get("id"))) or {}
        label, notes = str(info.get("label") or "").strip(), str(info.get("notes") or "").strip()
        labels += bool(label)
        descriptions += bool(notes)
        described += bool(label or notes)
    types = Counter(str(field.get("type") or "") for field in fields)
    row.update(answer=f"table with {with_noun(len(fields), 'field')}", fields=len(fields), fields_with_label=labels,
               fields_with_description=descriptions, fields_described=described,
               types=", ".join(f"{name}: {count}" for name, count in sorted(types.items())),
               notes=f"second reading (datastore_info): {second_note}")
    return row


def dictionary_evidence(rows: list[dict]) -> dict:
    """The data dictionaries of the DataStore tables of a dataset, in one line."""
    answered = [row for row in rows if str(row.get("fields", "")).strip() != ""]
    fields = sum(number(row["fields"]) for row in answered)
    described = sum(number(row["fields_described"]) for row in answered)
    if not rows:
        state = ""
    elif len(answered) < len(rows):
        state = "not read"
    else:
        state = "no" if not described else ("yes" if described == fields else "partly")
    return {"datastore_tables": len(rows) if rows else "", "datastore_fields": fields if answered else "",
            "datastore_fields_described": described if answered else "", "datastore_dictionary": state}


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------

def propose(organisation: dict, evidence: dict) -> tuple[str, str]:
    """The proposed score of AI2 where a rule decides without judgement, otherwise the mark of the review."""
    missing = organisation.get("no_data_file", "").strip()
    standards = evidence["standards_named"]
    if missing == "map images":
        return "n/a", "no fields: the dataset is a map image"
    if missing == "documents":
        return BY_HAND, ("documents: n/a when they are running text without fields; a table inside a document is "
                         "judged by a look at the document")
    if missing == "unavailable":
        if standards:
            return "1", f"no file to compare with; the metadata name a standard ({standards}): at most 1"
        return "0", ("no file to compare with, and the metadata name no standard; 1 if the description is found to "
                     "describe the fields")
    if evidence["all_gtfs"] and "GTFS" in standards:
        outside = evidence["gtfs_columns_outside_reference"]
        if outside == "none":
            return "2", (f"declared standard GTFS: all the {evidence['gtfs_columns']} columns of the "
                         f"{with_noun(evidence['gtfs_tables'], 'file')} of the feed are fields of the reference")
        return "1", f"declared standard GTFS, with columns outside the reference that nothing explains: {outside}"
    return BY_HAND, "judged in the review: the descriptions, the documents and the pages against the columns"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], dictionaries: list[dict], counts: dict, date: str,
                 titles: dict[str, str]) -> None:
    proposals = Counter(row["ai2_proposal"] for row in checks)
    lines = [
        f"# Documentation of the structure of the datasets of the sample (AI2), snapshot of {date}",
        "",
        "Produced by `scripts/08_documentation_checks.py`. The table collects the evidence for the review of the "
        "criterion; a score is proposed only where a rule decides without judgement, and the final scores are "
        "recorded in `DECISIONS.md`. The portal was asked only for the fields of its DataStore tables; this report "
        "contains no records of the data.",
        "",
        "## Whole catalogue",
        "",
        f"Datasets: {counts['datasets']:,}, with {counts['resources']:,} resources. Datasets that fill a metadata "
        f"field meant for documentation or for a standard ({', '.join(DOCUMENTATION_FIELDS)}): "
        f"{counts['datasets_with_field']:,}. The additional metadata (extras) are free entries outside the fields "
        f"of the schema of the portal: {counts['datasets_with_extras']:,} datasets carry them, "
        f"{counts['harvested']:,} of them harvested from another catalogue.",
        "",
        "| Level of the metadata | Datasets | " + " | ".join(DOCUMENTATION_FIELDS) + " | Publishers |",
        "| --- | ---: | " + "---: | " * len(DOCUMENTATION_FIELDS) + "--- |",
    ]
    for level in FIELD_LEVELS:
        fields = " | ".join(f"{counts['fields'][level][name]:,}" for name in DOCUMENTATION_FIELDS)
        lines.append(f"| {level} | {counts['datasets_at_level'][level]:,} | {fields} | "
                     f"{md_cell(publishers_text(counts['publishers'][level]))} |")
    lines += [
        "",
        f"Datasets whose additional metadata list the columns of the data ({', '.join(COLUMN_LIST_FIELDS)}): "
        f"{counts['datasets_with_column_list']:,}"
        + (f" ({publishers_text(counts['column_list_publishers'])})." if counts["datasets_with_column_list"]
           else "."),
        "",
        "## Proposals",
        "",
        "Proposed AI2: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", "n/a", BY_HAND)
                                    if proposals[score]) + ".",
        "",
        "| Dataset | Fields | Proposal | Reason | Documentation asked by the Annex |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in checks:
        title = md_cell(titles.get(row["sample_id"], "")[:60])
        lines.append(f"| {row['sample_id']} {title} | {row['fields_kind']} | {row['ai2_proposal']} | "
                     f"{md_cell(row['ai2_reason'])} | {row['hvd_documentation_required']} |")
    lines += ["", "## Evidence of the metadata", "",
              "| Dataset | Description (characters) | Repeats the title | Resource descriptions | Units named | "
              "Standards named | Documentation fields filled | Documents next to the data | Pages of the "
              "publisher |",
              "| --- | ---: | --- | ---: | --- | --- | --- | --- | --- |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} | {row['description_characters']} | {row['description_repeats_title']} | "
                     f"{row['resource_descriptions']} | {md_cell(row['units_in_descriptions'])} | "
                     f"{md_cell(row['standards_named'])} | {md_cell(row['documentation_fields'])} | "
                     f"{md_cell(row['documents_next_to_data'])} | {md_cell(row['publisher_pages'])} |")
    lines += ["", "## Evidence of the files", "",
              "| Dataset | Tables examined | Different sets of columns | Columns | With a unit in the name | "
              "Columns that look like codes | Tables without a header | Names written | GTFS columns outside the "
              "reference | Data dictionary of the DataStore |",
              "| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- |"]
    for row in checks:
        dictionary = ""
        if row["datastore_tables"] != "":
            dictionary = (f"{row['datastore_dictionary']} ({row['datastore_fields_described']} of "
                          f"{row['datastore_fields']} fields described, {with_noun(row['datastore_tables'], 'table')})"
                          if row["datastore_dictionary"] != "not read" else "not read")
        lines.append(f"| {row['sample_id']} | {row['tables_examined']} | {row['column_sets']} | {row['columns']} | "
                     f"{row['columns_with_unit']} | {md_cell(row['code_columns'])} | {row['tables_without_header']} | "
                     f"{md_cell(row['column_names_written'])} | {md_cell(row['gtfs_columns_outside_reference'])} | "
                     f"{dictionary} |")
    lines += ["", "## Data dictionaries of the DataStore tables", "",
              "| Dataset | Resource | Read on | Answer | Fields | With a label | With a description | Types | Notes |",
              "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |"]
    for row in dictionaries:
        lines.append(f"| {row['sample_id']} | {row.get('position', '')} | {row.get('tested_on', '')} | "
                     f"{md_cell(row.get('answer', ''))} | {row.get('fields', '')} | "
                     f"{row.get('fields_with_label', '')} | {row.get('fields_with_description', '')} | "
                     f"{md_cell(row.get('types', ''))} | {md_cell(row.get('notes', ''))} |")
    if not dictionaries:
        lines.append("| - | - | - | no DataStore table read | | | | | |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Evidence on the documentation of the structure of the datasets "
                                                 "of the sample (criterion AI2).")
    parser.add_argument("--only", nargs="+", metavar="ID",
                        help="sample ids whose DataStore tables are read, e.g. S07 (test run)")
    parser.add_argument("--report", action="store_true",
                        help="rebuild the evidence and the report from the recorded answers, without any call")
    args = parser.parse_args()

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    profiles_file = PROCESSED_DIR / f"file_profiles_{date}.csv"
    log_file = PROCESSED_DIR / f"resource_downloads_{date}.csv"
    for needed, script in ((log_file, "05_resource_download.py"), (profiles_file, "06_file_checks.py")):
        if not needed.exists():
            raise SystemExit(f"{relative(needed)} not found. Run {script} first.")
    profiles = read_csv(profiles_file)
    log = read_csv(log_file)
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    checks_file = PROCESSED_DIR / f"documentation_checks_{date}.csv"
    dictionaries_file = PROCESSED_DIR / f"datastore_dictionaries_{date}.csv"
    report_file = OUT_DIR / f"documentation_{date}" / "documentation_checks.md"
    today = dt.date.today().isoformat()

    wanted = {item.upper() for item in args.only} if args.only else set(sample)
    unknown = wanted - set(sample)
    if unknown:
        raise SystemExit(f"Not in the sample: {', '.join(sorted(unknown))}.")

    print(f"Snapshot: {relative(snapshot)}")
    datasets, counts = read_catalogue(snapshot, sample)
    levels = ", ".join(f"{level}: {counts['datasets_at_level'][level]:,}" for level in FIELD_LEVELS)
    print(f"Datasets of the catalogue: {counts['datasets']:,}; with a metadata field for documentation or for a "
          f"standard filled: {counts['datasets_with_field']:,} ({levels})")
    print(f"Datasets whose additional metadata list the columns of the data: "
          f"{counts['datasets_with_column_list']:,}")
    print(f"Datasets of the sample: {len(sample)}")

    recorded = read_csv(dictionaries_file) if dictionaries_file.exists() else []
    if args.report:
        print("Rebuilding the evidence and the report from the recorded answers, without calling the portal.")
        dictionaries = recorded
    else:
        print(f"Certificates checked through the {CERTIFICATES}.")
        dictionaries = [row for row in recorded if row["sample_id"] not in wanted]
        with requests.Session() as session:
            for sample_id in sorted(wanted):
                dataset = datasets.get(sample_id) or {}
                positions = {row["resource_id"]: f"r{number(row['position']):03d}" for row in log
                             if row["sample_id"] == sample_id}
                for resource in own_resources(dataset):
                    if not resource.get("datastore_active"):
                        continue
                    resource_id = str(resource.get("id") or "")
                    row = read_dictionary(session, resource_id)
                    row.update(sample_id=sample_id, dataset=dataset.get("name", ""),
                               position=positions.get(resource_id, ""), resource_id=resource_id, tested_on=today)
                    print(f"    {sample_id} {row['position'] or resource_id}: {row['answer']}"
                          + (f", {row['fields_described']} described" if row["fields"] != "" else ""), flush=True)
                    dictionaries.append(row)
    dictionaries.sort(key=lambda row: (row["sample_id"], row.get("position", "")))

    checks = []
    for sample_id in sorted(sample):
        dataset = datasets.get(sample_id) or {}
        entry = organisation.get(sample_id, {})
        columns = column_evidence([row for row in profiles if row["sample_id"] == sample_id])
        positions = {row["resource_id"]: f"r{number(row['position']):03d}" for row in log
                     if row["sample_id"] == sample_id}
        missing = entry.get("no_data_file", "").strip()
        kind = {"map images": "no fields: map images", "documents": "documents",
                "unavailable": "no file to compare with"}.get(missing, "tables" if columns["tables_examined"]
                                                               else "no table examined")
        evidence = {**metadata_evidence(dataset, positions, bool(columns["tables_examined"])), **columns,
                    **dictionary_evidence([row for row in dictionaries if row["sample_id"] == sample_id])}
        proposal, reason = propose(entry, evidence)
        category = sample[sample_id].get("category", "")
        group = sample[sample_id].get("group", "")
        required = "-" if group == COMPARISON_GROUP else (
            "yes" if category in DOCUMENTATION_REQUIRED else "not asked by the Annex")
        checks.append({"sample_id": sample_id, "dataset": dataset.get("name", sample[sample_id].get("name", "")),
                       "group": group, "category": category, "fields_kind": kind, **evidence,
                       "ai2_proposal": proposal, "ai2_reason": reason, "hvd_documentation_required": required})
    write_csv(checks_file, CHECK_FIELDS, checks)
    write_csv(dictionaries_file, DICTIONARY_FIELDS, dictionaries)
    write_report(report_file, checks, dictionaries, counts, date, titles)

    for check in checks:
        print(f"{check['sample_id']} AI2 {check['ai2_proposal']}: {check['ai2_reason'][:140]}")
    proposals = Counter(check["ai2_proposal"] for check in checks)
    print("Proposed AI2: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", "n/a", BY_HAND)
                                       if proposals[score]))
    described = sum(number(row.get("fields_described")) for row in dictionaries)
    total = sum(number(row.get("fields")) for row in dictionaries)
    print(f"DataStore tables read: {len(dictionaries)}; fields with a label or a description: {described:,} of "
          f"{total:,}")
    print("Files:")
    for path in (checks_file, dictionaries_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
