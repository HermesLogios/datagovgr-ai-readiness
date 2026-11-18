"""Rows that the page shows for a second reading of the description of a dataset.

A reading of Jev (aiready/jev.py) gives, for each of five statements, the probability that the texts of the
publisher make it. Here every probability becomes a row in plain words: what is stated, in which band the
probability falls, and what to add to the description when the statement is not likely made. A reading gives
no score and changes none (DECISIONS.md #54).
"""

from dataclasses import dataclass
from datetime import date

from aiready import jev
from aiready.texts import Texts

DECIMAL_MARKS = {"el": ","}


@dataclass(frozen=True)
class ReadingRow:
    """One statement as the page shows it."""

    key: str
    criterion: str
    label: str
    probability: float
    figure: str         # the probability with two decimals, written as in the language of the page
    band: str           # likely, unsure or unlikely
    band_label: str
    advice: str         # what to add to the description; empty when the statement is likely made


@dataclass(frozen=True)
class ReadingModel:
    """A reading as the page shows it: the rows in the order of the statements and where the reading comes from."""

    rows: tuple[ReadingRow, ...]
    source: str         # the model that answered and the day of the reading


def figure_of(probability: float, texts: Texts) -> str:
    """Probability with two decimals and the decimal mark of the language."""
    return f"{probability:.2f}".replace(".", DECIMAL_MARKS.get(texts.language, "."))


def build_reading_model(reading: jev.Reading, texts: Texts, day: date) -> ReadingModel:
    """Rows of a reading in the language of the texts, with the model that answered and the day."""
    rows = []
    for statement in jev.STATEMENTS:
        probability = reading.probabilities[statement.key]
        band = jev.band(probability)
        rows.append(ReadingRow(
            key=statement.key,
            criterion=statement.criterion,
            label=texts.text(f"reading.row.{statement.key}"),
            probability=probability,
            figure=figure_of(probability, texts),
            band=band,
            band_label=texts.text(f"reading.band.{band}"),
            advice="" if band == "likely" else texts.text(f"reading.advice.{statement.key}"),
        ))
    source = texts.text("reading.result.source", model=reading.model or jev.MODEL, date=texts.date(day))
    return ReadingModel(tuple(rows), source)
