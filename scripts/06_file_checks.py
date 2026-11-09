r"""
06_file_checks.py
Phase 3, step 2: examination of the downloaded files of the sample (criteria AI1, a structure that a program can
read without manual cleaning, Q2, completeness, Q3, consistency, Q4, plausibility, and AI6, linkage through
common identifiers).

What it does, in order:
  1. Reads the download log of 05_resource_download.py (data/processed/resource_downloads_YYYY-MM-DD.csv), the
     organisation of the files of each dataset (criteria/file_organisation.csv) and the sample.
  2. Opens every downloaded file of the 36 datasets (data/raw/resources/<sample id>/), the files downloaded by
     hand from a web page of the publisher (named rNNN_manual.<extension>) and the files inside ZIP and RAR
     archives. Each table (a CSV file, a sheet of a spreadsheet, a file of a GTFS feed) is checked for its
     layout; each file in a standard structured format (JSON, GeoJSON, XML, KML, GML, Turtle, shapefile) is
     parsed. The cells of the records of every table or file are counted, and among them the empty ones; the
     values of every column are read by kind and form (Q3) and checked against their plausible range (Q4); the
     columns that carry an identifier or coordinates are recognised (AI6).
  3. Proposes a score of AI1, Q2, Q3, Q4 and AI6 for every dataset: AI1 and Q2 from the files named in
     criteria/file_organisation.csv, Q3, Q4 and AI6 from all the data files.
  4. Writes:
        data/processed/file_profiles_YYYY-MM-DD.csv   one row per resource, table or file examined
        data/processed/file_columns_YYYY-MM-DD.csv    one row per column counted for Q2: cells and empty cells
        data/processed/file_formats_YYYY-MM-DD.csv    one row per column examined for Q3: kinds and forms of values
        data/processed/file_structures_YYYY-MM-DD.csv one row per header of the files of the same table (Q3)
        data/processed/file_plausibility_YYYY-MM-DD.csv one row per column with a range check (Q4): extremes, counts
        data/processed/file_keys_YYYY-MM-DD.csv       one row per identifier or coordinate column found (AI6)
        data/processed/file_checks_YYYY-MM-DD.csv     one row per dataset: organisation, proposed scores, reasons
        outputs/files_YYYY-MM-DD/file_checks.md       the proposed scores per dataset
        outputs/files_YYYY-MM-DD/factsheets/Sxx.md    the fact sheet of every dataset
        review/sample_records_YYYY-MM-DD.xlsx         local review file of Q3 and Q4 (see below)
     The date in the names is the date of the snapshot. None of the files in data/processed and outputs contains
     records of the data: only names, sizes, counts, column names, the forms of the values (such as "d/m/yyyy"
     or "decimal comma"), the extremes of the columns checked for their range (such as the earliest and the latest
     date), the placeholders of missing values (such as "-" or "///") and the findings of the checks. For the
     datasets that seem to contain personal data (DECISIONS.md #29), the column names are not written either, only
     their number. The local review file in the folder review holds a random sample of the
     records of every dataset and the rows that show the findings of Q3 and Q4, for the manual look: the folder is
     ignored by git (.gitignore), so these records never enter the repository; for the datasets that seem to
     contain personal data it holds the row numbers only.

Rules of AI1 (DECISIONS.md #38):
  - The files that are judged are named in criteria/file_organisation.csv: the single data file; the best one of
    the same data in several formats; the latest edition of a series; the worst one of the parts of an edition.
    A dataset without any data file available scores 0.
  - Data files: CSV and other delimited text, spreadsheets (XLS, XLSX), JSON and GeoJSON, XML with data (GML,
    KML), RDF in Turtle, shapefiles, GTFS feeds. PDF and Word documents, images, web pages, map views (WMS) and
    capabilities documents are not data files.
  - A table scores 2 with one header row, one record per row and one value per cell, without notes or totals in
    it. It scores 1 when it needs minor cleaning: title or note rows above the header, a header over two rows,
    totals rows, sub-heading rows, repeated header rows or empty rows inside the table, note rows below it, numbers
    stored as text (spreadsheets). An empty row is read by a program as an empty record: a row of a sheet without
    values, or a line of a CSV file with delimiters only (a line without any character is skipped and not counted).
    It scores 0 when it cannot be read without manual work: merged cells inside the data, several tables in one
    sheet or file, rows of a CSV file with values beyond the columns of the header, a file that cannot be read.
  - A spreadsheet scores its worst visible sheet that holds a table; sheets without a table (e.g. notes) and
    hidden sheets are recorded but not scored. A GTFS feed scores its worst file; an archive scores its worst
    data file.
  - A file in a standard structured format (JSON, GeoJSON, XML, KML, GML, Turtle, shapefile) scores 2 when it is
    parsed without error and 0 otherwise.

How the layout of a table is read: the rows are grouped in blocks separated by empty rows. The block with the most
rows of two or more values is the table, and its first row filled at least half as much as its usual row is the
header. Another block with three or more such rows is a second table when it lies above the table with a similar
width, when it is wider than the header, or when, below the table, it starts with a title and a header of its own
(text only, in a table of numbers); a narrower block is a set of title or note rows, a block of summary rows
(totals, maxima, minima, means) or a block that continues with records belongs to the table, and the empty rows
inside the table count. A row that repeats the header inside the table counts as a repeated header. A totals row
starts with a word such as "Σύνολο" or "Total", or is a whole summary label such as "Μέγιστο", "Μεγ. ύψος" or
"Μ.Ο."; a sub-heading row has a single text value in a table of three or more columns. In a spreadsheet, a number
stored as text is a text cell that reads as a number, in a column that holds numbers or mostly such cells; codes
with a leading zero or of five digits or more (postal codes, tax numbers) do not count. In a CSV file every value is
text, so the formats of numbers are examined under Q3.

Rules of Q2 (DECISIONS.md #39):
  - The files are those of AI1, with one difference: the parts of an edition are counted together, as one file,
    and a column is without any value only when it has no value in any part. Of the same data in several formats
    the most complete one counts; a field that more than half of the formats carry and one format leaves out (a KML
    file leaves out the fields without any value) counts in that format as a column without any value. Of a series
    the latest edition counts. All the visible tables of a file count together.
  - A cell is empty when it holds nothing (or only spaces), only symbols that stand for a missing value (dashes,
    dots, slashes, asterisks, question marks and the like: "-", "..", "…", "/", "///", "*", "?"), a word for a
    missing value (N/A, NA, null, None, NaN, Δ/Υ, Δ.Υ.), an error value of a spreadsheet (#N/A, #DIV/0!, #REF! and
    the like) or the number -999 or -9999. A unit or currency sign on its own, such as "%", "°" or "€", is a value.
    Every empty cell counts, whatever it may mean to a reader (zero, not applicable, unknown), since a program
    cannot tell; a meaning of empty cells belongs in a legend of the dataset.
  - Only the cells of the records count: under the header and in its columns. Title and note rows, totals and
    summary rows, sub-heading rows, empty rows and repeated header rows do not count (their layout is judged under
    AI1). The column _id that the portal adds to the CSV files of its DataStore does not count; a merged cell
    counts with its value over all the cells that it covers; in a sheet with several tables the records of all of
    them count; a column without a name and without any value is not a column.
  - GeoJSON, shapefile and KML: one record per feature, one column per property, and the geometry as one more
    column. JSON: one record per object of the list of records, one column per key; a missing key is an empty cell.
  - GTFS feeds and RDF in the STIRData model: only the fields that the standard makes mandatory count, since the
    standard allows the other fields to stay empty and defines what an empty value means. GTFS: the required fields
    of each file of the reference, the name and the coordinates of stops, stations and entrances, the parent
    station of entrances, generic nodes and boarding areas, the short or the long name of a route, the stop of a
    stop time, the arrival time at the first and the last stop of a trip, and the arrival and departure times at
    timepoints. STIRData: the legal name and the legal identifier of every legal entity.
  - Score: under 5% of empty cells without a column that has no value at all scores 2; 5% to 20%, or a column
    without any value, scores 1; over 20%, or no file that can be opened, scores 0.
  - Datasets without a data file (criteria/file_organisation.csv, column no_data_file): data published only as
    documents are estimated by inspection (n/d); map images only are not applicable (n/a); nothing available
    scores 0.

Rules of Q3 (DECISIONS.md #40):
  - All the data files of the dataset count: every edition of a series, every part, every format and every visible
    sheet, since the criterion asks whether the values are recorded in the same way throughout the dataset and
    whether all its files share the same structure (AI1 and Q2 examine the most recent file only).
  - The values of every column are read by kind (number, date, text) and form: a date "d/m/yyyy", "m/d/yyyy" or
    "yyyy-mm-dd", with or without the time; a number with a decimal point or a decimal comma, with or without a
    thousands separator, in scientific notation, or written with its unit ("12,50 €", "5 kg"); a comparison such
    as "<5"; a range such as "5-10"; text. A value such as "2001-02" in a column that also holds ranges such as
    "2001-2002" is a period, not a month. In spreadsheets, JSON, GeoJSON and shapefiles the stored type of every
    value is known as well.
    The columns of the files that hold the same table are pooled. Empty cells and the placeholders of Q2 are left
    out. Columns of codes and identifiers are not judged, since codes are rightly written as text: by their name
    (code, κωδικός, id, α/α, Α.Φ., ΑΦΜ, ΚΑΕΚ, Τ.Κ., αριθμός πρωτοκόλλου) or by numbers with a leading zero.
  - Minor inconsistencies (score 1), already from a single value: dates in several formats in one column; decimal
    point and decimal comma, different thousands separators, or a thousands separator in some values only, in
    one column; numbers stored as text in a spreadsheet, JSON or a
    shapefile (the rule of AI1: text cells that read as numbers, apart from codes with a leading zero or of five
    digits or more, in a column with numbers or mostly of such cells); numbers written with their unit in the
    cell; values of another kind in a column of numbers or dates, values converted to dates by the spreadsheet
    program in a column of text, or no kind of value in more than half of a column; values not in the format of
    the GTFS reference (dates YYYYMMDD, times HH:MM:SS or H:MM:SS, coordinates and decimals with a point,
    integers, colours of six hexadecimal digits); columns that differ in name, order or number between the files
    of the same table.
  - Major inconsistencies (score 0): different units in one column; values shifted between columns (rows of a CSV
    file with more fields than the header, and the cases found in the manual look); no file that can be opened.
  - The files of the same table follow criteria/file_organisation.csv, column tables: empty, all the files hold
    the same table; "file name", the files with the same name (the files of a GTFS feed are always compared by
    name); "cycle N", the N resources of every edition in the same order; "resource", a table per resource;
    "one; apart NAME", one table apart from the files named. Different formats of the same data are not compared
    with each other (a shapefile cuts the names to ten characters). Several tables in one sheet or file (AI1) are
    tables of their own, compared with the table in the same place of the other files, not with each other. The
    order of the columns counts in CSV files and spreadsheets only. A file that is the same, byte for byte, as the
    file of another table of the dataset, and whose columns differ from the other files of its own table, is a
    wrong file and is left out. A table whose header row looks like a record (its names read as numbers or dates
    like the values below them: a decimal number, or a serial number that the first record continues) keeps the
    position of its columns only and is left out of the comparison, for the manual look.
  - Recorded without a score: scientific notation in some values of a column (a valid way of writing a number,
    read by every program), the same value written in different ways (case, accents, spaces or punctuation), rows
    of a CSV file with fewer fields than the header, a header row that looks like a record.
  - Manual look: ten random records of every dataset (Q3_SAMPLE), the same in every run (at least one from every
    table; for the same data in several formats, the same records from each format), and up to three rows for
    every finding are written to the local review file review/sample_records_YYYY-MM-DD.xlsx.
  - Datasets without a data file: as in Q2.

Rules of Q4 (DECISIONS.md #41):
  - All the data files of the dataset count, as in Q3; the shares are shares of all their records.
  - Coordinates must lie inside Greece: in degrees (WGS84) latitude 34.5 to 42.0 and longitude 19.0 to 30.0; in
    the Greek Grid (EGSA87, EPSG:2100) x 40,000 to 1,052,000 and y 3,815,000 to 4,670,000 (the same box
    transformed; Kastellorizo lies at x 1,003,000 to 1,009,000). The system of a
    geospatial file is its declaration (.prj, the crs member of GeoJSON, which defaults to WGS84; KML and GTFS are
    WGS84 by their standards); the system of a column is read from its name (latitude, longitude, lat, lng, stop_lat
    mean degrees; X_EGSA87 means the Greek Grid). A bare X or Y without a declared system is accepted when its
    values fall in one of the two known ranges, and noted (for AI6); otherwise its values are outside Greece. The
    geometries of shapefiles, GeoJSON and KML are checked by their bounding boxes.
  - Dates must not be later than the date on which the file was downloaded (the download log; the date of the file
    for a file downloaded by hand), not before 1800, and must exist (no 30/02). Columns of an end, validity or
    planned date (end_date, feed_end_date, "Διάρκεια ισχύος") may lie in the future and are not checked; the dates
    of a GTFS schedule may lie in the future. Year columns (Έτος, year) must lie between 1800 and the year
    of the download. Time stamps yyyyMMddHHmm are dates.
  - Quantities recognised by the name of their column (counts, amounts, prices, values, areas, weights,
    capacities) must not be negative; differences, changes, balances, percentages, rates and indices are not
    checked. Weather elements,
    recognised by their names, must lie in their physical range: temperature -50 to 50 °C, relative humidity 0 to
    100 %, rainfall, wind speed and radiation not negative, wind direction 0 to 360, pressure 700 to 1,070 hPa
    (the standard atmosphere gives 708 hPa at the summit of Olympus, 2,918 m, far above every station of the
    country; the highest pressure ever recorded in Europe is 1,067 hPa).
  - Records identical to an earlier record of the same table, in all their values (for the features of a
    geospatial file, their geometry included), are duplicates; editions of a series are not compared with each
    other.
  - Rows of a CSV file with more fields than the header (values shifted between columns, Q3) are implausible
    records.
  - Outliers that look like typing errors are not judged automatically (a test on the sample marked thousands of
    legitimate large values); they are left to the manual look at the random sample, which is shared with Q3.
  - Score: 2 without implausible values in the range checks (and in the manual look); 1 for isolated implausible
    values, below 1% of the records; 0 from 1% of the records (systematic), or when no file can be opened.
  - Datasets without a data file: as in Q2.

Rules of AI6 (DECISIONS.md #42):
  - All the data files of the dataset are examined and the best counts: one file with a standard key makes the
    dataset linkable.
  - A reference system is declared when the file or its standard states it: a .prj file, the crs member of GeoJSON
    (WGS84 by the GeoJSON standard when absent), KML and GTFS (WGS84 by their standards), or a column whose name
    states the system (X_EGSA87). Latitude and longitude in degrees without any declaration, and a bare X or Y,
    are coordinates without a declared system.
  - Standard codes are those defined outside the publisher and used by many: KAEK cadastral codes, Kallikratis
    codes, NUTS and LAU codes, KAD/NACE activity codes, tax numbers (AFM), GEMI numbers, ADA codes of Diavgeia,
    Natura 2000 site codes, Corine Land Cover codes, COICOP codes, postal codes, KAE budget codes, the specialty
    codes of teachers and the codes of the national registry of water abstraction points (EMSY). They are
    recognised by the name of the column and, for the first KEY_SAMPLE records, by the form of the values; the
    codes of Diavgeia, of Natura 2000, of NUTS and of teacher specialties are recognised by their form alone.
  - Codes that only the publisher defines (serial numbers, protocol numbers, file numbers, the ids of stops,
    routes and sensors) are internal codes; places, bodies and stations given by their names are names.
  - Map services (WMS) are judged by the reference systems that their capabilities document declares; documents
    are estimated by inspection; datasets without a data file as in Q2.
  - Score: 2 with a standard code or coordinates in a declared system in any file; 1 with names, internal codes or
    coordinates without a declared system only; 0 without any of them.

Usage (from the project root, with the .venv activated):
    python scripts\06_file_checks.py                  all datasets of the sample
    python scripts\06_file_checks.py --only S06 S24   some datasets only (test run)

RAR archives are opened with the tar program of the operating system (included in Windows 10 and later).

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import codecs
import csv
import datetime
import heapq
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import warnings
import zipfile
import zlib
from array import array
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import openpyxl
import rdflib
import shapefile
import xlrd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = ROOT / "data" / "raw" / "resources"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
REVIEW_DIR = ROOT / "review"          # local review files, ignored by git (.gitignore): they may contain records
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
ORGANISATION_FILE = ROOT / "criteria" / "file_organisation.csv"
DATASET_URL = "https://data.gov.gr/dataset/"

# Datasets that seem to contain personal data (DECISIONS.md #29, #36, #38 and #40): their column names are not written
# (S24: names of owners; S29: the columns are named after shops, some after their owners).
PERSONAL_DATA_SUSPECTED = {"S24", "S29"}

TABLE_TYPES = {"text", "xlsx", "ole2"}
PARSED_TYPES = {"json", "xml", "turtle", "kmz"}
ARCHIVE_TYPES = {"shapefile", "gtfs", "zip", "rar"}
DATA_TYPES = TABLE_TYPES | PARSED_TYPES | ARCHIVE_TYPES
CAPABILITIES_ROOTS = {"wms_capabilities", "wmt_ms_capabilities", "wfs_capabilities", "capabilities",
                      "serviceexceptionreport", "exceptionreport"}
SYSTEM_FILES = {"thumbs.db", "ehthumbs.db", "desktop.ini"}   # files that Windows adds to folders
SHAPEFILE_PARTS = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".qpj", ".qix", ".fix", ".aih", ".ain",
                   ".atx", ".ixs", ".mxs"}

SIGNATURES = [
    (b"%PDF", "pdf"), (b"PK\x03\x04", "zip"), (b"PK\x05\x06", "zip"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "ole2"), (b"Rar!\x1a\x07", "rar"), (b"\x1f\x8b", "gzip"),
    (b"7z\xbc\xaf\x27\x1c", "7z"), (b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"), (b"II*\x00", "tiff"), (b"MM\x00*", "tiff"),
]
TEXT_ENCODINGS = ("utf-8", "cp1253", "iso-8859-7")
DELIMITERS = ",;\t|"
CODE_PAGES = {"utf-8": "utf-8", "utf8": "utf-8", "1253": "cp1253", "cp1253": "cp1253", "ansi 1253": "cp1253",
              "windows-1253": "cp1253", "8859_7": "iso-8859-7", "iso-8859-7": "iso-8859-7", "iso88597": "iso-8859-7",
              "737": "cp737", "cp737": "cp737", "1252": "cp1252", "ansi 1252": "cp1252", "cp1252": "cp1252"}

TOTAL_WORDS = re.compile(r"^(γενικο\s+|γεν\.\s*)?(συνολ|αθροισμα)|^(grand\s+)?total\b|^ολικο\b")
SUMMARY_LABELS = re.compile(r"(μεγ(ιστ[οηα])?|ελ(αχιστ[οηα])?)( υψοσ| τιμη)?|μ ο|μεσ(οσ οροσ|η τιμη)|average|mean"
                            r"|max(imum)?|min(imum)?|sum")     # a whole label, so that "Μεγ. Αλεξάνδρου" does not count
NUMBER_TEXT = re.compile(r"^[+-]?(?:\d{1,3}(?:[.,\u00a0 ]\d{3})+|\d+)(?:[.,]\d+)?\s*%?$")
IDENTIFIER = re.compile(r"^(?:0\d+|\d{5,})$")
KEEP_TEXT_ROWS = 300          # rows at the start of a table whose values are kept for the header analysis
TOTAL, SINGLE_TEXT, EMPTY_RECORD, HAS_NUMBER = 1, 2, 4, 8     # flags of a row

# Empty cells for Q2 (DECISIONS.md #39): kinds of a cell, and the placeholders of a missing value.
VALUE, EMPTY, PLACEHOLDER = 0, 1, 2
HAS_LETTER_OR_DIGIT = re.compile(r"[^\W_]")
# Symbols that stand for a missing value: dashes, dots, colons, slashes, asterisks, question marks, hashes, tildes.
PLACEHOLDER_SYMBOLS = re.compile(r"[\s\-\u2010-\u2015\u2212_.\u2026\u00b7:;/\\|*?#~\ufffd]+")
MISSING_WORDS = {"n/a", "na", "n.a.", "null", "none", "nan", "δ/υ", "δ.υ.", "δ.υ"}
SPREADSHEET_ERRORS = re.compile(r"#(?:n/a|div/0!|ref!|value!|name\?|num!|null!|spill!|calc!|error)")
MISSING_NUMBERS = re.compile(r"-(?:999|9999)(?:[.,]0+)?")
PLACEHOLDER_START = set("nN#-δΔ")             # first characters of the words, error values and numbers above
GEOMETRY = "(geometry)"
GEOMETRY_KEY = ("", "geometry", GEOMETRY)
SCOPE_TABLE = "all columns of the records"
SCOPE_FEATURES = "all properties and the geometry of the features"
SCOPE_GTFS = "mandatory fields of the GTFS reference"
SCOPE_STIRDATA = "legal name and legal identifier of every legal entity (mandatory in the STIRData model)"

# Fields of the GTFS reference (gtfs.org/documentation/schedule/reference) that must always have a value. The fields
# that are required under a condition are counted in gtfs_tally(); fields whose empty value has a meaning in the
# reference (transfers of fare_attributes.txt, transfer_type of transfers.txt) are left out.
GTFS_REQUIRED = {
    "agency.txt": ["agency_name", "agency_url", "agency_timezone"],
    "stops.txt": ["stop_id"],
    "routes.txt": ["route_id", "route_type"],
    "trips.txt": ["route_id", "service_id", "trip_id"],
    "stop_times.txt": ["trip_id", "stop_sequence"],
    "calendar.txt": ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                     "start_date", "end_date"],
    "calendar_dates.txt": ["service_id", "date", "exception_type"],
    "fare_attributes.txt": ["fare_id", "price", "currency_type", "payment_method"],
    "fare_rules.txt": ["fare_id"],
    "shapes.txt": ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
    "frequencies.txt": ["trip_id", "start_time", "end_time", "headway_secs"],
    "transfers.txt": [],                          # from_stop_id and to_stop_id for transfer types 1 to 3
    "pathways.txt": ["pathway_id", "from_stop_id", "to_stop_id", "pathway_mode", "is_bidirectional"],
    "levels.txt": ["level_id", "level_index"],
    "feed_info.txt": ["feed_publisher_name", "feed_publisher_url", "feed_lang"],
    "translations.txt": ["table_name", "field_name", "language", "translation"],
    "attributions.txt": ["organization_name"],
}

PROFILE_FIELDS = [
    "sample_id", "position", "resource_id", "file", "member", "sheet", "kind", "data_file", "examined",
    "readable", "error", "rows", "columns", "header_row", "title_rows", "header_rows", "totals_rows",
    "subheading_rows", "notes_below", "merged_in_data", "tables", "numbers_as_text_columns", "extra_field_rows",
    "cells_beyond_header", "blank_rows_inside", "repeated_headers", "hidden", "encoding", "delimiter", "crs", "column_names",
    "ai1_score", "ai1_reason", "q2_scope", "q2_records", "q2_cells", "q2_missing", "q2_placeholders", "q2_share",
    "q2_columns", "q2_empty_columns", "q2_empty_column_names", "q2_placeholder_values", "q2_score", "q2_reason",
    "q2_notes", "q3_score", "q3_reason", "q4_score", "q4_reason",
]
CHECK_FIELDS = [
    "sample_id", "dataset", "organisation", "examined", "combine", "files_examined", "ai1_score", "ai1_reason",
    "decisive", "q2_score", "q2_reason", "q2_records", "q2_cells", "q2_missing", "q2_placeholders", "q2_share",
    "q2_empty_columns", "q2_decisive", "q2_notes", "q3_score", "q3_reason", "q3_major", "q3_minor", "q3_notes",
    "q4_score", "q4_reason", "q4_records", "q4_implausible", "q4_share", "q4_notes",
    "ai6_score", "ai6_reason", "ai6_keys", "ai6_notes",
]
KEY_FIELDS = ["sample_id", "where", "format", "column", "name", "kind", "key", "evidence"]
COLUMN_FIELDS = [
    "sample_id", "position", "member", "sheet", "scope", "column", "name", "cells", "empty", "placeholders", "share",
]
FORMAT_FIELDS = [
    "sample_id", "group", "format", "tables", "column", "name", "values", "kind", "forms", "units", "severity",
    "finding",
]
STRUCTURE_FIELDS = [
    "sample_id", "group", "format", "tables", "headers", "header", "count", "files", "columns", "names",
]
PLAUSIBILITY_FIELDS = [
    "sample_id", "where", "format", "column", "name", "role", "checked", "range", "implausible", "kinds", "notes",
]

csv.field_size_limit(2**31 - 1)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")   # headers and footers of print layouts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def normalise(text: str) -> str:
    """Lower case without accents, final sigma as sigma: for the recognition of words such as "Σύνολο"."""
    text = unicodedata.normalize("NFD", str(text).strip().lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").replace("ς", "σ")


def is_total(text: str) -> bool:
    """A label of a totals or summary row: it starts with a word such as "Σύνολο", or it is a whole label such as
    "Μέγιστο", "Μεγ. ύψος" or "Μ.Ο."."""
    words = normalise(text)
    if TOTAL_WORDS.match(words):
        return True
    return bool(SUMMARY_LABELS.fullmatch(" ".join(re.sub(r"[^\w]+", " ", words).split())))


def looks_numeric(text: str) -> bool:
    return bool(NUMBER_TEXT.match(text))


def number_text(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def detect_type(path: Path) -> str:
    """The type of a file from its first bytes, as in 05_resource_download.py, for the files inside archives and
    the files downloaded by hand."""
    with open(path, "rb") as handle:
        head = handle.read(65536)
    if not head:
        return "empty"
    for signature, kind in SIGNATURES:
        if head.startswith(signature):
            return zip_type(path) if kind == "zip" else kind
    text = None
    for encoding in ("utf-8-sig", "utf-16", "cp1253"):
        if encoding == "utf-16" and not head.startswith((b"\xff\xfe", b"\xfe\xff")):
            continue
        try:
            text = head.decode(encoding)
            break
        except UnicodeDecodeError as error:
            if encoding == "utf-8-sig" and error.start >= len(head) - 3:
                text = head[:error.start].decode(encoding, errors="ignore")
                break
    if text is None:
        return "unknown"
    start = text.lstrip("\ufeff \t\r\n")
    lower = start[:4096].lower()
    if re.match(r"<(?:https?|urn|ftp|file):", start, re.IGNORECASE) or start.startswith(("@prefix", "@base", "PREFIX")):
        return "turtle"
    if start.startswith("<"):
        return "html" if "<html" in lower or "<!doctype html" in lower else "xml"
    if start.startswith(("{", "[")):
        return "json"
    return "text"


def zip_type(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            lower = [name.lower() for name in archive.namelist()]
    except (zipfile.BadZipFile, OSError):
        return "zip"
    if "[content_types].xml" in lower and any(name.startswith("xl/") for name in lower):
        return "xlsx"
    if "[content_types].xml" in lower and any(name.startswith("word/") for name in lower):
        return "docx"
    if "mimetype" in lower:
        return "opendocument"
    if any(name.endswith(".kml") for name in lower):
        return "kmz"
    if {"stops.txt", "routes.txt"} <= {name.rsplit("/", 1)[-1] for name in lower}:
        return "gtfs"
    if any(name.endswith(".shp") for name in lower):
        return "shapefile"
    return "zip"


def text_encoding(path: Path) -> str:
    """The encoding of a text file, checked over the whole file: UTF-16 with a byte order mark, UTF-8, Greek
    Windows-1253 or ISO 8859-7; Latin-1 when none of them fits."""
    with open(path, "rb") as handle:
        head = handle.read(4)
    if head.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    for encoding in TEXT_ENCODINGS:
        decoder = codecs.getincrementaldecoder(encoding)()
        try:
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    decoder.decode(chunk)
                decoder.decode(b"", final=True)
            return "utf-8-sig" if encoding == "utf-8" else encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def delimiter_of(path: Path, encoding: str) -> tuple[str, float]:
    """The delimiter of a CSV file: the candidate that splits the first lines into the most constant number of
    fields, and the share of the first lines with that number of fields."""
    with open(path, encoding=encoding, errors="replace", newline="") as handle:
        sample = handle.read(65536)
    lines = [line for line in sample.splitlines()[:60] if line.strip()]
    if not lines:
        return ",", 0.0
    best, best_score = ",", -1.0
    for candidate in DELIMITERS:
        counts = [len(fields) for fields in csv.reader(lines, delimiter=candidate)]
        common, frequency = Counter(counts).most_common(1)[0]
        score = frequency / len(counts) if common > 1 else 0.0
        if score > best_score:
            best, best_score = candidate, score
    return best, best_score


def extract_archive(path: Path, kind: str, target: Path) -> str:
    """Extracts a ZIP or RAR archive into target: an empty string, or the error."""
    if kind == "rar":
        tool = shutil.which("tar")
        if not tool:
            return "no tar program to open the RAR archive"
        try:
            result = subprocess.run([tool, "-xf", str(path), "-C", str(target)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=1800)
        except (OSError, subprocess.TimeoutExpired) as error:
            return f"the RAR archive could not be opened: {type(error).__name__}"
        if result.returncode != 0:
            message = " ".join((result.stderr or "").split())[:150]
            return ("the RAR archive could not be opened with tar: " + message).strip()
        return ""
    try:
        with zipfile.ZipFile(path, metadata_encoding=zip_encoding(path)) as archive:
            archive.extractall(target)
    except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as error:
        return f"the archive could not be opened: {type(error).__name__}: {str(error)[:120]}"
    return ""


def zip_encoding(path: Path) -> str | None:
    """The code page of the names of a ZIP archive that do not carry the UTF-8 flag: Greek DOS (cp737) or Greek
    Windows (cp1253) when one of them gives Greek letters, otherwise the default of the ZIP format."""
    try:
        with zipfile.ZipFile(path) as archive:
            raw = [info.filename.encode("cp437") for info in archive.infolist() if not info.flag_bits & 0x800]
    except (zipfile.BadZipFile, OSError, UnicodeEncodeError):
        return None
    if all(name.isascii() for name in raw):
        return None
    best, best_count = None, 0
    for encoding in ("cp737", "cp1253"):
        count = sum(1 for name in raw for ch in name.decode(encoding, errors="replace") if "\u0386" <= ch <= "\u03ce")
        if count > best_count:
            best, best_count = encoding, count
    return best


def member_files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.rglob("*") if path.is_file() and "__MACOSX" not in path.parts
                  and not path.name.startswith(".") and path.name.lower() not in SYSTEM_FILES)


def relative_to(path: Path, folder: Path) -> str:
    return path.relative_to(folder).as_posix()


# ---------------------------------------------------------------------------
# Layout of a table
# ---------------------------------------------------------------------------

class Rows:
    """Summary of the rows of a table: number of values, number of fields, flags, and the values of the first
    rows for the header analysis. The values of the other rows are not kept."""

    def __init__(self) -> None:
        self.nonempty = array("I")
        self.nfields = array("I")
        self.flags = bytearray()
        self.texts: dict[int, list[str]] = {}
        self._after_blank = 0           # the first rows after an empty row are kept too, for the second tables

    def __len__(self) -> int:
        return len(self.nonempty)

    def _store(self, filled: list[int], flags: int, values: list[str]) -> None:
        index = len(self.nonempty)
        self.nonempty.append(len(filled))
        self.nfields.append(filled[-1] + 1 if filled else 0)
        self.flags.append(flags)
        if not filled:
            self._after_blank = 3
        elif index < KEEP_TEXT_ROWS or self._after_blank:
            self.texts[index] = [value[:120] for value in values]
            self._after_blank = max(0, self._after_blank - 1)

    def add_text(self, values: list[str]) -> None:
        """A row of a CSV file: every value is text; numbers are told apart only where it matters."""
        filled = [j for j, value in enumerate(values) if value]
        flags = EMPTY_RECORD if values and not filled else 0     # a line of delimiters only is an empty record
        words = [values[j] for j in filled[:3] if not looks_numeric(values[j])][:2]
        if any(is_total(word) for word in words):
            flags |= TOTAL
        if len(filled) == 1 and not looks_numeric(values[filled[0]]):
            flags |= SINGLE_TEXT
        if any(looks_numeric(values[j]) for j in filled[:6]):
            flags |= HAS_NUMBER
        self._store(filled, flags, values)

    def add_typed(self, values: list[str], kinds: list[str]) -> None:
        """A row of a sheet: the type of every cell is known."""
        filled = [j for j, kind in enumerate(kinds) if kind != "empty"]
        flags = 0 if filled else EMPTY_RECORD                     # an empty row of a sheet is an empty record
        words = [values[j] for j in filled if kinds[j] == "text"][:2]
        if any(is_total(word) for word in words):
            flags |= TOTAL
        if len(filled) == 1 and kinds[filled[0]] == "text":
            flags |= SINGLE_TEXT
        if any(kinds[j] in ("number", "date") for j in filled):
            flags |= HAS_NUMBER
        self._store(filled, flags, [value if kind != "empty" else "" for value, kind in zip(values, kinds)])


def two_row_header(rows: Rows, header: int, merged: list[tuple[int, int, int, int]]) -> bool:
    """A header over two rows: a merged cell in the header row that spans several columns or rows, or a header row
    with gaps that the next row fills while its first column stays empty."""
    for first_row, last_row, first_col, last_col in merged:
        if first_row <= header <= last_row and (last_col > first_col or last_row > first_row):
            return True
    top, below = rows.texts.get(header), rows.texts.get(header + 1)
    if not top or not below:
        return False
    filled = [j for j, value in enumerate(top) if value]
    if not filled:
        return False
    gaps = [j for j in range(filled[0], filled[-1] + 1) if not top[j]]
    first_empty = filled[0] >= len(below) or not below[filled[0]]
    return bool(gaps) and first_empty and any(j < len(below) and below[j] for j in gaps)


def analyse(rows: Rows, merged: list[tuple[int, int, int, int]] | None = None, csv_file: bool = False) -> dict:
    """The layout of a table: header, title rows, totals, sub-headings, notes, merged cells, second tables."""
    merged = merged or []
    count, nonempty = len(rows), rows.nonempty
    blocks, start = [], None
    for index in range(count):
        if nonempty[index] and start is None:
            start = index
        elif not nonempty[index] and start is not None:
            blocks.append((start, index - 1))
            start = None
    if start is not None:
        blocks.append((start, count - 1))

    def wide(block: tuple[int, int]) -> int:
        return sum(1 for index in range(block[0], block[1] + 1) if nonempty[index] >= 2)

    tables = [block for block in blocks if wide(block) >= 2]
    if not tables:
        return {"table": False}
    main = max(tables, key=wide)
    widths = Counter(nonempty[index] for index in range(main[0], main[1] + 1) if nonempty[index] >= 2)
    width = widths.most_common(1)[0][0]
    threshold = max(2, (width + 1) // 2)
    header = next(index for index in range(main[0], main[1] + 1) if nonempty[index] >= threshold)
    header_end = header + 1 if header + 1 <= main[1] and two_row_header(rows, header, merged) else header
    header_fields = max(rows.nfields[header], rows.nfields[header_end])

    main_data = [index for index in range(header_end + 1, main[1] + 1) if nonempty[index]]
    numeric = sum(1 for index in main_data if rows.flags[index] & HAS_NUMBER) * 2 >= max(1, len(main_data))
    header_key = [normalise(value) for value in rows.texts.get(header, []) if value]
    others, continued, repeated_rows = [], [], []
    for block in blocks:
        if block == main:
            continue
        filled = [index for index in range(block[0], block[1] + 1) if nonempty[index]]
        wide_rows = [index for index in filled if nonempty[index] >= 2]
        summary = sum(1 for index in filled if rows.flags[index] & TOTAL) * 2 >= len(filled)
        if len(wide_rows) < 3:
            if block[0] > main[1] and summary:
                continued.append(block)         # summary rows of the table after empty rows
            continue                            # otherwise title rows above or note rows below
        narrower = Counter(nonempty[index] for index in wide_rows).most_common(1)[0][0] < threshold
        if block[1] < main[0]:
            if not narrower:
                others.append(block)            # a table above the table
            continue                            # otherwise title or note rows above the header
        if summary:
            continued.append(block)
            continue
        if narrower:
            continue                            # note rows below the table
        if any(rows.nfields[index] > header_fields for index in wide_rows):
            others.append(block)                # a wider table
            continue
        first = wide_rows[0]
        titled = any(rows.flags[index] & SINGLE_TEXT for index in filled if index < first)
        same_header = [normalise(value) for value in rows.texts.get(first, []) if value] == header_key
        if titled and (same_header or (numeric and not rows.flags[first] & HAS_NUMBER)):
            others.append(block)                # a table with a title and a header of its own
        elif same_header:
            continued.append(block)             # the table goes on after a repeated header
            repeated_rows.append(first)
        else:
            continued.append(block)             # the same table after empty rows
    repeated = len(repeated_rows)
    other_rows = {index for block in others for index in range(block[0], block[1] + 1)}
    last_data = max([main[1]] + [block[1] for block in continued])
    data = [index for index in range(header_end + 1, last_data + 1) if nonempty[index] and index not in other_rows]
    blank_inside = sum(1 for index in range(header_end + 1, last_data) if rows.flags[index] & EMPTY_RECORD)
    title_rows = sum(1 for index in range(0, header) if nonempty[index] and index not in other_rows)
    notes_below = sum(1 for index in range(last_data + 1, count) if nonempty[index] and index not in other_rows)
    totals = sum(1 for index in data if rows.flags[index] & TOTAL)
    subheadings = sum(1 for index in data if width >= 3 and nonempty[index] == 1 and rows.flags[index] & SINGLE_TEXT
                      and not rows.flags[index] & TOTAL)
    merged_in_data = sum(1 for first_row, last_row, _, _ in merged if last_row > header_end and first_row <= main[1])
    beyond = sum(1 for index in data if nonempty[index] >= 2 and rows.nfields[index] > header_fields)
    names = [value for value in rows.texts.get(header, []) if value]
    if header_end > header:
        names += [value for value in rows.texts.get(header_end, []) if value]
    records = sum(1 for index in data if nonempty[index]) - totals - subheadings - repeated

    # The records of every table for Q2: mask[row] is 1 for a record of the table, 2 and above for a record of a
    # second table, 0 for any other row (title, header, totals, sub-heading, repeated header, empty, note).
    mask = bytearray(count)
    skipped = set(repeated_rows)
    for index in data:
        if not (rows.flags[index] & TOTAL or index in skipped
                or (width >= 3 and nonempty[index] == 1 and rows.flags[index] & SINGLE_TEXT)):
            mask[index] = 1
    parts = [{"header": header, "header_end": header_end, "fields": header_fields}]
    for block in sorted(others)[:250]:
        filled = [index for index in range(block[0], block[1] + 1) if nonempty[index]]
        block_width = Counter(nonempty[index] for index in filled if nonempty[index] >= 2).most_common(1)[0][0]
        block_header = next(index for index in filled if nonempty[index] >= max(2, (block_width + 1) // 2))
        parts.append({"header": block_header, "header_end": block_header, "fields": rows.nfields[block_header]})
        for index in filled:
            if index > block_header and not (rows.flags[index] & TOTAL or (block_width >= 3 and nonempty[index] == 1
                                                                            and rows.flags[index] & SINGLE_TEXT)):
                mask[index] = len(parts)
    return {
        "table": True, "header": header, "header_end": header_end, "data": data, "width": width,
        "title_rows": title_rows, "header_rows": header_end - header + 1, "totals_rows": totals,
        "subheading_rows": subheadings, "notes_below": notes_below, "merged_in_data": merged_in_data,
        "tables": 1 + len(others), "extra_field_rows": beyond if csv_file else 0,
        "cells_beyond_header": 0 if csv_file else beyond, "blank_rows_inside": blank_inside, "rows": records,
        "repeated_headers": repeated,
        "columns": header_fields, "names": names, "parts": parts, "mask": mask,
    }


def table_score(layout: dict, numbers_as_text: int = 0, container: str = "sheet") -> tuple[int, str]:
    """AI1 of one table from its layout."""
    zero, one = [], []
    if layout["tables"] > 1:
        zero.append(f"{layout['tables']} tables in one {container}")
    if layout["merged_in_data"]:
        zero.append(f"merged cells inside the data ({layout['merged_in_data']})")
    if layout["extra_field_rows"]:
        zero.append(f"{layout['extra_field_rows']} rows with values beyond the columns of the header"
                    if layout["extra_field_rows"] > 1 else "1 row with values beyond the columns of the header")
    if layout["title_rows"]:
        one.append(f"{layout['title_rows']} title or note rows above the header" if layout["title_rows"] > 1
                   else "1 title or note row above the header")
    if layout["header_rows"] > 1:
        one.append("header over two rows")
    if layout["blank_rows_inside"]:
        one.append(f"{layout['blank_rows_inside']} empty rows inside the table" if layout["blank_rows_inside"] > 1
                   else "1 empty row inside the table")
    if layout["repeated_headers"]:
        one.append(f"{layout['repeated_headers']} repeated header rows inside the table" if layout["repeated_headers"] > 1
                   else "1 repeated header row inside the table")
    if layout["totals_rows"]:
        one.append(f"{layout['totals_rows']} totals rows" if layout["totals_rows"] > 1 else "1 totals row")
    if layout["subheading_rows"]:
        one.append(f"{layout['subheading_rows']} sub-heading rows inside the table" if layout["subheading_rows"] > 1
                   else "1 sub-heading row inside the table")
    if layout["notes_below"]:
        one.append(f"{layout['notes_below']} note rows below the table" if layout["notes_below"] > 1
                   else "1 note row below the table")
    if numbers_as_text:
        one.append(f"numbers stored as text in {numbers_as_text} columns" if numbers_as_text > 1
                   else "numbers stored as text in 1 column")
    if zero:
        return 0, "; ".join(zero + one)
    if one:
        return 1, "; ".join(one)
    return 2, "one header row, one record per row"


# ---------------------------------------------------------------------------
# Empty cells (Q2)
# ---------------------------------------------------------------------------

def missing_kind(text: str) -> int:
    """VALUE, EMPTY (nothing or only spaces) or PLACEHOLDER (only symbols that stand for a missing value, a word for
    a missing value, an error value of a spreadsheet, -999 or -9999) for the text of a cell. A unit or currency sign
    on its own, such as "%", "°" or "€", is a value."""
    text = text.strip()
    if not text:
        return EMPTY
    if not HAS_LETTER_OR_DIGIT.search(text):
        return PLACEHOLDER if PLACEHOLDER_SYMBOLS.fullmatch(text) else VALUE
    if len(text) <= 14 and text[0] in PLACEHOLDER_START:
        lower = text.lower()
        if lower in MISSING_WORDS or SPREADSHEET_ERRORS.fullmatch(lower) or MISSING_NUMBERS.fullmatch(text):
            return PLACEHOLDER
    return VALUE


def value_kind(value) -> int:
    """The kind of a value read from JSON, GeoJSON, a shapefile or RDF."""
    if value is None:
        return EMPTY
    if isinstance(value, str):
        return missing_kind(value)
    if isinstance(value, bool):
        return VALUE
    if isinstance(value, (int, float)):
        return PLACEHOLDER if value != value or value in (-999, -9999) else VALUE     # NaN, -999, -9999
    if isinstance(value, (list, dict)):
        return VALUE if value else EMPTY
    return VALUE


def geometry_kind(geometry) -> int:
    """A GeoJSON geometry: EMPTY when the feature has no geometry or no coordinates."""
    if not isinstance(geometry, dict):
        return EMPTY
    if geometry.get("type") == "GeometryCollection":
        return VALUE if geometry.get("geometries") else EMPTY
    return VALUE if geometry.get("coordinates") not in (None, [], "") else EMPTY


def column_key(name: str) -> str:
    """Columns of different tables or parts with the same name, apart from case, accents, spaces and punctuation,
    are the same column."""
    return re.sub(r"[\W_]+", "", normalise(name))


class Tally:
    """The cells of the records that Q2 counts in a table or a file, per column: [name, cells, empty, placeholders].
    The values themselves are not kept, only the texts of the placeholders."""

    def __init__(self, scope: str) -> None:
        self.scope = scope
        self.records = 0
        self.columns: dict = {}
        self.tokens: Counter = Counter()
        self.notes: list[str] = []

    def add(self, key, name: str, cells: int, empty: int, placeholders: int) -> None:
        entry = self.columns.setdefault(key, [name, 0, 0, 0])
        entry[1] += cells
        entry[2] += empty
        entry[3] += placeholders

    def add_columns(self, names: list[str], cells: list[int], empty: list[int], placeholders: list[int],
                    prefix: str = "") -> None:
        """The columns of one table: a column without a name and without any value is not a column."""
        used = set()
        for index, name in enumerate(names):
            if not name and empty[index] + placeholders[index] >= cells[index]:
                continue
            key = (prefix, column_key(name)) if name and column_key(name) else ("#", id(self), index)
            if key in used:
                key = key + (index,)
            used.add(key)
            self.add(key, name or f"(column {index + 1})", cells[index], empty[index], placeholders[index])

    def merge(self, other: "Tally") -> None:
        self.records += other.records
        for key, (name, cells, empty, placeholders) in other.columns.items():
            self.add(key, name, cells, empty, placeholders)
        self.tokens.update(other.tokens)
        self.notes += [note for note in other.notes if note not in self.notes]
        if other.scope != self.scope and other.scope not in self.scope:
            self.scope = f"{self.scope}; {other.scope}"

    @property
    def cells(self) -> int:
        return sum(entry[1] for entry in self.columns.values())

    @property
    def missing(self) -> int:
        return sum(entry[2] + entry[3] for entry in self.columns.values())

    @property
    def placeholders(self) -> int:
        return sum(entry[3] for entry in self.columns.values())

    def empty_columns(self) -> list[str]:
        return [name for name, cells, empty, placeholders in self.columns.values()
                if cells and empty + placeholders >= cells]

    def share(self) -> float:
        return self.missing / self.cells if self.cells else 1.0


def tally_from_counts(scope: str, names: list[str], records: int, empty: list[int], placeholders: list[int],
                      tokens: Counter, prefix: str = "") -> Tally:
    tally = Tally(scope)
    tally.records = records
    tally.add_columns(names, [records] * len(names), empty, placeholders, prefix)
    tally.tokens = tokens
    return tally


def q2_score(tally: Tally) -> tuple[int, str]:
    """Q2 from the counted cells: share of empty cells and columns without any value."""
    cells, missing = tally.cells, tally.missing
    if not cells:
        return 0, "no records to count"
    empty_columns = tally.empty_columns()
    if missing * 100 > 20 * cells:
        score = 0
    elif missing * 100 >= 5 * cells or empty_columns:
        score = 1
    else:
        score = 2
    return score, ""


def q2_text(tally: Tally, personal: bool) -> str:
    """The reason of a score of Q2, without values of the data: counts, placeholders and the names of the columns
    without any value (not for the datasets that may contain personal data)."""
    cells, missing, placeholders = tally.cells, tally.missing, tally.placeholders
    if not cells:
        return "no records to count"
    text = f"{100 * missing / cells:.2f}% of {cells:,} cells empty"
    if placeholders:
        shown = ", ".join(f"'{token[:12]}' {count:,}" for token, count in tally.tokens.most_common(3))
        text += f" ({placeholders:,} of them placeholders: {shown})"
    empty_columns = tally.empty_columns()
    if empty_columns:
        text += f"; {len(empty_columns)} column{'s' if len(empty_columns) > 1 else ''} without any value"
        if not personal:
            text += ": " + ", ".join(empty_columns[:8]) + (", …" if len(empty_columns) > 8 else "")
    else:
        text += "; no column without any value"
    return text


def part_names(rows: Rows, part: dict, cells: dict | None = None) -> list[str]:
    """The names of the columns of a table from its header rows (two rows joined)."""
    names = []
    for column in range(part["fields"]):
        words = []
        for index in dict.fromkeys((part["header"], part["header_end"])):
            if cells is not None:
                kind, value = cells.get(index, {}).get(column, ("empty", ""))
                value = value if kind != "empty" else ""
            else:
                values = rows.texts.get(index, [])
                value = values[column] if column < len(values) else ""
            if value:
                words.append(value)
        names.append(" ".join(words))
    return names


def csv_tally(path: Path, encoding: str, delimiter: str, rows: Rows, layout: dict,
              formats_out: list | None = None) -> Tally:
    """The empty cells of the records of a CSV file, read a second time: only the rows that the layout marks as
    records count, in the columns of their header. With formats_out, the forms of the values of every table of the
    file are collected for Q3 in the same reading."""
    parts, mask = layout["parts"], layout["mask"]
    names = [part_names(rows, part) for part in parts]
    skip_first = names[0][:1] == ["_id"]          # the column that the DataStore of the portal adds
    widths = [part["fields"] for part in parts]
    records = [0] * len(parts)
    empty = [[0] * width for width in widths]
    placeholders = [[0] * width for width in widths]
    tokens: Counter = Counter()
    formats, starts, named = None, [0] * len(parts), [0] * len(parts)
    if formats_out is not None:
        formats = []
        for number, part in enumerate(parts):
            starts[number] = 1 if number == 0 and skip_first else 0
            part_list = names[number][starts[number]:widths[number]]
            named[number] = starts[number] + max((index + 1 for index, name in enumerate(part_list) if name), default=0)
            formats.append(Formats(part_list, typed=False, family="csv"))
        formats_out += formats
    with open(path, encoding=encoding, errors="replace", newline="") as handle:
        for index, fields in enumerate(csv.reader(handle, delimiter=delimiter)):
            number = mask[index] if index < len(mask) else 0
            if not number:
                continue
            part = number - 1
            records[part] += 1
            row_empty, row_placeholders = empty[part], placeholders[part]
            length = len(fields)
            for column in range(widths[part]):
                if column >= length:
                    row_empty[column] += 1
                    continue
                kind = missing_kind(fields[column])
                if kind == EMPTY:
                    row_empty[column] += 1
                elif kind == PLACEHOLDER:
                    row_placeholders[column] += 1
                    if len(tokens) < 50 or fields[column].strip() in tokens:
                        tokens[fields[column].strip()] += 1
            if formats is not None:
                table = formats[part]
                if length < named[part]:
                    table.short_rows += 1
                table.add_texts(index + 1, fields[starts[part]:widths[part]])
    tally = Tally(SCOPE_TABLE)
    tally.tokens = tokens
    for part in range(len(parts)):
        part_names_list, width = names[part], widths[part]
        start = 1 if part == 0 and skip_first else 0
        tally.records += records[part]
        tally.add_columns(part_names_list[start:width], [records[part]] * (width - start), empty[part][start:width],
                          placeholders[part][start:width])
    return tally


def sheet_tally(cells: dict, merged: list, rows: Rows, layout: dict, formats_out: list | None = None,
                dates: dict | None = None) -> Tally:
    """The empty cells of the records of a sheet. A merged cell counts with its value over all the cells it covers.
    With formats_out, the forms of the values of every table of the sheet are collected for Q3 (dates: the texts of
    the date cells, for the local review file)."""
    covered = {}
    for first_row, last_row, first_col, last_col in merged:
        if (last_row - first_row + 1) * (last_col - first_col + 1) > 1_000_000:
            continue
        for row in range(first_row, last_row + 1):
            for column in range(first_col, last_col + 1):
                if (row, column) != (first_row, first_col):
                    covered[(row, column)] = (first_row, first_col)
    parts, mask = layout["parts"], layout["mask"]
    dates = dates or {}
    tally = Tally(SCOPE_TABLE)
    for number, part in enumerate(parts, start=1):
        width = part["fields"]
        records, empty, placeholders = 0, [0] * width, [0] * width
        names = part_names(rows, part, cells)
        formats = None
        if formats_out is not None:
            formats = Formats(names, typed=True, family="spreadsheet")
            formats_out.append(formats)
        for index in range(len(mask)):
            if mask[index] != number:
                continue
            records += 1
            row = cells.get(index, {})
            values = []
            for column in range(width):
                found, place = row.get(column), (index, column)
                if found is None and (index, column) in covered:
                    place = covered[(index, column)]
                    found = cells.get(place[0], {}).get(place[1])
                if found is None:
                    empty[column] += 1
                    values.append(("empty", ""))
                    continue
                kind_name, value = found
                values.append(("date", dates.get(place, "")) if kind_name == "date" else found)
                if kind_name == "text":
                    kind = missing_kind(value)
                elif kind_name == "number":
                    kind = PLACEHOLDER if MISSING_NUMBERS.fullmatch(value) else VALUE
                else:
                    kind = VALUE
                if kind == EMPTY:
                    empty[column] += 1
                elif kind == PLACEHOLDER:
                    placeholders[column] += 1
                    tally.tokens[value.strip()] += 1
            if formats is not None:
                formats.add_cells(index + 1, values)
        tally.records += records
        tally.add_columns(names, [records] * width, empty, placeholders)
    return tally


def gtfs_tally(path: Path, encoding: str, delimiter: str, table: str, formats_out: list | None = None) -> Tally | None:
    """The empty cells of the mandatory fields of a file of a GTFS feed (DECISIONS.md #39). None for a file that is
    not part of the GTFS reference. With formats_out, the header, the random sample and the values of the fields
    whose format the reference defines (Q3) are collected in the same reading."""
    if not GTFS_REQUIRED.get(table) and table != "transfers.txt":
        if formats_out is not None:
            with open(path, encoding=encoding, errors="replace", newline="") as handle:
                header = next(csv.reader(handle, delimiter=delimiter), None) or []
            formats_out.append(Formats([name.strip().lstrip("﻿").strip() for name in header], typed=False,
                                       family="gtfs"))
        return None
    tally = Tally(SCOPE_GTFS)
    counts: dict[str, list[int]] = {}            # field -> [cells, empty, placeholders]

    def count(field: str, value: str) -> int:
        entry = counts.setdefault(field, [0, 0, 0])
        entry[0] += 1
        kind = missing_kind(value)
        if kind == EMPTY:
            entry[1] += 1
        elif kind == PLACEHOLDER:
            entry[2] += 1
            tally.tokens[value.strip()] += 1
        return kind

    trips: dict[str, list] = {}         # trip_id -> [first sequence, kind of its arrival, last sequence, kind]
    with open(path, encoding=encoding, errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, None) or []
        names = [name.strip().lstrip("\ufeff").strip().lower() for name in header]
        position = {name: index for index, name in enumerate(names) if name}

        def cell(fields: list[str], name: str) -> str:
            index = position.get(name)
            return fields[index].strip() if index is not None and index < len(fields) else ""

        required = GTFS_REQUIRED[table]
        for field in required:
            counts.setdefault(field, [0, 0, 0])
        formats, checks = None, []
        if formats_out is not None:
            formats = Formats([name.strip().lstrip("﻿").strip() for name in header], typed=False, family="gtfs")
            formats_out.append(formats)
            for field, rule in GTFS_FORMATS.get(table, {}).items():
                if field in position:
                    entry = [0, 0, rule, []]
                    formats.gtfs[f"{table}: {field}"] = entry
                    checks.append((position[field], GTFS_RULES[rule][0], entry, {}))
        for line, fields in enumerate(reader, start=2):
            if not any(value.strip() for value in fields):
                continue                          # an empty line or an empty record: layout, judged under AI1
            if formats is not None:
                formats.add_sample(line, fields)
                for index, pattern, entry, cache in checks:
                    value = fields[index].strip() if index < len(fields) else ""
                    if not value:
                        continue
                    state = cache.get(value)      # 0: placeholder (Q2), 1: in the format, 2: not in the format
                    if state is None:
                        state = 0 if missing_kind(value) != VALUE else 1 if pattern.fullmatch(value) else 2
                        if len(cache) < 100_000:
                            cache[value] = state
                    if state:
                        entry[0] += 1
                        if state == 2:
                            entry[1] += 1
                            if len(entry[3]) < Q3_EXAMPLES:
                                entry[3].append((line, index, short_text(value)))
            tally.records += 1
            for field in required:
                count(field, cell(fields, field))
            if table == "stops.txt":
                location = cell(fields, "location_type")
                if location in ("", "0", "1", "2"):
                    for field in ("stop_name", "stop_lat", "stop_lon"):
                        count(field, cell(fields, field))
                if location in ("2", "3", "4"):
                    count("parent_station", cell(fields, "parent_station"))
            elif table == "transfers.txt":
                if cell(fields, "transfer_type") in ("1", "2", "3"):
                    count("from_stop_id", cell(fields, "from_stop_id"))
                    count("to_stop_id", cell(fields, "to_stop_id"))
            elif table == "routes.txt":
                short_name = cell(fields, "route_short_name")
                count("route_short_name or route_long_name",
                      short_name if missing_kind(short_name) == VALUE else cell(fields, "route_long_name"))
            elif table == "stop_times.txt":
                if not cell(fields, "location_group_id") and not cell(fields, "location_id"):
                    count("stop_id", cell(fields, "stop_id"))
                arrival = cell(fields, "arrival_time")
                timepoint = cell(fields, "timepoint") == "1"
                if timepoint:
                    count("arrival_time", arrival)
                    count("departure_time", cell(fields, "departure_time"))
                trip, sequence = cell(fields, "trip_id"), cell(fields, "stop_sequence")
                if trip and sequence.isdigit():
                    value = int(sequence)
                    kind = None if timepoint else missing_kind(arrival)     # None: already counted at a timepoint
                    entry = trips.get(trip)
                    if entry is None:
                        trips[trip] = [value, kind, value, kind]
                    else:
                        if value < entry[0]:
                            entry[0], entry[1] = value, kind
                        if value > entry[2]:
                            entry[2], entry[3] = value, kind
    for first, first_kind, last, last_kind in trips.values():
        ends = [first_kind] if first == last else [first_kind, last_kind]
        for kind in ends:
            if kind is None:
                continue
            entry = counts.setdefault("arrival_time", [0, 0, 0])
            entry[0] += 1
            entry[1] += kind == EMPTY
            entry[2] += kind == PLACEHOLDER
    for field, (cells, empty, placeholders) in counts.items():
        if cells or field in GTFS_REQUIRED[table]:
            tally.add(("gtfs", table, field), f"{table}: {field}", cells, empty, placeholders)
    return tally


def records_tally(records: list, scope: str = SCOPE_TABLE) -> Tally:
    """The empty cells of a list of JSON objects: one column per key; a missing key is an empty cell."""
    objects = [item for item in records if isinstance(item, dict)]
    keys = list(dict.fromkeys(str(key) for item in objects for key in item))
    empty, placeholders = [0] * len(keys), [0] * len(keys)
    tokens: Counter = Counter()
    for item in objects:
        values = {str(key): value for key, value in item.items()}
        for index, key in enumerate(keys):
            value = values.get(key)
            kind = value_kind(value) if key in values else EMPTY
            if kind == EMPTY:
                empty[index] += 1
            elif kind == PLACEHOLDER:
                placeholders[index] += 1
                tokens[str(value).strip()[:12]] += 1
    return tally_from_counts(scope, keys, len(objects), empty, placeholders, tokens)


def features_tally(features: list) -> Tally:
    """The empty cells of the features of a GeoJSON file: the properties and the geometry."""
    objects = [feature for feature in features if isinstance(feature, dict)]
    rows = [dict(feature.get("properties") or {}) for feature in objects]
    tally = records_tally(rows, SCOPE_FEATURES)
    missing = sum(1 for feature in objects if geometry_kind(feature.get("geometry")) == EMPTY)
    tally.add(GEOMETRY_KEY, GEOMETRY, len(objects), missing, 0)
    return tally


def kml_tally(path: Path, formats_out: list | None = None) -> Tally:
    """The empty cells of the placemarks of a KML file: their name, the fields of their extended data and their
    geometry. With formats_out, the forms of their values are collected for Q3 (KML has no types: every value is
    text)."""
    rows, geometries, boxes = [], [], []
    for _, element in ElementTree.iterparse(str(path), events=("end",)):
        if local_name(element.tag) != "placemark":
            continue
        values: dict[str, str] = {}
        has_geometry = False
        points: list = []
        for child in element.iter():
            name = local_name(child.tag)
            if name == "name" and child is not element:
                values.setdefault("name", (child.text or ""))
            elif name in ("simpledata", "data") and child.get("name"):
                text = child.text or ""
                if name == "data":
                    found = next((item for item in child if local_name(item.tag) == "value"), None)
                    text = (found.text or "") if found is not None else ""
                values[child.get("name")] = text
            elif name == "coordinates" and (child.text or "").strip():
                has_geometry = True
                for pair in child.text.split():
                    numbers = pair.split(",")
                    try:
                        points.append((float(numbers[0]), float(numbers[1])))
                    except (ValueError, IndexError):
                        continue
        rows.append(values)
        geometries.append(has_geometry)
        boxes.append((min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points),
                      max(y for _, y in points)) if points else None)
        element.clear()
    tally = records_tally(rows, SCOPE_FEATURES)
    tally.add(GEOMETRY_KEY, GEOMETRY, len(rows), geometries.count(False), 0)
    if formats_out is not None:
        keys = list(dict.fromkeys(key for values in rows for key in values))
        formats = Formats(keys, typed=False, family="kml")
        formats.plausible.set_geometry("WGS84, the system of KML")
        for number, values in enumerate(rows, start=1):
            formats.add_texts(number, [values.get(key, "") for key in keys])
            formats.plausible.shape(boxes[number - 1], number)
        formats_out.append(formats)
    return tally


def most_common(counts: Counter, limit: int) -> list[tuple[str, int]]:
    """The most frequent items, the ties in alphabetical order, so that every run gives the same text."""
    return sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))[:limit]


def stirdata_tally(graph: rdflib.Graph) -> Tally | None:
    """The legal name and the legal identifier (with its notation) of every legal entity of an RDF graph in the
    STIRData model; the properties are recognised by their local names. None when the graph has no legal entity."""
    def local(term) -> str:
        return str(term).rsplit("/", 1)[-1].rsplit("#", 1)[-1]

    names, identifiers, notations, entities = {}, {}, {}, set()
    properties: dict = {}                         # subject -> local names of its predicates
    statuses: dict = {}
    for subject, predicate, value in graph:
        name = local(predicate)
        properties.setdefault(subject, Counter())[name] += 1
        if name in ("companyStatus", "orgStatus"):
            statuses[subject] = (str(value) if isinstance(value, rdflib.Literal) else local(value))[:40]
        if name == "legalName":
            names.setdefault(subject, []).append(value)
        elif name == "legalIdentifier":
            identifiers.setdefault(subject, []).append(value)
        elif name == "notation":
            notations.setdefault(subject, []).append(value)
        elif name == "type" and local(value) == "LegalEntity":
            entities.add(subject)
    entities |= set(names) | set(identifiers)
    if not entities:
        return None
    tally = Tally(SCOPE_STIRDATA)
    tally.records = len(entities)
    counts = {"legalName": [0, 0], "legalIdentifier": [0, 0]}      # empty, placeholders

    def best(values: list) -> int:
        kinds = [value_kind(str(value)) for value in values]
        return VALUE if VALUE in kinds else PLACEHOLDER if PLACEHOLDER in kinds else EMPTY

    lacking: dict[str, list] = {"legalName": [], "legalIdentifier": []}
    for entity in entities:
        name_kind = best(names.get(entity, []))
        identifier_values = []
        for identifier in identifiers.get(entity, []):
            if isinstance(identifier, rdflib.Literal):
                identifier_values.append(identifier)
            else:
                identifier_values += notations.get(identifier, [])
        for field, kind in (("legalName", name_kind), ("legalIdentifier", best(identifier_values))):
            if kind != VALUE:
                counts[field][kind - 1] += 1
                lacking[field].append(entity)
    for field, (empty, placeholders) in counts.items():
        tally.add(("stirdata", field), field, len(entities), empty, placeholders)

    # What the legal entities with a missing value hold instead: counts and names of properties only, no values.
    declared_only = sum(1 for entity in entities if set(properties.get(entity, {})) <= {"type"})
    if declared_only:
        tally.notes.append(f"{declared_only:,} of the {len(entities):,} legal entities "
                           f"{'has' if declared_only == 1 else 'have'} no property other than their type")
    for field, group in lacking.items():
        if not group:
            continue
        common = Counter(name for entity in group for name in properties.get(entity, {}) if name != "type")
        status = Counter(statuses.get(entity, "none") for entity in group)
        text = f"{len(group):,} legal entit{'y' if len(group) == 1 else 'ies'} without a " \
               f"{'legal name' if field == 'legalName' else 'legal identifier'}"
        if field == "legalIdentifier":
            without = sum(1 for entity in group if entity not in identifiers)
            text += f" ({without:,} without any legalIdentifier, {len(group) - without:,} with an identifier " \
                    "that has no notation)"
        text += "; their most frequent properties: " + (", ".join(f"{name} ({count:,})" for name, count
                                                                  in most_common(common, 5)) or "none")
        text += "; their status: " + ", ".join(f"{name} ({count:,})" for name, count in most_common(status, 4))
        tally.notes.append(text)
    return tally


# ---------------------------------------------------------------------------
# Kinds and forms of the values (Q3)
# ---------------------------------------------------------------------------

Q3_SAMPLE = 10              # records of every dataset in the local review file (DECISIONS.md #40, rule E)
Q3_EXAMPLES = 3             # rows of the local review file for each form found in a column
Q3_DISTINCT = 20_000        # distinct texts of a column kept to find the same value written in different ways
CELL_TEXT = 100             # characters of a value kept for the local review file
HASH_MASK = (1 << 64) - 1
HEADER_NOT_RECOGNISED = "(no header recognised: the row read as the header looks like a record)"
UNUSUAL_NUMBER = "number in an unusual form"    # text that reads as a number by the rule of AI1 but not by the forms above
Q3_STATE = {"dataset": 0, "counter": 0, "aligned": False}     # seeds of the random sample, set for every dataset

PERIOD_FORM = "yyyy-mm (or a period such as 2001-02)"
RANGE_FORM = "range such as 5-10"
# Forms of a date written as text. The order of day and month is read from the numbers: a first number above 12 is
# a day; a second number above 12 is a day, and the form becomes "m/d/yyyy".
DATE_FORMS = [
    ("d/m/yyyy", re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")),
    ("d-m-yyyy", re.compile(r"(\d{1,2})-(\d{1,2})-(\d{4})")),
    ("d.m.yyyy", re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")),
    ("d/m/yy", re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2})")),
    ("d-m-yy", re.compile(r"(\d{1,2})-(\d{1,2})-(\d{2})")),
    ("d.m.yy", re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2})")),
    ("yyyy-mm-dd", re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")),
    ("yyyy/mm/dd", re.compile(r"(\d{4})/(\d{1,2})/(\d{1,2})")),
    ("m/yyyy", re.compile(r"(\d{1,2})/(\d{4})")),
    (PERIOD_FORM, re.compile(r"(\d{4})-(\d{1,2})")),
]
DATE_BASES = {name.split(" ")[0] for name, _ in DATE_FORMS} | {"m/d/yyyy", "m-d-yyyy", "m.d.yyyy", "m/d/yy", "m-d-yy",
                                                                 "m.d.yy", "hh:mm", "hh:mm:ss"}
CLOCK = re.compile(r"(?:T|\s+)(\d{1,2}):([0-5]\d)(?::([0-5]\d)(?:[.,]\d+)?)?(?:\s*(?:Z|[+-]\d{2}:?\d{2}))?")
TIME_ONLY = re.compile(r"(\d{1,2}):([0-5]\d)(?::([0-5]\d)(?:[.,]\d+)?)?")

# Forms of a number written as text.
INTEGER = re.compile(r"[+-]?\d+")
SCIENTIFIC = re.compile(r"[+-]?\d+(?:[.,]\d+)?[eE][+-]?\d+")
AMBIGUOUS = re.compile(r"[+-]?\d{1,3}([.,])\d{3}")
DECIMAL = re.compile(r"[+-]?(\d*)([.,])(\d+)")
GROUPED = re.compile(r"[+-]?\d{1,3}([.,   ])\d{3}(?:\1\d{3})*(?:([.,])\d+)?")
NUMBER_MARKS = {    # form -> (decimal mark, thousands separator, four or more digits without a separator)
    "integer": ("", "", False), "integer, 4+ digits": ("", "", True),
    "decimal point": (".", "", False), "decimal point, 4+ digits": (".", "", True),
    "decimal comma": (",", "", False), "decimal comma, 4+ digits": (",", "", True),
    "point: decimal or thousands": ("?.", "", False), "comma: decimal or thousands": ("?,", "", False),
    "thousands point": ("", ".", False), "thousands point, decimal comma": (",", ".", False),
    "thousands comma": ("", ",", False), "thousands comma, decimal point": (".", ",", False),
    "thousands space": ("", " ", False), "thousands space, decimal point": (".", " ", False),
    "thousands space, decimal comma": (",", " ", False), "scientific notation": ("", "", False),
}
# Units written next to a number, in lower case without accents, dots and spaces -> the unit.
UNITS = {
    "%": "%", "‰": "‰", "€": "€", "eur": "€", "euro": "€", "ευρω": "€", "$": "$", "usd": "$", "£": "£",
    "kg": "kg", "kgr": "kg", "κιλα": "kg", "κιλ": "kg", "κγρ": "kg", "g": "g", "gr": "g", "γρ": "g", "γραμ": "g",
    "mg": "mg", "t": "t", "tn": "t", "τον": "t", "τονοι": "t", "l": "l", "lt": "l", "λιτ": "l", "λιτρα": "l",
    "λτ": "l", "ml": "ml", "m": "m", "μ": "m", "μετρα": "m", "km": "km", "χλμ": "km", "cm": "cm", "mm": "mm",
    "m2": "m²", "m²": "m²", "τμ": "m²", "στρ": "στρέμμα", "στρεμματα": "στρέμμα", "ha": "ha", "m3": "m³", "m³": "m³",
    "κμ": "m³", "kw": "kW", "kwh": "kWh", "mw": "MW", "mwh": "MWh", "°": "°", "°c": "°C", "oc": "°C", "h": "h",
    "ωρεσ": "h", "ωρ": "h", "min": "min", "λεπτα": "min", "sec": "s", "τεμ": "τεμ.", "τεμαχια": "τεμ.", "τμχ": "τεμ.",
    "pcs": "τεμ.", "ατομα": "άτομα", "κλινεσ": "κλίνες", "κλινη": "κλίνες", "θεσεισ": "θέσεις", "θεση": "θέσεις",
}
WITH_UNIT = re.compile(r"(?P<pre>[€$£])?\s*(?P<number>[+-]?[\d.,  ]*\d)\s*(?P<post>[^\d\s+\-][^\s]{0,11})?")
COMPARISON = re.compile(r"[<>≤≥]=?\s*[+-]?\d[\d.,]*")
RANGE = re.compile(r"[+-]?\d[\d.,]*\s*[-–—]\s*[+-]?\d[\d.,]*")

# Columns of codes or identifiers, recognised by their name: codes are rightly written as text, so their values are
# not judged as numbers (code, κωδικός, id, α/α, ΑΦΜ, ΚΑΕΚ, Τ.Κ., αριθμός πρωτοκόλλου, legal identifier).
IDENTIFIER_WORDS = re.compile(r"(?:^|[\W_])(?:id|fid|objectid|code|kodikos|kodik\w*|κωδ\w*|kod|kwd\w*|α\W?α|a\W?a|αφμ"
                              r"|afm|kaek|καεκ|τ\W?κ|tk|zip|notation|identifier|ar\W*prot\w*|αρ\W*πρωτ\w*"
                              r"|αριθμ\w*\W*πρωτ\w*|α\W?φ\W?|a\W?ph\W?|αρ\W*φακ\w*|ar\W*fak\w*)"
                              r"(?:$|[\W_\d])")
IDENTIFIER_END = re.compile(r"(?:code|kod|objectid|identifier)_?\d*$")
CAMEL_ID = re.compile(r"[a-z](?:Id|ID)_?\d*$")

# Formats of the GTFS reference (gtfs.org/documentation/schedule/reference) checked under Q3.
GTFS_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
GTFS_FORMATS = {
    "stops.txt": {"stop_lat": "latitude", "stop_lon": "longitude", "location_type": "integer",
                  "wheelchair_boarding": "integer"},
    "routes.txt": {"route_type": "integer", "route_color": "colour", "route_text_color": "colour",
                   "route_sort_order": "integer", "continuous_pickup": "integer", "continuous_drop_off": "integer"},
    "trips.txt": {"direction_id": "integer", "wheelchair_accessible": "integer", "bikes_allowed": "integer"},
    "stop_times.txt": {"arrival_time": "time", "departure_time": "time", "stop_sequence": "integer",
                       "pickup_type": "integer", "drop_off_type": "integer", "continuous_pickup": "integer",
                       "continuous_drop_off": "integer", "shape_dist_traveled": "number", "timepoint": "integer"},
    "calendar.txt": dict({day: "integer" for day in GTFS_DAYS}, start_date="date", end_date="date"),
    "calendar_dates.txt": {"date": "date", "exception_type": "integer"},
    "fare_attributes.txt": {"price": "number", "payment_method": "integer", "transfers": "integer",
                            "transfer_duration": "integer"},
    "shapes.txt": {"shape_pt_lat": "latitude", "shape_pt_lon": "longitude", "shape_pt_sequence": "integer",
                   "shape_dist_traveled": "number"},
    "frequencies.txt": {"start_time": "time", "end_time": "time", "headway_secs": "integer", "exact_times": "integer"},
    "transfers.txt": {"transfer_type": "integer", "min_transfer_time": "integer"},
    "pathways.txt": {"pathway_mode": "integer", "is_bidirectional": "integer", "length": "number",
                     "traversal_time": "integer", "stair_count": "integer", "max_slope": "number",
                     "min_width": "number"},
    "levels.txt": {"level_index": "number"},
    "feed_info.txt": {"feed_start_date": "date", "feed_end_date": "date"},
}
GTFS_RULES = {
    "date": (re.compile(r"\d{4}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"), "YYYYMMDD"),
    "time": (re.compile(r"\d{1,3}:[0-5]\d:[0-5]\d"), "HH:MM:SS"),
    "latitude": (re.compile(r"-?\d{1,2}(?:\.\d+)?"), "decimal degrees with a point"),
    "longitude": (re.compile(r"-?\d{1,3}(?:\.\d+)?"), "decimal degrees with a point"),
    "integer": (re.compile(r"-?\d+"), "integer"),
    "number": (re.compile(r"-?(?:\d+(?:\.\d+)?|\.\d+)"), "number with a decimal point"),
    "colour": (re.compile(r"[0-9A-Fa-f]{6}"), "six hexadecimal digits"),
}

FORM_CACHE: dict[str, tuple[str, str]] = {}


def date_form(text: str) -> str:
    """The form of a date or a time of day written as text, such as "d/m/yyyy" or "yyyy-mm-dd hh:mm", or ""."""
    found = TIME_ONLY.fullmatch(text)
    if found:
        if int(found.group(1)) > 23:
            return ""
        return "hh:mm:ss" if found.group(3) else "hh:mm"
    for name, pattern in DATE_FORMS:
        found = pattern.match(text)
        if not found:
            continue
        rest, suffix = text[found.end():], ""
        if rest:
            clock = CLOCK.fullmatch(rest)
            if not clock or int(clock.group(1)) > 23:
                return ""
            suffix = " hh:mm:ss" if clock.group(3) else " hh:mm"
        numbers = [int(group) for group in found.groups()]
        if name.startswith("yyyy"):
            if not 1800 <= numbers[0] <= 2199 or not 1 <= numbers[1] <= 12:
                return ""
            if len(numbers) == 3 and not 1 <= numbers[2] <= 31:
                return ""
            return name + suffix
        if name == "m/yyyy":
            return name + suffix if 1 <= numbers[0] <= 12 and 1800 <= numbers[1] <= 2199 else ""
        if len(found.group(3)) == 4 and not 1800 <= numbers[2] <= 2199:
            return ""
        first, second = numbers[0], numbers[1]
        if 1 <= first <= 31 and 1 <= second <= 12:
            return name + suffix
        if 1 <= first <= 12 and 13 <= second <= 31:
            return name.replace("d", "#").replace("m", "d").replace("#", "m") + suffix
        return ""
    return ""


def number_form(text: str) -> str:
    """The form of a number written as text, such as "decimal comma" or "thousands point, decimal comma", or ""."""
    if INTEGER.fullmatch(text):
        digits = text.lstrip("+-")
        if len(digits) > 1 and digits[0] == "0":
            return "leading zero"
        return "integer, 4+ digits" if len(digits) >= 4 else "integer"
    if SCIENTIFIC.fullmatch(text):
        return "scientific notation"
    found = AMBIGUOUS.fullmatch(text)
    if found:
        return "point: decimal or thousands" if found.group(1) == "." else "comma: decimal or thousands"
    found = DECIMAL.fullmatch(text)
    if found:
        mark = "point" if found.group(2) == "." else "comma"
        return f"decimal {mark}, 4+ digits" if len(found.group(1)) >= 4 else f"decimal {mark}"
    found = GROUPED.fullmatch(text)
    if found:
        group, mark = found.group(1), found.group(2)
        if mark == group:
            return ""
        name = {".": "thousands point", ",": "thousands comma"}.get(group, "thousands space")
        if mark:
            name += ", decimal point" if mark == "." else ", decimal comma"
        return name
    return ""


def unit_form(text: str) -> tuple[str, str]:
    """A number written together with its unit, such as "12,50 €", "€ 12" or "5 kg": (form of the number, unit)."""
    found = WITH_UNIT.fullmatch(text)
    if not found or bool(found.group("pre")) == bool(found.group("post")):
        return "", ""
    form = number_form(found.group("number"))
    if not form or form == "leading zero":
        return "", ""
    unit = UNITS.get(re.sub(r"[.\s]", "", normalise(found.group("pre") or found.group("post"))))
    return (form, unit) if unit else ("", "")


def text_form(text: str) -> tuple[str, str]:
    """(form, unit) of a value written as text: a form of date or of number, a number with its unit, a comparison
    such as "<5", a range such as "5-10", or "text"."""
    found = FORM_CACHE.get(text)
    if found is not None:
        return found
    form, unit = date_form(text), ""
    if not form:
        form = number_form(text)
    if not form:
        form, unit = unit_form(text)
    if not form:
        form = ("comparison such as <5" if COMPARISON.fullmatch(text) else
                RANGE_FORM if RANGE.fullmatch(text) else "text")
    if len(FORM_CACHE) > 200_000:
        FORM_CACHE.clear()
    FORM_CACHE[text] = (form, unit)
    return form, unit


def effective(forms: Counter) -> Counter:
    """The forms of a column as judged: "2001-02" next to ranges such as "2001-2002" is a period, not a month, so the
    yyyy-mm values count with the ranges."""
    result = Counter(forms)
    if any(form.endswith(RANGE_FORM) for form in result):
        for prefix in ("", "text: "):
            moved = result.pop(prefix + PERIOD_FORM, 0)
            if moved:
                result[prefix + RANGE_FORM] += moved
    return result


def category(form: str) -> str:
    """The kind of value of a form: number, date, text, code (a number with a leading zero), bool, list or link."""
    base = form[6:] if form.startswith("text: ") else form
    if base == "number" or base in NUMBER_MARKS or base == UNUSUAL_NUMBER:
        return "number"
    if base == "date" or base.split(" ")[0] in DATE_BASES:
        return "date"
    if base == "true/false":
        return "bool"
    if base == "list or object":
        return "list"
    if base == "link":
        return "link"
    if base == "leading zero":
        return "code"
    return "text"


def identifier_name(name: str) -> bool:
    text = normalise(name)
    return bool(IDENTIFIER_WORDS.search(text) or IDENTIFIER_END.search(text) or CAMEL_ID.search(str(name)))


def next_seed() -> int:
    """The seed of the random sample of a table: the same for every format of the same data, so that the same
    records are drawn from each format; otherwise one seed per table, in the order in which the tables are read."""
    if Q3_STATE["aligned"]:
        return Q3_STATE["dataset"]
    Q3_STATE["counter"] += 1
    return hash((Q3_STATE["dataset"], Q3_STATE["counter"])) & HASH_MASK


def short_text(value) -> str:
    """A value as shown in the local review file: one line, at most CELL_TEXT characters."""
    text = " ".join(str(value).split())
    return text[:CELL_TEXT] + ("…" if len(text) > CELL_TEXT else "")


def date_text(value) -> str:
    """The text of a date read from a spreadsheet or a shapefile, for the local review file."""
    if hasattr(value, "hour") and hasattr(value, "date"):
        return value.date().isoformat() if (value.hour, value.minute, value.second) == (0, 0, 0) else \
            value.isoformat(sep=" ", timespec="minutes")
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def python_cell(value) -> tuple[str, str]:
    """A value read from JSON, GeoJSON, a shapefile or RDF as a (kind, text) pair."""
    if value is None:
        return "empty", ""
    if isinstance(value, bool):
        return "bool", str(value).lower()
    if isinstance(value, (int, float)):
        return ("number", number_text(value)) if value == value and value not in (float("inf"), float("-inf")) \
            else ("empty", "")
    if isinstance(value, str):
        return "text", value
    if isinstance(value, (list, dict)):
        return ("list", json.dumps(value, ensure_ascii=False)[:CELL_TEXT]) if value else ("empty", "")
    if isinstance(value, bytes):
        return "text", value.decode("utf-8", errors="replace")
    if hasattr(value, "year"):
        return "date", date_text(value)
    return "text", str(value)


class Formats:
    """The kinds and forms of the values of one table, per column, for Q3 (DECISIONS.md #40). The values themselves
    are not kept, apart from a few rows for the local review file (folder review, ignored by git): the candidate rows
    of the random sample and up to three rows for each form found in a column."""

    def __init__(self, names: list, typed: bool, family: str) -> None:
        self.names = [str(name).strip() for name in names]
        self.typed = typed              # spreadsheets, JSON, GeoJSON, shapefiles: the type of every value is known
        self.family = family
        width = len(self.names)
        self.values = [0] * width
        self.forms = [Counter() for _ in range(width)]
        self.units = [Counter() for _ in range(width)]
        self.text_numbers = [0] * width     # text cells that read as numbers, by the rule of AI1
        self.typed_numbers = [0] * width    # numbers and dates stored as such
        self.text_cells = [0] * width
        self.examples: list[dict] = [{} for _ in range(width)]
        self.variants: list[dict | None] = [{} for _ in range(width)]
        self.raw: list[dict] = [{} for _ in range(width)]
        self.skip = [identifier_name(name) for name in self.names]
        self.records = 0
        self.short_rows = 0
        self.gtfs: dict[str, list] = {}     # field -> [values, values not in the format, format, examples]
        self.sample: list = []
        self.seed = next_seed()
        self.unnamed = False                # the row read as the header was a record: the columns have no names
        self.first: list[str] = []          # the values of the first record, for the header heuristic
        self.plausible = Plausibility(self.names, self.skip, family)      # the range checks of Q4
        self.keys = KeyColumns(self.names)                                # the identifiers of AI6

    def drop_header(self) -> None:
        """The row read as the header looks like a record: the columns keep their position only, and the table is
        left out of the comparison of structure."""
        self.names = [f"(column {index + 1})" for index in range(len(self.names))]
        self.skip = [False] * len(self.names)
        self.unnamed = True
        self.keys.names = self.names

    def draw(self, row: int, cells, typed_cells: bool) -> None:
        """The random sample: the Q3_SAMPLE records with the smallest keys (a hash of the seed and the row)."""
        self.records += 1
        if self.records == 1:
            self.first = [str(cell[1] if typed_cells else cell) for cell in cells]
        if self.keys.open:
            self.keys.record(cells, typed_cells)
        key = hash((self.seed, row)) & HASH_MASK
        sample = self.sample
        if len(sample) < Q3_SAMPLE or key < -sample[0][0]:
            entry = (-key, row, [short_text(cell[1] if typed_cells else cell) for cell in cells])
            if len(sample) < Q3_SAMPLE:
                heapq.heappush(sample, entry)
            else:
                heapq.heapreplace(sample, entry)

    def add_sample(self, row: int, texts) -> None:
        """A record of a GTFS feed: the random sample, the range checks of the fields with a rule (Q4) and the
        duplicates; the formats are checked by field."""
        self.draw(row, texts, False)
        bad = False
        for column in self.plausible.active:
            if column < len(texts):
                text = texts[column].strip()
                if text and missing_kind(text) == VALUE:
                    bad = self.plausible.value(column, "text", text, text_form(text)[0], row, texts, False) or bad
        self.plausible.record(row, bad, texts, False)

    def add_texts(self, row: int, texts: list) -> None:
        """One record of a format without types (CSV, KML): every value is text."""
        self.draw(row, texts, False)
        bad = False
        for column in range(min(len(self.names), len(texts))):
            text = texts[column]
            if text:
                bad = self.add_value(column, "text", text, row, texts, False) or bad
        self.plausible.record(row, bad, texts, False)

    def add_cells(self, row: int, cells: list) -> None:
        """One record of a format with types. Every cell is a (kind, text) pair: kind "text", "number", "date",
        "bool", "list" or "empty"."""
        self.draw(row, cells, True)
        bad = False
        for column in range(min(len(self.names), len(cells))):
            kind, text = cells[column]
            if kind != "empty":
                bad = self.add_value(column, kind, text, row, cells, True) or bad
        self.plausible.record(row, bad, cells, True)

    def add_value(self, column: int, kind: str, text: str, row, cells: list | None = None,
                  typed_cells: bool = False) -> bool:
        """One value of a column. Empty cells and placeholders of a missing value (Q2) are not examined. Returns
        True when the value is implausible (Q4)."""
        unit = ""
        if kind == "text":
            text = text.strip()
            if not text or missing_kind(text) != VALUE:
                return False
            if self.skip[column]:
                self.values[column] += 1
                return False
            form, unit = text_form(text)
            if self.typed:
                self.text_cells[column] += 1
                if looks_numeric(text) and not IDENTIFIER.match(text):
                    self.text_numbers[column] += 1
                    if form == "text":
                        form = UNUSUAL_NUMBER
                if form != "text":
                    form = "text: " + form
        elif kind in ("number", "date"):
            if kind == "number" and MISSING_NUMBERS.fullmatch(text):
                return False
            if self.skip[column]:
                self.values[column] += 1
                return False
            form = kind
            self.typed_numbers[column] += 1
        elif kind == "bool":
            form = "true/false"
        elif kind == "link":
            form = "link"
        else:
            form = "list or object"
        self.values[column] += 1
        self.forms[column][form] += 1
        examples = self.examples[column]
        if unit:
            self.units[column][unit] += 1
            found = examples.get("unit " + unit)
            if found is None or len(found) < Q3_EXAMPLES:
                self.example(examples, "unit " + unit, row, column, cells, text, typed_cells)
        found = examples.get(form)
        if found is None or len(found) < Q3_EXAMPLES:
            self.example(examples, form, row, column, cells, text, typed_cells)
        if form == "text" and self.variants[column] is not None:
            self.variant(column, text)
        return self.plausible.value(column, kind, text, form, row, cells, typed_cells)

    def example(self, examples: dict, form: str, row, column: int, cells: list | None, text: str,
                typed_cells: bool) -> None:
        """A row that shows a form of a column: the value and the values of the columns on its left and right."""
        found = examples.setdefault(form, [])
        if len(found) >= Q3_EXAMPLES:
            return
        if cells is None:
            found.append((row, column, (short_text(text),)))
            return
        start = max(0, column - 1)
        found.append((row, start, tuple(short_text(cells[index][1] if typed_cells else cells[index])
                                        for index in range(start, min(len(cells), column + 2)))))

    def variant(self, column: int, text: str) -> None:
        """The same value written in different ways: texts that differ only in case, accents, spaces or
        punctuation. Checked up to Q3_DISTINCT distinct texts per column."""
        raw = self.raw[column]
        if text in raw:
            return
        if len(raw) >= Q3_DISTINCT:
            self.variants[column], self.raw[column] = None, {}
            return
        key = " ".join(re.sub(r"[\W_]+", " ", normalise(text)).split())
        raw[text] = None
        groups = self.variants[column]
        first = groups.get(key)
        if first is None:
            groups[key] = [text, False]
        elif first[0] != text:
            first[1] = True

    def main_category(self, column: int) -> str:
        kinds = Counter()
        for form, count in effective(self.forms[column]).items():
            kinds[category(form)] += count
        return kinds.most_common(1)[0][0] if kinds else ""

    def header_looks_like_record(self) -> bool:
        """The row read as the header looks like a record: its names read as numbers or dates, as the values of
        their columns do. An integer or a date as a name weighs 1 (years and months are common headers), a decimal
        or grouped number 2 (no header), and an integer that the first record continues (1 above 2, a serial
        number) 3; the header is a record from a weight of 3, or when more than half of the named columns are
        alike."""
        named = alike = weight = 0
        for column, name in enumerate(self.names):
            if not name:
                continue
            named += 1
            form = text_form(name)[0]
            kind = category(form)
            if kind not in ("number", "date") or self.main_category(column) != kind:
                continue
            alike += 1
            weight += 1 if kind == "date" or form in ("integer", "integer, 4+ digits") else 2
            if form == "integer" and column < len(self.first) and INTEGER.fullmatch(self.first[column].strip()) \
                    and int(self.first[column]) == int(name) + 1:
                weight += 2
        return weight >= 3 or (named >= 2 and alike * 2 > named)


def json_formats(objects: list, keys: list[str], family: str) -> Formats:
    """The forms of the values of a list of JSON objects (or of the properties of GeoJSON features): one column per
    key; a missing key is an empty cell."""
    formats = Formats(keys, typed=True, family=family)
    for number, item in enumerate(objects, start=1):
        values = {str(key): value for key, value in item.items()}
        formats.add_cells(number, [python_cell(values.get(key)) for key in keys])
    return formats


def rdf_formats(graph: rdflib.Graph) -> Formats:
    """The forms of the values of an RDF graph, per property (by its local name): typed literals (dates, numbers,
    true/false), literals without a type, and links to other resources. The random sample is drawn among the
    subjects that have a type."""
    def local(term) -> str:
        return str(term).rsplit("/", 1)[-1].rsplit("#", 1)[-1]

    predicates = sorted({local(predicate) for predicate in graph.predicates()})
    position = {name: index for index, name in enumerate(predicates)}
    formats = Formats(predicates, typed=False, family="rdf")
    for subject, predicate, value in graph:
        column = position[local(predicate)]
        row = local(subject) or str(subject)
        if isinstance(value, rdflib.Literal):
            datatype = local(value.datatype) if value.datatype else ""
            if datatype in ("date", "dateTime", "gYear", "gYearMonth"):
                kind = "date"
            elif datatype in ("integer", "int", "long", "short", "decimal", "double", "float", "nonNegativeInteger",
                              "positiveInteger"):
                kind = "number"
            elif datatype == "boolean":
                kind = "bool"
            else:
                kind = "text"
            formats.add_value(column, kind, str(value), row)
        else:
            formats.add_value(column, "link", local(value) or str(value), row)
    subjects = {subject for subject, _, _ in graph.triples((None, rdflib.RDF.type, None))}
    chosen: list = []
    for subject in subjects:
        text = str(subject)
        key = hash((formats.seed, zlib.crc32(text.encode("utf-8")))) & HASH_MASK
        if len(chosen) < Q3_SAMPLE:
            heapq.heappush(chosen, (-key, text, subject))
        elif key < -chosen[0][0]:
            heapq.heapreplace(chosen, (-key, text, subject))
    formats.records = len(subjects)
    for negative, text, subject in chosen:
        values = [""] * len(predicates)
        for _, predicate, value in graph.triples((subject, None, None)):
            column = position[local(predicate)]
            if not values[column]:
                values[column] = short_text(value if isinstance(value, rdflib.Literal) else local(value))
        formats.sample.append((negative, local(subject) or text, values))
    return formats


class Column:
    """A column pooled over the tables of the same table of a dataset (Q3)."""

    def __init__(self, name: str, typed: bool, family: str, skip: bool) -> None:
        self.name, self.typed, self.family, self.skip = name, typed, family, skip
        self.values = self.text_numbers = self.typed_numbers = self.text_cells = 0
        self.forms: Counter = Counter()
        self.units: Counter = Counter()
        self.examples: dict[str, list] = {}
        self.variants: dict | None = {}
        self.tables = 0
        self.by_table: list[tuple[str, int, int]] = []     # (table, text cells that read as numbers, typed numbers)

    def merge(self, formats: Formats, index: int, table: dict) -> None:
        self.tables += 1
        self.by_table.append((where_q3(table), formats.text_numbers[index], formats.typed_numbers[index]))
        self.values += formats.values[index]
        self.forms.update(formats.forms[index])
        self.units.update(formats.units[index])
        self.text_numbers += formats.text_numbers[index]
        self.typed_numbers += formats.typed_numbers[index]
        self.text_cells += formats.text_cells[index]
        for form, rows in formats.examples[index].items():
            kept = self.examples.setdefault(form, [])
            for row, start, texts in rows:
                if len(kept) < Q3_EXAMPLES:
                    kept.append((table, row, start, texts))
        other = formats.variants[index]
        if self.variants is None or other is None:
            self.variants = None
            return
        for key, (text, doubled) in other.items():
            mine = self.variants.get(key)
            if mine is None:
                self.variants[key] = [text, doubled]
            elif mine[0] != text or doubled:
                mine[1] = True
        if len(self.variants) > Q3_DISTINCT:
            self.variants = None

    def main(self) -> tuple[str, Counter]:
        kinds: Counter = Counter()
        for form, count in effective(self.forms).items():
            kinds[category(form)] += count
        return (kinds.most_common(1)[0][0] if kinds else ""), kinds

    def doubled(self) -> int | None:
        """Values written in two or more ways (case, accents, spaces or punctuation); None when not checked."""
        if self.variants is None:
            return None
        return sum(1 for _, doubled in self.variants.values() if doubled)


def listing(counts, limit: int = 4) -> str:
    """Items with their counts, the most frequent first (the ties in alphabetical order)."""
    items = list(counts.items()) if isinstance(counts, dict) else list(counts)
    items.sort(key=lambda item: (-item[1], str(item[0])))
    text = ", ".join(f"{name} {count:,}" for name, count in items[:limit])
    return text + (f" and {len(items) - limit} more" if len(items) > limit else "")


def plural(count: int, word: str) -> str:
    return f"{count:,} {word}{'' if count == 1 else 's'}"


def some(items: list[str], limit: int = 3) -> str:
    return ", ".join(items[:limit]) + (f" and {len(items) - limit} more" if len(items) > limit else "")


def column_findings(column: Column) -> list[dict]:
    """The findings of Q3 for one pooled column: minor (score 1) or major (score 0), each with the forms of the
    values that show it."""
    findings: list[dict] = []
    if column.skip or not column.values or column.family == "gtfs":
        return findings
    forms = effective(column.forms)
    if any(category(form) == "code" for form in forms):
        return findings                          # numbers with a leading zero: a column of codes, rightly text

    def add(severity: str, kind: str, detail: str, shown_forms) -> None:
        findings.append({"severity": severity, "type": kind, "detail": detail, "forms": list(shown_forms)})

    main, kinds = column.main()
    total = sum(kinds.values())
    if kinds[main] * 2 <= total:
        large = [name for name, count in kinds.items() if count * 5 >= total and name in ("number", "date", "text")]
        if len(large) >= 2:
            add("minor", "values of several kinds in one column", listing(kinds), forms)
        return findings
    if main == "date":
        dates = Counter()
        for form, count in forms.items():
            if category(form) == "date":
                dates["date stored as date" if form == "date" else form] += count
        if len(dates) > 1:
            common = dates.most_common(1)[0][0]
            add("minor", "dates written in several formats", listing(dates),
                [form for form in forms if category(form) == "date" and form != common
                 and not (form == "date" and common == "date stored as date")])
        others = Counter({form: count for form, count in forms.items() if category(form) != "date"})
        if others:
            add("minor", "values that are not dates in a column of dates",
                listing(Counter({category(form): count for form, count in others.items()})), others)
        return findings
    if main == "number":
        if column.typed and column.text_numbers and (
                column.typed_numbers or column.text_numbers * 2 >= column.typed_numbers + column.text_cells):
            detail = plural(column.text_numbers, "cell")
            as_text = [where for where, text, typed in column.by_table if text and not typed]
            as_numbers = [where for where, text, typed in column.by_table if typed and not text]
            if as_text and as_numbers and len(as_text) + len(as_numbers) == len(column.by_table):
                detail += (f": stored as text in {some(as_text)} and as numbers in {some(as_numbers)}; the type "
                           "differs between files")
            add("minor", "numbers stored as text", detail,
                [form for form in forms if form.startswith("text: ") and category(form) == "number"])
        decimals, groups, long_values, scientific, plain = Counter(), Counter(), 0, 0, 0
        for form, count in forms.items():
            base = form[6:] if form.startswith("text: ") else form
            if base not in NUMBER_MARKS:
                continue
            decimal, group, long_value = NUMBER_MARKS[base]
            plain += count
            if decimal in (".", ","):
                decimals[decimal] += count
            if group:
                groups[group] += count
            if long_value:
                long_values += count
            if base == "scientific notation":
                scientific += count
        for form, count in forms.items():       # a.bbb and a,bbb: decimal or thousands, read from the other values
            base = form[6:] if form.startswith("text: ") else form
            if base in ("point: decimal or thousands", "comma: decimal or thousands"):
                mark = "." if base.startswith("point") else ","
                other = "," if mark == "." else "."
                if decimals[other] and not decimals[mark]:
                    groups[mark] += count
                elif decimals[mark] and not decimals[other]:
                    decimals[mark] += count

        def number_forms(test) -> list[str]:
            return [form for form in forms if (form[6:] if form.startswith("text: ") else form) in NUMBER_MARKS
                    and test(NUMBER_MARKS[form[6:] if form.startswith("text: ") else form])]

        if decimals["."] and decimals[","]:
            minority = "." if decimals["."] < decimals[","] else ","
            add("minor", "decimal point and decimal comma in one column",
                f"point {decimals['.']:,}, comma {decimals[',']:,}",
                number_forms(lambda marks: marks[0] in (minority, "?" + minority)))
        if len(groups) > 1:
            add("minor", "different thousands separators in one column", listing(groups),
                number_forms(lambda marks: bool(marks[1])))
        elif groups and set(groups) & {mark for mark, count in decimals.items() if count}:
            add("minor", "the same mark as decimal mark and as thousands separator", listing(groups),
                number_forms(lambda marks: bool(marks[1])))
        if groups and long_values:
            add("minor", "thousands separator in some values only",
                f"{sum(groups.values()):,} with a separator, {long_values:,} of four or more digits without",
                number_forms(lambda marks: marks[2]))
        if scientific and plain > scientific:        # a valid way of writing a number: recorded, not scored (#40)
            add("note", "scientific notation in some values", plural(scientific, "value"),
                [form for form in forms if form.endswith("scientific notation")])
        if len(column.units) > 1:
            add("major", "different units in one column", listing(column.units),
                ["unit " + unit for unit in column.units])
        elif column.units:
            add("minor", "numbers written with their unit in the cell", listing(column.units),
                ["unit " + unit for unit in column.units])
        others = Counter({form: count for form, count in forms.items() if category(form) != "number"})
        if others:
            add("minor", "values that are not numbers in a column of numbers",
                listing(Counter({(form[6:] if form.startswith("text: ") else form): count
                                 for form, count in others.items()})), others)
        return findings
    if main == "text" and forms.get("date"):
        add("minor", "values stored as dates in a column of text",
            f"{plural(forms['date'], 'cell')} converted to dates by the spreadsheet program", ["date"])
    if main in ("bool", "list", "link"):
        others = Counter({form: count for form, count in forms.items() if category(form) != main})
        if others:
            kind_name = "true/false values" if main == "bool" else main + "s"
            add("minor", f"values of another kind in a column of {kind_name}", listing(others), others)
    return findings


def structure_of(formats: Formats) -> tuple[tuple[str, ...], list[str]]:
    """The columns of a table for the comparison of structure: their keys (name without case, accents, spaces and
    punctuation) and their names; a column without a name and without any value is not a column."""
    keys, names = [], []
    for index, name in enumerate(formats.names):
        if not name and not formats.values[index] and not formats.forms[index]:
            continue
        keys.append(column_key(name) or f"#{index + 1}")
        names.append(name or f"(column {index + 1})")
    return tuple(keys), names


def family_of(kind: str) -> str:
    return {"text": "csv", "xls": "spreadsheet", "xlsx": "spreadsheet", "kmz": "kml"}.get(kind, kind)


def table_group(rule: str, label: str, member: str) -> str:
    """The table that a file holds, by the column tables of criteria/file_organisation.csv: empty (all the files hold
    the same table), "file name" (the files with the same name hold the same table, as the files of GTFS feeds),
    "cycle N" (the N resources of every edition, always in the same order), "resource" (every resource holds a table
    of its own) or "one; apart NAME, NAME" (one table, apart from the files named)."""
    rule = " ".join((rule or "").split()).lower()
    name = Path(member).name.lower() if member else ""
    if rule == "file name":
        return name or label
    if rule.startswith("cycle "):
        size = int(rule.split()[1])
        number = int(re.match(r"r(\d+)", label).group(1))
        return f"kind {(number - 1) % size + 1} of {size}"
    if rule == "resource":
        return label
    if rule.startswith("one; apart "):
        apart = {item.strip() for item in rule[len("one; apart "):].split(",")}
        return name if name in apart else "all"
    return "all"


def wrong_files(tables: list[dict], hashes: dict[str, str]) -> dict[str, str]:
    """Resources whose file is the same, byte for byte, as the file of a resource that holds another table of the
    dataset, and whose columns differ from those of the other files of their own table: a wrong file, left out of
    Q3. Returns {resource: resource with the same file}."""
    groups: dict[str, set] = {}
    for table in tables:
        groups.setdefault(table["label"], set()).add((table["group"], table["family"]))
    by_hash: dict[str, list[str]] = {}
    for label in groups:
        digest = hashes.get(label)
        if digest:
            by_hash.setdefault(digest, []).append(label)
    wrong: dict[str, str] = {}
    for labels in by_hash.values():
        if len(labels) < 2 or len({frozenset(groups[label]) for label in labels}) < 2:
            continue
        for label in labels:
            for table in (item for item in tables if item["label"] == label):
                peers = Counter(structure_of(item["formats"])[0] for item in tables
                                if (item["group"], item["family"]) == (table["group"], table["family"])
                                and item["label"] not in labels)
                if peers and structure_of(table["formats"])[0] != peers.most_common(1)[0][0]:
                    wrong[label] = next(other for other in labels if other != label)
    return wrong


def where_q3(table: dict) -> str:
    record = table["record"]
    text = " ".join(part for part in (table["label"], where_of(record)) if part)
    if len(record.get("_formats") or []) > 1:
        text += f" table {table['part'] + 1}"
    return text


def assess(tables: list[dict], personal: bool) -> dict:
    """The findings of Q3 over a set of tables: the values of every column pooled over the files of the same table,
    the formats of the GTFS reference, the comparison of the columns of the files of the same table, and the rows
    of CSV files with more fields than the header."""
    found: dict = {"major": [], "minor": [], "notes": [], "columns": [], "structures": []}
    pools: dict[tuple, dict] = {}
    for table in tables:
        pool = pools.setdefault((table["group"], table["family"]), {"tables": [], "columns": {}, "gtfs": {}})
        pool["tables"].append(table)
        formats, used = table["formats"], set()
        for index, name in enumerate(formats.names):
            if not name and not formats.values[index] and not formats.forms[index]:
                continue
            column_id = column_key(name) if name and column_key(name) else f"#{index + 1}"
            if column_id in used:
                column_id += f"#{index + 1}"
            used.add(column_id)
            column = pool["columns"].get(column_id)
            if column is None:
                column = pool["columns"][column_id] = Column(name or f"(column {index + 1})", formats.typed,
                                                             formats.family, formats.skip[index])
            column.merge(formats, index, table)
        for field, (values, wrong, rule, examples) in formats.gtfs.items():
            entry = pool["gtfs"].setdefault(field, [0, 0, rule, []])
            entry[0] += values
            entry[1] += wrong
            entry[3] += [(table, row, index, (text,)) for row, index, text in examples][
                :max(0, Q3_EXAMPLES - len(entry[3]))]
    families = Counter(family for _, family in pools)
    for (group, family), pool in pools.items():
        if len(pools) == 1 and group in ("all", "unit"):
            prefix = ""
        elif group in ("all", "unit"):
            prefix = "the other files: " if families[family] > 1 else f"{family}: "
        else:
            prefix = f"{group}: "
        for position, column in enumerate(pool["columns"].values(), start=1):
            if family == "gtfs":
                continue
            name = f"column {position}" if personal else column.name
            main, kinds = column.main()
            items = column_findings(column)
            for item in items:
                item.update(group=group, family=family, column=prefix + name,
                            examples=examples_of(column, item["forms"]))
                found["notes" if item["severity"] == "note" else item["severity"]].append(item)
            doubled = column.doubled() if main == "text" and not column.skip else None
            if doubled:
                found["notes"].append({"type": "the same value written in different ways", "group": group,
                                       "family": family, "column": prefix + name,
                                       "detail": f"{doubled:,} value{'s' if doubled > 1 else ''} written in two or "
                                                 "more ways (case, accents, spaces or punctuation)",
                                       "examples": examples_of(column, [])})
            found["columns"].append({
                "group": group, "format": family, "tables": column.tables, "column": position, "name": name,
                "values": column.values, "kind": "code" if column.skip else main,
                "forms": "identifier by its name: not judged" if column.skip else listing(effective(column.forms), 6),
                "units": listing(column.units, 6),
                "severity": "major" if any(item["severity"] == "major" for item in items) else
                            "minor" if any(item["severity"] == "minor" for item in items) else
                            "note" if items or doubled else "",
                "finding": "; ".join(f"{item['type']} ({item['detail']})" for item in items)
                           or (f"the same value written in different ways ({doubled:,})" if doubled else "")})
        for field, (values, wrong, rule, examples) in pool["gtfs"].items():
            pattern, form = GTFS_RULES[rule]
            found["columns"].append({"group": group, "format": family, "tables": len(pool["tables"]),
                                     "column": "", "name": field, "values": values, "kind": "GTFS " + rule,
                                     "forms": f"{values - wrong:,} in the format {form}", "units": "",
                                     "severity": "minor" if wrong else "",
                                     "finding": f"{plural(wrong, 'value')} not in the format {form}" if wrong else ""})
            if wrong:
                found["minor"].append({"severity": "minor", "type": "values not in the format of the GTFS reference",
                                       "detail": f"{wrong:,} of {values:,} not {form}", "group": group,
                                       "family": family, "column": f"{group}: {field.split(': ')[-1]}",
                                       "examples": examples})
        tables_of = pool["tables"]
        if len(tables_of) >= 2 or any(table["formats"].unnamed for table in tables_of):
            compare_structures(group, family, tables_of, personal, found)
    for table in tables:
        record, formats = table["record"], table["formats"]
        if table["part"] == 0 and record.get("extra_field_rows"):
            rows = int(record["extra_field_rows"])
            found["major"].append({"severity": "major", "type": "values shifted between columns",
                                   "detail": f"{rows:,} row{'s' if rows > 1 else ''} with more fields than the header",
                                   "group": table["group"], "family": table["family"], "column": where_q3(table),
                                   "examples": []})
        if formats.short_rows:
            found["notes"].append({"type": "rows with fewer fields than the header", "group": table["group"],
                                   "family": table["family"], "column": where_q3(table),
                                   "detail": f"{formats.short_rows:,} rows: to be checked for values shifted between "
                                             "columns", "examples": []})
        if formats.unnamed:
            found["notes"].append({"type": "no header recognised", "group": table["group"], "family": table["family"],
                                   "column": where_q3(table),
                                   "detail": "the row read as the header looks like a record: to be checked in the "
                                             "file", "examples": []})
    return found


def examples_of(column: Column, forms: list[str]) -> list:
    """Up to three rows that show a finding: rows of the less frequent forms first."""
    chosen = []
    ordered = sorted(forms, key=lambda form: column.forms.get(form, 0) or column.units.get(form[5:], 0))
    for form in ordered or list(column.examples):
        for item in column.examples.get(form, []):
            if len(chosen) < Q3_EXAMPLES and item not in chosen:
                chosen.append(item)
    return chosen


def compare_structures(group: str, family: str, tables: list[dict], personal: bool, found: dict) -> None:
    """The columns of the files of the same table: the same names (without case, accents, spaces and punctuation),
    in the same order and in the same number. The order counts in tables (CSV, spreadsheets), not in formats whose
    values are read by name (JSON, GeoJSON, KML, shapefiles, GTFS)."""
    ordered = family in ("csv", "spreadsheet")
    headers: dict[tuple, list] = {}
    names_of: dict[tuple, list[str]] = {}
    unnamed = [table for table in tables if table["formats"].unnamed]
    tables = [table for table in tables if not table["formats"].unnamed]
    for table in tables:
        keys, names = structure_of(table["formats"])
        key = keys if ordered else tuple(sorted(keys))
        headers.setdefault(key, []).append(where_q3(table))
        names_of.setdefault(key, names)
    for number, (key, members) in enumerate(headers.items(), start=1):
        found["structures"].append({
            "group": group, "format": family, "tables": len(tables), "headers": len(headers), "header": number,
            "count": len(members), "files": " | ".join(members[:40]) + (" | …" if len(members) > 40 else ""),
            "columns": len(key), "names": "" if personal else " | ".join(names_of[key])})
    for table in unnamed:
        found["structures"].append({
            "group": group, "format": family, "tables": len(tables), "headers": len(headers), "header": "",
            "count": 1, "files": where_q3(table), "columns": len(table["formats"].names),
            "names": "no header recognised: not compared"})
    if len(headers) <= 1:
        return
    sets = {frozenset(key) for key in headers}
    widths = sorted({len(key) for key in headers})
    if len(sets) == 1:
        kind, detail = "different order of the columns in the files of the same table", ""
    else:
        kind = "different columns in the files of the same table"
        detail = f"{min(widths)} to {max(widths)} columns" if len(widths) > 1 else "different names"
    text = f"{len(tables)} tables, {len(headers)} different headers" + (f", {detail}" if detail else "")
    found["minor"].append({"severity": "minor", "type": kind, "detail": text, "group": group, "family": family,
                           "column": "" if group in ("all", "unit") else group, "examples": []})


def q3_summary(found: dict) -> str:
    """The reason of a score of Q3: the findings by type, with the columns that show them."""
    parts = []
    for severity in ("major", "minor"):
        by_type: dict[str, list] = {}
        for item in found[severity]:
            by_type.setdefault(item["type"], []).append(item)
        for kind, items in by_type.items():
            columns = list(dict.fromkeys(item["column"] for item in items if item["column"]))
            text = kind
            if columns:
                text += ": " + ", ".join(columns[:5]) + (f" and {len(columns) - 5} more" if len(columns) > 5 else "")
            if len(items) == 1 and items[0]["detail"]:
                text += f" ({items[0]['detail']})"
            elif all("the type differs between files" in item["detail"] for item in items):
                text += " (the type differs between files)"
            parts.append(text)
    return "; ".join(parts)


def unit_q3(record: dict, personal: bool) -> None:
    """The fields of Q3 of a table or file in the profile: its own columns, without the other files of the
    dataset."""
    parts = record.get("_formats")
    if record["data_file"] is not True or record["readable"] is False or not parts:
        return
    if record["hidden"] is True:
        record["q3_reason"] = "hidden sheet, not examined"
        return
    tables = [{"label": record["position"], "record": record, "part": number, "formats": formats,
               "group": "unit" if len(parts) == 1 else f"table {number + 1}", "family": family_of(record["kind"])}
              for number, formats in enumerate(parts)]
    found = assess(tables, personal)
    record["q3_score"] = 0 if found["major"] else 1 if found["minor"] else 2
    record["q3_reason"] = q3_summary(found) or "one kind and one form of value in every column"


def sample_sections(tables: list[dict], aligned: bool) -> list[dict]:
    """The random sample of a dataset for the local review file: Q3_SAMPLE records drawn over all its tables, at
    least one from every table group (file name, kind) when there are no more groups than records; for the same data
    in several formats, the same records from each format."""
    if aligned:
        chosen = [(table, row, values) for table in tables for _, row, values in table["formats"].sample]
    else:
        candidates = sorted(((-negative, index, row, values) for index, table in enumerate(tables)
                             for negative, row, values in table["formats"].sample), key=lambda item: item[:3])
        chosen_keys, groups_seen = [], set()
        for item in candidates:
            group = (tables[item[1]]["group"], tables[item[1]]["family"])
            if group not in groups_seen:
                groups_seen.add(group)
                chosen_keys.append(item)
        for item in candidates:
            if len(chosen_keys) >= max(Q3_SAMPLE, len(groups_seen)):
                break
            if item not in chosen_keys:
                chosen_keys.append(item)
        chosen = [(tables[index], row, values) for _, index, row, values in chosen_keys]
    order = {id(table): index for index, table in enumerate(tables)}
    sections: dict[int, dict] = {}
    for table, row, values in chosen:
        section = sections.setdefault(id(table), {"where": where_q3(table), "names": table["formats"].names,
                                                  "rows": []})
        section["rows"].append((row, values))
    for section in sections.values():
        section["rows"].sort(key=lambda item: str(item[0]).zfill(12))
    return [sections[key] for key in sorted(sections, key=lambda key: order[key])]


def judge_q3(organisation: dict, files: list, personal: bool, hashes: dict[str, str]) -> dict:
    """Q3 of a dataset (DECISIONS.md #40): all its data files; the values of every column pooled over the files of
    the same table; the columns of the files of the same table compared."""
    result = {"score": None, "reason": "", "found": {"major": [], "minor": [], "notes": [], "columns": [],
                                                       "structures": []}, "sample": [], "notes": []}
    combine = organisation["combine"]
    if combine == "none":
        kind = (organisation.get("no_data_file") or "").strip()
        if kind == "documents":
            result["reason"] = ("data published only as documents: the consistency of their tables is estimated by "
                                "inspection (not applicable when the documents hold no table)")
        elif kind == "map images":
            result.update(score="n/a", reason="map images only: no values to examine")
        else:
            result.update(score=0, reason="no file can be opened: " + organisation["note"])
        return result
    rule = organisation.get("tables", "")
    tables, failed, uncounted, unavailable = [], [], [], []
    for label, _, units in files:
        for record in units:
            if record["data_file"] is not True:
                if record["readable"] is False and str(record["ai1_reason"]).startswith("not available"):
                    unavailable.append(label)
                continue
            if record["readable"] is False:
                failed.append(label)
                continue
            if record["hidden"] is True:
                continue
            parts = record.get("_formats") or []
            if not parts:
                uncounted.append(record)
                continue
            group = table_group("file name" if record["kind"] == "gtfs" else rule, label, record["member"])
            for number, formats in enumerate(parts):
                part_group = group                  # several tables in one sheet or file: each one a table of its own
                if len(parts) > 1:
                    part_group = f"table {number + 1}" if group == "all" else f"{group}, table {number + 1}"
                tables.append({"label": label, "record": record, "part": number, "formats": formats,
                               "group": part_group, "family": family_of(record["kind"])})
    notes = []
    wrong = wrong_files(tables, hashes)
    for label, other in sorted(wrong.items()):
        notes.append(f"{label} is the same file, byte for byte, as {other}, which holds another table of the "
                     f"dataset: a wrong file, left out")
    tables = [table for table in tables if table["label"] not in wrong]
    if not tables:
        if uncounted and not failed:
            result["reason"] = f"values not read in {uncounted[0]['kind'].upper()}: estimated by inspection"
        elif failed:
            result.update(score=0, reason="no file can be opened: " + ", ".join(sorted(set(failed))))
        elif unavailable:
            result.update(score=0, reason="no file can be opened: not available (Q1): "
                                          + ", ".join(sorted(set(unavailable))))
        else:
            result.update(score=0, reason="no file can be opened: no data file among the resources")
        return result
    found = assess(tables, personal)
    score = 0 if found["major"] else 1 if found["minor"] else 2
    labels = list(dict.fromkeys(table["label"] for table in tables))
    reason = q3_summary(found) or "one kind and one form of value in every column, and the same columns in the " \
                                  "files of the same table"
    scope = f"{len(labels)} file{'s' if len(labels) > 1 else ''}" + (f" ({labels[0]})" if len(labels) == 1 else "")
    if failed:
        notes.append(f"{len(set(failed))} file{'s' if len(set(failed)) > 1 else ''} could not be opened: "
                     + ", ".join(sorted(set(failed))))
    if unavailable:
        notes.append("not available (Q1): " + ", ".join(sorted(set(unavailable))))
    notes += [f"{item['type']}: {item['column']} ({item['detail']})" for item in found["notes"]]
    result.update(score=score, reason=f"{scope}: {reason}", found=found, notes=notes,
                  sample=sample_sections(tables, organisation["organisation"] == "formats"))
    return result


# ---------------------------------------------------------------------------
# Plausibility of the values (Q4)
# ---------------------------------------------------------------------------

Q4_STATE: dict = {"until": None}    # the download date of the file being examined: later dates are in the future
Q4_EXAMPLES = 3
EARLIEST_YEAR = 1800
INFINITY = float("inf")
# Greece, with its outermost islands (Othonoi, Gavdos, Kastellorizo) and its northern border.
WGS84 = {"lat": (34.5, 42.0), "lon": (19.0, 30.0)}                      # decimal degrees
EGSA87 = {"x": (40_000, 1_052_000), "y": (3_815_000, 4_670_000)}       # metres, Greek Grid (EPSG:2100): the box
# above transformed (Kastellorizo and Strongyli lie at x 1,003,000 to 1,009,000; Othonoi at x 104,000)
PHYSICAL = {                        # columns recognised by their name -> plausible range
    "count": (0, INFINITY), "temperature": (-50, 50), "humidity": (0, 100), "rainfall": (0, INFINITY),
    "wind": (0, INFINITY), "direction": (0, 360), "pressure": (700, 1070), "radiation": (0, INFINITY),
}
# Words of the column names, after normalise() (lower case, no accents): the order decides.
ROLE_RULES = [
    ("end", re.compile(r"(?:^|[\s_])(?:end|until|valid\w*|expir\w*|planned|to)(?:$|[\s_])|ληξ|ισχυ|^εωσ$"
                       r"|προγραμματ|διαρκεια|diarkeia|iskh[uy]os|lexe|lixi")),
    ("schedule", re.compile(r"^(?:date|start[\s_]date|feed[\s_]start[\s_]date)$")),
    ("stamp", re.compile(r"yyyymmdd")),
    ("year", re.compile(r"^(?:ετοσ|etos|year|yr)$")),
    ("lat", re.compile(r"(?:^|[\s_])(?:lat|latitude|πλατοσ|platos)$|^(?:γεωγρ\w*\s+)?πλατοσ$"
                       r"|^y[\s_]?wgs84$")),
    ("lon", re.compile(r"(?:^|[\s_])(?:lon|lng|long|longitude|μηκοσ|mekos|mikos)$|^(?:γεωγρ\w*\s+)?μηκοσ$"
                       r"|^x[\s_]?wgs84$")),
    ("x", re.compile(r"^(?:x[\s_]?egsa\w*|egsa\w*[\s_]?x|easting|x[\s_]?2100|x[\s_]?hatt)$")),
    ("y", re.compile(r"^(?:y[\s_]?egsa\w*|egsa\w*[\s_]?y|northing|y[\s_]?2100|y[\s_]?hatt)$")),
    ("x?", re.compile(r"^(?:x|x[\s_]?coord\w*|coord\w*[\s_]?x|χ)$")),
    ("y?", re.compile(r"^(?:y|y[\s_]?coord\w*|coord\w*[\s_]?y|ψ)$")),
    ("temperature", re.compile(r"θερμ|temp(?!late)|^t[\s_]?(?:mean|max|min|avg)$")),
    ("humidity", re.compile(r"υγρασ|hum|^rh(?:$|[\s_])")),
    ("rainfall", re.compile(r"βροχ|υετ|prec|rain|^ac[\s_]?r$")),
    ("direction", re.compile(r"dir|^dwd$|διευθ")),
    ("wind", re.compile(r"wind|ανεμ|^ws(?:$|[\s_])|^wg$|gust|ριπ")),
    ("pressure", re.compile(r"πιεσ|press|^prs(?:$|[\s_])|barom")),
    ("radiation", re.compile(r"^rad(?:$|[\s_])|ακτινοβ")),
    ("count", re.compile(r"πληθ|αριθμ|ποσοτ|(?:^|\s)ποσο|αξια|τιμη|προυπολ|εμβαδ|εκταση|βαροσ|κλιν|ατομα|δυναμικ"
                         r"|θεσεισ|εσοδ|δαπαν|εισπραξ|κοστ|συνολο|count|number|quantity|amount|price|value"
                         r"|population|places|total|weight|area|capacity|budget|cost|(?:^|[\s_(])kg(?:$|[\s_)])|€"
                         r"|slots")),
]
NOT_COUNT = re.compile(r"διαφορ|μεταβολ|change|diff|delta|balance|υπολοιπ|καθαρ|(?:^|[\s_])net(?:$|[\s_])"
                       r"|anomal|ποσοστ|percent|pct|%|(?:^|[\s_])rate|ρυθμ|δεικτ|index")
DATE_PARTS = {       # form -> (indices of year, month, day in the three numbers of the form)
    "d/m/yyyy": (2, 1, 0), "d-m-yyyy": (2, 1, 0), "d.m.yyyy": (2, 1, 0), "d/m/yy": (2, 1, 0), "d-m-yy": (2, 1, 0),
    "d.m.yy": (2, 1, 0), "m/d/yyyy": (2, 0, 1), "m-d-yyyy": (2, 0, 1), "m.d.yyyy": (2, 0, 1), "m/d/yy": (2, 0, 1),
    "m-d-yy": (2, 0, 1), "m.d.yy": (2, 0, 1), "yyyy-mm-dd": (0, 1, 2), "yyyy/mm/dd": (0, 1, 2),
}
INVALID_DATE = "invalid"


def column_role(name: str) -> str:
    """The rule that applies to a column, from its name: a coordinate (lat, lon, x, y, or x?/y? for a bare X or Y
    whose system is not declared), a non-negative quantity (count), a weather element, a year, a schedule date
    (GTFS, the future is allowed), a time stamp yyyyMMddHHmm, an end or validity date (the future is allowed), or
    nothing."""
    text = normalise(str(name)).replace("ς", "σ")
    text = re.sub(r"[^\w\s€%()]+", " ", text).strip()
    if not text:
        return ""
    for role, pattern in ROLE_RULES:
        if pattern.search(text):
            if role == "count" and NOT_COUNT.search(text):
                return ""
            return role
    return ""


def number_value(text: str, form: str) -> float | None:
    """The number written in a text whose form is known (number_form)."""
    text = text.strip()
    try:
        if form in ("integer", "integer, 4+ digits", "leading zero", "decimal point", "decimal point, 4+ digits",
                    "point: decimal or thousands", "scientific notation"):
            return float(text.replace(",", "."))
        if form in ("decimal comma", "decimal comma, 4+ digits", "comma: decimal or thousands"):
            return float(text.replace(",", "."))
        if form in ("thousands point", "thousands point, decimal comma"):
            return float(text.replace(".", "").replace(",", "."))
        if form in ("thousands comma", "thousands comma, decimal point"):
            return float(text.replace(",", ""))
        if form.startswith("thousands space"):
            return float(re.sub(r"[\s  ]", "", text).replace(",", "."))
    except ValueError:
        return None
    return None


def date_value(text: str, form: str, until):
    """The date written in a text whose form is known (date_form): a date, INVALID_DATE for a day that does not
    exist (30/02), or None for a form without a day (a month or a time)."""
    base = form.split(" hh:mm")[0]
    parts = DATE_PARTS.get(base)
    if parts is None:
        return None
    numbers = [int(item) for item in re.findall(r"\d+", text)[:3]]
    if len(numbers) < 3:
        return None
    year, month, day = numbers[parts[0]], numbers[parts[1]], numbers[parts[2]]
    if base.endswith("yy") and year < 100:
        year += 2000 if year <= until.year % 100 else 1900
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return INVALID_DATE


def compact_date(text: str):
    """A date written as YYYYMMDD (GTFS) or YYYYMMDDHHMM (time stamps)."""
    if not text.isdigit() or len(text) not in (8, 12):
        return None
    try:
        return datetime.date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError:
        return INVALID_DATE


def typed_date(text: str):
    try:
        return datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None


def inside(value: float, limits: tuple) -> bool:
    return limits[0] <= value <= limits[1]


def crs_system(crs: str) -> str:
    """The coordinate system of a geospatial file from its declaration: egsa87, wgs84, other or undeclared."""
    text = (crs or "").lower()
    if not text or text.startswith("no .prj"):
        return "undeclared"
    if "ggrs" in text or "greek" in text or "2100" in text or "egsa" in text or "hgrs" in text:
        return "egsa87"
    if "wgs" in text or "4326" in text or "crs84" in text:
        return "wgs84"
    return "other"


def bbox_inside(bbox: tuple, system: str) -> bool | None:
    """Whether a bounding box (xmin, ymin, xmax, ymax) lies inside Greece in a coordinate system; None when the
    system is not one of the two known ones."""
    xmin, ymin, xmax, ymax = bbox
    if system == "egsa87":
        return inside(xmin, EGSA87["x"]) and inside(xmax, EGSA87["x"]) and inside(ymin, EGSA87["y"]) \
            and inside(ymax, EGSA87["y"])
    if system == "wgs84":
        return inside(xmin, WGS84["lon"]) and inside(xmax, WGS84["lon"]) and inside(ymin, WGS84["lat"]) \
            and inside(ymax, WGS84["lat"])
    return None


def coordinates_bbox(coordinates) -> tuple | None:
    """The bounding box of GeoJSON coordinates (nested lists of [x, y, ...])."""
    xs, ys = [], []
    stack = [coordinates]
    while stack:
        item = stack.pop()
        if not isinstance(item, (list, tuple)) or not item:
            continue
        if isinstance(item[0], (int, float)):
            if len(item) >= 2 and isinstance(item[1], (int, float)):
                xs.append(float(item[0]))
                ys.append(float(item[1]))
        else:
            stack.extend(item)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


class Plausibility:
    """The range checks of Q4 (DECISIONS.md #41) for one table: coordinates inside Greece, dates not in the future
    and not before 1800, non-negative quantities, weather elements inside their physical range, years, duplicate
    records, geometries inside Greece. Counts, extremes and a few example rows only."""

    def __init__(self, names: list, skip: list, family: str) -> None:
        self.until = Q4_STATE["until"] or datetime.date.today()
        self.roles = ["" if skip[index] else column_role(name) for index, name in enumerate(names)]
        if family != "gtfs":                # the schedule dates (the future is allowed) exist in GTFS feeds only
            self.roles = ["" if role == "schedule" else role for role in self.roles]
        self.active = [index for index, role in enumerate(self.roles) if role and role != "end"]
        width = len(names)
        self.checked = [0] * width
        self.low: list = [None] * width
        self.high: list = [None] * width
        self.bad = [Counter() for _ in range(width)]
        self.examples: list[dict] = [{} for _ in range(width)]
        self.systems = [Counter() for _ in range(width)]     # x?/y?: the systems that the values fall in
        self.flags = bytearray()
        self.hashes = array("Q")                # one hash of the values of every record, for the duplicates
        self.rows = array("L")                  # the row of every record
        self.pending: tuple | None = None       # (row, hash of the geometry) read before its record
        self.found_duplicates: tuple | None = None
        self.family = family
        self.geometry: dict | None = None

    def extremes(self, column: int, value) -> None:
        self.checked[column] += 1
        low = self.low[column]
        if low is None:
            self.low[column] = self.high[column] = value
        elif type(low) is type(value):          # a column with numbers and dates keeps the extremes of the first kind
            if value < low:
                self.low[column] = value
            if value > self.high[column]:
                self.high[column] = value

    def value(self, column: int, kind: str, text: str, form: str, row, cells, typed_cells: bool) -> bool:
        """One value: True when it is implausible."""
        role = self.roles[column]
        if role == "end":
            return False
        base = form[6:] if form.startswith("text: ") else form
        number = date = None
        if kind == "number":
            try:
                number = float(text)
            except ValueError:
                return False
        elif kind == "date":
            date = typed_date(text)
        elif kind == "text":
            if role in ("schedule", "stamp"):
                date = compact_date(text.strip())
            elif base in NUMBER_MARKS:
                number = number_value(text, base)
            elif category(base) == "date":
                date = date_value(text.strip(), base, self.until)
        problem = None
        if number is not None:
            if not role or role in ("schedule", "stamp"):
                return False
            self.extremes(column, number)
            problem = self.number_problem(column, role, number)
        elif date is not None:
            if date == INVALID_DATE:
                problem = "invalid date"
            else:
                self.extremes(column, date)
                if date.year < EARLIEST_YEAR:
                    problem = f"before {EARLIEST_YEAR}"
                elif role != "schedule" and date > self.until:
                    problem = "future date"
        if problem is None:
            return False
        self.bad[column][problem] += 1
        found = self.examples[column].setdefault(problem, [])
        if len(found) < Q4_EXAMPLES:
            if cells is None:
                found.append((row, column, (short_text(text),)))
            else:
                start = max(0, column - 1)
                found.append((row, start, tuple(short_text(cells[index][1] if typed_cells else cells[index])
                                                for index in range(start, min(len(cells), column + 2)))))
        return True

    def number_problem(self, column: int, role: str, number: float) -> str | None:
        if role == "lat":
            return None if inside(number, WGS84["lat"]) else "outside Greece"
        if role == "lon":
            return None if inside(number, WGS84["lon"]) else "outside Greece"
        if role == "x":
            return None if inside(number, EGSA87["x"]) else "outside Greece"
        if role == "y":
            return None if inside(number, EGSA87["y"]) else "outside Greece"
        if role in ("x?", "y?"):               # no declared system: accepted when the value falls in a known one
            axis = "x" if role == "x?" else "y"
            degrees = "lon" if axis == "x" else "lat"
            if inside(number, EGSA87[axis]):
                self.systems[column]["EGSA87"] += 1
                return None
            if inside(number, WGS84[degrees]):
                self.systems[column]["WGS84"] += 1
                return None
            return "outside Greece"
        if role == "year":
            if number != int(number) or not EARLIEST_YEAR <= number <= self.until.year:
                return "year out of range"
            return None
        limits = PHYSICAL.get(role)
        if limits is None:
            return None
        if inside(number, limits):
            return None
        return "negative" if role == "count" else "outside the physical range"

    def record(self, row, bad: bool, cells, typed_cells: bool) -> None:
        """One record read to the end: its flag and its hash, for the share of implausible records and the
        duplicates. The hash of the geometry of a feature (shape) joins the hash of its values."""
        self.flags.append(1 if bad else 0)
        texts = tuple((cell[1] if typed_cells else cell) for cell in cells)
        key = hash(texts) & HASH_MASK
        if self.pending is not None and self.pending[0] == row:
            key = hash((key, self.pending[1])) & HASH_MASK
        self.pending = None
        self.hashes.append(key)
        self.rows.append(row if isinstance(row, int) and row >= 0 else 0)

    def duplicates(self) -> tuple:
        """Records identical to an earlier record of the same table, in all their values (and their geometry):
        their number and, for up to three of them, the row of the first record and the rows of its copies."""
        if self.found_duplicates is not None:
            return self.found_duplicates
        if len(self.hashes) < 2:
            self.found_duplicates = (0, [])
            return self.found_duplicates
        ordered = sorted(self.hashes)
        count, wanted = 0, []
        for index in range(1, len(ordered)):
            if ordered[index] == ordered[index - 1]:
                count += 1
                if len(wanted) < Q4_EXAMPLES and ordered[index] not in wanted:
                    wanted.append(ordered[index])
        examples: dict = {}
        if count:
            for position, value in enumerate(self.hashes):
                if value in wanted:
                    examples.setdefault(value, []).append(self.rows[position])
        self.found_duplicates = (count, [(rows[0], rows[1:]) for rows in examples.values()])
        return self.found_duplicates

    def set_geometry(self, crs: str) -> None:
        self.geometry = {"system": crs_system(crs), "declared": crs or "", "shapes": 0, "outside": 0,
                         "inferred": Counter(), "examples": []}

    def shape(self, bbox: tuple | None, row=None) -> None:
        """The bounding box of one geometry, checked against the declared system; for an undeclared system the
        system that the first shapes fall in is taken, and noted. The geometry joins the hash of its record (the
        record of the same row, read before or after the geometry)."""
        if self.geometry is None:
            return
        box_key = hash(bbox) & HASH_MASK if bbox is not None else 0
        index = row - 1 if isinstance(row, int) else -1
        if 0 <= index < len(self.rows) and self.rows[index] == row:
            self.hashes[index] = hash((self.hashes[index], box_key)) & HASH_MASK
        else:
            self.pending = (row, box_key)
        if bbox is None:
            return
        self.geometry["shapes"] += 1
        system = self.geometry["system"]
        if system in ("undeclared", "other"):
            for candidate in ("egsa87", "wgs84"):
                if bbox_inside(bbox, candidate):
                    self.geometry["inferred"][candidate] += 1
                    return
            result = False
        else:
            result = bbox_inside(bbox, system)
        if result is False:
            self.geometry["outside"] += 1
            if len(self.geometry["examples"]) < Q4_EXAMPLES:
                self.geometry["examples"].append((row, 0, (", ".join(plain_number(value) for value in bbox),)))

    def problems(self) -> int:
        return sum(sum(counter.values()) for counter in self.bad)


def plain_number(value: float) -> str:
    """A number for the reports: thousands separators, up to 6 decimals, no scientific notation."""
    if value == int(value) and abs(value) < 1e15:
        return f"{int(value):,}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def range_text(low, high, role: str = "") -> str:
    if low is None:
        return ""
    if hasattr(low, "isoformat"):
        return f"{low.isoformat()} to {high.isoformat()}"
    if role == "year":
        return f"{low:.0f} to {high:.0f}"
    return f"{plain_number(low)} to {plain_number(high)}"


def role_text(role: str) -> str:
    return {"lat": "latitude (degrees)", "lon": "longitude (degrees)", "x": "x (EGSA87)", "y": "y (EGSA87)",
            "x?": "x (system not declared)", "y?": "y (system not declared)", "count": "non-negative quantity",
            "year": "year", "schedule": "schedule date", "stamp": "time stamp", "end": "end or validity date",
            "": "dates"}.get(role, role)


def plausibility_rows(where: str, family: str, formats, personal: bool) -> list[dict]:
    """One row per column with a range check, for data/processed/file_plausibility_YYYY-MM-DD.csv."""
    rows = []
    checker = formats.plausible
    for column, name in enumerate(formats.names):
        if not checker.checked[column] and not checker.bad[column]:
            continue
        role = checker.roles[column]
        notes = ""
        if role in ("x?", "y?") and checker.systems[column]:
            notes = "system not declared: values in the range of " + ", ".join(
                f"{system} ({count:,})" for system, count in checker.systems[column].most_common())
        rows.append({"where": where, "format": family, "column": column + 1,
                     "name": f"column {column + 1}" if personal else name, "role": role_text(role),
                     "checked": checker.checked[column], "range": "" if personal else range_text(
                         checker.low[column], checker.high[column], role),
                     "implausible": sum(checker.bad[column].values()),
                     "kinds": kinds_text(checker.bad[column]) if checker.bad[column] else "", "notes": notes})
    geometry = checker.geometry
    if geometry and geometry["shapes"]:
        notes = ""
        if geometry["system"] in ("undeclared", "other") and geometry["inferred"]:
            notes = "system not declared: shapes in the range of " + ", ".join(
                f"{system} ({count:,})" for system, count in geometry["inferred"].most_common())
        system = geometry["declared"][:40] if geometry["declared"] else "system not declared"
        outside = geometry["outside"]
        rows.append({"where": where, "format": family, "column": "", "name": GEOMETRY, "role": f"geometry ({system})",
                     "checked": geometry["shapes"], "range": "", "implausible": outside,
                     "kinds": kinds_text({"geometries outside Greece": outside}) if outside else "", "notes": notes})
    duplicates = checker.duplicates()[0]
    if duplicates:
        rows.append({"where": where, "format": family, "column": "", "name": "(records)", "role": "duplicate records",
                     "checked": formats.records, "range": "", "implausible": duplicates,
                     "kinds": kinds_text({"duplicate records": duplicates}), "notes": ""})
    return rows


def assess_q4(tables: list[dict], personal: bool) -> dict:
    """The findings of Q4 over a set of tables: implausible records, duplicates, geometries outside Greece and rows
    shifted between columns (Q3), with the rows of the plausibility file and the example rows."""
    found = {"records": 0, "implausible": 0, "kinds": Counter(), "columns": [], "examples": [], "notes": [],
             "undeclared": [], "until": set()}
    for table in tables:
        formats, record = table["formats"], table["record"]
        checker = formats.plausible
        found["until"].add(checker.until)
        where = where_q3(table)
        found["records"] += formats.records
        flagged = sum(checker.flags) if checker.flags else checker.problems()
        found["implausible"] += flagged
        duplicates, copies = checker.duplicates()
        found["implausible"] += duplicates
        if duplicates:
            found["kinds"]["duplicate records"] += duplicates
            for first, rows in copies:
                for row in rows:
                    found["examples"].append({"finding": "duplicate record", "column": "(records)", "where": where,
                                              "row": row, "start": 0, "texts": (f"identical to row {first}",),
                                              "names": [""]})
        for column in range(len(formats.names)):
            for problem, count in checker.bad[column].items():
                found["kinds"][problem] += count
            name = f"column {column + 1}" if personal else formats.names[column]
            for problem, items in checker.examples[column].items():
                for row, start, texts in items:
                    found["examples"].append({"finding": KIND_PHRASES.get(problem, (problem,))[0], "column": name,
                                              "where": where, "row": row, "start": start, "texts": texts,
                                              "names": formats.names})
            if checker.roles[column] in ("x?", "y?") and checker.systems[column]:
                found["undeclared"].append(f"{where}: {name} in the range of "
                                           + checker.systems[column].most_common(1)[0][0])
        geometry = checker.geometry
        if geometry and geometry["shapes"]:
            if geometry["outside"]:
                found["implausible"] += geometry["outside"]
                found["kinds"]["geometries outside Greece"] += geometry["outside"]
                for row, start, texts in geometry["examples"]:
                    found["examples"].append({"finding": "geometry outside Greece", "column": GEOMETRY, "where": where,
                                              "row": row, "start": start, "texts": texts, "names": ["bounding box"]})
            if geometry["system"] in ("undeclared", "other") and geometry["inferred"]:
                found["undeclared"].append(f"{where}: geometries in the range of "
                                           + geometry["inferred"].most_common(1)[0][0])
        if table["part"] == 0 and record.get("extra_field_rows"):
            shifted = int(record["extra_field_rows"])
            found["implausible"] += shifted
            found["kinds"]["values shifted between columns"] += shifted
        found["columns"] += plausibility_rows(where, table["family"], formats, personal)
    return found


KIND_PHRASES = {                    # kind of finding -> (singular, plural) of what is counted
    "outside Greece": ("coordinate outside Greece", "coordinates outside Greece"),
    "negative": ("negative quantity", "negative quantities"),
    "future date": ("date after the download", "dates after the download"),
    "invalid date": ("date that does not exist", "dates that do not exist"),
    f"before {EARLIEST_YEAR}": (f"date before {EARLIEST_YEAR}", f"dates before {EARLIEST_YEAR}"),
    "year out of range": ("year out of range", "years out of range"),
    "outside the physical range": ("value outside the physical range", "values outside the physical range"),
    "duplicate records": ("duplicate record", "duplicate records"),
    "geometries outside Greece": ("geometry outside Greece", "geometries outside Greece"),
    "values shifted between columns": ("row with values shifted between columns",
                                       "rows with values shifted between columns"),
}


def kinds_text(counts) -> str:
    """The kinds of finding with their counts, the most frequent first: "18 coordinates outside Greece, 1 date after
    the download"."""
    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{count:,} {KIND_PHRASES.get(kind, (kind, kind))[0 if count == 1 else 1]}"
                     for kind, count in items)


def q4_score(found: dict) -> tuple:
    """The score and the reason of Q4 from the findings: 2 without implausible values; 1 below 1% of the records;
    0 from 1% (systematic)."""
    records, implausible = found["records"], found["implausible"]
    if not records:
        return None, "no records to check"
    kinds = kinds_text(found["kinds"])
    if not implausible:
        return 2, f"no implausible value in the range checks of {records:,} records"
    share = 100 * implausible / records
    text = f"{implausible:,} implausible of {records:,} records ({share:.2f}%): {kinds}"
    if share >= 1:
        return 0, "systematic: " + text
    return 1, "isolated: " + text


def unit_q4(record: dict, personal: bool) -> None:
    """The fields of Q4 of a table or file in the profile."""
    parts = record.get("_formats")
    if record["data_file"] is not True or record["readable"] is False or not parts:
        return
    if record["hidden"] is True:
        record["q4_reason"] = "hidden sheet, not examined"
        return
    tables = [{"label": record["position"], "record": record, "part": number, "formats": formats, "group": "unit",
               "family": family_of(record["kind"])} for number, formats in enumerate(parts)]
    found = assess_q4(tables, personal)
    score, reason = q4_score(found)
    record["q4_score"] = score
    record["q4_reason"] = reason + ("; " + "; ".join(found["undeclared"]) if found["undeclared"] else "")


def judge_q4(organisation: dict, files: list, personal: bool) -> dict:
    """Q4 of a dataset (DECISIONS.md #41): the range checks over all its data files, the duplicates of every table,
    the geometries and the rows shifted between columns; the manual look at the random sample follows."""
    result = {"score": None, "reason": "", "records": "", "implausible": "", "share": "", "notes": [],
              "columns": [], "examples": []}
    combine = organisation["combine"]
    if combine == "none":
        kind = (organisation.get("no_data_file") or "").strip()
        if kind == "documents":
            result["reason"] = ("data published only as documents: the plausibility of their values is estimated by "
                                "inspection (not applicable when the documents hold no table)")
        elif kind == "map images":
            result.update(score="n/a", reason="map images only: no values to examine")
        else:
            result.update(score=0, reason="no file can be opened: " + organisation["note"])
        return result
    tables, failed, uncounted, unavailable = [], [], [], []
    for label, _, units in files:
        for record in units:
            if record["data_file"] is not True:
                if record["readable"] is False and str(record["ai1_reason"]).startswith("not available"):
                    unavailable.append(label)
                continue
            if record["readable"] is False:
                failed.append(label)
                continue
            if record["hidden"] is True:
                continue
            parts = record.get("_formats") or []
            if not parts:
                uncounted.append(record)
                continue
            for number, formats in enumerate(parts):
                tables.append({"label": label, "record": record, "part": number, "formats": formats, "group": "all",
                               "family": family_of(record["kind"])})
    if not tables:
        if uncounted and not failed:
            result["reason"] = f"values not read in {uncounted[0]['kind'].upper()}: estimated by inspection"
        elif failed:
            result.update(score=0, reason="no file can be opened: " + ", ".join(sorted(set(failed))))
        elif unavailable:
            result.update(score=0, reason="no file can be opened: not available (Q1): "
                                          + ", ".join(sorted(set(unavailable))))
        else:
            result.update(score=0, reason="no file can be opened: no data file among the resources")
        return result
    found = assess_q4(tables, personal)
    score, reason = q4_score(found)
    labels = list(dict.fromkeys(table["label"] for table in tables))
    scope = f"{len(labels)} file{'s' if len(labels) > 1 else ''}" + (f" ({labels[0]})" if len(labels) == 1 else "")
    notes = []
    if failed:
        notes.append(f"{len(set(failed))} file{'s' if len(set(failed)) > 1 else ''} could not be opened: "
                     + ", ".join(sorted(set(failed))))
    if unavailable:
        notes.append("not available (Q1): " + ", ".join(sorted(set(unavailable))))
    if found["undeclared"]:
        notes.append("coordinates without a declared system, accepted by their range (AI6): "
                     + "; ".join(found["undeclared"][:6]) + (" …" if len(found["undeclared"]) > 6 else ""))
    columns = sum(1 for row in found["columns"] if row["name"] not in (GEOMETRY, "(records)"))
    geometries = any(row["name"] == GEOMETRY for row in found["columns"])
    scope_text = f"{columns} column{'s' if columns != 1 else ''}" if columns else ""
    if geometries:
        scope_text = (scope_text + " and the geometries") if scope_text else "the geometries"
    scope_text = (scope_text or "no column") + " with a range check"
    dates = sorted(found["until"])
    when = dates[0].isoformat() if len(dates) == 1 else f"{dates[0].isoformat()} to {dates[-1].isoformat()}"
    notes.append(f"{scope_text}; dates after the download ({when}) count as future")
    result.update(score=score, reason=f"{scope}: {reason}", records=found["records"],
                  implausible=found["implausible"],
                  share=f"{100 * found['implausible'] / found['records']:.2f}" if found["records"] else "",
                  notes=notes, columns=found["columns"], examples=found["examples"])
    return result


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def unit(**values) -> dict:
    record = {field: "" for field in PROFILE_FIELDS}
    record.update({"data_file": True, "readable": True})
    record.update(values)
    return record


def layout_fields(layout: dict) -> dict:
    keys = ("title_rows", "header_rows", "totals_rows", "subheading_rows", "notes_below", "merged_in_data", "tables",
            "extra_field_rows", "cells_beyond_header", "blank_rows_inside", "repeated_headers", "rows", "columns")
    values = {key: layout[key] for key in keys}
    values["header_row"] = layout["header"] + 1
    values["column_names"] = " | ".join(layout["names"])
    return values


def examine_csv(path: Path, member: str = "", kind: str = "csv", delimiter: str | None = None,
                strict: bool = True) -> dict:
    """A delimited text file. With strict=False (a .txt file inside an archive), a file whose lines do not split
    into a constant number of fields is taken as a text document and not as a table."""
    encoding = text_encoding(path)
    consistency = 1.0
    if delimiter is None:
        delimiter, consistency = delimiter_of(path, encoding)
    shown = "tab" if delimiter == "\t" else delimiter
    if not strict and consistency < 0.8:
        return unit(member=member, kind="text", data_file=False, encoding=encoding,
                    ai1_reason="not a data file: text without a table")
    rows = Rows()
    try:
        with open(path, encoding=encoding, errors="replace", newline="") as handle:
            for fields in csv.reader(handle, delimiter=delimiter):
                rows.add_text([field.strip() for field in fields])
    except csv.Error as error:
        return unit(member=member, kind=kind, readable=False, error=f"csv: {str(error)[:120]}", encoding=encoding,
                    delimiter=shown, ai1_score=0, ai1_reason="the file cannot be read as a table")
    layout = analyse(rows, csv_file=True)
    if not layout["table"]:
        return unit(member=member, kind=kind, data_file=False, encoding=encoding, delimiter=shown,
                    rows=sum(1 for n in rows.nonempty if n), ai1_reason="no table: one value per row at most")
    score, reason = table_score(layout, container="file")
    record = unit(member=member, kind=kind, encoding=encoding, delimiter=shown, ai1_score=score, ai1_reason=reason,
                  **layout_fields(layout))
    formats: list = []
    if kind == "gtfs":
        record["_tally"] = gtfs_tally(path, encoding, delimiter, Path(member).name.lower(), formats)
        if record["_tally"] is None:
            known = Path(member).name.lower() in GTFS_REQUIRED
            record.update(_q2_skip=True, q2_reason="no field of this file must always have a value, not counted"
                          if known else "not a file of the GTFS reference, not counted")
    else:
        record["_tally"] = csv_tally(path, encoding, delimiter, rows, layout, formats)
        if formats and formats[0].header_looks_like_record():
            record["column_names"] = HEADER_NOT_RECOGNISED
            formats[0].drop_header()
    record["_formats"] = formats
    return record


def sheet_rows(cells: dict[int, dict[int, tuple[str, str]]]) -> Rows:
    rows = Rows()
    last = max(cells) if cells else -1
    for index in range(last + 1):
        row = cells.get(index, {})
        width = max(row) + 1 if row else 0
        values, kinds = [""] * width, ["empty"] * width
        for column, (kind, value) in row.items():
            values[column], kinds[column] = value, kind
        rows.add_typed(values, kinds)
    return rows


def numbers_as_text(cells: dict[int, dict[int, tuple[str, str]]], layout: dict, rows: Rows) -> int:
    """Columns of the data rows of a sheet with numbers stored as text."""
    columns: dict[int, list[int]] = {}
    for index in layout["data"]:
        if rows.flags[index] & TOTAL or (rows.flags[index] & SINGLE_TEXT and layout["width"] >= 3):
            continue
        for column, (kind, value) in cells.get(index, {}).items():
            counts = columns.setdefault(column, [0, 0, 0])      # numbers, numbers as text, text
            if kind in ("number", "date"):
                counts[0] += 1
            elif kind == "text":
                counts[2] += 1
                if looks_numeric(value) and not IDENTIFIER.match(value):
                    counts[1] += 1
    return sum(1 for numbers, as_text, texts in columns.values()
               if as_text and (numbers or as_text >= 0.5 * (numbers + texts)))


def examine_sheet(name: str, cells: dict, merged: list, hidden: bool, kind: str, dates: dict | None = None) -> dict:
    rows = sheet_rows(cells)
    layout = analyse(rows, merged)
    if not layout["table"]:
        return unit(sheet=name, kind=kind, hidden=hidden, data_file=False, rows=sum(1 for n in rows.nonempty if n),
                    ai1_reason="no table in the sheet (notes or a single column)")
    as_text = numbers_as_text(cells, layout, rows)
    score, reason = table_score(layout, as_text)
    record = unit(sheet=name, kind=kind, hidden=hidden, numbers_as_text_columns=as_text, **layout_fields(layout))
    if hidden:
        record.update(ai1_reason="hidden sheet, not scored: " + reason, _q2_skip=True,
                      q2_reason="hidden sheet, not counted")
    else:
        formats: list = []
        record.update(ai1_score=score, ai1_reason=reason,
                      _tally=sheet_tally(cells, merged, rows, layout, formats, dates), _formats=formats)
        if formats and formats[0].header_looks_like_record():
            record["column_names"] = HEADER_NOT_RECOGNISED
            formats[0].drop_header()
    return record


def cell_kind(value) -> tuple[str, str]:
    if value is None:
        return "empty", ""
    if isinstance(value, bool):
        return "bool", str(value)
    if isinstance(value, (int, float)):
        return "number", number_text(value)
    if hasattr(value, "year"):
        return "date", ""
    text = str(value).strip()
    return ("text", text) if text else ("empty", "")


def examine_xlsx(path: Path) -> list[dict]:
    workbook = openpyxl.load_workbook(path, data_only=True)
    units = []
    for sheet in workbook.worksheets:
        cells: dict[int, dict[int, tuple[str, str]]] = {}
        dates: dict[tuple[int, int], str] = {}
        stored = getattr(sheet, "_cells", None)
        items = (stored.items() if stored is not None
                 else (((cell.row, cell.column), cell) for row in sheet.iter_rows() for cell in row))
        for (row, column), cell in items:
            kind, value = cell_kind(cell.value)
            if kind != "empty":
                cells.setdefault(row - 1, {})[column - 1] = (kind, value)
                if kind == "date":
                    dates[(row - 1, column - 1)] = date_text(cell.value)
        merged = [(r.min_row - 1, r.max_row - 1, r.min_col - 1, r.max_col - 1) for r in sheet.merged_cells.ranges]
        units.append(examine_sheet(sheet.title, cells, merged, sheet.sheet_state != "visible", "xlsx", dates))
    workbook.close()
    return units


def examine_xls(path: Path) -> list[dict]:
    note = ""
    try:
        book = xlrd.open_workbook(str(path), formatting_info=True, on_demand=True, logfile=io.StringIO())
    except (NotImplementedError, xlrd.XLRDError, AssertionError):
        book = xlrd.open_workbook(str(path), on_demand=True, logfile=io.StringIO())
        note = "merged cells could not be read"
    units = []
    try:
        for index in range(book.nsheets):
            sheet = book.sheet_by_index(index)
            cells: dict[int, dict[int, tuple[str, str]]] = {}
            dates: dict[tuple[int, int], str] = {}
            for row in range(sheet.nrows):
                for column in range(sheet.ncols):
                    cell_type = sheet.cell_type(row, column)
                    if cell_type in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                        continue
                    value = sheet.cell_value(row, column)
                    if cell_type == xlrd.XL_CELL_TEXT:
                        text = str(value).strip()
                        if text:
                            cells.setdefault(row, {})[column] = ("text", text)
                    elif cell_type == xlrd.XL_CELL_NUMBER:
                        cells.setdefault(row, {})[column] = ("number", number_text(value))
                    elif cell_type == xlrd.XL_CELL_DATE:
                        cells.setdefault(row, {})[column] = ("date", "")
                        try:
                            dates[(row, column)] = date_text(xlrd.xldate_as_datetime(value, book.datemode))
                        except (ValueError, OverflowError, xlrd.xldate.XLDateError):
                            dates[(row, column)] = number_text(value)
                    elif cell_type == xlrd.XL_CELL_BOOLEAN:
                        cells.setdefault(row, {})[column] = ("bool", str(bool(value)))
                    else:
                        cells.setdefault(row, {})[column] = ("text", xlrd.error_text_from_code.get(value, "#error"))
            merged = [(rlo, rhi - 1, clo, chi - 1) for rlo, rhi, clo, chi in getattr(sheet, "merged_cells", [])]
            record = examine_sheet(sheet.name, cells, merged, getattr(sheet, "visibility", 0) != 0, "xls", dates)
            if note:
                record["error"] = note
            units.append(record)
            book.unload_sheet(index)
    finally:
        book.release_resources()
    return units


def examine_spreadsheet(path: Path, kind: str, member: str = "") -> list[dict]:
    try:
        units = examine_xlsx(path) if kind == "xlsx" else examine_xls(path)
    except Exception as error:          # any failure of the reader means that a program cannot read the file
        return [unit(member=member, kind=kind, readable=False, error=f"{type(error).__name__}: {str(error)[:120]}",
                     ai1_score=0, ai1_reason="the spreadsheet cannot be read")]
    for record in units:
        record["member"] = member
    if not units:
        units = [unit(member=member, kind=kind, data_file=False, ai1_reason="no sheets")]
    return units


def records_of(data) -> tuple[int, list[str], list]:
    """Number of records, their keys and the records themselves in a JSON document: the largest list of objects
    within three levels, or the document itself when it is a single object."""
    best: tuple[int, list[str], list] = (0, [], [])

    def visit(node, depth: int) -> None:
        nonlocal best
        if isinstance(node, list):
            objects = [item for item in node[:5000] if isinstance(item, dict)]
            if objects and len(node) > best[0]:
                keys = Counter(key for item in objects[:2000] for key in item)
                best = (len(node), list(keys), node)
            if depth < 3:
                for item in node[:50]:
                    visit(item, depth + 1)
        elif isinstance(node, dict) and depth < 3:
            for value in node.values():
                visit(value, depth + 1)

    visit(data, 0)
    if best[0] == 0 and isinstance(data, dict):
        return 1, [str(key) for key in data][:200], [data]
    return best


def examine_json(path: Path, member: str = "") -> dict:
    try:
        raw = path.read_bytes()
        encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        data = json.loads(raw.decode(encoding))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        return unit(member=member, kind="json", readable=False, error=f"{type(error).__name__}: {str(error)[:120]}",
                    ai1_score=0, ai1_reason="the JSON file cannot be parsed")
    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        features = data.get("features") or []
        keys = Counter(key for feature in features[:2000] if isinstance(feature, dict)
                       for key in (feature.get("properties") or {}))
        crs = ((data.get("crs") or {}).get("properties") or {}).get("name", "")
        properties = [dict(feature.get("properties") or {}) for feature in features if isinstance(feature, dict)]
        every_key = list(dict.fromkeys(str(key) for item in properties for key in item))
        formats = json_formats(properties, every_key, "geojson")
        formats.plausible.set_geometry(crs or "WGS84, the default of GeoJSON")
        for number, feature in enumerate((item for item in features if isinstance(item, dict)), start=1):
            geometry = feature.get("geometry") or {}
            formats.plausible.shape(coordinates_bbox(geometry.get("coordinates")), number)
        return unit(member=member, kind="geojson", encoding=encoding, rows=len(features), columns=len(keys),
                    column_names=" | ".join(keys), crs=crs, ai1_score=2, ai1_reason="GeoJSON parsed without error",
                    _tally=features_tally(features), _formats=[formats])
    count, keys, records = records_of(data)
    objects = [item for item in records if isinstance(item, dict)]
    every_key = list(dict.fromkeys(str(key) for item in objects for key in item))
    return unit(member=member, kind="json", encoding=encoding, rows=count, columns=len(keys),
                column_names=" | ".join(map(str, keys)), ai1_score=2, ai1_reason="JSON parsed without error",
                _tally=records_tally(records), _formats=[json_formats(objects, every_key, "json")])


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def examine_xml(path: Path, member: str = "") -> dict:
    root, elements, features, namespaces = "", 0, 0, set()
    try:
        for event, element in ElementTree.iterparse(str(path), events=("start", "end")):
            if event == "start":
                elements += 1
                if not root:
                    root = local_name(element.tag)
                if "}" in element.tag:
                    namespaces.add(element.tag[1:].split("}", 1)[0])
                if local_name(element.tag) in ("placemark", "featuremember", "member", "record"):
                    features += 1
            else:
                element.clear()
    except ElementTree.ParseError as error:
        return unit(member=member, kind="xml", readable=False, error=f"ParseError: {str(error)[:120]}", ai1_score=0,
                    ai1_reason="the XML file cannot be parsed")
    if root in CAPABILITIES_ROOTS:
        return unit(member=member, kind="xml", data_file=False, rows=elements,
                    ai1_reason=f"not a data file: {root} document of a service")
    kind = "kml" if root == "kml" else "gml" if any("opengis.net/gml" in ns for ns in namespaces) else "xml"
    record = unit(member=member, kind=kind, rows=features or elements, column_names=f"root element: {root}",
                  ai1_score=2, ai1_reason=f"{kind.upper()} parsed without error")
    if kind == "kml":
        formats: list = []
        record["_tally"] = kml_tally(path, formats)
        record["_formats"] = formats
    else:
        record["q2_reason"] = f"values not counted in {kind.upper()}: estimated by inspection"
    return record


def examine_turtle(path: Path, member: str = "") -> dict:
    last = ""
    for rdf_format in ("turtle", "nt"):
        graph = rdflib.Graph()
        try:
            graph.parse(str(path), format=rdf_format)
        except Exception as error:      # rdflib raises parser-specific exceptions
            last = f"{type(error).__name__}: {str(error)[:120]}"
            continue
        subjects = len(set(graph.subjects()))
        predicates = sorted({str(predicate).rsplit("/", 1)[-1].rsplit("#", 1)[-1] for predicate in graph.predicates()})
        record = unit(member=member, kind="rdf", rows=subjects, columns=len(predicates),
                      column_names=" | ".join(predicates[:200]), ai1_score=2,
                      ai1_reason=f"RDF parsed without error ({len(graph)} triple{'s' if len(graph) != 1 else ''})",
                      _tally=stirdata_tally(graph), _formats=[rdf_formats(graph)])
        if record["_tally"] is None:
            record["q2_reason"] = "no legal entity of the STIRData model: values not counted, estimated by inspection"
        return record
    return unit(member=member, kind="rdf", readable=False, error=last, ai1_score=0,
                ai1_reason="the RDF file cannot be parsed")


def projection_name(path: Path | None) -> str:
    if not path:
        return "no .prj file"
    text = path.read_text(encoding="latin-1", errors="replace")
    found = re.search(r'(?:PROJCS|GEOGCS)\["([^"]+)"', text)
    return found.group(1) if found else text[:60]


def examine_shapefiles(folder: Path, prefix: str = "") -> list[dict]:
    """Every shapefile in a folder: the geometries and the attribute table are read to the end."""
    units = []
    by_stem: dict[str, dict[str, Path]] = {}
    for path in member_files(folder):
        suffix = path.suffix.lower()
        if suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            by_stem.setdefault(str(path.with_suffix("")).lower(), {})[suffix] = path
    for parts in (by_stem[stem] for stem in sorted(by_stem)):
        if ".shp" not in parts:
            continue
        name = prefix + relative_to(parts[".shp"], folder)
        missing = [suffix for suffix in (".shx", ".dbf") if suffix not in parts]
        if missing:
            units.append(unit(member=name, kind="shapefile", readable=False, error="missing " + ", ".join(missing),
                              ai1_score=0, ai1_reason="incomplete shapefile: missing " + ", ".join(missing)))
            continue
        declared = ""
        if ".cpg" in parts:
            declared = CODE_PAGES.get(parts[".cpg"].read_text(encoding="latin-1").strip().lower(), "")
        error_text, done, encoding = "", False, ""
        crs = projection_name(parts.get(".prj"))
        for encoding in [code for code in dict.fromkeys((declared, "utf-8", "cp1253")) if code]:
            try:
                with open(parts[".shp"], "rb") as shp, open(parts[".shx"], "rb") as shx, open(parts[".dbf"], "rb") as dbf:
                    with shapefile.Reader(shp=shp, shx=shx, dbf=dbf, encoding=encoding) as reader:
                        fields = [field[0] for field in reader.fields[1:]]
                        empty, placeholders, tokens = [0] * len(fields), [0] * len(fields), Counter()
                        formats = Formats(fields, typed=True, family="shapefile")
                        formats.plausible.set_geometry(crs)
                        records = 0
                        for values in reader.iterRecords():
                            records += 1
                            for index, value in enumerate(values):
                                kind = value_kind(value)
                                if kind == EMPTY:
                                    empty[index] += 1
                                elif kind == PLACEHOLDER:
                                    placeholders[index] += 1
                                    tokens[str(value).strip()[:12]] += 1
                            formats.add_cells(records, [python_cell(value) for value in values])
                        shapes = no_geometry = 0
                        for shape in reader.iterShapes():
                            shapes += 1
                            if shape.shapeType == shapefile.NULL or not shape.points:
                                no_geometry += 1
                                continue
                            bbox = getattr(shape, "bbox", None)
                            if bbox is None:
                                xs = [point[0] for point in shape.points]
                                ys = [point[1] for point in shape.points]
                                bbox = (min(xs), min(ys), max(xs), max(ys))
                            formats.plausible.shape(tuple(bbox), shapes)
                        shape_type = reader.shapeTypeName
                done = True
                break
            except UnicodeDecodeError:
                continue
            except Exception as error:      # pyshp raises generic exceptions on damaged files
                error_text = f"{type(error).__name__}: {str(error)[:120]}"
                break
        if not done:
            units.append(unit(member=name, kind="shapefile", readable=False,
                              error=error_text or "text fields not readable in UTF-8 or Windows-1253",
                              ai1_score=0, ai1_reason="the shapefile cannot be read"))
            continue
        if records != shapes:
            units.append(unit(member=name, kind="shapefile", readable=False, rows=records, columns=len(fields),
                              error=f"{shapes} shapes for {records} records", crs=crs, encoding=encoding,
                              ai1_score=0, ai1_reason="damaged shapefile: the shapes and the records differ in number"))
            continue
        tally = tally_from_counts(SCOPE_FEATURES, fields, records, empty, placeholders, tokens)
        tally.add(GEOMETRY_KEY, GEOMETRY, shapes, no_geometry, 0)
        units.append(unit(member=name, kind="shapefile", rows=records, columns=len(fields),
                          column_names=" | ".join(fields), crs=crs, encoding=encoding, ai1_score=2,
                          ai1_reason=f"shapefile ({shape_type.lower()}) read without error", _tally=tally,
                          _formats=[formats]))
    return units


def examine_member(path: Path, name: str, depth: int) -> list[dict]:
    """A file found inside an archive, examined by its own type."""
    suffix = path.suffix.lower()
    if suffix in SHAPEFILE_PARTS or path.name.lower().endswith(".shp.xml"):
        return []                                   # parts and metadata of a shapefile, examined together
    kind = detect_type(path)
    if kind == "ole2" and suffix not in (".xls", ".xlt", ""):
        return [unit(member=name, kind="ole2", data_file=False, ai1_reason=f"not a data file (OLE2 file {suffix})")]
    if kind in ("xlsx", "ole2"):
        return examine_spreadsheet(path, "xlsx" if kind == "xlsx" else "xls", member=name)
    if kind == "text":
        return [examine_csv(path, member=name, strict=suffix in (".csv", ".tsv"))]
    if kind == "json":
        return [examine_json(path, member=name)]
    if kind == "xml":
        return [examine_xml(path, member=name)]
    if kind == "turtle":
        return [examine_turtle(path, member=name)]
    if kind in ("zip", "gtfs", "shapefile", "kmz", "rar") and depth < 2:
        return examine_archive(path, kind, prefix=name + "/", depth=depth + 1)
    return [unit(member=name, kind=kind, data_file=False, ai1_reason=f"not a data file ({kind})")]


def examine_archive(path: Path, kind: str, prefix: str = "", depth: int = 0) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="datagovgr_", ignore_cleanup_errors=True) as temporary:
        folder = Path(temporary)
        error = extract_archive(path, kind, folder)
        if error:
            score = None if kind == "rar" else 0
            return [unit(member=prefix.rstrip("/"), kind=kind, readable=False, error=error, ai1_score=score,
                         ai1_reason=("not determined: " if score is None else "") + error)]
        files = member_files(folder)
        names = {member.name.lower() for member in files}
        if {"stops.txt", "routes.txt"} <= names:
            return [examine_csv(member, member=prefix + relative_to(member, folder), kind="gtfs", delimiter=",")
                    for member in files if member.suffix.lower() == ".txt"]
        units = examine_shapefiles(folder, prefix)
        for member in files:
            units += examine_member(member, prefix + relative_to(member, folder), depth)
        if kind == "kmz":
            for record in units:
                if record["kind"] == "kml":
                    record["kind"] = "kmz"
        if not units:
            units.append(unit(member=prefix.rstrip("/"), kind=kind, data_file=False, ai1_reason="empty archive"))
        return units


def examine_file(path: Path, kind: str) -> list[dict]:
    """All the tables or parsed files of one downloaded file."""
    if kind in ("xlsx", "ole2"):
        return examine_spreadsheet(path, "xlsx" if kind == "xlsx" else "xls")
    if kind == "text":
        return [examine_csv(path)]
    if kind == "json":
        return [examine_json(path)]
    if kind == "xml":
        return [examine_xml(path)]
    if kind == "turtle":
        return [examine_turtle(path)]
    if kind in ARCHIVE_TYPES or kind == "kmz":
        return examine_archive(path, kind)
    return [unit(kind=kind, data_file=False, ai1_reason=f"not a data file ({kind})")]


def where_of(record: dict) -> str:
    return " ".join(part for part in (record["member"], f"sheet \"{record['sheet']}\"" if record["sheet"] else "") if part)


def file_result(units: list[dict]) -> tuple[int | None, str, str]:
    """AI1 of a file from its tables: the worst scored table. (score, reason, the table that decides)"""
    data = [record for record in units if record["data_file"] is True]
    scored = [record for record in data if record["ai1_score"] not in ("", None)]
    undetermined = [record for record in data if record["ai1_score"] is None]
    if not scored and undetermined:
        return None, undetermined[0]["ai1_reason"], where_of(undetermined[0])
    if not scored:
        return 0, "no table in the file", ""
    worst = min(scored, key=lambda record: record["ai1_score"])
    reason = worst["ai1_reason"]
    if len(scored) > 1 and len({(record["ai1_score"], record["ai1_reason"]) for record in scored}) == 1:
        return worst["ai1_score"], f"all {len(scored)} tables or files: {reason}", ""
    if undetermined:
        reason += " (provisional: some parts could not be opened)"
    return worst["ai1_score"], reason, where_of(worst)


def q2_unit(record: dict, personal: bool) -> None:
    """The fields of Q2 of a table or file in the profile."""
    tally = record.get("_tally")
    if tally is None:
        return
    empty_columns = tally.empty_columns()
    record.update(
        q2_scope=tally.scope, q2_records=tally.records, q2_cells=tally.cells, q2_missing=tally.missing,
        q2_placeholders=tally.placeholders,
        q2_share=f"{100 * tally.missing / tally.cells:.2f}" if tally.cells else "",
        q2_columns=len(tally.columns), q2_empty_columns=len(empty_columns),
        q2_empty_column_names="" if personal else " | ".join(empty_columns),
        q2_placeholder_values=", ".join(f"{token[:12]} ({count})" for token, count in tally.tokens.most_common(5)),
        q2_notes="; ".join(tally.notes),
        q2_score=q2_score(tally)[0] if tally.cells else "",
        q2_reason=q2_text(tally, personal) if tally.cells or not tally.records
        else "nothing to count: no field of these records must have a value")


def q2_file(units: list[dict]) -> dict:
    """Q2 of a file: all its visible tables or files together. A dict with the score, the merged tally (or None)
    and a reason when nothing could be counted."""
    data = [record for record in units if record["data_file"] is True and not record.get("_q2_skip")]
    counted = [record for record in data if record.get("_tally") is not None]
    failed = [record for record in data if record["readable"] is False]
    uncounted = [record for record in data if record["readable"] is not False and record.get("_tally") is None]
    if counted:
        tally = Tally(counted[0]["_tally"].scope)
        for record in counted:
            tally.merge(record["_tally"])
        note = ""
        if failed or uncounted:
            note = f" (provisional: {len(failed) + len(uncounted)} of {len(data)} tables or files not counted)"
        return {"score": q2_score(tally)[0], "tally": tally, "note": note, "tables": len(counted),
                "where": where_of(counted[0]) if len(counted) == 1 else ""}
    if failed and any(record["ai1_score"] is None for record in failed):
        reason = next(record["ai1_reason"] for record in failed if record["ai1_score"] is None)
        return {"score": None, "tally": None,
                "reason": reason if reason.startswith("not determined") else "not determined: " + reason}
    if failed:
        return {"score": 0, "tally": None, "reason": "no file can be opened: " + failed[0]["ai1_reason"]}
    if uncounted:
        return {"score": None, "tally": None, "reason": uncounted[0]["q2_reason"] or "values not counted"}
    return {"score": None, "tally": None, "reason": "no table to count"}


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def positions(examined: str) -> list[str]:
    """The files named in criteria/file_organisation.csv: r003, r122-r132, r001_manual, or all."""
    tokens = []
    for token in examined.split():
        found = re.fullmatch(r"r(\d+)-r(\d+)", token)
        if found:
            tokens += [f"r{number:03d}" for number in range(int(found.group(1)), int(found.group(2)) + 1)]
        else:
            tokens.append(token)
    return tokens


def newest_log() -> Path:
    logs = sorted(PROCESSED_DIR.glob("resource_downloads_*.csv"))
    if not logs:
        raise SystemExit("No download log in data/processed. Run 05_resource_download.py first.")
    return logs[-1]


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


# --- AI6: linkage through common identifiers (DECISIONS.md #42) ---------------------------------------------------

KEY_SAMPLE = 2_000                  # records of every table whose values are tested against the patterns of codes

STANDARD_KEYS = [                   # (key, pattern of the column name, pattern of the values or None)
    ("KAEK cadastral code", re.compile(r"kaek|καεκ"), re.compile(r"^\d{12}$")),
    ("Kallikratis code", re.compile(r"kal_?code|kallikrat\w*[\s_]*(?:code|kwd|κωδ)|κωδ\w*[\s_]*καλλικρ"
                                    r"|kwd[\s_]*kall|kodikos[\s_]*kallikr"), re.compile(r"^\d{2,5}$")),
    ("NUTS or LAU code", re.compile(r"(?:^|[\s_])nuts|(?:^|[\s_])lau(?:$|[\s_])"),
     re.compile(r"^EL\d{1,3}$|^\d{3,8}$")),
    ("KAD/NACE activity code", re.compile(r"(?:^|[\s_])kad(?:$|[\s_])|^κ\.?α\.?δ\.?$|nace|(?:primary|secondary"
                                          r"|auxiliary|company)activity|activity[\s_]*code"),
     re.compile(r"^\d{2}(?:\.\d{1,2}){0,3}$")),
    ("tax number (AFM)", re.compile(r"αφμ|α\.φ\.μ|(?:^|[\s_])afm|(?:^|[\s_])vat|(?:^|[\s_])tin(?:$|[\s_])"),
     re.compile(r"^\d{9}$")),
    ("GEMI number", re.compile(r"γεμη|γ\.ε\.μη|(?:^|[\s_])gemi|legalidentifier"), re.compile(r"^\d{12}$")),
    ("ADA (Diavgeia)", re.compile(r"(?:^|[\s_])αδα(?:$|[\s_])|(?:^|[\s_])ada(?:$|[\s_])|diavgeia|διαυγει"),
     re.compile(r"^[Α-ΩA-Z0-9]{7}-[Α-ΩA-Z0-9]{3}$")),
    ("Natura 2000 site code", re.compile(r"sitecode|site[\s_]*code"), re.compile(r"^[A-Z]{2}\d{7}$")),
    ("Corine Land Cover code", re.compile(r"^code[\s_]?\d\d$|(?:^|[\s_])clc"), re.compile(r"^\d{3}$")),
    ("COICOP code", re.compile(r"coicop"), re.compile(r"^\d{2}(?:\.\d{1,2})*$|^\d{2,5}$")),
    ("postal code", re.compile(r"postcode|post[\s_]*code|postal|^τ\.?κ\.?$|ταχ\w*[\s_]*κωδ|(?:^|[\s_])zip"),
     re.compile(r"^\d{3}\s?\d{2}$")),
    ("KAE budget code", re.compile(r"^κ\.?α\.?ε\.?$|^kae$"), re.compile(r"^\d{2,6}(?:[.\-]\d+)*$")),
    ("teacher specialty code", re.compile(r"κωδ\w*[\s_.]*ειδικ|ειδικ\w*[\s_]*κωδ|kod\w*[\s_.]*eidik"),
     re.compile(r"^(?:ΠΕ|ΤΕ|ΔΕ|ΥΕ)\d{2}(?:\.\d{2})?$")),
    ("EMSY registry code", re.compile(r"emsy|εμσυ"), None),
]
VALUE_ONLY_KEYS = {                 # codes recognised from their values alone (distinctive forms)
    "ADA (Diavgeia)", "Natura 2000 site code", "teacher specialty code",
}
NUTS_VALUE = re.compile(r"^EL\d{1,3}$")
CODE_WITH_CONTEXT = re.compile(r"^code$|^κωδ|^kod")     # a generic code column named by a neighbouring header
DESCRIPTION_WORDS = re.compile(r"περιγραφ|descr|label|ονομασ|(?:^|[\s_])name|lektiko|title|τιτλ|perigra[fp]")
INTERNAL_NAME = re.compile(r"^id$|_id$|^_id$|(?:^|\s)id$|objectid|^fid$|^cid$|^α/α$|^a/a$|^#$|^αα$|αρ\.?\s*πρωτ"
                           r"|αριθμ\.?\s*πρωτ"
                           r"|πρωτοκ|serial|^κωδικ|^κωδ\.?$|^code$|^kod|φακ[εέ]λ|^α\.φ\.?$|ref_id|record_id"
                           r"|^(?:stop|route|trip|service|shape|agency|zone|block)_?(?:code|id)$")
NAME_WORDS = re.compile(r"δημ(?:ος|ου|οσ)|περιφερ|νοσοκομ|ονομασ|επωνυμ|φορε(?:ας|ασ|α)|διευθυνσ|address|municipal"
                        r"|region|(?:^|[\s_])name|(?:^|[\s_])stations?$|σταθμ|lektiko|κοινοτ|koinot|ενοτητ|enotita"
                        r"|τοποθεσ|^location$|περιοχ|^νομ(?:ος|οσ|ου)|dhmos|perifer|hospital|town|city|χωρ(?:ιο|α)"
                        r"|oikism|οικισμ|καταστημ|επιχειρ|εταιρ|business|shop|store|οργανισμ|organi[sz]ation"
                        r"|υπηρεσ|school|σχολ|κλινικ|clinic|ιδιοκτητ|owner|operator")


class KeyColumns:
    """The identifiers of one table for AI6: the columns whose names or values show a standard code, an internal
    code or a name. The values of the first KEY_SAMPLE records are tested against the patterns of the codes; the
    values themselves are not kept."""

    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.open = True
        self.seen = 0
        self.filled = [0] * len(names)
        self.matches = [Counter() for _ in names]       # column -> key -> values that follow its pattern
        self.nuts = [0] * len(names)

    def record(self, cells, typed_cells: bool) -> None:
        if not self.open:
            return
        self.seen += 1
        if self.seen > KEY_SAMPLE:
            self.open = False
            return
        for column in range(min(len(self.names), len(cells))):
            text = str(cells[column][1] if typed_cells else cells[column]).strip()
            if not text or missing_kind(text) != VALUE:
                continue
            self.filled[column] += 1
            for key, _, values in STANDARD_KEYS:
                if values is not None and values.match(text):
                    self.matches[column][key] += 1
            if NUTS_VALUE.match(text):
                self.nuts[column] += 1

    def findings(self, where: str, family: str, personal: bool, roles: list[str], geometry: dict | None,
                 unnamed: bool) -> list[dict]:
        """The identifiers and the coordinates of the table, one finding per column, with the evidence."""
        found = []
        context = normalise(" ".join(self.names))
        for column, name in enumerate(self.names):
            text = normalise(name)
            shown = f"column {column + 1}" if personal or unnamed else name
            filled = self.filled[column]
            matched = self.matches[column]
            key = None
            for label, pattern, values in STANDARD_KEYS:
                if pattern.search(text):
                    key = label
                    break
            if key is not None and DESCRIPTION_WORDS.search(text):
                pattern = next(values for label, _, values in STANDARD_KEYS if label == key)
                if pattern is not None and matched[key] < 0.5 * max(filled, 1):
                    key = None                  # a description named after the code, not the code itself
            if key is None and "coicop" in context and CODE_WITH_CONTEXT.search(text):
                key = "COICOP code"
            if key is None and filled >= 20:
                for label in VALUE_ONLY_KEYS:
                    if matched[label] >= 0.9 * filled:
                        key = label
                        break
                if key is None and self.nuts[column] >= 0.9 * filled:
                    key = "NUTS or LAU code"
            if key is not None:
                fitting = matched[key]
                pattern = next(values for label, _, values in STANDARD_KEYS if label == key)
                if pattern is None or filled == 0:
                    evidence = "recognised by the name of the column"
                elif fitting >= 0.9 * filled:
                    evidence = f"{fitting:,} of {filled:,} values tested follow the usual form"
                else:
                    evidence = (f"recognised by the name of the column; {fitting:,} of {filled:,} values tested "
                                f"follow the usual form")
                found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                              "kind": "standard code", "key": key, "evidence": evidence})
                continue
            role = roles[column] if column < len(roles) else ""
            if role in ("lat", "lon"):
                if family == "gtfs":
                    found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                                  "kind": "coordinates (declared system)",
                                  "key": "degrees, WGS84 by the GTFS reference",
                                  "evidence": "stop_lat, stop_lon, shape_pt_lat and shape_pt_lon are WGS84 by the "
                                              "GTFS reference"})
                else:
                    found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                                  "kind": "coordinates (system not declared)",
                                  "key": "degrees without a declared datum",
                                  "evidence": "latitude and longitude in degrees; no reference system is declared in "
                                              "the file or in the metadata"})
                continue
            if role in ("x", "y"):
                found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                              "kind": "coordinates (declared system)", "key": "EGSA87, named in the column",
                              "evidence": "the name of the column states the system"})
                continue
            if role in ("x?", "y?"):
                found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                              "kind": "coordinates (system not declared)", "key": "X/Y without a declared system",
                              "evidence": "accepted by the range of the values (Q4), no system declared"})
                continue
            if INTERNAL_NAME.search(text):
                found.append({"where": where, "format": family, "column": column + 1, "name": shown,
                              "kind": "internal code", "key": "code of the publisher",
                              "evidence": "identifier without a known standard behind it"})
                continue
            if NAME_WORDS.search(text):
                found.append({"where": where, "format": family, "column": column + 1, "name": shown, "kind": "name",
                              "key": "name", "evidence": "names of places, bodies or stations"})
        if geometry is not None:
            if geometry["system"] != "undeclared":
                found.append({"where": where, "format": family, "column": "", "name": GEOMETRY,
                              "kind": "geometry (declared system)", "key": geometry["declared"][:60],
                              "evidence": f"{geometry['shapes']:,} geometries in a declared reference system"})
            else:
                found.append({"where": where, "format": family, "column": "", "name": GEOMETRY,
                              "kind": "geometry (system not declared)", "key": geometry["declared"] or "no crs",
                              "evidence": f"{geometry['shapes']:,} geometries without a declared reference system"})
        return found


