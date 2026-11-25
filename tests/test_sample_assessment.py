"""Tests of the rules of scripts/13_assessment.py: the effort that a criterion names, the score per level, the
readiness group and the choice of the score of a dataset in a criterion."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_assessment():
    spec = importlib.util.spec_from_file_location("sample_assessment", ROOT / "scripts" / "13_assessment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ASSESSMENT = load_assessment()


def criterion(code: str, level: str, core: str, applies_to: str, typical_fix: str, rules: str) -> dict:
    return {"id": code, "level": level, "name": code, "core": core, "applies_to": applies_to, "typical_fix": typical_fix,
            "how_to_check": f"Short statement of the rules. Rules in full: DECISIONS.md {rules}."}


CRITERIA = [
    criterion("Q1", "Quality", "yes", "all", "Low: correct the link. Medium: restore or upload the file again.", "#37 and #51"),
    criterion("Q5", "Quality", "no", "all", "Low: declare the actual frequency. High: set up regular updates.", "#36"),
    criterion("M4", "Metadata and legal status", "yes", "all", "Low: declare the licence in the metadata.", "#31"),
    criterion("M9", "Metadata and legal status", "no", "high-value", "Low: complete the metadata.", "#28 and #32"),
]
SAMPLE = [
    {"sample_id": "S01", "name": "first", "group": "high-value", "title": "First", "organization_title": "Body",
     "url": "https://example.org/first"},
    {"sample_id": "S02", "name": "second", "group": "comparison", "title": "Second", "organization_title": "Body",
     "url": "https://example.org/second"},
]
CHECKS = {"first": {"q5_score": "1.0", "m4_score": "0.0", "m9_score": "2.0"},
          "second": {"q5_score": "", "m4_score": "2.0", "m9_score": "0.0"}}
REVIEWED = {("S01", "Q1"): {"score": "1", "decision": "#37"}, ("S02", "Q1"): {"score": "2", "decision": "#37"},
            ("S01", "Q5"): {"score": "1", "decision": "#63"}, ("S02", "Q5"): {"score": "not measurable", "decision": "#63"}}
EFFORTS = {("S01", "Q1"): {"effort": "low", "decision": "#57"}, ("S01", "Q5"): {"effort": "low", "decision": "#63"}}


class UsualEffort(unittest.TestCase):
    def test_one_level_named(self):
        self.assertEqual(ASSESSMENT.usual_efforts("Low: complete the metadata."), ["low"])

    def test_two_levels_named(self):
        self.assertEqual(ASSESSMENT.usual_efforts("Low: correct the link. Medium: restore or upload the file again."),
                         ["low", "medium"])
        self.assertEqual(ASSESSMENT.usual_efforts("Medium: publish a complete download. High: build an API."),
                         ["medium", "high"])


class ScorePerLevel(unittest.TestCase):
    def test_sum_over_the_maximum(self):
        self.assertEqual(ASSESSMENT.level_percent([2, 2, 2, 2, 2, 1, 1]), 85.7)
        self.assertEqual(ASSESSMENT.level_percent([2, 2]), 100.0)

    def test_half_is_rounded_up(self):
        self.assertEqual(ASSESSMENT.level_percent([1, 2, 2, 2, 2, 2, 2, 2]), 93.8)
        self.assertEqual(ASSESSMENT.level_percent([1, 1, 2, 2, 1, 2, 2, 2]), 81.3)

    def test_no_score(self):
        self.assertIsNone(ASSESSMENT.level_percent([]))


class ReadinessGroup(unittest.TestCase):
    def test_all_core_criteria_at_two(self):
        self.assertEqual(ASSESSMENT.readiness_group({}), "Ready")

    def test_only_low_effort(self):
        self.assertEqual(ASSESSMENT.readiness_group({"M4": "low", "AI2": "low"}), "Almost ready")

    def test_medium_or_high_effort(self):
        self.assertEqual(ASSESSMENT.readiness_group({"M4": "low", "Q6": "medium"}), "Not yet")
        self.assertEqual(ASSESSMENT.readiness_group({"Q1": "high"}), "Not yet")


class ScoreOfADataset(unittest.TestCase):
    def setUp(self):
        records = ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, REVIEWED, EFFORTS)
        self.records = {(record["sample_id"], record["criterion"]): record for record in records}
        self.rows = {row["sample_id"]: row for row in ASSESSMENT.dataset_rows(CRITERIA, SAMPLE, records)}

    def test_score_of_the_reviewer_with_its_recorded_effort(self):
        record = self.records[("S01", "Q1")]
        self.assertEqual((record["score"], record["basis"], record["decision"]), (1, "reviewed", "#37"))
        self.assertEqual((record["effort"], record["effort_basis"]), ("low", "recorded (#57)"))

    def test_automated_score_with_the_usual_effort_of_its_criterion(self):
        record = self.records[("S01", "M4")]
        self.assertEqual((record["score"], record["basis"], record["decision"]), (0, "automatic", "#31"))
        self.assertEqual((record["effort"], record["effort_basis"]), ("low", "usual case of the criterion"))

    def test_criterion_outside_the_group_of_the_dataset(self):
        record = self.records[("S02", "M9")]
        self.assertEqual((record["score"], record["basis"]), ("n/a", "not applicable to the group"))

    def test_final_score_of_the_reviewer_replaces_the_automated_one(self):
        record = self.records[("S01", "Q5")]
        self.assertEqual((record["score"], record["basis"], record["decision"], record["provisional"]),
                         (1, "reviewed", "#63", ""))
        self.assertEqual((record["effort"], record["effort_basis"]), ("low", "recorded (#63)"))

    def test_not_measurable_stays_out_of_its_level_without_effort(self):
        record = self.records[("S02", "Q5")]
        self.assertEqual((record["score"], record["basis"], record["effort"], record["effort_basis"]),
                         ("not measurable", "reviewed", "", ""))
        self.assertEqual(self.rows["S02"]["quality_percent"], 100.0)
        self.assertEqual(self.rows["S01"]["quality_percent"], 50.0)

    def test_levels_and_groups(self):
        first, second = self.rows["S01"], self.rows["S02"]
        self.assertEqual((first["metadata_percent"], first["ai_readiness_percent"]), (50.0, None))
        self.assertEqual((first["core_low_effort"], first["core_medium_or_high_effort"]), ("Q1 M4", ""))
        self.assertEqual((first["readiness_group"], second["readiness_group"]), ("Almost ready", "Ready"))
        self.assertEqual(second["metadata_percent"], 100.0)

    def test_run_stops_without_a_score(self):
        with self.assertRaises(SystemExit):
            ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, {("S01", "Q1"): REVIEWED[("S01", "Q1")]}, EFFORTS)

    def test_run_stops_when_the_effort_of_a_core_criterion_is_open(self):
        records = ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, REVIEWED, {})
        with self.assertRaises(SystemExit):
            ASSESSMENT.dataset_rows(CRITERIA, SAMPLE, records)

    def test_run_stops_on_an_effort_for_a_score_that_is_not_below_two(self):
        with self.assertRaises(SystemExit):
            ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, REVIEWED, {**EFFORTS, ("S02", "Q1"): {"effort": "low", "decision": "#57"}})

    def test_run_stops_on_an_effort_for_a_score_that_is_not_measurable(self):
        with self.assertRaises(SystemExit):
            ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, REVIEWED, {**EFFORTS, ("S02", "Q5"): {"effort": "low", "decision": "#63"}})


class ProvisionalCriterion(unittest.TestCase):
    def test_provisional_criterion_has_no_effort_and_stays_out_of_its_level(self):
        reviewed = {key: value for key, value in REVIEWED.items() if key[1] == "Q1"}
        efforts = {("S01", "Q1"): EFFORTS[("S01", "Q1")]}
        with mock.patch.dict(ASSESSMENT.PROVISIONAL, {"Q5": "metadata part of the criterion"}):
            records = ASSESSMENT.assess(CRITERIA, SAMPLE, CHECKS, reviewed, efforts)
        by_key = {(record["sample_id"], record["criterion"]): record for record in records}
        rows = {row["sample_id"]: row for row in ASSESSMENT.dataset_rows(CRITERIA, SAMPLE, records)}
        self.assertTrue(by_key[("S01", "Q5")]["provisional"])
        self.assertEqual(by_key[("S01", "Q5")]["effort"], "")
        self.assertIsNone(by_key[("S02", "Q5")]["score"])
        self.assertEqual(rows["S01"]["quality_percent"], 50.0)
        self.assertEqual(rows["S02"]["quality_percent"], 100.0)

    def test_no_criterion_is_provisional_after_the_final_scores_of_q5(self):
        self.assertEqual(ASSESSMENT.PROVISIONAL, {})


class FilesOfTheStudy(unittest.TestCase):
    def test_metadata_checks_of_the_snapshot_on_which_the_study_rests(self):
        self.assertEqual(ASSESSMENT.base_checks().name, "metadata_checks_2026-10-24.csv")

    def test_the_reviewer_may_record_a_score_as_not_measurable(self):
        self.assertIn("not measurable", ASSESSMENT.REVIEWED_SCORES)


if __name__ == "__main__":
    unittest.main()
