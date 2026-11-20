"""The questions that the second reading asks since version 1.4: three statements on the texts, one on the names
of the columns, and the hint of the category of high-value data."""

import json
import unittest
from datetime import date
from types import SimpleNamespace

from aiready import jev
from aiready.second_reading import build_reading_model
from aiready.texts import load_texts
from web import browser, pages

TABLE = "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a11"
NEW_STATEMENTS = {"frequency": "M2", "personal": "M8", "fields": "AI2", "names": "AI2"}
TRIED = ("contents", "coverage", "gaps", "collection", "errors")
CATEGORIES = {"geospatial", "earth_observation", "meteorological", "statistics", "companies", "mobility", "none"}


def dataset_record(**fields) -> dict:
    record = {
        "name": "troxaia-atyxhmata",
        "title": "Τροχαία ατυχήματα",
        "notes": "Τα τροχαία ατυχήματα ανά δήμο και μήνα.",
        "resources": [{"id": TABLE, "name": "Ατυχήματα 2024", "format": "CSV", "datastore_active": True}],
    }
    record.update(fields)
    return record


def columns_reply(*names: str) -> str:
    return json.dumps({"columns": {TABLE: [{"id": name, "type": "text", "label": "", "notes": ""} for name in names]}})


def model_reply(probabilities: dict | None = None, categories: dict | None = None, names: bool = True) -> dict:
    probabilities = probabilities or {}
    answers = {statement.key: {"type": "noul", "noul": probabilities.get(statement.key, 0.9)}
               for statement in jev.STATEMENTS if names or not statement.needs_columns}
    if categories is not False:
        chances = categories or {"statistics": 0.82, "none": 0.1, "geospatial": 0.08}
        answers[jev.CATEGORY_QUESTION.key] = {"type": "choice", "choice": max(chances, key=chances.get),
                                              "confidence": 0.7, "probabilities": chances}
    return {"model": "jev-1.14.0", "answers": answers, "usage": {"input_tokens": 900}}


class QuestionsTest(unittest.TestCase):
    def setUp(self):
        self.texts = jev.publisher_texts(dataset_record())

    def test_new_statements_are_asked_under_their_criteria_next_to_the_five_of_the_trial(self):
        criteria = {statement.key: statement.criterion for statement in jev.STATEMENTS}
        self.assertEqual({key: criteria[key] for key in NEW_STATEMENTS}, NEW_STATEMENTS)
        self.assertLessEqual(set(TRIED), set(criteria))
        self.assertEqual(jev.TRIED, TRIED)
        self.assertEqual([statement.key for statement in jev.STATEMENTS if statement.needs_columns], ["names"])

    def test_names_of_the_columns_are_sent_and_asked_about_only_when_there_are_columns(self):
        without = jev.request_body(self.texts)
        self.assertNotIn("columns", without["state"])
        self.assertNotIn("names", without["questions"])
        self.assertEqual(len(without["questions"]), 9)
        with_columns = jev.request_body(self.texts, columns=("Δήμος", "Πλήθος"))
        self.assertEqual(with_columns["state"]["columns"], ["Δήμος", "Πλήθος"])
        self.assertIn("names", with_columns["questions"])
        self.assertEqual(len(with_columns["questions"]), 10)

    def test_category_is_a_question_of_choice_on_the_six_categories_and_none(self):
        question = jev.request_body(self.texts)["questions"]["hvd_category"]
        self.assertEqual(question["type"], "choice")
        self.assertEqual(set(question["criteria"]), CATEGORIES)
        self.assertTrue(all(isinstance(text, str) and text for text in question["criteria"].values()))
        self.assertEqual(jev.CATEGORY_QUESTION.criterion, "M9")

    def test_columns_come_from_the_relay_with_their_data_dictionary_once_each(self):
        reply = {"columns": {
            TABLE: [{"id": "Δήμος", "type": "text", "label": "Δήμος", "notes": "Ο δήμος του ατυχήματος"},
                    {"id": "N1", "type": "numeric", "label": "Πλήθος", "notes": ""}],
            "7d1e2a3b-4c5d-4e6f-8a9b-0c1d2e3f4a5b": [{"id": "Δήμος", "type": "text", "label": "Δήμος",
                                                      "notes": "Ο δήμος του ατυχήματος"}],
        }}
        self.assertEqual(jev.column_texts(json.dumps(reply)), ("Δήμος: Ο δήμος του ατυχήματος", "N1 (Πλήθος)"))
        for text in ("", "not json", "[]", '{"columns": []}', '{"error": "request"}'):
            self.assertEqual(jev.column_texts(text), (), text)

    def test_tables_of_the_datastore_are_chosen_up_to_three_without_the_bundle(self):
        resources = [{"id": f"0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a1{number}", "datastore_active": number != 1}
                     for number in range(6)]
        resources.insert(0, {"id": "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a19", "datastore_active": True,
                             jev.BUNDLE_MARK: "abc"})
        chosen = jev.datastore_tables(dataset_record(resources=resources))
        self.assertEqual(chosen, ["0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a10", "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a12",
                                  "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a13"])

    def test_reply_is_read_with_the_category_and_without_the_question_that_was_not_asked(self):
        reading = jev.reading_in_reply(model_reply(names=False))
        self.assertNotIn("names", reading.probabilities)
        self.assertEqual(reading.categories["statistics"], 0.82)
        self.assertEqual(reading.categories["mobility"], 0.0)
        self.assertEqual(jev.reading_in_reply(model_reply(categories=False)).categories, {})
        with self.assertRaises(jev.JevReplyError):
            jev.reading_in_reply(model_reply(categories={"statistics": 1.4}))


