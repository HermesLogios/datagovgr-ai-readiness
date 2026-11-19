"""Checks of the texts of the criteria in the two languages against criteria/criteria.csv.

Usage:
    python -m unittest discover -s tests
"""

import re
import unittest

from aiready.criteria import load_criteria
from aiready.metadata_checks import CHECK_IDS, checks_script
from aiready.plain_language import CHECKLIST_FILES, CHECKLIST_JUDGEMENT, criterion_title, level_key
from aiready.texts import LANGUAGES, load_texts

CRITERIA = load_criteria()
RULE_FIELDS = ("question", "score_2", "score_1", "score_0", "not_applicable")
DIGITS = re.compile(r"\d+")
ACRONYM = re.compile(r"\b[A-Z][A-Za-z]*[A-Z][A-Za-z0-9]*\b")
# Acronyms of the criteria file that the Greek texts write in Greek, with what stands in their place.
WRITTEN_IN_GREEK = {"URL": "διεύθυνση", "KAD": "ΚΑΔ", "GEMI": "ΓΕΜΗ", "KAEK": "ΚΑΕΚ", "AI": "ΤΝ"}
OWN_FAMILIES = ("criterion.", "criteria.", "opinion.how.", "opinion.key.")
PERIOD_WORDS = {"el": {2: "δύο", 4: "τέσσερις"}, "en": {2: "two", 4: "four"}}


def rule_texts():
    """Every rule text of the criteria file: the code of its criterion, its field and the text."""
    for code, criterion in CRITERIA.items():
        for field in RULE_FIELDS:
            if getattr(criterion, field):
                yield code, field, getattr(criterion, field)


class RuleTextsTest(unittest.TestCase):
    def test_every_rule_of_the_criteria_file_is_written_in_both_languages(self):
        for language in LANGUAGES:
            texts = load_texts(language)
            for code, field, _ in rule_texts():
                self.assertTrue(texts.has(f"criterion.{code}.{field}"), f"{language}: {code} {field}")

    def test_no_language_has_a_rule_that_the_criteria_file_does_not_have(self):
        expected = {f"criterion.{code}.{field}" for code, field, _ in rule_texts()}
        expected |= {f"criterion.{code}.how" for code in CHECK_IDS}
        for language in LANGUAGES:
            found = {key for key in load_texts(language).entries if key.startswith("criterion.")}
            self.assertEqual(found, expected, language)

    def test_english_rules_are_the_texts_of_the_criteria_file(self):
        english = load_texts("en")
        for code, field, text in rule_texts():
            self.assertEqual(english.text(f"criterion.{code}.{field}"), text, f"{code} {field}")

    def test_greek_rules_carry_the_numbers_of_the_criteria_file(self):
        greek = load_texts("el")
        for code, field, text in rule_texts():
            self.assertEqual(sorted(DIGITS.findall(greek.text(f"criterion.{code}.{field}"))), sorted(DIGITS.findall(text)),
                             f"{code} {field}")

    def test_greek_rules_keep_the_formats_and_the_standards_that_the_criteria_file_names(self):
        greek = load_texts("el")
        for code, field, text in rule_texts():
            translated = greek.text(f"criterion.{code}.{field}")
            for acronym in ACRONYM.findall(text):
                self.assertIn(WRITTEN_IN_GREEK.get(acronym, acronym), translated, f"{code} {field}")

    def test_no_rule_has_a_field_to_fill(self):
        for language in LANGUAGES:
            texts = load_texts(language)
            for key, value in texts.entries.items():
                if key.startswith("criterion."):
                    self.assertNotIn("{", value, f"{language}: {key}")


class NamesTest(unittest.TestCase):
    def test_every_criterion_has_its_own_name_in_the_application(self):
        for language in LANGUAGES:
            texts = load_texts(language)
            names = [criterion_title(code, texts) for code in CRITERIA]
            self.assertTrue(all(names), language)
            self.assertEqual(len(set(names)), len(CRITERIA), language)

    def test_checks_and_checklist_together_are_the_criteria_of_the_file(self):
        self.assertEqual(sorted(CHECK_IDS + CHECKLIST_FILES + CHECKLIST_JUDGEMENT), sorted(CRITERIA))

    def test_approved_greek_names_of_the_checklist(self):
        greek = load_texts("el")
        approved = {
            "Q1": "Διαθεσιμότητα αρχείων", "Q2": "Πληρότητα", "Q3": "Συνέπεια", "Q4": "Αληθοφάνεια τιμών",
            "M5": "Δωρεάν πρόσβαση", "M8": "Προσωπικά δεδομένα", "M10": "API και μαζική λήψη",
            "AI1": "Δομή που διαβάζεται από πρόγραμμα", "AI2": "Τεκμηρίωση της δομής", "AI3": "Ιστορικό βάθος",
            "AI4": "Περιγραφή σε Croissant ή δελτίο δεδομένων", "AI5": "Καταλληλότητα για ανάκτηση (RAG)",
            "AI6": "Σύνδεση με κοινούς κωδικούς", "AI7": "Δηλωμένοι περιορισμοί",
        }
        self.assertEqual({code: criterion_title(code, greek) for code in CHECKLIST_FILES + CHECKLIST_JUDGEMENT}, approved)

    def test_levels_are_named_as_in_the_criteria_file(self):
        english = load_texts("en")
        for code, criterion in CRITERIA.items():
            self.assertEqual(english.text(f"criteria.level.{level_key(code)}"), criterion.level, code)
        self.assertEqual([level_key(code) for code in ("Q1", "M10", "AI7")], ["Q", "M", "AI"])


class OwnTextsTest(unittest.TestCase):
    def test_texts_of_the_two_languages_carry_the_same_numbers(self):
        greek, english = load_texts("el"), load_texts("en")
        for key, value in greek.entries.items():
            if key.startswith(OWN_FAMILIES):
                self.assertEqual(sorted(DIGITS.findall(value)), sorted(DIGITS.findall(english.entries[key])), key)

    def test_timeliness_text_states_the_limits_that_the_check_applies(self):
        script = checks_script()
        for language in LANGUAGES:
            text = load_texts(language).text("criterion.Q5.how")
            self.assertIn(PERIOD_WORDS[language][script.Q5_WITHIN_PERIODS], text, language)
            self.assertIn(PERIOD_WORDS[language][script.Q5_LATE_PERIODS], text, language)
            self.assertIn(f"{round(script.Q5_NO_PERIOD_DAYS * 12 / 365)} ", text, language)

    def test_texts_name_a_status_with_the_word_of_the_result(self):
        for language in LANGUAGES:
            texts = load_texts(language)
            self.assertIn(texts.quoted(texts.text("status.not_judged")), texts.text("criterion.M9.how"), language)
            self.assertIn(texts.quoted(texts.text("status.not_measured")), texts.text("criterion.Q5.how"), language)


if __name__ == "__main__":
    unittest.main()