STANDARD_KINDS = {"standard code", "coordinates (declared system)", "geometry (declared system)"}
WEAK_KINDS = {"internal code", "name", "coordinates (system not declared)", "geometry (system not declared)"}


def assess_ai6(tables: list[dict], personal: bool) -> list[dict]:
    """The identifiers of all the tables of a dataset."""
    found = []
    for table in tables:
        formats = table["formats"]
        found += formats.keys.findings(where_q3(table), table["family"], personal, formats.plausible.roles,
                                       formats.plausible.geometry, formats.unnamed)
    return found


def ai6_score(found: list[dict]) -> tuple:
    """The score of AI6 from the identifiers found: 2 with a standard code or coordinates in a declared system in any
    file; 1 with names, internal codes or coordinates without a declared system only; 0 without any of them."""
    standard = [item for item in found if item["kind"] in STANDARD_KINDS]
    weak = [item for item in found if item["kind"] in WEAK_KINDS]
    if standard:
        keys = ", ".join(dict.fromkeys(item["key"] if item["kind"] == "standard code" else item["kind"]
                                       for item in standard))
        return 2, f"standard identifiers or coordinates in a declared system: {keys}"
    if weak:
        keys = ", ".join(dict.fromkeys(item["kind"] for item in weak))
        return 1, f"only {keys}: no standard code"
    return 0, "no identifier or location information that allows linkage"


