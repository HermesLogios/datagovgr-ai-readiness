r"""
10_croissant_checks.py
Phase 3, step 3: a Croissant description of every dataset of the sample, written only from what the portal and the
files already give, and its validation (criterion AI4: can the dataset be described in Croissant, or with a
datasheet, from the information available).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one), the sample
     (data/processed/sample.csv), the organisation of the files (criteria/file_organisation.csv), the tables of
     05_resource_download.py, 06_file_checks.py and 08_documentation_checks.py (download log, file profiles, kinds
     of the values of the columns, evidence on the documentation) and the descriptions of the columns taken from
     the documentation of the publishers (criteria/field_descriptions.csv).
  2. Counts, in the whole catalogue, the datasets whose metadata can fill each property of a Croissant
     description: the properties that the specification requires at the level of the dataset, the checksum and the
     media type of the files, and the tables of the DataStore, whose columns the portal already knows.
  3. Writes a Croissant description (JSON-LD, Croissant 1.1) for every dataset of the sample. The properties of
     the dataset follow the mapping of the Croissant profile of ckanext-dcat, the extension of the software of the
     portal (title, description, address of the page, creator, date of the record, tags, version), except for the
     licence, which is read from the resources (DECISIONS.md #31). The creator is every organisation named in the
     creator field of the dataset; where the field names none, it is the organisation that publishes the dataset.
     Of a creator only the name is written, never an e-mail address, and the publisher field is not written. The
     files are the resources that were obtained, with the name of the resource (the file name of its address where
     the resource has no name), the address used, the media type of the file found, its size and its SHA-256 from
     the download log.
     The fields are the columns of the examined tables (criteria/file_organisation.csv), with the type found by
     06_file_checks.py and, where the documentation gives it, the meaning of the column. The type of a field is
     the kind of most of the values of its column; values of another kind in the same column are a finding of Q3
     and do not change it. The source of a field names its file; the column is given as the way to read the
     values only for delimited text (CSV files and the files of a GTFS feed), the tabular format for which the
     specification defines the reading of a column by its name.
  4. Validates every description with the mlcroissant library, from the JSON that was written.
  5. Asks the portal, with one anonymous call to its API (status_show), whether the Croissant plugin of its
     software is enabled. Only when it is, reads the description that the portal serves for every dataset of the
     sample (/dataset/NAME/croissant.jsonld) and validates it in the same way.
  6. Proposes a score only where a rule decides without judgement (a description that is valid at the level of the
     dataset, with or without the meaning of every field); every other dataset is marked "by hand" and is judged in
     the review of the criterion, with the evidence collected here and by 08_documentation_checks.py.
  7. Writes:
        data/processed/croissant_checks_YYYY-MM-DD.csv      one row per dataset of the sample: the evidence and the
                                                            proposal
        data/processed/croissant_catalogue_YYYY-MM-DD.csv   one row per property: the datasets or resources of the
                                                            catalogue that can fill it
        data/processed/croissant_portal_YYYY-MM-DD.csv      the answers of the portal
        outputs/croissant_YYYY-MM-DD/Sxx.json               the description of each dataset of the sample
        outputs/croissant_YYYY-MM-DD/croissant_checks.md    the same evidence as a report
     The date in the names is the date of the snapshot; the date of each call is recorded in the rows. None of the
     files contains records of the data, and the names of the columns that the file profiles withhold
     (DECISIONS.md #29) are not written.

Rules of AI4 (DECISIONS.md #48):
  - Nothing is added to what exists: the licence is the one read for M4, the files are those obtained for Q1, the
    columns and their types are those found by 06_file_checks.py, the meaning of the columns is the one judged for
    AI2.
  - A description is valid at the level of the dataset when it holds every property that the specification
    requires (name, description, licence, address, creator, date of publication), at least one data file that was
    obtained, and the validator reports no error. On these properties the validator is more lenient than the
    specification (a missing licence gives a warning, a missing description nothing), so the specification
    decides.
  - The fields are the columns of the files examined for AI1 and AI2. A field carries a meaning where the
    documentation of the publisher explains the column (criteria/field_descriptions.csv, written for the datasets
    whose documentation explains every column), or where the dataset declares the GTFS standard and the column is
    a field of its reference.
  - Datasets with records: 2 for a valid description with the meaning of every field, 1 for a valid description
    whose fields are missing or lack their meaning.
  - Data without records (map images, documents) are judged with a datasheet: 2 when the documentation says what
    the data contain, how they were collected and for which uses they are suitable.
  - Where neither a valid description nor a complete datasheet can be written: 1 when the documentation says more
    than the title about what the data contain or how they were collected, 0 when it only repeats the title.
  - Datasets of which no file was obtained score 1 at most. So do the datasets whose examined files were exported
    by hand from an application: the files are not resources of the dataset and cannot be described
    (DECISIONS.md #51).
  - Documentation counts where the public can open it: a page or a metadata record that a publisher links to and
    that does not open is recorded as a finding and is not counted.

Certificates of the servers are checked through the trust store of the operating system when the package
truststore is installed (requirements.txt); otherwise through the certificates bundled with requests.

Usage (from the project root, with the .venv activated):
    python scripts\10_croissant_checks.py             all the datasets of the sample
    python scripts\10_croissant_checks.py --report    rebuilds the descriptions, the evidence and the report with
                                                      the recorded answers of the portal, without any call

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import html
import json
import logging
import re
import sys
import time
from collections import Counter
from importlib.metadata import version as installed_version
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import truststore
    truststore.inject_into_ssl()
    CERTIFICATES = "trust store of the operating system"
except ImportError:
    CERTIFICATES = "certificates bundled with requests"

import requests

try:
    import mlcroissant as mlc
except ImportError as error:
    raise SystemExit(f"The library mlcroissant could not be imported ({error}). It is listed in requirements.txt "
                     "and is installed with: python -m pip install -r requirements.txt")

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
ORGANISATION_FILE = ROOT / "criteria" / "file_organisation.csv"
DESCRIPTIONS_FILE = ROOT / "criteria" / "field_descriptions.csv"
PORTAL = "https://data.gov.gr"

HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}
TIMEOUT_SECONDS = (30, 120)      # connection, and waiting time for the answer
TRIES_PER_CALL = 3               # tries against network errors and server errors
WAIT_BETWEEN_TRIES = (5, 15)     # seconds before the second and the third try
PAUSE_SECONDS = 0.5              # pause between two calls

BY_HAND = "by hand"
CROISSANT_VERSION = "http://mlcommons.org/croissant/1.1"
VALIDATOR_VERSION = installed_version("mlcroissant")
PLUGIN = "croissant"             # name of the Croissant plugin of ckanext-dcat among the extensions of the portal
LICENCE_PREFIX = "http://publications.europa.eu/resource/authority/licence/"
NOT_SPECIFIED = "notspecified"   # entry "License not specified" of the licence list of the software of the portal
GTFS_REFERENCE = "https://gtfs.org/documentation/schedule/reference/"

# Properties that the specification of Croissant requires at the level of the dataset (Croissant Format
# Specification 1.1, dataset-level information), next to @context, @type and conformsTo, which every description
# written here carries.
REQUIRED = ("name", "description", "license", "url", "creator", "datePublished")
# Where the creator of a dataset is read from (column creator_source).
CREATOR_FIELD = "creator field of the dataset"
CREATOR_ORGANISATION = "organisation of the dataset"
CREATOR_FIELD_UNNAMED = "organisation of the dataset (the creator field holds no name)"

# Media type of a downloaded resource, from the type found by 05_resource_download.py and the suffix of the stored
# file, and of a table inside an archive, from the kind recorded by 06_file_checks.py.
MEDIA_TYPES = {
    "ole2": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "shapefile": "application/zip", "gtfs": "application/zip", "zip": "application/zip",
    "rar": "application/vnd.rar", "json": "application/json", "xml": "application/xml", "html": "text/html",
    "png": "image/png", "pdf": "application/pdf", "turtle": "text/turtle", "text": "text/plain",
}
SUFFIX_MEDIA_TYPES = {".csv": "text/csv", ".geojson": "application/geo+json",
                      ".kml": "application/vnd.google-earth.kml+xml"}
TABLE_MEDIA_TYPES = {
    "csv": "text/csv", "gtfs": "text/csv", "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "shapefile": "application/vnd.shp",
    "json": "application/json", "geojson": "application/geo+json", "rdf": "text/turtle",
}
SPREADSHEETS = {"xls", "xlsx"}
DELIMITED_TEXT = {"csv", "gtfs"}     # kinds of tables read by the name of the column
WITHOUT_RECORDS = {"documents", "map images"}

# Type of a field, from the kind of the values of the column recorded by 06_file_checks.py (file_formats). Numbers
# are integers only when every form found is an integer; a GTFS time may pass 24:00:00 and stays a text. The
# columns of a GTFS feed that the table does not list (identifiers, names, addresses) are texts.
FIELD_TYPES = {
    "text": mlc.DataType.TEXT, "code": mlc.DataType.TEXT, "list": mlc.DataType.TEXT, "": mlc.DataType.TEXT,
    "link": mlc.DataType.URL, "bool": mlc.DataType.BOOL, "GTFS integer": mlc.DataType.INTEGER,
    "GTFS number": mlc.DataType.FLOAT, "GTFS latitude": mlc.DataType.FLOAT, "GTFS longitude": mlc.DataType.FLOAT,
    "GTFS date": mlc.DataType.DATE, "GTFS time": mlc.DataType.TEXT, "GTFS colour": mlc.DataType.TEXT,
}
TYPE_NAMES = {mlc.DataType.TEXT: "text", mlc.DataType.URL: "link", mlc.DataType.BOOL: "boolean",
              mlc.DataType.INTEGER: "integer", mlc.DataType.FLOAT: "number", mlc.DataType.DATE: "date",
              mlc.DataType.DATETIME: "date and time", mlc.DataType.TIME: "time"}

CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "data_kind", "description_characters",
    "description_repeats_title", "licence", "resources_with_licence", "licence_dataset_field", "creator_source",
    "date_published", "version", "required_missing", "resources", "files_described", "files_without_name",
    "resources_not_obtained",
    "data_files", "checksums_in_metadata", "media_types_in_metadata", "datastore_tables", "tables_examined",
    "tables_outside_distribution", "tables_names_withheld", "tables_without_names", "record_sets", "fields",
    "field_types", "field_formats", "fields_described", "description_sources", "croissant_file",
    "validator_errors", "validator_warnings", "validator_messages", "documents_next_to_data", "publisher_pages",
    "portal_croissant", "ai4_proposal", "ai4_reason",
]
CATALOGUE_FIELDS = ["level", "property", "filled_from", "count", "of", "share", "note"]
PORTAL_FIELDS = ["sample_id", "dataset", "address", "tested_on", "http_status", "answer", "validator_errors",
                 "validator_warnings", "licence", "record_sets", "file"]


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


def number(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def with_noun(count: int, noun: str) -> str:
    """A number with its noun, in the singular or in the plural."""
    return f"{count:,} {noun}{'' if count == 1 else 's'}"


def share(count: int, total: int) -> str:
    return f"{100 * count / total:.1f}" if total else ""


def counted(counter: Counter) -> str:
    """The entries of a counter as a text, in alphabetical order."""
    return ", ".join(f"{name}: {count}" for name, count in sorted(counter.items()))


def own_resources(dataset: dict) -> list[dict]:
    """The resources of a dataset, without the automatic bundle of the portal."""
    return [resource for resource in dataset.get("resources") or []
            if isinstance(resource, dict) and not is_bundle(resource)]


def filled(value) -> bool:
    """Whether a metadata value holds anything."""
    return value not in (None, "", [], {}) and str(value).strip() not in ("", "[]", "{}")


def licence_term(resource: dict) -> str:
    """The term of the EU licence vocabulary that a resource carries, or an empty text (as for M4)."""
    text = str(resource.get("license") or "").strip()
    return text if text.startswith(LICENCE_PREFIX) and len(text) > len(LICENCE_PREFIX) else ""


def checksum_kind(resource: dict) -> str:
    """The kind of checksum in the metadata of a resource that a Croissant description accepts: md5 or sha256."""
    return {32: "md5", 64: "sha256"}.get(len(str(resource.get("hash") or "").strip()), "")


def in_datastore(resource: dict) -> bool:
    return str(resource.get("datastore_active")).strip().lower() == "true"


def position_label(value) -> str:
    """The label of a resource in the tables of the files: r001, r002, ..."""
    return f"r{number(value):03d}"


def file_name(address: str) -> str:
    """The last part of the path of an address, which is the name of the file where the address ends in one."""
    return unquote(urlsplit(address).path.rstrip("/").rsplit("/", 1)[-1])


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def read_catalogue(snapshot: Path, sample: dict[str, dict]) -> tuple[dict[str, dict], Counter]:
    """The records of the datasets of the sample, by sample id, and the counts of the whole catalogue: the datasets
    and the resources whose metadata can fill each property of a Croissant description."""
    by_id = {row["id"]: row["sample_id"] for row in sample.values()}
    found: dict[str, dict] = {}
    counts: Counter = Counter()
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("id") in by_id:
                found[by_id[record["id"]]] = record
            if record.get("type") != "dataset":
                continue
            resources = own_resources(record)
            name = filled(plain_text(record.get("title")))
            description = filled(plain_text(record.get("notes")))
            creators, creator_source = creator_names(record)
            creator = bool(creators)
            date = filled(record.get("issued")) or filled(record.get("metadata_created"))
            licensed = bool(resources) and all(licence_term(resource) for resource in resources)
            field_licence = any(filled(record.get(key)) for key in ("license", "license_url", "license_title"))
            named_licence = field_licence and str(record.get("license_id") or "").strip() != NOT_SPECIFIED
            basic = name and description and creator and date
            counts["datasets"] += 1
            counts["name"] += name
            counts["description"] += description
            counts["licence_resources"] += licensed
            counts["licence_field"] += field_licence
            counts["licence_field_named"] += named_licence
            counts["creator"] += creator
            counts["creator_field"] += creator_source == CREATOR_FIELD
            counts["creator_field_unnamed"] += creator_source == CREATOR_FIELD_UNNAMED
            counts["date"] += date
            counts["issued"] += filled(record.get("issued"))
            counts["keywords"] += filled(record.get("tags"))
            counts["version"] += filled(record.get("version"))
            counts["language"] += filled(record.get("language"))
            counts["with_resources"] += bool(resources)
            counts["address"] += bool(resources) and all(filled(resource.get("url")) for resource in resources)
            counts["media_type"] += bool(resources) and all(filled(r.get("mimetype")) for r in resources)
            counts["checksum"] += bool(resources) and all(checksum_kind(resource) for resource in resources)
            counts["datastore"] += any(in_datastore(resource) for resource in resources)
            counts["required_resources"] += bool(basic and licensed)
            counts["required_field"] += bool(basic and field_licence)
            counts["required_field_named"] += bool(basic and named_licence)
            for resource in resources:
                counts["resources"] += 1
                counts["resource_md5"] += checksum_kind(resource) == "md5"
                counts["resource_sha256"] += checksum_kind(resource) == "sha256"
                counts["resource_other_checksum"] += filled(resource.get("hash")) and not checksum_kind(resource)
                counts["resource_no_checksum"] += not filled(resource.get("hash"))
                counts["resource_name"] += filled(plain_text(resource.get("name")))
                counts["resource_media_type"] += filled(resource.get("mimetype"))
                counts["resource_datastore"] += in_datastore(resource)
    return found, counts


def catalogue_rows(counts: Counter) -> list[dict]:
    """The counts of the catalogue as a table: one row per property of a Croissant description."""
    datasets, resources = counts["datasets"], counts["resources"]
    generic = ("the generic licence field of the software of the portal, which the Croissant profile of "
               "ckanext-dcat reads and the portal neither displays nor exports (DECISIONS.md #31)")
    table = [
        ("dataset", "name", "title", "name", "required"),
        ("dataset", "description", "description (notes)", "description", "required"),
        ("dataset", "license", "licence term on every resource", "licence_resources",
         "required; the licence of a dataset is that of its resources (DECISIONS.md #31)"),
        ("dataset", "license", "licence field of the dataset (license_url, license_title)", "licence_field", generic),
        ("dataset", "license", "the same field, other than \"License not specified\"", "licence_field_named",
         "the entry \"License not specified\" would be written as the licence"),
        ("dataset", "creator", "creator field of the dataset, otherwise its organisation", "creator", "required"),
        ("dataset", "creator", "creator field of the dataset with at least one name", "creator_field",
         "what the Croissant profile of ckanext-dcat writes as the creator"),
        ("dataset", "creator", "creator field filled without any name", "creator_field_unnamed",
         "the profile would write a creator without a name; the organisation is written here"),
        ("dataset", "datePublished", "issued, otherwise the date of the record (metadata_created)", "date",
         "required"),
        ("dataset", "datePublished", "issued", "issued", "the field of the date of publication itself"),
        ("dataset", "keywords", "tags", "keywords", "recommended"),
        ("dataset", "version", "version", "version", "recommended"),
        ("dataset", "inLanguage", "language of the dataset", "language", "recommended"),
        ("dataset", "distribution", "at least one resource", "with_resources", ""),
        ("dataset", "contentUrl", "every resource with an address (url)", "address", ""),
        ("dataset", "encodingFormat", "every resource with a media type (mimetype)", "media_type", ""),
        ("dataset", "md5 or sha256", "every resource with a checksum of 32 or 64 characters (hash)", "checksum",
         "the validator asks for a checksum of every file"),
        ("dataset", "recordSet", "at least one resource in the DataStore", "datastore",
         "the columns that the portal knows already"),
        ("dataset", "all the required properties", "the licence read from the resources", "required_resources",
         "name, description, licence, creator and date; the address of the page always exists"),
        ("dataset", "all the required properties", "the licence read from the field of the dataset",
         "required_field", "what the Croissant profile of ckanext-dcat would write from the metadata as they are"),
        ("dataset", "all the required properties", "the same field, other than \"License not specified\"",
         "required_field_named", ""),
        ("resource", "name", "name of the resource", "resource_name", ""),
        ("resource", "md5", "checksum of 32 characters (hash)", "resource_md5", ""),
        ("resource", "sha256", "checksum of 64 characters (hash)", "resource_sha256", ""),
        ("resource", "checksum of another kind", "checksum of another length (hash)", "resource_other_checksum",
         "for example SHA-1, which a Croissant description does not accept"),
        ("resource", "no checksum", "empty hash", "resource_no_checksum", ""),
        ("resource", "encodingFormat", "media type (mimetype)", "resource_media_type", ""),
        ("resource", "recordSet", "resource in the DataStore", "resource_datastore", ""),
    ]
    rows = []
    for level, name, source, key, note in table:
        total = datasets if level == "dataset" else resources
        rows.append({"level": level, "property": name, "filled_from": source, "count": counts[key], "of": total,
                     "share": share(counts[key], total), "note": note})
    return rows


# ---------------------------------------------------------------------------
# Description of a dataset
# ---------------------------------------------------------------------------

def creator_names(dataset: dict) -> tuple[list[str], str]:
    """The creator of a dataset and where it is read from: the organisations named in the creator field of the
    dataset, otherwise the organisation that publishes the dataset. An entry of the field that is marked as a
    person is left out, and of every creator only the name is kept."""
    entries = dataset.get("creator") if isinstance(dataset.get("creator"), list) else []
    names = []
    for entry in entries:
        if not isinstance(entry, dict) or str(entry.get("type") or "").strip().lower() == "person":
            continue
        name = plain_text(entry.get("name"))
        if name and "@" not in name and name not in names:
            names.append(name)
    if names:
        return names, CREATOR_FIELD
    organisation = dataset.get("organization") if isinstance(dataset.get("organization"), dict) else {}
    title = plain_text(organisation.get("title"))
    if not title:
        return [], ""
    return [title], CREATOR_FIELD_UNNAMED if entries else CREATOR_ORGANISATION


def dataset_level(dataset: dict) -> dict:
    """What the metadata of the portal give for the properties of the dataset, by the name of the property."""
    resources = own_resources(dataset)
    creators, creator_source = creator_names(dataset)
    terms = sorted({licence_term(resource) for resource in resources} - {""})
    licensed = sum(1 for resource in resources if licence_term(resource))
    issued = str(dataset.get("issued") or "")[:10]
    created = str(dataset.get("metadata_created") or "")[:10]
    return {
        "name": plain_text(dataset.get("title")),
        "description": plain_text(dataset.get("notes")),
        "license": terms if resources and licensed == len(resources) else [],
        "url": f"{PORTAL}/dataset/{dataset['name']}" if dataset.get("name") else "",
        "creator": creators,
        "creator_source": creator_source,
        "datePublished": issued or created,
        "date_source": "issued" if issued else "metadata_created" if created else "",
        "dateModified": str(dataset.get("modified") or dataset.get("metadata_modified") or "")[:10],
        "version": str(dataset.get("version") or "").strip(),
        "keywords": [str(tag["name"]) for tag in dataset.get("tags") or []
                     if isinstance(tag, dict) and tag.get("name")],
        "licensed": licensed,
    }


def media_type(row: dict) -> str:
    """The media type of a downloaded resource (a row of the download log)."""
    suffix = Path(row.get("file", "")).suffix.lower()
    return SUFFIX_MEDIA_TYPES.get(suffix) or MEDIA_TYPES.get(row.get("detected_type", ""), "application/octet-stream")


def field_type(kind: str, forms: str):
    """The Croissant data type of a column, from the kind and the forms of its values."""
    if kind == "number":
        whole = "integer" in forms and not re.search(r"decimal|number|scientific|thousands|point:", forms)
        return mlc.DataType.INTEGER if whole else mlc.DataType.FLOAT
    if kind == "date":
        clock = "hh:mm" in forms
        day = bool(re.search(r"yyyy|date", forms))
        return mlc.DataType.DATETIME if clock and day else mlc.DataType.TIME if clock else mlc.DataType.DATE
    return FIELD_TYPES.get(kind, mlc.DataType.TEXT)


def examined_tables(profiles: list[dict], described: set[str]) -> tuple[list[dict], dict]:
    """The examined tables of a dataset whose file is among the described resources, each with the names of its
    columns, and the numbers of the examined tables that give no fields: those of files outside the described
    resources (for example files exported by hand), those whose names are withheld, and those of which the file
    profiles list no names (no header recognised, or a format without a list of columns). The column _id that the
    portal adds to the files of its DataStore does not count (as in 06_file_checks.py)."""
    tables = []
    left_out = {"outside": 0, "withheld": 0, "unnamed": 0}
    for row in profiles:
        if row.get("data_file") != "True" or row.get("examined") != "True":
            continue
        text = row.get("column_names", "")
        if row["position"] not in described:
            left_out["outside"] += 1
        elif not text.strip() and number(row.get("columns")):
            left_out["withheld"] += 1
        elif not text.strip() or text.startswith(("(no header recognised", "root element")) \
                or row.get("kind") not in TABLE_MEDIA_TYPES:
            left_out["unnamed"] += 1
        else:
            names = [name.strip() for name in text.split(" | ")]
            if names[:1] == ["_id"]:
                names = names[1:]
            tables.append({"position": row["position"], "member": row.get("member", ""),
                           "sheet": row.get("sheet", ""), "kind": row["kind"], "names": names})
    return tables, left_out


def column_sets(tables: list[dict]) -> list[dict]:
    """The different sets of columns among the tables of a dataset, in the order met: the first table of each set
    stands for it, and the others are counted."""
    sets: dict[tuple, dict] = {}
    for table in tables:
        key = (table["kind"] == "gtfs" and table["member"].rsplit("/", 1)[-1], tuple(table["names"]))
        if key in sets:
            sets[key]["tables"] += 1
        else:
            sets[key] = {**table, "tables": 1}
    return list(sets.values())


def outside_reference(text: str) -> tuple[dict[str, set[str]], set[str]]:
    """The GTFS columns outside the reference, by file, and the files that the reference does not hold, from the
    evidence of 08_documentation_checks.py (gtfs_columns_outside_reference)."""
    columns: dict[str, set[str]] = {}
    files: set[str] = set()
    for part in (text or "").split("; "):
        head, _, tail = part.partition(": ")
        if head.startswith("files that the list"):
            files |= {name.strip() for name in tail.split(",") if name.strip()}
        elif tail:
            columns.setdefault(head.strip(), set()).update(name.strip() for name in tail.split(",") if name.strip())
    return columns, files


def table_place(table: dict) -> str:
    """Where a table is found, in words: the resource, the file inside an archive, the sheet."""
    place = table["position"]
    if table["member"]:
        place += f", file {table['member']}"
    if table["sheet"]:
        place += f", sheet \"{table['sheet']}\""
    return place


def describe(dataset: dict, log: list[dict], profiles: list[dict], formats: list[dict],
             meanings: dict[str, str], documentation: dict):
    """The Croissant description of one dataset and the evidence on what it holds. Returns the context of the
    library (with the errors and the warnings of the validator), the description, or None when the validator
    refuses it, and the evidence."""
    resources = own_resources(dataset)
    level = dataset_level(dataset)
    missing = [name for name in REQUIRED if not level[name]]

    ctx = mlc.Context(conforms_to=CROISSANT_VERSION)
    by_resource = {str(resource.get("id")): resource for resource in resources}
    files, described, unnamed_files = [], set(), 0
    for row in sorted(log, key=lambda item: number(item["position"])):
        if row.get("outcome") != "available" or not row.get("sha256") or not row.get("address"):
            continue
        label = position_label(row["position"])
        resource = by_resource.get(row["resource_id"], {})
        name = plain_text(resource.get("name")) or plain_text(row.get("resource"))
        if not name:
            unnamed_files += 1
            name = file_name(row["address"]) or label
        details = plain_text(resource.get("description"))
        optional = {}
        if number(row.get("bytes")):
            optional["content_size"] = f"{number(row['bytes'])} B"
        if details and details != name:
            optional["description"] = details
        files.append(mlc.FileObject(ctx=ctx, id=label, name=name, content_url=row["address"],
                                    encoding_formats=[media_type(row)], sha256=row["sha256"], **optional))
        described.add(label)

    tables, left_out = examined_tables(profiles, described)
    sets = column_sets(tables)
    kinds: dict[str, list[dict]] = {}
    for row in formats:
        kinds.setdefault(row["name"], []).append(row)
    gtfs_declared = "GTFS" in documentation.get("standards_named", "")
    outside_columns, outside_files = outside_reference(documentation.get("gtfs_columns_outside_reference", ""))
    record_sets, members = [], {}
    types: Counter = Counter()
    by_format: Counter = Counter()
    from_table = from_gtfs = 0
    for set_number, table in enumerate(sets, 1):
        source = table["position"]
        if table["member"]:
            key = (table["position"], table["member"])
            if key not in members:
                members[key] = f"{table['position']}_m{len(members) + 1:02d}"
                files.append(mlc.FileObject(
                    ctx=ctx, id=members[key], name=table["member"].rsplit("/", 1)[-1], content_url=table["member"],
                    encoding_formats=[TABLE_MEDIA_TYPES[table["kind"]]], contained_in=[table["position"]]))
            source = members[key]
        set_id = "records" if len(sets) == 1 else f"records_{set_number:02d}"
        gtfs_file = table["member"].rsplit("/", 1)[-1] if table["kind"] == "gtfs" else ""
        fields = []
        for index, name in enumerate(table["names"], 1):
            label = name or f"column {index}"
            candidates = kinds.get(f"{gtfs_file}: {name}" if gtfs_file else name, [])
            same = [row for row in candidates if row.get("format") == table["kind"]
                    or (row.get("format") == "spreadsheet" and table["kind"] in SPREADSHEETS)]
            row = (same or candidates or [{}])[0]
            data_type = field_type(row.get("kind", ""), row.get("forms", ""))
            meaning = meanings.get(name, "")
            if meaning:
                from_table += 1
            elif gtfs_file and gtfs_declared and gtfs_file not in outside_files \
                    and name not in outside_columns.get(gtfs_file, set()):
                meaning = f"Field {name} of {gtfs_file}, defined in the GTFS Schedule Reference ({GTFS_REFERENCE})."
                from_gtfs += 1
            by_column = {"extract": mlc.Extract(ctx=ctx, column=label)} if table["kind"] in DELIMITED_TEXT else {}
            fields.append(mlc.Field(
                ctx=ctx, id=f"{set_id}/c{index:03d}", name=label, data_types=data_type,
                source=mlc.Source(ctx=ctx, file_object=source, **by_column),
                **({"description": meaning} if meaning else {})))
            types[TYPE_NAMES[data_type]] += 1
            by_format[table["kind"]] += 1
        same_columns = "" if table["tables"] == 1 else \
            f" The same columns are found in {table['tables']} of the examined tables of the dataset."
        record_sets.append(mlc.RecordSet(
            ctx=ctx, id=set_id, name=set_id, fields=fields,
            description=f"Columns of the table examined for the assessment ({table_place(table)})." + same_columns))

    values = {"ctx": ctx, "name": level["name"], "distribution": files, "record_sets": record_sets}
    for key, name in (("description", "description"), ("url", "url"), ("datePublished", "date_published"),
                      ("dateModified", "date_modified"), ("keywords", "keywords"), ("version", "version")):
        if level[key]:
            values[name] = level[key]
    if level["license"]:
        values["license"] = level["license"][0] if len(level["license"]) == 1 else level["license"]
    if level["creator"]:
        values["creators"] = [mlc.Organization(name=name) for name in level["creator"]]
    try:
        metadata = mlc.Metadata(**values)
    except mlc.ValidationError:
        metadata = None

    data_files = {row["position"] for row in profiles
                  if row.get("data_file") == "True" and row["position"] in described}
    sources = [text for text in (f"{relative(DESCRIPTIONS_FILE)}: {from_table}" if from_table else "",
                                 f"GTFS Schedule Reference: {from_gtfs}" if from_gtfs else "") if text]
    evidence = {
        "licence": "; ".join(term[len(LICENCE_PREFIX):] for term in level["license"]),
        "resources_with_licence": f"{level['licensed']} of {len(resources)}",
        "licence_dataset_field": str(dataset.get("license_id") or "").strip(),
        "creator_source": level["creator_source"],
        "date_published": f"{level['datePublished']} ({level['date_source']})" if level["datePublished"] else "",
        "version": level["version"],
        "required_missing": ", ".join(missing),
        "resources": len(resources),
        "files_described": len(described),
        "files_without_name": unnamed_files or "",
        "resources_not_obtained": len(resources) - len(described),
        "data_files": len(data_files),
        "checksums_in_metadata": f"{sum(1 for r in resources if checksum_kind(r))} of {len(resources)}",
        "media_types_in_metadata": f"{sum(1 for r in resources if filled(r.get('mimetype')))} of {len(resources)}",
        "datastore_tables": sum(1 for resource in resources if in_datastore(resource)) or "",
        "tables_examined": len(tables) + sum(left_out.values()),
        "tables_outside_distribution": left_out["outside"] or "",
        "tables_names_withheld": left_out["withheld"] or "",
        "tables_without_names": left_out["unnamed"] or "",
        "record_sets": len(record_sets),
        "fields": sum(types.values()),
        "field_types": counted(types),
        "field_formats": counted(by_format),
        "fields_described": from_table + from_gtfs,
        "description_sources": "; ".join(sources),
    }
    return ctx, metadata, evidence


def messages_of(issues) -> tuple[list[str], list[str]]:
    """The errors and the warnings that the validator collected, as sorted lists."""
    return sorted(str(item) for item in issues.errors), sorted(str(item) for item in issues.warnings)


def validate(description: dict) -> tuple[list[str], list[str]]:
    """Validation of a description read back from its JSON: the errors and the warnings of mlcroissant."""
    try:
        loaded = mlc.Dataset(jsonld=description)
    except mlc.ValidationError as error:
        # The message of the library lists the errors and then the warnings, each list under its own heading.
        found: dict[str, list[str]] = {"error": [], "warning": []}
        heading = ""
        for line in str(error).splitlines():
            text = line.strip()
            if text.endswith("during the validation:"):
                heading = "warning" if "warning(s)" in text else "error"
            elif text.startswith("-") and heading:
                found[heading].append(text.strip(" -"))
        return sorted(found["error"]) or [str(error)[:300]], sorted(found["warning"])
    except Exception as error:      # a description that the library cannot read at all
        return [f"{type(error).__name__}: {str(error)[:200]}"], []
    return messages_of(loaded.metadata.ctx.issues)


def short(messages: list[str]) -> str:
    """The messages of the validator without the name of the node that each one starts with."""
    cleaned = [re.sub(r"^\[[^\]]*\]\s*", "", message) for message in messages]
    return " ; ".join(dict.fromkeys(cleaned))


# ---------------------------------------------------------------------------
# The portal
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


def read_portal(session: requests.Session, datasets: dict[str, dict], folder: Path, today: str) -> list[dict]:
    """Whether the portal has the Croissant plugin of its software enabled (one call to status_show) and, only when
    it has, the description that it serves for every dataset of the sample, saved and validated."""
    address = f"{PORTAL}/api/3/action/status_show"
    facts = call(session, address)
    body = facts["body"] if isinstance(facts["body"], dict) else {}
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    extensions = result.get("extensions") if isinstance(result.get("extensions"), list) else None
    row = {"sample_id": "", "dataset": "", "address": address, "tested_on": today, "http_status": facts["status"]}
    if facts["status"] != 200 or extensions is None:
        parts = (f"HTTP {facts['status']}" if facts["status"] else "", facts["error"],
                 "the list of the extensions was not read")
        row["answer"] = "; ".join(part for part in parts if part)
        return [row]
    enabled = PLUGIN in extensions
    row["answer"] = (f"CKAN {result.get('ckan_version', '')}, {with_noun(len(extensions), 'extension')}; "
                     f"dcat plugin: {'yes' if 'dcat' in extensions else 'no'}; "
                     f"{PLUGIN} plugin: {'yes' if enabled else 'no'}")
    rows = [row]
    if not enabled:
        return rows
    for sample_id in sorted(datasets):
        name = datasets[sample_id].get("name", "")
        address = f"{PORTAL}/dataset/{name}/croissant.jsonld"
        facts = call(session, address)
        row = {"sample_id": sample_id, "dataset": name, "address": address, "tested_on": today,
               "http_status": facts["status"]}
        if facts["status"] == 200 and isinstance(facts["body"], dict):
            path = folder / "portal" / f"{sample_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(facts["body"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                            newline="\n")
            errors, warnings = validate(facts["body"])
            record_sets = facts["body"].get("recordSet")
            record_sets = record_sets if isinstance(record_sets, list) else [record_sets] if record_sets else []
            row.update(answer="description served", validator_errors=len(errors), validator_warnings=len(warnings),
                       licence="yes" if filled(facts["body"].get("license")) else "no",
                       record_sets=len(record_sets), file=relative(path))
        else:
            parts = (f"HTTP {facts['status']}" if facts["status"] else "", facts["error"], "no description served")
            row["answer"] = "; ".join(part for part in parts if part)
        rows.append(row)
    return rows


def portal_evidence(rows: list[dict], sample_id: str) -> str:
    """What the portal offers for one dataset, in one line."""
    state = next((row for row in rows if not row.get("sample_id")), None)
    if state is None:
        return "not asked"
    answer = state.get("answer", "")
    if f"{PLUGIN} plugin: no" in answer:
        return f"none: the {PLUGIN} plugin of the portal is not enabled ({state.get('tested_on', '')})"
    if f"{PLUGIN} plugin: yes" not in answer:
        return f"not read: {answer}"
    own = next((row for row in rows if row.get("sample_id") == sample_id), None)
    if own is None:
        return "plugin enabled; the description of the dataset was not asked for"
    if own.get("answer") != "description served":
        return f"plugin enabled; {own.get('answer', '')}"
    return (f"served by the portal: {own.get('validator_errors')} errors and {own.get('validator_warnings')} "
            f"warnings of the validator, licence: {own.get('licence')}, record sets: {own.get('record_sets')}")


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------

def propose(kind: str, evidence: dict) -> tuple[str, str]:
    """The proposed score of AI4 where a rule decides without judgement, otherwise the mark of the review."""
    more = ("1 when the documentation says more than the title about what the data contain or how they were "
            "collected, 0 when it only repeats the title")
    lacks = []
    outside = evidence["tables_outside_distribution"]
    not_resources = f"examined tables of files that are not resources of the dataset: {outside}"
    if evidence["required_missing"]:
        lacks.append(f"required by the specification and missing: {evidence['required_missing']}")
    if not evidence["files_described"] and outside:
        lacks += ["no resource of the dataset was obtained", not_resources]
    elif not evidence["files_described"]:
        lacks.append("no file of the dataset was obtained" + (f" ({kind})" if kind in WITHOUT_RECORDS else ""))
    elif not evidence["data_files"]:
        lacks.append(f"no data file: {kind}" if kind in WITHOUT_RECORDS else
                     "no data file among the resources obtained" + (f" ({not_resources})" if outside else ""))
    if evidence["validator_errors"]:
        lacks.append(f"{with_noun(evidence['validator_errors'], 'error')} of the validator")
    if lacks:
        if not evidence["files_described"] and outside:
            scores = f"1 at most, since the examined files are not resources of the dataset: {more}"
        elif not evidence["files_described"]:
            scores = f"1 at most, since no file was obtained: {more}"
        elif kind in WITHOUT_RECORDS:
            scores = ("data without records, judged with a datasheet: 2 when the documentation says what the data "
                      f"contain, how they were collected and for which uses they are suitable; otherwise {more}")
        else:
            scores = more
        return BY_HAND, (f"no valid description at the level of the dataset ({'; '.join(lacks)}); {scores} "
                         f"(the description repeats the title: {evidence.get('description_repeats_title', '')})")
    fields, described = evidence["fields"], evidence["fields_described"]
    withheld, unnamed = evidence["tables_names_withheld"], evidence["tables_without_names"]
    without_list = []
    if withheld:
        without_list.append(f"the columns of {with_noun(withheld, 'examined table')} are not written, their names "
                            "being withheld (DECISIONS.md #29)")
    if unnamed:
        without_list.append(f"{with_noun(unnamed, 'examined table')} without a list of columns in the file profiles")
    if fields and described == fields:
        if without_list:
            return BY_HAND, ("valid at the level of the dataset, every field written with its type and its meaning; "
                             f"{'; '.join(without_list)}: 2 when the columns of those tables are documented as well")
        every = "the field" if fields == 1 else f"all the {fields} fields"
        return "2", f"valid, with the type and the meaning of {every} ({evidence['description_sources']})"
    parts = [f"{with_noun(fields, 'field')} with the type, {described or 'none'} of them with a documented meaning"] \
        if fields else []
    parts += without_list
    return "1", "valid at the level of the dataset; " + ("; ".join(parts) if parts else "no field could be listed")


def proposed_scores(proposals: Counter) -> str:
    """The numbers of the datasets by proposed score, as a text."""
    return ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", BY_HAND) if proposals[score])


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], catalogue: list[dict], portal: list[dict], date: str,
                 titles: dict[str, str]) -> None:
    proposals = Counter(row["ai4_proposal"] for row in checks)
    state = next((row for row in portal if not row.get("sample_id")), {})
    by_format: Counter = Counter()
    for row in checks:
        for part in filter(None, row["field_formats"].split(", ")):
            name, _, count = part.partition(": ")
            by_format[name] += number(count)
    lines = [
        f"# Croissant descriptions of the datasets of the sample (AI4), snapshot of {date}",
        "",
        "Produced by `scripts/10_croissant_checks.py`. Every description is written only from the metadata of the "
        "portal and from the tables of the earlier checks, and is validated with the mlcroissant library "
        f"(version {VALIDATOR_VERSION}); a score is proposed only where a rule decides without judgement, and the "
        "final scores are recorded in `DECISIONS.md`. The descriptions and this report contain no records of the "
        "data.",
        "",
        "## Whole catalogue",
        "",
        "Datasets and resources whose metadata can fill each property of a Croissant description. The automatic "
        "bundle that the portal adds to every dataset is not counted among the resources.",
        "",
        "| Level | Property | Filled from | Count | Of | % | Note |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in catalogue:
        lines.append(f"| {row['level']} | {row['property']} | {md_cell(row['filled_from'])} | {row['count']:,} | "
                     f"{row['of']:,} | {row['share']} | {md_cell(row['note'])} |")
    lines += [
        "",
        "## The portal",
        "",
        (f"Asked on {state.get('tested_on', '')} ({state.get('address', '')}): {md_cell(state.get('answer', ''))}."
         if state else "The portal was not asked."),
        "",
    ]
    served = [row for row in portal if row.get("sample_id")]
    if served:
        lines += ["| Dataset | HTTP | Answer | Errors | Warnings | Licence | Record sets |",
                  "| --- | --- | --- | ---: | ---: | --- | ---: |"]
        for row in served:
            lines.append(f"| {row['sample_id']} | {row.get('http_status', '')} | {md_cell(row.get('answer', ''))} | "
                         f"{row.get('validator_errors', '')} | {row.get('validator_warnings', '')} | "
                         f"{row.get('licence', '')} | {row.get('record_sets', '')} |")
        lines.append("")
    lines += [
        "## Proposals",
        "",
        "Proposed AI4: " + proposed_scores(proposals) + ".",
        "",
        "| Dataset | Data | Proposal | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in checks:
        title = md_cell(titles.get(row["sample_id"], "")[:60])
        lines.append(f"| {row['sample_id']} {title} | {row['data_kind']} | {row['ai4_proposal']} | "
                     f"{md_cell(row['ai4_reason'])} |")
    lines += ["", "## The description at the level of the dataset", "",
              "| Dataset | Required and missing | Licence of the resources | Licence field of the dataset | "
              "Creator read from | Date of publication | Resources | Files described | Named by the address | Data "
              "files | Checksums in the metadata | Media types in the metadata | Errors | Warnings | Messages of the "
              "validator |",
              "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} | {md_cell(row['required_missing']) or 'none'} | "
                     f"{md_cell(row['licence']) or 'none'} ({row['resources_with_licence']}) | "
                     f"{md_cell(row['licence_dataset_field'])} | {row['creator_source']} | "
                     f"{row['date_published']} | {row['resources']} | "
                     f"{row['files_described']} | {row['files_without_name']} | {row['data_files']} | "
                     f"{row['checksums_in_metadata']} | {row['media_types_in_metadata']} | "
                     f"{row['validator_errors']} | {row['validator_warnings']} | "
                     f"{md_cell(row['validator_messages'])} |")
    lines += ["", "## The fields", "",
              f"Fields by the format of their file: {counted(by_format) or 'none'}. The column is given as the way "
              "to read the values only for delimited text (csv, gtfs).", "",
              "| Dataset | Tables examined | Outside the described files | Names withheld | Without a list of "
              "columns | Record sets | Fields | Types | Formats | With a documented meaning | Source of the meaning "
              "| DataStore tables |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | ---: |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} | {row['tables_examined']} | {row['tables_outside_distribution']} | "
                     f"{row['tables_names_withheld']} | {row['tables_without_names']} | {row['record_sets']} | "
                     f"{row['fields']} | {md_cell(row['field_types'])} | {md_cell(row['field_formats'])} | "
                     f"{row['fields_described']} | {md_cell(row['description_sources'])} | "
                     f"{row['datastore_tables']} |")
    lines += ["", "## Evidence for the datasets judged by hand", "",
              "From `08_documentation_checks.py`: what the metadata offer beyond the title.", "",
              "| Dataset | Description (characters) | Repeats the title | Documents next to the data | Pages of the "
              "publisher |",
              "| --- | ---: | --- | --- | --- |"]
    for row in checks:
        if row["ai4_proposal"] == BY_HAND:
            lines.append(f"| {row['sample_id']} | {row['description_characters']} | "
                         f"{row['description_repeats_title']} | {md_cell(row['documents_next_to_data'])} | "
                         f"{md_cell(row['publisher_pages'])} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.getLogger("absl").setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description="Croissant descriptions of the datasets of the sample and their "
                                                 "validation (criterion AI4).")
    parser.add_argument("--report", action="store_true",
                        help="rebuild everything with the recorded answers of the portal, without any call")
    args = parser.parse_args()

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    log_file = PROCESSED_DIR / f"resource_downloads_{date}.csv"
    profiles_file = PROCESSED_DIR / f"file_profiles_{date}.csv"
    formats_file = PROCESSED_DIR / f"file_formats_{date}.csv"
    documentation_file = PROCESSED_DIR / f"documentation_checks_{date}.csv"
    for needed, script in ((log_file, "05_resource_download.py"), (profiles_file, "06_file_checks.py"),
                           (formats_file, "06_file_checks.py"), (documentation_file, "08_documentation_checks.py")):
        if not needed.exists():
            raise SystemExit(f"{relative(needed)} not found. Run {script} first.")
    if not DESCRIPTIONS_FILE.exists():
        raise SystemExit(f"{relative(DESCRIPTIONS_FILE)} not found.")
    log = read_csv(log_file)
    profiles = read_csv(profiles_file)
    formats = read_csv(formats_file)
    documentation = {row["sample_id"]: row for row in read_csv(documentation_file)}
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    meanings: dict[str, dict[str, str]] = {}
    for row in read_csv(DESCRIPTIONS_FILE):
        meanings.setdefault(row["sample_id"], {})[row["column"]] = row["description"].strip()
    checks_file = PROCESSED_DIR / f"croissant_checks_{date}.csv"
    catalogue_file = PROCESSED_DIR / f"croissant_catalogue_{date}.csv"
    portal_file = PROCESSED_DIR / f"croissant_portal_{date}.csv"
    folder = OUT_DIR / f"croissant_{date}"
    report_file = folder / "croissant_checks.md"
    today = dt.date.today().isoformat()

    print(f"Snapshot: {relative(snapshot)}")
    print(f"Validator: mlcroissant {VALIDATOR_VERSION}; descriptions written for Croissant "
          f"{CROISSANT_VERSION.rsplit('/', 1)[-1]}")
    datasets, counts = read_catalogue(snapshot, sample)
    catalogue = catalogue_rows(counts)
    total = counts["datasets"]
    print(f"Datasets of the catalogue: {total:,}; with every required property, the licence read from the "
          f"resources: {counts['required_resources']:,} ({share(counts['required_resources'], total)}%); from the "
          f"licence field of the dataset: {counts['required_field']:,} ({share(counts['required_field'], total)}%)")
    print(f"Datasets with a checksum on every resource: {counts['checksum']:,} "
          f"({share(counts['checksum'], total)}%); with a table in the DataStore: {counts['datastore']:,} "
          f"({share(counts['datastore'], total)}%)")
    print(f"Datasets of the sample: {len(sample)}")

    if args.report:
        print("Rebuilding with the recorded answers of the portal, without any call.")
        portal = read_csv(portal_file) if portal_file.exists() else []
    else:
        print(f"Certificates checked through the {CERTIFICATES}.")
        with requests.Session() as session:
            portal = read_portal(session, datasets, folder, today)
    state = next((row for row in portal if not row.get("sample_id")), None)
    print("Portal: " + (state.get("answer", "") if state else "not asked (no recorded answer)"))

    folder.mkdir(parents=True, exist_ok=True)
    checks = []
    for sample_id in sorted(sample):
        dataset = datasets.get(sample_id) or {}
        entry = organisation.get(sample_id, {})
        evidence_of_08 = documentation.get(sample_id, {})
        ctx, metadata, evidence = describe(
            dataset, [row for row in log if row["sample_id"] == sample_id],
            [row for row in profiles if row["sample_id"] == sample_id],
            [row for row in formats if row["sample_id"] == sample_id],
            meanings.get(sample_id, {}), evidence_of_08)
        path = folder / f"{sample_id}.json"
        if metadata is None:
            errors, warnings = messages_of(ctx.issues)
            written = ""
            if path.exists():
                path.unlink()
        else:
            text = json.dumps(metadata.to_json(), ensure_ascii=False, indent=2, default=str)
            path.write_text(text + "\n", encoding="utf-8", newline="\n")
            errors, warnings = validate(json.loads(text))
            written = relative(path)
        missing = entry.get("no_data_file", "").strip()
        kind = missing or ("data files" if evidence["data_files"] else "no data file among the resources obtained")
        evidence.update(
            croissant_file=written, validator_errors=len(errors), validator_warnings=len(warnings),
            validator_messages=short(errors + warnings),
            description_characters=evidence_of_08.get("description_characters", ""),
            description_repeats_title=evidence_of_08.get("description_repeats_title", ""),
            documents_next_to_data=evidence_of_08.get("documents_next_to_data", ""),
            publisher_pages=evidence_of_08.get("publisher_pages", ""),
            portal_croissant=portal_evidence(portal, sample_id))
        proposal, reason = propose(missing, evidence)
        checks.append({"sample_id": sample_id, "dataset": dataset.get("name", sample[sample_id].get("name", "")),
                       "group": sample[sample_id].get("group", ""), "category": sample[sample_id].get("category", ""),
                       "data_kind": kind, **evidence, "ai4_proposal": proposal, "ai4_reason": reason})
    write_csv(checks_file, CHECK_FIELDS, checks)
    write_csv(catalogue_file, CATALOGUE_FIELDS, catalogue)
    write_csv(portal_file, PORTAL_FIELDS, portal)
    write_report(report_file, checks, catalogue, portal, date, titles)

    for check in checks:
        print(f"{check['sample_id']} AI4 {check['ai4_proposal']}: {check['ai4_reason'][:140]}")
    print("Proposed AI4: " + proposed_scores(Counter(check["ai4_proposal"] for check in checks)))
    written = sum(1 for check in checks if check["croissant_file"])
    in_text = sum(number(part.partition(": ")[2]) for check in checks
                  for part in check["field_formats"].split(", ") if part.partition(": ")[0] in DELIMITED_TEXT)
    print(f"Descriptions written: {written}; with errors of the validator: "
          f"{sum(1 for check in checks if check['validator_errors'])}; fields: "
          f"{sum(check['fields'] for check in checks):,}, with a documented meaning: "
          f"{sum(check['fields_described'] for check in checks):,}, in delimited text files: {in_text:,}")
    print("Files:")
    for path in (checks_file, catalogue_file, portal_file, report_file):
        print(f"  {relative(path)}")
    print(f"  {relative(folder)}/Sxx.json ({written} descriptions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
