"""Tests of the trial of Jev on the datasets of the sample, with a stand-in for the address of the model.

Usage:
    python -m unittest discover -s tests
"""

import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

from aiready import jev, jev_trial
from aiready.texts import load_texts
from fake_model import model_stub

ROOT = Path(__file__).resolve().parent.parent
TRIAL_KEY = "trial-key-7c41"
STATEMENT_KEYS = tuple(statement.key for statement in jev.STATEMENTS)


def run_trial(arguments: list[str], environ: dict) -> tuple[int, str]:
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        code = jev_trial.main(arguments, environ=environ)
    return code, printed.getvalue()


class ReferenceTest(unittest.TestCase):
    def test_reference_follows_the_decision_on_the_declared_limitations(self):
        reference = jev_trial.reviewed_statements(jev_trial.REFERENCE_FILE)
        self.assertEqual(sorted(reference), [f"S{number:02d}" for number in range(1, 37)])
        stated = Counter(key for answers in reference.values() for key, value in answers.items()
                         if value in ("yes", "outside"))
        self.assertEqual(stated, {"collection": 13, "coverage": 10, "errors": 6, "gaps": 2})
        answered = {sample_id: sum(value in ("yes", "outside") for value in answers.values())
                    for sample_id, answers in reference.items()}
        self.assertEqual(sorted(sample_id for sample_id, count in answered.items() if count == 3),
                         ["S03", "S11", "S16", "S17"])
        scores = jev_trial.final_ai7_scores((ROOT / "DECISIONS.md").read_text(encoding="utf-8"))
        self.assertEqual(Counter(scores.values()), {2: 1, 1: 14, 0: 21})
        self.assertEqual({sample_id: 2 if count == 4 else 1 if count else 0 for sample_id, count in answered.items()},
                         scores)

    def test_statements_outside_the_metadata_and_contradicted_ones_are_marked(self):
        reference = jev_trial.reviewed_statements(jev_trial.REFERENCE_FILE)
        marked = {(sample_id, key): value for sample_id, answers in reference.items()
                  for key, value in answers.items() if value not in ("yes", "no")}
        self.assertEqual(marked, {("S20", "gaps"): "outside", ("S20", "errors"): "outside",
                                  ("S06", "coverage"): "contradicted", ("S18", "coverage"): "contradicted",
                                  ("S21", "coverage"): "contradicted"})

    def test_contents_expected_by_the_rule_of_the_mandatory_metadata(self):
        expected = jev_trial.contents_by_rule(jev_trial.METADATA_TABLE)
        self.assertEqual(Counter(expected.values()), {"yes": 24, "no": 12})
        self.assertEqual((expected["S12"], expected["S14"], expected["S06"], expected["S04"]), ("yes", "no", "no", "no"))

    def test_expected_answer_of_a_reading_of_the_metadata(self):
        self.assertEqual([jev_trial.expected_answer(value) for value in ("yes", "no", "outside", "contradicted")],
                         [True, False, False, None])


class SummaryTest(unittest.TestCase):
    def test_agreement_is_counted_at_the_threshold(self):
        reference = {"S01": {"coverage": "yes"}, "S02": {"coverage": "no"}, "S03": {"coverage": "yes"},
                     "S04": {"coverage": "outside"}, "S05": {"coverage": "contradicted"}, "S06": {"coverage": "no"}}
        probabilities = {"S01": {"coverage": 0.92}, "S02": {"coverage": 0.61}, "S03": {"coverage": 0.2},
                         "S04": {"coverage": 0.05}, "S05": {"coverage": 0.99}, "S06": {"coverage": 0.5}}
        summary = jev_trial.statement_summary("coverage", probabilities, reference)
        self.assertEqual((summary.compared, summary.agreed), (5, 2))
        self.assertEqual((summary.reference_yes, summary.model_yes), (2, 3))
        self.assertEqual(summary.model_yes_only, ["S02", "S06"])
        self.assertEqual(summary.reference_yes_only, ["S03"])
        self.assertEqual(summary.unsure, ["S02", "S06"])
        self.assertEqual(summary.not_compared, ["S05"])


