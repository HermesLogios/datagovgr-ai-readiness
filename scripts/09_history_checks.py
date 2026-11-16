r"""
09_history_checks.py
Phase 3, step 3: evidence on the historical depth of the datasets of the sample (criterion AI3: are earlier periods
or versions of the data available).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one), the sample
     (data/processed/sample.csv), the organisation of the files (criteria/file_organisation.csv) and the tables of
     05_resource_download.py and 06_file_checks.py (download log, file profiles, structures, plausibility).
  2. Collects, for every dataset of the sample, what its metadata say about time: the frequency, the temporal
     coverage (marked when it carries the placeholder 1900 or 2099), the version, the dates among the additional
     metadata, and the resources whose file was replaced after the resource was created.
  3. Reads the period that the name of every resource carries (a date, a range of dates, a month, a year, a range
     of years; for a workbook without one, the periods in the names of its sheets). Where the resources of a
     dataset carry different periods it describes the series: the periods from the first to the last, those that
     are missing, the files that were not obtained, the files identical to the file of another period, and whether
     the files have the same columns (structures of 06_file_checks.py).
  4. Reads the downloaded tables (delimited text and workbooks, on disk or inside a ZIP archive) and looks for the
     periods inside them: a column of dates or time stamps, a column of years with or without a column of months,
     or a column of labels of two consecutive years (1960-61). For every table with such a column it lists the
     periods present and those missing between the first and the last. A record counts for its period when it
     holds at least one value besides the period; rows that hold only their period, and records whose period
     cannot be read, are counted apart. Dates make a daily series when at least half of the days between the
     first and the last are present, a monthly one when at least half of the months are, otherwise a yearly one.
     Period names in the header of a table (one column per month or per year) are read from the file profiles. A
     table counts as laid out by period when nine in ten of its periods, the first and the last left out, hold
     between half and twice the usual number of records; a date that is one of the attributes of the records of
     a register does not pass. Only periods are kept: no record is written.
  5. Looks in the whole catalogue for the other periods of a dataset that carries one period: the datasets of the
     same publisher with the same title once the period is taken out, and those whose title begins with the same
     two words.
  6. Proposes a score only where a rule decides without judgement (a series across the resources, a series inside
     files laid out by period, no file obtained); every other dataset is marked "by hand" and is judged in the
     review.
  7. Writes:
        data/processed/history_checks_YYYY-MM-DD.csv      one row per dataset of the sample: the evidence and the
                                                           proposal
        data/processed/history_series_YYYY-MM-DD.csv      one row per series found: across the resources, inside
                                                           a table, in the header of a table, in the catalogue
        data/processed/history_siblings_YYYY-MM-DD.csv    one row per dataset of the catalogue that may hold
                                                           another period of a dataset of the sample
        outputs/history_YYYY-MM-DD/history_checks.md      the same as a report
     The date in the names is the date of the snapshot. None of the files contains records of the data.

Rules of AI3 (card approved on 11 November 2026; recorded in DECISIONS.md #47):
  - Earlier periods or versions count wherever they are: inside the file, in separate files of the same dataset,
    or on a page of the publisher that the metadata link to. The temporal coverage of the metadata is only an
    indication.
  - Score 2: every period from the first to the last is there, with the same columns. Score 1: periods are missing
    in between, or the columns change from period to period. Score 0: only the present state. A series has at
    least three periods or versions: two alone score 1. The length of a series does not change the score.
  - A gap is a whole period missing between the first and the last. That a series has stopped is a matter of Q5,
    and a few missing readings of a sensor are a matter of Q2.
  - The same structure is the result of the comparison of the columns made for Q3 (DECISIONS.md #40).
  - Registers, lists and timetables show the present state: their past is their earlier versions, and a dataset
    whose every update replaces the previous file scores 0.
  - A dataset that holds a single period, while the other periods are published as separate datasets of the same
    publisher, scores 1; 0 when no other period is found.
  - n/a when the data have by nature no before and after: the image of a map of one act, a product with fixed
    reference years, the document of one act. A product with fixed reference years that is one period of a product
    that recurs, the other periods being separate datasets of the publisher, falls under the previous rule.
  - Datasets whose files could not be obtained are judged on the list of their resources and on their metadata
    alone, and cannot exceed 1.

Usage (from the project root, with the .venv activated):
    python scripts\09_history_checks.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import html
import io
import json
import re
import statistics
import sys
import unicodedata
import zipfile
from collections import Counter
from itertools import islice
from pathlib import Path

import openpyxl
import xlrd
from openpyxl.utils.exceptions import InvalidFileException

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
MINIMUM_SERIES = 3               # periods or versions that make a series; two alone score 1
SHARE_OF_PERIODS = 0.9           # share of the values of a column that must be read as periods
DENSE_SERIES = 0.5               # share of the days (or months) between the first and the last that must be
                                 # present for a series of dates to count as daily (or monthly)
EVEN_PERIODS = 0.9               # share of the periods of a table that must hold about the usual number of
                                 # records (between half and twice the median) for the table to count as laid
                                 # out by period
HEAD_RECORDS = 200               # records read to find the period columns of a table
LISTED = 6                       # periods, resources or tables listed in a cell before "and N more"

# Datasets whose column names are written nowhere (DECISIONS.md #29 and #43).
PERSONAL_DATA_SUSPECTED = {"S24", "S29"}

# Kinds of files of the file profiles whose tables are read for the periods inside them.
DELIMITED_KINDS = {"csv"}
WORKBOOK_KINDS = {"xls", "xlsx"}

# Temporal coverage that the portal carries where no real date was given.
PLACEHOLDER_START, PLACEHOLDER_END = "1900-01-01", "2099-12-31"

# Entries of the additional metadata (extras) that carry a date of the dataset.
DATE_ENTRIES = ("issued", "modified", "last_update", "source_metadata_created", "source_metadata_modified")

# Units of a period read from a name, a title or a table.
DAY, DAYS, MONTH, YEAR, YEARS, LABEL, EDITION = ("day", "range of days", "month", "year", "range of years",
                                                 "year label", "dated edition")

# Roles of the time columns recorded by 06_file_checks.py that describe when the data were observed. The dates of
# a timetable (role "schedule date") give the validity of the timetable and are reported separately.
OBSERVATION_ROLES = {"dates", "year", "time stamp"}
SCHEDULE_ROLE = "schedule date"

YEAR_WORDS = {"ετος", "ετη", "χρονια", "year", "years"}
MONTH_WORDS = {"μηνας", "μην", "month"}
GREEK_MONTHS = ("ιανουαρι", "φεβρουαρι", "μαρτι", "απριλι", "μαι", "ιουνι", "ιουλι", "αυγουστ", "σεπτεμβρι",
                "οκτωβρι", "νοεμβρι", "δεκεμβρι")
ENGLISH_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september",
                  "october", "november", "december")

# Proper names that carry a year which is not a period of the data.
PROPER_NAMES = re.compile(r"natura\s*2000|horizon\s*2020|οριζοντας\s*2020|ευρωπη\s*2020|europe\s*2020")

# Periods as they are written in titles and names, on a text in lower case and without accents. A number that
# follows a digit and a separator (4887/2022) is the number of an act, not a period.
RANGE_WORD = r"(?:\s*[-–]\s*|\s+(?:εως|ως|μεχρι|to|until)\s+)"
DAY_RANGE = re.compile(r"(?<![\d/.-])(\d{1,2})([/.-])(\d{1,2})\2(\d{4})" + RANGE_WORD
                       + r"(\d{1,2})([/.-])(\d{1,2})\6(\d{4})(?![\d/.-])")
SINGLE_DAY = re.compile(r"(?<![\d/.-])(\d{1,2})([/.-])(\d{1,2})\2(\d{4})(?![\d/.-])")
ISO_DAY = re.compile(r"(?<![\d-])(\d{4})-(\d{2})-(\d{2})(?![\d-])")
SHORT_DAY = re.compile(r"(?<![\d/.-])(\d{1,2})([/-])(\d{1,2})\2(\d{2})(?![\d/.-])")
NAMED_MONTH = re.compile(r"(?<![^\W\d_])(?:(" + "|".join(GREEK_MONTHS) + r")[^\W\d_]{0,3}|("
                         + "|".join(ENGLISH_MONTHS) + r"))\s+((?:19|20)\d\d)(?!\d)")
NUMBERED_MONTH = re.compile(r"(?<![\d/.-])(\d{1,2})/((?:19|20)\d\d)(?!\w)(?![/.-]\d)")
YEAR_RANGE = re.compile(r"(?<!\w)(?<!\d[/.-])((?:19|20)\d\d)(?:\s*[-–_/]\s*|\s+(?:εως|ως|μεχρι|to|until)\s+)"
                        r"((?:19|20)\d\d|\d\d)(?!\w)(?![/.-]\d)")
SINGLE_YEAR = re.compile(r"(?<!\w)(?<!\d[/.-])((?:19|20)\d\d)(?!\w)(?![/.-]\d)")

# Dates and time stamps as they are written in the cells of a table.
ISO_MOMENT = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?)?"
                        r"(?:Z|[+-]\d{2}:?\d{2})?")
DAY_FIRST_MOMENT = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?")
COMPACT_MOMENT = re.compile(r"(\d{4})(\d{2})(\d{2})(?:(\d{2})(\d{2})(\d{2})?)?")
TWO_YEAR_LABEL = re.compile(r"((?:18|19|20)\d\d)\s*[-–/]\s*(\d{4}|\d{2})")
MONTH_AS_COLUMN_NAME = re.compile(r"((?:18|19|20)\d\d)[-/](\d{2})")

CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "organisation", "frequency", "temporal_coverage", "version",
    "dates_in_additional_metadata", "resources", "resources_replaced", "period_in_title", "resources_with_period",
    "resource_series", "resource_periods", "resource_period_first", "resource_period_last",
    "resource_periods_missing", "resources_not_obtained", "resource_files_repeated", "structure_across_files",
    "tables_read", "tables_not_read", "tables_with_periods", "file_series", "file_periods", "file_period_first",
    "file_period_last", "file_tables_with_missing_periods", "file_periods_missing", "file_records_per_period",
    "file_tables_not_by_period", "file_rows_without_values", "file_periods_not_read", "time_columns_recorded",
    "timetable_validity", "same_title_datasets", "same_title_periods", "same_title_periods_missing",
    "similar_title_datasets", "ai3_proposal", "ai3_reason",
]
SERIES_FIELDS = [
    "sample_id", "source", "where", "column", "unit", "periods", "first", "last", "expected", "missing",
    "missing_periods", "records", "records_per_period", "rows_without_values", "periods_not_read", "notes",
]
SIBLING_FIELDS = ["sample_id", "level", "dataset", "title", "period", "resources"]


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


def own_resources(dataset: dict) -> list[dict]:
    """The resources of a dataset, without the automatic bundle of the portal."""
    return [resource for resource in dataset.get("resources") or []
            if isinstance(resource, dict) and not is_bundle(resource)]


def plain_text(value) -> str:
    """A text without HTML tags, character entities and repeated spaces."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))).strip()