def ai6_keys_text(found: list[dict]) -> str:
    """The identifiers of a dataset in one line, for the checks file: kind, key and columns."""
    groups: dict = {}
    for item in found:
        groups.setdefault((item["kind"], item["key"]), []).append(str(item["name"]))
    parts = []
    for (kind, key), names in groups.items():
        unique = list(dict.fromkeys(names))
        shown = ", ".join(unique[:4]) + (f" and {len(unique) - 4} more" if len(unique) > 4 else "")
        parts.append(f"{key} ({kind}): {shown}" if kind == "standard code" else f"{kind}: {shown}")
    return "; ".join(parts)


def wms_reference_systems(path: Path) -> list[str]:
    """The reference systems that a WMS capabilities document declares (CRS or SRS elements), the most frequent
    first; an empty list when the document is not a capabilities document."""
    try:
        counts: Counter = Counter()
        root_name = ""
        for event, element in ElementTree.iterparse(str(path), events=("start",)):
            tag = element.tag.rsplit("}", 1)[-1]
            if not root_name:
                root_name = tag
                if "Capabilities" not in root_name:
                    return []
            if tag in ("CRS", "SRS") and element.text:
                for code in element.text.split():
                    counts[code.strip()] += 1
            if sum(counts.values()) > 5000:
                break
        return [code for code, _ in counts.most_common(8)]
    except (ElementTree.ParseError, OSError):
        return []


