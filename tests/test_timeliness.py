"""Tests of the rules of scripts/18_timeliness.py: the newest period of a text, the change of the files between two
snapshots, the score from the newest date inside the data, rule 2, and a complete run on two small snapshots."""
import csv
import gzip
import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_timeliness():
    spec = importlib.util.spec_from_file_location("timeliness", ROOT / "scripts" / "18_timeliness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIMELINESS = load_timeliness()
CHECKS = TIMELINESS.load_metadata_checks()
DOWNLOAD = date(2026, 11, 4)
DATES = ("2026-10-24", "2026-11-25")


def check(frequency, group, period, score, stated="", reason="metadata reason"):
    return {"q5_frequency": frequency, "q5_frequency_group": group, "q5_period_days": period,
            "q5_period_stated": stated, "q5_score": score, "q5_reason": reason}


MONTHLY = check("MONTHLY", "periodic", "30.44", "2.0")
ANNUAL = check("ANNUAL", "periodic", "365.25", "2.0")
SAMPLE = {"sample_id": "S90", "title": "Monthly figures", "url": "https://example.org/monthly"}


def comparison(change):
    return {"files_change": change, "new_files": 0, "updated_files": 0, "last_upload_first": "2026-10-20",
            "last_upload_second": "2026-10-20"}


class PeriodEndTest(unittest.TestCase):
    def test_year_month_and_day(self):
        self.assertEqual(TIMELINESS.period_end("2025"), date(2025, 12, 31))
        self.assertEqual(TIMELINESS.period_end("2026-08"), date(2026, 8, 31))
        self.assertEqual(TIMELINESS.period_end("2024-02"), date(2024, 2, 29))
        self.assertEqual(TIMELINESS.period_end("2024-03-13"), date(2024, 3, 13))

    def test_newest_of_several_periods(self):
        self.assertEqual(TIMELINESS.period_end("2010-2023"), date(2023, 12, 31))
        self.assertEqual(TIMELINESS.period_end("2026-10-09 to 2026-10-25"), date(2026, 10, 25))

    def test_text_without_a_period(self):
        self.assertIsNone(TIMELINESS.period_end(""))
        self.assertIsNone(TIMELINESS.period_end("decision 21487"))
        self.assertIsNone(TIMELINESS.period_end("2026-13"))

    def test_inside_the_files_before_the_names(self):
        newest, source = TIMELINESS.newest_data({"file_period_last": "2023-12-31", "resource_period_last": "2026"})
        self.assertEqual((newest, source), (date(2023, 12, 31), "inside the files"))
        newest, source = TIMELINESS.newest_data({"file_period_last": "", "resource_period_last": "2024-03-13"})
        self.assertEqual((newest, source), (date(2024, 3, 13), "names of the files"))
        self.assertEqual(TIMELINESS.newest_data({}), (None, ""))


class DownloadDatesTest(unittest.TestCase):
    def test_newest_successful_attempt(self):
        rows = [
            {"sample_id": "S01", "attempt_1_date": "2026-11-04", "attempt_1_result": "available",
             "attempt_2_date": "", "attempt_2_result": ""},
            {"sample_id": "S02", "attempt_1_date": "2026-11-04", "attempt_1_result": "failed",
             "attempt_2_date": "2026-11-05", "attempt_2_result": "available"},
            {"sample_id": "S03", "attempt_1_date": "2026-11-04", "attempt_1_result": "failed",
             "attempt_2_date": "2026-11-05", "attempt_2_result": "failed"},
        ]
        self.assertEqual(TIMELINESS.download_dates(rows),
                         {"S01": date(2026, 11, 4), "S02": date(2026, 11, 5), "S03": date(2026, 11, 5)})


class CompareFilesTest(unittest.TestCase):
    OLD, NEW = date(2026, 10, 20), date(2026, 11, 20)

    def test_new_file(self):
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD)}, {"a": ("u1", self.OLD), "b": ("u2", None)})
        self.assertEqual((result["files_change"], result["new_files"]), ("changed", 1))

    def test_newer_upload(self):
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD)}, {"a": ("u1", self.NEW)})
        self.assertEqual((result["files_change"], result["updated_files"]), ("changed", 1))
        self.assertEqual(result["last_upload_second"], "2026-11-20")

    def test_same_files(self):
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD)}, {"a": ("u1", self.OLD)})
        self.assertEqual(result["files_change"], "unchanged")

    def test_record_created_again_for_the_same_address(self):
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD)}, {"x": ("u1", self.OLD)})
        self.assertEqual((result["files_change"], result["recreated_records"], result["removed_files"]),
                         ("unchanged", 1, 0))
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD)}, {"x": ("u1", self.NEW)})
        self.assertEqual((result["files_change"], result["updated_files"]), ("changed", 1))

    def test_external_addresses(self):
        external = {"a": ("https://example.org/data.csv", None)}
        self.assertEqual(TIMELINESS.compare_files(external, dict(external))["files_change"], "not measurable")
        added = dict(external, b=("https://example.org/more.csv", None))
        self.assertEqual(TIMELINESS.compare_files(external, added)["files_change"], "changed")

    def test_removed_file(self):
        result = TIMELINESS.compare_files({"a": ("u1", self.OLD), "b": ("u2", self.OLD)}, {"a": ("u1", self.OLD)})
        self.assertEqual((result["files_change"], result["removed_files"]), ("unchanged", 1))


