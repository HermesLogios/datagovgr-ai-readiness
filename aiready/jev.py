"""Reading of the texts of a dataset by Jev, a model of TypeSafe AI that answers typed questions.

Jev writes no text. A request holds a state (the texts to be read) and named questions; for a question of the
kind "noul" the answer is the probability, from 0 to 1, that a statement is true, and for a question of the kind
"choice" a probability for every named option (API reference of TypeSafe, docs.typesafe.ai/api, read on 18 and
20 November 2026).

The state holds the texts in which a publisher describes a dataset in words: the title, the description and the
descriptions of the resources that say more than a name. They are selected as in
scripts/12_limitation_checks.py, so that the model reads what the review of the study read. When the DataStore of
the portal holds tables of the dataset, the state also holds the names of their columns with the data dictionary
of the portal, as the relay of the site returns them: the structure of the tables only, as in
scripts/08_documentation_checks.py. No record of the data and no other field of the metadata is sent.

The statements follow the criteria of the study. Five were compared with the review of the study on its 36
datasets (aiready/jev_trial.py): whether the description says what the data contain (M1) and the four questions
of the declared limitations (AI7, DECISIONS.md #50). Four were added on 20 November 2026 and are not compared yet:
how often the data are updated (M2), whether they hold personal data (M8), whether the fields are explained and
whether the names of the columns are understandable (AI2). A question of choice gives the category of high-value
data that the texts resemble (M9). The answers are a second reading next to the checks; they give no score.
"""

import html
import json
import re
import unicodedata
from dataclasses import dataclass, field

MODEL = "jev-1.14.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

YES_THRESHOLD = 0.5     # a probability from here upwards counts as yes when answers are counted
LIKELY = 0.7            # from here upwards the statement is shown as likely true
UNLIKELY = 0.3          # up to here the statement is shown as likely false

MAX_DESCRIPTION_CHARACTERS = 6000
MAX_RESOURCE_DESCRIPTIONS = 20
MAX_RESOURCE_DESCRIPTION_CHARACTERS = 1000

# Entry of the additional metadata that names the layer of a harvested map layer. The descriptions that the
# harvester of the portal writes for the resources of such a dataset name the layer and are not texts of the
# publisher (scripts/12_limitation_checks.py).
LAYER_NAME = "wms_layer_name"
BUNDLE_MARK = "downloadall_datapackage_hash"

TEXT_FIELDS = "the field description or the field resource_descriptions"
ALL_TEXT_FIELDS = "the field description, the field resource_descriptions or the field columns"
MAX_TABLES = 3              # tables of the DataStore whose columns are asked for
MAX_COLUMNS = 100           # names of columns sent to the model
MAX_COLUMN_CHARACTERS = 160


@dataclass(frozen=True)
class Statement:
    """A statement about the texts of a dataset, with what counts as true and as false."""

    key: str
    criterion: str
    instructions: str
    when_true: str
    when_false: str
    needs_columns: bool = False     # asked only when names of columns are sent


