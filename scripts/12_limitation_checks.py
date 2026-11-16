r"""
12_limitation_checks.py
Phase 3, step 3: evidence on the limitations that the publishers of the datasets of the sample declare (criterion
AI7: do the metadata or the documentation state the known limitations of the data).

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one), the sample
     (data/processed/sample.csv) and the tables of 05_resource_download.py (download log), 06_file_checks.py (file
     checks, file profiles) and 09_history_checks.py (history checks).
  2. Counts, in the whole catalogue:
       - the datasets without a description, those whose description only repeats the title (it adds fewer than
         25 letters to it, as in 08_documentation_checks.py) and those whose description says more, by length;
       - the datasets in which the description of the dataset or of one of its resources holds a word that points
         to a statement of limitations: about what is missing, about the source or the method, about accuracy or
         errors; and those with the general phrase that the data are given as they are or that no liability is
         accepted. The words are an indicator: whether a statement is made is judged only in the sample;
       - the datasets that fill a field in which the origin or the quality of the data could be stated: the
         provenance (provenance), the notes on the version (version_info) and the lineage of an ISO 19115 record
         among the additional metadata (iso_lineage);
       - the datasets whose type is declared as synthetic data.
  3. Collects, for every dataset of the sample, the texts in which its publisher could state a limitation: the
     description of the dataset, the descriptions of its resources that differ from the name of the resource,
     from the title and from the description of the dataset, the documents published among the resources, the
     pages of the publisher that the metadata link to, and the fields of point 2. The descriptions that the
     harvester of the portal writes for the resources of a map layer (they name the layer and the kind of the
     resource) are left out. The words of point 2 that these texts hold are listed.
  4. Extracts the text of every PDF document among the files obtained and records the pages on which the same
     words are found. The text itself is not kept.
  5. Sets next to the texts what the earlier checks found in the examined files: the records, the empty cells
     (Q2), the implausible values (Q4), the period that the files cover and the periods missing from it (AI3),
     with the temporal coverage of the metadata. In the examined GTFS feeds it counts the stop times whose
     pickup_type or drop_off_type is other than 0 (a regular stop): the restrictions on boarding and alighting
     that the feed itself records. They are counted by the codes of the GTFS reference (1, 2, 3); any other
     value is counted without being written.
  6. Proposes a score only where a rule decides without judgement: 0 when the texts of a dataset say no more than
     its name, hold none of the words sought, and the dataset has neither a document nor a link to a page of its
     publisher. Every other dataset is marked "by hand" and is judged in the review of the criterion.
  7. Writes:
        data/processed/limitation_checks_YYYY-MM-DD.csv       one row per dataset of the sample: the texts, the
                                                               evidence and the proposal
        data/processed/limitation_catalogue_YYYY-MM-DD.csv    the counts of the whole catalogue
        outputs/limitations_YYYY-MM-DD/limitation_checks.md   the same as a report
     The date in the names is the date of the snapshot. The texts written are descriptions that the publishers
     wrote in the metadata. None of the files contains a value of a record, and of the documents only numbers of
     pages are written.

Rules of AI7 (card approved on 14 November 2026):
  - The evidence is what a publisher writes in words: the description of the dataset and of its resources, the
    documents published with the data, and the pages and documents of the publisher that the dataset points to.
    The fields of temporal and geographical coverage are not counted again: they are scored in M2, and the
    temporal coverage of many datasets is a placeholder (DECISIONS.md #47).
  - Four questions are asked: coverage (what the data cover and how far they reach), gaps (what is missing),
    collection (where the data come from and how they were produced), known errors or changes (how accurate the
    data are, which errors they have, whether the method changed).
  - The name is not a statement: a description that says only which dataset it is (subject, place, year) answers
    none of the questions, as in AI4 (DECISIONS.md #48). Nor does the general phrase that the data are given as
    they are, when it stands alone.
  - Score 0: no question is answered. Score 1: one to three questions. Score 2: all four.
  - A page or a document of the publisher counts when it opens for a visitor (DECISIONS.md #48).
  - A statement that the files contradict does not count and is recorded as a finding.
  - Datasets of which no file was obtained are judged on their texts and score 1 at most (DECISIONS.md #46 to
    #48). A dataset whose examined files were exported by hand from an application has files, and the limit does
    not apply to it (DECISIONS.md #51).
  - No record of the data and no name of a person is written.

Usage (from the project root, with the .venv activated):
    python scripts\12_limitation_checks.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

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
TITLE_MARGIN = 25                # letters that a description may add to a title and still only repeat it
LENGTHS = (100, 300, 1000)       # characters of a description, for the counts of the catalogue
WORDS_LISTED = 6                 # words of one kind listed in a cell before "and N more"
PAGES_LISTED = 15                # pages of a document or pages of a publisher listed in a cell before "and N more"
PUBLISHERS_SHOWN = 5             # names of publishers written for a count of the catalogue
FIELD_TEXT = 300                 # characters of the text of a field kept in a cell

# Formats of resources that are documents, as in 08_documentation_checks.py, and the metadata fields of DCAT-AP
# meant for the documentation of a dataset or of a resource, under the names of the catalogue API.
DOCUMENT_FORMATS = {"PDF", "DOC", "DOCX", "ODT", "RTF", "TXT"}
DOCUMENTATION_FIELDS = ("documentation", "page")
ARCHIVE_SUFFIXES = (".zip", ".rar", ".kmz")

# Fields in which a publisher could state the origin or the quality of the data: the provenance and the notes on
# the version, at the level of the dataset, and the lineage that a harvested ISO 19115 record carries among the
# additional metadata.
PROVENANCE = "provenance"
VERSION_NOTES = "version_info"
LINEAGE = "iso_lineage"
# Entry of the additional metadata that carries the name of the layer of a harvested map layer. The descriptions
# that the harvester writes for the resources of such a dataset name the layer and the kind of the resource (the
# preview of the layer, the capabilities documents of the server) and are not texts of the publisher.
LAYER_NAME = "wms_layer_name"
SYNTHETIC_TYPE = "SYNTHETIC_DATA"      # code of the EU vocabulary of dataset types

# Words that point to a statement of limitations, in Greek and in English. They are sought in text reduced to
# lower case without accents, with the final sigma written as sigma, and only at the start of a word.
WORD_KINDS = {
    "missing": ("what is missing",
                r"ελλειψ(?:η|ησ|εισ|εων)\b|ελλιπ\w*|λειπουν|δεν περιλαμβαν\w*|δεν εμφανιζ\w*|δεν περιεχ\w*|"
                r"δεν υπαρχουν (?:στοιχεια|δεδομενα)|δεν εχουν καταγραφ\w*|χωρισ (?:στοιχεια|δεδομενα)|"
                r"missing|incomplete|not includ\w*|does not include|do not include|no data\b"),
    "method": ("the source or the method",
               r"πηγη\s*:|πηγεσ\s*:|πηγη (?:των )?δεδομενων|προερχ\w*|"
               r"προελευση (?:των |τησ |του )?(?:δεδομενων|στοιχειων|πληροφορι\w*)|"
               r"συλλογη (?:και επεξεργασια|(?:των )?(?:δεδομενων|στοιχειων))|συλλεχθ\w*|ανακτηθηκ\w*|"
               r"ανακτηση (?:των )?(?:στοιχειων|δεδομενων)|ψηφιοποι\w*|"
               r"δειγματοληψ\w*|δημιουργηθηκε απο|μεθοδολογ\w*|οπωσ (?:αυτ[ηο] )?προκυπτ\w*|"
               r"source\s*:|collected|derived from|generated (?:by|from)|created from|retrieved from|"
               r"methodolog\w*|digiti[sz]ed"),
    "accuracy": ("accuracy or errors",
                 r"ακριβει\w*|ακριβεστερ\w*|ανακριβ\w*|κατα προσεγγιση|προσεγγιστικ\w*|ενδεικτικ\w*|αποκλισ\w*|"
                 r"σφαλμα\w*|προσωριν\w* (?:στοιχεια|δεδομενα|πινακ\w*)|προκαταρκτικ\w* (?:στοιχεια|δεδομενα)|"
                 r"accura\w*|inaccura\w*|approximat\w*|indicative|errors?\b|provisional"),
}
WORD_KINDS = {kind: (label, re.compile(rf"(?<!\w)(?:{pattern})")) for kind, (label, pattern) in WORD_KINDS.items()}
AS_IS = re.compile(r"(?<!\w)(?:ωσ εχ(?:ουν|ει)(?!\w)|ουδεμια ευθυνη|καμια ευθυνη|"
                   r"δεν φερ\w+ (?:καμια |ουδεμια )?ευθυνη|as is\b|no liability|without warrant\w*)")

# Stop times of a GTFS feed: the two fields that record whether passengers board and alight at a stop, the values
# that stand for a regular stop (0 or empty) and the other codes of the GTFS Schedule Reference: 1 no boarding or
# no alighting at the stop, 2 by arrangement with the agency on the telephone, 3 by arrangement with the driver.
STOP_TIMES = "stop_times.txt"
BOARDING_FIELDS = ("pickup_type", "drop_off_type")
REGULAR_STOP = {"", "0"}
BOARDING_CODES = ("1", "2", "3")
OTHER_VALUES = "other values"

CHECK_FIELDS = [
    "sample_id", "dataset", "group", "category", "data_kind", "files_obtained", "title", "description",
    "description_characters", "description_repeats_title", "resources", "resources_with_description",
    "resource_descriptions", "resource_description_texts", "documents_among_resources", "publisher_pages",
    "origin_fields", "words_missing", "words_method", "words_accuracy", "as_is_phrase", "documents_read",
    "records_in_files", "empty_cells", "implausible_values", "temporal_coverage", "period_found",
    "periods_missing", "boarding_restrictions", "ai7_proposal", "ai7_reason",
]
CATALOGUE_FIELDS = ["measure", "count", "of", "share", "note"]


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


def listed(items: list[str], limit: int, separator: str = ", ") -> str:
    """The first items of a list and the number of those left out."""
    shown = separator.join(items[:limit])
    return shown + (f"{separator}and {len(items) - limit} more" if len(items) > limit else "")


def position_label(value) -> str:
    """The label of a resource in the tables of the files: r001, r002 and so on."""
    text = str(value or "")
    return text if text.startswith("r") else f"r{number(text):03d}"


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


def folded(value) -> str:
    """A text in lower case without accents, the final sigma written as sigma: the form in which words are
    sought."""
    text = unicodedata.normalize("NFD", str(value or "").lower())
    return "".join(character for character in text if unicodedata.category(character) != "Mn").replace("ς", "σ")


def letters_only(value) -> str:
    """A text reduced to its letters and digits, without accents and in lower case, for comparisons, as in
    08_documentation_checks.py."""
    text = unicodedata.normalize("NFD", plain_text(value).lower())
    text = "".join(character for character in text if unicodedata.category(character) != "Mn")
    return re.sub(r"[\W_]+", " ", text).strip()


def only_repeats(text, name) -> bool:
    """Whether a text only repeats a name: it is equal to it, a part of it, or adds fewer than TITLE_MARGIN
    letters to it. An empty text repeats every name."""
    short_text, short_name = letters_only(text), letters_only(name)
    if not short_text:
        return True
    if not short_name:
        return False
    return (short_text == short_name or short_text in short_name
            or (short_name in short_text and len(short_text) - len(short_name) < TITLE_MARGIN))


def has_content(value) -> bool:
    """Whether a metadata value holds anything: a list or a structure whose elements are all blank holds nothing."""
    if isinstance(value, dict):
        return any(has_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_content(item) for item in value)
    return value is not None and str(value).strip() != ""


def additional_metadata(dataset: dict) -> dict:
    """The filled entries of the additional metadata of a dataset (extras), by key."""
    entries = {}
    for item in dataset.get("extras") or []:
        if isinstance(item, dict) and item.get("key") and has_content(item.get("value")):
            entries[str(item["key"])] = item["value"]
    return entries


def addresses_in(value) -> list[str]:
    """The web addresses that a metadata value holds, whether it is a text, a list or a structure."""
    if isinstance(value, dict):
        return [address for item in value.values() for address in addresses_in(item)]
    if isinstance(value, (list, tuple)):
        return [address for item in value for address in addresses_in(item)]
    return re.findall(r"https?://[^\s\"'<>]+", str(value or ""))


def words_in(text: str) -> dict[str, list[str]]:
    """The words of each kind found in a folded text, each once, in the order in which they are first met."""
    found = {}
    for kind, (_, pattern) in WORD_KINDS.items():
        words = []
        for match in pattern.finditer(text):
            word = re.sub(r"\s+", " ", match.group(0)).strip()
            if word not in words:
                words.append(word)
        found[kind] = words
    return found


def own_texts(dataset: dict) -> list[str]:
    """The description of a dataset and the different descriptions of its resources, as plain text."""
    texts = [plain_text(dataset.get("notes"))]
    for resource in own_resources(dataset):
        text = plain_text(resource.get("description"))
        if text and text not in texts:
            texts.append(text)
    return [text for text in texts if text]


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
    11_retrieval_checks.py."""

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

    def file_of(self, profile: dict) -> Path:
        """The file of a table on disk."""
        self.release()
        path = ROOT / profile["file"]
        if not path.is_file():
            raise TableNotRead("the downloaded file is not in data/raw/resources")
        member = profile.get("member") or ""
        return self.member(path, member) if member else path


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def read_catalogue(snapshot: Path, sample: dict[str, dict]) -> tuple[dict[str, dict], dict]:
    """The records of the datasets of the sample, by sample id, and the counts of the whole catalogue."""
    by_id = {row["id"]: row["sample_id"] for row in sample.values()}
    found: dict[str, dict] = {}
    counts = {"datasets": 0, "empty": 0, "repeats": 0, "more": 0, "longer": Counter(), "words": Counter(),
              "any_word": 0, "as_is": 0, "provenance": 0, "provenance_present": 0, "version_notes": 0,
              "lineage": 0, "synthetic": 0, "synthetic_publishers": Counter()}
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("id") in by_id:
                found[by_id[record["id"]]] = record
            if record.get("type") != "dataset":
                continue
            counts["datasets"] += 1
            notes = plain_text(record.get("notes"))
            if not letters_only(notes):
                counts["empty"] += 1
            elif only_repeats(notes, record.get("title")):
                counts["repeats"] += 1
            else:
                counts["more"] += 1
                for length in LENGTHS:
                    counts["longer"][length] += len(notes) >= length
            text = folded(" | ".join(own_texts(record)))
            kinds = [kind for kind, words in words_in(text).items() if words]
            counts["words"].update(kinds)
            counts["any_word"] += bool(kinds)
            counts["as_is"] += bool(AS_IS.search(text))
            counts["provenance"] += has_content(record.get(PROVENANCE))
            counts["provenance_present"] += PROVENANCE in record
            counts["version_notes"] += has_content(record.get(VERSION_NOTES))
            counts["lineage"] += LINEAGE in additional_metadata(record)
            types = record.get("dcat_type") or []
            types = types if isinstance(types, list) else [types]
            if any(str(item).rstrip("/").rsplit("/", 1)[-1] == SYNTHETIC_TYPE for item in types):
                counts["synthetic"] += 1
                organisation = record.get("organization") if isinstance(record.get("organization"), dict) else {}
                counts["synthetic_publishers"][str(organisation.get("name") or "not stated")] += 1
    return found, counts


