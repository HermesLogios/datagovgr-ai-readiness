r"""
11_retrieval_checks.py
Phase 3, step 3: evidence on the suitability of the datasets of the sample for retrieval (criterion AI5: can the
content be split into self-contained pieces that an AI system can retrieve and cite).

What it does, in order:
  1. Reads the date of the newest catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz), the sample
     (data/processed/sample.csv), the organisation of the files (criteria/file_organisation.csv) and the tables of
     05_resource_download.py and 06_file_checks.py (download log, file profiles).
  2. Sorts every table examined for AI1 by its layout, as the file profiles record it. A table whose every row
     after the header is a record (layout score 2, or empty rows as its only defect) can be split into records as
     it is, and is read again from the downloaded file. A table with rows that are not records (titles, totals,
     sub-headings, notes, a second header, merged cells) has to be cleaned first, and is not read. Hidden sheets
     are left out, as in the file profiles.
  3. In every table that is read, counts the cells with text (the names of the columns included), the cells with
     Greek letters and the cells whose text is damaged: a replacement character, characters of another encoding
     in the place of Greek letters (named by the form that they take), or question marks in the place of letters.
  4. Looks for an identifier of the records. The columns are sorted by their name and their values:
       - numbers of the rows: whole numbers that count the rows one by one in the order of the file, or whole
         numbers under a name that software or a list gives to the number of the row (_id, FID, OBJECTID, OID,
         α/α, #);
       - geometries and nested values;
       - codes, by their name, as in 06_file_checks.py;
       - periods: dates, time stamps, and the years or months of a column named after them;
       - measures: every other column of numbers;
       - links and text.
     An identifier is a column of codes, links, periods or text that is filled and different in every record, or
     the smallest combination of up to four such columns; numbers of rows, measures and geometries take no part.
     Combinations are sought among the ten such columns with the most different values. In a table whose
     candidate columns hold more than 2,000,000 values, single columns and pairs of the first four are tried.
     When there is no identifier, the evidence names the column nearest to one, with the number of records in
     which it repeats an earlier value, the candidate columns with empty cells, and the number of records that
     repeat an earlier one in every column, the columns that number the rows left out. When a column of whole
     numbers is then filled and different in every record, the table is left for the review: the values do not
     show whether such a column is an identifier or a measure. In the files of a GTFS feed the primary key of
     the GTFS Schedule Reference is checked instead, and where it is met again the records that repeat an
     earlier one in every column are counted. In an RDF file the identifier of a record is the URI of its
     subject.
  5. Extracts the text of every PDF document among the files obtained and counts, page by page, its letters and
     its Greek letters. The text itself is not kept.
  6. Proposes a score only where a rule decides without judgement. A dataset is marked "by hand" and is judged in
     the review of the criterion when its text is damaged, when a table could not be read or holds another
     number of records than its profile, when the search for an identifier could not cover every combination,
     when only a column of whole numbers tells its records apart, or when its documents are not among the files
     obtained.
  7. Writes:
        data/processed/retrieval_checks_YYYY-MM-DD.csv     one row per dataset of the sample: the evidence and
                                                            the proposal
        data/processed/retrieval_tables_YYYY-MM-DD.csv     one row per examined table: layout, text, columns,
                                                            identifier
        outputs/retrieval_YYYY-MM-DD/retrieval_checks.md   the same evidence as a report
     The date in the names is the date of the snapshot. None of the files contains a value of a record: of the
     tables only counts and names of columns are written, and the names of the columns that the file profiles
     withhold (DECISIONS.md #29) are replaced by their position.

Rules of AI5 (card approved on 12 November 2026; recorded in DECISIONS.md #49):
  - The files judged are those examined for AI1 (criteria/file_organisation.csv): of the same data in several
    formats the best one counts, of the parts of a dataset the worst one.
  - A piece is one record with the names of its columns, or one passage of a document. An image of a map has no
    pieces.
  - Reading a standard structured format with a library (delimited text, JSON, a GTFS feed, RDF, a shapefile, a
    sheet with a plain table) is not a conversion. A conversion is the extraction of the text of a PDF document
    or the cleaning of a sheet laid out for printing.
  - A stable identifier is a column, or a combination of up to four columns, with a value in every record and
    without any repetition. A name can be part of it. The number of the row and the columns of measures do not
    count. The identifier names or codes the thing that the record describes: whether a column that is
    different in every record does so, or gives only a class to which the thing belongs, is judged in the
    review.
  - The link to the source is the permanent address of the resource on the portal (DECISIONS.md #33). Data that
    are not among the resources of the dataset have none.
  - Datasets with records: 2 when every row after the header is a record (an empty row does not matter), the text
    is read without damaged characters, every record has an identifier and the file is a resource of the dataset;
    1 when one of these is missing.
  - PDF documents: 1 when their text can be extracted, 0 when they are scanned images. Documents that are not
    among the files obtained are judged in the review.
  - Images of maps: 0. Datasets of which no file was obtained: 0.

Usage (from the project root, with the .venv activated):
    python scripts\11_retrieval_checks.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import warnings
import zipfile
from array import array
from collections import Counter
from itertools import combinations
from operator import itemgetter
from pathlib import Path

import openpyxl
import rdflib
import shapefile
import xlrd

try:
    import pypdf
except ImportError as error:
    raise SystemExit(f"The library pypdf could not be imported ({error}). It is listed in requirements.txt and is "
                     "installed with: python -m pip install -r requirements.txt")

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
ORGANISATION_FILE = ROOT / "criteria" / "file_organisation.csv"

BY_HAND = "by hand"
KEY_COLUMNS = 4                  # columns of the largest combination tried as an identifier
COMBINED_COLUMNS = 10            # columns with the most different values among which combinations are tried
MEMORY_VALUES = 2_000_000        # values of candidate columns kept in memory for the search of a combination
ANNOUNCED_RECORDS = 500_000      # records above which the reading of a dataset is announced on the console
PAGE_LETTERS = 30                # letters that make a page of a PDF document a page with text
DAMAGED_SHARE = 0.01             # damaged characters per letter above which the text of a PDF is judged by hand
LISTED = 4                       # tables, columns or identifiers listed in a cell before "and N more"
HASH_MASK = (1 << 64) - 1

# Datasets whose column names are not written (DECISIONS.md #29): the columns are named by their position.
PERSONAL_DATA_SUSPECTED = {"S24", "S29"}

# Layout of a table, from the file profiles.
RECORDS = "records"
RECORDS_AND_EMPTY_ROWS = "records, with empty rows"
NOT_RECORDS = "rows that are not records"
NOT_READ = "not read"
# Defects of the layout, other than empty rows, counted in the file profiles.
LAYOUT_DEFECTS = ("title_rows", "totals_rows", "subheading_rows", "notes_below", "merged_in_data",
                  "numbers_as_text_columns", "extra_field_rows", "cells_beyond_header", "repeated_headers")
TABLE_KINDS = {"csv", "gtfs", "xls", "xlsx", "json", "geojson", "shapefile", "rdf"}
ARCHIVE_SUFFIXES = (".zip", ".rar", ".kmz")

# Kinds of columns.
EMPTY_COLUMN, ROW_NUMBER, SHAPE, CODE, PERIOD, MEASURE, LINK, TEXT = (
    "empty", "number of the row", "geometry or nested values", "code", "period", "measure", "link", "text")
PREFERENCE = {CODE: 0, LINK: 1, PERIOD: 2, TEXT: 3}      # order in which the columns are tried as identifiers

# Primary key of every file of the GTFS Schedule Reference (gtfs.org/documentation/schedule/reference, revision of
# 27 April 2026): the fields that identify a record. ("*",) stands for all the fields, () for no key.
GTFS_KEYS = {
    "agency.txt": ("agency_id",), "stops.txt": ("stop_id",), "routes.txt": ("route_id",), "trips.txt": ("trip_id",),
    "stop_times.txt": ("trip_id", "stop_sequence"), "calendar.txt": ("service_id",),
    "calendar_dates.txt": ("service_id", "date"), "fare_attributes.txt": ("fare_id",), "fare_rules.txt": ("*",),
    "timeframes.txt": ("*",), "rider_categories.txt": ("rider_category_id",), "fare_media.txt": ("fare_media_id",),
    "fare_products.txt": ("fare_product_id", "rider_category_id", "fare_media_id"),
    "fare_leg_rules.txt": ("network_id", "from_area_id", "to_area_id", "from_timeframe_group_id",
                           "to_timeframe_group_id", "fare_product_id"),
    "fare_leg_join_rules.txt": ("from_network_id", "to_network_id", "from_stop_id", "to_stop_id"),
    "fare_transfer_rules.txt": ("from_leg_group_id", "to_leg_group_id", "fare_product_id", "transfer_count",
                                "duration_limit"),
    "areas.txt": ("area_id",), "stop_areas.txt": ("*",), "networks.txt": ("network_id",),
    "route_networks.txt": ("route_id",), "shapes.txt": ("shape_id", "shape_pt_sequence"),
    "frequencies.txt": ("trip_id", "start_time"),
    "transfers.txt": ("from_stop_id", "to_stop_id", "from_trip_id", "to_trip_id", "from_route_id", "to_route_id"),
    "pathways.txt": ("pathway_id",), "levels.txt": ("level_id",), "location_groups.txt": ("location_group_id",),
    "location_group_stops.txt": ("*",), "booking_rules.txt": ("booking_rule_id",),
    "translations.txt": ("table_name", "field_name", "language", "record_id", "record_sub_id", "field_value"),
    "feed_info.txt": (), "attributions.txt": ("attribution_id",),
}

# Names of identifier columns, as in 06_file_checks.py.
IDENTIFIER_WORDS = re.compile(r"(?:^|[\W_])(?:id|fid|objectid|code|kodikos|kodik\w*|κωδ\w*|kod|kwd\w*|α\W?α|a\W?a|αφμ"
                              r"|afm|kaek|καεκ|τ\W?κ|tk|zip|notation|identifier|ar\W*prot\w*|αρ\W*πρωτ\w*"
                              r"|αριθμ\w*\W*πρωτ\w*|α\W?φ\W?|a\W?ph\W?|αρ\W*φακ\w*|ar\W*fak\w*)"
                              r"(?:$|[\W_\d])")
IDENTIFIER_END = re.compile(r"(?:code|kod|objectid|identifier)_?\d*$")
CAMEL_ID = re.compile(r"[a-z](?:Id|ID)_?\d*$")
# Names of the number of the row: the number that the DataStore of the portal (_id), a map server or a GIS program
# (FID, OBJECTID, OID) gives to every row, and the running number of a list (α/α, #).
ROW_NUMBER_NAME = re.compile(r"_id|(?:ogc_)?fid|oid|objectid(?:_\d+)?|[αa]\W?[αa]\W?|#")
YEAR_NAME = re.compile(r"ετοσ|ετη|χρονια|year")
MONTH_NAME = re.compile(r"μηνα|μην\b|month")

# Forms of the values of a column.
NUMBER = re.compile(r"[+-]?(?:\d{1,3}(?:[.\u00a0 ]\d{3})+|\d+)(?:[.,]\d+)?(?:[eE][+-]?\d+)?%?")
WHOLE_NUMBER = re.compile(r"\d{1,18}(?:\.0*)?")
FEATURE_NUMBER = re.compile(r"[^\s.]+\.\d+")      # identifier that a map server gives to a feature: layer.17
ISO_MOMENT = re.compile(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")
DAY_FIRST_MOMENT = re.compile(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{4}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?")
COMPACT_MOMENT = re.compile(r"(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d"
                            r"(?:[0-5]\d)?")
YEAR = re.compile(r"(?:18|19|20)\d\d")
MONTH = re.compile(r"0?[1-9]|1[0-2]")
WEB_LINK = re.compile(r"https?://\S+", re.IGNORECASE)
WELL_KNOWN_TEXT = re.compile(r"(?:SRID=\d+;)?\s*(?:MULTI)?(?:POINT|LINESTRING|POLYGON|GEOMETRYCOLLECTION)\s*"
                             r"(?:Z|M|ZM)?\s*\(", re.IGNORECASE)
WELL_KNOWN_START = "SMPLGsmplg"

# Text of a cell.
ASCII_LETTER = re.compile(r"[A-Za-z]")
LETTER = re.compile(r"[^\W\d_]")
GREEK_LETTER = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
# Greek text read with another encoding, by the form that the damage takes: control characters of the range C1;
# the pairs that UTF-8 Greek gives when it is read as Windows-1252 or Latin-1; the pairs that it gives when it is
# read as Windows-1253 (a capital xi or omicron before a sign); runs of accented Latin letters, which
# Windows-1253 Greek gives; box-drawing characters next to letters or to each other, which Greek read with a DOS
# code page gives.
ENCODING_FORMS = (
    ("control characters", re.compile("[\u0080-\u009f]")),
    ("UTF-8 read as Windows-1252 or Latin-1",
     re.compile("(?:[\u00c3\u00ce\u00cf][\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc"
                "\u2013\u2014\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122]){2,}")),
    ("UTF-8 read as Windows-1253",
     re.compile("(?:[\u039e\u039f][\u00a0-\u00bf\u0384-\u038f\u2013-\u2015\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039"
                "\u203a\u20ac\u2122\u0192]){2,}")),
    ("accented Latin letters in a row", re.compile("[\u00c0-\u00ff]{4,}")),
    ("box-drawing characters", re.compile("[\u2500-\u259f](?=[\\w\u2500-\u259f])|(?<=\\w)[\u2500-\u259f]")),
)
OTHER_ENCODING = re.compile("|".join(pattern.pattern for _, pattern in ENCODING_FORMS))
# Runs of signs of the upper half of Windows-1252, which Greek written with a DOS code page gives when it is read
# as Windows-1252. A run counts when it holds four signs or more, three of them different: quotation marks around
# an ellipsis or a dash do not make one.
SIGN_RUN = re.compile("[\u00a1-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013\u2014"
                      "\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122]{4,}")
SIGN_KINDS = 3
REPLACED, ENCODING, MARKS = ("replacement character", "characters of another encoding",
                             "question marks in the place of letters")
LOST_LETTERS = 4                 # question marks that, as half of a cell or more, stand for lost letters

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")   # headers and footers of print layouts

CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "data_kind", "organisation", "combine", "tables_examined",
    "tables_read", "tables_not_records", "tables_not_read", "records_read", "encodings", "text_cells", "greek_cells",
    "damaged_cells", "damaged_kinds", "tables_with_identifier", "tables_without_identifier", "identifiers",
    "identifier_kinds", "identifier_with_text", "row_number_columns", "repeating_records", "tables_outside_resources",
    "link_to_source", "documents", "decisive", "ai5_proposal", "ai5_reason",
]
TABLE_FIELDS = [
    "sample_id", "position", "member", "sheet", "kind", "encoding", "layout", "layout_defects", "read", "records",
    "records_in_profile", "columns", "text_cells", "greek_cells", "damaged_cells", "damaged_kinds",
    "row_number_columns", "measure_columns", "geometry_columns", "candidate_columns", "columns_with_empty_cells",
    "identifier", "identifier_kind", "identifier_source", "other_unique_columns", "unique_number_columns",
    "nearest_column", "nearest_column_repeats", "repeating_records", "resource_of_the_dataset", "outcome", "note",
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


def number(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def with_noun(count: int, noun: str) -> str:
    """A number with its noun, in the singular or in the plural."""
    return f"{count:,} {noun}{'' if count == 1 else 's'}"


def listed(items: list[str], limit: int = LISTED, separator: str = "; ") -> str:
    """The first items of a list and the number of those left out."""
    shown = separator.join(items[:limit])
    return shown + (f"{separator}and {len(items) - limit} more" if len(items) > limit else "")


def position_label(value) -> str:
    """The label of a resource in the tables of the files: r001, r002 and so on."""
    text = str(value or "")
    return text if text.startswith("r") else f"r{number(text):03d}"


def normalise(text: str) -> str:
    """Lower case without accents, final sigma as sigma, as in 06_file_checks.py."""
    text = unicodedata.normalize("NFD", str(text).strip().lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").replace("ς", "σ")


def identifier_name(name: str) -> bool:
    """Whether the name of a column marks an identifier, as in 06_file_checks.py."""
    text = normalise(name)
    return bool(IDENTIFIER_WORDS.search(text) or IDENTIFIER_END.search(text) or CAMEL_ID.search(str(name)))


def where_of(row: dict) -> str:
    """Where a table is found, in words: the resource, the file inside an archive, the sheet."""
    place = row["position"]
    if row.get("member"):
        place += f", file {row['member']}"
    if row.get("sheet"):
        place += f", sheet \"{row['sheet']}\""
    return place


# ---------------------------------------------------------------------------
# Files inside archives
# ---------------------------------------------------------------------------

class TableNotRead(Exception):
    """A table that cannot be read. Its message names no value of the data and no folder of the computer, so
    that it can be written in the tables of the results."""


class MemberNotFound(TableNotRead):
    """A file that the file profiles name and the archive does not hold under that name."""


def zip_encoding(path: Path) -> str | None:
    """The code page of the names of a ZIP archive that do not carry the UTF-8 flag, as 06_file_checks.py reads
    them: Greek DOS (cp737) or Greek Windows (cp1253) when one of them gives Greek letters."""
    with zipfile.ZipFile(path) as archive:
        raw = [info.filename.encode("cp437") for info in archive.infolist() if not info.flag_bits & 0x800]
    if all(name.isascii() for name in raw):
        return None
    best, best_count = None, 0
    for encoding in ("cp737", "cp1253"):
        count = sum(1 for name in raw for character in name.decode(encoding, errors="replace")
                    if "\u0386" <= character <= "\u03ce")
        if count > best_count:
            best, best_count = encoding, count
    return best


class Extracted:
    """The files taken out of the archives of one dataset, in a temporary folder that is removed when the dataset
    has been examined. A member of a ZIP archive is taken out alone and is removed when the next table is asked
    for; a RAR archive is taken out whole, once, with the tar program of the operating system, as in
    06_file_checks.py."""

    def __init__(self) -> None:
        self.folder = tempfile.TemporaryDirectory(prefix="datagovgr_", ignore_cleanup_errors=True)
        self.whole: dict[Path, Path] = {}
        self.single: list[Path] = []
        self.targets = 0

    def close(self) -> None:
        self.folder.cleanup()

    def target(self) -> Path:
        self.targets += 1
        path = Path(self.folder.name) / f"{self.targets:04d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def release(self) -> None:
        """Removes the members of ZIP archives taken out for the previous table."""
        for path in self.single:
            shutil.rmtree(path.parent, ignore_errors=True)
        self.single = []

    def from_zip(self, archive: Path, name: str) -> Path:
        with zipfile.ZipFile(archive, metadata_encoding=zip_encoding(archive)) as bundle:
            names = {info.filename: info for info in bundle.infolist() if not info.is_dir()}
            info = names.get(name)
            if info is None:
                wanted = name.lower()
                matches = [found for found_name, found in names.items() if found_name.lower() == wanted]
                if not matches:
                    last = wanted.rsplit("/", 1)[-1]
                    matches = [found for found_name, found in names.items()
                               if found_name.lower().rsplit("/", 1)[-1] == last]
                if len(matches) != 1:
                    raise MemberNotFound(f"file not found in the archive: {name}")
                info = matches[0]
            # A short name of its own, so that a long name inside the archive cannot exceed the limit of a path.
            path = self.target() / f"member{Path(info.filename).suffix.lower()}"
            with bundle.open(info) as source, open(path, "wb") as handle:
                shutil.copyfileobj(source, handle)
        self.single.append(path)
        return path

    def from_rar(self, archive: Path, name: str) -> Path:
        folder = self.whole.get(archive)
        if folder is None:
            folder = self.target()
            tool = shutil.which("tar")
            if not tool:
                raise TableNotRead("no tar program to open the RAR archive")
            result = subprocess.run([tool, "-xf", str(archive), "-C", str(folder)], capture_output=True, timeout=3600)
            if result.returncode != 0:
                raise TableNotRead("the RAR archive could not be opened with tar")
            self.whole[archive] = folder
        path = folder / name
        if not path.is_file():
            last = name.lower().rsplit("/", 1)[-1]
            matches = [found for found in folder.rglob("*") if found.is_file() and found.name.lower() == last]
            if len(matches) != 1:
                raise MemberNotFound(f"file not found in the archive: {name}")
            path = matches[0]
        return path

    def member(self, archive: Path, name: str) -> Path:
        """The file of a member of an archive, found by the name recorded in the file profiles. A member of an
        archive that lies inside the archive is found through the inner archive."""
        take = self.from_zip if zipfile.is_zipfile(archive) else self.from_rar
        try:
            return take(archive, name)
        except MemberNotFound:
            parts = name.split("/")
            for cut in range(1, len(parts)):
                inner = "/".join(parts[:cut])
                if inner.lower().endswith(ARCHIVE_SUFFIXES):
                    try:
                        return self.member(take(archive, inner), "/".join(parts[cut:]))
                    except MemberNotFound:
                        continue
            raise

    def file_of(self, profile: dict, suffix: str = "") -> Path:
        """The file of a table on disk. With a suffix, the file with the same name and that suffix: the attribute
        table (.dbf) of a shapefile."""
        self.release()
        path = ROOT / profile["file"]
        member = profile.get("member") or ""
        if suffix:
            member = (member or path.name).rsplit(".", 1)[0] + suffix
            if not profile.get("member"):
                path, member = path.with_name(member), ""
        if not path.is_file():
            raise TableNotRead("the downloaded file is not in data/raw/resources")
        return self.member(path, member) if member else path


# ---------------------------------------------------------------------------
# Records of a table
# ---------------------------------------------------------------------------

def cell_text(value) -> str:
    """The text of a value of a workbook, a shapefile or a JSON document. A list or an object gives no text."""
    if value is None or isinstance(value, (list, dict)):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value)
    if isinstance(value, dt.datetime):
        if (value.hour, value.minute, value.second) == (0, 0, 0):
            return value.date().isoformat()
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return str(value).strip()


def header_and_records(rows):
    """The names of the columns and a reader of the records, from a reader of the rows of a table that starts at
    its header row. Rows without any value are left out, and every record has one value for every column."""
    names = next(rows(), [])
    while names and not names[-1]:
        names = names[:-1]
    width = len(names)

    def records():
        reader = rows()
        next(reader, None)
        for row in reader:
            if not any(row):
                continue
            if len(row) != width:
                row = (row + [""] * width)[:width] if len(row) < width else row[:width]
            yield row

    return names, records


def delimited_table(path: Path, profile: dict):
    encoding = profile.get("encoding") or "utf-8-sig"
    delimiter = "\t" if profile.get("delimiter") == "tab" else (profile.get("delimiter") or ",")
    first = max(number(profile.get("header_row")), 1)

    def rows():
        with open(path, encoding=encoding, errors="replace", newline="") as handle:
            for index, row in enumerate(csv.reader(handle, delimiter=delimiter), start=1):
                if index >= first:
                    yield [cell.strip() for cell in row]

    return header_and_records(rows)


def workbook_table(path: Path, profile: dict):
    first = max(number(profile.get("header_row")), 1)

    def old_rows():
        book = xlrd.open_workbook(str(path))
        sheet = book.sheet_by_name(profile["sheet"]) if profile.get("sheet") else book.sheet_by_index(0)
        for index in range(first - 1, sheet.nrows):
            row = []
            for cell in sheet.row(index):
                value = cell.value
                if cell.ctype == xlrd.XL_CELL_DATE:
                    try:
                        value = xlrd.xldate_as_datetime(cell.value, book.datemode)
                    except (ValueError, OverflowError):
                        pass
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    value = bool(value)
                elif cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK, xlrd.XL_CELL_ERROR):
                    value = None
                row.append(cell_text(value))
            yield row

    def new_rows():
        book = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        try:
            sheet = book[profile["sheet"]] if profile.get("sheet") else book.worksheets[0]
            for index, values in enumerate(sheet.iter_rows(values_only=True), start=1):
                if index >= first:
                    yield [cell_text(value) for value in values]
        finally:
            book.close()

    return header_and_records(old_rows if profile["kind"] == "xls" else new_rows)


def records_of(data) -> list:
    """The records of a JSON document, found as in 06_file_checks.py: the largest list of objects within three
    levels, or the document itself when it is a single object."""
    best: tuple[int, list] = (0, [])

    def visit(node, depth: int) -> None:
        nonlocal best
        if isinstance(node, list):
            if any(isinstance(item, dict) for item in node[:5000]) and len(node) > best[0]:
                best = (len(node), node)
            if depth < 3:
                for item in node[:50]:
                    visit(item, depth + 1)
        elif isinstance(node, dict) and depth < 3:
            for value in node.values():
                visit(value, depth + 1)

    visit(data, 0)
    if best[0] == 0 and isinstance(data, dict):
        return [data]
    return best[1]


def json_table(path: Path):
    """The names, the records and, for every name, the records whose value is a list or an object."""
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"))
    del raw
    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        objects = [dict(feature.get("properties") or {}) if isinstance(feature, dict) else {}
                   for feature in data.get("features") or []]
    else:
        objects = [item if isinstance(item, dict) else {} for item in records_of(data)]
    del data
    names = list(dict.fromkeys(str(key) for item in objects for key in item))
    nested = [sum(isinstance(item.get(name), (list, dict)) for item in objects) for name in names]

    def records():
        for item in objects:
            yield [cell_text(item.get(name)) for name in names]

    return names, records, nested


def shapefile_table(path: Path, profile: dict):
    """The attribute table of a shapefile; the geometries are not read."""
    encoding = profile.get("encoding") or "utf-8"
    with open(path, "rb") as handle, shapefile.Reader(dbf=handle, encoding=encoding,
                                                      encodingErrors="replace") as reader:
        names = [field[0] for field in reader.fields[1:]]

    def records():
        with open(path, "rb") as handle, shapefile.Reader(dbf=handle, encoding=encoding,
                                                          encodingErrors="replace") as reader:
            for values in reader.iterRecords():
                yield [cell_text(value) for value in values]

    return names, records


# ---------------------------------------------------------------------------
# Text of the cells
# ---------------------------------------------------------------------------

def lost_letters(value: str) -> bool:
    """Whether question marks stand in the place of the letters of a cell: four of them or more, as half of the
    cell or more. One to three question marks alone stand for a missing value (DECISIONS.md #39)."""
    marks = value.count("?")
    return marks >= LOST_LETTERS and marks * 2 >= len(value) - value.count(" ")


def sign_runs(value: str) -> list[str]:
    """The runs of signs of a text that count as characters of another encoding."""
    return [run for run in SIGN_RUN.findall(value) if len(set(run)) >= SIGN_KINDS]


def damage_of(value: str) -> str:
    """The kind of damage of a text with characters outside ASCII, or an empty text. Characters of another
    encoding are named with the form that they take."""
    if "\ufffd" in value:
        return REPLACED
    if OTHER_ENCODING.search(value):
        form = next(form for form, pattern in ENCODING_FORMS if pattern.search(value))
        return f"{ENCODING} ({form})"
    if sign_runs(value):
        return f"{ENCODING} (signs in a row)"
    if "?" in value and lost_letters(value):
        return MARKS
    return ""


class Text:
    """Counts of the cells of a table with text, with Greek letters and with damaged text."""

    def __init__(self) -> None:
        self.cells = self.greek = 0
        self.damaged: Counter = Counter()

    def add(self, value: str) -> None:
        if value.isascii():
            if "?" in value and lost_letters(value):
                self.cells += 1
                self.damaged[MARKS] += 1
            elif ASCII_LETTER.search(value):
                self.cells += 1
            return
        damage = damage_of(value)
        if not damage and LETTER.search(value) is None:
            return
        self.cells += 1
        if GREEK_LETTER.search(value):
            self.greek += 1
        if damage:
            self.damaged[damage] += 1

    def kinds(self) -> str:
        return ", ".join(f"{kind}: {count:,}" for kind, count in self.damaged.most_common())


# ---------------------------------------------------------------------------
# Columns and identifiers
# ---------------------------------------------------------------------------

class Column:
    """What the values of one column show: how many are filled, and whether all of them are whole numbers, whole
    numbers that count the rows, identifiers of features, numbers, moments, years, months, links or geometries."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.filled = self.shapes = 0
        self.whole = self.counting = self.features = self.numbers = True
        self.moments = self.years = self.months = self.links = True
        self.testing = True
        self.start = None

    def add(self, value: str, index: int) -> None:
        self.filled += 1
        if self.testing:
            if self.whole:
                if WHOLE_NUMBER.fullmatch(value) is None:
                    self.whole = self.counting = False
                elif self.counting:
                    count = int(value.split(".", 1)[0])
                    if self.start is None:
                        self.start = count
                        self.counting = index == 0 and count in (0, 1)
                    elif count != self.start + index:
                        self.counting = False
            if self.features and FEATURE_NUMBER.fullmatch(value) is None:
                self.features = False
            if self.numbers and NUMBER.fullmatch(value) is None:
                self.numbers = False
            if self.moments and (ISO_MOMENT.fullmatch(value) or DAY_FIRST_MOMENT.fullmatch(value)
                                 or COMPACT_MOMENT.fullmatch(value)) is None:
                self.moments = False
            if self.years and YEAR.fullmatch(value) is None:
                self.years = False
            if self.months and MONTH.fullmatch(value) is None:
                self.months = False
            if self.links and WEB_LINK.fullmatch(value) is None:
                self.links = False
            self.testing = (self.whole or self.features or self.numbers or self.moments or self.years
                            or self.months or self.links)
        if value[0] in WELL_KNOWN_START and WELL_KNOWN_TEXT.match(value):
            self.shapes += 1

    def kind(self, records: int, nested: int = 0) -> str:
        if not self.filled and not nested:
            return EMPTY_COLUMN
        if nested or self.shapes * 10 >= self.filled * 9:
            return SHAPE
        name = normalise(self.name)
        if (self.years and YEAR_NAME.search(name)) or (self.months and MONTH_NAME.search(name)):
            return PERIOD
        if (self.whole or self.features) and ROW_NUMBER_NAME.fullmatch(name):
            return ROW_NUMBER
        if self.counting and self.filled == records and records > 1:
            return ROW_NUMBER
        if identifier_name(self.name):
            return CODE
        if self.moments:
            return PERIOD
        if self.numbers:
            return MEASURE
        return LINK if self.links else TEXT


def repeats_of(records, indexes: list[int], first_only: bool = False) -> int:
    """The records whose values in the given columns were met in an earlier record, counted exactly without
    keeping the values of every record: a mark of the values of every record first, the values themselves only
    where a mark is met twice. With first_only the count stops at the first such record, which is enough to tell
    whether the columns are different in every record."""
    pick = itemgetter(*indexes)
    marks = array("Q")
    for row in records():
        marks.append(hash(pick(row)) & HASH_MASK)
    ordered = sorted(marks)
    del marks
    twice = {ordered[place] for place in range(1, len(ordered)) if ordered[place] == ordered[place - 1]}
    del ordered
    if not twice:
        return 0
    counts: Counter = Counter()
    for row in records():
        key = pick(row)
        if hash(key) & HASH_MASK in twice:
            counts[key] += 1
            if first_only and counts[key] > 1:
                return 1
    return sum(times - 1 for times in counts.values() if times > 1)


def find_identifier(records, count: int, kinds: list[str], filled: list[int], whole: list[bool]) -> dict:
    """The identifier of the records of a table: the first column of codes, links, periods or text that is filled
    and different in every record, otherwise the smallest combination of such columns that is. Without one, the
    column nearest to an identifier is named, with the records in which it repeats an earlier value, and so are
    the columns of whole numbers that are filled and different in every record."""
    found = {"columns": [], "source": "", "others": [], "numbers": [], "note": "", "searched": True,
             "nearest": None}
    candidates = sorted((index for index, kind in enumerate(kinds) if kind in PREFERENCE and filled[index] == count),
                        key=lambda index: (PREFERENCE[kinds[index]], index))
    found["candidates"] = len(candidates)
    if len(candidates) == 1 or count * len(candidates) > MEMORY_VALUES:
        # One pass over the file for every column or pair that is tried; nothing but marks is kept in memory.
        # The repeats of the first columns are counted in full, to name the column nearest to an identifier.
        for place, index in enumerate(candidates[:COMBINED_COLUMNS]):
            repeats = repeats_of(records, [index], first_only=place >= KEY_COLUMNS)
            if repeats == 0:
                found.update(columns=[index], source="single column", nearest=None)
                return found
            if place < KEY_COLUMNS and (found["nearest"] is None or repeats < found["nearest"][1]):
                found["nearest"] = (index, repeats)
        for pair in combinations(candidates[:KEY_COLUMNS], 2):
            if repeats_of(records, list(pair), first_only=True) == 0:
                found.update(columns=sorted(pair), source="combination of 2 columns", nearest=None)
                return found
        if len(candidates) > 2:
            found.update(searched=False, note=(f"more than {MEMORY_VALUES:,} values in the candidate columns: single "
                                               f"columns and pairs of the first {min(len(candidates), KEY_COLUMNS)} "
                                               "tried, none of them different in every record"))
    elif candidates:
        pick = itemgetter(*candidates)
        if len(candidates) > 1:
            rows = [pick(row) for row in records()]
        else:
            rows = [(pick(row),) for row in records()]
        different = [len({row[place] for row in rows}) for place in range(len(candidates))]
        single = [place for place, total in enumerate(different) if total == count]
        if single:
            found.update(columns=[candidates[single[0]]], source="single column",
                         others=[candidates[place] for place in single[1:]])
            return found
        pool = sorted(sorted(range(len(candidates)), key=lambda place: -different[place])[:COMBINED_COLUMNS])
        for size in range(2, KEY_COLUMNS + 1):
            for places in combinations(pool, size):
                possible = 1
                for place in places:
                    possible *= different[place]
                if possible < count:
                    continue
                seen: set = set()
                values = itemgetter(*places)
                for row in rows:
                    key = values(row)
                    if key in seen:
                        break
                    seen.add(key)
                else:
                    found.update(columns=sorted(candidates[place] for place in places),
                                 source=f"combination of {size} columns")
                    return found
        del rows
        nearest = max(range(len(candidates)), key=lambda place: (different[place], -place))
        found["nearest"] = (candidates[nearest], count - different[nearest])
        if len(candidates) > COMBINED_COLUMNS:
            found.update(searched=False, note=(f"combinations tried among the {COMBINED_COLUMNS} columns with the "
                                               f"most different values, of {len(candidates)} candidate columns"))
    numbers = [index for index, kind in enumerate(kinds) if kind == MEASURE and whole[index]
               and filled[index] == count]
    found["numbers"] = [index for index in numbers[:KEY_COLUMNS] if repeats_of(records, [index], first_only=True) == 0]
    return found


def key_of_reference(names: list[str], file_name: str) -> list[int] | None:
    """The columns of the primary key that the GTFS reference gives to a file, when the file has all of them."""
    key = GTFS_KEYS.get(file_name)
    if not key:
        return None
    if key == ("*",):
        return list(range(len(names)))
    return [names.index(name) for name in key] if all(name in names for name in key) else None


def examine_table(names: list[str], records, nested: list[int] | None, file_name: str = "") -> dict:
    """The text and the identifier of one table that can be split into records as it is."""
    columns = [Column(name) for name in names]
    text = Text()
    for name in names:
        if name:
            text.add(name)
    count = 0
    for index, row in enumerate(records()):
        count = index + 1
        for column, value in zip(columns, row):
            if value:
                column.add(value, index)
                text.add(value)
    kinds = [column.kind(count, nested[place] if nested else 0) for place, column in enumerate(columns)]
    filled = [column.filled for column in columns]
    result = {"records": count, "columns": len(names), "text": text, "kinds": kinds,
              "row_numbers": [place for place, kind in enumerate(kinds) if kind == ROW_NUMBER],
              "measures": kinds.count(MEASURE), "shapes": kinds.count(SHAPE), "repeats": "", "others": [],
              "numbers": [], "identifier": [], "source": "", "note": "", "candidates": 0, "searched": True,
              "nearest": None,
              "partly_filled": [place for place, kind in enumerate(kinds)
                                if kind in PREFERENCE and 0 < filled[place] < count]}
    if count <= 1:
        result["source"] = "one record" if count else "no record"
        return result
    key = key_of_reference(names, file_name)
    if key is not None:
        # The key of the standard identifies the records, whatever its values look like.
        repeats = repeats_of(records, key)
        result.update(candidates=len(key), row_numbers=[])
        if repeats == 0:
            result.update(identifier=key, source="key of the GTFS reference")
        else:
            result["note"] = (f"the key of the GTFS reference ({' + '.join(names[place] for place in key)}) is met "
                              f"again in {with_noun(repeats, 'record')}")
            result["repeats"] = repeats_of(records, list(range(len(names))))
        return result
    found = find_identifier(records, count, kinds, filled, [column.whole for column in columns])
    result.update(identifier=found["columns"], source=found["source"], others=found["others"],
                  numbers=found["numbers"], note=found["note"], candidates=found["candidates"],
                  searched=found["searched"], nearest=found["nearest"])
    if not found["columns"] and not (nested and any(nested)):
        kept = [place for place, kind in enumerate(kinds) if kind != ROW_NUMBER]
        if kept:
            result["repeats"] = repeats_of(records, kept)
    return result


def examine_rdf(path: Path) -> dict:
    """An RDF file: its records are its subjects, and the identifier of a record is its URI. A subject without a
    URI (a blank node) belongs to the record that points to it; one that nothing points to has no identifier."""
    graph = rdflib.Graph()
    failure = ""
    for rdf_format in ("turtle", "nt"):
        try:
            graph.parse(str(path), format=rdf_format)
            failure = ""
            break
        except Exception as error:      # rdflib raises parser-specific exceptions
            failure = type(error).__name__
            graph = rdflib.Graph()
    if failure:
        raise TableNotRead(f"the RDF file cannot be parsed ({failure})")
    subjects = set(graph.subjects())
    blank = {subject for subject in subjects if isinstance(subject, rdflib.BNode)}
    text = Text()
    pointed = set()
    properties = set()
    for _, predicate, value in graph:
        properties.add(predicate)
        if isinstance(value, rdflib.Literal):
            content = str(value).strip()
            if content:
                text.add(content)
        elif isinstance(value, rdflib.BNode):
            pointed.add(value)
    loose = len(blank - pointed)
    return {"records": len(subjects), "columns": len(properties), "text": text, "kinds": [], "row_numbers": [],
            "measures": 0, "shapes": 0, "repeats": "", "others": [], "numbers": [], "candidates": 0,
            "searched": True, "nearest": None, "partly_filled": [], "identifier": [] if loose else ["URI"],
            "source": "" if loose else "URI of the subject",
            "note": (f"{with_noun(len(subjects) - len(blank), 'subject')} with a URI"
                     + (f"; {with_noun(len(blank), 'blank node')}, {loose:,} of them not part of another record"
                        if blank else ""))}


# ---------------------------------------------------------------------------
# Tables of a dataset
# ---------------------------------------------------------------------------

def layout_of(profile: dict) -> tuple[str, str]:
    """The layout of a table, from the file profiles, and its defects."""
    reason = profile.get("ai1_reason", "")
    if profile.get("readable") != "True":
        return NOT_READ, reason
    score = number(profile.get("ai1_score"))
    if score == 2:
        return RECORDS, ""
    other = (any(number(profile.get(field)) for field in LAYOUT_DEFECTS) or number(profile.get("header_rows")) > 1
             or number(profile.get("tables")) > 1)
    if score == 1 and not other and number(profile.get("blank_rows_inside")):
        return RECORDS_AND_EMPTY_ROWS, reason
    return NOT_RECORDS, reason


def table_row(sample_id: str, profile: dict, resources: set[str], files: Extracted) -> dict:
    """The evidence on one examined table."""
    withheld = sample_id in PERSONAL_DATA_SUSPECTED
    layout, defects = layout_of(profile)
    inside = profile["position"] in resources
    row = {field: "" for field in TABLE_FIELDS}
    row.update(sample_id=sample_id, position=profile["position"], member=profile.get("member", ""),
               sheet=profile.get("sheet", ""), kind=profile["kind"], encoding=profile.get("encoding", ""),
               layout=layout, layout_defects=defects, records_in_profile=profile.get("rows", ""), read="no",
               resource_of_the_dataset="yes" if inside else "no")
    if layout == NOT_READ:
        row.update(outcome=BY_HAND, note="not read by 06_file_checks.py")
        return row
    if layout == NOT_RECORDS:
        row.update(outcome="1", note="needs cleaning before it can be split into records")
        return row
    if profile["kind"] not in TABLE_KINDS:
        row.update(note=f"not read: no list of columns for the format {profile['kind']}")
        return row
    nested = None
    try:
        if profile["kind"] == "rdf":
            result = examine_rdf(files.file_of(profile))
            names: list[str] = []
        else:
            if profile["kind"] in ("csv", "gtfs"):
                names, records = delimited_table(files.file_of(profile), profile)
            elif profile["kind"] in ("xls", "xlsx"):
                names, records = workbook_table(files.file_of(profile), profile)
            elif profile["kind"] == "shapefile":
                names, records = shapefile_table(files.file_of(profile, ".dbf"), profile)
            else:
                names, records, nested = json_table(files.file_of(profile))
            member = (profile.get("member") or "").rsplit("/", 1)[-1].lower()
            result = examine_table(names, records, nested, member if profile["kind"] == "gtfs" else "")
    except TableNotRead as error:
        row.update(outcome=BY_HAND, note=f"not read: {error}")
        return row
    except Exception as error:      # a file that cannot be read is recorded and judged by hand
        # Only the kind of the error is written: the message of a parser can quote the line that it rejects, and
        # the message of the operating system names the folder of the file.
        detail = type(error).__name__
        if isinstance(error, OSError) and error.strerror:
            detail += f" ({error.strerror})"
        row.update(outcome=BY_HAND, note=f"not read: {detail}")
        return row

    def label(place: int) -> str:
        return f"column {place + 1}" if withheld or not names[place] else names[place]

    text = result["text"]
    row.update(read="yes", records=result["records"], columns=result["columns"], text_cells=text.cells,
               greek_cells=text.greek, damaged_cells=sum(text.damaged.values()), damaged_kinds=text.kinds(),
               row_number_columns=", ".join(label(place) for place in result["row_numbers"]),
               measure_columns=result["measures"], geometry_columns=result["shapes"],
               candidate_columns=result["candidates"], identifier_source=result["source"],
               columns_with_empty_cells=listed([label(place) for place in result["partly_filled"]], separator=", "),
               other_unique_columns=listed([label(place) for place in result["others"]], separator=", "),
               unique_number_columns=listed([label(place) for place in result["numbers"]], separator=", "),
               repeating_records=result["repeats"], note=result["note"])
    if result["identifier"] == ["URI"]:
        row.update(identifier="URI of the subject", identifier_kind=LINK)
    elif result["identifier"]:
        kinds = [result["kinds"][place] for place in result["identifier"]]
        if result["source"].startswith("key"):
            kinds = [CODE]
        row.update(identifier=" + ".join(label(place) for place in result["identifier"]),
                   identifier_kind=", ".join(dict.fromkeys(kinds)))
    if result["nearest"] and not result["identifier"]:
        row.update(nearest_column=label(result["nearest"][0]), nearest_column_repeats=result["nearest"][1])
    problems = []
    if row["damaged_cells"]:
        problems.append(f"damaged text in {with_noun(row['damaged_cells'], 'cell')}")
    if result["records"] != number(profile.get("rows")):
        problems.append(f"{result['records']:,} records read, {number(profile.get('rows')):,} in the file profiles")
    if not result["identifier"] and result["records"] > 1:
        if result["numbers"]:
            problems.append("no identifier among the codes, the periods and the text, and "
                            + with_noun(len(result["numbers"]), "column")
                            + " of whole numbers different in every record ("
                            + row["unique_number_columns"] + "): an identifier or a measure")
        elif not result["searched"]:
            problems.append("the search for a combination of columns was not completed")
    if problems:
        row.update(outcome=BY_HAND, note="; ".join(filter(None, [row["note"]] + problems)))
    elif result["records"] == 0:
        row["note"] = "no record"
    elif result["identifier"] or result["records"] == 1:
        row["outcome"] = "2" if inside else "1"
    else:
        row["outcome"] = "1"
    return row


def judged(row: dict, how: str) -> str:
    """The outcome of a table as it counts for its dataset. A table without records does not count. A table whose
    format is not read does not count among several formats of the same data, and is judged by hand among the
    parts of a dataset."""
    if row["outcome"] or row["read"] == "yes" or how == "best":
        return row["outcome"]
    return BY_HAND


def combined(outcomes: list[str], how: str) -> str:
    """The outcome of several tables or resources: the worst one, or the best one of the same data in several
    formats. An empty text when none of them counts."""
    known = [outcome for outcome in outcomes if outcome]
    order = ("2", BY_HAND, "1") if how == "best" else ("1", BY_HAND, "2")
    return next((outcome for outcome in order if outcome in known), "")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def pdf_text(path: Path) -> dict:
    """The pages of a PDF document, those with text that can be extracted, and the letters of that text."""
    found = {"pages": 0, "with_text": 0, "letters": 0, "greek": 0, "damaged": 0, "error": ""}
    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt("")
        for page in reader.pages:
            found["pages"] += 1
            try:
                content = page.extract_text() or ""
            except Exception:      # a page that the library cannot read counts as a page without text
                content = ""
            letters = len(LETTER.findall(content))
            found["letters"] += letters
            found["greek"] += len(GREEK_LETTER.findall(content))
            found["damaged"] += content.count("\ufffd") + sum(len(run) for run in OTHER_ENCODING.findall(content))
            found["damaged"] += sum(len(run) for run in sign_runs(content))
            if letters >= PAGE_LETTERS:
                found["with_text"] += 1
    except Exception as error:      # pypdf raises its own exceptions on damaged or protected files
        found["error"] = type(error).__name__
    return found


def pdf_summary(position: str, found: dict) -> str:
    if found["error"]:
        return f"{position}: PDF not read ({found['error']})"
    share = f", {found['greek'] / found['letters']:.0%} of them Greek" if found["letters"] else ""
    marks = f", {with_noun(found['damaged'], 'damaged character')}" if found["damaged"] else ""
    return (f"{position}: PDF of {with_noun(found['pages'], 'page')}, text extracted from {found['with_text']:,}, "
            f"{with_noun(found['letters'], 'letter')}{share}{marks}")


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def identified(row: dict) -> bool:
    """Whether a table that was read has an identifier of its records, or a single record."""
    return bool(row["identifier"]) or row["identifier_source"] == "one record"


def tables_evidence(rows: list[dict]) -> dict:
    """The counts of the tables of a dataset for its row of evidence."""
    read = [row for row in rows if row["read"] == "yes"]
    found = [row for row in read if identified(row)]
    kinds: Counter = Counter(row["identifier_kind"] for row in read if row["identifier"])
    identifiers = list(dict.fromkeys(f"{row['identifier']} ({row['identifier_kind']})" if row["identifier_kind"]
                                     else row["identifier"] for row in read if row["identifier"]))
    damaged: Counter = Counter()
    for row in read:
        for part in filter(None, row["damaged_kinds"].split(", ")):
            kind, _, total = part.rpartition(": ")
            damaged[kind] += number(total.replace(",", ""))
    numbers = list(dict.fromkeys(name for row in read for name in filter(None, row["row_number_columns"].split(", "))))
    encodings: Counter = Counter(row["encoding"] for row in read if row["encoding"])
    return {
        "tables_examined": len(rows), "tables_read": len(read),
        "tables_not_records": sum(row["layout"] == NOT_RECORDS for row in rows),
        "tables_not_read": sum(row["read"] != "yes" and row["layout"] != NOT_RECORDS for row in rows),
        "records_read": sum(number(row["records"]) for row in read),
        "encodings": ", ".join(f"{encoding}: {with_noun(total, 'table')}"
                               for encoding, total in encodings.most_common()),
        "text_cells": sum(number(row["text_cells"]) for row in read),
        "greek_cells": sum(number(row["greek_cells"]) for row in read),
        "damaged_cells": sum(number(row["damaged_cells"]) for row in read),
        "damaged_kinds": ", ".join(f"{kind}: {total:,}" for kind, total in damaged.most_common()),
        "tables_with_identifier": len(found), "tables_without_identifier": len(read) - len(found),
        "identifiers": listed(identifiers),
        "identifier_kinds": ", ".join(f"{kind}: {with_noun(total, 'table')}" for kind, total in kinds.most_common()),
        "identifier_with_text": "yes" if any(TEXT in kind for kind in kinds) else ("no" if kinds else ""),
        "row_number_columns": listed(numbers, separator=", "),
        "repeating_records": sum(number(row["repeating_records"]) for row in read) or "",
        "tables_outside_resources": sum(row["resource_of_the_dataset"] == "no" for row in rows) or "",
    }


def reason_of(row: dict) -> str:
    """Why a table has the outcome it has, in words."""
    place = where_of(row)
    if row["layout"] == NOT_RECORDS:
        return f"{place}: {row['layout_defects'] or 'rows that are not records'}"
    if row["layout"] == NOT_READ:
        return f"{place}: {row['note']}" + (f" ({row['layout_defects']})" if row["layout_defects"] else "")
    if row["outcome"] == BY_HAND or row["read"] != "yes":
        return f"{place}: {row['note']}"
    if identified(row):
        if row["resource_of_the_dataset"] == "no":
            return f"{place}: not a resource of the dataset, no link to the source"
        return f"{place}: {row['identifier'] or 'one record'}"
    details = [row["note"] or f"no column or combination of up to {KEY_COLUMNS} columns is filled and different "
                              "in every record"]
    if row["nearest_column"]:
        details.append(f"the column nearest to an identifier, {row['nearest_column']}, repeats an earlier value in "
                       + with_noun(number(row["nearest_column_repeats"]), "record"))
    repeats = number(row["repeating_records"])
    if repeats:
        compared = ("every column other than those that number the rows" if row["row_number_columns"]
                    else "every column")
        details.append(f"1 record repeats an earlier one in {compared}" if repeats == 1
                       else f"{repeats:,} records repeat an earlier one in {compared}")
    if row["row_number_columns"]:
        details.append(f"the rows are only numbered ({row['row_number_columns']})")
    return f"{place}: " + "; ".join(details)


def propose_documents(missing: str, documents: list[dict]) -> tuple[str, str, str]:
    """The proposal for a dataset without tables: by the text of its PDF documents."""
    if not documents:
        if missing == "documents":
            return BY_HAND, ("the documents are not among the files obtained: they are judged in the review, 1 "
                             "when a document holds text that can be extracted, 0 when it is a scanned image"), ""
        return BY_HAND, "no table examined for the layout (AI1) and no document among the files obtained", ""
    first = documents[0]["position"]
    pages = sum(found["pages"] for found in documents)
    with_text = sum(found["with_text"] for found in documents)
    letters = sum(found["letters"] for found in documents)
    damaged = sum(found["damaged"] for found in documents)
    if any(found["error"] for found in documents) or not pages:
        return BY_HAND, "a PDF document could not be read", first
    if with_text == 0:
        return "0", (f"no page of the PDF gives text that can be extracted ({with_noun(pages, 'page')}, "
                     f"{with_noun(letters, 'letter')}): scanned images"), first
    if with_text * 2 < pages:
        return BY_HAND, f"text extracted from {with_text:,} of the {with_noun(pages, 'page')} only", first
    if damaged > letters * DAMAGED_SHARE:
        return BY_HAND, (f"the text extracted from the PDF has {with_noun(damaged, 'damaged character')} in "
                         f"{with_noun(letters, 'letter')}"), first
    return "1", (f"PDF with text that can be extracted ({with_text:,} of {with_noun(pages, 'page')}): usable after "
                 "the extraction of the text"), first


def propose(entry: dict, rows: list[dict], documents: list[dict]) -> tuple[str, str, str]:
    """The proposed score of a dataset, the reason and the table or the document that decides."""
    missing = entry.get("no_data_file", "").strip()
    if missing == "map images":
        return "0", "images of maps: no text that can be extracted", ""
    if missing == "unavailable":
        return "0", "no file of the dataset was obtained: no content that can be extracted", ""
    if missing == "documents" or not rows:
        return propose_documents(missing, documents)
    how = "best" if entry.get("combine") == "best" else "worst"
    by_resource: dict[str, list[dict]] = {}
    for row in rows:
        by_resource.setdefault(row["position"], []).append(row)
    resource_outcome = {position: combined([judged(row, how) for row in tables], "worst")
                        for position, tables in by_resource.items()}
    outcome = combined(list(resource_outcome.values()), how) or BY_HAND
    deciding = [position for position, value in resource_outcome.items() if (value or BY_HAND) == outcome]
    decisive = deciding[0] if deciding else ""
    several = len(by_resource) > 1
    if how == "best":
        chosen = by_resource.get(decisive, rows)
        scope = f"best of {len(by_resource)} formats, {decisive}: " if several else ""
    else:
        chosen = rows
        scope = f"worst of {len(by_resource)} files: " if several else ""
    if outcome == "2":
        tested = [row for row in chosen if row["outcome"] == "2"]
        names = list(dict.fromkeys(row["identifier"] or "one record" for row in tested))
        tables = "the examined table" if len(tested) == 1 else f"each of the {len(tested):,} examined tables"
        return "2", (f"{scope}records that can be split as they are, text without damaged characters and an "
                     f"identifier of every record in {tables} ({listed(names)}); the file is a resource of the "
                     "dataset"), decisive
    if outcome == "1":
        failing = [row for row in chosen if row["outcome"] == "1"]
        layout = [row for row in failing if row["layout"] == NOT_RECORDS]
        keyless = [row for row in failing if row["layout"] != NOT_RECORDS and not identified(row)]
        parts = []
        if layout:
            parts.append(f"rows that are not records in {len(layout):,} of {with_noun(len(chosen), 'table')}: "
                         + listed([reason_of(row) for row in layout], 2))
        if keyless:
            parts.append(f"no identifier of the records in {len(keyless):,} of {with_noun(len(chosen), 'table')}: "
                         + listed([reason_of(row) for row in keyless], 2))
        if any(row["resource_of_the_dataset"] == "no" for row in chosen):
            parts.append("the examined tables are not resources of the dataset: no link to the source")
        return "1", scope + "; ".join(parts), decisive
    unclear = [row for row in chosen if row["outcome"] == BY_HAND or (row["read"] != "yes" and not row["outcome"])]
    return BY_HAND, scope + listed([reason_of(row) for row in unclear] or ["no table could be judged"], 2), decisive


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], tables: list[dict], date: str, titles: dict[str, str]) -> None:
    proposals = Counter(row["ai5_proposal"] for row in checks)
    lines = [
        f"# Suitability of the datasets of the sample for retrieval (AI5), snapshot of {date}",
        "",
        "Produced by `scripts/11_retrieval_checks.py`. The tables collect the evidence for the review of the "
        "criterion; a score is proposed only where a rule decides without judgement, and the final scores are "
        "recorded in `DECISIONS.md`. Of the files only counts and names of columns are written: this report "
        "contains no value of a record.",
        "",
        "## Proposals",
        "",
        "Proposed AI5: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", BY_HAND)
                                     if proposals[score]) + ".",
        "",
        "| Dataset | Kind of data | Files | Proposal | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in checks:
        title = md_cell(titles.get(row["sample_id"], "")[:60])
        lines.append(f"| {row['sample_id']} {title} | {row['data_kind']} | {row['organisation']} | "
                     f"{row['ai5_proposal']} | {md_cell(row['ai5_reason'])} |")
    lines += ["", "## Layout and text of the examined tables", "",
              "A table is read when every row after its header is a record; the other tables need cleaning first. "
              "The cells with text include the names of the columns.",
              "",
              "| Dataset | Tables examined | Read | Rows that are not records | Not read | Records read | Encoding "
              "| Cells with text | With Greek letters | With damaged text | Kinds of damage |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |"]
    for row in checks:
        if row["tables_examined"]:
            lines.append(f"| {row['sample_id']} | {row['tables_examined']} | {row['tables_read']} | "
                         f"{row['tables_not_records']} | {row['tables_not_read']} | {row['records_read']:,} | "
                         f"{md_cell(row['encodings'])} | {row['text_cells']:,} | {row['greek_cells']:,} | "
                         f"{row['damaged_cells']:,} | {md_cell(row['damaged_kinds'])} |")
    lines += ["", "## Identifiers of the records", "",
              "| Dataset | Tables with an identifier | Without | Identifiers | Kinds of their columns | With a column "
              "of text | Columns that number the rows | Records that repeat an earlier one, the numbers of the rows "
              "left out | Link to the source |",
              "| --- | ---: | ---: | --- | --- | --- | --- | ---: | --- |"]
    for row in checks:
        if row["tables_read"]:
            lines.append(f"| {row['sample_id']} | {row['tables_with_identifier']} | "
                         f"{row['tables_without_identifier']} | {md_cell(row['identifiers'])} | "
                         f"{md_cell(row['identifier_kinds'])} | {row['identifier_with_text']} | "
                         f"{md_cell(row['row_number_columns'])} | {row['repeating_records']} | "
                         f"{md_cell(row['link_to_source'])} |")
    lines += ["", "## Tables that are not read, have no identifier or have damaged text", "",
              "| Dataset | Table | Format | Layout | Records | Damaged cells | Outcome | Note |",
              "| --- | --- | --- | --- | ---: | ---: | --- | --- |"]
    shown = [row for row in tables if row["outcome"] != "2"]
    for row in shown:
        lines.append(f"| {row['sample_id']} | {md_cell(where_of(row))} | {row['kind']} | {row['layout']} | "
                     f"{row['records'] or row['records_in_profile']} | {row['damaged_cells']} | "
                     f"{row['outcome'] or 'not judged'} | {md_cell(reason_of(row).split(': ', 1)[-1])} |")
    if not shown:
        lines.append("| - | none | | | | | | |")
    lines += ["", "## Documents", "",
              "| Dataset | PDF documents among the files obtained |",
              "| --- | --- |"]
    documents = [row for row in checks if row["documents"]]
    for row in documents:
        lines.append(f"| {row['sample_id']} | {md_cell(row['documents'])} |")
    if not documents:
        lines.append("| - | none |")
    lines += ["", f"Every examined table is listed in `data/processed/retrieval_tables_{date}.csv` "
                  f"({with_noun(len(tables), 'row')})."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argparse.ArgumentParser(description="Evidence on the suitability of the datasets of the sample for retrieval "
                                        "(criterion AI5).").parse_args()
    csv.field_size_limit(2 ** 31 - 1)
    logging.getLogger("pypdf").setLevel(logging.ERROR)      # remarks of the library on the structure of a PDF file

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    inputs = {name: PROCESSED_DIR / f"{name}_{date}.csv" for name in ("resource_downloads", "file_profiles")}
    for name, needed in inputs.items():
        if not needed.exists():
            script = "05_resource_download.py" if name == "resource_downloads" else "06_file_checks.py"
            raise SystemExit(f"{relative(needed)} not found. Run {script} first.")
    log, profiles = (read_csv(inputs[name]) for name in inputs)
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    checks_file = PROCESSED_DIR / f"retrieval_checks_{date}.csv"
    tables_file = PROCESSED_DIR / f"retrieval_tables_{date}.csv"
    report_file = OUT_DIR / f"retrieval_{date}" / "retrieval_checks.md"

    print(f"Snapshot: {relative(snapshot)}")
    print(f"Text of the PDF documents: pypdf {pypdf.__version__}")
    print(f"Datasets of the sample: {len(sample)}")

    checks, tables = [], []
    for sample_id in sorted(sample):
        entry = organisation.get(sample_id, {})
        own_log = [row for row in log if row["sample_id"] == sample_id]
        resources = {position_label(row["position"]) for row in own_log if row.get("outcome") == "available"}
        examined = [row for row in profiles if row["sample_id"] == sample_id and row.get("data_file") == "True"
                    and row.get("examined") == "True" and row.get("hidden") != "True"]
        large = sum(number(row.get("rows")) for row in examined
                    if layout_of(row)[0] in (RECORDS, RECORDS_AND_EMPTY_ROWS))
        if large > ANNOUNCED_RECORDS or any(row["kind"] == "rdf" for row in examined):
            print(f"{sample_id}: reading {with_noun(len(examined), 'table')} with {with_noun(large, 'record')}",
                  flush=True)
        files = Extracted()
        rows = []
        try:
            for profile in examined:
                rows.append(table_row(sample_id, profile, resources, files))
                if number(rows[-1]["records"]) > ANNOUNCED_RECORDS:
                    print(f"  {where_of(rows[-1])}: {number(rows[-1]['records']):,} records read", flush=True)
        finally:
            files.close()
        documents = []
        for row in own_log:
            if row.get("outcome") == "available" and row.get("detected_type") == "pdf" and row.get("file"):
                documents.append({"position": position_label(row["position"]), **pdf_text(ROOT / row["file"])})
        proposal, reason, decisive = propose(entry, rows, documents)
        missing = entry.get("no_data_file", "").strip()
        outside = any(row["resource_of_the_dataset"] == "no" for row in rows)
        kind = missing or ("data files" if rows and not outside else "no data file among the resources obtained")
        link = ""
        if rows:
            link = ("none: the examined tables are not resources of the dataset" if outside
                    else "permanent address of the resource on the portal (DECISIONS.md #33)")
        checks.append({"sample_id": sample_id, "dataset": sample[sample_id].get("name", ""),
                       "group": sample[sample_id].get("group", ""), "category": sample[sample_id].get("category", ""),
                       "data_kind": kind, "organisation": entry.get("organisation", ""),
                       "combine": entry.get("combine", ""), **tables_evidence(rows), "link_to_source": link,
                       "documents": "; ".join(pdf_summary(found["position"], found) for found in documents),
                       "decisive": decisive, "ai5_proposal": proposal, "ai5_reason": reason})
        tables += rows
        print(f"{sample_id} AI5 {proposal}: {reason[:150]}", flush=True)

    write_csv(checks_file, CHECK_FIELDS, checks)
    write_csv(tables_file, TABLE_FIELDS, tables)
    write_report(report_file, checks, tables, date, titles)

    proposals = Counter(check["ai5_proposal"] for check in checks)
    print("Proposed AI5: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", BY_HAND)
                                       if proposals[score]))
    read = [row for row in tables if row["read"] == "yes"]
    print(f"Tables examined: {len(tables):,}; read: {len(read):,}; with rows that are not records: "
          f"{sum(row['layout'] == NOT_RECORDS for row in tables):,}; records read: "
          f"{sum(number(row['records']) for row in read):,}; cells with damaged text: "
          f"{sum(number(row['damaged_cells']) for row in read):,}")
    unread = [row for row in tables if row["read"] != "yes" and row["layout"] != NOT_RECORDS]
    for row in unread[:10]:
        print(f"  not read: {row['sample_id']} {where_of(row)}: {row['note'][:120]}")
    if len(unread) > 10:
        print(f"  and {len(unread) - 10} more")
    print("Files:")
    for path in (checks_file, tables_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
