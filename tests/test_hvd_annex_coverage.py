"""Tests of the rules of scripts/16_hvd_annex_coverage.py: the normalisation of the texts, the list of the datasets of
the Annex, the reading of the snapshot, the order of the candidates and the judgement of the reviewer."""
import csv
import gzip
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_coverage():
    spec = importlib.util.spec_from_file_location("hvd_annex_coverage", ROOT / "scripts" / "16_hvd_annex_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COVERAGE = load_coverage()
ITEM_COLUMNS = ["item_id", "annex_point", "category", "item", "item_el", "legal_basis", "patterns"]


def write_table(folder: Path, name: str, columns: list[str], rows: list[dict]) -> Path:
    path = folder / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def item(item_id: str, patterns: str, category: str = "Meteorological") -> dict:
    return {"item_id": item_id, "annex_point": "3.1", "category": category, "item": "Radar data",
            "item_el": "Δεδομένα ραντάρ", "legal_basis": "Annex, point 3.1", "patterns": patterns}


def record(name: str, title: str, views: int, body: str = "", organisation: str = "Body") -> dict:
    return {"kind": "dataset", "name": name, "title": title, "organisation": organisation,
            "address": f"https://data.gov.gr/dataset/{name}", "hvd_categories": "", "views": views,
            "title_text": COVERAGE.normalise(title), "body_text": COVERAGE.normalise(body)}


class Normalisation(unittest.TestCase):
    def test_accents_case_and_final_sigma(self):
        self.assertEqual(COVERAGE.normalise("Ραντάρ ΚΑΙΡΟΥ"), "ρανταρ καιρου")
        self.assertEqual(COVERAGE.normalise("Κτηματολόγιος"), "κτηματολογιοσ")
        self.assertEqual(COVERAGE.normalise("Ισοϋψείς"), "ισουψεισ")


class ListOfTheAnnex(unittest.TestCase):
    def test_row_that_cannot_be_used_stops_the_run(self):
        with tempfile.TemporaryDirectory() as folder:
            for rows in ([item("3.1-04", "ρανταρ", category="Weather")], [item("3.1-04", "ρανταρ(")],
                         [item("3.1-04", "ρανταρ"), item("3.1-04", "radar")]):
                path = write_table(Path(folder), "items.csv", ITEM_COLUMNS, rows)
                with self.assertRaises(SystemExit):
                    COVERAGE.load_items(path)

    def test_list_of_the_repository(self):
        items = COVERAGE.load_items(COVERAGE.ITEMS_FILE)
        points = {}
        for entry in items:
            points[entry["annex_point"]] = points.get(entry["annex_point"], 0) + 1
        self.assertEqual(points, {"1.1": 7, "2.1": 27, "3.1": 5, "4.1": 21, "5.1": 2, "6.1": 4})


class Snapshot(unittest.TestCase):
    def test_datasets_and_data_services_are_read_and_decisions_left_out(self):
        lines = [
            {"type": "dataset", "name": "radar-images", "title": "Εικόνες ραντάρ", "title_translated": {"en": "Radar images"},
             "notes": "Σάρωση", "tags": [{"name": "καιρός"}], "organization": {"title": "Service"},
             "tracking_summary": {"total": 7}},
            {"type": "data-service", "name": "weather-api", "title": "API καιρού", "landing_page": ["https://example.org/api"],
             "organization": {"title": "Service"}},
            {"type": "decision", "name": "decision-1", "title": "Απόφαση ραντάρ"},
        ]
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / "catalog_2026-10-24.jsonl.gz"
            with gzip.open(snapshot, "wt", encoding="utf-8") as handle:
                for line in lines:
                    handle.write(json.dumps(line, ensure_ascii=False) + "\n")
            records = COVERAGE.catalogue_records(snapshot, lambda entry: "")
        self.assertEqual([entry["name"] for entry in records], ["radar-images", "weather-api"])
        self.assertEqual(records[0]["address"], "https://data.gov.gr/dataset/radar-images")
        self.assertEqual(records[1]["address"], "https://example.org/api")
        self.assertIn("radar images", records[0]["title_text"])
        self.assertIn("καιροσ", records[0]["body_text"])
        self.assertEqual((records[0]["views"], records[1]["kind"]), (7, "data service"))


class Candidates(unittest.TestCase):
    def test_title_matches_first_then_the_most_viewed(self):
        items = [dict(item("3.1-04", r"ρανταρ|radar"), pattern=re.compile(r"ρανταρ|radar"))]
        records = [record("b", "Χάρτης", 500, body="εικόνες ραντάρ"), record("c", "Ραντάρ Αθήνας", 3),
                   record("d", "Ραντάρ Κρήτης", 40), record("e", "Θερμοκρασίες", 900)]
        found = COVERAGE.search(items, records)["3.1-04"]
        self.assertEqual([(entry["name"], place) for entry, place in found],
                         [("d", "title"), ("c", "title"), ("b", "description or tags")])


class Judgement(unittest.TestCase):
    COLUMNS = ["item_id", "answer", "datasets", "reason"]
    ITEMS = [{"item_id": "3.1-04"}, {"item_id": "3.1-05"}]
    NAMES = {"radar-images"}

    def judged(self, rows: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            path = write_table(Path(folder), "judgement.csv", self.COLUMNS, rows)
            return COVERAGE.load_judgement(path, self.ITEMS, self.NAMES)

    def test_missing_file_means_no_judgement(self):
        self.assertEqual(COVERAGE.load_judgement(Path("/nonexistent/judgement.csv"), self.ITEMS, self.NAMES), {})

    def test_valid_judgement(self):
        rows = [{"item_id": "3.1-04", "answer": "present", "datasets": "radar-images", "reason": "Images."},
                {"item_id": "3.1-05", "answer": "missing", "datasets": "", "reason": "No match."}]
        self.assertEqual(self.judged(rows)["3.1-04"]["answer"], "present")

    def test_rows_that_cannot_be_used_stop_the_run(self):
        good = {"item_id": "3.1-05", "answer": "missing", "datasets": "", "reason": "No match."}
        for wrong in ({"item_id": "3.1-04", "answer": "maybe", "datasets": "", "reason": ""},
                      {"item_id": "3.1-04", "answer": "present", "datasets": "", "reason": ""},
                      {"item_id": "3.1-04", "answer": "partly", "datasets": "unknown-name", "reason": ""},
                      {"item_id": "9.9-99", "answer": "missing", "datasets": "", "reason": ""}):
            with self.assertRaises(SystemExit):
                self.judged([wrong, good])

    def test_item_without_a_row_stops_the_run(self):
        with self.assertRaises(SystemExit):
            self.judged([{"item_id": "3.1-04", "answer": "missing", "datasets": "", "reason": "No match."}])

    def test_judgement_of_the_repository_covers_every_item(self):
        items = {entry["item_id"] for entry in COVERAGE.load_items(COVERAGE.ITEMS_FILE)}
        with COVERAGE.JUDGEMENT_FILE.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["item_id"] for row in rows}, items)
        self.assertTrue(all(row["answer"] in COVERAGE.ANSWERS for row in rows))


class Coverage(unittest.TestCase):
    def test_counts_and_addresses_of_the_named_datasets(self):
        items = [dict(item("3.1-04", "ρανταρ"), pattern=re.compile("ρανταρ"))]
        first, second = record("a", "Ραντάρ", 5, organisation="One"), record("b", "Χάρτης", 2, body="ραντάρ", organisation="Two")
        found = COVERAGE.search(items, [first, second])
        judgement = {"3.1-04": {"answer": "partly", "datasets": "a", "reason": "Images of one area."}}
        rows = COVERAGE.coverage_rows(items, found, judgement, {"a": first, "b": second})
        self.assertEqual((rows[0]["matches_in_title"], rows[0]["matches_in_description"], rows[0]["organisations"]), (1, 1, 2))
        self.assertEqual((rows[0]["answer"], rows[0]["addresses"]), ("partly", "https://data.gov.gr/dataset/a"))
        summary = COVERAGE.build_summary("2026-10-24", rows, [first, second], {"a": first, "b": second})
        self.assertIn("| Meteorological | 1 | 0 | 1 | 0 | 0 |", summary)


if __name__ == "__main__":
    unittest.main()
