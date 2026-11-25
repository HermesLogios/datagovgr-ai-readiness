r"""
15_gap_analysis.py
Phase 3, step 6: analysis of the gaps, from the scores, the effort of the fix and the answers on compliance that are
already recorded (DECISIONS.md #60).

What it does, in order:
  1. Reads the criteria (criteria/criteria.csv), the tables of 13_assessment.py (data/processed/assessment_YYYY-MM-DD.csv,
     the newest, and assessment_scores_YYYY-MM-DD.csv), the table of 04_metadata_checks.py and the two tables of
     14_hvd_compliance.py of the same date.
  2. Gaps by criterion in the sample: for each of the 23 criteria, the scores 2, 1 and 0 of the 36 datasets, the scores
     below 2, their share of the datasets to which the criterion applies and the effort of their fix. A score that the
     reviewer found not measurable (DECISIONS.md #63) is counted apart and left out of the share. A provisional
     criterion is listed and left out of the totals.
  3. Gaps by criterion in the catalogue: the same counts for the nine criteria that the metadata decide, over every
     dataset of the snapshot. A score that could not be determined is counted apart; M9 is counted over the datasets that
     carry a high-value marking, as in the report of 04_metadata_checks.py; Q5 is its metadata part (DECISIONS.md #36),
     since the dates inside the data are read in the sample only.
  4. What each dataset of the sample lacks for the ready group: its core criteria below 2 by effort, which decide its
     group, and its other scores below 2 by effort; the datasets one core criterion away from the ready group are named.
  5. Gaps of compliance of the high-value datasets: the requirements of Implementing Regulation (EU) 2023/138 answered
     no or partly for the datasets whose content is in the Annex, by dataset and by requirement, and the requirements that
     the metadata allow to check for every marked dataset of the catalogue.
  6. Writes:
       - data/processed/gap_criteria_YYYY-MM-DD.csv, one row per criterion (sample);
       - data/processed/gap_catalogue_YYYY-MM-DD.csv, one row per criterion decided by the metadata (catalogue);
       - data/processed/gap_datasets_YYYY-MM-DD.csv, one row per dataset of the sample;
       - data/processed/gap_hvd_YYYY-MM-DD.csv, one row per dataset whose content is in the Annex;
       - outputs/gap_analysis_YYYY-MM-DD/summary.md and gap_analysis.xlsx.

Rules:
  - Nothing is judged here: every score, effort and answer is read from the tables above.
  - A score below 2 without an effort of the fix, outside a provisional criterion, stops the run, and so does a group
    that the rule of the groups does not give.
  - No request is sent to the portal or to any other site.

Usage (from the project root, with the .venv activated):
    python scripts\15_gap_analysis.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
CRITERIA_FILE = ROOT / "criteria" / "criteria.csv"

EFFORTS = ("low", "medium", "high")
SCORES = ("2", "1", "0")
NOT_APPLICABLE, NOT_MEASURED, NOT_MEASURABLE = "n/a", "", "not measurable"
READY, ALMOST_READY, NOT_YET = "Ready", "Almost ready", "Not yet"
GROUPS = (READY, ALMOST_READY, NOT_YET)
CATALOGUE_CRITERIA = ("Q5", "Q6", "M1", "M2", "M3", "M4", "M6", "M7", "M9")
CATALOGUE_NOTES = {"Q5": "metadata part"}   # criteria that the catalogue measures in part only (DECISIONS.md #36)
MARKED_ONLY = "M9"
YES, PARTLY, NO = "yes", "partly", "no"
ANSWERS = (YES, PARTLY, NO, "not applicable", "not asked by the Annex")
# Requirements of the table of compliance of 14_hvd_compliance.py: column and title.
REQUIREMENTS = [
    ("free_of_charge", "Free of charge"),
    ("open_licence", "Open licence"),
    ("api", "API"),
    ("bulk_download", "Bulk download"),
    ("api_terms_and_documentation", "Terms of use and documentation of the API"),
    ("point_of_contact", "Point of contact"),
    ("marked_as_high_value", "Marked as a high-value dataset"),
    ("documentation_of_structure", "Documentation of the structure"),
]
# Requirements that the metadata allow to check for every marked dataset: column, title and the value of a gap.
CATALOGUE_REQUIREMENTS = [
    ("open_licence", "Open licence", NO),
    ("point_of_contact", "Point of contact", NO),
    ("marking", "Complete marking", "partial"),
]
GROUP_FILLS = {READY: "E2EFDA", ALMOST_READY: "FFF2CC", NOT_YET: "F8CBAD"}
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


def newest(prefix: str) -> Path:
    files = sorted(PROCESSED_DIR.glob(f"{prefix}_????-??-??.csv"))
    if not files:
        raise SystemExit(f"No {prefix} table in data/processed. Run 13_assessment.py first.")
    return files[-1]


def score_value(text: str) -> str:
    """A score as 2, 1 or 0, n/a for a criterion that does not apply, not measurable where the reviewer found nothing to
    measure, or an empty text where no score exists."""
    text = (text or "").strip()
    if text in (NOT_MEASURED, NOT_APPLICABLE, NOT_MEASURABLE):
        return text
    try:
        value = float(text)
    except ValueError:
        raise SystemExit(f"'{text}' is not a score") from None
    if value not in (0, 1, 2):
        raise SystemExit(f"'{text}' is not a score")
    return str(int(value))


def share(part: int, whole: int) -> float | None:
    """The share of part in whole as a percentage with one decimal, rounded half up; None when whole is 0."""
    if not whole:
        return None
    value = Decimal(100 * part) / Decimal(whole)
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def percent(value) -> str:
    return "" if value is None or value == "" else f"{value:.1f}%"


def criterion_gaps(criteria: list[dict], records: list[dict]) -> list[dict]:
    """One row per criterion: the scores of the sample, the scores below 2, their share and the effort of their fix."""
    rows = []
    for criterion in criteria:
        code = criterion["id"]
        mine = [record for record in records if record["criterion"] == code]
        if not mine:
            raise SystemExit(f"No score of {code} in the assessment")
        reasons = sorted({record["provisional"] for record in mine if record["provisional"]})
        scores = Counter(score_value(record["score"]) for record in mine)
        if scores[NOT_MEASURED] and not reasons:
            raise SystemExit(f"{code}: {scores[NOT_MEASURED]} datasets without a score")
        below = sorted((record for record in mine if score_value(record["score"]) in ("1", "0")),
                       key=lambda record: record["sample_id"])
        missing = [record["sample_id"] for record in below if record["effort"] not in EFFORTS]
        if missing and not reasons:
            raise SystemExit(f"{code}: no effort of the fix for {', '.join(missing)}")
        efforts = Counter(record["effort"] for record in below)
        applicable = sum(scores[score] for score in SCORES)
        rows.append({
            "criterion": code, "level": criterion["level"], "name": criterion["name"], "core": criterion["core"],
            "applies_to": criterion["applies_to"], "applicable": applicable,
            "score_2": scores["2"], "score_1": scores["1"], "score_0": scores["0"],
            "not_applicable": scores[NOT_APPLICABLE], "not_measured": scores[NOT_MEASURED],
            "not_measurable": scores[NOT_MEASURABLE],
            "below_two": len(below), "share_below_two": share(len(below), applicable),
            "effort_low": efforts["low"], "effort_medium": efforts["medium"], "effort_high": efforts["high"],
            "provisional": "yes" if reasons else "", "provisional_reason": "; ".join(reasons),
            "datasets_below_two": " ".join(record["sample_id"] for record in below),
        })
    return rows


def totals(gaps: list[dict]) -> dict:
    """The scores below 2 and their effort over every criterion that is not provisional."""
    counted = [row for row in gaps if not row["provisional"]]
    applicable = sum(row["applicable"] for row in counted)
    below = sum(row["below_two"] for row in counted)
    result = {"applicable": applicable, "below_two": below, "share_below_two": share(below, applicable)}
    for effort in EFFORTS:
        result[effort] = sum(row[f"effort_{effort}"] for row in counted)
    return result


def catalogue_gaps(criteria: list[dict], metadata_all: list[dict], provisional: set[str]) -> list[dict]:
    """One row per criterion that the metadata decide, counted over the datasets of the snapshot."""
    rows = []
    for criterion in criteria:
        code = criterion["id"]
        if code not in CATALOGUE_CRITERIA:
            continue
        column = f"{code.lower()}_score"
        if metadata_all and column not in metadata_all[0]:
            raise SystemExit(f"The table of the metadata checks has no column {column}")
        marked_only = code == MARKED_ONLY
        counted = [record for record in metadata_all if record["m9_marked"] == "True"] if marked_only else metadata_all
        scores = Counter(score_value(record[column]) for record in counted)
        if scores[NOT_APPLICABLE] or scores[NOT_MEASURABLE]:
            raise SystemExit(f"{code}: n/a and not measurable are not scores of the metadata checks")
        determined = sum(scores[score] for score in SCORES)
        below = scores["1"] + scores["0"]
        rows.append({
            "criterion": code, "level": criterion["level"], "name": criterion["name"],
            "counted_over": "datasets with a high-value marking" if marked_only else "every dataset of the snapshot",
            "datasets": len(counted), "score_2": scores["2"], "score_1": scores["1"], "score_0": scores["0"],
            "not_determined": scores[NOT_MEASURED], "below_two": below, "share_below_two": share(below, determined),
            "provisional": "yes" if code in provisional else "", "note": CATALOGUE_NOTES.get(code, ""),
        })
    return rows


def dataset_gaps(criteria: list[dict], assessment: list[dict], records: list[dict]) -> list[dict]:
    """One row per dataset of the sample: its core criteria below 2 by effort and its other scores below 2 by effort."""
    core = {criterion["id"] for criterion in criteria if criterion["core"] == "yes"}
    order = [criterion["id"] for criterion in criteria]
    by_dataset: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        by_dataset[record["sample_id"]][record["criterion"]] = record
    rows = []
    for dataset in sorted(assessment, key=lambda row: row["sample_id"]):
        sample_id = dataset["sample_id"]
        mine = by_dataset.get(sample_id)
        if not mine:
            raise SystemExit(f"No score of {sample_id} in the assessment")
        below = [mine[code] for code in order if code in mine and not mine[code]["provisional"]
                 and score_value(mine[code]["score"]) in ("1", "0")]
        missing = [record["criterion"] for record in below if record["effort"] not in EFFORTS]
        if missing:
            raise SystemExit(f"{sample_id}: no effort of the fix for {', '.join(missing)}")
        core_low = [record["criterion"] for record in below if record["criterion"] in core and record["effort"] == "low"]
        core_heavy = [record["criterion"] for record in below if record["criterion"] in core and record["effort"] != "low"]
        group = READY if not (core_low or core_heavy) else ALMOST_READY if not core_heavy else NOT_YET
        if group != dataset["readiness_group"]:
            raise SystemExit(f"{sample_id}: the rule of the groups gives {group} and the assessment records "
                             f"{dataset['readiness_group']}")
        row = {
            "sample_id": sample_id, "sample_group": dataset["sample_group"], "title": dataset["title"],
            "organisation": dataset["organisation"], "address": dataset["address"], "readiness_group": group,
            "quality_percent": dataset["quality_percent"], "metadata_percent": dataset["metadata_percent"],
            "ai_readiness_percent": dataset["ai_readiness_percent"],
            "core_below_two_low": " ".join(core_low), "core_below_two_medium_or_high": " ".join(core_heavy),
        }
        for effort in EFFORTS:
            row[f"other_below_two_{effort}"] = " ".join(record["criterion"] for record in below
                                                       if record["criterion"] not in core and record["effort"] == effort)
        row["scores_below_two"] = len(below)
        rows.append(row)
    return rows


def single_steps(datasets: list[dict], order: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]], Counter]:
    """The datasets one core criterion away from the ready group, by criterion: those of the group Almost ready with a
    single core criterion below 2, and those of the group Not yet with a single core criterion of medium or high effort;
    and the core criteria of medium or high effort that keep the datasets of the group Not yet."""
    one_low: dict[str, list[str]] = defaultdict(list)
    one_heavy: dict[str, list[str]] = defaultdict(list)
    blocking: Counter = Counter()
    for row in datasets:
        low, heavy = row["core_below_two_low"].split(), row["core_below_two_medium_or_high"].split()
        if row["readiness_group"] == ALMOST_READY and len(low) == 1:
            one_low[low[0]].append(row["sample_id"])
        if row["readiness_group"] == NOT_YET:
            blocking.update(heavy)
            if len(heavy) == 1:
                one_heavy[heavy[0]].append(row["sample_id"])

    def in_order(mapping: dict) -> dict:
        return {code: mapping[code] for code in order if code in mapping}

    return in_order(one_low), in_order(one_heavy), blocking


def in_annex(compliance: list[dict]) -> list[dict]:
    """The datasets whose content is in the Annex, after a check of their answers."""
    rows = [row for row in compliance if row["in_annex"] == "yes"]
    for row in rows:
        for column, _ in REQUIREMENTS:
            if row[column] not in ANSWERS:
                raise SystemExit(f"{row['sample_id']}: unexpected answer '{row[column]}' in {column}")
    return rows


def hvd_dataset_gaps(compliance: list[dict]) -> list[dict]:
    """One row per dataset whose content is in the Annex: the requirements answered no and partly."""
    rows = []
    for row in in_annex(compliance):
        not_met = [title for column, title in REQUIREMENTS if row[column] == NO]
        partly = [title for column, title in REQUIREMENTS if row[column] == PARTLY]
        rows.append({"sample_id": row["sample_id"], "title": row["title"], "address": row["address"],
                     "annex_point": row["annex_point"], "requirements_not_met": "; ".join(not_met),
                     "requirements_partly_met": "; ".join(partly), "gaps": len(not_met) + len(partly)})
    return rows


def hvd_requirement_gaps(compliance: list[dict]) -> list[dict]:
    """One row per requirement: the datasets in the Annex answered no and partly."""
    scope = in_annex(compliance)
    rows = []
    for column, title in REQUIREMENTS:
        not_met = [row["sample_id"] for row in scope if row[column] == NO]
        partly = [row["sample_id"] for row in scope if row[column] == PARTLY]
        rows.append({"column": column, "requirement": title, "datasets": len(scope), "no": len(not_met),
                     "partly": len(partly), "datasets_no": " ".join(not_met), "datasets_partly": " ".join(partly)})
    return rows


def hvd_catalogue_gaps(catalogue: list[dict]) -> list[dict]:
    """The marked datasets of the catalogue that lack each requirement the metadata allow to check."""
    rows = []
    for column, title, lacking in CATALOGUE_REQUIREMENTS:
        count = sum(record[column] == lacking for record in catalogue)
        rows.append({"requirement": title, "datasets": len(catalogue), "lacking": count,
                     "share_lacking": share(count, len(catalogue))})
    return rows


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def by_share(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: (-(row["share_below_two"] or 0), rows.index(row)))


def build_summary(date: str, gaps: list[dict], catalogue: list[dict], snapshot_size: int, datasets: list[dict],
                  hvd_requirements: list[dict], hvd_datasets: list[dict], hvd_catalogue: list[dict]) -> str:
    total = totals(gaps)
    order = [row["criterion"] for row in gaps]
    one_low, one_heavy, blocking = single_steps(datasets, order)
    groups = Counter(row["readiness_group"] for row in datasets)
    lines = [
        f"# Gap analysis, snapshot of {date}", "",
        "A gap is a score below 2 in a criterion that applies to the dataset, read with the effort of its fix: low, "
        "metadata and documentation only; medium, a change in the file itself; high, a change in a system or in the source "
        "of the data. Nothing is judged here: the scores, the effort of the fix and the answers on compliance come from "
        "`13_assessment.py`, `04_metadata_checks.py` and `14_hvd_compliance.py` (DECISIONS.md #57 to #60). Which "
        "high-value datasets are missing from the portal is examined separately.",
        "", "## 1. Gaps by criterion", "", f"### Sample ({len(datasets)} datasets)", "",
        "Datasets: those to which the criterion applies. Share: the scores below 2 of these datasets. Ordered by share.", "",
        "| Criterion | Level | Core | Datasets | 2 | 1 | 0 | Below 2 | Share | Low effort | Medium effort | High effort |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in by_share([row for row in gaps if not row["provisional"]]):
        lines.append(f"| {row['criterion']} {row['name']} | {row['level']} | {row['core']} | {row['applicable']} | "
                     f"{row['score_2']} | {row['score_1']} | {row['score_0']} | {row['below_two']} | "
                     f"{percent(row['share_below_two'])} | {row['effort_low']} | {row['effort_medium']} | "
                     f"{row['effort_high']} |")
    lines += ["", f"All the criteria that are not provisional: {total['below_two']} scores below 2 of {total['applicable']} "
              f"({percent(total['share_below_two'])}); effort of the fix low {total['low']}, medium {total['medium']}, high "
              f"{total['high']}."]
    for row in gaps:
        if row["not_measurable"] and not row["provisional"]:
            lines += ["", f"{row['criterion']} {row['name']}: {row['not_measurable']} datasets not measurable, left out of "
                      "its datasets and of the totals (DECISIONS.md #63)."]
        if row["provisional"]:
            lines += ["", f"{row['criterion']} {row['name']} is provisional and left out of the totals: {row['score_2']} "
                      f"datasets with 2, {row['score_1']} with 1, {row['score_0']} with 0, {row['not_measured']} not "
                      f"measured. Reason: {row['provisional_reason']}."]

    lines += ["", f"### Catalogue ({snapshot_size:,} datasets)", "",
              "The nine criteria that the metadata decide (`04_metadata_checks.py`); the other criteria need the files and "
              "are judged in the sample only. A score that could not be determined is counted apart, and the share is taken "
              "over the datasets with a score. Ordered by share.", "",
              "| Criterion | Counted over | Datasets | 2 | 1 | 0 | Not determined | Below 2 | Share |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in by_share(catalogue):
        name = (f"{row['criterion']} {row['name']}" + (f" ({row['note']})" if row["note"] else "")
                + (" (provisional)" if row["provisional"] else ""))
        lines.append(f"| {name} | {row['counted_over']} | {row['datasets']:,} | {row['score_2']:,} | {row['score_1']:,} | "
                     f"{row['score_0']:,} | {row['not_determined']:,} | {row['below_two']:,} | "
                     f"{percent(row['share_below_two'])} |")

    def listing(mapping: dict) -> str:
        return "; ".join(f"{code}: {', '.join(ids)}" for code, ids in mapping.items()) or "none"

    heavy_order = sorted(blocking.items(), key=lambda item: (-item[1], order.index(item[0])))
    lines += ["", "## 2. What each dataset lacks for the ready group", "",
              "Rule of the groups (DECISIONS.md #20): Ready, every core criterion scores 2; Almost ready, every core criterion "
              "below 2 can be fixed with low effort; Not yet, at least one core criterion below 2 needs medium or high "
              f"effort. Groups: {READY} {groups[READY]}, {ALMOST_READY} {groups[ALMOST_READY]}, {NOT_YET} "
              f"{groups[NOT_YET]}.", "",
              f"- One core criterion of low effort from the ready group: {listing(one_low)}.",
              "- One core criterion of medium or high effort from the ready group, with or without core criteria of low "
              f"effort: {listing(one_heavy)}.",
              "- Core criteria of medium or high effort in the group Not yet: "
              + (", ".join(f"{code} {count}" for code, count in heavy_order) or "none") + ".", "",
              "| Dataset | Title | Group | Core below 2, low effort | Core below 2, medium or high effort | Other below 2, low "
              "| Other below 2, medium | Other below 2, high |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in sorted(datasets, key=lambda row: (GROUPS.index(row["readiness_group"]), row["sample_id"])):
        cells = [row[key] or "-" for key in ("core_below_two_low", "core_below_two_medium_or_high", "other_below_two_low",
                                             "other_below_two_medium", "other_below_two_high")]
        lines.append(f"| {row['sample_id']} | [{md_cell(row['title'])}]({row['address']}) | {row['readiness_group']} | "
                     + " | ".join(cells) + " |")

    scope = hvd_requirements[0]["datasets"] if hvd_requirements else 0
    lines += ["", "## 3. Gaps of compliance of the high-value datasets", "",
              f"Over the {scope} datasets whose content is in the Annex of Implementing Regulation (EU) 2023/138 "
              "(DECISIONS.md #58). Not applicable and not asked by the Annex are not gaps.", "",
              "| Requirement | No | Partly | Datasets answered no | Datasets answered partly |",
              "| --- | ---: | ---: | --- | --- |"]
    for row in hvd_requirements:
        lines.append(f"| {row['requirement']} | {row['no']} | {row['partly']} | {row['datasets_no'] or '-'} | "
                     f"{row['datasets_partly'] or '-'} |")
    lines += ["", "| Dataset | Title | Point of the Annex | Not met | Partly met |", "| --- | --- | --- | --- | --- |"]
    for row in hvd_datasets:
        lines.append(f"| {row['sample_id']} | [{md_cell(row['title'])}]({row['address']}) | {md_cell(row['annex_point'])} | "
                     f"{row['requirements_not_met'] or '-'} | {row['requirements_partly_met'] or '-'} |")
    if hvd_catalogue:
        lines += ["", f"Catalogue: what the metadata allow to check for the {hvd_catalogue[0]['datasets']:,} datasets "
                  "marked as high-value (`14_hvd_compliance.py`).", "",
                  "| Requirement | Datasets without it | Share |", "| --- | ---: | ---: |"]
        for row in hvd_catalogue:
            lines.append(f"| {row['requirement']} | {row['lacking']:,} | {percent(row['share_lacking'])} |")
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_workbook(path: Path, date: str, gaps: list[dict], catalogue: list[dict], datasets: list[dict],
                   hvd_requirements: list[dict], hvd_datasets: list[dict], hvd_catalogue: list[dict]) -> None:
    font, bold = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
    link_font = Font(name="Arial", size=10, color="0563C1", underline="single")
    wrap = Alignment(wrap_text=True, vertical="top")
    centre = Alignment(horizontal="center", vertical="top", wrap_text=True)

    def sheet_of(workbook: Workbook, title: str, columns: list[tuple[str, str, int]], rows: list[dict],
                 link: str = "", first: bool = False):
        sheet = workbook.active if first else workbook.create_sheet()
        sheet.title = title
        for index, (_, heading, width) in enumerate(columns, start=1):
            cell = sheet.cell(row=1, column=index, value=heading)
            cell.font, cell.alignment = bold, centre
            cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
            sheet.column_dimensions[get_column_letter(index)].width = width
        for number, row in enumerate(rows, start=2):
            for index, (key, _, width) in enumerate(columns, start=1):
                value = row[key]
                cell = sheet.cell(row=number, column=index, value="" if value is None else value)
                cell.font = link_font if key == link and value else font
                cell.alignment = centre if width <= 12 else wrap
                if key == link and value:
                    cell.hyperlink = value
                if key == "readiness_group" and value in GROUP_FILLS:
                    cell.fill = PatternFill("solid", fgColor=GROUP_FILLS[value])
        sheet.freeze_panes = "B2"
        return sheet

    workbook = Workbook()
    sheet_of(workbook, "Criteria", [
        ("criterion", "Criterion", 9), ("level", "Level", 22), ("name", "Name", 34), ("core", "Core", 7),
        ("applies_to", "Applies to", 12), ("applicable", "Datasets to which it applies", 12),
        ("score_2", "Score 2", 8), ("score_1", "Score 1", 8), ("score_0", "Score 0", 8),
        ("not_applicable", "Not applicable", 11), ("not_measured", "Not measured", 10),
        ("not_measurable", "Not measurable", 11), ("below_two", "Below 2", 8),
        ("share_below_two", "Share below 2 (%)", 11), ("effort_low", "Low effort", 8),
        ("effort_medium", "Medium effort", 9), ("effort_high", "High effort", 8), ("provisional", "Provisional", 11),
        ("datasets_below_two", "Datasets below 2", 60)], gaps, first=True)
    sheet_of(workbook, "Catalogue", [
        ("criterion", "Criterion", 9), ("level", "Level", 22), ("name", "Name", 34), ("counted_over", "Counted over", 30),
        ("datasets", "Datasets", 10), ("score_2", "Score 2", 9), ("score_1", "Score 1", 9), ("score_0", "Score 0", 9),
        ("not_determined", "Not determined", 11), ("below_two", "Below 2", 9),
        ("share_below_two", "Share below 2 (%)", 11), ("provisional", "Provisional", 11), ("note", "Note", 16)],
        catalogue)
    sheet_of(workbook, "Datasets", [
        ("sample_id", "Dataset", 9), ("title", "Title", 40), ("organisation", "Organisation", 28),
        ("address", "Address", 32), ("sample_group", "Group of the sample", 12), ("readiness_group", "Readiness group", 12),
        ("quality_percent", "Quality (%)", 9), ("metadata_percent", "Metadata (%)", 10),
        ("ai_readiness_percent", "AI readiness (%)", 10), ("core_below_two_low", "Core below 2, low effort", 18),
        ("core_below_two_medium_or_high", "Core below 2, medium or high effort", 18),
        ("other_below_two_low", "Other below 2, low effort", 22), ("other_below_two_medium", "Other below 2, medium effort", 22),
        ("other_below_two_high", "Other below 2, high effort", 18), ("scores_below_two", "Scores below 2", 9)],
        datasets, link="address")
    sheet_of(workbook, "High-value requirements", [
        ("requirement", "Requirement", 40), ("datasets", "Datasets in the Annex", 11), ("no", "No", 7),
        ("partly", "Partly", 7), ("datasets_no", "Datasets answered no", 34),
        ("datasets_partly", "Datasets answered partly", 34)], hvd_requirements)
    sheet_of(workbook, "High-value datasets", [
        ("sample_id", "Dataset", 9), ("title", "Title", 40), ("address", "Address", 32),
        ("annex_point", "Point of the Annex", 30), ("requirements_not_met", "Not met", 44),
        ("requirements_partly_met", "Partly met", 34), ("gaps", "Gaps", 7)], hvd_datasets, link="address")
    sheet_of(workbook, "High-value catalogue", [
        ("requirement", "Requirement", 30), ("datasets", "Marked datasets", 12), ("lacking", "Datasets without it", 12),
        ("share_lacking", "Share (%)", 10)], hvd_catalogue)

    sheet = workbook.create_sheet("Notes")
    sheet.column_dimensions["A"].width = 140
    notes = [
        f"Gap analysis, snapshot of {date}.",
        "A gap is a score below 2 in a criterion that applies to the dataset. Effort of the fix: low, metadata and "
        "documentation only; medium, a change in the file itself; high, a change in a system or in the source of the data.",
        "Nothing is judged in this workbook: the scores, the effort of the fix and the answers on compliance come from "
        "13_assessment.py, 04_metadata_checks.py and 14_hvd_compliance.py (DECISIONS.md #57 to #60).",
        "Sheet Criteria: the 23 criteria in the sample; a score that the reviewer found not measurable is counted apart "
        "and left out of the share (DECISIONS.md #63), and a provisional criterion is listed and left out of the totals. "
        "Sheet Catalogue: the nine criteria that the metadata decide, over the datasets of the snapshot; M9 is counted "
        "over the datasets that carry a high-value marking, and Q5 is its metadata part (DECISIONS.md #36).",
        "Sheet Datasets: what each dataset of the sample lacks for the ready group. The core criteria below 2 decide the "
        "group (DECISIONS.md #20): Ready, every core criterion scores 2; Almost ready, every core criterion below 2 can be "
        "fixed with low effort; Not yet, at least one needs medium or high effort.",
        "Sheets High-value requirements and High-value datasets: the requirements of Implementing Regulation (EU) 2023/138 "
        "answered no or partly for the datasets whose content is in the Annex (DECISIONS.md #58). Sheet High-value "
        "catalogue: the marked datasets of the catalogue that lack a requirement the metadata allow to check.",
    ]
    for index, note in enumerate(notes, start=1):
        cell = sheet.cell(row=index, column=1, value=note)
        cell.font, cell.alignment = (bold if index == 1 else font), wrap
    workbook.save(path)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Gap analysis from the recorded scores, efforts of the fix and answers "
                                                 "on compliance.")
    parser.add_argument("--assessment", type=Path, default=None,
                        help="table of the assessment (default: the newest in data/processed)")
    args = parser.parse_args()

    assessment_file = args.assessment or newest("assessment")
    found = re.search(r"(\d{4}-\d{2}-\d{2})", assessment_file.name)
    if not found:
        raise SystemExit(f"No date in the name of {relative(assessment_file)}")
    date = found.group(1)
    criteria = read_table(CRITERIA_FILE)
    assessment = read_table(assessment_file)
    records = read_table(PROCESSED_DIR / f"assessment_scores_{date}.csv")
    metadata_all = read_table(PROCESSED_DIR / f"metadata_checks_{date}.csv")
    compliance = read_table(PROCESSED_DIR / f"hvd_compliance_{date}.csv")
    compliance_catalogue = read_table(PROCESSED_DIR / f"hvd_compliance_catalogue_{date}.csv")

    gaps = criterion_gaps(criteria, records)
    provisional = {row["criterion"] for row in gaps if row["provisional"]}
    catalogue = catalogue_gaps(criteria, metadata_all, provisional)
    datasets = dataset_gaps(criteria, assessment, records)
    hvd_requirements = hvd_requirement_gaps(compliance)
    hvd_datasets = hvd_dataset_gaps(compliance)
    hvd_catalogue = hvd_catalogue_gaps(compliance_catalogue)

    out_dir = OUT_DIR / f"gap_analysis_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "criteria": PROCESSED_DIR / f"gap_criteria_{date}.csv",
        "catalogue": PROCESSED_DIR / f"gap_catalogue_{date}.csv",
        "datasets": PROCESSED_DIR / f"gap_datasets_{date}.csv",
        "hvd": PROCESSED_DIR / f"gap_hvd_{date}.csv",
    }
    for key, rows in (("criteria", gaps), ("catalogue", catalogue), ("datasets", datasets), ("hvd", hvd_datasets)):
        write_csv(files[key], rows)
    summary = build_summary(date, gaps, catalogue, len(metadata_all), datasets, hvd_requirements, hvd_datasets,
                            hvd_catalogue)
    (out_dir / "summary.md").write_text(summary, encoding="utf-8", newline="\n")
    write_workbook(out_dir / "gap_analysis.xlsx", date, gaps, catalogue, datasets, hvd_requirements, hvd_datasets,
                   hvd_catalogue)

    total = totals(gaps)
    order = [row["criterion"] for row in gaps]
    one_low, one_heavy, _ = single_steps(datasets, order)
    counted = [row for row in gaps if not row["provisional"]]
    largest = by_share(counted)[:3]
    largest_catalogue = by_share([row for row in catalogue if not row["provisional"]])[:3]
    print(f"Assessment: {relative(assessment_file)}")
    print(f"Sample: {len(datasets)} datasets; scores below 2: {total['below_two']} of {total['applicable']} "
          f"({percent(total['share_below_two'])}); effort of the fix low {total['low']}, medium {total['medium']}, "
          f"high {total['high']}")
    print("Provisional, left out of the totals: " + (", ".join(sorted(provisional)) or "none"))
    print("Largest gaps in the sample: " + ", ".join(f"{row['criterion']} {row['below_two']} of {row['applicable']}"
                                                    for row in largest))
    print(f"Catalogue: {len(metadata_all):,} datasets; largest gaps: "
          + ", ".join(f"{row['criterion']} {percent(row['share_below_two'])}" for row in largest_catalogue))
    print(f"One core criterion from the ready group: low effort {sum(len(ids) for ids in one_low.values())} datasets, "
          f"medium or high effort {sum(len(ids) for ids in one_heavy.values())} datasets")
    scope = hvd_requirements[0]["datasets"] if hvd_requirements else 0
    print(f"High-value datasets in the Annex: {scope}; requirements answered no or partly: "
          + (", ".join(f"{row['requirement']} {row['no'] + row['partly']}" for row in hvd_requirements
                       if row["no"] + row["partly"]) or "none"))
    print("Files:")
    for path in list(files.values()) + [out_dir / "summary.md", out_dir / "gap_analysis.xlsx"]:
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
