"""Assessments and page models of two datasets of the catalogue snapshot, for the tests of the reports and the page."""

from functools import lru_cache
from pathlib import Path

from aiready.assessment import Assessment, Source, build_assessment
from aiready.criteria import load_criteria
from aiready.identifier import DatasetIdentifier
from aiready.metadata_checks import run_metadata_checks
from aiready.plain_language import PageModel, build_page_model
from aiready.snapshot import find_dataset_record, snapshot_reference_date
from aiready.texts import load_texts

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
CRITERIA = load_criteria()
SOURCE = Source("snapshot", f"snapshot {SNAPSHOT.name}", snapshot_reference_date(SNAPSHOT))
EXAMPLE = "troxaia-atyxhmata"                           # marked as high-value, four checks partly met
UNMARKED = "gis-ypen-wfd-wms-kallikratikoi_dimoi"       # no high-value marking, timeliness not measured


@lru_cache(maxsize=None)
def snapshot_record(name: str) -> dict:
    return find_dataset_record(SNAPSHOT, DatasetIdentifier("name", name))


@lru_cache(maxsize=None)
def assessment_of(name: str) -> Assessment:
    record = snapshot_record(name)
    return build_assessment(record, CRITERIA, run_metadata_checks(record, SOURCE.date), SOURCE)


def page_model(name: str, language: str = "el") -> PageModel:
    return build_page_model(assessment_of(name), load_texts(language), CRITERIA)
