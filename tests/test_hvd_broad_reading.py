"""Tests of the rules of scripts/17_hvd_broad_reading.py: the order of the rule that places a map layer in a group, the
reading of the snapshot, the draw of the sample, the judgement of the reviewer and the summary."""
import csv
import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_broad_reading():
    spec = importlib.util.spec_from_file_location("hvd_broad_reading", ROOT / "scripts" / "17_hvd_broad_reading.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BROAD_READING = load_broad_reading()
BOTH, BROAD, NEITHER = BROAD_READING.BOTH, BROAD_READING.BROAD, BROAD_READING.NEITHER
THEMES = BROAD_READING.theme_patterns(BROAD_READING.read_table(BROAD_READING.ITEMS_FILE))


def write_table(folder: Path, name: str, columns: list[str], rows: list[dict]) -> Path:
    path = folder / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def layer(name: str, group: str, title: str = "Τίτλος") -> dict:
    return {"name": name, "title": title, "organisation": "Body", "address": f"https://data.gov.gr/dataset/{name}",
            "map_view_only": "no", "marked_high_value": "no", "group": group, "rule": "none"}


class OrderOfTheRule(unittest.TestCase):
    def placed(self, name: str, title: str) -> tuple[str, str]:
        return BROAD_READING.classify(name, title, THEMES)

    def test_orthoimagery_comes_first(self):
        self.assertEqual(self.placed("gis-a-wms-only-ofx_ras_1", "Ορθοφωτοχάρτης 472-912"), (BOTH, "orthoimagery"))

    def test_scans_of_legal_acts(self):
        for name, title in (("gis-a-wms-only-rym-a_024346fs000685_1996e", "Διάγραμμα 685/Δ/1996"),
                            ("gis-a-wms-only-rasrym-a_01", "01"),
                            ("gis-a-wms-only-trm", "ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 22/Δ/1967-03-03)")):
            self.assertEqual(self.placed(name, title), (BROAD, "scan of a legal act"))

    def test_same_act_as_vector_data_is_land_use(self):
        self.assertEqual(self.placed("gis-a-wms-vec-trm", "ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 22/Δ/1967-03-03)"),
                         (BOTH, "theme 2.1-T12"))

    def test_survey_diagram_is_not_an_act(self):
        self.assertEqual(self.placed("gis-a-wms-only-top_ras_dianomi_1946_44_geo",
                                     "Διάγραμμα Αποτύπωσης Παλιάς Πόλης Χανίων - Φύλλο 44"), (NEITHER, "none"))

    def test_local_emissions_and_waste_collection_come_before_the_themes(self):
        for title in ("Εκπομπές Αιωρούμενων Σωματιδίων 10 (PM 10) από Οδικές Μεταφορές",
                      "Συνολικές Εκπομπές Αιωρούμενων Σωματιδίων 10 (PM 10)", "Κάδοι Ανακύκλωσης (GIS 2009)"):
            self.assertEqual(self.placed("gis-a-wms-vec-x", title), (BROAD, "emissions or waste collection"))

    def test_themes_with_the_terms_of_the_map_layers(self):
        expected = {"ΥΔ01 - Μέγιστο Βάθος (T=100)": "theme 2.1-T14", "Χρήσεις Γης": "theme 2.1-T12",
                    "Υψομετρικές Ζώνες": "theme 2.1-T03", "Ρέματα": "theme 2.1-T01",
                    "Τοπική Συλλεκτήρια / Συνδετήρια Οδός - Προτεινόμενη": "theme 6.1-01"}
        for title, rule in expected.items():
            self.assertEqual(self.placed("gis-a-wms-vec-x", title), (BOTH, rule))

    def test_act_on_vector_data_environmental_term_and_neither(self):
        self.assertEqual(self.placed("gis-a-wms-vec-x", "Άδειες Δόμησης (ΤΕΕ)"), (BROAD, "legal act or plan"))
        self.assertEqual(self.placed("gis-a-wms-only-x", "Αριθμός ημερών ανά έτος με PR > 10mm - ημέρες ισχυρής "
                                                         "βροχόπτωσης"), (BROAD, "environmental term"))
        self.assertEqual(self.placed("gis-a-wms-vec-x", "Σύλλογοι"), (NEITHER, "none"))

    def test_terms_for_an_item_outside_the_list_stop_the_run(self):
        rows = [{"item_id": "1.1-01", "annex_point": "1.1", "patterns": "διοικητικ"}]
        with self.assertRaises(SystemExit):
            BROAD_READING.theme_patterns(rows)


class Snapshot(unittest.TestCase):
    def test_only_harvested_datasets_are_read(self):
        lines = [
            {"type": "dataset", "name": "gis-a-wms-only-rasrym-a_01", "title": "01", "organization": {"title": "Δήμος"}},
            {"type": "dataset", "name": "gis-a-wms-vec-syllogoi", "title": "Σύλλογοι", "organization": {"title": "Δήμος"}},
            {"type": "dataset", "name": "budget-2025", "title": "Προϋπολογισμός", "organization": {"title": "Δήμος"}},
            {"type": "data-service", "name": "gis-a-service", "title": "Υπηρεσία", "organization": {"title": "Δήμος"}},
        ]
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / "catalog_2026-10-24.jsonl.gz"
            with gzip.open(snapshot, "wt", encoding="utf-8") as handle:
                for line in lines:
                    handle.write(json.dumps(line, ensure_ascii=False) + "\n")
            layers = BROAD_READING.harvested_layers(snapshot, {"gis-a-wms-vec-syllogoi": True}, THEMES)
        self.assertEqual([entry["name"] for entry in layers], ["gis-a-wms-only-rasrym-a_01", "gis-a-wms-vec-syllogoi"])
        self.assertEqual((layers[0]["map_view_only"], layers[0]["group"], layers[0]["marked_high_value"]),
                         ("yes", BROAD, "no"))
        self.assertEqual((layers[1]["map_view_only"], layers[1]["group"], layers[1]["marked_high_value"]),
                         ("no", NEITHER, "yes"))
        self.assertEqual(layers[1]["address"], "https://data.gov.gr/dataset/gis-a-wms-vec-syllogoi")


class Sample(unittest.TestCase):
    LAYERS = ([layer(f"b{number:02}", BOTH) for number in range(25)] + [layer(f"a{number:02}", BROAD) for number in
              range(12)] + [layer(f"n{number}", NEITHER) for number in range(3)])

    def test_ten_of_each_group_or_all_of_a_smaller_group(self):
        sample = BROAD_READING.draw_sample(self.LAYERS)
        self.assertEqual([entry["group"] for entry in sample], [BOTH] * 10 + [BROAD] * 10 + [NEITHER] * 3)
        names = [entry["name"] for entry in sample[:10]]
        self.assertEqual(names, sorted(names))

    def test_same_layers_give_the_same_sample(self):
        first = [entry["name"] for entry in BROAD_READING.draw_sample(self.LAYERS)]
        second = [entry["name"] for entry in BROAD_READING.draw_sample(list(reversed(self.LAYERS)))]
        self.assertEqual(first, second)


class Judgement(unittest.TestCase):
    COLUMNS = ["name", "group_by_reviewer", "note"]
    SAMPLE = [layer("x1", BOTH, "Χρήσεις Γης"), layer("x2", BROAD), layer("x3", NEITHER)]

    def judged(self, rows: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            path = write_table(Path(folder), "check.csv", self.COLUMNS, rows)
            return BROAD_READING.load_check(path, self.SAMPLE)

    def rows(self, first_group: str = NEITHER) -> list[dict]:
        return [{"name": "x1", "group_by_reviewer": first_group, "note": "Borderline. Zones of a plan."},
                {"name": "x2", "group_by_reviewer": BROAD, "note": "Scan."},
                {"name": "x3", "group_by_reviewer": NEITHER, "note": "Services."}]

    def test_missing_file_means_no_judgement(self):
        self.assertEqual(BROAD_READING.load_check(Path("/nonexistent/check.csv"), self.SAMPLE), {})

    def test_agreement_by_group_of_the_rule(self):
        check = self.judged(self.rows())
        self.assertEqual(BROAD_READING.agreement(self.SAMPLE, check), {BOTH: (0, 1), BROAD: (1, 1), NEITHER: (1, 1)})

    def test_rows_that_cannot_be_used_stop_the_run(self):
        good = self.rows(BOTH)
        for wrong in ([dict(good[0], group_by_reviewer="maybe")] + good[1:],
                      [dict(good[0], name="y9")] + good[1:],
                      good + [good[0]],
                      good[:2]):
            with self.assertRaises(SystemExit):
                self.judged(wrong)

    def test_summary_lists_the_layers_on_which_the_two_differ(self):
        check = self.judged(self.rows())
        summary = BROAD_READING.build_summary("2026-10-24", self.SAMPLE, 100, self.SAMPLE, check)
        self.assertIn("Agreement over the sample: 2 of 3; 1 judgements are marked as borderline", summary)
        self.assertIn("| [Χρήσεις Γης](https://data.gov.gr/dataset/x1) | both readings | neither |", summary)
        self.assertIn("2 map layers would be high-value instead of 1", summary)
        self.assertIn("not recorded yet", BROAD_READING.build_summary("2026-10-24", self.SAMPLE, 100, self.SAMPLE, {}))

    def test_judgement_of_the_repository_covers_the_sample(self):
        rows = BROAD_READING.read_table(BROAD_READING.CHECK_FILE)
        sample = BROAD_READING.read_table(BROAD_READING.PROCESSED_DIR / "hvd_broad_reading_sample_2026-10-24.csv")
        self.assertEqual(sorted(row["name"] for row in rows), sorted(entry["name"] for entry in sample))
        self.assertTrue(all(row["group_by_reviewer"] in BROAD_READING.GROUPS and row["note"] for row in rows))


if __name__ == "__main__":
    unittest.main()
