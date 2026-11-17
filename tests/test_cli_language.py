"""Checks of the options of the command for the language and the Excel report.

Usage:
    python -m unittest discover -s tests
"""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from openpyxl import load_workbook

from aiready.cli import main
from sample_pages import EXAMPLE, SNAPSHOT


def run_command(*arguments: str) -> tuple[int, str, str]:
    output, errors = io.StringIO(), io.StringIO()
    with redirect_stdout(output), redirect_stderr(errors):
        code = main([EXAMPLE, "--snapshot", str(SNAPSHOT), *arguments])
    return code, output.getvalue(), errors.getvalue()


class LanguageOptionTest(unittest.TestCase):
    def test_greek_summary_is_in_plain_language(self):
        code, output, errors = run_command("--lang", "el")
        self.assertEqual((code, errors), (0, ""))
        self.assertIn("Τροχαία ατυχήματα", output)
        self.assertIn("5 από τους 9 ελέγχους είναι εντάξει. Οι άλλοι 4 πληρούνται εν μέρει.", output)
        self.assertIn("  1. Γράψτε πληρέστερη περιγραφή. Βασικό κριτήριο.", output)
        self.assertIn("[Εν μέρει] Τίτλος και περιγραφή: Η περιγραφή είναι πολύ σύντομη: 76 χαρακτήρες", output)
        self.assertIn("Κατεβαίνουν και ανοίγουν όλα τα αρχεία;", output)
        self.assertNotIn("Scored from the metadata", output)

    def test_english_summary_in_plain_language(self):
        code, output, _ = run_command("--lang", "en")
        self.assertEqual(code, 0)
        self.assertIn("5 of the 9 checks are met. The other 4 are partly met.", output)

    def test_without_the_option_the_summary_stays_technical(self):
        code, output, _ = run_command()
        self.assertEqual(code, 0)
        self.assertIn("Scored from the metadata: 9 of 9 criteria (5 met, 4 partly met)", output)

    def test_excel_report_is_written_in_the_language_asked(self):
        with tempfile.TemporaryDirectory() as folder:
            code, output, _ = run_command("--out", folder, "--format", "xlsx", "--lang", "el")
            written = sorted(path.name for path in Path(folder).iterdir())
            self.assertEqual((code, written), (0, ["troxaia-atyxhmata_2026-10-24.xlsx"]))
            self.assertEqual(load_workbook(Path(folder) / written[0]).sheetnames[0], "Σύνοψη")
            self.assertIn("Report written:", output)

    def test_excel_report_is_english_when_no_language_is_asked(self):
        with tempfile.TemporaryDirectory() as folder:
            code, _, _ = run_command("--out", folder, "--format", "xlsx", "md")
            written = sorted(path.name for path in Path(folder).iterdir())
            self.assertEqual((code, written), (0, ["troxaia-atyxhmata_2026-10-24.md", "troxaia-atyxhmata_2026-10-24.xlsx"]))
            self.assertEqual(load_workbook(Path(folder) / written[1]).sheetnames[0], "Summary")


if __name__ == "__main__":
    unittest.main()