def judge_ai6(organisation: dict, files: list, personal: bool, log_rows: list[dict]) -> dict:
    """AI6 of a dataset (DECISIONS.md #42): the identifiers and the coordinates of all its data files; the best file
    counts. Map services are judged by the reference systems that their capabilities document declares; documents
    are estimated by inspection."""
    result = {"score": None, "reason": "", "keys": "", "notes": [], "found": []}
    combine = organisation["combine"]
    if combine == "none":
        kind = (organisation.get("no_data_file") or "").strip()
        if kind == "documents":
            result["reason"] = ("data published only as documents: the identifiers in them (such as ADA codes, tax "
                                "numbers or standard codes) are judged by inspection")
        elif kind == "map images":
            systems = []
            for row in log_rows:
                if row.get("outcome") != "available" or row.get("detected_type") != "xml" or not row.get("file"):
                    continue
                systems = wms_reference_systems(ROOT / row["file"])
                if systems:
                    break
            if systems:
                result.update(score=2, reason="map service with a declared reference system: " + ", ".join(systems),
                              keys="WMS capabilities: " + ", ".join(systems))
            else:
                result.update(score=0, reason="no available document declares a reference system: "
                                              + organisation["note"])
        else:
            result.update(score=0, reason="no file can be opened: " + organisation["note"])
        return result
    tables, failed, uncounted, unavailable = [], [], [], []
    for label, _, units in files:
        for record in units:
            if record["data_file"] is not True:
                if record["readable"] is False and str(record["ai1_reason"]).startswith("not available"):
                    unavailable.append(label)
                continue
            if record["readable"] is False:
                failed.append(label)
                continue
            if record["hidden"] is True:
                continue
            parts = record.get("_formats") or []
            if not parts:
                uncounted.append(record)
                continue
            for number, formats in enumerate(parts):
                tables.append({"label": label, "record": record, "part": number, "formats": formats, "group": "all",
                               "family": family_of(record["kind"])})
    if not tables:
        if uncounted and not failed:
            result["reason"] = f"values not read in {uncounted[0]['kind'].upper()}: estimated by inspection"
        elif failed:
            result.update(score=0, reason="no file can be opened: " + ", ".join(sorted(set(failed))))
        elif unavailable:
            result.update(score=0, reason="no file can be opened: not available (Q1): "
                                          + ", ".join(sorted(set(unavailable))))
        else:
            result.update(score=0, reason="no file can be opened: no data file among the resources")
        return result
    found = assess_ai6(tables, personal)
    score, reason = ai6_score(found)
    labels = list(dict.fromkeys(table["label"] for table in tables))
    scope = f"{len(labels)} file{'s' if len(labels) > 1 else ''}" + (f" ({labels[0]})" if len(labels) == 1 else "")
    notes = []
    if failed:
        notes.append(f"{len(set(failed))} file{'s' if len(set(failed)) > 1 else ''} could not be opened: "
                     + ", ".join(sorted(set(failed))))
    if unavailable:
        notes.append("not available (Q1): " + ", ".join(sorted(set(unavailable))))
    weak_only = [item for item in found if item["kind"] == "coordinates (system not declared)"]
    if score == 2 and weak_only:
        notes.append("coordinates without a declared system in other columns or files: "
                     + ", ".join(dict.fromkeys(f"{item['where']}: {item['name']}" for item in weak_only))[:300])
    result.update(score=score, reason=f"{scope}: {reason}", keys=ai6_keys_text(found), notes=notes, found=found)
    return result


