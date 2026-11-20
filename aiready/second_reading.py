"""Rows that the page shows for a second reading of the description of a dataset.

A reading of Jev (aiready/jev.py) gives, for each statement asked, the probability that the texts of the
publisher make it, and a probability for each category of high-value data, which becomes a hint. Here every probability becomes a row in plain words: what is stated, in which band the
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
    hint: str = ""          # the category of high-value data that the texts resemble; empty without an answer
    hint_detail: str = ""   # that the marking is missing, for a likely category of a dataset without it
    columns_read: bool = True   # whether names of columns were read


def figure_of(probability: float, texts: Texts) -> str:
    """Probability with two decimals and the decimal mark of the language."""
    return f"{probability:.2f}".replace(".", DECIMAL_MARKS.get(texts.language, "."))


def category_hint(categories: dict[str, float], texts: Texts, marked: bool) -> tuple[str, str]:
    """Sentence on the category of high-value data that the texts resemble and, for a likely category of a dataset
    without the marking, the sentence that the marking is missing; empty texts without an answer.

    A category is named as likely from the same limit as a likely statement. Below it, the sentence says that the
    texts show no category clearly and names the likeliest one with its probability.
    """
    if not categories:
        return "", ""
    best = max(categories, key=categories.get)
    if categories[best] >= jev.LIKELY and best == jev.NO_CATEGORY:
        return texts.text("reading.hvd.none", figure=figure_of(categories[best], texts)), ""
    if categories[best] >= jev.LIKELY:
        name = texts.text(f"hvd.{jev.HIGH_VALUE_CATEGORIES[best]}")
        detail = "" if marked else texts.text("reading.hvd.unmarked")
        return texts.text("reading.hvd.likely", category=name, figure=figure_of(categories[best], texts)), detail
    likeliest = max(jev.HIGH_VALUE_CATEGORIES, key=lambda option: categories.get(option, 0.0))
    name = texts.text(f"hvd.{jev.HIGH_VALUE_CATEGORIES[likeliest]}")
    return texts.text("reading.hvd.unclear", category=name, figure=figure_of(categories[likeliest], texts)), ""


def build_reading_model(reading: jev.Reading, texts: Texts, day: date, marked: bool = False) -> ReadingModel:
    """Rows of a reading in the language of the texts, with the model that answered, the day and the hint of
    the category; marked tells whether the metadata mark the dataset as high-value."""
    rows = []
    for statement in jev.STATEMENTS:
        if statement.key not in reading.probabilities:
            continue
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
    hint, detail = category_hint(reading.categories, texts, marked)
    columns_read = any(statement.key in reading.probabilities for statement in jev.STATEMENTS if statement.needs_columns)
    return ReadingModel(tuple(rows), source, hint, detail, columns_read)
