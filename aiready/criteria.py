"""Criteria of the assessment, read from criteria/criteria.csv."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRITERIA_FILE = ROOT / "criteria" / "criteria.csv"
CRITERIA_VERSION = "1.3"

# Criteria that are not scored from the metadata, grouped by what their assessment needs.
NEEDS_FILES = ("Q1", "Q2", "Q3", "Q4", "AI1", "AI6")
NEEDS_JUDGEMENT = ("M5", "M8", "M10", "AI2", "AI3", "AI4", "AI5", "AI7")

EFFORT_ORDER = ("Low", "Medium", "High")


@dataclass(frozen=True)
class Criterion:
    id: str
    level: str
    name: str
    question: str
    score_0: str
    score_1: str
    score_2: str
    not_applicable: str
    method: str
    core: bool
    applies_to: str
    typical_fix: str


def load_criteria(path: Path = CRITERIA_FILE) -> dict[str, Criterion]:
    """Reads the criteria in the order of the file, keyed by their identifier."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return {
            row["id"]: Criterion(
                id=row["id"],
                level=row["level"],
                name=row["name"],
                question=row["question"],
                score_0=row["score_0"],
                score_1=row["score_1"],
                score_2=row["score_2"],
                not_applicable=row["not_applicable"],
                method=row["method"],
                core=row["core"] == "yes",
                applies_to=row["applies_to"],
                typical_fix=row["typical_fix"],
            )
            for row in csv.DictReader(handle)
        }


def result_kind(criterion: Criterion) -> str:
    """'by rule' when the method of the criterion is fully automatic, 'proposal' otherwise.

    A proposal is a score that the study confirms with a look at the dataset.
    """
    return "by rule" if criterion.method == "automatic" else "proposal"


def effort_levels(typical_fix: str) -> list[str]:
    """Effort levels named in the typical fix of a criterion, in the order of the text."""
    return re.findall(r"\b(Low|Medium|High):", typical_fix)
