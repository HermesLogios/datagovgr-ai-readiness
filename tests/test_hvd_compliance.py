"""Tests of the rules of scripts/14_hvd_compliance.py: the answer that a score gives, the rows of the table and the
counts over the datasets whose content is in the Annex of the Regulation."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_compliance():
    spec = importlib.util.spec_from_file_location("hvd_compliance", ROOT / "scripts" / "14_hvd_compliance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPLIANCE = load_compliance()
SAMPLE = [
    {"sample_id": "S01", "group": "high-value", "title": "First", "organization_title": "Body", "url": "https://example.org/1"},
    {"sample_id": "S02", "group": "high-value", "title": "Second", "organization_title": "Body", "url": "https://example.org/2"},
    {"sample_id": "S25", "group": "comparison", "title": "Third", "organization_title": "Body", "url": "https://example.org/3"},
]
ASSESSMENT = {"S01": {"M5": "2", "M4": "0", "M9": "2", "AI2": "1"}, "S02": {"M5": "2", "M4": "2", "M9": "2", "AI2": "2"}}
METADATA = {
    "S01": {"m9_categories": "Geospatial", "m2_contact": "False", "m4_licences": "", "m9_reason": "category declared"},
    "S02": {"m9_categories": "Statistics", "m2_contact": "True", "m4_licences": "CC_BY_4_0", "m9_reason": "category declared"},
}
API = {
    "S01": {"hvd_api": "no", "hvd_bulk_download": "yes", "hvd_api_terms_and_documentation": "-", "api_kinds": "",
            "api_works": "no", "api_complete": "", "bulk_evidence": "1 file behind direct links"},
    "S02": {"hvd_api": "partly", "hvd_bulk_download": "yes", "hvd_api_terms_and_documentation": "yes",
            "api_kinds": "DataStore of the portal", "api_works": "yes", "api_complete": "no",
            "bulk_evidence": "1 file behind direct links"},
}
DOCUMENTATION = {"S01": {"hvd_documentation_required": "not asked by the Annex"}, "S02": {"hvd_documentation_required": "yes"}}
MARKING = {
    "S01": {"in_annex": "yes", "annex_point": "1.1 Cadastral parcels", "category_by_content": "Geospatial",
            "marking": "correct", "reason": "Parcels."},
    "S02": {"in_annex": "no", "annex_point": "", "category_by_content": "", "marking": "", "reason": "Not listed."},
}


class AnswerOfAScore(unittest.TestCase):
    def test_scores_of_the_scale(self):
        self.assertEqual([COMPLIANCE.answer_of_score(score) for score in ("2", "1.0", "0", "n/a")],
                         ["yes", "partly", "no", "not applicable"])

    def test_run_stops_without_a_score(self):
        with self.assertRaises(SystemExit):
            COMPLIANCE.answer_of_score("")


class RowsOfTheTable(unittest.TestCase):
    def setUp(self):
        rows = COMPLIANCE.sample_rows(SAMPLE, ASSESSMENT, METADATA, API, DOCUMENTATION, MARKING)
        self.rows = {row["sample_id"]: row for row in rows}

    def test_only_the_high_value_group_is_listed(self):
        self.assertEqual(sorted(self.rows), ["S01", "S02"])

    def test_answers_of_a_dataset_without_an_api(self):
        row = self.rows["S01"]
        self.assertEqual((row["free_of_charge"], row["open_licence"], row["api"], row["bulk_download"]),
                         ("yes", "no", "no", "yes"))
        self.assertEqual((row["api_terms_and_documentation"], row["point_of_contact"], row["marked_as_high_value"]),
                         ("not applicable", "no", "yes"))
        self.assertEqual((row["documentation_of_structure"], row["licence_evidence"], row["api_evidence"]),
                         ("not asked by the Annex", "no licence", "no API"))

    def test_answers_of_a_dataset_with_an_incomplete_api(self):
        row = self.rows["S02"]
        self.assertEqual((row["api"], row["api_terms_and_documentation"], row["documentation_of_structure"]),
                         ("partly", "yes", "yes"))
        self.assertEqual(row["api_evidence"], "DataStore of the portal: works, does not serve the complete dataset")

    def test_documentation_is_asked_by_the_category_of_the_content(self):
        judged = {**MARKING, "S01": {**MARKING["S01"], "category_by_content": "Earth observation and environment",
                                    "marking": "other category"}}
        rows = COMPLIANCE.sample_rows(SAMPLE, ASSESSMENT, METADATA, API, DOCUMENTATION, judged)
        self.assertEqual(rows[0]["documentation_of_structure"], "partly")

    def test_counts_cover_only_the_datasets_in_the_annex(self):
        tally = COMPLIANCE.counts(list(self.rows.values()))
        self.assertEqual(dict(tally["open_licence"]), {"no": 1})
        self.assertEqual(dict(tally["free_of_charge"]), {"yes": 1})

    def test_run_stops_without_a_judgement_on_the_marking(self):
        with self.assertRaises(SystemExit):
            COMPLIANCE.sample_rows(SAMPLE, ASSESSMENT, METADATA, API, DOCUMENTATION, {"S01": MARKING["S01"]})

    def test_run_stops_when_the_judgement_contradicts_the_marking_score(self):
        judged = {**MARKING, "S01": {**MARKING["S01"], "marking": "not marked"}}
        with self.assertRaises(SystemExit):
            COMPLIANCE.sample_rows(SAMPLE, ASSESSMENT, METADATA, API, DOCUMENTATION, judged)


class JudgementFile(unittest.TestCase):
    def load(self, line: str):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "hvd_marking.csv"
            path.write_text("sample_id,in_annex,annex_point,category_by_content,marking,reason\n" + line + "\n",
                            encoding="utf-8")
            return COMPLIANCE.load_marking(path)

    def test_row_of_a_dataset_in_the_annex(self):
        self.assertEqual(self.load("S01,yes,1.1 Cadastral parcels,Geospatial,correct,Parcels.")["S01"]["marking"], "correct")

    def test_unknown_value_stops_the_run(self):
        with self.assertRaises(SystemExit):
            self.load("S01,perhaps,,,,Reason.")

    def test_category_is_judged_only_inside_the_annex(self):
        with self.assertRaises(SystemExit):
            self.load("S01,no,,,correct,Reason.")


if __name__ == "__main__":
    unittest.main()