def publishers_text(publishers: Counter) -> str:
    """The publishers behind a count of the catalogue: how many they are and the names of the largest."""
    if not publishers:
        return ""
    names = [name for name, _ in sorted(publishers.items(), key=lambda item: (-item[1], item[0]))]
    return f"{with_noun(len(names), 'publisher')}: {listed(names, PUBLISHERS_SHOWN)}"


def catalogue_rows(counts: dict) -> list[dict]:
    """The counts of the catalogue as rows of a table."""
    total = counts["datasets"]

    def row(measure: str, count: int, note: str = "") -> dict:
        share = f"{100 * count / total:.1f}" if total else ""
        return {"measure": measure, "count": count, "of": total, "share": share, "note": note}

    indicator = ("indicator: the words are sought in the description of the dataset and of its resources; whether "
                 "a statement is made is judged only in the sample")
    rows = [
        {"measure": "datasets of the catalogue", "count": total, "of": "", "share": "", "note": ""},
        row("datasets without a description", counts["empty"]),
        row("datasets whose description only repeats the title", counts["repeats"],
            f"the description adds fewer than {TITLE_MARGIN} letters to the title, as in "
            "08_documentation_checks.py; 04_metadata_checks.py counts the descriptions equal to the title"),
        row("datasets whose description says more than the title", counts["more"]),
    ]
    rows += [row(f"datasets whose description says more than the title in at least {length:,} characters",
                 counts["longer"][length]) for length in LENGTHS]
    rows += [row(f"datasets with a word about {label} in a description", counts["words"][kind], indicator)
             for kind, (label, _) in WORD_KINDS.items()]
    rows += [
        row("datasets with a word of at least one of the three kinds in a description", counts["any_word"],
            indicator),
        row("datasets with the phrase that the data are given as they are or that no liability is accepted",
            counts["as_is"], indicator),
        row(f"datasets that fill a field for the provenance of the data ({PROVENANCE})", counts["provenance"],
            "" if counts["provenance_present"] else "no record of the catalogue has a field of this name"),
        row(f"datasets that fill the notes on the version ({VERSION_NOTES})", counts["version_notes"]),
        row(f"datasets with the lineage of an ISO 19115 record among the additional metadata ({LINEAGE})",
            counts["lineage"]),
        row(f"datasets whose type is declared as synthetic data ({SYNTHETIC_TYPE})", counts["synthetic"],
            publishers_text(counts["synthetic_publishers"])),
    ]
    return rows