STATEMENTS = (
    Statement(
        key="contents",
        criterion="M1",
        instructions="The description of the dataset tells a reader what the data contain.",
        when_true="The field description names what is recorded in the data, in words that add information to "
                  "the field title: for example the items, the measures or the attributes that the data hold.",
        when_false="The field description is empty, repeats the title or says it in other words, or gives only "
                   "a place, a date, a file format or the name of an organisation.",
    ),
    Statement(
        key="frequency",
        criterion="M2",
        instructions="The texts state how often the data are updated, or that they will not be updated.",
        when_true=f"A sentence in {TEXT_FIELDS} gives how often new data are added or the data are revised, for "
                  "example daily, monthly or every year, or says that the data are complete and will not change.",
        when_false="No sentence speaks of updates. A date of publication or of the last change alone does not say "
                   "how often the data are updated.",
    ),
    Statement(
        key="personal",
        criterion="M8",
        instructions="The texts state whether the data hold personal data, or that they are anonymised or "
                     "aggregated.",
        when_true=f"A sentence in {TEXT_FIELDS} says that the data include or exclude data about identifiable "
                  "persons, or that they are anonymised, pseudonymised, aggregated or statistical.",
        when_false="No sentence speaks of persons, personal data, anonymisation or aggregation.",
    ),
    Statement(
        key="fields",
        criterion="AI2",
        instructions="The texts explain what the fields of the data hold.",
        when_true=f"A text in {ALL_TEXT_FIELDS} explains the meaning of the fields or columns of the data, for "
                  "example their contents, their units or the meaning of their codes.",
        when_false="No text explains the fields. Naming the files, their format or their number of rows does not "
                   "explain the fields.",
    ),
    Statement(
        key="names",
        criterion="AI2",
        instructions="The names of the columns can be understood without a data dictionary.",
        when_true="Most names in the field columns are words or common abbreviations that say what the column "
                  "holds, such as a date, a municipality or a count.",
        when_false="Most names in the field columns are codes, letters, numbers or abbreviations that need an "
                   "explanation to be understood.",
        needs_columns=True,
    ),
    Statement(
        key="coverage",
        criterion="AI7",
        instructions="The texts state what the data cover and how far they reach.",
        when_true=f"A sentence in {TEXT_FIELDS} gives the extent of the data as information about them: the area, "
                  "the period, the population or the cases that are included.",
        when_false="The texts only name the dataset, with its subject, place, year or categories, as a title "
                   "does, or they say nothing about the extent of the data.",
    ),
    Statement(
        key="gaps",
        criterion="AI7",
        instructions="The texts state that something is missing from the data.",
        when_true=f"A sentence in {TEXT_FIELDS} says that some data are missing, incomplete, not included or not shown.",
        when_false="No sentence says that data are missing. A sentence that only tells the users of a service "
                   "about a restriction of the service is not such a statement.",
    ),
    Statement(
        key="collection",
        criterion="AI7",
        instructions="The texts state where the data come from or how they were collected or produced.",
        when_true=f"A sentence in {TEXT_FIELDS} names the source of the data, or the way in which they were "
                  "collected, measured, computed or produced.",
        when_false="No sentence gives the source or the method. Naming the organisation that publishes the "
                   "dataset as the provider of the data is not such a statement, and neither is the phrase "
                   "that the data are provided as they are.",
    ),
    Statement(
        key="errors",
        criterion="AI7",
        instructions="The texts state how accurate the data are, which errors they have, or that the method "
                     "has changed.",
        when_true=f"A sentence in {TEXT_FIELDS} gives the accuracy of the data, a known error or correction, a change "
                  "of the method, or says that the data are provisional or indicative.",
        when_false="No sentence speaks of accuracy, errors, corrections or changes of the method. A general "
                   "statement that no liability is accepted is not such a statement.",
    ),
)


@dataclass(frozen=True)
class ChoiceQuestion:
    """A question with one answer out of named options; the model gives a probability for every option."""
    key: str
    criterion: str
    instructions: str
    options: dict[str, str]     # name of an option and what it covers


# Statements that the trial compared with the review of the study.
TRIED = ("contents", "coverage", "gaps", "collection", "errors")

# The six thematic categories of high-value datasets of Implementing Regulation (EU) 2023/138, each with the
# name under which the portal and the page show it.
HIGH_VALUE_CATEGORIES = {
    "geospatial": "Geospatial",
    "earth_observation": "Earth observation and environment",
    "meteorological": "Meteorological",
    "statistics": "Statistics",
    "companies": "Companies and company ownership",
    "mobility": "Mobility",
}
NO_CATEGORY = "none"
CATEGORY_QUESTION = ChoiceQuestion(
    key="hvd_category",
    criterion="M9",
    instructions="Which thematic category of high-value datasets of Implementing Regulation (EU) 2023/138 do the "
                 "data described in the texts belong to?",
    options={
        "geospatial": "Geospatial data: administrative units, geographical names, addresses, buildings, cadastral "
                      "parcels, reference parcels and agricultural parcels.",
        "earth_observation": "Earth observation and environment: hydrography, protected sites, elevation, geology, "
                             "land cover and land use, soil, natural risk zones, emissions, air and water quality, "
                             "noise, waste, nature and biodiversity.",
        "meteorological": "Meteorological data: observations of weather stations, climate data, weather warnings, "
                          "radar data and forecasts of weather models.",
        "statistics": "Statistics: official statistics on the economy, the population, the labour market, prices, "
                      "trade, industry, agriculture, transport, energy, health, education or the environment.",
        "companies": "Companies and company ownership: data of business registers, such as the name, number, "
                     "address, legal form and status of companies, and their documents and accounts.",
        "mobility": "Mobility: transport networks of roads, railways, inland waterways, air transport and "
                    "cableways, and data on inland waterways.",
        NO_CATEGORY: "The data belong to none of these six categories.",
    },
)


