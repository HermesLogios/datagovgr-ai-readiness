"""Entry points of the checks for the page that runs them inside the browser.

The script of the page fetches the reply of the catalogue and passes it here as text. Every
answer is JSON text, so that only text crosses between the page and Python. The reports and the
request of a second reading are those of the last dataset that was assessed.
"""

import copy
import json
import re
from datetime import date

from aiready import jev
from aiready.assessment import Assessment, Source, build_assessment
from aiready.criteria import load_criteria
from aiready.identifier import InvalidIdentifier, parse_dataset_identifier
from aiready.metadata_checks import run_metadata_checks
from aiready.plain_language import STATUS_KEYS, PageModel, build_page_model
from aiready.records import DatasetNotFound, NotADataset, dataset_in_records, records_in_reply
from aiready.report import json_text, markdown_text
from aiready.second_reading import build_reading_model
from aiready.texts import Texts, load_texts
from web import pages

PORTAL_ADDRESS = "https://data.gov.gr"
RECORD_ERRORS = ("data-service", "decision")      # record types with their own explanation
TEXT_REPORTS = {"md": markdown_text, "json": json_text}
EXCEL_FORMAT = "xlsx"

# What the storage of the browser keeps of a record stands without the contact details that the metadata name:
# the people and their e-mail addresses are left out, a contact point that holds a value keeps only a name (the
# name that the example record carries), the e-mail address of the publisher is left out, and a publisher that held
# nothing else keeps a name, the description of the organisation is left out, and every e-mail address in any
# other text is masked by as many characters, so that the checks give the same results.
CONTACT_PLACEHOLDER = "contact point of the publisher"
PUBLISHER_PLACEHOLDER = "publisher of the dataset"
PERSON_FIELDS = ("author", "author_email", "maintainer", "maintainer_email")
CONTACT_FIELDS = ("contact", "creator")
EMAIL_ADDRESS = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

_criteria = None
_last: dict = {}


def criteria() -> dict:
    global _criteria
    if _criteria is None:
        _criteria = load_criteria()
    return _criteria


def refusal(code: str, language: str) -> str:
    return json.dumps({"ok": False, "code": code, "html": pages.error_html(load_texts(language), code)}, ensure_ascii=False)


def identify(text: str, language: str = "el") -> str:
    """Field and value of the catalogue search for what the visitor typed, or the code of the refusal."""
    try:
        identifier = parse_dataset_identifier(text)
    except InvalidIdentifier as error:
        return refusal(error.code, language)
    return json.dumps({"ok": True, "kind": identifier.kind, "value": identifier.value})


def explained(record: dict, source: Source, language: str) -> tuple[Assessment, PageModel, Texts]:
    """Assessment of a record and its explanation in the given language."""
    assessment = build_assessment(record, criteria(), run_metadata_checks(record, source.date), source)
    texts = load_texts(language)
    return assessment, build_page_model(assessment, texts, criteria()), texts


def example_source(snapshot_date: str) -> Source:
    return Source("snapshot", "example record of the catalogue snapshot", date.fromisoformat(snapshot_date))


def masked(value):
    """A value of a record with every e-mail address inside its texts masked by as many characters."""
    if isinstance(value, str):
        return EMAIL_ADDRESS.sub(lambda found: "x" * len(found[0]), value)
    if isinstance(value, dict):
        return {key: masked(item) for key, item in value.items()}
    if isinstance(value, list):
        return [masked(item) for item in value]
    return value


def holds_value(value) -> bool:
    """The rule of the checks for a field that holds a value: a non-blank text, or a structure with one inside."""
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(holds_value(item) for item in value.values())
    if isinstance(value, list):
        return any(holds_value(item) for item in value)
    return value is not None and bool(value)


def contact_in_place(entry):
    if not holds_value(entry):
        return entry
    if isinstance(entry, dict):
        return {"name": CONTACT_PLACEHOLDER, "email": "", "uri": "", "url": ""}
    return CONTACT_PLACEHOLDER


def publisher_in_place(entry):
    if not isinstance(entry, dict) or "email" not in entry:
        return entry
    kept = dict(entry, email="")
    if holds_value(entry) and not holds_value(kept):
        kept["name"] = PUBLISHER_PLACEHOLDER
    return kept


