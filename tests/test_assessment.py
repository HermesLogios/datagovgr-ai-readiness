"""Tests of the assessment built from the metadata checks of one dataset."""

import csv
import unittest
from pathlib import Path

from aiready.assessment import NOT_JUDGED, Source, build_assessment
from aiready.criteria import NEEDS_FILES, NEEDS_JUDGEMENT, load_criteria
from aiready.identifier import DatasetIdentifier
from aiready.metadata_checks import CHECK_IDS, run_metadata_checks
from aiready.snapshot import find_dataset_record, snapshot_reference_date

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
PUBLISHED_TABLE = ROOT / "data" / "processed" / "metadata_checks_2026-10-24.csv"


def published_rows_of_the_sample() -> dict[str, dict]:
    with open(PUBLISHED_TABLE, encoding="utf-8-sig", newline="") as handle:
        return {row["sample_id"]: row for row in csv.DictReader(handle) if row["sample_id"]}


class AssessmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.criteria = load_criteria()
        cls.sample = published_rows_of_the_sample()
        cls.reference_date = snapshot_reference_date(SNAPSHOT)
        cls.source = Source("snapshot", f"snapshot {SNAPSHOT.name}", cls.reference_date)

    def assess(self, sample_id: str):
        record = find_dataset_record(SNAPSHOT, DatasetIdentifier("name", self.sample[sample_id]["name"]))
        outputs = run_metadata_checks(record, self.reference_date)
        return build_assessment(record, self.criteria, outputs, self.source)

    def test_dataset_with_partly_met_checks(self):
        assessment = self.assess("S06")
        self.assertEqual(assessment.dataset.name, "troxaia-atyxhmata")
        self.assertEqual(assessment.dataset.title, "Τροχαία ατυχήματα")
        self.assertEqual(assessment.dataset.publisher, "Υπουργείο Προστασίας του Πολίτη")
        self.assertEqual(assessment.dataset.url, "https://data.gov.gr/dataset/troxaia-atyxhmata")
        self.assertTrue(assessment.dataset.high_value_marked)
        self.assertEqual([result.criterion_id for result in assessment.scored], list(CHECK_IDS))
        self.assertEqual(assessment.status_counts(), {"met": 5, "partly met": 4})
        self.assertEqual(assessment.scored_count, 9)
        by_id = {result.criterion_id: result for result in assessment.scored}
        self.assertEqual(by_id["M1"].score, 1)
        self.assertEqual(by_id["M1"].reason, "description of 76 characters (minimum 100)")
        self.assertEqual(by_id["M1"].kind, "proposal")
        self.assertEqual(by_id["M2"].kind, "by rule")
        self.assertEqual(by_id["M1"].measurements["description_chars"], 76)

    def test_problems_are_ordered_by_core_then_effort(self):
        assessment = self.assess("S06")
        self.assertEqual([problem.criterion_id for problem in assessment.problems], ["M1", "Q6", "M3", "Q5"])
        first = assessment.problems[0]
        self.assertTrue(first.core)
        self.assertEqual(first.effort, ("Low",))
        self.assertEqual(first.typical_fix, self.criteria["M1"].typical_fix)
        self.assertEqual(assessment.problems[1].effort, ("Medium",))

    def test_core_criteria_below_two_rule_out_the_ready_group(self):
        core = self.assess("S06").core
        self.assertEqual(core.scores, {"Q6": 1, "M1": 1, "M4": 2})
        self.assertEqual(core.below, ("Q6", "M1"))
        self.assertTrue(core.ready_ruled_out)
        self.assertIn('"Ready" is ruled out until Q6 and M1 reach score 2.', core.message)
        self.assertIn("Q1, AI1 and AI2", core.message)
        for label in ("Almost ready", "Not yet"):
            self.assertNotIn(label, core.message)

    def test_unscored_criteria_are_listed_with_what_they_need(self):
        unscored = self.assess("S06").unscored
        self.assertEqual(len(unscored), 14)
        needs = {entry.criterion_id: entry.needs for entry in unscored}
        self.assertEqual({key for key, value in needs.items() if value == "the files"}, set(NEEDS_FILES))
        self.assertEqual({key for key, value in needs.items() if value == "judgement"}, set(NEEDS_JUDGEMENT))
        self.assertTrue(all(entry.question for entry in unscored))

    def test_dataset_without_high_value_marking(self):
        row = self.sample["S02"]
        self.assertEqual(row["m9_marked"], "False")
        assessment = self.assess("S02")
        by_id = {result.criterion_id: result for result in assessment.scored}
        self.assertEqual(by_id["M9"].status, NOT_JUDGED)
        self.assertIsNone(by_id["M9"].score)
        self.assertEqual(by_id["M9"].check_score, 0)
        self.assertFalse(assessment.dataset.high_value_marked)
        self.assertNotIn("M9", [problem.criterion_id for problem in assessment.problems])
        scores_in_the_table = sum(1 for code in CHECK_IDS if code != "M9" and row[f"{code.lower()}_score"] != "")
        self.assertEqual(assessment.scored_count, scores_in_the_table)

    def test_core_criteria_at_two_leave_the_group_to_the_other_three(self):
        row = self.sample["S02"]
        self.assertEqual([int(float(row[key])) for key in ("q6_score", "m1_score", "m4_score")], [2, 2, 2])
        core = self.assess("S02").core
        self.assertFalse(core.ready_ruled_out)
        self.assertIn("Q6, M1 and M4 score 2.", core.message)
        self.assertIn("Q1, AI1 and AI2", core.message)

    def test_record_with_empty_fields(self):
        record = {"id": "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9", "name": "empty-record"}
        outputs = run_metadata_checks(record, self.reference_date)
        assessment = build_assessment(record, self.criteria, outputs, self.source)
        self.assertEqual(assessment.dataset.title, "")
        self.assertEqual(assessment.dataset.publisher, "")
        self.assertEqual(len(assessment.scored), 9)


if __name__ == "__main__":
    unittest.main()
