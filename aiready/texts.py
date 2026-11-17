"""Texts of the tool in Greek and English, read from aiready/locales/<language>.json.

Each file is a flat table from a key to a text. A text may have fields in braces, filled
when it is used. A key with the suffix .one or .zero holds the wording for a count of 1 or 0.
"""

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
LANGUAGES = ("el", "en")
DEFAULT_LANGUAGE = "el"
QUOTATION_MARKS = {"el": ("«", "»"), "en": ("“", "”")}
ENGLISH_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
                  "October", "November", "December")
COUNT_SUFFIXES = {0: ".zero", 1: ".one"}


class Texts:
    """Texts of one language."""

    def __init__(self, language: str, entries: dict[str, str]):
        self.language = language
        self.entries = entries

    def has(self, key: str) -> bool:
        return key in self.entries

    def text(self, key: str, **values) -> str:
        """Text of the key, with its fields filled from the values."""
        return self.entries[key].format(**values)

    def counted(self, key: str, count: int, **values) -> str:
        """Text for a count: the wording for 0 or 1 when the file has one, otherwise the general wording."""
        variant = key + COUNT_SUFFIXES.get(count, "")
        return self.entries[variant if variant in self.entries else key].format(**values)

    def quoted(self, value: str) -> str:
        opening, closing = QUOTATION_MARKS[self.language]
        return f"{opening}{value}{closing}"

    def number(self, value: int) -> str:
        """Whole number with the thousands separator of the language."""
        grouped = f"{value:,}"
        return grouped.replace(",", ".") if self.language == "el" else grouped

    def date(self, value: date) -> str:
        if self.language == "el":
            return f"{value.day}/{value.month}/{value.year}"
        return f"{value.day} {ENGLISH_MONTHS[value.month - 1]} {value.year}"


@lru_cache(maxsize=None)
def load_texts(language: str) -> Texts:
    """Texts of the language el or en."""
    if language not in LANGUAGES:
        raise ValueError(f"no texts for the language '{language}' (available: {', '.join(LANGUAGES)})")
    with open(LOCALES_DIR / f"{language}.json", encoding="utf-8") as handle:
        return Texts(language, json.load(handle))
