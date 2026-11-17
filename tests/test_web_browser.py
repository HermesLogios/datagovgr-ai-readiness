"""Checks of the entry points that the page calls inside the browser.

Usage:
    python -m unittest discover -s tests
"""

import json
import unittest
from datetime import date
from pathlib import Path

import pandas

from aiready.assessment import Source, build_assessment
from aiready.metadata_checks import run_metadata_checks
from aiready.report import markdown_text
from aiready.texts import load_texts
from fake_portal import found_reply
from sample_pages import CRITERIA, EXAMPLE, page_model, snapshot_record
from web import browser, pages
from web.shims import pandas as csv_tables

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-11-17"


class IdentifierTest(unittest.TestCase):
    def test_address_of_a_dataset_gives_its_name(self):
        answer = json.loads(browser.identify(" https://data.gov.gr/dataset/troxaia-atyxhmata "))
        self.assertEqual(answer, {"ok": True, "kind": "name", "value": "troxaia-atyxhmata"})

    def test_refusal_carries_its_code_and_the_words_for_the_visitor(self):
        for text, code in (("", "empty"), ("https://example.org/dataset/x", "other_site"), ("δύο λέξεις", "not_a_name")):
            with self.subTest(text=text):
                answer = json.loads(browser.identify(text, "el"))
                self.assertEqual((answer["ok"], answer["code"]), (False, code))
                self.assertIn(load_texts("el").text(f"error.{code}"), answer["html"].replace("&quot;", '"'))


class ReplyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = snapshot_record(EXAMPLE)

    def test_reply_with_a_dataset_gives_the_result_of_the_day(self):
        answer = json.loads(browser.assess_reply(found_reply([self.record]), EXAMPLE, "el", TODAY))
        self.assertTrue(answer["ok"])
        self.assertEqual((answer["name"], answer["title"]), (EXAMPLE, "Τροχαία ατυχήματα"))
        self.assertIn("<h1>Τροχαία ατυχήματα</h1>", answer["html"])
        self.assertIn("Τα μεταδεδομένα διαβάστηκαν από την πύλη στις 17/11/2026.", answer["html"])

    def test_empty_search_other_record_types_and_unusable_replies_get_their_code(self):
        service = dict(self.record, type="data-service")
        showcase = dict(self.record, type="showcase")
        cases = ((found_reply([]), "not_found"), (found_reply([service]), "record.data-service"),
                 (found_reply([showcase]), "record.other"), ('{"success": false}', "portal"), ("<html>busy</html>", "portal"))
        for reply, code in cases:
            with self.subTest(code=code, reply=reply[:30]):
                answer = json.loads(browser.assess_reply(reply, EXAMPLE, "el", TODAY))
                self.assertEqual((answer["ok"], answer["code"]), (False, code))
                self.assertIn('role="alert"', answer["html"])

    def test_example_gives_the_page_that_the_build_writes(self):
        answer = json.loads(browser.assess_example(json.dumps(self.record), "en", "2026-10-24"))
        expected = pages.result_html(page_model(EXAMPLE, "en"), load_texts("en"), example=True)
        self.assertEqual(answer["html"], expected)


class ReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = snapshot_record(EXAMPLE)
        browser.assess_reply(found_reply([cls.record]), EXAMPLE, "el", TODAY)

    def test_technical_reports_are_those_of_the_command(self):
        day = date.fromisoformat(TODAY)
        source = Source("portal", f"https://data.gov.gr, read on {TODAY}", day)
        assessment = build_assessment(self.record, CRITERIA, run_metadata_checks(self.record, day), source)
        self.assertEqual(browser.report_text("md"), markdown_text(assessment))
        self.assertEqual(json.loads(browser.report_text("json"))["dataset"]["name"], EXAMPLE)

    def test_files_are_named_after_the_dataset_and_the_day(self):
        self.assertEqual(browser.report_name("xlsx"), "troxaia-atyxhmata_2026-11-17.xlsx")
        self.assertEqual(browser.report_name("md"), "troxaia-atyxhmata_2026-11-17.md")

    def test_excel_report_is_a_workbook(self):
        self.assertEqual(bytes(browser.report_excel())[:2], b"PK")

    def test_unknown_format_is_refused(self):
        with self.assertRaises(ValueError):
            browser.report_text("pdf")


class TableReaderTest(unittest.TestCase):
    def test_reader_gives_the_rows_that_pandas_gives_to_the_checks(self):
        path = ROOT / "data" / "reference" / "eu_file_type.csv"
        options = {"encoding": "utf-8-sig", "dtype": str, "keep_default_na": False}
        expected = pandas.read_csv(path, **options).to_dict("records")
        self.assertEqual(csv_tables.read_csv(path, **options).to_dict("records"), expected)
        self.assertGreater(len(expected), 100)


if __name__ == "__main__":
    unittest.main()
