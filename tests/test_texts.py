"""Checks of the texts of the two languages and of the errors of a refused dataset address.

Usage:
    python -m unittest discover -s tests
"""

import json
import re
import unittest
from datetime import date

from aiready.identifier import InvalidIdentifier, parse_dataset_identifier
from aiready.texts import LANGUAGES, LOCALES_DIR, load_texts

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def entries(language: str) -> dict[str, str]:
    with open(LOCALES_DIR / f"{language}.json", encoding="utf-8") as handle:
        return json.load(handle)


class LocaleFilesTest(unittest.TestCase):
    def test_both_languages_have_the_same_keys(self):
        self.assertEqual(sorted(entries("el")), sorted(entries("en")))

    def test_every_text_has_content(self):
        for language in LANGUAGES:
            for key, value in entries(language).items():
                self.assertTrue(isinstance(value, str) and value.strip(), f"{language}: {key}")

    def test_placeholders_agree_between_the_languages(self):
        greek, english = entries("el"), entries("en")
        for key in greek:
            self.assertEqual(set(PLACEHOLDER.findall(greek[key])), set(PLACEHOLDER.findall(english[key])), key)

    def test_count_variants_belong_to_an_existing_text(self):
        keys = entries("el")
        for key in keys:
            for suffix in (".one", ".zero"):
                if key.endswith(suffix):
                    self.assertIn(key[: -len(suffix)], keys, key)


class TextsTest(unittest.TestCase):
    def test_counted_text_picks_the_variant_of_the_count(self):
        greek = load_texts("el")
        self.assertEqual(greek.counted("common.days", 201, n=201), "201 ημέρες")
        self.assertEqual(greek.counted("common.days", 1, n=1), "1 ημέρα")
        self.assertEqual(greek.counted("common.days", 0, n=0), "λιγότερο από μία ημέρα")
        self.assertEqual(greek.counted("m7.stable", 1), greek.text("m7.stable"))

    def test_numbers_and_dates_follow_the_language(self):
        self.assertEqual(load_texts("el").number(22805), "22.805")
        self.assertEqual(load_texts("en").number(22805), "22,805")
        self.assertEqual(load_texts("el").date(date(2026, 10, 24)), "24/10/2026")
        self.assertEqual(load_texts("en").date(date(2026, 10, 24)), "24 October 2026")

    def test_quotation_marks_follow_the_language(self):
        self.assertEqual(load_texts("el").quoted("xl"), "«xl»")
        self.assertEqual(load_texts("en").quoted("xl"), "“xl”")

    def test_unknown_language_is_refused(self):
        with self.assertRaises(ValueError):
            load_texts("fr")


class InvalidIdentifierTest(unittest.TestCase):
    def test_every_refusal_carries_its_code(self):
        cases = {
            "": "empty",
            "   ": "empty",
            "https://example.org/dataset/x": "other_site",
            "https://data.gov.gr/organization/x": "not_dataset_page",
            "https://data.gov.gr/": "not_dataset_page",
            "Τροχαία ατυχήματα": "not_a_name",
        }
        for text, code in cases.items():
            with self.assertRaises(InvalidIdentifier) as caught:
                parse_dataset_identifier(text)
            self.assertEqual(caught.exception.code, code, text)

    def test_a_refusal_is_still_a_value_error_with_its_explanation(self):
        with self.assertRaises(ValueError) as caught:
            parse_dataset_identifier("https://example.org/dataset/x")
        self.assertEqual(str(caught.exception), "the address is not on data.gov.gr (found 'example.org')")


if __name__ == "__main__":
    unittest.main()
