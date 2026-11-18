"""Tests of the texts and statements sent to Jev and of the reading of its reply."""

import csv
import json
import re
import unittest
from pathlib import Path

from aiready import jev
from aiready.snapshot import iter_snapshot_records

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
LIMITATION_TABLE = ROOT / "data" / "processed" / "limitation_checks_2026-10-24.csv"
STATEMENT_KEYS = ("contents", "coverage", "gaps", "collection", "errors")


def dataset_record(**fields) -> dict:
    record = {
        "name": "staseis-leoforeion",
        "title": "Στάσεις λεωφορείων",
        "notes": "Οι στάσεις των αστικών λεωφορείων του δήμου, με τις συντεταγμένες τους.",
        "resources": [],
    }
    record.update(fields)
    return record


def reply_with(probabilities: dict, **fields) -> dict:
    reply = {
        "model": "jev-1.14.0",
        "answers": {key: {"type": "noul", "noul": value} for key, value in probabilities.items()},
        "usage": {"input_tokens": 812, "output_tokens": 5},
    }
    reply.update(fields)
    return reply


class PublisherTextsTest(unittest.TestCase):
    def test_texts_of_the_sample_are_those_read_by_the_study(self):
        with open(LIMITATION_TABLE, encoding="utf-8-sig", newline="") as handle:
            published = {row["dataset"]: row for row in csv.DictReader(handle)}
        compared = 0
        for record in iter_snapshot_records(SNAPSHOT):
            row = published.get(record.get("name"))
            if row is None:
                continue
            compared += 1
            texts = jev.publisher_texts(record)
            cell = row["resource_description_texts"]
            expected = re.split(r"(?:^| \| )\[[^\]]+\] ", cell)[1:] if cell else []
            self.assertEqual(texts.description, row["description"], row["sample_id"])
            self.assertEqual(list(texts.resource_descriptions), expected, row["sample_id"])
            self.assertFalse(texts.shortened, row["sample_id"])
        self.assertEqual(compared, 36)

    def test_tags_and_repeated_spaces_are_removed(self):
        record = dataset_record(title="  Στάσεις   λεωφορείων ", notes="<p>Οι στάσεις &amp; οι γραμμές.</p>\n<p>Ανά δήμο.</p>")
        texts = jev.publisher_texts(record)
        self.assertEqual(texts.title, "Στάσεις λεωφορείων")
        self.assertEqual(texts.description, "Οι στάσεις & οι γραμμές. Ανά δήμο.")

    def test_resource_descriptions_that_say_no_more_than_a_name_are_left_out(self):
        record = dataset_record(resources=[
            {"name": "Στάσεις 2025", "description": "Στάσεις 2025"},
            {"name": "Γραμμές", "description": "ΣΤΑΣΕΙΣ ΛΕΩΦΟΡΕΙΩΝ."},
            {"name": "Αρχείο", "description": "Οι στάσεις μετρήθηκαν με δέκτη GPS το 2024."},
            {"name": "Αντίγραφο", "description": "Οι στάσεις μετρήθηκαν με δέκτη GPS το 2024."},
            {"name": "Όλα τα αρχεία", "description": "Αυτόματο πακέτο.", "downloadall_datapackage_hash": "4f1c"},
            {"name": "Κενό", "description": ""},
        ])
        self.assertEqual(jev.publisher_texts(record).resource_descriptions,
                         ("Οι στάσεις μετρήθηκαν με δέκτη GPS το 2024.",))

    def test_descriptions_written_by_the_harvester_of_a_map_layer_are_left_out(self):
        record = dataset_record(
            extras=[{"key": "wms_layer_name", "value": "Syros:Stops"}],
            resources=[
                {"name": "WMS", "description": "Προεπισκόπηση του επιπέδου syros:stops"},
                {"name": "Υπόμνημα", "description": "Το υπόμνημα εξηγεί τα σύμβολα του χάρτη."},
            ],
        )
        self.assertEqual(jev.publisher_texts(record).resource_descriptions,
                         ("Το υπόμνημα εξηγεί τα σύμβολα του χάρτη.",))

    def test_long_texts_are_cut_and_marked(self):
        record = dataset_record(
            notes="α" * (jev.MAX_DESCRIPTION_CHARACTERS + 500),
            resources=[{"name": "Μεγάλο αρχείο", "description": "β" * (jev.MAX_RESOURCE_DESCRIPTION_CHARACTERS + 40)}]
            + [{"name": f"Αρχείο {number}", "description": f"Περιγραφή του αρχείου με αριθμό {number}."}
               for number in range(jev.MAX_RESOURCE_DESCRIPTIONS + 15)],
        )
        texts = jev.publisher_texts(record)
        self.assertEqual(len(texts.description), jev.MAX_DESCRIPTION_CHARACTERS)
        self.assertEqual(len(texts.resource_descriptions), jev.MAX_RESOURCE_DESCRIPTIONS)
        self.assertEqual(len(texts.resource_descriptions[0]), jev.MAX_RESOURCE_DESCRIPTION_CHARACTERS)
        self.assertTrue(texts.shortened)

    def test_texts_within_the_limits_are_not_marked(self):
        record = dataset_record(resources=[{"name": "Αρχείο", "description": "Οι στάσεις ανά γραμμή."}])
        self.assertFalse(jev.publisher_texts(record).shortened)

    def test_record_without_description_or_resources(self):
        texts = jev.publisher_texts({"name": "keno", "title": "Κενό σύνολο", "notes": None, "resources": None})
        self.assertEqual((texts.description, texts.resource_descriptions, texts.shortened), ("", (), False))


