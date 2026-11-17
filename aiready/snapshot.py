"""Reading of one dataset record from a stored catalogue snapshot (data/raw/catalog_<date>.jsonl.gz)."""

import gzip
import json
import re
from datetime import date, datetime
from pathlib import Path

from aiready.identifier import DatasetIdentifier
from aiready.records import DatasetNotFound, require_dataset


def iter_snapshot_records(snapshot: Path):
    """Yields every record of the snapshot: datasets, data services and decisions."""
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def snapshot_reference_date(snapshot: Path) -> date:
    """Date of the snapshot, taken from its file name."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", snapshot.name)
    if not match:
        raise ValueError(f"the file name {snapshot.name} holds no date (expected catalog_YYYY-MM-DD.jsonl.gz)")
    return datetime.strptime(match.group(1), "%Y-%m-%d").date()


def find_dataset_record(snapshot: Path, identifier: DatasetIdentifier) -> dict:
    """Returns the record of the snapshot with the given name or identifier.

    Raises DatasetNotFound when the snapshot has no such record and NotADataset when the
    record is a data service or a decision.
    """
    for record in iter_snapshot_records(snapshot):
        if record.get(identifier.kind) == identifier.value:
            return require_dataset(record)
    raise DatasetNotFound(identifier.value)