class ScoreFromDataTest(unittest.TestCase):
    def score(self, group, period, newest, stated=False, frequency="MONTHLY"):
        return TIMELINESS.score_from_data(CHECKS, group, period, stated, frequency, newest, DOWNLOAD)[0]

    def test_periodic_limits(self):
        self.assertEqual(self.score("periodic", 30.44, date(2026, 9, 30)), 2)
        self.assertEqual(self.score("periodic", 30.44, date(2026, 8, 31)), 1)
        self.assertEqual(self.score("periodic", 30.44, date(2025, 12, 31)), 0)
        self.assertEqual(self.score("periodic", 1.0, date(2026, 11, 3), frequency="CONT"), 2)

    def test_newest_data_after_the_download(self):
        self.assertEqual(self.score("periodic", 30.44, date(2026, 12, 31)), 2)
        score, reason = TIMELINESS.score_from_data(CHECKS, "no period", None, False, "", date(2026, 12, 31), DOWNLOAD)
        self.assertEqual(score, 1)
        self.assertIn("a period that ends after the download of 2026-11-04", reason)

    def test_no_usable_period(self):
        self.assertEqual(self.score("no period", None, date(2026, 6, 23), frequency=""), 1)
        self.assertEqual(self.score("no period", None, date(2023, 12, 31), frequency=""), 0)

    def test_not_updated(self):
        self.assertEqual(self.score("not updated", None, date(2017, 2, 28), stated=True, frequency="NOT_PLANNED"), 2)
        self.assertEqual(self.score("not updated", None, date(2025, 12, 31), frequency="NOT_PLANNED"), 1)
        self.assertEqual(self.score("not updated", None, date(2019, 12, 31), frequency="NOT_PLANNED"), 0)


class ProposeTest(unittest.TestCase):
    def propose(self, first, second, history, change):
        return TIMELINESS.propose(CHECKS, SAMPLE, first, second, history, DOWNLOAD, comparison(change), DATES)

    def test_rule_2_lowers_a_two(self):
        row = self.propose(MONTHLY, MONTHLY, {"file_period_last": "2026-10"}, "unchanged")
        self.assertEqual((row["proposed_score"], row["rule_2"]), (1, "applied"))
        self.assertIn("rule 2", row["reason"])

    def test_changed_files_keep_the_score(self):
        row = self.propose(MONTHLY, MONTHLY, {"file_period_last": "2026-10"}, "changed")
        self.assertEqual((row["proposed_score"], row["rule_2"]), (2, ""))

    def test_rule_2_only_for_short_periods(self):
        row = self.propose(ANNUAL, ANNUAL, {}, "unchanged")
        self.assertEqual((row["proposed_score"], row["rule"]), (2, "metadata part on the second snapshot"))

    def test_date_inside_the_data_comes_first(self):
        row = self.propose(MONTHLY, MONTHLY, {"file_period_last": "2026-08"}, "changed")
        self.assertEqual((row["proposed_score"], row["rule"]), (1, "1: newest date inside the data"))
        self.assertEqual((row["score_first"], row["metadata_score"]), (2, 2))

    def test_not_measurable(self):
        record_only = check("", "no period", "", "", reason="no upload date on the portal")
        row = self.propose(record_only, record_only, {}, "not measurable")
        self.assertEqual((row["proposed_score"], row["rule"]), ("", "3: not measurable"))

    def test_changed_frequency_is_noted(self):
        row = self.propose(MONTHLY, ANNUAL, {}, "changed")
        self.assertIn("changed from MONTHLY to ANNUAL", row["reason"])


def resource(identifier, address, last_modified=None):
    return {"id": identifier, "url": address, "created": "2026-01-10T10:00:00",
            "last_modified": last_modified, "format": "CSV"}


def dataset(identifier, resources):
    return {"type": "dataset", "id": identifier, "name": f"dataset-{identifier}", "title": f"Dataset {identifier}",
            "organization": {"title": "Body"}, "metadata_created": "2026-01-01T09:00:00", "resources": resources}


