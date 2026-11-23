r"""
13_assessment.py
Phase 3, step 4: assessment of the 36 datasets of the sample: the score of every dataset in each of the 23 criteria,
the score per level, the effort of the fix and the readiness group.

What it does, in order:
  1. Reads the criteria (criteria/criteria.csv), the sample (data/processed/sample.csv), the table of
     04_metadata_checks.py (data/processed/metadata_checks_YYYY-MM-DD.csv, the newest one), the scores given by the
     reviewer (criteria/sample_scores.csv) and the recorded effort of the fix (criteria/sample_effort.csv).
  2. Gives every dataset its score in each criterion:
       - the score of criteria/sample_scores.csv, where the reviewer judged the criterion or corrected an automated
         score after the download test of the sample;
       - "n/a" where the criterion does not apply to the group of the dataset (column applies_to);
       - otherwise the automated score of 04_metadata_checks.py.
  3. Marks as provisional the automated score of Q5, which is the metadata part of the criterion (DECISIONS.md #36):
     it stays out of the score of its level until the reviewer records the final scores.
  4. Computes the score per level: the sum of the scores divided by the maximum possible score (2 for each
     applicable criterion), as a percentage. The three levels are reported separately.
  5. Records the effort of the fix for every score below 2: the level of criteria/sample_effort.csv where one is
     recorded, otherwise the level that the column typical_fix of the criterion names when it names only one. Where
     typical_fix names two levels and none is recorded, the effort stays open and is counted in the summary.
  6. Places every dataset in a readiness group by the six core criteria (DECISIONS.md #20): Ready, all of them
     score 2; Almost ready, every core criterion below 2 can be fixed with low effort; Not yet, at least one needs
     medium or high effort.
  7. Writes:
       - data/processed/assessment_YYYY-MM-DD.csv, one row per dataset;
       - data/processed/assessment_scores_YYYY-MM-DD.csv, one row per dataset and criterion;
       - outputs/assessment_YYYY-MM-DD/summary.md;
       - outputs/assessment_YYYY-MM-DD/assessment.xlsx, the assessment workbook.

Rules:
  - A score is never filled in: a criterion without a score of the reviewer and without an automated score stops the
    run with a message that names the dataset and the criterion.
  - The effort of a core criterion is never left open: the run stops when it is missing, since the group depends on
    it.
  - No request is sent to the portal or to any other site.

Usage (from the project root, with the .venv activated):
    python scripts\13_assessment.py

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
CRITERIA_FILE = ROOT / "criteria" / "criteria.csv"
SCORES_FILE = ROOT / "criteria" / "sample_scores.csv"
EFFORT_FILE = ROOT / "criteria" / "sample_effort.csv"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"

NOT_APPLICABLE = "n/a"
EFFORTS = ("low", "medium", "high")
READY, ALMOST_READY, NOT_YET = "Ready", "Almost ready", "Not yet"
GROUPS = (READY, ALMOST_READY, NOT_YET)
LEVEL_COLUMNS = {"Quality": "quality_percent", "Metadata and legal status": "metadata_percent",
                 "AI-readiness": "ai_readiness_percent"}
# Criteria whose automated score covers one part of the rule: provisional until the reviewer records the final scores.
PROVISIONAL = {"Q5": "metadata part of the criterion; the final scores follow the second snapshot (DECISIONS.md #36)"}

SCORE_FILLS = {2: "E2EFDA", 1: "FFF2CC", 0: "F8CBAD", NOT_APPLICABLE: "EDEDED"}
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


def newest_checks() -> Path:
    files = sorted(PROCESSED_DIR.glob("metadata_checks_????-??-??.csv"))
    if not files:
        raise SystemExit("No table of metadata checks in data/processed. Run 04_metadata_checks.py first.")
    return files[-1]


def usual_efforts(typical_fix: str) -> list[str]:
    """The levels of effort that the column typical_fix names, in the order low, medium, high."""
    named = {match.lower() for match in re.findall(r"\b(Low|Medium|High):", typical_fix)}
    return [effort for effort in EFFORTS if effort in named]


def rules_of(how_to_check: str) -> str:
    """The decisions that record the rules of a criterion, from the end of the column how_to_check."""
    match = re.search(r"Rules in full: DECISIONS\.md (.+?)\.?$", how_to_check.strip())
    return match.group(1) if match else ""


def level_percent(scores: list[int]) -> float | None:
    """Sum of the scores divided by the maximum possible score, as a percentage with one decimal (a half is rounded
    up); None without any score."""
    if not scores:
        return None
    value = Decimal(100 * sum(scores)) / Decimal(2 * len(scores))
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def readiness_group(core_below_two: dict[str, str]) -> str:
    """The group of a dataset, from the effort of the fix of each core criterion that scores below 2."""
    if not core_below_two:
        return READY
    return ALMOST_READY if all(effort == "low" for effort in core_below_two.values()) else NOT_YET


def load_recorded(path: Path, column: str, allowed: tuple[str, ...], sample_ids: set[str], codes: set[str]) -> dict:
    """The rows of a file of the reviewer, by dataset and criterion; the run stops on a row that cannot be used."""
    recorded = {}
    for number, row in enumerate(read_table(path), start=2):
        key = (row["sample_id"], row["criterion"])
        if row["sample_id"] not in sample_ids or row["criterion"] not in codes:
            raise SystemExit(f"{relative(path)}, line {number}: unknown dataset or criterion ({key[0]}, {key[1]})")
        if row[column] not in allowed:
            raise SystemExit(f"{relative(path)}, line {number}: {column} '{row[column]}' is not one of {', '.join(allowed)}")
        if key in recorded:
            raise SystemExit(f"{relative(path)}, line {number}: second row for {key[0]} and {key[1]}")
        recorded[key] = row
    return recorded


def assess(criteria: list[dict], sample: list[dict], checks: dict[str, dict], reviewed: dict, efforts: dict) -> list[dict]:
    """One record per dataset and criterion: score, basis, decision, provisional mark and effort of the fix."""
    records = []
    for dataset in sample:
        sample_id = dataset["sample_id"]
        automated = checks.get(dataset["name"])
        if automated is None:
            raise SystemExit(f"Dataset {sample_id} is missing from the table of the metadata checks")
        for criterion in criteria:
            code = criterion["id"]
            column = f"{code.lower()}_score"
            rules = rules_of(criterion["how_to_check"])
            provisional = ""
            if (sample_id, code) in reviewed:
                row = reviewed[(sample_id, code)]
                score = NOT_APPLICABLE if row["score"] == NOT_APPLICABLE else int(row["score"])
                basis, decision = "reviewed", row["decision"]
            elif criterion["applies_to"] not in ("all", dataset["group"]):
                score, basis, decision = NOT_APPLICABLE, "not applicable to the group", rules
            elif column in automated:
                score = None if automated[column] == "" else int(float(automated[column]))
                basis, decision = "automatic", rules
                if code in PROVISIONAL:
                    provisional = PROVISIONAL[code]
                elif score is None:
                    raise SystemExit(f"No automated score for {sample_id} in {code}: a score of the reviewer is needed "
                                     f"in {relative(SCORES_FILE)}")
            else:
                raise SystemExit(f"No score for {sample_id} in {code}: a row is needed in {relative(SCORES_FILE)}")

            effort, effort_basis = "", ""
            if (sample_id, code) in efforts and score not in (0, 1):
                raise SystemExit(f"{relative(EFFORT_FILE)}: an effort is recorded for {sample_id} in {code}, whose score "
                                 "is not below 2")
            if score in (0, 1) and not provisional:
                usual = usual_efforts(criterion["typical_fix"])
                if (sample_id, code) in efforts:
                    row = efforts[(sample_id, code)]
                    effort, effort_basis = row["effort"], f"recorded ({row['decision']})"
                elif len(usual) == 1:
                    effort, effort_basis = usual[0], "usual case of the criterion"
                else:
                    effort_basis = "open"
            records.append({
                "sample_id": sample_id, "criterion": code, "name": criterion["name"], "level": criterion["level"],
                "core": criterion["core"], "score": score, "basis": basis, "decision": decision,
                "provisional": provisional, "effort": effort, "effort_basis": effort_basis,
            })
    return records


def dataset_rows(criteria: list[dict], sample: list[dict], records: list[dict]) -> list[dict]:
    """One row per dataset: its scores, the score per level, the core criteria below 2 by effort and the group."""
    by_dataset: dict[str, dict[str, dict]] = {}
    for record in records:
        by_dataset.setdefault(record["sample_id"], {})[record["criterion"]] = record
    rows = []
    for dataset in sample:
        sample_id = dataset["sample_id"]
        mine = by_dataset[sample_id]
        row = {"sample_id": sample_id, "sample_group": dataset["group"], "title": dataset["title"],
               "organisation": dataset["organization_title"], "address": dataset["url"]}
        for criterion in criteria:
            row[criterion["id"]] = mine[criterion["id"]]["score"]
        for level, column in LEVEL_COLUMNS.items():
            scores = [mine[c["id"]]["score"] for c in criteria
                      if c["level"] == level and isinstance(mine[c["id"]]["score"], int) and not mine[c["id"]]["provisional"]]
            row[column] = level_percent(scores)
        core_below_two = {c["id"]: mine[c["id"]]["effort"] for c in criteria
                          if c["core"] == "yes" and mine[c["id"]]["score"] in (0, 1)}
        missing = [code for code, effort in core_below_two.items() if not effort]
        if missing:
            raise SystemExit(f"The effort of the fix of {', '.join(missing)} is not recorded for {sample_id} in "
                             f"{relative(EFFORT_FILE)}: the group of the dataset depends on it")
        row["core_low_effort"] = " ".join(code for code, effort in core_below_two.items() if effort == "low")
        row["core_medium_or_high_effort"] = " ".join(code for code, effort in core_below_two.items() if effort != "low")
        row["readiness_group"] = readiness_group(core_below_two)
        rows.append(row)
    return rows


def shown(score) -> str:
    """A score as it is written in the tables: empty when the criterion is not measured yet."""
    return "" if score is None else str(score)


def percent_text(value) -> str:
    return "" if value is None else f"{value:.1f}%"


def md_cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def mean(values: list[float]) -> str:
    return f"{sum(values) / len(values):.1f}%" if values else ""


def build_summary(criteria: list[dict], rows: list[dict], records: list[dict], date: str, checks_name: str) -> str:
    lines = [
        f"# Assessment of the sample, snapshot of {date}", "",
        f"Scores of the {len(rows)} datasets of the sample in the {len(criteria)} criteria of `criteria/criteria.csv`: the "
        f"scores given by the reviewer (`{relative(SCORES_FILE)}`) and, for the criteria checked on the metadata, the "
        f"automated scores of `04_metadata_checks.py` (`{checks_name}`). Scale: 2 fully met, 1 partly met, 0 not met, "
        "n/a not applicable. The rules of every criterion and the reviews of the scores are recorded in `DECISIONS.md`.",
        "", "## Readiness groups", "",
        "The six core criteria decide the group (DECISIONS.md #20): Ready, all of them score 2; Almost ready, every core "
        "criterion below 2 can be fixed with low effort; Not yet, at least one needs medium or high effort.", "",
        "| Group | Datasets | High-value | Comparison | Datasets of the group |", "| --- | ---: | ---: | ---: | --- |",
    ]
    for group in GROUPS:
        members = [row for row in rows if row["readiness_group"] == group]
        lines.append(f"| {group} | {len(members)} | {sum(row['sample_group'] == 'high-value' for row in members)} | "
                     f"{sum(row['sample_group'] == 'comparison' for row in members)} | "
                     f"{', '.join(row['sample_id'] for row in members)} |")

    lines += ["", "## Score per level", "",
              "Sum of the scores divided by the maximum possible score (2 for each applicable criterion). The levels are "
              "not combined into one number. Mean of the datasets of each group of the sample:", "",
              "| Group of the sample | Datasets | " + " | ".join(LEVEL_COLUMNS) + " |", "| --- | ---: | ---: | ---: | ---: |"]
    for label, members in (("high-value", [row for row in rows if row["sample_group"] == "high-value"]),
                           ("comparison", [row for row in rows if row["sample_group"] == "comparison"]), ("all", rows)):
        means = " | ".join(mean([row[column] for row in members if row[column] is not None]) for column in LEVEL_COLUMNS.values())
        lines.append(f"| {label} | {len(members)} | {means} |")
    provisional = sorted({record["criterion"] for record in records if record["provisional"]})
    if provisional:
        lines += ["", f"Left out of the score of its level while provisional: {', '.join(provisional)}."]

    lines += ["", "## Datasets", "",
              "| Dataset | Title | " + " | ".join(LEVEL_COLUMNS) + " | Core criteria below 2, low effort | Core criteria "
              "below 2, medium or high effort | Group |", "| --- | --- | ---: | ---: | ---: | --- | --- | --- |"]
    for row in rows:
        levels = " | ".join(percent_text(row[column]) for column in LEVEL_COLUMNS.values())
        lines.append(f"| {row['sample_id']} | [{md_cell(row['title'])}]({row['address']}) | {levels} | "
                     f"{row['core_low_effort'] or '-'} | {row['core_medium_or_high_effort'] or '-'} | "
                     f"{row['readiness_group']} |")

    lines += ["", "## Scores by criterion", "",
              "| Criterion | Name | Core | 2 | 1 | 0 | n/a | Not measured | Basis |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for criterion in criteria:
        mine = [record for record in records if record["criterion"] == criterion["id"]]
        counts = Counter(shown(record["score"]) for record in mine)
        bases = Counter(record["basis"] for record in mine if record["basis"] != "not applicable to the group")
        basis = ", ".join(f"{name} {count}" for name, count in bases.most_common())
        if any(record["provisional"] for record in mine):
            basis += " (provisional)"
        lines.append(f"| {criterion['id']} | {criterion['name']} | {criterion['core']} | {counts['2']} | {counts['1']} | "
                     f"{counts['0']} | {counts[NOT_APPLICABLE]} | {counts['']} | {basis} |")

    lines += ["", "## Effort of the fix for the scores below 2", "",
              "Low: metadata and documentation only. Medium: a change in the file itself. High: a change in a system or in "
              "the source of the data. Open: the criterion names two levels and none is recorded yet for the dataset.", "",
              "| Criterion | Scores below 2 | Low | Medium | High | Open |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    open_total = 0
    for criterion in criteria:
        mine = [record for record in records
                if record["criterion"] == criterion["id"] and record["score"] in (0, 1) and not record["provisional"]]
        counts = Counter(record["effort"] or "open" for record in mine)
        open_total += counts["open"]
        lines.append(f"| {criterion['id']} | {len(mine)} | {counts['low']} | {counts['medium']} | {counts['high']} | "
                     f"{counts['open']} |")

    lines += ["", "## Open points", ""]
    for code in provisional:
        mine = [record for record in records if record["criterion"] == code]
        lines.append(f"- {code}: provisional, {PROVISIONAL[code]}; "
                     f"{sum(record['score'] is None for record in mine)} datasets are not measured from the metadata.")
    lines.append(f"- Effort of the fix still open: {open_total} scores below 2 in criteria that name two levels.")
    return "\n".join(lines) + "\n"


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: "" if row[column] is None else row[column] for column in columns})


def write_workbook(path: Path, criteria: list[dict], rows: list[dict], records: list[dict], date: str) -> None:
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
        return cell

    codes = [criterion["id"] for criterion in criteria]
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Datasets"
    header(sheet, ["Dataset", "Group of the sample", "Title", "Organisation", "Address"] + codes + list(LEVEL_COLUMNS)
           + ["Core criteria below 2, low effort", "Core criteria below 2, medium or high effort", "Readiness group"],
           [9, 12, 44, 30, 34] + [6] * len(codes) + [12, 14, 13, 18, 18, 14])
    for index, row in enumerate(rows, start=2):
        put(sheet, index, 1, row["sample_id"], centred=True)
        put(sheet, index, 2, row["sample_group"], centred=True)
        put(sheet, index, 3, row["title"])
        put(sheet, index, 4, row["organisation"])
        put(sheet, index, 5, row["address"], address=row["address"])
        for column, code in enumerate(codes, start=6):
            put(sheet, index, column, "" if row[code] is None else row[code], centred=True, fill=SCORE_FILLS.get(row[code]))
        for column, name in enumerate(LEVEL_COLUMNS.values(), start=6 + len(codes)):
            put(sheet, index, column, row[name], centred=True).number_format = "0.0"
        put(sheet, index, 9 + len(codes), row["core_low_effort"], centred=True)
        put(sheet, index, 10 + len(codes), row["core_medium_or_high_effort"], centred=True)
        put(sheet, index, 11 + len(codes), row["readiness_group"], centred=True)
    sheet.freeze_panes = "F2"

    sheet = workbook.create_sheet("Scores")
    columns = ["sample_id", "criterion", "name", "level", "core", "score", "basis", "decision", "provisional", "effort",
               "effort_basis"]
    header(sheet, ["Dataset", "Criterion", "Name", "Level", "Core", "Score", "Basis", "Decision", "Provisional",
                   "Effort of the fix", "Basis of the effort"], [9, 10, 36, 26, 7, 8, 24, 20, 50, 12, 28])
    for index, record in enumerate(records, start=2):
        for column, name in enumerate(columns, start=1):
            value = "" if record[name] is None else record[name]
            put(sheet, index, column, value, centred=name in ("sample_id", "criterion", "core", "score", "effort"),
                fill=SCORE_FILLS.get(record["score"]) if name == "score" else None)
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(records) + 1}"

    sheet = workbook.create_sheet("Criteria")
    header(sheet, ["Criterion", "Level", "Name", "Core", "Applies to", "Usual fix", "Rules (DECISIONS.md)"],
           [10, 26, 38, 7, 12, 60, 22])
    for index, criterion in enumerate(criteria, start=2):
        values = [criterion["id"], criterion["level"], criterion["name"], criterion["core"], criterion["applies_to"],
                  criterion["typical_fix"], rules_of(criterion["how_to_check"])]
        for column, value in enumerate(values, start=1):
            put(sheet, index, column, value, centred=column in (1, 4, 5))

    sheet = workbook.create_sheet("Notes")
    sheet.column_dimensions["A"].width = 140
    notes = [
        f"Assessment of the sample, snapshot of {date}.",
        "Scale: 2 fully met, 1 partly met, 0 not met, n/a not applicable. An empty score is a criterion that is not "
        "measured yet.",
        "Score per level: the sum of the scores divided by the maximum possible score (2 for each applicable criterion), "
        "as a percentage. The three levels are not combined into one number.",
    ] + [f"{code} is provisional and left out of the score of its level: {reason}." for code, reason in PROVISIONAL.items()
         if any(record["provisional"] for record in records if record["criterion"] == code)] + [
        "Readiness group, from the six core criteria: Ready, all of them score 2; Almost ready, every core criterion below "
        "2 can be fixed with low effort; Not yet, at least one needs medium or high effort.",
        "Effort of the fix: low, metadata and documentation only; medium, a change in the file itself; high, a change in "
        "a system or in the source of the data.",
        "Basis of a score: reviewed, given by the reviewer and recorded in criteria/sample_scores.csv; automatic, the "
        "score of 04_metadata_checks.py.",
    ]
    for index, note in enumerate(notes, start=1):
        cell = sheet.cell(row=index, column=1, value=note)
        cell.font, cell.alignment = (bold if index == 1 else font), wrap
    workbook.save(path)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Assessment of the datasets of the sample: scores, score per level, "
                                                 "effort of the fix and readiness group.")
    parser.add_argument("--checks", type=Path, default=None,
                        help="table of the metadata checks (default: the newest in data/processed)")
    args = parser.parse_args()

    checks_file = args.checks or newest_checks()
    found = re.search(r"(\d{4}-\d{2}-\d{2})", checks_file.name)
    if not found:
        raise SystemExit(f"No date in the name of {relative(checks_file)}")
    date = found.group(1)
    criteria = read_table(CRITERIA_FILE)
    sample = sorted(read_table(SAMPLE_FILE), key=lambda row: row["sample_id"])
    checks = {row["name"]: row for row in read_table(checks_file) if row.get("sample_id")}
    sample_ids = {row["sample_id"] for row in sample}
    codes = {criterion["id"] for criterion in criteria}
    reviewed = load_recorded(SCORES_FILE, "score", ("0", "1", "2", NOT_APPLICABLE), sample_ids, codes)
    efforts = load_recorded(EFFORT_FILE, "effort", EFFORTS, sample_ids, codes)

    records = assess(criteria, sample, checks, reviewed, efforts)
    rows = dataset_rows(criteria, sample, records)

    out_dir = OUT_DIR / f"assessment_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    datasets_file = PROCESSED_DIR / f"assessment_{date}.csv"
    scores_file = PROCESSED_DIR / f"assessment_scores_{date}.csv"
    write_csv(datasets_file, list(rows[0]), rows)
    write_csv(scores_file, list(records[0]), records)
    (out_dir / "summary.md").write_text(build_summary(criteria, rows, records, date, relative(checks_file)),
                                        encoding="utf-8", newline="\n")
    write_workbook(out_dir / "assessment.xlsx", criteria, rows, records, date)

    print(f"Metadata checks: {relative(checks_file)}")
    print(f"Datasets: {len(rows)}; criteria: {len(criteria)}; scores of the reviewer: {len(reviewed)}")
    groups = Counter(row["readiness_group"] for row in rows)
    print("Readiness groups: " + ", ".join(f"{group} {groups[group]}" for group in GROUPS))
    for code in sorted({record["criterion"] for record in records if record["provisional"]}):
        missing = sum(record["score"] is None for record in records if record["criterion"] == code)
        print(f"Provisional: {code}, left out of the score of its level; not measured in {missing} datasets")
    still_open = Counter(record["criterion"] for record in records if record["effort_basis"] == "open")
    print("Effort of the fix still open: " + (", ".join(f"{code} {count}" for code, count in still_open.items()) or "none"))
    print("Files:")
    for path in (datasets_file, scores_file, out_dir / "summary.md", out_dir / "assessment.xlsx"):
        print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
