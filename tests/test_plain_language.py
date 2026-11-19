"""Checks of the plain-language explanation of an assessment, in Greek and English.

Usage:
    python -m unittest discover -s tests
"""

import dataclasses
import re
import unittest
from collections import Counter
from functools import lru_cache
from pathlib import Path

from aiready.assessment import NOT_JUDGED, Source, build_assessment
from aiready.criteria import load_criteria
from aiready.identifier import DatasetIdentifier
from aiready.metadata_checks import run_metadata_checks
from aiready.plain_language import build_page_model, explain_check
from aiready.records import record_type
from aiready.snapshot import find_dataset_record, iter_snapshot_records, snapshot_reference_date
from aiready.texts import LANGUAGES, load_texts

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
CRITERIA = load_criteria()
SOURCE = Source("snapshot", f"snapshot {SNAPSHOT.name}", snapshot_reference_date(SNAPSHOT))
EXAMPLE = "troxaia-atyxhmata"
UNMARKED = "gis-ypen-wfd-wms-kallikratikoi_dimoi"
UNFILLED = re.compile(r"\{[a-z_]+\}")


@lru_cache(maxsize=None)
def assessment_of(name: str):
    record = find_dataset_record(SNAPSHOT, DatasetIdentifier("name", name))
    return build_assessment(record, CRITERIA, run_metadata_checks(record, SOURCE.date), SOURCE)


def page_model(name: str, language: str = "el"):
    return build_page_model(assessment_of(name), load_texts(language), CRITERIA)


class ExampleDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = page_model(EXAMPLE)
        cls.checks = {check.criterion_id: check for check in cls.model.checks}

    def test_checks_follow_the_two_groups_of_the_page(self):
        self.assertEqual([check.criterion_id for check in self.model.checks],
                         ["M1", "M2", "M3", "M9", "Q5", "M4", "M6", "M7", "Q6"])
        self.assertEqual([check.group for check in self.model.checks], ["description"] * 5 + ["availability"] * 4)

    def test_findings_are_the_approved_sentences(self):
        expected = {
            "M1": "Η περιγραφή είναι πολύ σύντομη: 76 χαρακτήρες, ενώ χρειάζονται τουλάχιστον 100.",
            "M2": "Είναι συμπληρωμένα και τα 7: λέξεις-κλειδιά, θέμα, εκδότης, σημείο επαφής, γεωγραφική κάλυψη, "
                  "χρονική κάλυψη, συχνότητα ενημέρωσης.",
            "M3": "Σε 6 από τα 11 αρχεία που δηλώνουν μορφότυπο, αυτός είναι γραμμένος ελεύθερα («xl», «xlx») "
                  "και όχι με όρο του καταλόγου.",
            "M9": "Το σύνολο δηλώνεται ως υψηλής αξίας, στην κατηγορία «Στατιστικά», με αναφορά στον Κανονισμό (ΕΕ) 2023/138.",
            "Q5": "Δηλώνεται ότι δεν προβλέπεται ενημέρωση, αλλά ούτε ο τίτλος ούτε η περιγραφή λένε ποια περίοδο "
                  "καλύπτουν τα δεδομένα. Το τελευταίο ανέβασμα έγινε πριν από 201 ημέρες.",
            "M4": "Όλα τα αρχεία έχουν την ίδια ανοιχτή άδεια, CC BY 4.0.",
            "M6": "Και τα 12 αρχεία κατεβαίνουν με απευθείας σύνδεσμο.",
            "M7": "Το σύνολο έχει μόνιμο αναγνωριστικό, και τα 12 αρχεία του είναι ανεβασμένα στην πύλη, με σταθερή διεύθυνση.",
            "Q6": "Τα δεδομένα δίνονται μόνο σε Excel (12 αρχεία), που είναι μορφότυπος ενός κατασκευαστή.",
        }
        for code, sentence in expected.items():
            self.assertEqual(self.checks[code].finding, sentence, code)

    def test_actions_are_given_only_below_the_full_score(self):
        self.assertEqual(self.checks["M1"].action,
                         "Γράψτε στην περιγραφή τι περιέχουν τα δεδομένα: τι μετρούν, για ποια περίοδο και για ποια περιοχή.")
        self.assertEqual(self.checks["M3"].action,
                         "Στη φόρμα της πύλης διαλέξτε τον μορφότυπο από τη λίστα, αντί να τον πληκτρολογήσετε.")
        self.assertEqual(self.checks["Q5"].action,
                         "Γράψτε στον τίτλο ή στην περιγραφή την περίοδο των δεδομένων. "
                         "Αν το σύνολο ενημερώνεται, δηλώστε την πραγματική συχνότητα.")
        self.assertEqual(self.checks["Q6"].action,
                         "Ανεβάστε τα ίδια δεδομένα και σε ανοιχτό μορφότυπο, π.χ. CSV, δίπλα στο Excel.")
        for code in ("M2", "M4", "M6", "M7", "M9"):
            self.assertEqual(self.checks[code].action, "", code)
            self.assertEqual(self.checks[code].fix_first, "", code)

    def test_labels_and_details_of_a_check(self):
        check = self.checks["M1"]
        self.assertEqual((check.title, check.status_label, check.kind_label, check.core, check.effort_label),
                         ("Τίτλος και περιγραφή", "Εν μέρει", "Πρόταση.", True, "Συνήθως χαμηλή προσπάθεια."))
        self.assertEqual((check.score, check.reason), (1, "description of 76 characters (minimum 100)"))
        self.assertEqual(check.rule, CRITERIA["M1"].score_1)
        self.assertEqual(check.criterion_name, "Mandatory metadata")
        self.assertTrue(check.why.startswith("Ο τίτλος και η περιγραφή"))
        self.assertFalse(check.generic)
        self.assertEqual((self.checks["M2"].kind_label, self.checks["M2"].effort_label), ("Βαθμός από κανόνα.", ""))

    def test_header_and_summary(self):
        model = self.model
        self.assertEqual((model.title, model.publisher), ("Τροχαία ατυχήματα", "Υπουργείο Προστασίας του Πολίτη"))
        self.assertEqual(model.url, "https://data.gov.gr/dataset/troxaia-atyxhmata")
        self.assertEqual(model.source_sentence, "Τα μεταδεδομένα διαβάστηκαν από το στιγμιότυπο της 24/10/2026.")
        self.assertEqual(model.marking_sentence, "Το σύνολο έχει σήμανση υψηλής αξίας, στην κατηγορία «Στατιστικά».")
        self.assertEqual(model.headline, "5 από τους 9 ελέγχους είναι εντάξει. Οι άλλοι 4 πληρούνται εν μέρει.")
        self.assertEqual(model.summary_note, "")
        self.assertEqual(model.strip_label, "9 έλεγχοι: 5 εντάξει, 4 εν μέρει, 0 όχι, 0 χωρίς αποτέλεσμα")
        self.assertIn("Δεν είναι ακόμη εντάξει: τίτλος και περιγραφή, μορφότυπος αρχείων. Ώσπου να διορθωθούν, "
                      "το σύνολο δεν μπορεί να χαρακτηριστεί «Έτοιμο».", model.group_note)
        self.assertTrue(model.group_note.endswith("(διαθεσιμότητα, δομή, τεκμηρίωση) είναι στη λίστα ελέγχου."))

    def test_priorities_follow_the_order_of_the_problems(self):
        self.assertEqual([(item.criterion_id, item.action) for item in self.model.fix_first], [
            ("M1", "Γράψτε πληρέστερη περιγραφή."),
            ("Q6", "Ανεβάστε τα δεδομένα και σε ανοιχτό μορφότυπο, π.χ. CSV."),
            ("M3", "Διαλέξτε τον μορφότυπο των αρχείων από τη λίστα της πύλης."),
            ("Q5", "Γράψτε ποια περίοδο καλύπτουν τα δεδομένα."),
        ])
        notes = [item.note for item in self.model.fix_first]
        self.assertEqual(notes[0], "Βασικό κριτήριο. Συνήθως χαμηλή προσπάθεια: αλλάζουν μόνο τα μεταδεδομένα.")
        self.assertEqual(notes[1], "Βασικό κριτήριο. Συνήθως μεσαία προσπάθεια: χρειάζεται νέο αρχείο ή νέος σύνδεσμος.")
        self.assertEqual(notes[2], "Συνήθως χαμηλή προσπάθεια: αλλάζουν μόνο τα μεταδεδομένα.")

    def test_checklist_has_the_fourteen_unscored_criteria(self):
        files, judgement = self.model.checklist_files, self.model.checklist_judgement
        self.assertEqual([item.criterion_id for item in files], ["Q1", "AI1", "Q2", "Q3", "Q4", "AI6"])
        self.assertEqual([item.criterion_id for item in judgement], ["AI2", "M5", "M8", "M10", "AI3", "AI4", "AI5", "AI7"])
        self.assertEqual((files[0].question, files[0].if_not),
                         ("Κατεβαίνουν και ανοίγουν όλα τα αρχεία;", "Διορθώστε τον σύνδεσμο ή ανεβάστε ξανά το αρχείο."))
        self.assertEqual([item.criterion_id for item in files + judgement if item.core], ["Q1", "AI1", "AI2"])

    def test_english_page_of_the_same_dataset(self):
        model = page_model(EXAMPLE, "en")
        self.assertEqual(model.headline, "5 of the 9 checks are met. The other 4 are partly met.")
        self.assertEqual(model.checks[0].finding, "The description is very short: 76 characters, while at least 100 are needed.")
        self.assertEqual(model.source_sentence, "The metadata were read from the snapshot of 24 October 2026.")
        self.assertEqual(model.checks[2].finding,
                         "In 6 of the 11 files that declare a format, the format is typed freely (“xl”, “xlx”) "
                         "and not with a term of the catalogue.")


