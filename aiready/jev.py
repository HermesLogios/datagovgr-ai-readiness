"""Reading of the texts of a dataset by Jev, a model of TypeSafe AI that answers typed questions.

Jev writes no text. A request holds a state (the texts to be read) and named questions; for a question of the
kind "noul" the answer is the probability, from 0 to 1, that a statement is true (API reference of TypeSafe,
docs.typesafe.ai/api, read on 18 November 2026).

The state holds only the texts in which a publisher describes a dataset in words: the title, the description
and the descriptions of the resources that say more than a name. They are selected as in
scripts/12_limitation_checks.py, so that the model reads what the review of the study read. No record of the
data and no other field of the metadata is sent.

The statements follow the criteria of the study: one asks whether the description says what the data contain
(M1), four ask the questions of the declared limitations (AI7, DECISIONS.md #50). The answers are a second
reading next to the checks; they give no score.
"""

import html
import re
import unicodedata
from dataclasses import dataclass

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


@dataclass(frozen=True)
class Statement:
    """A statement about the texts of a dataset, with what counts as true and as false."""

    key: str
    criterion: str
    instructions: str
    when_true: str
    when_false: str


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
class PublisherTexts:
    """The texts of a dataset that are sent to the model."""

    title: str
    description: str
    resource_descriptions: tuple[str, ...]
    shortened: bool


@dataclass(frozen=True)
class Reading:
    """The probability that each statement is true, as the model returned it."""

    model: str
    probabilities: dict[str, float]
    input_tokens: int


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


def request_body(texts: PublisherTexts, model: str = MODEL) -> dict:
    """Body of the request to the model: the texts as the state and the statements as questions."""
    return {
        "model": model,
        "state": {
            "title": texts.title,
            "description": texts.description,
            "resource_descriptions": list(texts.resource_descriptions),
        },
        "questions": {
            statement.key: {
                "type": "noul",
                "instructions": statement.instructions,
                "criteria": {"true": statement.when_true, "false": statement.when_false},
            }
            for statement in STATEMENTS
        },
    }


def reading_in_reply(reply) -> Reading:
    """The probabilities of a reply of the model; JevReplyError when one of them is missing or out of range."""
    answers = reply.get("answers") if isinstance(reply, dict) else None
    if not isinstance(answers, dict):
        raise JevReplyError("the reply holds no answers")
    probabilities = {}
    for statement in STATEMENTS:
        answer = answers.get(statement.key)
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
    )


def band(probability: float) -> str:
    """Band in which a probability is shown: likely, unsure or unlikely."""
    if probability >= LIKELY:
        return "likely"
    if probability <= UNLIKELY:
        return "unlikely"
    return "unsure"
