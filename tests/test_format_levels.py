"""Tests of the level that scripts/04_metadata_checks.py gives to a resource on the 5-star scale (criterion Q6),
for a file that the portal has also loaded in its DataStore (DECISIONS.md #56)."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = "https://data.gov.gr/dataset/11111111-2222-3333-4444-555555555555/resource/{}/download/{}"


def load_checks():
    """The script as a module, with its table of file types filled, as its own main function does."""
    spec = importlib.util.spec_from_file_location("metadata_checks_for_levels", ROOT / "scripts" / "04_metadata_checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.FILE_TYPES.update(module.load_file_types())
    return module


CHECKS = load_checks()


def uploaded(identifier: str, declared: str, name: str, in_datastore: bool) -> dict:
    """A file uploaded on the portal, as the catalogue describes it."""
    return {"id": identifier, "format": declared, "name": name, "url": UPLOAD.format(identifier, name),
            "datastore_active": in_datastore}


class LevelOfAFileInTheDataStore(unittest.TestCase):
    def test_excel_file_alone_stays_at_two_stars(self):
        level, reason = CHECKS.format_stars(uploaded("a1", "XLSX", "table.xlsx", False))
        self.assertEqual((level, reason), (2, "vendor-specific format XLSX"))

    def test_excel_file_loaded_in_the_datastore_reaches_three_stars(self):
        level, reason = CHECKS.format_stars(uploaded("a2", "XLSX", "table.xlsx", True))
        self.assertEqual(level, 3)
        self.assertEqual(reason, "DataStore table of the portal next to a file (vendor-specific format XLSX)")

    def test_open_file_in_the_datastore_keeps_its_own_reason(self):
        level, reason = CHECKS.format_stars(uploaded("a3", "CSV", "table.csv", True))
        self.assertEqual((level, reason), (3, "open format CSV"))

    def test_table_without_a_file_keeps_its_own_reason(self):
        level, reason = CHECKS.format_stars({"id": "a4", "format": "CSV", "name": "table", "url": "", "datastore_active": True})
        self.assertEqual((level, reason), (3, "DataStore table of the portal (CSV and JSON through the API)"))

    def test_dataset_counts_the_resources_rated_through_the_datastore(self):
        dataset = {"resources": [uploaded("b1", "XLS", "first.xls", True), uploaded("b2", "XLS", "second.xls", False)]}
        result = CHECKS.check_q6(dataset)
        self.assertEqual((result["q6_best_stars"], result["q6_score"]), (3, 2))
        self.assertEqual((result["q6_stars_3"], result["q6_stars_3_datastore"], result["q6_stars_2"]), (1, 1, 1))

    def test_dataset_without_a_table_counts_none(self):
        dataset = {"resources": [uploaded("c1", "XLS", "first.xls", False), uploaded("c2", "CSV", "second.csv", False)]}
        result = CHECKS.check_q6(dataset)
        self.assertEqual((result["q6_best_stars"], result["q6_stars_3"], result["q6_stars_3_datastore"]), (3, 1, 0))


if __name__ == "__main__":
    unittest.main()
