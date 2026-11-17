"""Checks of the Markdown table cells of the reports.

Usage:
    python -m unittest discover -s tests
"""

import unittest

from aiready.report import cell


class MarkdownCellTest(unittest.TestCase):
    def test_column_separator_and_backslash_are_escaped(self):
        self.assertEqual(cell("first | second"), "first \\| second")
        self.assertEqual(cell("folder\\name"), "folder\\\\name")
        self.assertEqual(cell("left\\|right"), "left\\\\\\|right")

    def test_line_breaks_become_spaces(self):
        self.assertEqual(cell("first\nsecond\r\n third"), "first second third")

    def test_numbers_become_text(self):
        self.assertEqual(cell(7), "7")


if __name__ == "__main__":
    unittest.main()
