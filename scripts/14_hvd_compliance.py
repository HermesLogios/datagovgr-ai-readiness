r"""
14_hvd_compliance.py
Phase 3, step 5: compliance of the high-value datasets with Commission Implementing Regulation (EU) 2023/138,
reported separately from the scores (DECISIONS.md #28 and #58).

What it does, in order:
  1. Reads the sample (data/processed/sample.csv), the assessment of 13_assessment.py
     (data/processed/assessment_YYYY-MM-DD.csv, the newest one), the tables of 04_metadata_checks.py,
     07_api_checks.py and 08_documentation_checks.py of the same date and the judgement of the reviewer on the marking
     of the datasets (criteria/hvd_marking.csv).
  2. Answers, for each of the 24 datasets of the high-value group of the sample, the requirements of the Regulation
     with yes, partly, no or not applicable:
       - free of charge (Directive (EU) 2019/1024, Article 14(1)): criterion M5;
       - open licence, CC BY 4.0 or an equivalent or less restrictive one (Regulation, Article 4(3)): criterion M4;
       - API and bulk download (Article 3(1) and the Annex): the test of criterion M10;
       - terms of use and documentation of the API (Article 3(2) and 3(3)): the test of criterion M10;
       - point of contact (Article 3(4)): the contact point of the metadata, criterion M2;
       - marking as a high-value dataset (Article 3(5)): criterion M9;
       - documentation of the structure, in the categories where the Annex asks for it (all but the geospatial
         one): criterion AI2. The category is the one of the content, where the reviewer recorded it.
  3. Adds the judgement of the reviewer on the marking: whether the content of the dataset corresponds to a dataset
     of the Annex (yes, no or doubtful), the point of the Annex and whether the declared category is the right one.
  4. Counts the answers over the datasets whose content is in the Annex. The obligations of the Regulation do not
     apply to the other datasets, which stay in the table outside the counts.
  5. Lists, for every dataset of the catalogue that is marked as high-value, the requirements that the metadata
     allow to check: open licence, point of contact and completeness of the marking. Whether a marking is correct
     cannot be judged automatically.
  6. Writes:
       - data/processed/hvd_compliance_YYYY-MM-DD.csv, one row per high-value dataset of the sample;
       - data/processed/hvd_compliance_catalogue_YYYY-MM-DD.csv, one row per marked dataset of the catalogue;
       - outputs/hvd_compliance_YYYY-MM-DD/summary.md and hvd_compliance.xlsx.

Rules:
  - An answer is taken from a score or a test that is already recorded; none is judged here.
  - A dataset of the high-value group without a row in criteria/hvd_marking.csv stops the run.
  - No request is sent to the portal or to any other site.

Usage (from the project root, with the .venv activated):
    python scripts\14_hvd_compliance.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
MARKING_FILE = ROOT / "criteria" / "hvd_marking.csv"

REGULATION = ("Commission Implementing Regulation (EU) 2023/138 of 21 December 2022 laying down a list of specific "
              "high-value datasets and the arrangements for their publication and re-use (OJ L 19, 20.1.2023, p. 43)")
YES, PARTLY, NO, NOT_APPLICABLE, NOT_ASKED = "yes", "partly", "no", "not applicable", "not asked by the Annex"
ANSWERS = (YES, PARTLY, NO, NOT_APPLICABLE, NOT_ASKED)
SCORE_ANSWER = {"2": YES, "1": PARTLY, "0": NO, "n/a": NOT_APPLICABLE}
IN_ANNEX = ("yes", "no", "doubtful")
MARKINGS = ("correct", "correct with one more category", "other category", "not marked")
# Requirements of the table: column, title, legal basis and where the answer comes from.
REQUIREMENTS = [
    ("free_of_charge", "Free of charge", "Directive (EU) 2019/1024, Article 14(1)", "criterion M5"),
    ("open_licence", "Open licence: CC BY 4.0, equivalent or less restrictive", "Regulation, Article 4(3)", "criterion M4"),
    ("api", "API", "Regulation, Article 3(1)", "test of criterion M10"),
    ("bulk_download", "Bulk download", "Regulation, Article 3(1) and the Annex", "test of criterion M10"),
    ("api_terms_and_documentation", "Terms of use and documentation of the API", "Regulation, Article 3(2) and 3(3)",
     "test of criterion M10"),
    ("point_of_contact", "Point of contact", "Regulation, Article 3(4)", "contact point of the metadata, criterion M2"),
    ("marked_as_high_value", "Marked as a high-value dataset", "Regulation, Article 3(5)", "criterion M9"),
    ("documentation_of_structure", "Documentation of the structure",
     "Regulation, Annex, points 2.2(c), 3.2(c), 4.2(c), 5.2(b) and 6.2(c)", "criterion AI2"),
]
ANSWER_FILLS = {YES: "E2EFDA", PARTLY: "FFF2CC", NO: "F8CBAD", NOT_APPLICABLE: "EDEDED", NOT_ASKED: "EDEDED",
                "doubtful": "FFF2CC"}
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


def newest_assessment() -> Path:
    files = sorted(PROCESSED_DIR.glob("assessment_????-??-??.csv"))
    if not files:
        raise SystemExit("No assessment in data/processed. Run 13_assessment.py first.")
    return files[-1]


def answer_of_score(score: str) -> str:
    """The answer that the score of a criterion gives: yes for 2, partly for 1, no for 0."""
    key = score if score == "n/a" else str(int(float(score))) if score != "" else ""
    if key not in SCORE_ANSWER:
        raise SystemExit(f"A score is needed for the table of compliance and '{score}' was found")
    return SCORE_ANSWER[key]


def load_marking(path: Path) -> dict[str, dict]:
    """The judgement of the reviewer on the marking of each dataset; the run stops on a row that cannot be used."""
    marking = {}
    for number, row in enumerate(read_table(path), start=2):
        place = f"{relative(path)}, line {number}"
        if row["in_annex"] not in IN_ANNEX:
            raise SystemExit(f"{place}: in_annex '{row['in_annex']}' is not one of {', '.join(IN_ANNEX)}")
        if row["in_annex"] == "yes" and row["marking"] not in MARKINGS:
            raise SystemExit(f"{place}: marking '{row['marking']}' is not one of {', '.join(MARKINGS)}")
        if row["in_annex"] != "yes" and row["marking"]:
            raise SystemExit(f"{place}: the category of a dataset is judged only when its content is in the Annex")
        if row["sample_id"] in marking:
            raise SystemExit(f"{place}: second row for {row['sample_id']}")
        marking[row["sample_id"]] = row
    return marking


def api_evidence(tested: dict) -> str:
    kinds = tested["api_kinds"]
    if tested["api_works"] == "yes":
        return f"{kinds}: works, " + ("serves the complete dataset" if tested["api_complete"] == "yes"
                                      else "does not serve the complete dataset")
    return f"{kinds}: does not work" if kinds else "no API"


def sample_rows(sample: list[dict], assessment: dict, metadata: dict, api: dict, documentation: dict,
                marking: dict) -> list[dict]:
    """One row per dataset of the high-value group of the sample: the judgement on its marking and the answers."""
    rows = []
    for dataset in sample:
        if dataset["group"] != "high-value":
            continue
        sample_id = dataset["sample_id"]
        if sample_id not in marking:
            raise SystemExit(f"{relative(MARKING_FILE)} has no row for {sample_id}")
        scores, checks, tested, judged = assessment[sample_id], metadata[sample_id], api[sample_id], marking[sample_id]
        marked = answer_of_score(scores["M9"])
        if (judged["marking"] == "not marked") != (marked == NO) and judged["in_annex"] == "yes":
            raise SystemExit(f"{sample_id}: the judgement '{judged['marking']}' does not agree with the M9 score "
                             f"{scores['M9']}")
        terms = tested["hvd_api_terms_and_documentation"]
        category = judged["category_by_content"]
        asked = (category != "Geospatial" if category
                 else documentation[sample_id]["hvd_documentation_required"] == "yes")
        row = {
            "sample_id": sample_id, "title": dataset["title"], "organisation": dataset["organization_title"],
            "address": dataset["url"], "declared_categories": checks["m9_categories"],
            "in_annex": judged["in_annex"], "annex_point": judged["annex_point"],
            "category_by_content": judged["category_by_content"], "marking": judged["marking"],
            "free_of_charge": answer_of_score(scores["M5"]),
            "open_licence": answer_of_score(scores["M4"]),
            "api": tested["hvd_api"],
            "bulk_download": tested["hvd_bulk_download"],
            "api_terms_and_documentation": NOT_APPLICABLE if terms == "-" else terms,
            "point_of_contact": YES if checks["m2_contact"] == "True" else NO,
            "marked_as_high_value": marked,
            "documentation_of_structure": answer_of_score(scores["AI2"]) if asked else NOT_ASKED,
            "licence_evidence": checks["m4_licences"] or "no licence",
            "api_evidence": api_evidence(tested),
            "bulk_download_evidence": tested["bulk_evidence"],
            "marking_evidence": checks["m9_reason"],
            "judgement_reason": judged["reason"],
        }
        for column, _, _, _ in REQUIREMENTS:
            if row[column] not in ANSWERS:
                raise SystemExit(f"{sample_id}: unexpected answer '{row[column]}' in {column}")
        rows.append(row)
    return rows


def counts(rows: list[dict]) -> dict[str, Counter]:
    """The answers to each requirement, counted over the datasets whose content is in the Annex."""
    in_scope = [row for row in rows if row["in_annex"] == "yes"]
    return {column: Counter(row[column] for row in in_scope) for column, _, _, _ in REQUIREMENTS}


def catalogue_rows(metadata_all: list[dict]) -> list[dict]:
    """One row per dataset of the catalogue marked as high-value, with what its metadata allow to check."""
    rows = []
    for record in metadata_all:
        if record["m9_marked"] != "True":
            continue
        rows.append({
            "name": record["name"], "title": record["title"], "organisation": record["organization_title"],
            "sample_id": record["sample_id"], "declared_categories": record["m9_categories"],
            "marking": "complete" if answer_of_score(record["m9_score"]) == YES else "partial",
            "marking_evidence": record["m9_reason"],
            "open_licence": answer_of_score(record["m4_score"]), "licences": record["m4_licences"] or "no licence",
            "point_of_contact": YES if record["m2_contact"] == "True" else NO,
        })
    return rows


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def share(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else ""


def build_summary(rows: list[dict], catalogue: list[dict], date: str) -> str:
    tally = counts(rows)
    in_scope = [row for row in rows if row["in_annex"] == "yes"]
    lines = [
        f"# Compliance of the high-value datasets with Implementing Regulation (EU) 2023/138, snapshot of {date}", "",
        f"Source of the requirements: {REGULATION}, Articles 3 and 4 and the Annex; free of charge follows Article 14(1) of "
        "Directive (EU) 2019/1024. The table is reported separately from the scores of the assessment (DECISIONS.md #28). "
        "Every answer comes from a score or a test that is already recorded; the reading of the Annex and the judgement "
        "on the marking of each dataset are recorded in DECISIONS.md #58 and in `criteria/hvd_marking.csv`.",
        "", "## Marking of the high-value group of the sample", "",
        f"The group holds {len(rows)} datasets: those that their publishers mark as high-value and those counted as "
        "high-value by their content. The obligations of the Regulation apply to a dataset when its content corresponds to "
        "a dataset of the Annex.", "",
        "| Content in the Annex | Datasets | Datasets of the group |", "| --- | ---: | --- |",
    ]
    for value, label in (("yes", "yes"), ("no", "no: marked by the publisher, not listed in the Annex"),
                         ("doubtful", "doubtful: the text of the Annex gives no clear answer")):
        members = [row["sample_id"] for row in rows if row["in_annex"] == value]
        lines.append(f"| {label} | {len(members)} | {', '.join(members)} |")
    lines += ["", "Declared category of the datasets whose content is in the Annex:", "",
              "| Marking | Datasets | Datasets of the group |", "| --- | ---: | --- |"]
    for value in MARKINGS:
        members = [row["sample_id"] for row in in_scope if row["marking"] == value]
        lines.append(f"| {value} | {len(members)} | {', '.join(members)} |")

    lines += ["", f"## Compliance of the {len(in_scope)} datasets whose content is in the Annex", "",
              "| Requirement | Legal basis | Answer taken from | Yes | Partly | No | Not applicable or not asked |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for column, title, basis, origin in REQUIREMENTS:
        found = tally[column]
        lines.append(f"| {title} | {basis} | {origin} | {found[YES]} | {found[PARTLY]} | {found[NO]} | "
                     f"{found[NOT_APPLICABLE] + found[NOT_ASKED]} |")

    lines += ["", "## The table", "",
              "The datasets outside the Annex and the doubtful ones are listed with their answers and are not counted above.",
              "", "| Dataset | Title | In the Annex | Declared category | Marking | Free | Licence | API | Bulk download | "
              "API terms and documentation | Contact | Marked | Documentation of the structure |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        answers = " | ".join(row[column] for column, _, _, _ in REQUIREMENTS)
        lines.append(f"| {row['sample_id']} | [{md_cell(row['title'])}]({row['address']}) | {row['in_annex']} | "
                     f"{row['declared_categories'] or '-'} | {row['marking'] or '-'} | {answers} |")

    by_category: dict[str, list[dict]] = {}
    for record in catalogue:
        for category in [part.strip() for part in record["declared_categories"].split(";") if part.strip()] or ["(none)"]:
            by_category.setdefault(category, []).append(record)
    lines += ["", f"## Datasets of the catalogue marked as high-value ({len(catalogue):,})", "",
              "What the metadata allow to check for every marked dataset. A dataset that declares two categories is counted "
              "in both. Whether the content of a marked dataset is in the Annex cannot be judged automatically: in the "
              f"sample it holds for {sum(row['in_annex'] == 'yes' and row['marked_as_high_value'] != NO for row in rows)} of "
              f"the {sum(row['marked_as_high_value'] != NO for row in rows)} marked datasets.", "",
              "| Declared category | Datasets | Open licence | Point of contact | Complete marking |",
              "| --- | ---: | ---: | ---: | ---: |"]

    def catalogue_line(label: str, members: list[dict]) -> str:
        licence = sum(record["open_licence"] == YES for record in members)
        contact = sum(record["point_of_contact"] == YES for record in members)
        complete = sum(record["marking"] == "complete" for record in members)
        return (f"| {label} | {len(members):,} | {licence:,} ({share(licence, len(members))}) | "
                f"{contact:,} ({share(contact, len(members))}) | {complete:,} ({share(complete, len(members))}) |")

    for category, members in sorted(by_category.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(catalogue_line(category, members))
    lines.append(catalogue_line("all marked datasets", catalogue))
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_workbook(path: Path, rows: list[dict], catalogue: list[dict], date: str) -> None:
    font, bold = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
    link_font = Font(name="Arial", size=10, color="0563C1", underline="single")
    wrap = Alignment(wrap_text=True, vertical="top")
    centre = Alignment(horizontal="center", vertical="top", wrap_text=True)

    def header(sheet, titles: list[str], widths: list[int]) -> None:
        for index, (title, width) in enumerate(zip(titles, widths), start=1):
            cell = sheet.cell(row=1, column=index, value=title)
            cell.font, cell.alignment = bold, centre
            cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
            sheet.column_dimensions[get_column_letter(index)].width = width

    def put(sheet, row: int, column: int, value, centred: bool = False, fill: str | None = None, address: str = ""):
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font, cell.alignment = (link_font if address else font), (centre if centred else wrap)
        if address:
            cell.hyperlink = address
        if fill:
            cell.fill = PatternFill("solid", fgColor=fill)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Compliance"
    requirement_titles = [title for _, title, _, _ in REQUIREMENTS]
    header(sheet, ["Dataset", "Title", "Organisation", "Address", "Declared category", "Content in the Annex",
                   "Point of the Annex", "Category by content", "Marking"] + requirement_titles
           + ["Licences", "API", "Bulk download", "Marking in the metadata", "Reason of the judgement"],
           [9, 40, 28, 32, 22, 12, 30, 22, 16] + [14] * len(REQUIREMENTS) + [16, 34, 34, 34, 60])
    for index, row in enumerate(rows, start=2):
        values = [row["sample_id"], row["title"], row["organisation"], row["address"], row["declared_categories"],
                  row["in_annex"], row["annex_point"], row["category_by_content"], row["marking"]]
        values += [row[column] for column, _, _, _ in REQUIREMENTS]
        values += [row["licence_evidence"], row["api_evidence"], row["bulk_download_evidence"], row["marking_evidence"],
                   row["judgement_reason"]]
        for column, value in enumerate(values, start=1):
            answer = column == 6 or 10 <= column < 10 + len(REQUIREMENTS)
            put(sheet, index, column, value, centred=column == 1 or answer,
                fill=ANSWER_FILLS.get(value) if answer else None, address=value if column == 4 else "")
    sheet.freeze_panes = "B2"

    sheet = workbook.create_sheet("Counts")
    tally = counts(rows)
    header(sheet, ["Requirement", "Legal basis", "Answer taken from", "Yes", "Partly", "No",
                   "Not applicable or not asked"], [44, 50, 40, 8, 8, 8, 16])
    for index, (column, title, basis, origin) in enumerate(REQUIREMENTS, start=2):
        found = tally[column]
        values = [title, basis, origin, found[YES], found[PARTLY], found[NO], found[NOT_APPLICABLE] + found[NOT_ASKED]]
        for position, value in enumerate(values, start=1):
            put(sheet, index, position, value, centred=position > 3)

    sheet = workbook.create_sheet("Catalogue")
    columns = ["name", "title", "organisation", "sample_id", "declared_categories", "marking", "marking_evidence",
               "open_licence", "licences", "point_of_contact"]
    header(sheet, ["Dataset", "Title", "Organisation", "In the sample", "Declared category", "Marking",
                   "Marking in the metadata", "Open licence", "Licences", "Point of contact"],
           [34, 44, 30, 10, 26, 10, 40, 12, 18, 12])
    for index, record in enumerate(catalogue, start=2):
        for position, name in enumerate(columns, start=1):
            answer = name in ("open_licence", "point_of_contact")
            put(sheet, index, position, record[name], centred=answer or name in ("sample_id", "marking"),
                fill=ANSWER_FILLS.get(record[name]) if answer else None)
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(catalogue) + 1}"

    sheet = workbook.create_sheet("Notes")
    sheet.column_dimensions["A"].width = 140
    notes = [
        f"Compliance of the high-value datasets with Implementing Regulation (EU) 2023/138, snapshot of {date}.",
        f"Source of the requirements: {REGULATION}.",
        "Sheet Compliance: the 24 datasets of the high-value group of the sample. Sheet Counts: the answers over the "
        "datasets whose content is in the Annex. Sheet Catalogue: every dataset of the catalogue marked as high-value, "
        "with what its metadata allow to check.",
        "Content in the Annex: yes, the content corresponds to a dataset of the Annex; no, the dataset is marked by its "
        "publisher and is not listed in the Annex; doubtful, the text of the Annex gives no clear answer.",
        "Marking: correct, the declared category is the one of the content; correct with one more category, a second "
        "declared category does not correspond; other category, the content belongs to another category than the declared "
        "one; not marked, the dataset carries no marking.",
        "Partly, in the column of the API: the API works and does not serve the complete dataset. Partly, in the "
        "documentation of the structure: the names of the fields can be understood and not every field is explained.",
        "The reading of the Annex and the judgement on each dataset are recorded in DECISIONS.md #58.",
    ]
    for index, note in enumerate(notes, start=1):
        cell = sheet.cell(row=index, column=1, value=note)
        cell.font, cell.alignment = (bold if index == 1 else font), wrap
    workbook.save(path)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Compliance of the high-value datasets with Implementing Regulation "
                                                 "(EU) 2023/138, reported separately from the scores.")
    parser.add_argument("--assessment", type=Path, default=None,
                        help="table of the assessment (default: the newest in data/processed)")
    args = parser.parse_args()

    assessment_file = args.assessment or newest_assessment()
    found = re.search(r"(\d{4}-\d{2}-\d{2})", assessment_file.name)
    if not found:
        raise SystemExit(f"No date in the name of {relative(assessment_file)}")
    date = found.group(1)
    sample = sorted(read_table(SAMPLE_FILE), key=lambda row: row["sample_id"])
    assessment = {row["sample_id"]: row for row in read_table(assessment_file)}
    metadata_all = read_table(PROCESSED_DIR / f"metadata_checks_{date}.csv")
    metadata = {row["sample_id"]: row for row in metadata_all if row["sample_id"]}
    api = {row["sample_id"]: row for row in read_table(PROCESSED_DIR / f"api_checks_{date}.csv")}
    documentation = {row["sample_id"]: row for row in read_table(PROCESSED_DIR / f"documentation_checks_{date}.csv")}
    marking = load_marking(MARKING_FILE)

    rows = sample_rows(sample, assessment, metadata, api, documentation, marking)
    catalogue = catalogue_rows(metadata_all)

    out_dir = OUT_DIR / f"hvd_compliance_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_file = PROCESSED_DIR / f"hvd_compliance_{date}.csv"
    catalogue_file = PROCESSED_DIR / f"hvd_compliance_catalogue_{date}.csv"
    write_csv(sample_file, rows)
    write_csv(catalogue_file, catalogue)
    (out_dir / "summary.md").write_text(build_summary(rows, catalogue, date), encoding="utf-8", newline="\n")
    write_workbook(out_dir / "hvd_compliance.xlsx", rows, catalogue, date)

    in_annex = Counter(row["in_annex"] for row in rows)
    print(f"Assessment: {relative(assessment_file)}")
    print(f"High-value datasets of the sample: {len(rows)}; content in the Annex: yes {in_annex['yes']}, "
          f"no {in_annex['no']}, doubtful {in_annex['doubtful']}")
    print(f"Answers over the {in_annex['yes']} datasets whose content is in the Annex:")
    for column, title, _, _ in REQUIREMENTS:
        found_answers = counts(rows)[column]
        print(f"  {title}: " + ", ".join(f"{answer} {found_answers[answer]}" for answer in ANSWERS if found_answers[answer]))
    print(f"Datasets of the catalogue marked as high-value: {len(catalogue):,}")
    print("Files:")
    for path in (sample_file, catalogue_file, out_dir / "summary.md", out_dir / "hvd_compliance.xlsx"):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