def download_date(row: dict, path: Path | None):
    """The date on which a file was downloaded (the last successful attempt of the download log), or the date of
    the file itself for a file downloaded by hand: a date in the data after it is a date in the future (Q4)."""
    for attempt in ("attempt_2", "attempt_1"):
        if row.get(f"{attempt}_result") == "available" and row.get(f"{attempt}_date"):
            try:
                return datetime.date.fromisoformat(row[f"{attempt}_date"][:10])
            except ValueError:
                continue
    if path is not None:
        return datetime.date.fromtimestamp(path.stat().st_mtime)
    return None


def dataset_files(sample_id: str, log_rows: list[dict]) -> list[tuple[str, dict, Path | None, str]]:
    """Every resource of a dataset, (label, log row, path or None, type), and the files downloaded by hand, named
    rNNN_manual.<extension> after the resource they come from."""
    found = []
    for row in sorted(log_rows, key=lambda item: int(item["position"])):
        label = f"r{int(row['position']):03d}"
        path = ROOT / row["file"] if row.get("outcome") == "available" and row.get("file") else None
        found.append((label, row, path if path and path.exists() else None, row.get("detected_type", "")))
    folder = RESOURCES_DIR / sample_id
    if folder.exists():
        by_label = {item[0]: item[1] for item in found}
        for path in sorted(folder.glob("r*_manual.*")):
            found.append((path.stem, by_label.get(path.stem.split("_", 1)[0], {}), path, detect_type(path)))
    return found