class PanelTest(unittest.TestCase):
    def setUp(self):
        self.texts = load_texts("el")

    def model(self, probabilities=None, categories=None, names=True, marked=False):
        reading = jev.reading_in_reply(model_reply(probabilities, categories, names))
        return build_reading_model(reading, self.texts, date(2026, 11, 20), marked=marked)

    def test_rows_of_the_new_statements_stand_under_their_criteria_with_advice_when_not_likely(self):
        rows = {row.key: row for row in self.model({"frequency": 0.1}).rows}
        self.assertEqual({key: rows[key].criterion for key in NEW_STATEMENTS}, NEW_STATEMENTS)
        self.assertEqual(rows["frequency"].advice, self.texts.text("reading.advice.frequency"))
        self.assertEqual(rows["personal"].advice, "")
        self.assertNotIn("names", {row.key for row in self.model(names=False).rows})

    def test_hint_names_a_likely_category_with_its_probability_and_the_missing_marking(self):
        unmarked = self.model()
        statistics = self.texts.text("hvd.Statistics")
        self.assertEqual(unmarked.hint, self.texts.text("reading.hvd.likely", category=statistics, figure="0,82"))
        self.assertEqual(unmarked.hint_detail, self.texts.text("reading.hvd.unmarked"))
        self.assertEqual(self.model(marked=True).hint_detail, "")

    def test_hint_says_when_the_texts_show_no_category_or_none_clearly(self):
        none = self.model(categories={"none": 0.8, "statistics": 0.15, "mobility": 0.05})
        self.assertEqual(none.hint, self.texts.text("reading.hvd.none", figure="0,80"))
        self.assertEqual(none.hint_detail, "")
        unclear = self.model(categories={"statistics": 0.45, "mobility": 0.35, "none": 0.2})
        self.assertEqual(unclear.hint, self.texts.text("reading.hvd.unclear", category=self.texts.text("hvd.Statistics"),
                                                       figure="0,45"))
        self.assertEqual(self.model(categories=False).hint, "")

    def test_panel_shows_the_hint_with_its_limit_and_the_notes_on_new_questions_and_on_columns(self):
        with_columns = pages.reading_result_html(self.model(), self.texts)
        for key in ("reading.hvd.disclaimer", "reading.note.new", "reading.hvd.unmarked"):
            self.assertIn(self.texts.text(key), with_columns, key)
        self.assertNotIn(self.texts.text("reading.note.no_columns"), with_columns)
        without_columns = pages.reading_result_html(self.model(names=False), self.texts)
        self.assertIn(self.texts.text("reading.note.no_columns"), without_columns)

    def test_note_on_new_questions_names_the_criteria_of_every_question_outside_the_trial(self):
        untried = {statement.criterion for statement in jev.STATEMENTS if statement.key not in TRIED}
        untried.add(jev.CATEGORY_QUESTION.criterion)
        for language in ("el", "en"):
            note = load_texts(language).text("reading.note.new")
            for code in untried:
                self.assertIn(code, note, (language, code))


class PageRequestTest(unittest.TestCase):
    def setUp(self):
        browser._last.clear()
        browser._last["record"] = dataset_record()
        browser._last["assessment"] = SimpleNamespace(dataset=SimpleNamespace(high_value_marked=False))

    def tearDown(self):
        browser._last.clear()

    def test_page_asks_the_relay_for_the_tables_of_the_datastore(self):
        self.assertEqual(json.loads(browser.field_request()), [TABLE])

    def test_request_carries_the_columns_that_the_relay_returned(self):
        body = json.loads(browser.reading_request(columns_reply("Δήμος", "Πλήθος")))
        self.assertEqual(body["state"]["columns"], ["Δήμος", "Πλήθος"])
        self.assertIn("names", body["questions"])
        self.assertNotIn("columns", json.loads(browser.reading_request())["state"])

    def test_result_shows_the_missing_marking_only_for_a_dataset_without_it(self):
        shown = json.loads(browser.reading_result(json.dumps(model_reply()), "el", "2026-11-20"))
        self.assertIn(load_texts("el").text("reading.hvd.unmarked"), shown["html"])
        browser._last["assessment"] = SimpleNamespace(dataset=SimpleNamespace(high_value_marked=True))
        shown = json.loads(browser.reading_result(json.dumps(model_reply()), "el", "2026-11-20"))
        self.assertNotIn(load_texts("el").text("reading.hvd.unmarked"), shown["html"])


if __name__ == "__main__":
    unittest.main()