# ---------------------------------------------------------------------------
# Evidence of the texts
# ---------------------------------------------------------------------------

def text_evidence(dataset: dict, positions: dict[str, str]) -> dict:
    """The texts of a dataset in which a limitation could be stated, and the words that they hold."""
    title = plain_text(dataset.get("title"))
    notes = plain_text(dataset.get("notes"))
    resources = own_resources(dataset)
    extras = additional_metadata(dataset)
    layer = str(extras.get(LAYER_NAME) or "").strip().lower()
    described = 0
    groups: dict[str, list[str]] = {}
    for resource in resources:
        text = plain_text(resource.get("description"))
        if not text:
            continue
        described += 1
        if letters_only(text) in (letters_only(resource.get("name")), letters_only(title), letters_only(notes)):
            continue
        if layer and layer in text.lower():
            continue
        groups.setdefault(text, []).append(positions.get(str(resource.get("id") or ""), ""))
    descriptions = []
    for text, places in groups.items():
        places = [place for place in places if place]
        label = listed(places, 3) if places else with_noun(len(groups[text]), "resource")
        descriptions.append(f"[{label}] {text}")
    documents = [f"{positions.get(str(resource.get('id') or ''), '')} "
                 f"{str(resource.get('format') or '').strip().upper()}".strip()
                 for resource in resources if str(resource.get("format") or "").strip().upper() in DOCUMENT_FORMATS]
    pages = []
    declared = dataset.get("landing_page") or []
    declared = declared if isinstance(declared, list) else [declared]
    written = re.findall(r'href="([^"]+)"', str(dataset.get("notes") or "")) + addresses_in(notes)
    for resource in resources:
        written += addresses_in(plain_text(resource.get("description")))
    documented = [address for name in DOCUMENTATION_FIELDS
                  for address in addresses_in([dataset.get(name), extras.get(name),
                                               [resource.get(name) for resource in resources]])]
    for address in [*documented, *declared, dataset.get("url"), *written]:
        address = html.unescape(str(address or "")).strip().rstrip(".,;)")
        if address.startswith("http") and address not in pages:
            pages.append(address)
    origin = [f"{name}: {plain_text(dataset.get(name))[:FIELD_TEXT]}" for name in (PROVENANCE, VERSION_NOTES)
              if has_content(dataset.get(name))]
    if LINEAGE in extras:
        origin.append(f"{LINEAGE}: {plain_text(extras[LINEAGE])[:FIELD_TEXT]}")
    text = folded(" | ".join(own_texts(dataset) + origin))
    words = words_in(text)
    return {
        "title": title,
        "description": notes,
        "description_characters": len(notes),
        "description_repeats_title": "yes" if only_repeats(notes, title) else "no",
        "resources": len(resources),
        "resources_with_description": described,
        "resource_descriptions": len(descriptions),
        "resource_description_texts": " | ".join(descriptions),
        "documents_among_resources": ", ".join(documents),
        "publisher_pages": listed(pages, PAGES_LISTED, " ; "),
        "pages_linked": len(pages),
        "origin_fields": " | ".join(origin),
        **{f"words_{kind}": listed(found, WORDS_LISTED, "; ") for kind, found in words.items()},
        "as_is_phrase": "yes" if AS_IS.search(text) else "no",
    }


