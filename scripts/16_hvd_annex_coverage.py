r"""
16_hvd_annex_coverage.py
Phase 3, step 7: which datasets named by the Annex of Implementing Regulation (EU) 2023/138 are on the portal, part 4
of the gap analysis (DECISIONS.md #60 and #61).

What it does, in order:
  1. Reads the datasets that the Annex names, with their search patterns (criteria/hvd_annex_items.csv), and every
     dataset and data service of the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest).
  2. Searches the title, the description and the tags of every record, in Greek and in English, after lower case and
     the removal of accents, and lists the records that match each item: matches in the title first, then the records
     that declare a high-value category, then the most viewed.
  3. Where the judgement of the reviewer is recorded (criteria/hvd_annex_coverage.csv), reports for each item whether
     it is on the portal: present (the whole country, by one dataset or by several together, at the detail that the
     Annex asks), partly (some areas only, aggregates only, or part of the data), missing, or not applicable.
  4. Writes:
       - data/processed/hvd_annex_candidates_YYYY-MM-DD.csv, the matching records of each item (at most 25 per item);
       - data/processed/hvd_annex_coverage_YYYY-MM-DD.csv, one row per item, with the judgement where it exists;
       - outputs/hvd_annex_coverage_YYYY-MM-DD/summary.md and hvd_annex_coverage.xlsx.

Rules:
  - A data service of the portal counts as a dataset; the decisions of the catalogue are not data and are not searched.
  - A match is a candidate, not a finding: whether an item is on the portal is judged by the reviewer.
  - Only the metadata of the snapshot are read; no request is sent to the portal or to any other site.

Usage (from the project root, with the .venv activated):
    python scripts\16_hvd_annex_coverage.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
ITEMS_FILE = ROOT / "criteria" / "hvd_annex_items.csv"
JUDGEMENT_FILE = ROOT / "criteria" / "hvd_annex_coverage.csv"
METADATA_CHECKS = ROOT / "scripts" / "04_metadata_checks.py"
PORTAL = "https://data.gov.gr"

SEARCHED_TYPES = ("dataset", "data-service")
KIND_NAMES = {"dataset": "dataset", "data-service": "data service"}
IN_TITLE, IN_DESCRIPTION = "title", "description or tags"
PRESENT, PARTLY, MISSING, NOT_APPLICABLE = "present", "partly", "missing", "not applicable"
ANSWERS = (PRESENT, PARTLY, MISSING, NOT_APPLICABLE)
CATEGORIES = ("Geospatial", "Earth observation and environment", "Meteorological", "Statistics", "Companies",
              "Mobility")
CANDIDATES_PER_ITEM = 25
LISTED_IN_SUMMARY = 3
ANSWER_FILLS = {PRESENT: "E2EFDA", PARTLY: "FFF2CC", MISSING: "F8CBAD", NOT_APPLICABLE: "EDEDED"}
HEADER_FILL = "DDEBF7"


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_table(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"File not found: {relative(path)}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_metadata_checks():
    """The script of the metadata checks as a module, for its reading of the high-value categories."""
    spec = importlib.util.spec_from_file_location("metadata_checks", METADATA_CHECKS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalise(text: str) -> str:
    """Lower case without accents, with the final sigma written as a sigma, so that one pattern finds every form."""
    decomposed = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("ς", "σ")


def load_items(path: Path) -> list[dict]:
    """The datasets that the Annex names, with their compiled patterns; the run stops on a row that cannot be used."""
    items, seen = [], set()
    for number, row in enumerate(read_table(path), start=2):
        place = f"{relative(path)}, line {number}"
        if row["item_id"] in seen:
            raise SystemExit(f"{place}: second row for {row['item_id']}")
        if row["category"] not in CATEGORIES:
            raise SystemExit(f"{place}: category '{row['category']}' is not one of {', '.join(CATEGORIES)}")
        try:
            pattern = re.compile(row["patterns"])
        except re.error as error:
            raise SystemExit(f"{place}: the pattern cannot be read ({error})") from None
        seen.add(row["item_id"])
        items.append(dict(row, pattern=pattern))
    return items


def texts_of(value) -> list[str]:
    if isinstance(value, dict):
        return [str(text) for text in value.values() if text]
    if isinstance(value, list):
        return [str(text) for text in value if text]
    return [str(value)] if value else []


def tag_names(record: dict) -> list[str]:
    names = []
    for tag in record.get("tags") or []:
        names.append(str(tag.get("display_name") or tag.get("name") or "") if isinstance(tag, dict) else str(tag))
    return [name for name in names if name]


def address_of(record: dict) -> str:
    if record.get("type") == "data-service":
        for field in ("landing_page", "endpoint_url"):
            values = texts_of(record.get(field))
            if values:
                return values[0]
        return ""
    return f"{PORTAL}/dataset/{record.get('name', '')}"


def views_of(record: dict) -> int:
    summary = record.get("tracking_summary")
    return int(summary.get("total") or 0) if isinstance(summary, dict) else 0


def catalogue_records(snapshot: Path, categories_of) -> list[dict]:
    """The datasets and data services of the snapshot, with the texts that are searched."""
    records = []
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            kind = record.get("type") or "dataset"
            if kind not in SEARCHED_TYPES:
                continue
            organisation = record.get("organization") or {}
            titles = texts_of(record.get("title")) + texts_of(record.get("title_translated"))
            body = texts_of(record.get("notes")) + texts_of(record.get("notes_translated")) + tag_names(record)
            records.append({
                "kind": KIND_NAMES[kind], "name": record.get("name", ""), "title": record.get("title") or "",
                "organisation": organisation.get("title", "") if isinstance(organisation, dict) else "",
                "address": address_of(record), "hvd_categories": categories_of(record), "views": views_of(record),
                "title_text": normalise(" ".join(titles)), "body_text": normalise(" ".join(body)),
            })
    return records


def match_place(pattern: re.Pattern, record: dict) -> str:
    if pattern.search(record["title_text"]):
        return IN_TITLE
    if pattern.search(record["body_text"]):
        return IN_DESCRIPTION
    return ""


def search(items: list[dict], records: list[dict]) -> dict[str, list[tuple[dict, str]]]:
    """For each item, the matching records with the place of the match, in the order of the candidates."""
    found = {}
    for item in items:
        hits = [(record, place) for record in records if (place := match_place(item["pattern"], record))]
        hits.sort(key=lambda hit: (hit[1] != IN_TITLE, -hit[0]["views"], hit[0]["name"]))
        found[item["item_id"]] = hits
    return found


def load_judgement(path: Path, items: list[dict], names: set[str]) -> dict[str, dict]:
    """The judgement of the reviewer for each item, if recorded; the run stops on a row that cannot be used."""
    if not path.exists():
        return {}
    known = {item["item_id"] for item in items}
    judgement = {}
    for number, row in enumerate(read_table(path), start=2):
        place = f"{relative(path)}, line {number}"
        if row["item_id"] not in known:
            raise SystemExit(f"{place}: unknown item {row['item_id']}")
        if row["item_id"] in judgement:
            raise SystemExit(f"{place}: second row for {row['item_id']}")
        if row["answer"] not in ANSWERS:
            raise SystemExit(f"{place}: answer '{row['answer']}' is not one of {', '.join(ANSWERS)}")
        listed = row["datasets"].split()
        unknown = [name for name in listed if name not in names]
        if unknown:
            raise SystemExit(f"{place}: not in the snapshot: {', '.join(unknown)}")
        if row["answer"] in (PRESENT, PARTLY) and not listed:
            raise SystemExit(f"{place}: an item that is present or partly present needs at least one dataset")
        judgement[row["item_id"]] = row
    missing = sorted(known - set(judgement))
    if missing:
        raise SystemExit(f"{relative(path)} has no row for {', '.join(missing)}")
    return judgement


def candidate_rows(items: list[dict], found: dict) -> list[dict]:
    rows = []
    for item in items:
        for rank, (record, place) in enumerate(found[item["item_id"]][:CANDIDATES_PER_ITEM], start=1):
            rows.append({"item_id": item["item_id"], "rank": rank, "kind": record["kind"], "name": record["name"],
                         "title": record["title"], "organisation": record["organisation"], "address": record["address"],
                         "matched_in": place, "hvd_categories": record["hvd_categories"], "views": record["views"]})
    return rows


def coverage_rows(items: list[dict], found: dict, judgement: dict, records_by_name: dict) -> list[dict]:
    rows = []
    for item in items:
        hits = found[item["item_id"]]
        judged = judgement.get(item["item_id"], {})
        named = judged.get("datasets", "").split()
        rows.append({
            "item_id": item["item_id"], "annex_point": item["annex_point"], "category": item["category"],
            "item": item["item"], "item_el": item["item_el"], "legal_basis": item["legal_basis"],
            "matches_in_title": sum(place == IN_TITLE for _, place in hits),
            "matches_in_description": sum(place == IN_DESCRIPTION for _, place in hits),
            "organisations": len({record["organisation"] for record, _ in hits}),
            "answer": judged.get("answer", ""), "datasets": " ".join(named),
            "addresses": " ".join(records_by_name[name]["address"] for name in named),
            "reason": judged.get("reason", ""),
            "first_candidates": " ".join(record["name"] for record, _ in hits[:LISTED_IN_SUMMARY]),
        })
    return rows


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def build_summary(date: str, rows: list[dict], records: list[dict], records_by_name: dict) -> str:
    kinds = Counter(record["kind"] for record in records)
    judged = all(row["answer"] for row in rows)
    lines = [
        f"# Datasets of the Annex of Regulation (EU) 2023/138 on the portal, snapshot of {date}", "",
        f"{len(rows)} datasets named by the Annex (`criteria/hvd_annex_items.csv`), searched in the title, the description "
        f"and the tags of the {kinds['dataset']:,} datasets and {kinds['data service']:,} data services of the snapshot. "
        "A match is a candidate; whether a dataset of the Annex is on the portal is judged by the reviewer. Present: the "
        "whole country, by one dataset or by several together, at the detail that the Annex asks; partly: some areas "
        "only, aggregates only, or part of the data; missing: nothing on the portal. A dataset that is missing from the "
        "portal may be published elsewhere, for example on the site of its producer.", "",
    ]
    if judged:
        lines += ["## Answers by category", "", "| Category | Datasets of the Annex | Present | Partly | Missing | "
                  "Not applicable |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for category in CATEGORIES:
            mine = [row for row in rows if row["category"] == category]
            if not mine:
                continue
            count = Counter(row["answer"] for row in mine)
            lines.append(f"| {category} | {len(mine)} | {count[PRESENT]} | {count[PARTLY]} | {count[MISSING]} | "
                         f"{count[NOT_APPLICABLE]} |")
        total = Counter(row["answer"] for row in rows)
        lines += [f"| all | {len(rows)} | {total[PRESENT]} | {total[PARTLY]} | {total[MISSING]} | {total[NOT_APPLICABLE]} |",
                  "", "Missing from the portal: " + (", ".join(f"{row['item_id']} {row['item']}" for row in rows
                                                            if row["answer"] == MISSING) or "none") + ".", ""]
    else:
        lines += ["The judgement of the reviewer is not recorded yet (`criteria/hvd_annex_coverage.csv`).", ""]
    lines += ["## The datasets of the Annex", "",
              "| Item | Dataset of the Annex | Answer | On the portal | Matches in the title | Matches elsewhere | Reason |",
              "| --- | --- | --- | --- | ---: | ---: | --- |"]
    for row in rows:
        named = row["datasets"].split() if judged else row["first_candidates"].split()
        links = ", ".join(f"[{md_cell(records_by_name[name]['title'])}]({records_by_name[name]['address']})"
                          for name in named) or "-"
        lines.append(f"| {row['item_id']} | {md_cell(row['item'])} | {row['answer'] or '-'} | {links} | "
                     f"{row['matches_in_title']:,} | {row['matches_in_description']:,} | {md_cell(row['reason']) or '-'} |")
    if not judged:
        lines += ["", "Before the judgement, the column On the portal lists the first candidates of each item."]
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_workbook(path: Path, date: str, rows: list[dict], candidates: list[dict]) -> None:
    font, bold = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
    link_font = Font(name="Arial", size=10, color="0563C1", underline="single")
    wrap = Alignment(wrap_text=True, vertical="top")
    centre = Alignment(horizontal="center", vertical="top", wrap_text=True)

    def sheet_of(workbook: Workbook, title: str, columns: list[tuple[str, str, int]], table: list[dict],
                 first: bool = False):
        sheet = workbook.active if first else workbook.create_sheet()
        sheet.title = title
        for index, (_, heading, width) in enumerate(columns, start=1):
            cell = sheet.cell(row=1, column=index, value=heading)
            cell.font, cell.alignment = bold, centre
            cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
            sheet.column_dimensions[get_column_letter(index)].width = width
        for number, row in enumerate(table, start=2):
            for index, (key, _, width) in enumerate(columns, start=1):
                value = row[key]
                cell = sheet.cell(row=number, column=index, value=value)
                is_link = key == "address" and bool(value)
                cell.font = link_font if is_link else font
                cell.alignment = centre if width <= 12 else wrap
                if is_link:
                    cell.hyperlink = value
                if key == "answer" and value in ANSWER_FILLS:
                    cell.fill = PatternFill("solid", fgColor=ANSWER_FILLS[value])
        sheet.freeze_panes = "B2"
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(table) + 1}"

    workbook = Workbook()
    sheet_of(workbook, "Datasets of the Annex", [
        ("item_id", "Item", 9), ("annex_point", "Point", 7), ("category", "Category", 20), ("item", "Dataset of the Annex", 34),
        ("item_el", "In Greek", 34), ("answer", "Answer", 11), ("datasets", "On the portal", 40),
        ("reason", "Reason", 60), ("matches_in_title", "Matches in the title", 10),
        ("matches_in_description", "Matches elsewhere", 10), ("organisations", "Organisations", 11),
        ("legal_basis", "Legal basis", 50)], rows, first=True)
    sheet_of(workbook, "Candidates", [
        ("item_id", "Item", 9), ("rank", "Rank", 6), ("kind", "Kind", 11), ("title", "Title", 50),
        ("organisation", "Organisation", 32), ("address", "Address", 40), ("matched_in", "Matched in", 12),
        ("hvd_categories", "Declared high-value category", 22), ("views", "Views", 8), ("name", "Name", 34)], candidates)
    sheet = workbook.create_sheet("Notes")
    sheet.column_dimensions["A"].width = 140
    notes = [
        f"Datasets of the Annex of Implementing Regulation (EU) 2023/138 on the portal, snapshot of {date}.",
        "The datasets that the Annex names are listed with their search patterns in criteria/hvd_annex_items.csv; the "
        "patterns are applied to the title, the description and the tags, in lower case and without accents.",
        "A match is a candidate, not a finding. Answers of the reviewer: present, the whole country by one dataset or by "
        "several together at the detail that the Annex asks; partly, some areas only, aggregates only or part of the data; "
        "missing; not applicable.",
        "A data service of the portal counts as a dataset. A dataset that is missing from the portal may be published "
        "elsewhere. The judgement is recorded in criteria/hvd_annex_coverage.csv and in DECISIONS.md #61.",
    ]
    for index, note in enumerate(notes, start=1):
        cell = sheet.cell(row=index, column=1, value=note)
        cell.font, cell.alignment = (bold if index == 1 else font), wrap
    workbook.save(path)


def newest_snapshot() -> Path:
    files = sorted(RAW_DIR.glob("catalog_????-??-??.jsonl.gz"))
    if not files:
        raise SystemExit("No catalogue snapshot in data/raw.")
    return files[-1]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Datasets of the Annex of Regulation (EU) 2023/138 on the portal.")
    parser.add_argument("--snapshot", type=Path, default=None, help="catalogue snapshot (default: the newest in data/raw)")
    args = parser.parse_args()

    snapshot = args.snapshot or newest_snapshot()
    found_date = re.search(r"(\d{4}-\d{2}-\d{2})", snapshot.name)
    if not found_date:
        raise SystemExit(f"No date in the name of {relative(snapshot)}")
    date = found_date.group(1)
    checks = load_metadata_checks()
    items = load_items(ITEMS_FILE)
    records = catalogue_records(snapshot, lambda record: checks.check_m9(record)["m9_categories"])
    records_by_name = {record["name"]: record for record in records}
    judgement = load_judgement(JUDGEMENT_FILE, items, set(records_by_name))
    found = search(items, records)

    candidates = candidate_rows(items, found)
    rows = coverage_rows(items, found, judgement, records_by_name)
    out_dir = OUT_DIR / f"hvd_annex_coverage_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates_file = PROCESSED_DIR / f"hvd_annex_candidates_{date}.csv"
    coverage_file = PROCESSED_DIR / f"hvd_annex_coverage_{date}.csv"
    write_csv(candidates_file, candidates)
    write_csv(coverage_file, rows)
    (out_dir / "summary.md").write_text(build_summary(date, rows, records, records_by_name), encoding="utf-8",
                                        newline="\n")
    write_workbook(out_dir / "hvd_annex_coverage.xlsx", date, rows, candidates)

    kinds = Counter(record["kind"] for record in records)
    print(f"Snapshot: {relative(snapshot)}")
    print(f"Searched: {kinds['dataset']:,} datasets and {kinds['data service']:,} data services; datasets of the Annex: "
          f"{len(items)}")
    print("Datasets of the Annex without any match: " + (", ".join(row["item_id"] for row in rows
                                                                 if not row["matches_in_title"]
                                                                 and not row["matches_in_description"]) or "none"))
    if judgement:
        answers = Counter(row["answer"] for row in rows)
        print("Answers of the reviewer: " + ", ".join(f"{answer} {answers[answer]}" for answer in ANSWERS))
    else:
        print("Answers of the reviewer: not recorded yet")
    print("Files:")
    for path in (candidates_file, coverage_file, out_dir / "summary.md", out_dir / "hvd_annex_coverage.xlsx"):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