class RequestTest(unittest.TestCase):
    def test_request_states_five_statements_about_the_texts(self):
        body = jev.request_body(jev.publisher_texts(dataset_record()))
        self.assertEqual(set(body), {"model", "state", "questions"})
        self.assertEqual(body["model"], "jev-1.14.0")
        self.assertEqual(set(body["state"]), {"title", "description", "resource_descriptions"})
        self.assertEqual(tuple(body["questions"]), STATEMENT_KEYS)
        for question in body["questions"].values():
            self.assertEqual(question["type"], "noul")
            self.assertEqual(set(question["criteria"]), {"true", "false"})
            self.assertTrue(question["instructions"])

    def test_statements_follow_the_criteria_of_the_study(self):
        criteria = {statement.key: statement.criterion for statement in jev.STATEMENTS}
        self.assertEqual(criteria, {"contents": "M1", "coverage": "AI7", "gaps": "AI7", "collection": "AI7", "errors": "AI7"})

    def test_fields_about_persons_and_other_metadata_are_not_sent(self):
        record = dataset_record(
            author="Μαρία Παπαδοπούλου", author_email="maria@example.gr", maintainer="Γιώργος Νικολάου",
            maintainer_email="giorgos@example.gr", contact=[{"name": "Ελένη Δήμου", "email": "eleni@example.gr"}],
            tags=[{"name": "συγκοινωνίες"}], organization={"title": "Δήμος Παραδείγματος"},
            resources=[{"name": "Αρχείο", "description": "Οι στάσεις ανά γραμμή.", "url": "https://example.gr/staseis.csv"}],
        )
        sent = json.dumps(jev.request_body(jev.publisher_texts(record)), ensure_ascii=False)
        for value in ("Παπαδοπούλου", "example.gr", "Νικολάου", "Δήμου", "συγκοινωνίες", "Δήμος Παραδείγματος"):
            self.assertNotIn(value, sent)
        self.assertIn("Οι στάσεις ανά γραμμή.", sent)


class ReadingTest(unittest.TestCase):
    def test_reading_of_a_reply(self):
        probabilities = {"contents": 0.94, "coverage": 0.81, "gaps": 0.03, "collection": 0.55, "errors": 0}
        reading = jev.reading_in_reply(reply_with(probabilities))
        self.assertEqual(reading.model, "jev-1.14.0")
        self.assertEqual(reading.probabilities, probabilities)
        self.assertEqual(reading.input_tokens, 812)

    def test_reply_without_one_of_the_answers_is_refused(self):
        with self.assertRaisesRegex(jev.JevReplyError, "errors"):
            jev.reading_in_reply(reply_with({"contents": 0.9, "coverage": 0.8, "gaps": 0.1, "collection": 0.5}))

    def test_reply_with_another_kind_of_answer_is_refused(self):
        reply = reply_with({key: 0.5 for key in STATEMENT_KEYS})
        reply["answers"]["gaps"] = {"type": "choice", "choice": "yes"}
        with self.assertRaisesRegex(jev.JevReplyError, "gaps"):
            jev.reading_in_reply(reply)

    def test_probability_outside_zero_to_one_is_refused(self):
        for value in (1.2, -0.1, "0.5", None, True):
            reply = reply_with({key: 0.5 for key in STATEMENT_KEYS})
            reply["answers"]["coverage"]["noul"] = value
            with self.assertRaisesRegex(jev.JevReplyError, "coverage", msg=repr(value)):
                jev.reading_in_reply(reply)

    def test_reply_that_is_not_an_object_is_refused(self):
        for reply in (None, [], "text", {"answers": []}):
            with self.assertRaises(jev.JevReplyError, msg=repr(reply)):
                jev.reading_in_reply(reply)

    def test_bands_of_a_probability(self):
        self.assertEqual([jev.band(value) for value in (0.0, 0.3, 0.31, 0.5, 0.69, 0.7, 1.0)],
                         ["unlikely", "unlikely", "unsure", "unsure", "unsure", "likely", "likely"])


if __name__ == "__main__":
    unittest.main()
