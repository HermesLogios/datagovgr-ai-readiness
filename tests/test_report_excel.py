"""Checks of the Excel report in plain language.

Usage:
    python -m unittest discover -s tests
"""

import dataclasses
import unittest
from io import BytesIO

from openpyxl import load_workbook

from aiready.report_excel import excel_bytes
from aiready.texts import load_texts
from sample_pages import EXAMPLE, page_model


def workbook_of(model, language: str = "el"):
    return load_workbook(BytesIO(excel_bytes(model, load_texts(language))))


def rows_of(sheet) -> list[tuple]:
    return [tuple(cell.value for cell in row) for row in sheet.iter_rows()]


class ExcelReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = page_model(EXAMPLE)
        cls.workbook = workbook_of(cls.model)

    def test_workbook_has_the_four_sheets(self):
        self.assertEqual(self.workbook.sheetnames, ["Σύνοψη", "Έλεγχοι", "Τι να διορθώσετε", "Λίστα ελέγχου"])
        self.assertEqual(workbook_of(page_model(EXAMPLE, "en"), "en").sheetnames,
                         ["Summary", "Checks", "What to fix", "Checklist"])

    def test_summary_names_the_dataset_and_the_result(self):
        values = dict(row[:2] for row in rows_of(self.workbook["Σύνοψη"]))
        self.assertEqual(values["Σύνολο"], "Τροχαία ατυχήματα")
        self.assertEqual(values["Φορέας"], "Υπουργείο Προστασίας του Πολίτη")
        self.assertEqual(values["Διεύθυνση"], "https://data.gov.gr/dataset/troxaia-atyxhmata")
        self.assertEqual(values["Σύνοψη"], "5 από τους 9 ελέγχους είναι εντάξει. Οι άλλοι 4 πληρούνται εν μέρει.")
        self.assertIn("στιγμιότυπο της 24/10/2026", values["Μεταδεδομένα"])
        self.assertIn("έκδοση 1.2", values["Κριτήρια"])

    def test_checks_sheet_has_one_row_per_check(self):
        rows = rows_of(self.workbook["Έλεγχοι"])
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0][:4], ("Έλεγχος", "Κατάσταση", "Τι βρέθηκε", "Τι να κάνετε"))
        first = dict(zip(rows[0], rows[1]))
        self.assertEqual(first["Έλεγχος"], "Τίτλος και περιγραφή")
        self.assertEqual(first["Κατάσταση"], "Εν μέρει")
        self.assertEqual(first["Τι βρέθηκε"], "Η περιγραφή είναι πολύ σύντομη: 76 χαρακτήρες, ενώ χρειάζονται τουλάχιστον 100.")
        self.assertEqual((first["Κωδικός"], first["Βαθμός (0 έως 2)"], first["Βασικό κριτήριο"]), ("M1", 1, "Ναι"))
        self.assertEqual(first["Αιτιολογία του ελέγχου (αγγλικά)"], "description of 76 characters (minimum 100)")

    def test_fixes_sheet_keeps_the_order_of_the_priorities(self):
        rows = rows_of(self.workbook["Τι να διορθώσετε"])
        self.assertEqual([row[0] for row in rows[1:]], [1, 2, 3, 4])
        self.assertEqual([row[2] for row in rows[1:]], [item.action for item in self.model.fix_first])

    def test_checklist_sheet_has_the_fourteen_questions(self):
        rows = rows_of(self.workbook["Λίστα ελέγχου"])
        self.assertEqual(len(rows), 15)
        self.assertEqual(rows[1][:2], ("Κατεβαίνουν και ανοίγουν όλα τα αρχεία;", "Διορθώστε τον σύνδεσμο ή ανεβάστε ξανά το αρχείο."))

    def test_text_that_looks_like_a_formula_stays_text(self):
        formula = '=HYPERLINK("http://example.org","x")'
        workbook = workbook_of(dataclasses.replace(self.model, title=formula))
        cell = next(row[1] for row in workbook["Σύνοψη"].iter_rows() if row[0].value == "Σύνολο")
        self.assertEqual((cell.value, cell.data_type), (formula, "s"))


if __name__ == "__main__":
    unittest.main()