class SettingsTest(unittest.TestCase):
    def test_key_is_read_from_the_environment_file(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / ".env"
            env_file.write_text('﻿# key of the model\nTYPESAFE_API_KEY = "from-file"\nOTHER=1\n', encoding="utf-8")
            self.assertEqual(jev_trial.model_settings({}, env_file), ("from-file", jev.API_URL))
            self.assertEqual(jev_trial.model_settings({"TYPESAFE_API_KEY": "from-variable"}, env_file)[0], "from-variable")
            env_file.write_text("TYPESAFE_API_KEY=k\nTYPESAFE_API_URL=http://127.0.0.1:9/v1/systemone\n", encoding="utf-8")
            self.assertEqual(jev_trial.model_settings({}, env_file), ("k", "http://127.0.0.1:9/v1/systemone"))

    def test_missing_key_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(jev_trial.MissingKey):
                jev_trial.model_settings({}, Path(folder) / ".env")
            code, printed = run_trial(["--limit", "1", "--out", folder, "--env-file", str(Path(folder) / ".env")], {})
        self.assertEqual(code, 2)
        self.assertIn("TYPESAFE_API_KEY", printed)


class ModelCallTest(unittest.TestCase):
    def setUp(self):
        self.body = jev.request_body(jev.publisher_texts({"title": "Στάσεις", "notes": "Οι στάσεις του δήμου.", "resources": []}))

    def test_model_is_asked_with_the_key_and_asked_again_after_a_limit(self):
        with model_stub(replies=[(429, {"Retry-After": "0"}, {"detail": "rate limit"})]) as (server, url):
            waits = []
            reply = jev_trial.ask_model(url, TRIAL_KEY, self.body, wait=waits.append)
        self.assertEqual(len(server.received), 2)
        headers, received = server.received[-1]
        self.assertEqual(headers["Authorization"], f"Bearer {TRIAL_KEY}")
        self.assertEqual(received, self.body)
        self.assertEqual(waits, [0.0])
        self.assertEqual(set(reply["answers"]), set(self.body["questions"]))

    def test_refused_key_is_reported(self):
        with model_stub(replies=[(401, {}, {"detail": "invalid key"})]) as (_, url):
            with self.assertRaisesRegex(jev_trial.KeyRefused, "401"):
                jev_trial.ask_model(url, TRIAL_KEY, self.body)

    def test_rejected_request_reports_the_detail(self):
        detail = [{"loc": ["body", "questions", "gaps", "type"], "msg": "Input should be 'noul'", "type": "literal_error"}]
        with model_stub(replies=[(422, {}, {"detail": detail})]) as (_, url):
            with self.assertRaisesRegex(jev_trial.RequestRejected, "Input should be 'noul'"):
                jev_trial.ask_model(url, TRIAL_KEY, self.body)

    def test_failure_of_the_service_is_reported(self):
        with model_stub(replies=[(503, {}, {"detail": "unavailable"})]) as (_, url):
            with self.assertRaisesRegex(jev_trial.ModelUnavailable, "503"):
                jev_trial.ask_model(url, TRIAL_KEY, self.body)

    def test_answer_to_the_request_of_a_web_page(self):
        with model_stub(page_origin="*") as (_, url):
            self.assertEqual(jev_trial.browser_access(url), "*")
        with model_stub() as (_, url):
            self.assertEqual(jev_trial.browser_access(url), "")


class TrialRunTest(unittest.TestCase):
    def test_trial_writes_the_workbook_and_the_answers_without_the_key(self):
        with tempfile.TemporaryDirectory() as folder, model_stub(page_origin="*") as (server, url):
            environ = {"TYPESAFE_API_KEY": TRIAL_KEY, "TYPESAFE_API_URL": url}
            code, printed = run_trial(["--limit", "3", "--pause", "0", "--out", folder,
                                       "--env-file", str(Path(folder) / ".env")], environ)
            written = sorted(Path(folder).iterdir())
            self.assertEqual(code, 0, printed)
            self.assertEqual([path.suffix for path in written], [".json", ".xlsx"])
            self.assertEqual(len(server.received), 3)
            answers = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual([entry["sample_id"] for entry in answers["datasets"]], ["S01", "S02", "S03"])
            self.assertEqual(answers["datasets"][0]["probabilities"]["contents"], 0.9)
            self.assertEqual(answers["browser_access"], "*")
            workbook = load_workbook(written[1])
            self.assertEqual(workbook.sheetnames, ["Read me", "Summary", "Datasets", "Texts", "Statements"])
            datasets = workbook["Datasets"]
            self.assertEqual(datasets.max_row, 4)
            self.assertEqual(datasets["A2"].value, "S01")
            self.assertTrue(datasets["B2"].hyperlink.target.startswith("https://data.gov.gr/dataset/"))
            for path in written:
                content = path.read_bytes()
                if path.suffix == ".xlsx":
                    with zipfile.ZipFile(path) as archive:
                        content = b"".join(archive.read(name) for name in archive.namelist())
                self.assertNotIn(TRIAL_KEY.encode("utf-8"), content, path.name)
        self.assertNotIn(TRIAL_KEY, printed)
        self.assertIn("Answered: 3 of 3 datasets", printed)

    def test_refused_key_stops_the_trial_after_the_first_request(self):
        with tempfile.TemporaryDirectory() as folder, model_stub(replies=[(401, {}, {"detail": "invalid key"})]) as (server, url):
            environ = {"TYPESAFE_API_KEY": TRIAL_KEY, "TYPESAFE_API_URL": url}
            code, printed = run_trial(["--pause", "0", "--out", folder, "--env-file", str(Path(folder) / ".env")], environ)
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertEqual(code, 2)
        self.assertEqual(len(server.received), 1)
        self.assertIn("refused the key", printed)

    def test_failed_dataset_is_recorded_and_the_trial_goes_on(self):
        with tempfile.TemporaryDirectory() as folder, model_stub(replies=[(503, {}, {"detail": "unavailable"})]) as (_, url):
            environ = {"TYPESAFE_API_KEY": TRIAL_KEY, "TYPESAFE_API_URL": url}
            code, printed = run_trial(["--limit", "2", "--pause", "0", "--out", folder,
                                       "--env-file", str(Path(folder) / ".env")], environ)
            answers = json.loads(next(Path(folder).glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertIn("HTTP 503", answers["datasets"][0]["error"])
        self.assertEqual(answers["datasets"][1]["error"], "")
        self.assertIn("Answered: 1 of 2 datasets", printed)

    def test_dry_run_writes_the_requests_and_asks_nothing(self):
        with tempfile.TemporaryDirectory() as folder, model_stub() as (server, url):
            code, printed = run_trial(["--dry-run", "--out", folder, "--env-file", str(Path(folder) / ".env")],
                                      {"TYPESAFE_API_URL": url})
            requests_file = Path(folder) / "jev_trial_requests.json"
            planned = json.loads(requests_file.read_text(encoding="utf-8"))
            self.assertEqual([path.name for path in Path(folder).iterdir()], ["jev_trial_requests.json"])
        self.assertEqual(code, 0, printed)
        self.assertEqual(server.received, [])
        self.assertEqual(len(planned["datasets"]), 36)
        self.assertEqual(set(planned["datasets"][0]["request"]), {"model", "state", "questions"})
        self.assertIn("36 datasets", printed)


class PublishedTrialTest(unittest.TestCase):
    """The answers of the trial of 18 November 2026, which DECISIONS.md #54 quotes."""

    @classmethod
    def setUpClass(cls):
        cls.stored = json.loads(jev_trial.PUBLISHED_ANSWERS.read_text(encoding="utf-8"))
        cls.probabilities = jev_trial.stored_probabilities(jev_trial.PUBLISHED_ANSWERS)
        reference = jev_trial.statement_reference(sorted(cls.probabilities), jev_trial.REFERENCE_FILE, jev_trial.METADATA_TABLE)
        cls.summaries = {statement.key: jev_trial.statement_summary(statement.key, cls.probabilities, reference)
                         for statement in jev_trial.TRIAL_STATEMENTS}
        cls.reference = reference

    def test_agreement_with_the_reference_is_the_one_of_the_decision(self):
        self.assertEqual({key: (item.agreed, item.compared) for key, item in self.summaries.items()},
                         {"contents": (31, 36), "coverage": (23, 33), "gaps": (36, 36), "collection": (30, 36), "errors": (35, 36)})

    def test_every_statement_counted_by_the_review_was_found(self):
        limitations = [item for key, item in self.summaries.items() if key != "contents"]
        self.assertEqual([item.reference_yes_only for item in limitations], [[], [], [], []])
        self.assertEqual(sum(item.reference_yes for item in limitations), 29)
        found = [self.probabilities[sample_id][key] for sample_id, answers in self.reference.items()
                 for key, value in answers.items() if key != "contents" and value == "yes"]
        self.assertEqual((len(found), min(found)), (29, 0.75))

    def test_differences_on_the_limitations_are_all_a_yes_of_the_model(self):
        different = {key: len(item.model_yes_only) for key, item in self.summaries.items() if key != "contents"}
        self.assertEqual(different, {"coverage": 10, "gaps": 0, "collection": 6, "errors": 1})
        self.assertEqual(self.summaries["contents"].model_yes_only, ["S06"])
        self.assertEqual(self.summaries["contents"].reference_yes_only, ["S08", "S13", "S23", "S32"])

    def test_total_agreement_is_the_one_of_the_decision(self):
        self.assertEqual((sum(item.agreed for item in self.summaries.values()),
                          sum(item.compared for item in self.summaries.values())), (155, 177))
        limitations = [item for key, item in self.summaries.items() if key != "contents"]
        self.assertEqual((sum(item.agreed for item in limitations), sum(item.compared for item in limitations)), (124, 141))

    def test_bands_of_the_limitations_against_the_review_are_those_that_the_guide_quotes(self):
        counts = Counter()
        for sample_id, answers in self.reference.items():
            for key, value in answers.items():
                expected = jev_trial.expected_answer(value)
                if key != "contents" and expected is not None:
                    counts[jev.band(self.probabilities[sample_id][key]), expected] += 1
        self.assertEqual(dict(counts), {("likely", True): 29, ("likely", False): 10, ("unsure", False): 14,
                                        ("unlikely", False): 88})
        unlikely = counts["unlikely", False]
        likely = counts["likely", True] + counts["likely", False]
        for language, sentences in (("el", (f"({unlikely} απαντήσεις)", f"Από τα {likely} «Μάλλον ναι», τα {counts['likely', True]} ήταν")),
                                    ("en", (f"({unlikely} answers)", f"Of its {likely} “Likely”, {counts['likely', True]} were"))):
            trial = load_texts(language).text("guide.reading.trial")
            self.assertIn(str(len(self.probabilities)), trial)
            for sentence in sentences:
                self.assertIn(sentence, trial)

    def test_answers_are_those_of_the_statements_of_the_code_and_hold_no_key(self):
        """The published trial asked the five statements that the review answered; their wording in the code and
        the texts sent are still those of the trial. The questions added later are not part of it."""
        datasets = jev_trial.sample_datasets(jev_trial.SAMPLE_FILE, jev_trial.SNAPSHOT)
        entries = {entry["sample_id"]: entry for entry in self.stored["datasets"]}
        self.assertEqual(sorted(entries), [dataset.sample_id for dataset in datasets])
        for dataset in datasets:
            expected = jev.request_body(jev.publisher_texts(dataset.record))
            expected["questions"] = {key: expected["questions"][key] for key in jev.TRIED}
            self.assertEqual(entries[dataset.sample_id]["request"], expected, dataset.sample_id)
        self.assertEqual({entry["model"] for entry in entries.values()}, {jev.MODEL})
        self.assertNotIn("Bearer", jev_trial.PUBLISHED_ANSWERS.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