def judge_dataset(organisation: dict, results: dict[str, tuple[int | None, str, str]]) -> tuple[int | None, str, str]:
    """AI1 of a dataset from the results of the files named in the organisation table."""
    combine = organisation["combine"]
    if combine == "none":
        return 0, "no data file: " + organisation["note"], ""
    wanted = positions(organisation["examined"])
    if wanted == ["all"]:
        wanted = sorted(results)
    chosen = {label: results[label] for label in wanted if label in results}
    missing = [label for label in wanted if label not in results]
    if not chosen:
        return 0, "no data file available among " + ", ".join(wanted), ""
    determined = {label: result for label, result in chosen.items() if result[0] is not None}
    if not determined:
        label, result = next(iter(chosen.items()))
        return None, f"{label}: {result[1]}", label
    if combine == "best":
        label = max(determined, key=lambda key: determined[key][0])
    else:
        label = min(determined, key=lambda key: determined[key][0])
    score, reason, where = determined[label]
    text = f"{label}{' ' + where if where else ''}: {reason}"
    if combine == "best" and len(determined) > 1:
        text = f"best of {len(determined)} formats, " + text
    if combine == "worst" and len(determined) > 1:
        text = f"worst of {len(determined)} parts, " + text
    if missing:
        text += f" ({', '.join(missing)} not available)"
    if len(determined) < len(chosen):
        text += " (provisional: some files could not be opened)"
    return score, text, label


