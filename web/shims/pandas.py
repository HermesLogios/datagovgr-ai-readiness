"""Reader of CSV tables for the browser, where pandas is not loaded.

scripts/04_metadata_checks.py reads its table of file types with pandas.read_csv and
DataFrame.to_dict("records"). Inside the browser this module answers to the name pandas and
gives the same rows with the csv module of the standard library.
"""

import csv


class Table:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def to_dict(self, orient: str) -> list[dict]:
        if orient != "records":
            raise NotImplementedError(f"orient {orient!r} is not supported")
        return [dict(row) for row in self.rows]


def read_csv(path, encoding: str = "utf-8", dtype=str, keep_default_na: bool = False) -> Table:
    """Rows of a CSV file as text, with empty cells kept as empty text."""
    if dtype is not str or keep_default_na:
        raise NotImplementedError("only text columns with empty cells kept as text are supported")
    with open(path, encoding=encoding, newline="") as handle:
        return Table(list(csv.DictReader(handle)))
