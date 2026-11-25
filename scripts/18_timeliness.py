r"""
18_timeliness.py
Phase 3, step 9: scores of Q5, timeliness, for the 36 datasets of the sample with the second snapshot of the catalogue
(DECISIONS.md #36, rule e; rules approved by the reviewer on 24 November 2026).

What it does, in order:
  1. Reads the two snapshots of the catalogue (the first, data/raw/catalog_2026-10-24.jsonl.gz, and the second, given
     with --second) and matches every dataset by its identifier, which the portal never changes.
  2. Compares the files of every dataset present in both snapshots. A change of the files is a new file (a resource
     whose address the first snapshot does not have) or a newer upload date (last_modified, read as in
     04_metadata_checks.py, with the correction for the copies of the migration). A resource record created again for
     the same address is not a new file. A dataset without an uploaded file and without a new file is not measurable,
     because a change of a file behind an external address does not show in the catalogue.
  3. Proposes the score of Q5 for the 36 datasets of the sample:
       - rule 1: the newest date inside the data comes first: the newest period read inside the files, otherwise the
         newest period in the names of the files (data/processed/history_checks_2026-10-24.csv), counted to the day on
         which the files were downloaded (data/processed/resource_downloads_2026-10-24.csv), with the limits of #36;
       - otherwise the metadata part of Q5 on the second snapshot (data/processed/metadata_checks_<date>.csv, written
         by 04_metadata_checks.py);
       - rule 2: a dataset that declares a period of one month or shorter and whose files did not change between the
         two snapshots does not score 2;
       - rule 3: a dataset that neither rule 1 nor the metadata can measure stays not measurable, out of the shares;
       - rule 4: the dates issued and modified of the source catalogue (extras) are not used.
  4. Counts, over the catalogue, the datasets that declare a period of one month or shorter and whose files changed,
     did not change or cannot be measured: counts for the study, not scores.
  5. Writes:
       - data/processed/timeliness_sample_<date>.csv, one row per dataset of the sample;
       - data/processed/timeliness_catalogue_<date>.csv, one row per dataset of either snapshot;
       - outputs/timeliness_<date>/summary.md.

The scores are proposals; they become final after the review recorded in DECISIONS.md.

Usage (from the project root, with the .venv activated), after 01_snapshot.py and 04_metadata_checks.py on the second
snapshot:
    python scripts\18_timeliness.py --second data\raw\catalog_2026-11-25.jsonl.gz

Only the snapshots and the tables of the repository are read; no request is sent to the portal or to any other site.
Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import calendar
import csv
import importlib.util
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
METADATA_CHECKS = ROOT / "scripts" / "04_metadata_checks.py"
FIRST_SNAPSHOT = RAW_DIR / "catalog_2026-10-24.jsonl.gz"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
HISTORY_FILE = PROCESSED_DIR / "history_checks_2026-10-24.csv"
DOWNLOADS_FILE = PROCESSED_DIR / "resource_downloads_2026-10-24.csv"

SHORT_PERIOD_DAYS = 31        # a declared period of one month or shorter (rule 2)
AVAILABLE = "available"       # outcome of a successful download attempt in resource_downloads
CHANGED, UNCHANGED, NOT_MEASURABLE = "changed", "unchanged", "not measurable"
NOT_IN_SECOND = "not in the second snapshot"
BOTH, FIRST_ONLY, SECOND_ONLY = "both", "first snapshot only", "second snapshot only"
PERIOD = re.compile(r"(?<!\d)\d{4}(?:-\d{2}(?:-\d{2})?)?(?!\d)")

SAMPLE_COLUMNS = [
    "sample_id", "title", "address", "frequency_first", "frequency", "frequency_group", "period_days",
    "data_end", "data_end_source", "download_date", "score_first", "metadata_score", "files_change", "new_files",
    "updated_files", "last_upload_first", "last_upload_second", "rule", "rule_2", "proposed_score", "reason",
]
CATALOGUE_COLUMNS = [
    "id", "name", "title", "organisation", "presence", "frequency", "frequency_group", "period_days",
    "one_month_or_shorter", "files_first", "files_second", "new_files", "updated_files", "recreated_records",
    "removed_files", "last_upload_first", "last_upload_second", "files_change",
]


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


def write_table(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_metadata_checks():
    """The script of the metadata checks as a module, for its reading of the snapshots and of the upload dates."""
    spec = importlib.util.spec_from_file_location("metadata_checks", METADATA_CHECKS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fmt_int(number) -> str:
    return f"{int(number):,}"


def fmt_share(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def as_day(text) -> date | None:
    try:
        return date.fromisoformat(str(text or "").strip()[:10])
    except ValueError:
        return None


def as_score(text) -> int | None:
    value = str(text or "").strip()
    return int(float(value)) if value else None


def as_period(text) -> float | None:
    value = str(text or "").strip()
    return float(value) if value else None


def period_end(text: str) -> date | None:
    """The last day of the newest period written in the text: a year, a month (YYYY-MM) or a day (YYYY-MM-DD)."""
    ends = []
    for token in PERIOD.findall(text or ""):
        parts = [int(part) for part in token.split("-")]
        try:
            if len(parts) == 1:
                ends.append(date(parts[0], 12, 31))
            elif len(parts) == 2:
                ends.append(date(parts[0], parts[1], calendar.monthrange(parts[0], parts[1])[1]))
            else:
                ends.append(date(parts[0], parts[1], parts[2]))
        except ValueError:
            continue
    return max(ends) if ends else None


def newest_data(history: dict) -> tuple[date | None, str]:
    """The newest date inside the data: from the contents of the files first, then from the names of the files."""
    inside = period_end(history.get("file_period_last", ""))
    if inside:
        return inside, "inside the files"
    named = period_end(history.get("resource_period_last", ""))
    if named:
        return named, "names of the files"
    return None, ""


def download_dates(rows: list[dict]) -> dict[str, date]:
    """The day on which the files of each dataset were read: the newest successful attempt, else the newest attempt."""
    successful, attempted = {}, {}
    for row in rows:
        for number in (1, 2):
            when = as_day(row.get(f"attempt_{number}_date"))
            if not when:
                continue
            sample_id = row["sample_id"]
            attempted[sample_id] = max(when, attempted.get(sample_id, when))
            if row.get(f"attempt_{number}_result") == AVAILABLE:
                successful[sample_id] = max(when, successful.get(sample_id, when))
    return {sample_id: successful.get(sample_id, when) for sample_id, when in attempted.items()}


def file_state(module, dataset: dict) -> dict[str, tuple[str, date | None]]:
    """The files of a dataset: resource identifier -> (address, upload date or None)."""
    created = module.parse_timestamp(dataset.get("metadata_created"))
    state = {}
    for resource in module.own_resources(dataset):
        uploaded, _ = module.upload_date(resource, created)
        address = str(resource.get("url") or resource.get("access_url") or "").strip()
        state[str(resource.get("id") or address)] = (address, uploaded)
    return state


def read_snapshot(module, path: Path) -> dict[str, dict]:
    """The datasets of a snapshot, with what the comparison needs: name, title, organisation and files."""
    if not path.exists():
        raise SystemExit(f"Snapshot not found: {relative(path)}")
    datasets = {}
    for dataset in module.read_datasets(path):
        organisation = dataset.get("organization") or {}
        datasets[str(dataset.get("id"))] = {
            "name": dataset.get("name") or "",
            "title": module.visible_text(dataset.get("title")),
            "organisation": organisation.get("title") or "",
            "files": file_state(module, dataset),
        }
    return datasets


def compare_files(first: dict[str, tuple], second: dict[str, tuple]) -> dict:
    """The change of the files of one dataset between the two snapshots."""
    first_addresses: dict[str, date | None] = {}
    for address, uploaded in first.values():
        if address:
            first_addresses[address] = max(filter(None, (first_addresses.get(address), uploaded)), default=None)
    second_addresses = {address for address, _ in second.values() if address}
    new_files = updated_files = recreated = 0
    for resource_id, (address, uploaded) in second.items():
        if resource_id in first:
            earlier = first[resource_id][1]
        elif address and address in first_addresses:
            recreated += 1
            earlier = first_addresses[address]
        else:
            new_files += 1
            continue
        if uploaded and (earlier is None or uploaded > earlier):
            updated_files += 1
    removed = sum(1 for resource_id, (address, _) in first.items()
                  if resource_id not in second and address not in second_addresses)
    uploads_first = [uploaded for _, uploaded in first.values() if uploaded]
    uploads_second = [uploaded for _, uploaded in second.values() if uploaded]
    if new_files or updated_files:
        change = CHANGED
    elif uploads_first or uploads_second:
        change = UNCHANGED
    else:
        change = NOT_MEASURABLE
    return {
        "files_first": len(first),
        "files_second": len(second),
        "new_files": new_files,
        "updated_files": updated_files,
        "recreated_records": recreated,
        "removed_files": removed,
        "last_upload_first": max(uploads_first).isoformat() if uploads_first else "",
        "last_upload_second": max(uploads_second).isoformat() if uploads_second else "",
        "files_change": change,
    }


def score_from_data(module, group: str, period_days: float | None, stated: bool, frequency: str,
                    newest: date, reference: date) -> tuple[int, str]:
    """Rule 1: the score from the newest date inside the data, counted to the day of the download, limits of #36."""
    declared = frequency or "none"
    if group == "not updated" and stated:
        return 2, f"{declared}: declared as not updated, and the title or description states the period of the data"
    days = (reference - newest).days
    age = max(days, 0)
    delay = f"newest data {newest.isoformat()}, a period that ends after the download of {reference.isoformat()}"
    if group == "periodic" and period_days:
        periods = age / period_days
        score = 2 if periods <= module.Q5_WITHIN_PERIODS else 1 if periods <= module.Q5_LATE_PERIODS else 0
        if days >= 0:
            delay = (f"newest data {newest.isoformat()}, {periods:.1f} periods before the download of "
                     f"{reference.isoformat()}")
        return score, f"{declared}: {delay}"
    prefix = (f"{declared}: declared as not updated without a stated period" if group == "not updated"
              else f"no period declared ({declared})")
    score = 1 if age <= module.Q5_NO_PERIOD_DAYS else 0
    if days >= 0:
        delay = f"newest data {newest.isoformat()}, {days} days before the download of {reference.isoformat()}"
    return score, f"{prefix}: {delay}"