def field_keys(tally: Tally) -> dict[str, str]:
    """The named fields of a table or file (not its geometry): key -> name."""
    return {key[1]: entry[0] for key, entry in tally.columns.items() if len(key) == 2 and key[0] == "" and key[1]}


def has_field(keys: dict[str, str], key: str) -> bool:
    """A field is present under its name, or under a name cut short by a format (ten characters in a shapefile)."""
    return key in keys or any(min(len(key), len(other)) >= 6 and (other.startswith(key) or key.startswith(other))
                              for other in keys)


def complete_formats(counted: dict[str, dict]) -> tuple[dict[str, Tally], list[str]]:
    """The same data in several formats: a field that more than half of the formats carry and one format leaves out
    (a KML file leaves out the fields without any value) counts in that format as a column without any value."""
    keys = {label: field_keys(result["tally"]) for label, result in counted.items()}
    names: dict[str, str] = {}
    for label_keys in keys.values():
        for key, name in label_keys.items():
            names.setdefault(key, name)
    tallies, notes = {}, []
    for label, result in counted.items():
        tally = result["tally"]
        lacking = [key for key in names if not has_field(keys[label], key)
                   and 2 * sum(1 for other in keys.values() if has_field(other, key)) > len(keys)]
        if lacking:
            adjusted = Tally(tally.scope)
            adjusted.merge(tally)
            for key in lacking:
                adjusted.add(("", key), names[key], tally.records, tally.records, 0)
            tally = adjusted
            notes.append(f"{label} leaves out {', '.join(names[key] for key in lacking)}, which the other formats "
                         "carry: counted in it as a column without any value")
        tallies[label] = tally
    return tallies, notes


def judge_q2(organisation: dict, results: dict[str, dict], personal: bool) -> dict:
    """Q2 of a dataset (DECISIONS.md #39): the single file; the most complete of the same data in several formats;
    the latest edition of a series; all the parts of an edition together."""
    combine = organisation["combine"]
    if combine == "none":
        kind = (organisation.get("no_data_file") or "").strip()
        if kind == "documents":
            return {"score": None, "tally": None, "decisive": "",
                    "reason": "data published only as documents: the share of empty cells in their tables is "
                              "estimated by inspection (not applicable when the documents hold no table)"}
        if kind == "map images":
            return {"score": "n/a", "tally": None, "decisive": "", "reason": "map images only: no records to count"}
        return {"score": 0, "tally": None, "decisive": "", "reason": "no file can be opened: " + organisation["note"]}
    wanted = positions(organisation["examined"])
    if wanted == ["all"]:
        wanted = sorted(results)
    chosen = {label: results[label] for label in wanted if label in results}
    missing = [label for label in wanted if label not in results]
    if not chosen:
        return {"score": 0, "tally": None, "decisive": "",
                "reason": "no file can be opened: no data file available among " + ", ".join(wanted)}
    counted = {label: result for label, result in chosen.items() if result["tally"] is not None}
    if not counted:
        determined = {label: result for label, result in chosen.items() if result["score"] is not None}
        label, result = next(iter((determined or chosen).items()))
        return {"score": result["score"], "tally": None, "decisive": label, "reason": f"{label}: {result['reason']}"}
    notes: list[str] = []
    if combine == "best":
        tallies, notes = complete_formats(counted)
        label = min(tallies, key=lambda key: (-q2_score(tallies[key])[0], tallies[key].share(), key))
        result = counted[label]
        tally, decisive = tallies[label], label
        text = label + (" " + result["where"] if result["where"] else "") + result["note"]
        if len(counted) > 1:
            text = f"most complete of {len(counted)} formats, " + text
    elif combine == "worst" and len(counted) > 1:
        tally = Tally(next(iter(counted.values()))["tally"].scope)
        for result in counted.values():
            tally.merge(result["tally"])
        decisive = "all"
        text = f"all {len(counted)} parts together ({', '.join(counted)})" if len(counted) <= 6 else \
            f"all {len(counted)} parts together ({next(iter(counted))} to {list(counted)[-1]})"
        notes = [label for label, result in counted.items() if result["note"]]
        if notes:
            text += f" (provisional: some tables of {', '.join(notes)} not counted)"
    else:
        label, result = next(iter(counted.items()))
        tally, decisive = result["tally"], label
        text = label + (" " + result["where"] if result["where"] else "") + result["note"]
    if tally.scope != SCOPE_TABLE:
        text += f", {tally.scope}"
    skipped = [label for label in chosen if label not in counted]
    if skipped and combine != "best":
        text += f" ({', '.join(skipped)} not counted)"
    if missing:
        text += f" ({', '.join(missing)} not available)"
    return {"score": q2_score(tally)[0], "tally": tally, "decisive": decisive,
            "reason": f"{text}: {q2_text(tally, personal)}", "notes": notes + tally.notes}


def score_text(value) -> str:
    return "" if value == "" else "n/d" if value is None else str(value)