class UnmarkedDatasetTest(unittest.TestCase):
    def test_dataset_without_marking_is_not_judged_and_not_counted(self):
        model = page_model(UNMARKED)
        marking = next(check for check in model.checks if check.criterion_id == "M9")
        self.assertEqual((marking.status, marking.status_label, marking.score), (NOT_JUDGED, "Δεν κρίνεται αυτόματα", None))
        self.assertTrue(marking.finding.startswith("Το σύνολο δεν έχει καμία σήμανση υψηλής αξίας."))
        self.assertTrue(marking.action.startswith("Αν τα δεδομένα ανήκουν"))
        self.assertEqual(marking.fix_first, "")
        self.assertEqual(model.headline, "6 από τους 8 ελέγχους είναι εντάξει. Από τους υπόλοιπους: 1 εν μέρει, 1 δεν μετριέται.")
        self.assertEqual(model.summary_note, "Η σήμανση υψηλής αξίας δεν κρίνεται αυτόματα και δεν μετρά εδώ.")
        self.assertEqual(model.strip_label, "9 έλεγχοι: 6 εντάξει, 1 εν μέρει, 0 όχι, 2 χωρίς αποτέλεσμα")
        self.assertEqual(model.marking_sentence, "")
        self.assertEqual([item.criterion_id for item in model.fix_first], ["M2"])
        self.assertIn("Και τα τρία είναι εντάξει.", model.group_note)


class SingleCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scored = {result.criterion_id: result for result in assessment_of(EXAMPLE).scored}
        cls.greek = load_texts("el")

    def test_reason_of_an_unknown_form_gets_the_general_text_of_its_status(self):
        changed = dataclasses.replace(self.scored["M1"], reason="wording that no text covers")
        check = explain_check(changed, self.greek, CRITERIA)
        self.assertTrue(check.generic)
        self.assertEqual(check.finding, "Ο έλεγχος πληρούται εν μέρει.")
        self.assertEqual(check.fix_first, "Διορθώστε: Τίτλος και περιγραφή.")
        self.assertTrue(check.action)

    def test_one_file_is_described_in_the_singular(self):
        direct = self.scored["M6"]
        one = dataclasses.replace(direct, reason="direct link to a file: 1 file",
                                  measurements={**direct.measurements, "resources": 1, "file": 1})
        self.assertEqual(explain_check(one, self.greek, CRITERIA).finding, "Το αρχείο κατεβαίνει με απευθείας σύνδεσμο.")
        licence = self.scored["M4"]
        one = dataclasses.replace(licence, measurements={**licence.measurements, "resources": 1, "resources_with_licence": 1})
        self.assertEqual(explain_check(one, self.greek, CRITERIA).finding, "Το αρχείο έχει ανοιχτή άδεια, CC BY 4.0.")

    def test_dataset_without_files_is_said_so(self):
        timeliness = self.scored["Q5"]
        empty = dataclasses.replace(timeliness, score=None, status="not measured", reason="no resources: nothing to measure",
                                    measurements={**timeliness.measurements, "frequency_group": "", "age_days": None})
        check = explain_check(empty, self.greek, CRITERIA)
        self.assertEqual(check.finding, "Το σύνολο δεν έχει κανένα αρχείο ή σύνδεσμο.")
        self.assertEqual(check.fix_first, "")


class WholeCatalogueTest(unittest.TestCase):
    def test_every_dataset_gets_a_text_for_every_check_in_both_languages(self):
        texts = [load_texts(language) for language in LANGUAGES]
        datasets = 0
        generic = Counter()
        for record in iter_snapshot_records(SNAPSHOT):
            if record_type(record) != "dataset":
                continue
            datasets += 1
            assessment = build_assessment(record, CRITERIA, run_metadata_checks(record, SOURCE.date), SOURCE)
            for language_texts in texts:
                model = build_page_model(assessment, language_texts, CRITERIA)
                self.assertEqual([item.criterion_id for item in model.fix_first],
                                 [problem.criterion_id for problem in assessment.problems])
                for check in model.checks:
                    if check.generic:
                        generic[(check.criterion_id, check.reason[:50])] += 1
                    self.assertTrue(check.finding, check.criterion_id)
                    if check.score in (0, 1):
                        self.assertTrue(check.action and check.fix_first, (check.criterion_id, check.reason))
                    for text in (check.finding, check.action, check.fix_first):
                        self.assertIsNone(UNFILLED.search(text), text)
                for text in (model.headline, model.group_note, model.source_sentence, model.strip_label):
                    self.assertTrue(text)
                    self.assertIsNone(UNFILLED.search(text), text)
        self.assertEqual(datasets, 22805)
        self.assertEqual(sum(generic.values()), 0, generic.most_common(8))


if __name__ == "__main__":
    unittest.main()