def one_month_or_shorter(group: str, period_days: float | None) -> bool:
    return group == "periodic" and period_days is not None and period_days <= SHORT_PERIOD_DAYS


def propose(module, sample: dict, first_check: dict, second_check: dict | None, history: dict,
            reference: date | None, comparison: dict, dates: tuple[str, str]) -> dict:
    """The proposed score of Q5 for one dataset of the sample, with the evidence and the rule that decides it."""
    check = second_check or first_check
    group = check.get("q5_frequency_group", "")
    period_days = as_period(check.get("q5_period_days"))
    stated = str(check.get("q5_period_stated", "")).strip() == "True"
    frequency = check.get("q5_frequency", "")
    newest, source = newest_data(history)
    metadata_score = as_score(second_check.get("q5_score")) if second_check else None

    if newest and group and reference:
        rule = "1: newest date inside the data"
        base, reason = score_from_data(module, group, period_days, stated, frequency, newest, reference)
        reason += f" ({source})"
    elif metadata_score is not None:
        rule = "metadata part on the second snapshot"
        base, reason = metadata_score, second_check.get("q5_reason", "")
    else:
        rule = "3: not measurable"
        base = None
        reason = (second_check or {}).get("q5_reason") or "not in the second snapshot and no date inside the data"

    rule_2 = ""
    if base is not None and one_month_or_shorter(group, period_days) and comparison["files_change"] == UNCHANGED:
        rule_2 = "applied"
        if base == 2:
            base = 1
        reason += f"; no new or updated file between {dates[0]} and {dates[1]}: at most 1 (rule 2)"
    if first_check.get("q5_frequency", "") != frequency:
        reason += f"; the declared frequency changed from {first_check.get('q5_frequency') or 'none'} to {frequency or 'none'}"

    return {
        "sample_id": sample["sample_id"],
        "title": sample.get("title", ""),
        "address": sample.get("url", ""),
        "frequency_first": first_check.get("q5_frequency", ""),
        "frequency": frequency,
        "frequency_group": group,
        "period_days": check.get("q5_period_days", ""),
        "data_end": newest.isoformat() if newest else "",
        "data_end_source": source,
        "download_date": reference.isoformat() if reference else "",
        "score_first": "" if as_score(first_check.get("q5_score")) is None else as_score(first_check.get("q5_score")),
        "metadata_score": "" if metadata_score is None else metadata_score,
        "files_change": comparison["files_change"],
        "new_files": comparison["new_files"],
        "updated_files": comparison["updated_files"],
        "last_upload_first": comparison["last_upload_first"],
        "last_upload_second": comparison["last_upload_second"],
        "rule": rule,
        "rule_2": rule_2,
        "proposed_score": "" if base is None else base,
        "reason": reason,
    }