@dataclass(frozen=True)
class PublisherTexts:
    """The texts of a dataset that are sent to the model."""

    title: str
    description: str
    resource_descriptions: tuple[str, ...]
    shortened: bool


@dataclass(frozen=True)
class Reading:
    """The probability that each statement asked is true, and of every category, as the model returned them."""

    model: str
    probabilities: dict[str, float]
    input_tokens: int
    categories: dict[str, float] = field(default_factory=dict)     # empty when the reply holds no category


class JevReplyError(ValueError):
    """A reply of the model that does not hold a probability for every statement."""


def plain_text(value) -> str:
    """A text without HTML tags, character entities and repeated spaces."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))).strip()


def letters_only(value) -> str:
    """A text reduced to its letters and digits, without accents and in lower case, for comparisons."""
    text = unicodedata.normalize("NFD", plain_text(value).lower())
    text = "".join(character for character in text if unicodedata.category(character) != "Mn")
    return re.sub(r"[\W_]+", " ", text).strip()


def layer_name(record: dict) -> str:
    """Name of the map layer of a harvested dataset, in lower case, or an empty text."""
    name = ""
    for entry in record.get("extras") or []:
        if isinstance(entry, dict) and entry.get("key") == LAYER_NAME and str(entry.get("value") or "").strip():
            name = str(entry["value"]).strip().lower()
    return name


def publisher_texts(record: dict) -> PublisherTexts:
    """Title, description and the descriptions of the resources that say more than a name.

    A description of a resource is left out when it is empty, when it equals the name of the resource, the
    title or the description of the dataset, when it names the layer of a harvested map layer, and when it
    belongs to the automatic bundle of the portal. Equal descriptions are kept once.
    """
    title = plain_text(record.get("title"))
    description = plain_text(record.get("notes"))
    layer = layer_name(record)
    found = []
    for resource in record.get("resources") or []:
        if not isinstance(resource, dict) or resource.get(BUNDLE_MARK):
            continue
        text = plain_text(resource.get("description"))
        if not text or text in found:
            continue
        if letters_only(text) in (letters_only(resource.get("name")), letters_only(title), letters_only(description)):
            continue
        if layer and layer in text.lower():
            continue
        found.append(text)
    kept = tuple(text[:MAX_RESOURCE_DESCRIPTION_CHARACTERS] for text in found[:MAX_RESOURCE_DESCRIPTIONS])
    shortened = (len(description) > MAX_DESCRIPTION_CHARACTERS or len(found) > MAX_RESOURCE_DESCRIPTIONS
                 or any(len(text) > MAX_RESOURCE_DESCRIPTION_CHARACTERS for text in found[:MAX_RESOURCE_DESCRIPTIONS]))
    return PublisherTexts(title, description[:MAX_DESCRIPTION_CHARACTERS], kept, shortened)


def datastore_tables(record: dict) -> list[str]:
    """Identifiers of the first tables of a dataset that the DataStore of the portal holds, without the bundle."""
    tables = []
    for resource in record.get("resources") or []:
        if (isinstance(resource, dict) and resource.get("datastore_active") is True and not resource.get(BUNDLE_MARK)
                and isinstance(resource.get("id"), str) and resource["id"] not in tables):
            tables.append(resource["id"])
    return tables[:MAX_TABLES]


def column_texts(reply_text: str) -> tuple[str, ...]:
    """Names of the columns in a reply of the relay of the site, each with the label and the notes of the data
    dictionary when they say more than the name, once each; empty when the reply holds none."""
    try:
        tables = json.loads(reply_text or "{}").get("columns")
    except (ValueError, AttributeError):
        return ()
    found = []
    for columns in tables.values() if isinstance(tables, dict) else ():
        for column in columns if isinstance(columns, list) else ():
            name = plain_text(column.get("id")) if isinstance(column, dict) else ""
            if not name:
                continue
            label, notes = plain_text(column.get("label")), plain_text(column.get("notes"))
            text = f"{name} ({label})" if label and letters_only(label) != letters_only(name) else name
            text = (f"{text}: {notes}" if notes else text)[:MAX_COLUMN_CHARACTERS]
            if text not in found:
                found.append(text)
    return tuple(found[:MAX_COLUMNS])


def request_body(texts: PublisherTexts, model: str = MODEL, columns: tuple[str, ...] = ()) -> dict:
    """Body of the request to the model: the texts and any names of columns as the state, the statements and the
    question of the category as questions. The statement on the names of the columns is asked only with them."""
    state = {
        "title": texts.title,
        "description": texts.description,
        "resource_descriptions": list(texts.resource_descriptions),
    }
    if columns:
        state["columns"] = list(columns)
    questions = {
        statement.key: {
            "type": "noul",
            "instructions": statement.instructions,
            "criteria": {"true": statement.when_true, "false": statement.when_false},
        }
        for statement in STATEMENTS if columns or not statement.needs_columns
    }
    questions[CATEGORY_QUESTION.key] = {
        "type": "choice",
        "instructions": CATEGORY_QUESTION.instructions,
        "criteria": dict(CATEGORY_QUESTION.options),
    }
    return {"model": model, "state": state, "questions": questions}


def categories_in_answer(answer) -> dict[str, float]:
    """Probability of every category in the answer to the question of the category; empty without such an
    answer, and JevReplyError for a probability out of range or an option that was not asked."""
    chances = answer.get("probabilities") if isinstance(answer, dict) and answer.get("type") == "choice" else None
    if not isinstance(chances, dict) or not chances:
        return {}
    if not set(chances) <= set(CATEGORY_QUESTION.options):
        raise JevReplyError("the reply holds an option of the category that was not asked")
    categories = {}
    for option in CATEGORY_QUESTION.options:
        value = chances.get(option, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise JevReplyError(f"the reply holds no probability for the category {option}")
        categories[option] = float(value)
    return categories


def reading_in_reply(reply) -> Reading:
    """The probabilities of a reply of the model; JevReplyError when one of them is missing or out of range.

    The statement on the names of the columns may be missing, since it is asked only when columns are sent.
    """
    answers = reply.get("answers") if isinstance(reply, dict) else None
    if not isinstance(answers, dict):
        raise JevReplyError("the reply holds no answers")
    probabilities = {}
    for statement in STATEMENTS:
        answer = answers.get(statement.key)
        if answer is None and statement.needs_columns:
            continue
        value = answer.get("noul") if isinstance(answer, dict) and answer.get("type") == "noul" else None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise JevReplyError(f"the reply holds no probability for the statement {statement.key}")
        probabilities[statement.key] = float(value)
    usage = reply.get("usage") if isinstance(reply.get("usage"), dict) else {}
    tokens = usage.get("input_tokens")
    return Reading(
        model=str(reply.get("model") or ""),
        probabilities=probabilities,
        input_tokens=tokens if isinstance(tokens, int) and not isinstance(tokens, bool) else 0,
        categories=categories_in_answer(answers.get(CATEGORY_QUESTION.key)),
    )


def band(probability: float) -> str:
    """Band in which a probability is shown: likely, unsure or unlikely."""
    if probability >= LIKELY:
        return "likely"
    if probability <= UNLIKELY:
        return "unlikely"
    return "unsure"