# ---------------------------------------------------------------------------
# Evidence of the documents
# ---------------------------------------------------------------------------

def pdf_words(path: Path) -> dict:
    """The pages of a PDF document and, for each kind of words, the pages on which a word is found. The text is
    not kept."""
    found = {"pages": 0, "with_text": 0, "error": "", **{kind: [] for kind in WORD_KINDS}}
    if not path.is_file():
        found["error"] = "the downloaded file is not in data/raw/resources"
        return found
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
            text = folded(re.sub(r"\s+", " ", content))
            found["with_text"] += bool(text.strip())
            for kind, words in words_in(text).items():
                if words:
                    found[kind].append(found["pages"])
    except Exception as error:      # pypdf raises its own exceptions on damaged or protected files
        found["error"] = f"PDF not read ({type(error).__name__})"
    return found


def pdf_summary(position: str, found: dict) -> str:
    if found["error"]:
        return f"{position}: {found['error']}"
    parts = [f"{position}: PDF of {with_noun(found['pages'], 'page')}, text on {found['with_text']:,}"]
    for kind, (label, _) in WORD_KINDS.items():
        pages = [str(page) for page in found[kind]]
        if pages:
            parts.append(f"words about {label} on {with_noun(len(pages), 'page')} ({listed(pages, PAGES_LISTED)})")
    if len(parts) == 1:
        parts.append("none of the words sought")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Evidence of the files
