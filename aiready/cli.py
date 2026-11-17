"""Command line of the tool: python -m aiready.

Usage:
    python -m aiready troxaia-atyxhmata
    python -m aiready https://data.gov.gr/dataset/troxaia-atyxhmata --out assessments
    python -m aiready troxaia-atyxhmata --snapshot data/raw/catalog_2026-10-24.jsonl.gz
    python -m aiready troxaia-atyxhmata --lang el --out assessments --format xlsx
"""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

from aiready import portal
from aiready.assessment import Assessment, Source, build_assessment
from aiready.criteria import Criterion, load_criteria
from aiready.identifier import parse_dataset_identifier
from aiready.metadata_checks import run_metadata_checks
from aiready.plain_language import build_page_model
from aiready.records import DatasetNotFound, NotADataset, PortalError
from aiready.report import FORMATS, console_text, write_reports
from aiready.report_excel import excel_bytes
from aiready.report_plain import plain_text
from aiready.snapshot import find_dataset_record, snapshot_reference_date
from aiready.texts import LANGUAGES, load_texts

EXCEL_FORMAT = "xlsx"
EXCEL_LANGUAGE = "en"      # language of the Excel report when no language is asked


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aiready",
        description="Applies the metadata checks of the study to datasets of data.gov.gr.",
    )
    parser.add_argument(
        "datasets",
        nargs="+",
        metavar="DATASET",
        help="name, identifier or address of a dataset of data.gov.gr",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        metavar="FILE",
        help="read the datasets from a stored catalogue snapshot instead of the portal",
    )
    parser.add_argument(
        "--lang",
        choices=LANGUAGES,
        help="print the summary in plain language, in Greek (el) or English (en); also the language of the Excel report",
    )
    parser.add_argument("--out", type=Path, metavar="FOLDER", help="write a report per dataset in this folder")
    parser.add_argument(
        "--format",
        nargs="+",
        choices=(*FORMATS, EXCEL_FORMAT),
        default=list(FORMATS),
        help="formats of the reports written with --out (default: md json)",
    )
    return parser


def assess_dataset(text: str, criteria: dict[str, Criterion], snapshot: Path | None) -> Assessment:
    """Assessment of the dataset named by the text, read from the snapshot or from the portal."""
    identifier = parse_dataset_identifier(text)
    if snapshot is not None:
        record = find_dataset_record(snapshot, identifier)
        source = Source("snapshot", f"snapshot {snapshot.name}", snapshot_reference_date(snapshot))
    else:
        record = portal.fetch_dataset_record(identifier)
        today = date.today()
        source = Source("portal", f"{portal.portal_base_url()}, read on {today.isoformat()}", today)
    return build_assessment(record, criteria, run_metadata_checks(record, source.date), source)


def failure_text(error: Exception, snapshot: Path | None) -> str:
    """One-line explanation of why a dataset could not be assessed."""
    place = f"in the snapshot {snapshot.name}" if snapshot is not None else "on the portal"
    if isinstance(error, DatasetNotFound):
        return f"no dataset with this name or identifier {place}"
    if isinstance(error, NotADataset):
        return f"the record is a {error.record_type} of the catalogue, not a dataset; the criteria apply to datasets"
    return str(error)


def write_excel_report(assessment: Assessment, criteria: dict[str, Criterion], language: str, out_dir: Path) -> Path:
    """Writes the Excel report in plain language and returns its path."""
    texts = load_texts(language)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{assessment.dataset.name}_{assessment.source.date.isoformat()}.{EXCEL_FORMAT}"
    path.write_bytes(excel_bytes(build_page_model(assessment, texts, criteria), texts))
    return path


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.snapshot is not None:
        if not arguments.snapshot.is_file():
            parser.error(f"snapshot not found: {arguments.snapshot}")
        try:
            snapshot_reference_date(arguments.snapshot)
        except ValueError as error:
            parser.error(str(error))
    criteria = load_criteria()
    failures = 0
    shown = 0
    for position, text in enumerate(arguments.datasets):
        if position and arguments.snapshot is None:
            time.sleep(portal.PAUSE_SECONDS)
        try:
            assessment = assess_dataset(text, criteria, arguments.snapshot)
        except (ValueError, DatasetNotFound, NotADataset, PortalError) as error:
            failures += 1
            print(f"{text}: {failure_text(error, arguments.snapshot)}", file=sys.stderr)
            continue
        if shown:
            print()
        shown += 1
        if arguments.lang:
            texts = load_texts(arguments.lang)
            print(plain_text(build_page_model(assessment, texts, criteria), texts), end="")
        else:
            print(console_text(assessment), end="")
        if arguments.out is not None:
            technical = [name for name in arguments.format if name != EXCEL_FORMAT]
            written = write_reports(assessment, arguments.out, technical)
            if EXCEL_FORMAT in arguments.format:
                written.append(write_excel_report(assessment, criteria, arguments.lang or EXCEL_LANGUAGE, arguments.out))
            for path in written:
                print(f"Report written: {path}")
    return 1 if failures else 0