def unaccented(value) -> str:
    """A text in lower case and without accents, with its punctuation kept."""
    text = unicodedata.normalize("NFD", plain_text(value).lower())
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def words_of(value) -> list[str]:
    """The words of a text in lower case and without accents: its runs of letters and digits."""
    return [word for word in re.split(r"[\W_]+", unaccented(value)) if word]


def number(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def with_noun(count: int, noun: str) -> str:
    """A number with its noun, in the singular or in the plural."""
    return f"{count:,} {noun}{'' if count == 1 else 's'}"


def listed(items: list[str], limit: int = LISTED) -> str:
    """The first items of a list and the number of those left out."""
    shown = ", ".join(items[:limit])
    return shown + (f", and {len(items) - limit} more" if len(items) > limit else "")


def position_of(row: dict) -> str:
    """The position of a resource as written in every table of the project: r001, r002 and so on."""
    value = str(row.get("position") or "")
    return value if value.startswith("r") else f"r{number(value):03d}"


# ---------------------------------------------------------------------------
# Periods in titles and names
# ---------------------------------------------------------------------------

def day_of(year, month, day) -> dt.date | None:
    """A date from its three numbers, or nothing when they are not a date. A year of two digits belongs to the
    twentieth century from 70 on and to the twenty-first before that."""
    year = int(year)
    if year < 100:
        year += 1900 if year >= 70 else 2000
    try:
        return dt.date(year, int(month), int(day)) if 1800 <= year <= 2199 else None
    except ValueError:
        return None


def month_end(year: int, month: int) -> dt.date:
    return (dt.date(year + (month == 12), month % 12 + 1, 1)) - dt.timedelta(days=1)


def find_period(value) -> tuple[tuple, int, int] | None:
    """The first period that a title or a name carries, as (unit, first day, last day), with the place of its text
    in the lower-case text without accents. The more precise form wins: a range of days, a day, a month, a range
    of years, a year."""
    text = PROPER_NAMES.sub(lambda match: " " * len(match.group(0)), unaccented(value))
    found = DAY_RANGE.search(text)
    if found:
        first = day_of(found.group(4), found.group(3), found.group(1))
        last = day_of(found.group(8), found.group(7), found.group(5))
        if first and last and first <= last:
            return (DAYS, first, last), found.start(), found.end()
    for pattern, order in ((SINGLE_DAY, (4, 3, 1)), (ISO_DAY, (1, 2, 3)), (SHORT_DAY, (4, 3, 1))):
        for found in pattern.finditer(text):
            day = day_of(*(found.group(index) for index in order))
            if day:
                return (DAY, day, day), found.start(), found.end()
    found = NAMED_MONTH.search(text)
    if found:
        month = (GREEK_MONTHS.index(found.group(1)) if found.group(1) else ENGLISH_MONTHS.index(found.group(2))) + 1
        year = int(found.group(3))
        return (MONTH, dt.date(year, month, 1), month_end(year, month)), found.start(), found.end()
    for found in NUMBERED_MONTH.finditer(text):
        month, year = int(found.group(1)), int(found.group(2))
        if 1 <= month <= 12:
            return (MONTH, dt.date(year, month, 1), month_end(year, month)), found.start(), found.end()
    for found in YEAR_RANGE.finditer(text):
        first, second = int(found.group(1)), found.group(2)
        last = int(second) if len(second) == 4 else (first + 1 if int(second) == (first + 1) % 100 else 0)
        if first < last <= first + 150:
            return (YEARS, dt.date(first, 1, 1), dt.date(last, 12, 31)), found.start(), found.end()
    found = SINGLE_YEAR.search(text)
    if found:
        year = int(found.group(1))
        return (YEAR, dt.date(year, 1, 1), dt.date(year, 12, 31)), found.start(), found.end()
    return None


def period_of(value) -> tuple | None:
    found = find_period(value)
    return found[0] if found else None


def period_text(period: tuple | None) -> str:
    if not period:
        return ""
    unit, first, last = period
    if unit == DAY:
        return first.isoformat()
    if unit == DAYS:
        return f"{first.isoformat()} to {last.isoformat()}"
    if unit == MONTH:
        return f"{first.year}-{first.month:02d}"
    if unit == YEAR:
        return str(first.year)
    return f"{first.year}-{last.year}"


def single_period(period: tuple | None) -> bool:
    """Whether a period is one unit of time: a day, a month, a year, or two consecutive years (a school year)."""
    if not period:
        return False
    unit, first, last = period
    return unit in (DAY, MONTH, YEAR) or (unit == YEARS and last.year - first.year == 1)


def stem_of(value) -> str:
    """A title without its period, as words in lower case without accents: what the datasets of one series have
    in common."""
    found = find_period(value)
    text = unaccented(value)
    if found:
        text = text[:found[1]] + " " + text[found[2]:]
    return " ".join(words_of(text))


# ---------------------------------------------------------------------------
# Series of periods
# ---------------------------------------------------------------------------

def ordinal(unit: str, period: tuple) -> int | None:
    """The place of a period on the line of its unit, so that the missing ones can be counted. Ranges of days and
    ranges of more than two years have no regular step."""
    _, first, last = period
    if unit == DAY:
        return first.toordinal()
    if unit == MONTH:
        return first.year * 12 + first.month - 1
    if unit == YEAR or (unit == YEARS and last.year - first.year == 1):
        return first.year
    return None


def ordinal_text(unit: str, value: int) -> str:
    if unit == DAY:
        return dt.date.fromordinal(value).isoformat()
    if unit == MONTH:
        return f"{value // 12}-{value % 12 + 1:02d}"
    if unit == YEARS:
        return f"{value}-{value + 1}"
    if unit == LABEL:
        return f"{value}-{(value + 1) % 100:02d}"
    return str(value)


def missing_runs(present: set[int]) -> list[tuple[int, int]]:
    """The runs of missing places between the first and the last place present."""
    runs, ordered = [], sorted(present)
    for before, after in zip(ordered, ordered[1:]):
        if after - before > 1:
            runs.append((before + 1, after - 1))
    return runs


def runs_text(unit: str, runs: list[tuple[int, int]]) -> str:
    texts = [ordinal_text(unit, first) if first == last
             else f"{ordinal_text(unit, first)} to {ordinal_text(unit, last)} ({last - first + 1})"
             for first, last in runs]
    return listed(texts) if texts else "none"


def regular_series(unit: str, present: set[int]) -> dict:
    """The description of a series with a regular step: its periods, the first, the last and the missing ones."""
    runs = missing_runs(present)
    missing = sum(last - first + 1 for first, last in runs)
    return {"unit": unit, "periods": len(present), "first": ordinal_text(unit, min(present)),
            "last": ordinal_text(unit, max(present)), "expected": len(present) + missing, "missing": missing,
            "missing_periods": runs_text(unit, runs)}


def covered(unit: str, periods: list[tuple]) -> set[int]:
    """The days (for ranges of days) or the years (for ranges of years) that a list of ranges covers."""
    if unit == DAYS:
        return {value for _, first, last in periods for value in range(first.toordinal(), last.toordinal() + 1)}
    return {value for _, first, last in periods for value in range(first.year, last.year + 1)}


def series_of_periods(unit: str, distinct: list[tuple], kept: list[tuple] | None = None) -> dict:
    """The series that a list of different periods makes. Days, months, years and pairs of consecutive years have a
    regular step: the missing ones are those between the first and the last. Ranges are judged by what they cover
    of the time between the first and the last (kept: the ranges whose file was obtained). Dates too far apart to
    be a daily series are dated editions, without a regular step."""
    places = {period: ordinal(unit, period) for period in distinct}
    if all(place is not None for place in places.values()):
        dense = unit != DAY or len(distinct) >= DENSE_SERIES * (max(places.values()) - min(places.values()) + 1)
        if dense:
            return regular_series(unit, set(places.values()))
        return {"unit": EDITION, "periods": len(distinct), "first": period_text(distinct[0]),
                "last": period_text(distinct[-1]), "expected": "", "missing": "",
                "missing_periods": "no regular step"}
    small = DAY if unit == DAYS else YEAR
    span = covered(unit, [(unit, min(period[1] for period in distinct), max(period[2] for period in distinct))])
    left = sorted(span - covered(unit, distinct if kept is None else kept))
    runs: list[list[int]] = []
    for value in left:
        if runs and value == runs[-1][1] + 1:
            runs[-1][1] = value
        else:
            runs.append([value, value])
    return {"unit": unit, "periods": len(distinct), "first": ordinal_text(small, min(span)),
            "last": ordinal_text(small, max(span)), "expected": len(span), "missing": len(left),
            "missing_periods": runs_text(small, [(first, last) for first, last in runs])}


def series_of_days(days: set[dt.date]) -> dict:
    """A set of dates as a series: daily or monthly when most of the days or of the months between the first and
    the last are present, otherwise by year."""
    ordinals = {day.toordinal() for day in days}
    months = {day.year * 12 + day.month - 1 for day in days}
    if len(ordinals) >= DENSE_SERIES * (max(ordinals) - min(ordinals) + 1):
        return regular_series(DAY, ordinals)
    if len(months) >= DENSE_SERIES * (max(months) - min(months) + 1):
        return regular_series(MONTH, months)
    return regular_series(YEAR, {day.year for day in days})


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def read_catalogue(snapshot: Path, sample: dict[str, dict]) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """The records of the datasets of the sample, by sample id, and the titles and resource names of every dataset
    of the catalogue, by publisher."""
    by_id = {row["id"]: row["sample_id"] for row in sample.values()}
    found: dict[str, dict] = {}
    publishers: dict[str, list[dict]] = {}
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("id") in by_id:
                found[by_id[record["id"]]] = record
            if record.get("type") != "dataset":
                continue
            organisation = record.get("organization") if isinstance(record.get("organization"), dict) else {}
            publishers.setdefault(str(organisation.get("name") or ""), []).append({
                "id": record.get("id"), "name": record.get("name", ""), "title": plain_text(record.get("title")),
                "resources": [plain_text(resource.get("name")) for resource in own_resources(record)]})
    return found, publishers


# ---------------------------------------------------------------------------
# Evidence of the metadata
# ---------------------------------------------------------------------------

def metadata_evidence(dataset: dict) -> dict:
    """What the metadata of a dataset say about time."""
    coverage = []
    for item in dataset.get("temporal_coverage") or []:
        if not isinstance(item, dict):
            continue
        start, end = str(item.get("start") or "")[:10], str(item.get("end") or "")[:10]
        marks = [side for side, value, default in (("start", start, PLACEHOLDER_START), ("end", end, PLACEHOLDER_END))
                 if value == default]
        note = {2: " (placeholder)", 1: f" (the {marks[0]} is a placeholder)" if marks else ""}.get(len(marks), "")
        coverage.append(f"{start or 'open'} to {end or 'open'}{note}")
    extras = {str(item.get("key")): str(item.get("value") or "").strip() for item in dataset.get("extras") or []
              if isinstance(item, dict)}
    dates = [f"{key} {extras[key][:10]}" for key in DATE_ENTRIES if extras.get(key)]
    resources = own_resources(dataset)
    created_on = str(dataset.get("metadata_created") or "")
    replaced = []
    for resource in resources:
        created, modified = str(resource.get("created") or ""), str(resource.get("last_modified") or "")
        if not created or not modified or modified[:10] <= created[:10]:
            continue
        copied = created < created_on and abs(seconds_between(modified, created_on)) < 86400
        if not copied:
            replaced.append(modified[:10])
    replaced_text = ""
    if replaced:
        days = sorted(set(replaced))
        replaced_text = (f"{len(replaced)} of {len(resources)}: last upload on "
                         + (days[0] if len(days) == 1 else f"{days[0]} to {days[-1]}"))
    return {
        "frequency": str(dataset.get("frequency") or "").rstrip("/").rsplit("/", 1)[-1],
        "temporal_coverage": "; ".join(coverage),
        "version": str(dataset.get("version") or "").strip(),
        "dates_in_additional_metadata": "; ".join(dates),
        "resources": len(resources),
        "resources_replaced": replaced_text,
        "period_in_title": period_text(period_of(dataset.get("title"))),
    }


def seconds_between(later: str, earlier: str) -> float:
    """The seconds between two time stamps of the catalogue; a large number when one of them cannot be read."""
    try:
        return (dt.datetime.fromisoformat(later[:19]) - dt.datetime.fromisoformat(earlier[:19])).total_seconds()
    except ValueError:
        return 10 ** 12


# ---------------------------------------------------------------------------
# Series across the resources
# ---------------------------------------------------------------------------

def resource_series(dataset: dict, log: list[dict], profiles: list[dict]) -> tuple[dict, dict | None]:
    """The periods that the resources of a dataset carry in their names (or, for a workbook without one, in the
    names of its sheets): the evidence for the row of the dataset and, when the periods differ, the series."""
    by_id = {row["resource_id"]: row for row in log}
    sheets: dict[str, list[tuple]] = {}
    for profile in profiles:
        period = period_of(profile.get("sheet"))
        if period and period not in sheets.setdefault(profile["position"], []):
            sheets[profile["position"]].append(period)
    carried = []                     # (position, period, obtained, sha256), one entry per period of a resource
    for resource in own_resources(dataset):
        row = by_id.get(str(resource.get("id") or ""), {})
        position = position_of(row) if row else ""
        named = period_of(resource.get("name"))
        for period in [named] if named else sheets.get(position, []):
            carried.append((position, period, row.get("outcome") == "available", row.get("sha256", "")))
    evidence = {"resources_with_period": len({position for position, *_ in carried}), "resource_series": "",
                "resource_periods": "", "resource_period_first": "", "resource_period_last": "",
                "resource_periods_missing": "", "resources_not_obtained": "", "resource_files_repeated": "",
                "single_resource_period": None}
    if not carried:
        return evidence, None
    unit = Counter(period[0] for _, period, *_ in carried).most_common(1)[0][0]
    carried = [entry for entry in carried if entry[1][0] == unit]
    distinct = sorted({period for _, period, *_ in carried}, key=lambda period: (period[1], period[2]))
    evidence.update(resource_periods=len(distinct), resource_period_first=period_text(distinct[0]),
                    resource_period_last=period_text(distinct[-1]))
    if len(distinct) == 1:
        evidence["single_resource_period"] = distinct[0]
        evidence["resource_series"] = "one period in the names of the resources"
        return evidence, None

    failed = sorted({(position, period_text(period)) for position, period, obtained, _ in carried if not obtained})
    kept = [period for period in distinct
            if any(obtained for _, other, obtained, _ in carried if other == period)]
    per_period = Counter(period for _, period, *_ in carried)
    series = series_of_periods(unit, distinct, kept)
    notes = []
    if series["unit"] == EDITION:
        notes.append("editions: " + listed([period_text(period) for period in distinct]))
    elif any(ordinal(unit, period) is None for period in distinct):
        small = "days" if unit == DAYS else "years"
        listed_only = series_of_periods(unit, distinct)["missing"]
        notes.append(f"{series['missing']:,} of the {series['expected']:,} {small} between the first and the last "
                     f"are covered by no file obtained ({listed_only:,} by no resource listed)")
    lost = [period_text(period) for period in distinct if period not in kept]
    if lost:
        notes.append("no file obtained for " + listed(lost))
    if len(set(per_period.values())) == 1:
        notes.append(f"{with_noun(per_period[distinct[0]], 'resource')} per period")
    else:
        notes.append(f"{min(per_period.values())} to {max(per_period.values())} resources per period")
    repeated, same_period = repeated_files(carried)
    if repeated:
        notes.append(f"{with_noun(repeated, 'file')} identical to the file of an earlier period")
    if same_period:
        notes.append(f"{with_noun(same_period, 'file')} identical to another file of the same period")
    series.update(source="resources", where="", column="", notes="; ".join(notes))
    evidence.update(
        resource_series=f"{series['unit']}: {with_noun(len(distinct), 'period')}",
        resource_periods_missing=series["missing_periods"] if series["missing"] != "" else "no regular step",
        resources_not_obtained=listed([f"{position} ({text})" for position, text in failed]) if failed else "none",
        resource_files_repeated=repeated)
    series["not_obtained"] = len(failed)
    return evidence, series


def repeated_files(carried: list[tuple]) -> tuple[int, int]:
    """The files obtained that are identical, byte for byte, to the file of an earlier period, and those identical
    to another file of the same period."""
    seen: dict[str, tuple] = {}
    counted: set[str] = set()
    earlier = same = 0
    for position, period, obtained, digest in sorted(carried, key=lambda entry: (entry[1][1], entry[0])):
        if not obtained or not digest or position in counted:
            continue
        counted.add(position)
        if digest in seen:
            if seen[digest] == period:
                same += 1
            else:
                earlier += 1
        else:
            seen[digest] = period
    return earlier, same


def structure_evidence(structures: list[dict]) -> tuple[str, str]:
    """Whether the files of a dataset have the same columns, from the comparison of 06_file_checks.py: the state
    (same, different, unknown) and its description."""
    if not structures:
        return "unknown", ""
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in structures:
        groups.setdefault((row["group"], row["format"]), []).append(row)
    different, unread = [], 0
    for (group, family), rows in groups.items():
        headers = max(number(row["headers"]) for row in rows)
        tables = max(number(row["tables"]) for row in rows)
        if headers > 1:
            label = family if group == "all" else f"{group}, {family}"
            different.append(f"{headers} different headers in {with_noun(tables, 'table')} ({label})")
    recognised = sum(1 for row in structures if str(row.get("header") or "").strip())
    unread = sum(number(row["count"]) for row in structures if not str(row.get("header") or "").strip())
    if unread and recognised:
        different.append(f"{with_noun(unread, 'table')} without a header row that could be recognised")
    if different:
        return "different", "; ".join(different)
    if unread:
        return "unknown", f"not compared: {with_noun(unread, 'table')} without a header row that could be recognised"
    return "same", "the same columns in the files of each table"


# ---------------------------------------------------------------------------
# Periods inside the files
# ---------------------------------------------------------------------------

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


def member_bytes(path: Path, member: str) -> bytes:
    """The content of a member of a ZIP archive, found by the name recorded in the file profiles."""
    with zipfile.ZipFile(path, metadata_encoding=zip_encoding(path)) as archive:
        names = {info.filename: info for info in archive.infolist() if not info.is_dir()}
        info = names.get(member)
        if info is None:
            last = member.rsplit("/", 1)[-1]
            matches = [found for name, found in names.items() if name.rsplit("/", 1)[-1] == last]
            if len(matches) != 1:
                raise KeyError(f"member not found in the archive: {member}")
            info = matches[0]
        return archive.read(info)


def table_rows(profile: dict):
    """The rows of a table of the file profiles, from its header row on, as lists of cell values. The dates of a
    workbook come as dates."""
    path = ROOT / profile["file"]
    member, kind = profile.get("member") or "", profile["kind"]
    first = max(number(profile.get("header_row")), 1)
    if kind in DELIMITED_KINDS:
        encoding = profile.get("encoding") or "utf-8-sig"
        if member:
            handle = io.StringIO(member_bytes(path, member).decode(encoding, errors="replace"), newline="")
        else:
            handle = open(path, encoding=encoding, errors="replace", newline="")
        with handle:
            for index, row in enumerate(csv.reader(handle, delimiter=profile.get("delimiter") or ","), start=1):
                if index >= first:
                    yield row
        return
    data = member_bytes(path, member) if member else path.read_bytes()
    if kind == "xls":
        book = xlrd.open_workbook(file_contents=data)
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
                row.append(value)
            yield row
        return
    book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        sheet = book[profile["sheet"]] if profile.get("sheet") else book.worksheets[0]
        for index, values in enumerate(sheet.iter_rows(values_only=True), start=1):
            if index >= first:
                yield list(values)
    finally:
        book.close()


def whole_number(value) -> int | None:
    """The whole number that a cell holds, whether it is stored as a number or written as text."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    return int(float(text)) if re.fullmatch(r"\d{1,14}(?:\.0+)?", text) else None


def moment_of(value) -> dt.datetime | None:
    """The day, and the time when there is one, that a cell holds: a date of a workbook, or a date or time stamp
    written as text (2026-04-01, 1/4/2026, 2026-04-01 10:05, 202604011005). A number is read as a time stamp only
    with twelve or fourteen digits: a number of eight digits cannot be told from a code."""
    if isinstance(value, dt.datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    if value is None or isinstance(value, bool):
        return None
    compact = whole_number(value)
    text = str(compact) if compact is not None else str(value).strip()
    for pattern, order in ((ISO_MOMENT, (1, 2, 3)), (DAY_FIRST_MOMENT, (3, 2, 1)), (COMPACT_MOMENT, (1, 2, 3))):
        found = pattern.fullmatch(text)
        if not found or (pattern is COMPACT_MOMENT and len(text) not in (12, 14)):
            continue
        clock = [int(part or 0) for part in found.groups()[3:6]] + [0, 0, 0]
        try:
            year, month, day = (int(found.group(index)) for index in order)
            if not 1800 <= year <= 2199:
                return None
            return dt.datetime(year, month, day, clock[0], clock[1], clock[2])
        except ValueError:
            return None
    return None


def year_of(value) -> int | None:
    found = whole_number(value)
    return found if found is not None and 1800 <= found <= 2199 else None


def month_of(value) -> int | None:
    found = whole_number(value)
    return found if found is not None and 1 <= found <= 12 else None


def label_year(value) -> int | None:
    """The first year of a label of two consecutive years, such as 1960-61 or 1998-1999 (a hydrological, school or
    financial year)."""
    found = TWO_YEAR_LABEL.fullmatch(str(value).strip()) if isinstance(value, str) else None
    if not found:
        return None
    first, second = int(found.group(1)), int(found.group(2))
    return first if second in ((first + 1) % 100, first + 1) else None


def with_digit(value) -> bool:
    return not isinstance(value, (dt.date, dt.datetime)) and value is not None and bool(re.search(r"\d", str(value)))


def share_read(values: list, reader) -> bool:
    """Whether a column holds periods: at least three of its cells are read as periods, and so are nine in ten of
    its cells that hold a date or a digit (words such as a total are left out of the count)."""
    counted = [value for value in values if isinstance(value, (dt.date, dt.datetime)) or with_digit(value)]
    read = sum(1 for value in counted if reader(value) is not None)
    return read >= MINIMUM_SERIES and read >= SHARE_OF_PERIODS * len(counted)


def period_columns(names: list[str], head: list[list]) -> tuple[str, list[int]] | None:
    """The columns of a table that give the period of each record, chosen on its first records: a column of dates
    or time stamps; else a column of years, with a column of months when there is one; else a column of labels of
    two consecutive years."""
    width = max([len(names)] + [len(row) for row in head])
    columns = [[row[index] for row in head if index < len(row) and str(row[index] or "").strip()]
               for index in range(width)]
    words = [set(words_of(names[index])) if index < len(names) else set() for index in range(width)]
    for index in range(width):
        if share_read(columns[index], moment_of):
            return "dates", [index]
    years = [index for index in range(width) if words[index] & YEAR_WORDS and share_read(columns[index], year_of)]
    if years:
        months = [index for index in range(width)
                  if words[index] & MONTH_WORDS and share_read(columns[index], month_of)]
        return ("year and month", [years[0], months[0]]) if months else ("years", [years[0]])
    for index in range(width):
        if share_read(columns[index], label_year):
            return "labels", [index]
    return None


def steps_note(moments: set[dt.datetime]) -> str:
    """For readings with a time of day: the usual step between two readings, how many readings are missing between
    the first and the last, and the longest interruption."""
    ordered = sorted(moments)
    if len(ordered) < MINIMUM_SERIES or all(moment.time() == dt.time(0) for moment in ordered):
        return ""
    gaps = [int((after - before).total_seconds()) for before, after in zip(ordered, ordered[1:])]
    step = Counter(gaps).most_common(1)[0][0]
    if step <= 0 or step >= 86400:
        return ""
    missing = sum(round(gap / step) - 1 for gap in gaps if gap > step)
    expected = len(ordered) + missing
    return (f"readings every {step // 60:,} minutes; {missing:,} of {expected:,} readings missing between the "
            f"first and the last; longest interruption {max(gaps) // 60:,} minutes")


def filled(value) -> bool:
    return value is not None and str(value).strip() != ""


def period_of_record(kind: str, cells: list):
    """The period that the period cells of a record give: the moment for a column of dates, the place of the month
    or of the year for the other columns; nothing when the cells cannot be read as a period."""
    if kind == "dates":
        return moment_of(cells[0])
    if kind == "year and month":
        year, month = year_of(cells[0]), month_of(cells[1])
        return year * 12 + month - 1 if year and month else None
    return year_of(cells[0]) if kind == "years" else label_year(cells[0])


def period_key_text(kind: str, key) -> str:
    """A period as it was read from a record: a day, a month, a year or a label of two years."""
    if kind == "dates":
        return key.isoformat()
    if kind == "year and month":
        return ordinal_text(MONTH, key)
    return ordinal_text(LABEL, key) if kind == "labels" else str(key)


def records_by_period(counts: dict[int, int]) -> tuple[int, int, bool]:
    """The fewest and the most records that a period of a table holds, and whether the table is laid out by period:
    nine in ten of its periods, the first and the last left out, hold between half and twice the usual number of
    records. A date that is one of the attributes of the records of a register does not pass."""
    ordered = [counts[place] for place in sorted(counts)]
    inner = ordered[1:-1] if len(ordered) > 2 else ordered
    usual = statistics.median(inner)
    close = sum(1 for count in inner if usual / 2 <= count <= usual * 2)
    return min(ordered), max(ordered), close >= EVEN_PERIODS * len(inner)


def span_text(low: int, high: int) -> str:
    return f"{low:,}" if low == high else f"{low:,} to {high:,}"


def table_series(profile: dict, personal: bool) -> dict | None:
    """The series of periods inside a table, or nothing when no column gives the period of its records."""
    rows = table_rows(profile)
    header = next(rows, None)
    if header is None:
        return None
    names = [plain_text(value) for value in header]
    head = list(islice(rows, HEAD_RECORDS))
    chosen = period_columns(names, head)
    if not chosen:
        return None
    kind, columns = chosen
    moments: set[dt.datetime] = set()
    records: Counter = Counter()     # records with values, per day (dates) or per year, month or label
    bare: Counter = Counter()        # rows that hold their period and nothing else
    unread = 0                       # records whose period cells hold a digit and cannot be read as a period
    rows = table_rows(profile)
    next(rows, None)
    for row in rows:
        cells = [row[index] if index < len(row) else None for index in columns]
        period = period_of_record(kind, cells)
        if period is None:
            unread += any(with_digit(cell) for cell in cells)
            continue
        key = period.date() if kind == "dates" else period
        if not any(filled(value) for index, value in enumerate(row) if index not in columns):
            bare[key] += 1
            continue
        records[key] += 1
        if kind == "dates":
            moments.add(period)
    if not records:
        return None
    if kind == "dates":
        days = set(records)
        series = series_of_days(days)
        span = (max(days) - min(days)).days + 1
        series["notes"] = steps_note(moments) if series["unit"] == DAY else (
            f"dates on {len(days):,} of the {span:,} days between the first and the last")
        place = {DAY: lambda day: day.toordinal(), MONTH: lambda day: day.year * 12 + day.month - 1,
                 YEAR: lambda day: day.year}[series["unit"]]
        counts: Counter = Counter()
        for day, count in records.items():
            counts[place(day)] += count
    else:
        series = regular_series({"year and month": MONTH, "years": YEAR, "labels": LABEL}[kind], set(records))
        series["notes"] = ""
        counts = records
    low, high, by_period = records_by_period(counts)
    notes = [series["notes"]] if series["notes"] else []
    if high > 1 and statistics.median(counts.values()) == 1:
        repeated = sorted(place for place, count in counts.items() if count > 1)
        notes.append(f"{with_noun(len(repeated), 'period')} carried by more than one record: "
                     + listed([ordinal_text(series["unit"], place) for place in repeated]))
    empty = sorted(key for key in bare if key not in records)
    if empty:
        notes.append(f"{with_noun(len(empty), 'period')} with a row that holds no value: "
                     + listed([period_key_text(kind, key) for key in empty]))
    if unread:
        notes.append(f"{with_noun(unread, 'record')} with a period that could not be read")
    series.update(records_low=low, records_high=high, records_per_period=span_text(low, high), by_period=by_period,
                  records=sum(records.values()), rows_without_values=sum(bare.values()), periods_not_read=unread,
                  notes="; ".join(notes))
    column = " and ".join(names[index] if index < len(names) and names[index] else f"column {index + 1}"
                          for index in columns)
    series.update(source="table", where=where_of(profile), column="(name not written)" if personal else column)
    return series


def where_of(profile: dict) -> str:
    """The place of a table: the position of its resource, the member of the archive and the sheet."""
    parts = [profile["position"]]
    if profile.get("member"):
        parts.append(profile["member"])
    if profile.get("sheet"):
        parts.append(f'sheet "{profile["sheet"]}"')
    return " ".join(parts)


def header_series(profile: dict) -> dict | None:
    """The series of periods written as the names of the columns of a table (one column per month or per year),
    from the names recorded in the file profiles."""
    names = [name.strip() for name in str(profile.get("column_names") or "").split(" | ")]
    months = [MONTH_AS_COLUMN_NAME.fullmatch(name) for name in names]
    months = [(int(found.group(1)), int(found.group(2))) for found in months if found]
    years = [int(name) for name in names if re.fullmatch(r"(?:18|19|20)\d\d", name)]
    labels = [label_year(name) for name in names if label_year(name) is not None]
    if len(months) >= MINIMUM_SERIES and all(1 <= month <= 12 for _, month in months) and len(labels) < len(months):
        series = regular_series(MONTH, {year * 12 + month - 1 for year, month in months})
    elif len(labels) >= MINIMUM_SERIES:
        series = regular_series(LABEL, set(labels))
    elif len(years) >= MINIMUM_SERIES:
        series = regular_series(YEAR, set(years))
    else:
        return None
    series.update(source="header", where=where_of(profile), column="", notes="the periods are the names of columns",
                  records="", records_per_period="", rows_without_values="", periods_not_read="", by_period=True)
    return series


def file_evidence(sample_id: str, profiles: list[dict]) -> tuple[dict, list[dict]]:
    """The periods inside the tables of a dataset: the evidence for its row and the series found."""
    personal = sample_id in PERSONAL_DATA_SUSPECTED
    found, unread, read = [], [], 0
    for profile in profiles:
        if profile.get("data_file") != "True" or profile["kind"] not in DELIMITED_KINDS | WORKBOOK_KINDS:
            continue
        series = None
        try:
            series = table_series(profile, personal)
            read += 1
        except FileNotFoundError:
            unread.append(f"{where_of(profile)}: file not found")
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, xlrd.XLRDError, csv.Error,
                InvalidFileException) as error:
            unread.append(f"{where_of(profile)}: {type(error).__name__}")
        if series is None and not personal:
            series = header_series(profile)
        if series:
            found.append(series)
    evidence = {"tables_read": read, "tables_not_read": len(unread), "tables_with_periods": len(found),
                "file_series": "", "file_periods": "", "file_period_first": "", "file_period_last": "",
                "file_tables_with_missing_periods": "", "file_periods_missing": "",
                "file_tables_not_by_period": "", "file_records_per_period": "", "file_rows_without_values": "",
                "file_periods_not_read": "", "unread": unread}
    if found:
        units = Counter(series["unit"] for series in found)
        unit = units.most_common(1)[0][0]
        main = [series for series in found if series["unit"] == unit]
        counts = sorted(series["periods"] for series in main)
        gapped = [series for series in main if series["missing"]]
        counted = [series for series in main if series["records_per_period"]]
        evidence.update(
            file_tables_not_by_period=sum(1 for series in main if not series["by_period"]),
            file_rows_without_values=sum(number(series["rows_without_values"]) for series in main),
            file_periods_not_read=sum(number(series["periods_not_read"]) for series in main),
            file_records_per_period=span_text(min(series["records_low"] for series in counted),
                                              max(series["records_high"] for series in counted)) if counted else "",
            file_series=f"{unit}: {with_noun(len(main), 'table')}"
                        + (f" (and {len(found) - len(main)} with another unit)" if len(found) > len(main) else ""),
            file_periods=str(counts[0]) if counts[0] == counts[-1] else f"{counts[0]} to {counts[-1]}",
            file_period_first=min(series["first"] for series in main),
            file_period_last=max(series["last"] for series in main),
            file_tables_with_missing_periods=len(gapped),
            file_periods_missing="none" if not gapped else listed(
                [f"{series['where']}: {series['missing_periods']}" for series in gapped], 3))
    return evidence, found


def recorded_time_columns(rows: list[dict]) -> tuple[str, str]:
    """The time columns that 06_file_checks.py recorded for a dataset, with the range of each over all its tables:
    those that say when the data were observed, and the validity of a timetable."""
    def ranges(roles: set[str]) -> str:
        columns: dict[str, list[dict]] = {}
        for row in rows:
            if row["role"] in roles and " to " in row["range"]:
                columns.setdefault(row["name"] or "(name not written)", []).append(row)
        texts = []
        for name, items in columns.items():
            starts = [item["range"].split(" to ")[0] for item in items]
            ends = [item["range"].split(" to ")[1] for item in items]
            texts.append(f"{name}: {min(starts)} to {max(ends)} ({with_noun(len(items), 'table')})")
        return listed(texts)
    return ranges(OBSERVATION_ROLES), ranges({SCHEDULE_ROLE})


# ---------------------------------------------------------------------------
# Other periods in separate datasets
# ---------------------------------------------------------------------------

def carried_periods(entry: dict) -> list[tuple]:
    """The periods that a dataset of the catalogue carries: the one of its title, else those of the names of its
    resources."""
    period = period_of(entry["title"])
    if period:
        return [period]
    periods = []
    for name in entry["resources"]:
        period = period_of(name)
        if period and period not in periods:
            periods.append(period)
    return sorted(periods, key=lambda period: (period[1], period[2]))


def sibling_evidence(sample_id: str, dataset: dict, own: tuple, publishers: dict[str, list[dict]]
                     ) -> tuple[dict, list[dict], dict | None]:
    """The other datasets of the same publisher that may hold other periods of a dataset: those with the same title
    once the period is taken out, and those whose title begins with the same two words."""
    organisation = dataset.get("organization") if isinstance(dataset.get("organization"), dict) else {}
    stem = stem_of(dataset.get("title"))
    start = stem.split()[:2]
    same, similar = [], []
    for entry in publishers.get(str(organisation.get("name") or ""), []):
        if entry["id"] == dataset.get("id"):
            continue
        other = stem_of(entry["title"])
        if other == stem:
            same.append(entry)
        elif len(start) == 2 and other.split()[:2] == start:
            similar.append(entry)
    rows = []
    for level, entries in (("same title", same), ("similar title", similar)):
        ordered = sorted(entries, key=lambda entry: ((carried_periods(entry) or [(0, dt.date.max)])[0][1],
                                                     entry["title"]))
        for entry in ordered:
            periods = carried_periods(entry)
            texts = [period_text(period) for period in periods]
            text = listed(texts) if len(texts) <= LISTED else f"{texts[0]} to {texts[-1]} ({len(texts)} periods)"
            rows.append({"sample_id": sample_id, "level": level, "dataset": entry["name"], "title": entry["title"],
                         "period": text, "resources": len(entry["resources"])})
    evidence = {"same_title_datasets": len(same), "same_title_periods": "", "same_title_periods_missing": "",
                "similar_title_datasets": len(similar)}
    series = None
    unit = own[0]
    periods = [own] + [period for entry in same for period in carried_periods(entry) if period[0] == unit]
    if same:
        distinct = sorted(set(periods), key=lambda period: (period[1], period[2]))
        series = series_of_periods(unit, distinct)
        notes = [f"{with_noun(len(same), 'other dataset')} of the publisher with the same title"]
        unread = sum(1 for entry in same if not carried_periods(entry))
        doubled = len(periods) - len(distinct)
        if unread:
            notes.append(f"{with_noun(unread, 'dataset')} without a period that could be read")
        if doubled:
            notes.append(f"{with_noun(doubled, 'period')} carried by more than one dataset")
        series.update(source="catalogue", where=stem, column="", notes="; ".join(notes))
        evidence.update(
            same_title_periods=f"{series['unit']}: {with_noun(series['periods'], 'period')}, "
                               f"{series['first']} to {series['last']}",
            same_title_periods_missing=series["missing_periods"])
    return evidence, rows, series


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------

def other_periods(evidence: dict) -> str:
    """What the catalogue shows about the other periods of a dataset that carries one period, and the scores that
    the rule gives."""
    found = evidence.get("same_title_datasets") or 0
    others = (f"{with_noun(found, 'other dataset')} of the publisher with the same title and another period"
              if found else "no other dataset of the publisher with the same title")
    return (f"{others}, {evidence.get('similar_title_datasets') or 0} with a similar title: 1 when the other "
            "periods exist as separate datasets, 0 when none is found, n/a for one fixed moment")


def propose(entry: dict, evidence: dict, series: dict | None, tables: list[dict], own: tuple | None,
            structure: str) -> tuple[str, str]:
    """The proposed score of AI3 where a rule decides without judgement, otherwise the mark of the review."""
    missing_files = entry.get("no_data_file", "").strip()
    if missing_files == "unavailable":
        if series:
            return "1", (f"no file obtained; the names of the resources show {series['periods']} periods "
                         f"({series['first']} to {series['last']}): at most 1")
        return "0", "no file obtained, and the names of the resources show no earlier period or version"
    if missing_files == "map images":
        return BY_HAND, "map images: n/a when the image shows the map of one act or of one moment"
    if missing_files == "documents":
        return BY_HAND, ("documents: the earlier documents on the page of the publisher, when the page keeps them; "
                         "n/a for the document of one act")
    if series:
        text = (f"series across the resources ({series['unit']}): {series['periods']} periods, "
                f"{series['first']} to {series['last']}")
        if series["periods"] < MINIMUM_SERIES:
            return "1", f"{text}: fewer than the {MINIMUM_SERIES} periods or versions that make a series"
        problems = []
        if series["missing"] not in ("", 0):
            problems.append(f"missing: {series['missing_periods']}")
        if series["not_obtained"]:
            problems.append(f"{with_noun(series['not_obtained'], 'file')} not obtained")
        if structure == "different":
            problems.append(f"different columns ({evidence['structure_across_files']})")
        if problems:
            return "1", f"{text}; " + "; ".join(problems)
        if structure == "unknown":
            return BY_HAND, f"{text}, nothing missing; the columns of the files were not compared"
        return "2", f"{text}, nothing missing, the same columns"
    if single_period(own):
        return BY_HAND, f"one period ({period_text(own)}); {other_periods(evidence)}"
    if tables:
        unit = Counter(item["unit"] for item in tables).most_common(1)[0][0]
        main = [item for item in tables if item["unit"] == unit]
        most = max(item["periods"] for item in main)
        gapped = [item for item in main if item["missing"]]
        text = (f"series inside the files ({unit}): {with_noun(len(main), 'table')}, up to {most} periods, "
                f"{evidence['file_period_first']} to {evidence['file_period_last']}")
        if most < MINIMUM_SERIES:
            return BY_HAND, f"{text}: fewer than the {MINIMUM_SERIES} periods that make a series"
        loose = [item for item in main if not item["by_period"]]
        if loose:
            return BY_HAND, (f"{text}; {with_noun(len(loose), 'table')} not laid out by period (records per period: "
                             f"{evidence['file_records_per_period']}): 2 or 1 when the column gives the period of "
                             "the data, 0 when it is an attribute of the records of a register or of a list")
        if gapped:
            return "1", f"{text}; {with_noun(len(gapped), 'table')} with missing periods"
        return "2", f"{text}, nothing missing"
    if own:
        span = "days" if own[0] == DAYS else "years"
        return BY_HAND, (f"one period of several {span} ({period_text(own)}) and no series inside the files; "
                         f"{other_periods(evidence)}")
    return BY_HAND, ("no earlier period or version found in the resources or in the files: 0 when the data show a "
                     "state that changes, n/a when they show one fixed moment by nature")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], series: list[dict], siblings: list[dict], date: str,
                 titles: dict[str, str]) -> None:
    proposals = Counter(row["ai3_proposal"] for row in checks)
    lines = [
        f"# Historical depth of the datasets of the sample (AI3), snapshot of {date}",
        "",
        "Produced by `scripts/09_history_checks.py`. The tables collect the evidence for the review of the "
        "criterion; a score is proposed only where a rule decides without judgement, and the final scores are "
        "recorded in `DECISIONS.md`. Only periods were read from the files; this report contains no records of "
        "the data.",
        "",
        "## Proposals",
        "",
        "Proposed AI3: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", "n/a", BY_HAND)
                                    if proposals[score]) + ".",
        "",
        "| Dataset | Organisation of the files | Proposal | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in checks:
        title = md_cell(titles.get(row["sample_id"], "")[:60])
        lines.append(f"| {row['sample_id']} {title} | {row['organisation']} | {row['ai3_proposal']} | "
                     f"{md_cell(row['ai3_reason'])} |")
    lines += ["", "## What the metadata say about time", "",
              "| Dataset | Frequency | Temporal coverage | Version | Dates in the additional metadata | Resources | "
              "Files replaced after the resource was created | Period in the title |",
              "| --- | --- | --- | --- | --- | ---: | --- | --- |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} | {row['frequency']} | {md_cell(row['temporal_coverage'])} | "
                     f"{md_cell(row['version'])} | {md_cell(row['dates_in_additional_metadata'])} | "
                     f"{row['resources']} | {md_cell(row['resources_replaced'])} | {row['period_in_title']} |")
    lines += ["", "## Series across the resources", "",
              "| Dataset | Resources with a period | Series | First | Last | Missing | Files not obtained | Files "
              "identical to an earlier period | Columns of the files |",
              "| --- | ---: | --- | --- | --- | --- | --- | ---: | --- |"]
    for row in checks:
        if row["resources_with_period"]:
            lines.append(f"| {row['sample_id']} | {row['resources_with_period']} | {row['resource_series']} | "
                         f"{row['resource_period_first']} | {row['resource_period_last']} | "
                         f"{md_cell(row['resource_periods_missing'])} | {md_cell(row['resources_not_obtained'])} | "
                         f"{row['resource_files_repeated']} | {md_cell(row['structure_across_files'])} |")
    lines += ["", "## Periods inside the files", "",
              "| Dataset | Tables read | Not read | With periods | Series | Periods per table | First | Last | "
              "Tables with missing periods | Missing | Records per period | Tables not laid out by period | Rows "
              "without values | Periods not read | Time columns recorded by the file checks | Validity of the "
              "timetable |",
              "| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- | "
              "--- |"]
    for row in checks:
        if row["tables_read"] or row["tables_not_read"] or row["time_columns_recorded"] or row["timetable_validity"]:
            lines.append(f"| {row['sample_id']} | {row['tables_read']} | {row['tables_not_read']} | "
                         f"{row['tables_with_periods']} | {row['file_series']} | {row['file_periods']} | "
                         f"{row['file_period_first']} | {row['file_period_last']} | "
                         f"{row['file_tables_with_missing_periods']} | {md_cell(row['file_periods_missing'])} | "
                         f"{row['file_records_per_period']} | {row['file_tables_not_by_period']} | "
                         f"{row['file_rows_without_values']} | {row['file_periods_not_read']} | "
                         f"{md_cell(row['time_columns_recorded'])} | {md_cell(row['timetable_validity'])} |")
    lines += ["", "## Other periods in separate datasets of the same publisher", "",
              "| Dataset | Same title, other period | Periods with the dataset itself | Missing | Titles that begin "
              "with the same two words |",
              "| --- | ---: | --- | --- | ---: |"]
    for row in checks:
        if row["same_title_datasets"] != "":
            lines.append(f"| {row['sample_id']} | {row['same_title_datasets']} | "
                         f"{md_cell(row['same_title_periods'])} | {md_cell(row['same_title_periods_missing'])} | "
                         f"{row['similar_title_datasets']} |")
    lines += ["", "## Series found", "",
              "| Dataset | Source | Where | Column | Unit | Periods | First | Last | Expected | Missing | Missing "
              "periods | Records | Records per period | Rows without values | Periods not read | Notes |",
              "| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | "
              "--- |"]
    for row in series:
        lines.append(f"| {row['sample_id']} | {row['source']} | {md_cell(row['where'])} | {md_cell(row['column'])} | "
                     f"{row['unit']} | {row['periods']} | {row['first']} | {row['last']} | {row['expected']} | "
                     f"{row['missing']} | {md_cell(row['missing_periods'])} | {row.get('records', '')} | "
                     f"{row.get('records_per_period', '')} | {row.get('rows_without_values', '')} | "
                     f"{row.get('periods_not_read', '')} | {md_cell(row['notes'])} |")
    if not series:
        lines.append("| - | no series found | | | | | | | | | | | | | | |")
    lines += ["", f"The datasets of the catalogue behind the fifth table are listed in "
                  f"`data/processed/history_siblings_{date}.csv` ({with_noun(len(siblings), 'row')})."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argparse.ArgumentParser(description="Evidence on the historical depth of the datasets of the sample "
                                        "(criterion AI3).").parse_args()
    csv.field_size_limit(2 ** 31 - 1)

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    inputs = {name: PROCESSED_DIR / f"{name}_{date}.csv"
              for name in ("resource_downloads", "file_profiles", "file_structures", "file_plausibility")}
    for name, needed in inputs.items():
        if not needed.exists():
            script = "05_resource_download.py" if name == "resource_downloads" else "06_file_checks.py"
            raise SystemExit(f"{relative(needed)} not found. Run {script} first.")
    log, profiles, structures, plausibility = (read_csv(inputs[name]) for name in inputs)
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    checks_file = PROCESSED_DIR / f"history_checks_{date}.csv"
    series_file = PROCESSED_DIR / f"history_series_{date}.csv"
    siblings_file = PROCESSED_DIR / f"history_siblings_{date}.csv"
    report_file = OUT_DIR / f"history_{date}" / "history_checks.md"

    print(f"Snapshot: {relative(snapshot)}")
    datasets, publishers = read_catalogue(snapshot, sample)
    print(f"Datasets of the catalogue: {sum(len(entries) for entries in publishers.values()):,}; of the sample: "
          f"{len(sample)}")

    checks, all_series, all_siblings, unread = [], [], [], []
    for sample_id in sorted(sample):
        dataset = datasets.get(sample_id) or {}
        entry = organisation.get(sample_id, {})
        own_profiles = [row for row in profiles if row["sample_id"] == sample_id]
        evidence = metadata_evidence(dataset)
        across, series = resource_series(dataset, [row for row in log if row["sample_id"] == sample_id],
                                         own_profiles)
        state, description = structure_evidence([row for row in structures if row["sample_id"] == sample_id])
        inside, tables = file_evidence(sample_id, own_profiles)
        unread += [f"{sample_id} {text}" for text in inside.pop("unread")]
        observed, timetable = recorded_time_columns([row for row in plausibility if row["sample_id"] == sample_id])
        evidence.update(across, structure_across_files=description, **inside, time_columns_recorded=observed,
                        timetable_validity=timetable, same_title_datasets="", same_title_periods="",
                        same_title_periods_missing="", similar_title_datasets="")
        own = period_of(dataset.get("title")) or evidence.pop("single_resource_period")
        evidence.pop("single_resource_period", None)
        found_series = ([series] if series else []) + tables
        if own and not series and entry.get("no_data_file", "").strip() != "map images":
            related, rows, catalogue = sibling_evidence(sample_id, dataset, own, publishers)
            evidence.update(related)
            all_siblings += rows
            if catalogue:
                found_series.append(catalogue)
        proposal, reason = propose(entry, evidence, series, tables, own, state)
        checks.append({"sample_id": sample_id, "dataset": dataset.get("name", sample[sample_id].get("name", "")),
                       "group": sample[sample_id].get("group", ""), "category": sample[sample_id].get("category", ""),
                       "organisation": entry.get("organisation", ""), **evidence, "ai3_proposal": proposal,
                       "ai3_reason": reason})
        all_series += [{"sample_id": sample_id, **item} for item in found_series]
        print(f"{sample_id} AI3 {proposal}: {reason[:150]}", flush=True)

    write_csv(checks_file, CHECK_FIELDS, checks)
    write_csv(series_file, SERIES_FIELDS, all_series)
    write_csv(siblings_file, SIBLING_FIELDS, all_siblings)
    write_report(report_file, checks, all_series, all_siblings, date, titles)

    proposals = Counter(check["ai3_proposal"] for check in checks)
    print("Proposed AI3: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", "n/a", BY_HAND)
                                       if proposals[score]))
    print(f"Tables read: {sum(check['tables_read'] for check in checks):,}; with periods inside: "
          f"{sum(check['tables_with_periods'] for check in checks):,}; not read: {len(unread):,}")
    for text in unread[:10]:
        print(f"  not read: {text}")
    if len(unread) > 10:
        print(f"  and {len(unread) - 10} more")
    print("Files:")
    for path in (checks_file, series_file, siblings_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
