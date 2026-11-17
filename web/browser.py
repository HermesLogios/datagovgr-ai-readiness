"""Entry points of the checks for the page that runs them inside the browser.

The script of the page fetches the reply of the catalogue and passes it here as text. Every
answer is JSON text, so that only text crosses between the page and Python. The reports are
those of the last dataset that was assessed.
"""

import json
from datetime import date

from aiready.assessment import Assessment, Source, build_assessment
from aiready.criteria import load_criteria
from aiready.identifier import InvalidIdentifier, parse_dataset_identifier
from aiready.metadata_checks import run_metadata_checks
from aiready.plain_language import PageModel, build_page_model
from aiready.records import DatasetNotFound, NotADataset, dataset_in_records, records_in_reply
from aiready.report import json_text, markdown_text
from aiready.texts import Texts, load_texts
from web import pages

PORTAL_ADDRESS = "https://data.gov.gr"
RECORD_ERRORS = ("data-service", "decision")      # record types with their own explanation
TEXT_REPORTS = {"md": markdown_text, "json": json_text}
EXCEL_FORMAT = "xlsx"

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


def result(record: dict, source: Source, language: str, example: bool) -> str:
    assessment, model, texts = explained(record, source, language)
    _last.update(assessment=assessment, language=language)
    return json.dumps(
        {"ok": True, "name": model.name, "title": model.title, "html": pages.result_html(model, texts, example=example)},
        ensure_ascii=False,
    )


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