def write_factsheet(path: Path, sample_id: str, title: str, name: str, organisation: dict,
                    files: list[tuple[str, str, list[dict]]], judged: tuple, examined: set[str], date: str,
                    q2: dict, q3: dict, q4: dict, ai6: dict) -> None:
    score, reason, _ = judged
    lines = [
        f"# {sample_id}: {md_cell(title)}",
        "",
        f"Dataset: [{md_cell(title)}]({DATASET_URL}{name}). Snapshot of {date}. This fact sheet contains no records of "
        "the data: only file names, counts, column names, the forms of the values (such as \"d/m/yyyy\"), "
        "placeholders of missing values and the findings of the checks.",
        "",
        f"Organisation of the files: {organisation['organisation']} ({organisation['note']}). Examined for AI1 and "
        f"Q2: {organisation['examined'] or 'none'}. Examined for Q3, Q4 and AI6: all the data files.",
        "",
        f"Proposed score of AI1: **{score_text(score)}**: {md_cell(reason)}.",
        "",
        f"Proposed score of Q2: **{score_text(q2['score'])}**: {md_cell(q2['reason'])}.",
        "",
    ]
    if q2.get("notes"):
        lines += ["Notes on Q2: " + md_cell("; ".join(q2["notes"])) + ".", ""]
    lines += [f"Proposed score of Q3: **{score_text(q3['score'])}**: {md_cell(q3['reason'])}.", ""]
    if q3.get("notes"):
        lines += ["Notes on Q3: " + md_cell("; ".join(q3["notes"])) + ".", ""]
    lines += [f"Proposed score of Q4: **{score_text(q4['score'])}**: {md_cell(q4['reason'])}.", ""]
    lines += [f"Proposed score of AI6: **{score_text(ai6['score'])}**: {md_cell(ai6['reason'])}.", ""]
    if ai6.get("notes"):
        lines += ["Notes on AI6: " + md_cell("; ".join(ai6["notes"])) + ".", ""]
    if q4.get("notes"):
        lines += ["Notes on Q4: " + md_cell("; ".join(q4["notes"])) + ".", ""]
    lines += [
        "| File | Table | Type | Rows | Columns | AI1 | Q3 | Q4 | Findings of AI1 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, file_name, units in files:
        mark = " (examined)" if label in examined else ""
        for record in units:
            table = " ".join(part for part in (where_of(record), "(hidden)" if record["hidden"] is True else "") if part)
            findings = record["ai1_reason"] or ""
            if record["error"]:
                findings += f" [{record['error']}]"
            lines.append(f"| {label}{mark} {md_cell(file_name)} | {md_cell(table) or '-'} | {record['kind']} | "
                         f"{record['rows']} | {record['columns']} | {score_text(record['ai1_score'])} | "
                         f"{score_text(record.get('q3_score', ''))} | {score_text(record.get('q4_score', ''))} | "
                         f"{md_cell(findings)} |")
    counted = [(label, file_name, record) for label, file_name, units in files if label in examined
               for record in units if record.get("_tally") is not None]
    if counted:
        lines += ["", "Cells of the records counted for Q2 in the examined files:", "",
                  "| File | Table | Counted | Records | Cells | Empty | Of them placeholders | Share % | "
                  "Columns without any value |",
                  "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
        for label, file_name, record in counted:
            without = record["q2_empty_column_names"] or str(record["q2_empty_columns"] or "")
            placeholders = str(record["q2_placeholders"])
            if record["q2_placeholder_values"]:
                placeholders += f" ({record['q2_placeholder_values']})"
            lines.append(f"| {label} {md_cell(file_name)} | {md_cell(where_of(record)) or '-'} | "
                         f"{record['q2_scope']} | "
                         f"{record['q2_records']} | {record['q2_cells']} | {record['q2_missing']} | "
                         f"{md_cell(placeholders)} | {record['q2_share']} | {md_cell(without[:600]) or '-'} |")
    flagged = [row for row in q3["found"]["columns"] if row["severity"]]
    if flagged:
        lines += ["", "Columns with a finding of Q3 (all the data files; the forms of the values only, no values):", "",
                  "| Table | Format | Column | Values | Kind | Forms found | Finding |",
                  "| --- | --- | --- | ---: | --- | --- | --- |"]
        for row in flagged[:200]:
            lines.append(f"| {md_cell(row['group'])} | {row['format']} | {md_cell(row['name'])} | {row['values']} | "
                         f"{row['kind']} | {md_cell(row['forms'])}"
                         f"{' (units: ' + md_cell(row['units']) + ')' if row['units'] else ''} | "
                         f"{md_cell(row['finding'])} |")
        if len(flagged) > 200:
            lines.append(f"| … | | {len(flagged) - 200} more columns | | | | |")
    checked = q4.get("columns") or []
    if checked:
        lines += ["", "Range checks of Q4 (columns with a rule, geometries and duplicate records; extremes only, no "
                      "records):", "",
                  "| File and table | Column | Rule | Values checked | Range of the values | Implausible | Kinds "
                  "| Notes |",
                  "| --- | --- | --- | ---: | --- | ---: | --- | --- |"]
        for row in checked[:200]:
            lines.append(f"| {md_cell(row['where'])} | {md_cell(row['name'])} | {md_cell(row['role'])} | "
                         f"{row['checked']} | {md_cell(row['range'])} | {row['implausible']} | "
                         f"{md_cell(row['kinds'])} | {md_cell(row['notes'])} |")
        if len(checked) > 200:
            lines.append(f"| … | {len(checked) - 200} more rows | | | | | | |")
    keys = ai6.get("found") or []
    if keys:
        lines += ["", "Identifiers and coordinates (AI6; column names and the kind of identifier, no values):", "",
                  "| File and table | Column | Kind | Identifier | Evidence |", "| --- | --- | --- | --- | --- |"]
        for row in keys[:150]:
            lines.append(f"| {md_cell(row['where'])} | {md_cell(str(row['name']))} | {md_cell(row['kind'])} | "
                         f"{md_cell(row['key'])} | {md_cell(row['evidence'])} |")
        if len(keys) > 150:
            lines.append(f"| … | {len(keys) - 150} more rows | | | |")
    structures = q3["found"]["structures"]
    if structures:
        lines += ["", "Columns of the files of the same table (Q3):"]
        for row in structures:
            text = f"- {row['group']} ({row['format']}), header {row['header']} of {row['headers']}, " \
                   f"{row['count']} of {row['tables']} tables, {row['columns']} columns: {row['files']}"
            if row["names"]:
                text += f". Columns: {row['names']}"
            lines.append(md_cell(text[:2000]))
    names = [(label, record) for label, _, units in files if label in examined for record in units
             if record["data_file"] is True and (record["column_names"] or record["columns"])]
    if names:
        lines += ["", "Column names of the examined files:"]
        for label, record in names:
            where = " ".join(part for part in (label, where_of(record)) if part)
            if sample_id in PERSONAL_DATA_SUSPECTED:
                lines.append(f"- {md_cell(where)}: {record['columns']} columns (names not written: the dataset may "
                             "contain personal data)")
            elif record["column_names"]:
                text = record["column_names"]
                lines.append(f"- {md_cell(where)}: {md_cell(text[:1500])}{'…' if len(text) > 1500 else ''}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_summary(path: Path, checks: list[dict], date: str, titles: dict[str, str]) -> None:
    lines = [
        f"# Examination of the files of the sample: snapshot of {date}",
        "",
        "Criteria AI1 (a structure that a program can read without manual cleaning, DECISIONS.md #38) and Q2 "
        "(completeness, DECISIONS.md #39), proposed per dataset from the files named in "
        "criteria/file_organisation.csv, and Q3 (consistency, DECISIONS.md #40) and Q4 (plausibility, DECISIONS.md "
        "#41), proposed from all the data files. "
        "The proposals are confirmed or corrected in the manual assessment. The fact sheets of the datasets are in "
        "the folder factsheets. No file of this folder contains records of the data.",
        "",
        "## AI1: structure",
        "",
        "| ID | Dataset | Organisation | Examined | Proposed AI1 | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in checks:
        lines.append(f"| [{row['sample_id']}](factsheets/{row['sample_id']}.md) | "
                     f"[{md_cell(titles.get(row['sample_id'], row['dataset']))}]({DATASET_URL}{row['dataset']}) | "
                     f"{row['organisation']} | {row['examined'] or '-'} | {score_text(row['ai1_score'])} | "
                     f"{md_cell(row['ai1_reason'])} |")
    scores = Counter(score_text(row["ai1_score"]) for row in checks)
    lines += ["", "Proposed scores of AI1: " + ", ".join(f"{key}: {value}" for key, value in sorted(scores.items()))
              + ".",
              "", "## Q2: completeness", "",
              "| ID | Dataset | Cells counted | Empty | Share % | Columns without any value | Proposed Q2 | Reason |",
              "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |"]
    for row in checks:
        lines.append(f"| [{row['sample_id']}](factsheets/{row['sample_id']}.md) | "
                     f"[{md_cell(titles.get(row['sample_id'], row['dataset']))}]({DATASET_URL}{row['dataset']}) | "
                     f"{row.get('q2_cells', '')} | {row.get('q2_missing', '')} | {row.get('q2_share', '')} | "
                     f"{row.get('q2_empty_columns', '')} | {score_text(row.get('q2_score', ''))} | "
                     f"{md_cell(row.get('q2_reason', ''))} |")
    scores = Counter(score_text(row.get("q2_score", "")) for row in checks)
    lines += ["", "Proposed scores of Q2: "
              + ", ".join(f"{key or 'none'}: {value}" for key, value in sorted(scores.items())) + "."]
    lines += ["", "## Q3: consistency", "",
              "| ID | Dataset | Major findings | Minor findings | Proposed Q3 | Reason |",
              "| --- | --- | ---: | ---: | --- | --- |"]
    for row in checks:
        lines.append(f"| [{row['sample_id']}](factsheets/{row['sample_id']}.md) | "
                     f"[{md_cell(titles.get(row['sample_id'], row['dataset']))}]({DATASET_URL}{row['dataset']}) | "
                     f"{row.get('q3_major', '')} | {row.get('q3_minor', '')} | {score_text(row.get('q3_score', ''))} | "
                     f"{md_cell(row.get('q3_reason', ''))} |")
    scores = Counter(score_text(row.get("q3_score", "")) for row in checks)
    lines += ["", "Proposed scores of Q3: "
              + ", ".join(f"{key or 'none'}: {value}" for key, value in sorted(scores.items())) + "."]
    lines += ["", "## Q4: plausibility", "",
              "| ID | Dataset | Records | Implausible | Share % | Proposed Q4 | Reason |",
              "| --- | --- | ---: | ---: | ---: | --- | --- |"]
    for row in checks:
        lines.append(f"| [{row['sample_id']}](factsheets/{row['sample_id']}.md) | "
                     f"[{md_cell(titles.get(row['sample_id'], row['dataset']))}]({DATASET_URL}{row['dataset']}) | "
                     f"{row.get('q4_records', '')} | {row.get('q4_implausible', '')} | {row.get('q4_share', '')} | "
                     f"{score_text(row.get('q4_score', ''))} | {md_cell(row.get('q4_reason', ''))} |")
    scores = Counter(score_text(row.get("q4_score", "")) for row in checks)
    lines += ["", "Proposed scores of Q4: "
              + ", ".join(f"{key or 'none'}: {value}" for key, value in sorted(scores.items())) + "."]
    lines += ["", "## AI6: linkage through common identifiers", "",
              "| ID | Dataset | Proposed AI6 | Reason | Identifiers found |", "| --- | --- | --- | --- | --- |"]
    for row in checks:
        lines.append(f"| [{row['sample_id']}](factsheets/{row['sample_id']}.md) | "
                     f"[{md_cell(titles.get(row['sample_id'], row['dataset']))}]({DATASET_URL}{row['dataset']}) | "
                     f"{score_text(row.get('ai6_score', ''))} | {md_cell(row.get('ai6_reason', ''))} | "
                     f"{md_cell(str(row.get('ai6_keys', ''))[:400])} |")
    scores = Counter(score_text(row.get("ai6_score", "")) for row in checks)
    lines += ["", "Proposed scores of AI6: "
              + ", ".join(f"{key or 'none'}: {value}" for key, value in sorted(scores.items())) + "."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def sheet_value(sheet, row: int, column: int, value, bold: bool = False) -> None:
    """A cell of the local review file: text without control characters, never read as a formula."""
    if isinstance(value, str):
        value = ILLEGAL_CHARACTERS_RE.sub("", value)
    cell = sheet.cell(row=row, column=column, value=value)
    if isinstance(value, str) and value.startswith("="):
        cell.data_type = "s"
    if bold:
        cell.font = Font(bold=True)


def write_review_sample(path: Path, datasets: dict[str, dict], partial: bool) -> None:
    """The local review file of Q3 and Q4 (DECISIONS.md #40, rule E): one sheet per dataset with its random sample of
    records and up to three rows for every finding of Q3. It contains records of the data, so it is written to the
    folder review, which git ignores, and never to data/ or outputs/. For the datasets that seem to contain personal
    data only the row numbers are written. A partial run replaces the sheets of its datasets only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if partial and path.exists():
        workbook = openpyxl.load_workbook(path)
        for sheet_name in list(workbook.sheetnames):
            if sheet_name in datasets:
                del workbook[sheet_name]
    else:
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
    for sample_id in sorted(datasets):
        data = datasets[sample_id]
        personal = data["personal"]
        sheet = workbook.create_sheet(sample_id)
        sheet.column_dimensions["A"].width = 34
        sheet.column_dimensions["B"].width = 34
        sheet_value(sheet, 1, 1, f"{sample_id}: {data['title']}", bold=True)
        sheet_value(sheet, 2, 1, f"Random sample of {Q3_SAMPLE} records of the dataset, the same in every run, for the "
                                 "manual look of Q3 and Q4, and rows that show the findings of Q3 and Q4. Local "
                                 "review file: it contains records of the data and is not part of the repository.")
        if personal:
            sheet_value(sheet, 3, 1, "The dataset may contain personal data: only the row numbers are written; the "
                                     "records are looked at in the file itself.")
        line = 5
        if not data["sections"]:
            sheet_value(sheet, line, 1, f"No records to draw: {data['reason']}")
        for section in data["sections"]:
            sheet_value(sheet, line, 1, f"File and table: {section['where']}", bold=True)
            line += 1
            sheet_value(sheet, line, 1, "Row", bold=True)
            if not personal:
                for column, name in enumerate(section["names"], start=2):
                    sheet_value(sheet, line, column, name or f"(column {column - 1})", bold=True)
            line += 1
            for row, values in section["rows"]:
                sheet_value(sheet, line, 1, row)
                if not personal:
                    for column, value in enumerate(values, start=2):
                        sheet_value(sheet, line, column, value)
                line += 1
            line += 1
        sheet_value(sheet, line, 1, "Rows that show a finding of Q3 or Q4", bold=True)
        line += 1
        if not data["findings"]:
            sheet_value(sheet, line, 1, "No finding of Q3 or Q4 with rows to show.")
        else:
            for column, heading in enumerate(("Finding", "Column", "File and table", "Row",
                                              "Value, with the values on its left and right"), start=1):
                sheet_value(sheet, line, column, heading, bold=True)
            line += 1
            for item in data["findings"]:
                sheet_value(sheet, line, 1, item["finding"])
                sheet_value(sheet, line, 2, item["column"])
                sheet_value(sheet, line, 3, item["where"])
                sheet_value(sheet, line, 4, item["row"])
                if not personal:
                    sheet_value(sheet, line, 5, item["values"])
                line += 1
    if not workbook.sheetnames:
        workbook.create_sheet("none")
    workbook._sheets.sort(key=lambda sheet: sheet.title)
    workbook.save(path)


def review_findings(q3: dict) -> list[dict]:
    """The rows that show the findings of Q3, for the local review file."""
    rows = []
    found = q3["found"]
    for item in found["major"] + found["minor"] + found["notes"]:
        for table, row, start, texts in item.get("examples", []):
            names = table["formats"].names
            cells = [f"{names[start + offset] if start + offset < len(names) else ''}: {text}"
                     for offset, text in enumerate(texts)]
            rows.append({"finding": f"{item['type']} ({item['detail']})", "column": item["column"],
                         "where": where_q3(table), "row": row, "values": " | ".join(cells)})
    return rows


def review_findings_q4(q4: dict) -> list[dict]:
    """The rows that show the findings of Q4, for the local review file."""
    rows = []
    for item in q4.get("examples", []):
        names = item["names"]
        cells = []
        for offset, text in enumerate(item["texts"]):
            name = names[item["start"] + offset] if item["start"] + offset < len(names) else ""
            cells.append(f"{name}: {text}" if name else text)
        rows.append({"finding": f"Q4: {item['finding']}: {item['column']}", "column": item["column"],
                     "where": item["where"], "row": item["row"], "values": " | ".join(cells)})
    return rows


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Examination of the downloaded files of the sample (criteria AI1, "
                                                 "Q2, Q3, Q4 and AI6).")
    parser.add_argument("--only", nargs="+", metavar="ID", help="sample ids to examine, e.g. S06 (test run)")
    args = parser.parse_args()

    log_file = newest_log()
    date = log_file.stem.rsplit("_", 1)[-1]
    log = read_csv(log_file)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    titles = {key: row.get("title", "") for key, row in sample.items()}
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    wanted = {item.upper() for item in args.only} if args.only else set(organisation)
    unknown = wanted - set(organisation)
    if unknown:
        raise SystemExit(f"Not in {relative(ORGANISATION_FILE)}: {', '.join(sorted(unknown))}.")
    out_dir = OUT_DIR / f"files_{date}"
    profiles_file = PROCESSED_DIR / f"file_profiles_{date}.csv"
    columns_file = PROCESSED_DIR / f"file_columns_{date}.csv"
    checks_file = PROCESSED_DIR / f"file_checks_{date}.csv"
    formats_file = PROCESSED_DIR / f"file_formats_{date}.csv"
    structures_file = PROCESSED_DIR / f"file_structures_{date}.csv"
    plausibility_file = PROCESSED_DIR / f"file_plausibility_{date}.csv"
    keys_file = PROCESSED_DIR / f"file_keys_{date}.csv"
    review_file = REVIEW_DIR / f"sample_records_{date}.xlsx"
    kept_profiles, kept_columns, kept_checks, kept_formats, kept_structures = [], [], [], [], []
    kept_plausibility, kept_keys = [], []
    if args.only:          # a partial run keeps the results of the other datasets
        if profiles_file.exists():
            kept_profiles = [row for row in read_csv(profiles_file) if row["sample_id"] not in wanted]
        if columns_file.exists():
            kept_columns = [row for row in read_csv(columns_file) if row["sample_id"] not in wanted]
        if checks_file.exists():
            kept_checks = [row for row in read_csv(checks_file) if row["sample_id"] not in wanted]
        if formats_file.exists():
            kept_formats = [row for row in read_csv(formats_file) if row["sample_id"] not in wanted]
        if structures_file.exists():
            kept_structures = [row for row in read_csv(structures_file) if row["sample_id"] not in wanted]
        if plausibility_file.exists():
            kept_plausibility = [row for row in read_csv(plausibility_file) if row["sample_id"] not in wanted]
        if keys_file.exists():
            kept_keys = [row for row in read_csv(keys_file) if row["sample_id"] not in wanted]

    print(f"Download log: {relative(log_file)}")
    print(f"Datasets to examine: {len(wanted)}")
    profiles, columns, checks, formats_rows, structure_rows, review = [], [], [], [], [], {}
    plausibility_rows_all: list[dict] = []
    key_rows_all: list[dict] = []
    for sample_id in sorted(wanted):
        org = organisation[sample_id]
        personal = sample_id in PERSONAL_DATA_SUSPECTED
        rows = [row for row in log if row["sample_id"] == sample_id]
        name = rows[0]["dataset"] if rows else sample.get(sample_id, {}).get("name", "")
        named = None if org["examined"].strip() == "all" else set(positions(org["examined"]))
        files, results, q2_results = [], {}, {}
        Q3_STATE.update(dataset=zlib.crc32(sample_id.encode("utf-8")), counter=0,
                        aligned=org["organisation"] == "formats")
        print(f"{sample_id}: {org['organisation']}", flush=True)
        for label, row, path, kind in dataset_files(sample_id, rows):
            if path is None:
                reason = row.get("reason") or "no file"
                units = [unit(kind=kind or row.get("declared_format", ""), data_file=False, readable=False,
                              ai1_reason=f"not available (Q1: {reason})")]
            elif kind not in DATA_TYPES:
                units = [unit(kind=kind, data_file=False, ai1_reason=f"not a data file ({kind})")]
            else:
                size = path.stat().st_size
                if size > 20_000_000:
                    print(f"    {label}: {path.name}, {size / 1e6:.0f} MB, please wait", flush=True)
                Q4_STATE["until"] = download_date(row, path)
                try:
                    units = examine_file(path, kind)
                except Exception as error:      # one damaged file must not stop the examination of the others
                    units = [unit(kind=kind, readable=False, error=f"{type(error).__name__}: {str(error)[:120]}",
                                  ai1_score=0, ai1_reason="the file cannot be read")]
            for record in units:
                record.update(sample_id=sample_id, position=label, resource_id=row.get("resource_id", ""),
                              file=relative(path) if path else "",
                              examined=record["data_file"] is True and (named is None or label in named))
                if personal:
                    record["column_names"] = ""
                q2_unit(record, personal)
                unit_q3(record, personal)
                unit_q4(record, personal)
            if any(record["data_file"] is True for record in units):
                results[label] = file_result(units)
                q2_results[label] = q2_file(units)
            files.append((label, path.name if path else "", units))
            profiles += units
        examined = set(results) if named is None else named
        judged = judge_dataset(org, results)
        score, reason, decisive = judged
        q2 = judge_q2(org, q2_results, personal)
        tally = q2["tally"]
        hashes = {f"r{int(row['position']):03d}": row.get("sha256", "") for row in rows
                  if row.get("outcome") == "available" and row.get("sha256")}
        q3 = judge_q3(org, files, personal, hashes)
        examined_q3 = any(q3["found"][key] for key in ("columns", "structures", "major", "minor"))
        q4 = judge_q4(org, files, personal)
        ai6 = judge_ai6(org, files, personal, rows)
        checks.append({"sample_id": sample_id, "dataset": name, "organisation": org["organisation"],
                       "examined": org["examined"], "combine": org["combine"],
                       "files_examined": len([label for label in examined if label in results]),
                       "ai1_score": score, "ai1_reason": reason, "decisive": decisive,
                       "q2_score": q2["score"], "q2_reason": q2["reason"], "q2_decisive": q2["decisive"],
                       "q2_records": tally.records if tally else "", "q2_cells": tally.cells if tally else "",
                       "q2_missing": tally.missing if tally else "",
                       "q2_placeholders": tally.placeholders if tally else "",
                       "q2_share": f"{100 * tally.share():.2f}" if tally and tally.cells else "",
                       "q2_empty_columns": len(tally.empty_columns()) if tally else "",
                       "q2_notes": "; ".join(q2.get("notes", [])),
                       "q3_score": q3["score"], "q3_reason": q3["reason"],
                       "q3_major": len(q3["found"]["major"]) if examined_q3 else "",
                       "q3_minor": len(q3["found"]["minor"]) if examined_q3 else "",
                       "q3_notes": "; ".join(q3["notes"]),
                       "q4_score": q4["score"], "q4_reason": q4["reason"], "q4_records": q4["records"],
                       "q4_implausible": q4["implausible"], "q4_share": q4["share"],
                       "q4_notes": "; ".join(q4["notes"]),
                       "ai6_score": ai6["score"], "ai6_reason": ai6["reason"], "ai6_keys": ai6["keys"],
                       "ai6_notes": "; ".join(ai6["notes"])})
        formats_rows += [dict(row, sample_id=sample_id) for row in q3["found"]["columns"]]
        structure_rows += [dict(row, sample_id=sample_id) for row in q3["found"]["structures"]]
        plausibility_rows_all += [dict(row, sample_id=sample_id) for row in q4["columns"]]
        key_rows_all += [dict(row, sample_id=sample_id) for row in ai6["found"]]
        review[sample_id] = {"title": titles.get(sample_id, name), "personal": personal, "reason": q3["reason"],
                             "sections": q3["sample"], "findings": review_findings(q3) + review_findings_q4(q4)}
        for label, _, units in files:
            if label not in examined:
                continue
            for record in units:
                if record.get("_tally") is None:
                    continue
                entries = record["_tally"].columns.values()
                for number, (column_name, cells, empty, placeholders) in enumerate(entries, 1):
                    columns.append({"sample_id": sample_id, "position": label, "member": record["member"],
                                    "sheet": record["sheet"], "scope": record["_tally"].scope, "column": number,
                                    "name": "" if personal else column_name, "cells": cells, "empty": empty,
                                    "placeholders": placeholders,
                                    "share": f"{100 * (empty + placeholders) / cells:.2f}" if cells else ""})
        print(f"    AI1 {score_text(score)}: {reason[:120]}", flush=True)
        print(f"    Q2 {score_text(q2['score'])}: {q2['reason'][:120]}", flush=True)
        print(f"    Q3 {score_text(q3['score'])}: {q3['reason'][:120]}", flush=True)
        print(f"    Q4 {score_text(q4['score'])}: {q4['reason'][:120]}", flush=True)
        print(f"    AI6 {score_text(ai6['score'])}: {ai6['reason'][:120]}", flush=True)
        write_factsheet(out_dir / "factsheets" / f"{sample_id}.md", sample_id, titles.get(sample_id, name), name, org,
                        files, judged, examined, date, q2, q3, q4, ai6)
        for _, _, units in files:              # the forms of the values are no longer needed
            for record in units:
                record.pop("_formats", None)

    for row in kept_checks:
        row["ai1_score"] = None if row["ai1_score"] in ("n/d", "") else int(row["ai1_score"])
    all_checks = sorted(kept_checks + checks, key=lambda row: row["sample_id"])
    for record in profiles:
        record["ai1_score"] = score_text(record["ai1_score"])
        record["q4_score"] = score_text(record.get("q4_score", ""))
    write_csv(profiles_file, PROFILE_FIELDS, sorted(kept_profiles + profiles, key=lambda row: (row["sample_id"], row["position"])))
    write_csv(columns_file, COLUMN_FIELDS, sorted(kept_columns + columns, key=lambda row: row["sample_id"]))
    write_csv(checks_file, CHECK_FIELDS, [dict(row, ai1_score=score_text(row["ai1_score"]),
                                               q2_score=score_text(row.get("q2_score", "")),
                                               q3_score=score_text(row.get("q3_score", "")),
                                               q4_score=score_text(row.get("q4_score", "")),
                                               ai6_score=score_text(row.get("ai6_score", ""))) for row in all_checks])
    write_csv(formats_file, FORMAT_FIELDS, sorted(kept_formats + formats_rows, key=lambda row: row["sample_id"]))
    write_csv(structures_file, STRUCTURE_FIELDS,
              sorted(kept_structures + structure_rows, key=lambda row: row["sample_id"]))
    write_csv(plausibility_file, PLAUSIBILITY_FIELDS,
              sorted(kept_plausibility + plausibility_rows_all, key=lambda row: row["sample_id"]))
    write_csv(keys_file, KEY_FIELDS, sorted(kept_keys + key_rows_all, key=lambda row: row["sample_id"]))
    write_summary(out_dir / "file_checks.md", all_checks, date, titles)
    write_review_sample(review_file, review, partial=bool(args.only))
    for criterion, field in (("AI1", "ai1_score"), ("Q2", "q2_score"), ("Q3", "q3_score"), ("Q4", "q4_score"),
                             ("AI6", "ai6_score")):
        scores = Counter(score_text(row.get(field, "")) for row in all_checks)
        print(f"Proposed {criterion}: "
              + ", ".join(f"{key or 'none'}: {value}" for key, value in sorted(scores.items())))
    print("Files:")
    for path in (profiles_file, columns_file, checks_file, formats_file, structures_file, plausibility_file,
                 keys_file, out_dir / "file_checks.md", out_dir / "factsheets"):
        print(f"  {relative(path)}")
    print(f"Local review file (records of the data, not part of the repository): {relative(review_file)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
