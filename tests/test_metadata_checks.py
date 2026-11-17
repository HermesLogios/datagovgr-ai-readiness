"""Tests of the metadata checks against the published table of the study."""

import csv
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

from aiready.assessment import NOT_JUDGED, Source, build_assessment
from aiready.criteria import load_criteria
from aiready.metadata_checks import CHECK_IDS, checks_script, run_metadata_checks
from aiready.records import record_type
from aiready.snapshot import iter_snapshot_records, snapshot_reference_date

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
PUBLISHED_TABLE = ROOT / "data" / "processed" / "metadata_checks_2026-10-24.csv"


def published_scores_and_reasons() -> dict[str, dict]:
    with open(PUBLISHED_TABLE, encoding="utf-8-sig", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


class MetadataChecksTest(unittest.TestCase):
    def test_check_ids_follow_the_script(self):
        self.assertEqual(CHECK_IDS, tuple(code for code, _, _ in checks_script().CHECKS))

    def test_reference_date_of_the_snapshot(self):
        self.assertEqual(snapshot_reference_date(SNAPSHOT), date(2026, 10, 24))
        with self.assertRaises(ValueError):
            snapshot_reference_date(Path("catalog.jsonl.gz"))

    def test_whole_snapshot_matches_the_published_table(self):
        published = published_scores_and_reasons()
        criteria = load_criteria()
        reference_date = snapshot_reference_date(SNAPSHOT)
        source = Source("snapshot", f"snapshot {SNAPSHOT.name}", reference_date)
        differences = []
        datasets = 0
        statuses = Counter()
        for record in iter_snapshot_records(SNAPSHOT):
            if record_type(record) != "dataset":
                continue
            datasets += 1
            outputs = run_metadata_checks(record, reference_date)
            row = published[record["id"]]
            for code in CHECK_IDS:
                prefix = code.lower()
                expected_score = None if row[f"{prefix}_score"] == "" else int(float(row[f"{prefix}_score"]))
                if outputs[code].score != expected_score or (outputs[code].reason or "") != row[f"{prefix}_reason"]:
                    differences.append((record["name"], code))
            assessment = build_assessment(record, criteria, outputs, source)
            statuses.update(result.status for result in assessment.scored)
        self.assertEqual(datasets, 22805)
        self.assertEqual(len(published), 22805)
        self.assertEqual(differences, [])
        self.assertEqual(statuses[NOT_JUDGED], 21503)
        self.assertEqual(sum(statuses.values()), 22805 * len(CHECK_IDS))


if __name__ == "__main__":
    unittest.main()
