"""Tests of the command python -m aiready and of its reports."""

import contextlib
import dataclasses
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from aiready import portal
from aiready.assessment import Source, build_assessment
from aiready.cli import main
from aiready.criteria import load_criteria
from aiready.identifier import DatasetIdentifier
from aiready.metadata_checks import CHECK_IDS, run_metadata_checks
from aiready.report import markdown_text
from aiready.snapshot import find_dataset_record, snapshot_reference_date
from fake_portal import FakePortal, found_reply

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
SECOND_DATASET = "gis-ypen-wfd-wms-kallikratikoi_dimoi"


def run_command(arguments: list[str]) -> tuple[int, str, str]:
    output, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        code = main(arguments)
    return code, output.getvalue(), errors.getvalue()


class CommandTest(unittest.TestCase):
    def test_dataset_of_the_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            code, output, errors = run_command(["troxaia-atyxhmata", "--snapshot", str(SNAPSHOT), "--out", folder])
            self.assertEqual(code, 0)
            self.assertEqual(errors, "")
            self.assertIn("Τροχαία ατυχήματα", output)
            self.assertIn("snapshot catalog_2026-10-24.jsonl.gz", output)
            self.assertIn("description of 76 characters (minimum 100)", output)
            self.assertIn('"Ready" is ruled out until Q6 and M1 reach score 2.', output)
            self.assertIn("Problems and typical fixes", output)
            for code_of_check in CHECK_IDS:
                self.assertRegex(output, rf"(?m)^\s+{code_of_check}\s")
            written = sorted(path.name for path in Path(folder).iterdir())
            self.assertEqual(written, ["troxaia-atyxhmata_2026-10-24.json", "troxaia-atyxhmata_2026-10-24.md"])
            report = json.loads((Path(folder) / written[0]).read_bytes().decode("utf-8"))
            self.assertEqual(report["dataset"]["title"], "Τροχαία ατυχήματα")
            self.assertEqual(report["source"]["date"], "2026-10-24")
            self.assertEqual([entry["criterion_id"] for entry in report["scored"]], list(CHECK_IDS))
            self.assertEqual(report["scored"][0]["score"], 1)
            self.assertEqual(len(report["unscored"]), 14)
            self.assertEqual([entry["criterion_id"] for entry in report["problems"]], ["M1", "Q6", "M3", "Q5"])
            markdown = (Path(folder) / written[1]).read_bytes().decode("utf-8")
            self.assertIn("# Τροχαία ατυχήματα", markdown)
            self.assertIn("| M1 |", markdown)

    def test_nothing_is_written_without_an_output_folder(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.chdir(folder):
            code, _, _ = run_command(["troxaia-atyxhmata", "--snapshot", str(SNAPSHOT)])
            self.assertEqual(code, 0)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_several_datasets_and_one_unknown(self):
        arguments = ["troxaia-atyxhmata", "no-such-dataset", "https://data.gov.gr/dataset/" + SECOND_DATASET]
        code, output, errors = run_command(arguments + ["--snapshot", str(SNAPSHOT)])
        self.assertEqual(code, 1)
        self.assertIn("Τροχαία ατυχήματα", output)
        self.assertIn(SECOND_DATASET, output)
        self.assertEqual(len(errors.strip().splitlines()), 1)
        self.assertIn("no-such-dataset", errors)
        self.assertNotIn("Traceback", errors)

    def test_input_that_is_not_a_dataset(self):
        code, _, errors = run_command(["https://example.org/dataset/x", "--snapshot", str(SNAPSHOT)])
        self.assertEqual(code, 1)
        self.assertIn("data.gov.gr", errors)

    def test_dataset_read_from_the_portal(self):
        record = find_dataset_record(SNAPSHOT, DatasetIdentifier("name", "troxaia-atyxhmata"))
        replies = {'name:"troxaia-atyxhmata"': (200, found_reply([record])), 'name:"server-error"': (500, "{}")}
        with FakePortal(replies) as fake, mock.patch.dict("os.environ", {portal.BASE_URL_VARIABLE: fake.url}), \
                mock.patch.object(portal, "PAUSE_SECONDS", 0):
            code, output, errors = run_command(["troxaia-atyxhmata"])
            self.assertEqual((code, errors), (0, ""))
            self.assertIn("Τροχαία ατυχήματα", output)
            self.assertIn("read on", output)
            code, _, errors = run_command(["server-error"])
            self.assertEqual(code, 1)
            self.assertEqual(len(errors.strip().splitlines()), 1)
            self.assertNotIn("Traceback", errors)


class ReportTest(unittest.TestCase):
    def test_table_cells_keep_their_columns(self):
        reference_date = snapshot_reference_date(SNAPSHOT)
        record = find_dataset_record(SNAPSHOT, DatasetIdentifier("name", "troxaia-atyxhmata"))
        assessment = build_assessment(
            record,
            load_criteria(),
            run_metadata_checks(record, reference_date),
            Source("snapshot", f"snapshot {SNAPSHOT.name}", reference_date),
        )
        changed = dataclasses.replace(assessment.scored[0], reason="first | second\nthird")
        assessment = dataclasses.replace(assessment, scored=(changed,) + assessment.scored[1:])
        row = next(line for line in markdown_text(assessment).splitlines() if line.startswith("| M1 |"))
        self.assertIn("first \\| second third", row)
        self.assertEqual(row.count(" | "), 5)


if __name__ == "__main__":
    unittest.main()