def write_snapshot(path, datasets):
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for record in datasets:
            handle.write(json.dumps(record) + "\n")


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class CompleteRunTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        base = Path(self.folder.name)
        self.raw, self.processed, self.out = base / "raw", base / "processed", base / "outputs"
        for folder in (self.raw, self.processed, self.out):
            folder.mkdir()
        for name, value in (("PROCESSED_DIR", self.processed), ("OUT_DIR", self.out),
                            ("SAMPLE_FILE", self.processed / "sample.csv"),
                            ("HISTORY_FILE", self.processed / "history.csv"),
                            ("DOWNLOADS_FILE", self.processed / "downloads.csv")):
            self.addCleanup(setattr, TIMELINESS, name, getattr(TIMELINESS, name))
            setattr(TIMELINESS, name, value)
        self.addCleanup(self.folder.cleanup)

        monthly = dataset("d1", [resource("f1", "https://data.gov.gr/f1.csv", "2026-10-20T08:00:00")])
        daily = dataset("d2", [resource("f2", "https://data.gov.gr/f2.csv", "2026-10-23T08:00:00")])
        daily_updated = dataset("d2", [resource("f2", "https://data.gov.gr/f2.csv", "2026-11-20T08:00:00")])
        external = dataset("d3", [resource("f3", "https://example.org/f3.csv")])
        removed = dataset("d4", [resource("f4", "https://data.gov.gr/f4.csv", "2026-05-01T08:00:00")])
        new = dataset("d5", [resource("f5", "https://data.gov.gr/f5.csv", "2026-11-10T08:00:00")])
        write_snapshot(self.raw / "catalog_2026-10-24.jsonl.gz", [monthly, daily, external, removed])
        write_snapshot(self.raw / "catalog_2026-11-25.jsonl.gz", [monthly, daily_updated, external, new])

        def checks(rows):
            return [dict(id=identifier, sample_id=sample_id, **values) for identifier, sample_id, values in rows]

        first = [("d1", "S90", MONTHLY), ("d2", "S91", check("DAILY", "periodic", "1.0", "0.0")),
                 ("d3", "", check("DAILY", "periodic", "1.0", "")), ("d4", "", ANNUAL)]
        second = [("d1", "S90", MONTHLY), ("d2", "S91", check("DAILY", "periodic", "1.0", "2.0")),
                  ("d3", "", check("DAILY", "periodic", "1.0", "")), ("d5", "", ANNUAL)]
        write_rows(self.processed / "metadata_checks_2026-10-24.csv", checks(first))
        write_rows(self.processed / "metadata_checks_2026-11-25.csv", checks(second))
        write_rows(self.processed / "sample.csv", [
            {"sample_id": "S90", "id": "d1", "title": "Monthly figures", "url": "https://example.org/monthly"},
            {"sample_id": "S91", "id": "d2", "title": "Daily figures", "url": "https://example.org/daily"}])
        write_rows(self.processed / "history.csv", [
            {"sample_id": "S90", "file_period_last": "2026-10", "resource_period_last": ""},
            {"sample_id": "S91", "file_period_last": "", "resource_period_last": ""}])
        write_rows(self.processed / "downloads.csv", [
            {"sample_id": "S90", "attempt_1_date": "2026-11-04", "attempt_1_result": "available",
             "attempt_2_date": "", "attempt_2_result": ""}])

    def test_run(self):
        code = TIMELINESS.main(["--first", str(self.raw / "catalog_2026-10-24.jsonl.gz"),
                                "--second", str(self.raw / "catalog_2026-11-25.jsonl.gz")])
        self.assertEqual(code, 0)
        with open(self.processed / "timeliness_sample_2026-11-25.csv", encoding="utf-8-sig") as handle:
            sample = {row["sample_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual((sample["S90"]["proposed_score"], sample["S90"]["rule_2"]), ("1", "applied"))
        self.assertEqual((sample["S91"]["proposed_score"], sample["S91"]["files_change"]), ("2", "changed"))
        with open(self.processed / "timeliness_catalogue_2026-11-25.csv", encoding="utf-8-sig") as handle:
            catalogue = {row["id"]: row for row in csv.DictReader(handle)}
        self.assertEqual({key: row["presence"] for key, row in catalogue.items()},
                         {"d1": "both", "d2": "both", "d3": "both", "d4": "first snapshot only",
                          "d5": "second snapshot only"})
        self.assertEqual([catalogue[key]["files_change"] for key in ("d1", "d2", "d3")],
                         ["unchanged", "changed", "not measurable"])
        summary = (self.out / "timeliness_2026-11-25" / "summary.md").read_text(encoding="utf-8")
        self.assertIn("Timeliness (Q5) with the second snapshot, 2026-10-24 and 2026-11-25", summary)
        self.assertIn("| MONTHLY | 1 | 0 | 1 | 0 |", summary)

    def test_second_snapshot_must_be_later(self):
        with self.assertRaises(SystemExit):
            TIMELINESS.main(["--first", str(self.raw / "catalog_2026-11-25.jsonl.gz"),
                             "--second", str(self.raw / "catalog_2026-10-24.jsonl.gz")])


if __name__ == "__main__":
    unittest.main()