def without_contact_details(record: dict) -> dict:
    """The record as the storage of the browser keeps it, without the contact details that its metadata name."""
    kept = masked(copy.deepcopy(record))
    for field in PERSON_FIELDS:
        if field in kept:
            kept[field] = None
    for field in CONTACT_FIELDS:
        entries = kept.get(field)
        kept_entries = [contact_in_place(entry) for entry in entries] if isinstance(entries, list) else contact_in_place(entries)
        if field in kept:
            kept[field] = kept_entries
    if isinstance(kept.get("publisher"), list):
        kept["publisher"] = [publisher_in_place(entry) for entry in kept["publisher"]]
    if isinstance(kept.get("organization"), dict) and "description" in kept["organization"]:
        kept["organization"]["description"] = ""
    return kept


def kept_reply(record: dict) -> str:
    """Reply of the catalogue that the storage of the browser keeps for a check: the record alone, without contact details."""
    return json.dumps({"success": True, "result": {"count": 1, "results": [without_contact_details(record)]}},
                      ensure_ascii=False)


def result(record: dict, source: Source, language: str, example: bool) -> str:
    assessment, model, texts = explained(record, source, language)
    _last.update(assessment=assessment, language=language, record=record)
    met = sum(STATUS_KEYS[check.status] == "met" for check in model.checks)
    shown = {"ok": True, "name": model.name, "title": model.title, "html": pages.result_html(model, texts, example=example),
             "counts": {"met": met, "total": len(model.checks)}}
    if not example:
        shown["kept"] = kept_reply(record)
    return json.dumps(shown, ensure_ascii=False)


def assess_reply(reply_text: str, requested: str, language: str, today: str) -> str:
    """Result for the reply of the catalogue action package_search, read on the given day (ISO date)."""
    try:
        record = dataset_in_records(records_in_reply(json.loads(reply_text)), requested)
    except DatasetNotFound:
        return refusal("not_found", language)
    except NotADataset as error:
        kind = error.record_type if error.record_type in RECORD_ERRORS else "other"
        return refusal(f"record.{kind}", language)
    except ValueError:
        return refusal("portal", language)
    source = Source("portal", f"{PORTAL_ADDRESS}, read on {today}", date.fromisoformat(today))
    return result(record, source, language, example=False)


def assess_example(record_text: str, language: str, snapshot_date: str) -> str:
    """Result for the example record, as it stood in the catalogue snapshot of the given day."""
    return result(json.loads(record_text), example_source(snapshot_date), language, example=True)


def field_request() -> str:
    """Identifiers of the tables of the last dataset that was assessed whose columns the relay of the site is
    asked for, as JSON text: at most three tables that the DataStore of the portal holds."""
    if "record" not in _last:
        raise LookupError("no dataset has been assessed yet")
    return json.dumps(jev.datastore_tables(_last["record"]))


def reading_request(fields_text: str = "") -> str:
    """Request to the model for the texts of the last dataset that was assessed, with the names of the columns
    that the relay of the site returned, as JSON text."""
    if "record" not in _last:
        raise LookupError("no dataset has been assessed yet")
    columns = jev.column_texts(fields_text)
    return json.dumps(jev.request_body(jev.publisher_texts(_last["record"]), columns=columns), ensure_ascii=False)


def reading_result(reply_text: str, language: str, today: str) -> str:
    """Panel of the second reading for the reply of the model, read on the given day (ISO date)."""
    try:
        reading = jev.reading_in_reply(json.loads(reply_text))
    except ValueError:
        return json.dumps({"ok": False, "code": "service"})
    texts = load_texts(language)
    assessment = _last.get("assessment")
    marked = bool(assessment and assessment.dataset.high_value_marked)
    model = build_reading_model(reading, texts, date.fromisoformat(today), marked=marked)
    return json.dumps({"ok": True, "html": pages.reading_result_html(model, texts)}, ensure_ascii=False)


def last_assessment() -> Assessment:
    if "assessment" not in _last:
        raise LookupError("no dataset has been assessed yet")
    return _last["assessment"]


def report_name(report_format: str) -> str:
    """File name of a report of the last assessment, as the command names it."""
    assessment = last_assessment()
    return f"{assessment.dataset.name}_{assessment.source.date.isoformat()}.{report_format}"


def report_text(report_format: str) -> str:
    """Technical report of the last assessment, in Markdown or JSON."""
    if report_format not in TEXT_REPORTS:
        raise ValueError(f"unknown report format: {report_format}")
    return TEXT_REPORTS[report_format](last_assessment())


def report_excel() -> bytes:
    """Report of the last assessment in plain language, as the bytes of an .xlsx file."""
    from aiready.report_excel import excel_bytes

    assessment = last_assessment()
    texts = load_texts(_last["language"])
    return excel_bytes(build_page_model(assessment, texts, criteria()), texts)
