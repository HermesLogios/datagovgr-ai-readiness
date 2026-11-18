"""Checks of the rows that the page shows for a second reading of a description.

Usage:
    python -m unittest discover -s tests
"""

import unittest
from datetime import date

from aiready import jev
from aiready.second_reading import build_reading_model
from aiready.texts import load_texts

PROBABILITIES = {"contents": 0.94, "coverage": 0.41, "gaps": 0.03, "collection": 0.7, "errors": 0.3}
READING = jev.Reading("jev-1.14.0", PROBABILITIES, 812)
DAY = date(2026, 11, 18)


class ReadingModelTest(unittest.TestCase):
    def test_rows_follow_the_statements_with_their_criterion_and_band(self):
        model = build_reading_model(READING, load_texts("el"), DAY)
        self.assertEqual(
            [(row.key, row.criterion, row.band) for row in model.rows],
            [("contents", "M1", "likely"), ("coverage", "AI7", "unsure"), ("gaps", "AI7", "unlikely"),
             ("collection", "AI7", "likely"), ("errors", "AI7", "unlikely")],
        )
        self.assertEqual([row.probability for row in model.rows], list(PROBABILITIES.values()))

    def test_words_come_from_the_texts_of_the_language(self):
        greek = build_reading_model(READING, load_texts("el"), DAY)
        english = build_reading_model(READING, load_texts("en"), DAY)
        self.assertEqual((greek.rows[0].label, greek.rows[0].band_label), ("Λέει τι περιέχουν τα δεδομένα", "Μάλλον ναι"))
        self.assertEqual((english.rows[2].label, english.rows[2].band_label), ("Says what is missing", "Unlikely"))

    def test_probability_is_written_with_the_decimal_mark_of_the_language(self):
        greek = build_reading_model(READING, load_texts("el"), DAY)
        self.assertEqual([row.figure for row in greek.rows], ["0,94", "0,41", "0,03", "0,70", "0,30"])
        self.assertEqual(build_reading_model(READING, load_texts("en"), DAY).rows[0].figure, "0.94")

    def test_advice_is_given_only_for_statements_that_are_not_likely(self):
        texts = load_texts("el")
        model = build_reading_model(READING, texts, DAY)
        self.assertEqual([bool(row.advice) for row in model.rows], [False, True, True, False, True])
        self.assertEqual(model.rows[2].advice, texts.text("reading.advice.gaps"))

    def test_source_names_the_model_that_answered_and_the_day(self):
        self.assertEqual(build_reading_model(READING, load_texts("el"), DAY).source, "Μοντέλο jev-1.14.0, 18/11/2026")
        self.assertEqual(build_reading_model(READING, load_texts("en"), DAY).source, "Model jev-1.14.0, 18 November 2026")

    def test_reply_without_a_model_name_shows_the_model_that_was_asked(self):
        unnamed = jev.Reading("", PROBABILITIES, 0)
        self.assertIn(jev.MODEL, build_reading_model(unnamed, load_texts("el"), DAY).source)


if __name__ == "__main__":
    unittest.main()