def catalogue_rows(first: dict, second: dict, first_checks: dict, second_checks: dict) -> list[dict]:
    """One row per dataset of either snapshot, with the change of its files where the dataset is in both."""
    rows = []
    for dataset_id in sorted(set(first) | set(second)):
        in_first, in_second = dataset_id in first, dataset_id in second
        record = first.get(dataset_id) or second.get(dataset_id)
        check = first_checks.get(dataset_id) or second_checks.get(dataset_id) or {}
        group = check.get("q5_frequency_group", "")
        period_days = as_period(check.get("q5_period_days"))
        row = {
            "id": dataset_id,
            "name": record["name"],
            "title": record["title"],
            "organisation": record["organisation"],
            "presence": BOTH if in_first and in_second else FIRST_ONLY if in_first else SECOND_ONLY,
            "frequency": check.get("q5_frequency", ""),
            "frequency_group": group,
            "period_days": check.get("q5_period_days", ""),
            "one_month_or_shorter": "yes" if one_month_or_shorter(group, period_days) else "no",
        }
        if in_first and in_second:
            row.update(compare_files(first[dataset_id]["files"], second[dataset_id]["files"]))
        else:
            files = record["files"]
            row.update({"files_first": len(files) if in_first else "", "files_second": len(files) if in_second else "",
                        "new_files": "", "updated_files": "", "recreated_records": "", "removed_files": "",
                        "last_upload_first": "", "last_upload_second": "", "files_change": ""})
        rows.append(row)
    return rows