# ---------------------------------------------------------------------------

def file_evidence(check: dict) -> dict:
    """What 06_file_checks.py found in the examined files of a dataset: records, empty cells, implausible values."""
    cells, missing = number(check.get("q2_cells")), number(check.get("q2_missing"))
    placeholders = number(check.get("q2_placeholders"))
    empty = ""
    if cells:
        empty = (f"{missing:,} of {cells:,} cells ({check.get('q2_share', '')}%)" if missing
                 else f"none of {cells:,} cells")
        if placeholders:
            empty += f", {placeholders:,} of them placeholders"
    examined, implausible = number(check.get("q4_records")), number(check.get("q4_implausible"))
    doubtful = ""
    if examined:
        doubtful = (f"{implausible:,} of {examined:,} records ({check.get('q4_share', '')}%)" if implausible
                    else f"none of {examined:,} records")
    return {"records_in_files": number(check.get("q2_records")) or "", "empty_cells": empty,
            "implausible_values": doubtful}


def history_evidence(check: dict) -> dict:
    """What 09_history_checks.py found: the period that the files or the resources cover and the periods missing
    from it, with the temporal coverage of the metadata."""
    period, missing = [], []
    for source, place, among in (("file", "in the files", "in the files"),
                                 ("resource", "in the names of the resources", "among the resources")):
        first, last = check.get(f"{source}_period_first", ""), check.get(f"{source}_period_last", "")
        if not first:
            continue
        period.append(f"{place}: {first}" if first == last else f"{place}: first {first}, last {last}")
        if check.get(f"{source}_periods_missing"):
            missing.append(f"{among}: {check[f'{source}_periods_missing']}")
    if check.get("timetable_validity"):
        period.append(f"validity of the timetable: {check['timetable_validity']}")
    return {"temporal_coverage": check.get("temporal_coverage", ""), "period_found": "; ".join(period),
            "periods_missing": "; ".join(missing)}


