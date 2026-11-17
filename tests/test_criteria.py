"""Tests of the criteria read from criteria/criteria.csv."""

import re
import unittest
from pathlib import Path

from aiready.criteria import (
    CRITERIA_VERSION,
    NEEDS_FILES,
    NEEDS_JUDGEMENT,
    effort_levels,
    load_criteria,
    result_kind,
)
from aiready.metadata_checks import CHECK_IDS

ROOT = Path(__file__).resolve().parent.parent


class CriteriaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.criteria = load_criteria()

    def test_all_criteria_are_read(self):
        self.assertEqual(len(self.criteria), 23)

    def test_scored_and_unscored_criteria_cover_the_grid_once(self):
        groups = [set(CHECK_IDS), set(NEEDS_FILES), set(NEEDS_JUDGEMENT)]
        self.assertEqual(sum(len(group) for group in groups), 23)
        self.assertEqual(set().union(*groups), set(self.criteria))

    def test_result_kind_follows_the_method_column(self):
        by_rule = {key for key in CHECK_IDS if result_kind(self.criteria[key]) == "by rule"}
        self.assertEqual(by_rule, {"M2", "M3", "M9"})
        proposals = {key for key in CHECK_IDS if result_kind(self.criteria[key]) == "proposal"}
        self.assertEqual(proposals, {"M1", "M4", "M6", "M7", "Q5", "Q6"})

    def test_core_criteria(self):
        core = {key for key, criterion in self.criteria.items() if criterion.core}
        self.assertEqual(core, {"Q1", "Q6", "M1", "M4", "AI1", "AI2"})

    def test_effort_levels_keep_the_order_of_the_text(self):
        self.assertEqual(effort_levels(self.criteria["Q6"].typical_fix), ["Medium"])
        self.assertEqual(effort_levels(self.criteria["Q5"].typical_fix), ["Low", "High"])
        self.assertEqual(effort_levels("no effort stated"), [])

    def test_version_matches_the_readme_of_the_criteria(self):
        text = (ROOT / "criteria" / "README.md").read_text(encoding="utf-8")
        versions = [tuple(int(part) for part in found.split(".")) for found in re.findall(r"Version (\d+(?:\.\d+)*)", text)]
        self.assertEqual(max(versions), tuple(int(part) for part in CRITERIA_VERSION.split(".")))


if __name__ == "__main__":
    unittest.main()