def md_link(title: str, address: str) -> str:
    text = (title or address).replace("|", "/").replace("[", "(").replace("]", ")")
    return f"[{text}]({address})" if address else text


def build_summary(dates: tuple[str, str], snapshot_names: tuple[str, str], catalogue: list[dict],
                  sample_rows: list[dict]) -> str:
    presence = Counter(row["presence"] for row in catalogue)
    both = [row for row in catalogue if row["presence"] == BOTH]
    changes = Counter(row["files_change"] for row in both)
    short = [row for row in both if row["one_month_or_shorter"] == "yes"]
    short_changes = Counter(row["files_change"] for row in short)
    by_frequency: dict[str, Counter] = {}
    for row in short:
        by_frequency.setdefault(row["frequency"], Counter())[row["files_change"]] += 1
    proposed = Counter(str(row["proposed_score"]) or "not measurable" for row in sample_rows)
    provisional = Counter(str(row["score_first"]) or "not measurable" for row in sample_rows)

    lines = [
        f"# Timeliness (Q5) with the second snapshot, {dates[0]} and {dates[1]}",
        "",
        f"Comparison of the snapshots `{snapshot_names[0]}` and `{snapshot_names[1]}` by the identifier of every dataset, "
        "and proposed scores of Q5 for the 36 datasets of the sample (`DECISIONS.md` #36, rule e). A change of the files "
        "is a new file or a newer upload date; a resource record created again for the same address is not a new file. "
        "A dataset without an uploaded file and without a new file is not measurable, because a change behind an "
        "external address does not show in the catalogue. The scores are proposals until the review.",
        "",
        "## The two snapshots",
        "",
        "| Datasets | Count |",
        "| --- | ---: |",
        f"| in the first snapshot ({dates[0]}) | {fmt_int(presence[BOTH] + presence[FIRST_ONLY])} |",
        f"| in the second snapshot ({dates[1]}) | {fmt_int(presence[BOTH] + presence[SECOND_ONLY])} |",
        f"| in both | {fmt_int(presence[BOTH])} |",
        f"| only in the first (removed from the catalogue) | {fmt_int(presence[FIRST_ONLY])} |",
        f"| only in the second (new) | {fmt_int(presence[SECOND_ONLY])} |",
        "",
        "## Files of the datasets present in both snapshots",
        "",
        "| Files between the snapshots | Datasets | Share |",
        "| --- | ---: | ---: |",
    ]
    for state in (CHANGED, UNCHANGED, NOT_MEASURABLE):
        lines.append(f"| {state} | {fmt_int(changes[state])} | {fmt_share(changes[state], len(both))} |")
    lines += [
        "",
        "## Datasets that declare an update of one month or less (rule 2, counts for the study)",
        "",
        f"Declared in the first snapshot and present in both: {fmt_int(len(short))}. Measurable: "
        f"{fmt_int(short_changes[CHANGED] + short_changes[UNCHANGED])}; of these, without any new or updated file in "
        f"the month: {fmt_int(short_changes[UNCHANGED])} "
        f"({fmt_share(short_changes[UNCHANGED], short_changes[CHANGED] + short_changes[UNCHANGED])}).",
        "",
        "| Declared frequency | Datasets | Changed | Unchanged | Not measurable |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for frequency, counts in sorted(by_frequency.items(), key=lambda item: (-sum(item[1].values()), item[0])):
        lines.append(f"| {frequency} | {fmt_int(sum(counts.values()))} | {fmt_int(counts[CHANGED])} | "
                     f"{fmt_int(counts[UNCHANGED])} | {fmt_int(counts[NOT_MEASURABLE])} |")
    lines += [
        "",
        "## The sample",
        "",
        "Rule 1: the newest date inside the data, counted to the day of the download of the files. Otherwise the "
        "metadata part on the second snapshot. Rule 2: a declared period of one month or shorter without any new or "
        "updated file between the snapshots does not score 2. The dates issued and modified of the source catalogue are "
        "not used.",
        "",
        "| Score | Provisional (metadata, first snapshot) | Proposed |",
        "| --- | ---: | ---: |",
    ]
    for score in ("2", "1", "0", "not measurable"):
        lines.append(f"| {score} | {provisional[score]} | {proposed[score]} |")
    lines += [
        "",
        "| Dataset | Title | Frequency | Newest data | Files in the month | Provisional | Proposed | Reason |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in sample_rows:
        newest = f"{row['data_end']} ({row['data_end_source']})" if row["data_end"] else "-"
        lines.append(
            f"| {row['sample_id']} | {md_link(row['title'], row['address'])} | {row['frequency'] or '-'} | {newest} | "
            f"{row['files_change']} | {row['score_first'] if row['score_first'] != '' else '-'} | "
            f"{row['proposed_score'] if row['proposed_score'] != '' else '-'} | {row['reason'].replace('|', '/')} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Scores of Q5, timeliness, with the second snapshot of the catalogue.")
    parser.add_argument("--first", type=Path, default=FIRST_SNAPSHOT, help="first snapshot (default: 2026-10-24)")
    parser.add_argument("--second", type=Path, required=True, help="second snapshot, e.g. data/raw/catalog_2026-11-25.jsonl.gz")
    args = parser.parse_args(argv)

    module = load_metadata_checks()
    first_path = args.first if args.first.is_absolute() else ROOT / args.first
    second_path = args.second if args.second.is_absolute() else ROOT / args.second
    dates = (module.snapshot_date(first_path), module.snapshot_date(second_path))
    if dates[1] <= dates[0]:
        raise SystemExit(f"The second snapshot ({dates[1]}) is not later than the first ({dates[0]}).")
    first_checks_file = PROCESSED_DIR / f"metadata_checks_{dates[0]}.csv"
    second_checks_file = PROCESSED_DIR / f"metadata_checks_{dates[1]}.csv"
    if not second_checks_file.exists():
        raise SystemExit(f"File not found: {relative(second_checks_file)}. "
                         f"Run 04_metadata_checks.py on the second snapshot first.")

    first_checks = {row["id"]: row for row in read_table(first_checks_file)}
    second_checks = {row["id"]: row for row in read_table(second_checks_file)}
    sample = read_table(SAMPLE_FILE)
    history = {row["sample_id"]: row for row in read_table(HISTORY_FILE)}
    downloads = download_dates(read_table(DOWNLOADS_FILE))
    print(f"Snapshots: {relative(first_path)} and {relative(second_path)}")
    first = read_snapshot(module, first_path)
    second = read_snapshot(module, second_path)

    catalogue = catalogue_rows(first, second, first_checks, second_checks)
    sample_rows = []
    for row in sample:
        dataset_id = row["id"]
        if dataset_id in first and dataset_id in second:
            comparison = compare_files(first[dataset_id]["files"], second[dataset_id]["files"])
        else:
            comparison = {"files_change": NOT_IN_SECOND, "new_files": "", "updated_files": "",
                          "last_upload_first": "", "last_upload_second": ""}
        sample_rows.append(propose(module, row, first_checks.get(dataset_id, {}), second_checks.get(dataset_id),
                                   history.get(row["sample_id"], {}), downloads.get(row["sample_id"]), comparison,
                                   dates))

    sample_file = PROCESSED_DIR / f"timeliness_sample_{dates[1]}.csv"
    catalogue_file = PROCESSED_DIR / f"timeliness_catalogue_{dates[1]}.csv"
    summary_file = OUT_DIR / f"timeliness_{dates[1]}" / "summary.md"
    write_table(sample_file, sample_rows, SAMPLE_COLUMNS)
    write_table(catalogue_file, catalogue, CATALOGUE_COLUMNS)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(build_summary(dates, (first_path.name, second_path.name), catalogue, sample_rows),
                            encoding="utf-8", newline="\n")

    presence = Counter(row["presence"] for row in catalogue)
    both = [row for row in catalogue if row["presence"] == BOTH]
    changes = Counter(row["files_change"] for row in both)
    short = Counter(row["files_change"] for row in both if row["one_month_or_shorter"] == "yes")
    proposed = Counter(str(row["proposed_score"]) or "not measurable" for row in sample_rows)
    print(f"Datasets: {fmt_int(presence[BOTH])} in both snapshots, {fmt_int(presence[SECOND_ONLY])} new, "
          f"{fmt_int(presence[FIRST_ONLY])} only in the first")
    print(f"Files in the month: changed {fmt_int(changes[CHANGED])}, unchanged {fmt_int(changes[UNCHANGED])}, "
          f"not measurable {fmt_int(changes[NOT_MEASURABLE])}")
    print(f"Declared period of one month or shorter: {fmt_int(sum(short.values()))}; changed {fmt_int(short[CHANGED])}, "
          f"unchanged {fmt_int(short[UNCHANGED])}, not measurable {fmt_int(short[NOT_MEASURABLE])}")
    print("Sample, proposed scores of Q5: " + ", ".join(
        f"{score}: {proposed[score]}" for score in ("2", "1", "0", "not measurable")))
    print(f"Written: {relative(sample_file)}, {relative(catalogue_file)}, {relative(summary_file)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
