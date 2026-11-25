"""Tests of the rules of scripts/15_gap_analysis.py: the gaps of a criterion, the totals without a provisional
criterion, the gaps of the catalogue, the path of a dataset to the ready group and the gaps of compliance of the
high-value datasets."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_gaps():
    spec = importlib.util.spec_from_file_location("gap_analysis", ROOT / "scripts" / "15_gap_analysis.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GAPS = load_gaps()
CRITERIA = [
    {"id": "Q1", "level": "Quality", "name": "Availability", "core": "yes", "applies_to": "all"},
    {"id": "Q5", "level": "Quality", "name": "Timeliness", "core": "no", "applies_to": "all"},
    {"id": "M4", "level": "Metadata and legal status", "name": "Licence", "core": "yes", "applies_to": "all"},
    {"id": "M10", "level": "Metadata and legal status", "name": "API and bulk download", "core": "no",
     "applies_to": "high-value"},
]
PROVISIONAL = "metadata part of the criterion"


def record(sample_id: str, criterion: str, score: str, effort: str = "", provisional: str = "") -> dict:
    return {"sample_id": sample_id, "criterion": criterion, "score": score, "effort": effort, "provisional": provisional}


RECORDS = [
    record("S01", "Q1", "2"), record("S01", "Q5", "1", provisional=PROVISIONAL), record("S01", "M4", "0", "low"),
    record("S01", "M10", "1", "high"),
    record("S02", "Q1", "0", "medium"), record("S02", "Q5", "", provisional=PROVISIONAL), record("S02", "M4", "2"),
    record("S02", "M10", "2"),
    record("S25", "Q1", "2"), record("S25", "Q5", "2", provisional=PROVISIONAL), record("S25", "M4", "2"),
    record("S25", "M10", "n/a"),
]


def dataset(sample_id: str, group: str) -> dict:
    return {"sample_id": sample_id, "sample_group": "high-value", "title": f"Dataset {sample_id}", "organisation": "Body",
            "address": f"https://example.org/{sample_id}", "quality_percent": "50.0", "metadata_percent": "50.0",
            "ai_readiness_percent": "", "readiness_group": group}


ASSESSMENT = [dataset("S01", "Almost ready"), dataset("S02", "Not yet"), dataset("S25", "Ready")]


class GapsOfACriterion(unittest.TestCase):
    def setUp(self):
        self.rows = {row["criterion"]: row for row in GAPS.criterion_gaps(CRITERIA, RECORDS)}

    def test_counts_the_scores_below_two_and_their_effort(self):
        q1 = self.rows["Q1"]
        self.assertEqual((q1["applicable"], q1["score_2"], q1["score_0"], q1["below_two"]), (3, 2, 1, 1))
        self.assertEqual((q1["effort_low"], q1["effort_medium"], q1["effort_high"]), (0, 1, 0))
        self.assertEqual((q1["share_below_two"], q1["datasets_below_two"]), (33.3, "S02"))

    def test_not_applicable_scores_are_left_out(self):
        m10 = self.rows["M10"]
        self.assertEqual((m10["applicable"], m10["not_applicable"], m10["below_two"], m10["share_below_two"]),
                         (2, 1, 1, 50.0))

    def test_provisional_criterion_is_listed_and_left_out_of_the_totals(self):
        q5 = self.rows["Q5"]
        self.assertEqual((q5["provisional"], q5["not_measured"], q5["below_two"]), ("yes", 1, 1))
        total = GAPS.totals(list(self.rows.values()))
        self.assertEqual((total["applicable"], total["below_two"], total["low"], total["medium"], total["high"]),
                         (8, 3, 1, 1, 1))
        self.assertEqual(total["share_below_two"], 37.5)

    def test_score_below_two_without_an_effort_stops_the_run(self):
        with self.assertRaises(SystemExit):
            GAPS.criterion_gaps(CRITERIA, RECORDS + [record("S03", "M4", "1")])

    def test_missing_score_outside_a_provisional_criterion_stops_the_run(self):
        with self.assertRaises(SystemExit):
            GAPS.criterion_gaps(CRITERIA, RECORDS + [record("S03", "M4", "")])

    def test_share_rounds_half_up(self):
        self.assertEqual((GAPS.share(1, 16), GAPS.share(1, 8), GAPS.share(0, 0)), (6.3, 12.5, None))

    def test_not_measurable_scores_are_counted_apart_and_left_out_of_the_share(self):
        final = [row for row in RECORDS if row["criterion"] != "Q5"] + [
            record("S01", "Q5", "1", "low"), record("S02", "Q5", "not measurable"), record("S25", "Q5", "2")]
        rows = {row["criterion"]: row for row in GAPS.criterion_gaps(CRITERIA, final)}
        q5 = rows["Q5"]
        self.assertEqual((q5["provisional"], q5["applicable"], q5["not_measurable"], q5["below_two"],
                          q5["share_below_two"], q5["effort_low"]), ("", 2, 1, 1, 50.0, 1))
        total = GAPS.totals(list(rows.values()))
        self.assertEqual((total["applicable"], total["below_two"], total["low"]), (10, 4, 2))


class GapsOfTheCatalogue(unittest.TestCase):
    def test_undetermined_scores_apart_and_m9_over_the_marked_datasets(self):
        criteria = [{"id": "Q6", "level": "Quality", "name": "Format", "core": "yes", "applies_to": "all"},
                    {"id": "M9", "level": "Metadata and legal status", "name": "High-value designation", "core": "no",
                     "applies_to": "high-value"}]
        metadata = [{"q6_score": "2.0", "m9_score": "0", "m9_marked": "False"},
                    {"q6_score": "0.0", "m9_score": "1", "m9_marked": "True"},
                    {"q6_score": "", "m9_score": "2", "m9_marked": "True"}]
        rows = {row["criterion"]: row for row in GAPS.catalogue_gaps(criteria, metadata, set())}
        q6, m9 = rows["Q6"], rows["M9"]
        self.assertEqual((q6["datasets"], q6["not_determined"], q6["below_two"], q6["share_below_two"]), (3, 1, 1, 50.0))
        self.assertEqual((m9["datasets"], m9["below_two"], m9["share_below_two"]), (2, 1, 50.0))
        self.assertEqual(m9["counted_over"], "datasets with a high-value marking")

    def test_criteria_that_need_the_files_are_not_counted(self):
        metadata = [{"q1_score": "2", "q5_score": "2.0", "m4_score": "2", "m10_score": "1", "m9_marked": "False"}]
        rows = GAPS.catalogue_gaps(CRITERIA, metadata, {"Q5"})
        self.assertEqual([(row["criterion"], row["provisional"]) for row in rows], [("Q5", "yes"), ("M4", "")])

    def test_timeliness_of_the_catalogue_is_its_metadata_part(self):
        metadata = [{"q5_score": "1.0", "m4_score": "2", "m9_marked": "False"}]
        rows = {row["criterion"]: row for row in GAPS.catalogue_gaps(CRITERIA, metadata, set())}
        self.assertEqual((rows["Q5"]["note"], rows["Q5"]["provisional"], rows["M4"]["note"]), ("metadata part", "", ""))


class PathToTheReadyGroup(unittest.TestCase):
    def setUp(self):
        self.rows = {row["sample_id"]: row for row in GAPS.dataset_gaps(CRITERIA, ASSESSMENT, RECORDS)}

    def test_core_and_other_gaps_by_effort(self):
        self.assertEqual((self.rows["S01"]["core_below_two_low"], self.rows["S01"]["other_below_two_high"]), ("M4", "M10"))
        self.assertEqual(self.rows["S02"]["core_below_two_medium_or_high"], "Q1")
        self.assertEqual(self.rows["S25"]["scores_below_two"], 0)

    def test_provisional_scores_are_not_gaps_of_a_dataset(self):
        self.assertEqual(self.rows["S01"]["scores_below_two"], 2)

    def test_group_that_disagrees_with_the_assessment_stops_the_run(self):
        wrong = [dataset("S01", "Ready")] + ASSESSMENT[1:]
        with self.assertRaises(SystemExit):
            GAPS.dataset_gaps(CRITERIA, wrong, RECORDS)

    def test_datasets_one_core_criterion_away_from_the_ready_group(self):
        one_low, one_heavy, blocking = GAPS.single_steps(list(self.rows.values()), [c["id"] for c in CRITERIA])
        self.assertEqual((one_low, one_heavy, dict(blocking)), ({"M4": ["S01"]}, {"Q1": ["S02"]}, {"Q1": 1}))


class GapsOfCompliance(unittest.TestCase):
    ANSWERED = {"free_of_charge": "yes", "open_licence": "yes", "api": "yes", "bulk_download": "yes",
                "api_terms_and_documentation": "yes", "point_of_contact": "yes", "marked_as_high_value": "yes",
                "documentation_of_structure": "yes"}
    COMPLIANCE = [
        dict(ANSWERED, sample_id="S01", title="Parcels", address="https://example.org/1", in_annex="yes",
             annex_point="1.1 Cadastral parcels", open_licence="no", api="no",
             api_terms_and_documentation="not applicable", point_of_contact="no",
             documentation_of_structure="not asked by the Annex"),
        dict(ANSWERED, sample_id="S05", title="Care units", address="https://example.org/5", in_annex="no",
             annex_point="", api="no"),
        dict(ANSWERED, sample_id="S10", title="Prices", address="https://example.org/10", in_annex="yes",
             annex_point="4.1 Prices", documentation_of_structure="partly"),
    ]

    def test_only_the_datasets_in_the_annex_and_only_no_or_partly(self):
        rows = {row["sample_id"]: row for row in GAPS.hvd_dataset_gaps(self.COMPLIANCE)}
        self.assertEqual(set(rows), {"S01", "S10"})
        self.assertEqual(rows["S01"]["requirements_not_met"], "Open licence; API; Point of contact")
        self.assertEqual((rows["S10"]["requirements_partly_met"], rows["S10"]["gaps"]), ("Documentation of the structure", 1))

    def test_requirements_count_the_datasets_in_the_annex(self):
        rows = {row["column"]: row for row in GAPS.hvd_requirement_gaps(self.COMPLIANCE)}
        self.assertEqual((rows["api"]["datasets"], rows["api"]["no"], rows["api"]["datasets_no"]), (2, 1, "S01"))
        self.assertEqual((rows["documentation_of_structure"]["partly"], rows["free_of_charge"]["no"]), (1, 0))

    def test_unexpected_answer_stops_the_run(self):
        with self.assertRaises(SystemExit):
            GAPS.hvd_dataset_gaps([dict(self.COMPLIANCE[0], api="maybe")])

    def test_catalogue_counts_what_the_metadata_allow_to_check(self):
        catalogue = [{"open_licence": "no", "point_of_contact": "yes", "marking": "partial"},
                     {"open_licence": "yes", "point_of_contact": "yes", "marking": "complete"}]
        rows = {row["requirement"]: row for row in GAPS.hvd_catalogue_gaps(catalogue)}
        self.assertEqual((rows["Open licence"]["lacking"], rows["Open licence"]["share_lacking"]), (1, 50.0))
        self.assertEqual((rows["Point of contact"]["lacking"], rows["Complete marking"]["lacking"]), (0, 1))


class RepositoryTables(unittest.TestCase):
    def test_the_tables_of_the_repository_agree_with_each_other(self):
        assessment_file = GAPS.newest("assessment")
        date = assessment_file.stem.rsplit("_", 1)[1]
        criteria = GAPS.read_table(GAPS.CRITERIA_FILE)
        records = GAPS.read_table(GAPS.PROCESSED_DIR / f"assessment_scores_{date}.csv")
        gaps = GAPS.criterion_gaps(criteria, records)
        datasets = GAPS.dataset_gaps(criteria, GAPS.read_table(assessment_file), records)
        self.assertEqual(len(gaps), len(criteria))
        self.assertEqual(sum(row["scores_below_two"] for row in datasets), GAPS.totals(gaps)["below_two"])


if __name__ == "__main__":
    unittest.main()