def boarding_restrictions(profile: dict, files: Extracted) -> str:
    """The stop times of one GTFS feed whose pickup_type or drop_off_type is other than 0, in words."""
    where = f"{profile['position']} {STOP_TIMES}"
    try:
        path = files.file_of(profile)
        encoding = profile.get("encoding") or "utf-8-sig"
        delimiter = "\t" if profile.get("delimiter") == "tab" else (profile.get("delimiter") or ",")
        first = max(number(profile.get("header_row")), 1)
        records = restricted = 0
        values = {name: Counter() for name in BOARDING_FIELDS}
        with open(path, encoding=encoding, errors="replace", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            for _ in range(first - 1):
                next(reader, None)
            names = [cell.strip() for cell in next(reader, [])]
            indexes = {name: names.index(name) for name in BOARDING_FIELDS if name in names}
            if not indexes:
                return f"{where}: neither pickup_type nor drop_off_type among the columns"
            for row in reader:
                if not any(row):
                    continue
                records += 1
                marked = False
                for name, index in indexes.items():
                    value = row[index].strip() if index < len(row) else ""
                    if value not in REGULAR_STOP:
                        values[name][value if value in BOARDING_CODES else OTHER_VALUES] += 1
                        marked = True
                restricted += marked
    except TableNotRead as error:
        return f"{where}: not read ({error})"
    except (OSError, UnicodeError, csv.Error, zipfile.BadZipFile) as error:
        return f"{where}: not read ({type(error).__name__})"
    if not restricted:
        return (f"{where}: none of {with_noun(records, 'stop time')} has a {' or '.join(indexes)} other than 0 "
                "(a regular stop)")
    detail = "; ".join(f"{name} {value}: {values[name][value]:,}" for name in indexes
                       for value in (*BOARDING_CODES, OTHER_VALUES) if values[name][value])
    return (f"{where}: {restricted:,} of {with_noun(records, 'stop time')} with a {' or '.join(indexes)} other "
            f"than 0 ({detail})")


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------

def propose(evidence: dict) -> tuple[str, str]:
    """The proposed score of AI7 where a rule decides without judgement, otherwise the mark of the review."""
    places = []
    if evidence["description_repeats_title"] == "no":
        places.append(f"the description of the dataset ({with_noun(evidence['description_characters'], 'character')})")
    if evidence["resource_descriptions"]:
        places.append(with_noun(evidence["resource_descriptions"], "description") + " of resources")
    if evidence["documents_among_resources"]:
        places.append(f"documents among the resources ({evidence['documents_among_resources']})")
    if evidence["pages_linked"]:
        places.append(with_noun(evidence["pages_linked"], "page") + " of the publisher that the metadata link to")
    if evidence["origin_fields"]:
        places.append("the fields on the origin of the data")
    limit = ("" if evidence["files_obtained"] or evidence["records_in_files"] != ""
             else "; no file of the dataset was obtained: 1 at most")
    words = [f"{label}: {evidence[f'words_{kind}']}" for kind, (label, _) in WORD_KINDS.items()
             if evidence[f"words_{kind}"]]
    if not places and not words:
        start = ("the dataset has no description" if not evidence["description_characters"]
                 else "the description only repeats the title")
        return "0", (f"{start}, no description of a resource says more than the name of the resource, and the "
                     "dataset has neither a document nor a link to a page of its publisher: no text in which a "
                     "limitation could be stated")
    if not places:
        places.append(f"the description of the dataset, which adds fewer than {TITLE_MARGIN} letters to the title")
    marks = f"; words about {'; about '.join(words)}" if words else "; none of the words sought in these texts"
    return BY_HAND, f"to be read: {', '.join(places)}{marks}{limit}"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(path: Path, checks: list[dict], catalogue: list[dict], date: str) -> None:
    proposals = Counter(row["ai7_proposal"] for row in checks)
    lines = [
        f"# Limitations declared for the datasets of the sample (AI7), snapshot of {date}",
        "",
        "Produced by `scripts/12_limitation_checks.py`. The tables collect the evidence for the review of the "
        "criterion; a score is proposed only where a rule decides without judgement, and the final scores are "
        "recorded in `DECISIONS.md`. The texts quoted are descriptions that the publishers wrote in the metadata. "
        "This report contains no value of a record, and of the documents only numbers of pages.",
        "",
        "## In the whole catalogue",
        "",
        "| Measure | Datasets | Share | Note |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in catalogue:
        share = f"{row['share']}%" if row["share"] != "" else ""
        lines.append(f"| {md_cell(row['measure'])} | {row['count']:,} | {share} | {md_cell(row['note'])} |")
    lines += ["", "## Proposals", "",
              "Proposed AI7: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", BY_HAND)
                                           if proposals[score]) + ".",
              "",
              "| Dataset | Kind of data | Proposal | Reason |",
              "| --- | --- | --- | --- |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} {md_cell(row['title'][:60])} | {row['data_kind']} | "
                     f"{row['ai7_proposal']} | {md_cell(row['ai7_reason'])} |")
    lines += ["", "## Where a limitation could be stated", "",
              "A description repeats the title when it adds fewer than "
              f"{TITLE_MARGIN} letters to it. The descriptions of resources counted are those that differ from "
              "the name of the resource, from the title and from the description of the dataset. The words are an "
              "indicator, not a judgement.",
              "",
              "| Dataset | Description, characters | Repeats the title | Resources | With a description | "
              "Descriptions that say more | Documents | Pages of the publisher | Words: what is missing | Words: "
              "source or method | Words: accuracy or errors | Given as they are |",
              "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- | --- | --- | --- |"]
    for row in checks:
        lines.append(f"| {row['sample_id']} | {row['description_characters']:,} | "
                     f"{row['description_repeats_title']} | {row['resources']} | "
                     f"{row['resources_with_description']} | {row['resource_descriptions']} | "
                     f"{md_cell(row['documents_among_resources'])} | {row['pages_linked']} | "
                     f"{md_cell(row['words_missing'])} | {md_cell(row['words_method'])} | "
                     f"{md_cell(row['words_accuracy'])} | {row['as_is_phrase']} |")
    lines += ["", "## What the earlier checks found in the examined files", "",
              "From `06_file_checks.py` (records, empty cells, implausible values) and `09_history_checks.py` "
              "(periods). The stop times are counted in the examined GTFS feeds. In the GTFS Schedule Reference "
              "the value 1 of `pickup_type` or `drop_off_type` stands for no boarding or no alighting at the stop, "
              "2 for an arrangement with the agency on the telephone and 3 for an arrangement with the driver.",
              "",
              "| Dataset | Records | Empty cells | Implausible values | Temporal coverage of the metadata | Period "
              "found | Periods missing | Stop times with a restriction on boarding or alighting |",
              "| --- | ---: | --- | --- | --- | --- | --- | --- |"]
    for row in checks:
        records = f"{row['records_in_files']:,}" if row["records_in_files"] != "" else ""
        lines.append(f"| {row['sample_id']} | {records} | {md_cell(row['empty_cells'])} | "
                     f"{md_cell(row['implausible_values'])} | {md_cell(row['temporal_coverage'])} | "
                     f"{md_cell(row['period_found'])} | {md_cell(row['periods_missing'])} | "
                     f"{md_cell(row['boarding_restrictions'])} |")
    lines += ["", "## Documents among the files obtained", "",
              "| Dataset | PDF documents and the pages with the words sought |",
              "| --- | --- |"]
    documents = [row for row in checks if row["documents_read"]]
    for row in documents:
        lines.append(f"| {row['sample_id']} | {md_cell(row['documents_read'])} |")
    if not documents:
        lines.append("| - | none |")
    lines += ["", "## Texts of the publishers", "",
              "The descriptions that say more than the title, the descriptions of resources that differ from the "
              "name of the resource, the pages that the metadata link to and the fields on the origin of the data."]
    for row in checks:
        parts = []
        if row["description_repeats_title"] == "no":
            parts.append(f"- Description: {row['description']}")
        if row["resource_description_texts"]:
            parts.append(f"- Descriptions of resources: {row['resource_description_texts']}")
        if row["publisher_pages"]:
            parts.append(f"- Pages of the publisher: {row['publisher_pages']}")
        if row["origin_fields"]:
            parts.append(f"- Fields on the origin of the data: {row['origin_fields']}")
        if parts:
            lines += ["", f"### {row['sample_id']} {row['title']}", ""] + parts
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argparse.ArgumentParser(description="Evidence on the limitations declared for the datasets of the sample "
                                        "(criterion AI7).").parse_args()
    csv.field_size_limit(2 ** 31 - 1)
    logging.getLogger("pypdf").setLevel(logging.ERROR)      # remarks of the library on the structure of a PDF file

    snapshot = newest_snapshot()
    date = snapshot_date(snapshot)
    sample = {row["sample_id"]: row for row in read_csv(SAMPLE_FILE)}
    scripts = {"resource_downloads": "05_resource_download.py", "file_checks": "06_file_checks.py",
               "file_profiles": "06_file_checks.py", "history_checks": "09_history_checks.py"}
    inputs = {name: PROCESSED_DIR / f"{name}_{date}.csv" for name in scripts}
    for name, needed in inputs.items():
        if not needed.exists():
            raise SystemExit(f"{relative(needed)} not found. Run {scripts[name]} first.")
    log, file_checks, profiles, history = (read_csv(inputs[name]) for name in scripts)
    file_checks = {row["sample_id"]: row for row in file_checks}
    history = {row["sample_id"]: row for row in history}
    organisation = {row["sample_id"]: row for row in read_csv(ORGANISATION_FILE)}
    checks_file = PROCESSED_DIR / f"limitation_checks_{date}.csv"
    catalogue_file = PROCESSED_DIR / f"limitation_catalogue_{date}.csv"
    report_file = OUT_DIR / f"limitations_{date}" / "limitation_checks.md"

    print(f"Snapshot: {relative(snapshot)}")
    print(f"Text of the PDF documents: pypdf {pypdf.__version__}")
    records, counts = read_catalogue(snapshot, sample)
    print(f"Datasets of the catalogue: {counts['datasets']:,}; of the sample: {len(sample)}")
    absent = sorted(set(sample) - set(records))
    if absent:
        raise SystemExit(f"Datasets of the sample that the snapshot does not hold: {', '.join(absent)}")

    checks = []
    for sample_id in sorted(sample):
        entry = organisation.get(sample_id, {})
        own_log = [row for row in log if row["sample_id"] == sample_id]
        positions = {row["resource_id"]: position_label(row["position"]) for row in own_log}
        obtained = sum(1 for row in own_log if row.get("outcome") == "available")
        evidence = text_evidence(records[sample_id], positions)
        documents = [pdf_summary(position_label(row["position"]), pdf_words(ROOT / row["file"]))
                     for row in own_log
                     if row.get("outcome") == "available" and row.get("detected_type") == "pdf" and row.get("file")]
        feeds = [row for row in profiles if row["sample_id"] == sample_id and row.get("kind") == "gtfs"
                 and row.get("examined") == "True"
                 and (row.get("member") or "").lower().rsplit("/", 1)[-1] == STOP_TIMES]
        if feeds:
            print(f"{sample_id}: reading the stop times of {with_noun(len(feeds), 'GTFS feed')} "
                  f"({sum(number(row.get('rows')) for row in feeds):,} rows)", flush=True)
        files = Extracted()
        try:
            restrictions = [boarding_restrictions(row, files) for row in feeds]
        finally:
            files.close()
        missing = entry.get("no_data_file", "").strip()
        examined = {row["position"] for row in profiles if row["sample_id"] == sample_id
                    and row.get("data_file") == "True" and row.get("examined") == "True"}
        among_resources = {position_label(row["position"]) for row in own_log if row.get("outcome") == "available"}
        kind = missing or ("data files" if examined & among_resources
                           else "no data file among the resources obtained")
        evidence.update({"sample_id": sample_id, "dataset": sample[sample_id].get("name", ""),
                         "group": sample[sample_id].get("group", ""),
                         "category": sample[sample_id].get("category", ""), "data_kind": kind,
                         "files_obtained": obtained, "documents_read": "; ".join(documents),
                         **file_evidence(file_checks.get(sample_id, {})),
                         **history_evidence(history.get(sample_id, {})),
                         "boarding_restrictions": "; ".join(restrictions)})
        evidence["ai7_proposal"], evidence["ai7_reason"] = propose(evidence)
        checks.append(evidence)
        print(f"{sample_id} AI7 {evidence['ai7_proposal']}: {evidence['ai7_reason'][:150]}", flush=True)

    catalogue = catalogue_rows(counts)
    write_csv(checks_file, CHECK_FIELDS, checks)
    write_csv(catalogue_file, CATALOGUE_FIELDS, catalogue)
    write_report(report_file, checks, catalogue, date)

    proposals = Counter(check["ai7_proposal"] for check in checks)
    print("Proposed AI7: " + ", ".join(f"{score}: {proposals[score]}" for score in ("0", "1", "2", BY_HAND)
                                       if proposals[score]))
    print(f"Catalogue: {counts['empty']:,} datasets without a description, {counts['repeats']:,} whose "
          f"description only repeats the title, {counts['more']:,} whose description says more; a word that "
          f"points to a statement in the descriptions of {counts['any_word']:,}")
    print("Files:")
    for path in (checks_file, catalogue_file, report_file):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
