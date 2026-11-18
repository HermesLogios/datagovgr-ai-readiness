"""Trial of the readings of Jev on the 36 datasets of the sample, next to the review of the study.

Every dataset of the sample is read from the stored snapshot. Its texts are sent to the model with the five
statements of aiready/jev.py, and the probabilities returned are set next to what the study found:
  - contents: the rule of M1, confirmed on the 36 datasets (DECISIONS.md #23): a description of at least 100
    characters that does not repeat the title;
  - coverage, gaps, collection, errors: the four questions of AI7 as answered in the review (DECISIONS.md #50),
    transcribed in aiready/jev_trial_reference.csv. The value "outside" marks a statement made only in a
    document or on a page outside the metadata, which a reading of the metadata cannot find. The value
    "contradicted" marks a statement that the files contradict: the review did not count it and the trial does
    not compare it.

Usage:
    python -m aiready.jev_trial --dry-run     writes the requests; asks nothing and needs no key
    python -m aiready.jev_trial --limit 2     asks for the first two datasets of the sample
    python -m aiready.jev_trial               asks for the 36 datasets

The key is read from the environment variable TYPESAFE_API_KEY or from the file .env of the repository
(a line TYPESAFE_API_KEY=...). It is sent only to the address of the model and is written in no output. The
outputs are written in the folder assessments, which stays outside the repository.

The answers of the run of 18 November 2026, which DECISIONS.md #54 quotes, are kept in
data/processed/jev_trial_2026-11-18.json: the file of answers that the run wrote, as it is.
"""

import argparse
import csv
import functools
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests
from openpyxl import Workbook
from openpyxl.styles import PatternFill

from aiready import jev
from aiready.records import record_type
from aiready.report_excel import MAX_WIDTH, finish_sheet
from aiready.snapshot import iter_snapshot_records

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
SAMPLE_FILE = ROOT / "data" / "processed" / "sample.csv"
METADATA_TABLE = ROOT / "data" / "processed" / "metadata_checks_2026-10-24.csv"
DECISIONS_FILE = ROOT / "DECISIONS.md"
REFERENCE_FILE = Path(__file__).resolve().parent / "jev_trial_reference.csv"
OUTPUT_FOLDER = ROOT / "assessments"
PUBLISHED_ANSWERS = ROOT / "data" / "processed" / "jev_trial_2026-11-18.json"
ENV_FILE = ROOT / ".env"
REQUESTS_FILE_NAME = "jev_trial_requests.json"

KEY_VARIABLE = "TYPESAFE_API_KEY"
URL_VARIABLE = "TYPESAFE_API_URL"

MINIMUM_DESCRIPTION = 100       # characters of a description that says more than a title (M1)
REFERENCE_VALUES = ("yes", "no", "outside", "contradicted")
AI7_KEYS = ("coverage", "gaps", "collection", "errors")

ATTEMPTS = 4                    # requests sent for one dataset while the address answers 429
TIMEOUT_SECONDS = 60
DEFAULT_WAIT_SECONDS = 2.0
LONGEST_WAIT_SECONDS = 30.0
PAUSE_SECONDS = 0.2             # pause between the requests of two datasets
ANY_PAGE = "https://example.org"
DETAIL_CHARACTERS = 500

DIFFERENT_FILL = PatternFill("solid", start_color="FDE9C8")


class MissingKey(RuntimeError):
    """No key of the model in the environment or in the environment file."""


class KeyRefused(RuntimeError):
    """The address of the model refused the key (HTTP 401 or 403)."""


class RequestRejected(RuntimeError):
    """The address of the model rejected the request as invalid."""


class ModelUnavailable(RuntimeError):
    """The address of the model answered with a failure of the service."""


@dataclass(frozen=True)
class SampleDataset:
    """A dataset of the sample with its record of the snapshot."""

    sample_id: str
    name: str
    title: str
    url: str
    record: dict


@dataclass(frozen=True)
class Answer:
    """What was sent for a dataset and what came back: a reading, or the reason why there is none."""

    dataset: SampleDataset
    texts: jev.PublisherTexts
    request: dict
    reading: jev.Reading | None
    error: str


@dataclass(frozen=True)
class StatementSummary:
    """Agreement of the model with the reference on one statement, over the datasets that were answered."""

    key: str
    compared: int
    agreed: int
    reference_yes: int
    model_yes: int
    model_yes_only: list[str]
    reference_yes_only: list[str]
    unsure: list[str]
    not_compared: list[str]


def environment_file_values(path: Path) -> dict[str, str]:
    """Values of a file with lines of the form NAME=value; other lines and lines that start with # are skipped."""
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, separator, value = line.partition("=")
        if separator and not name.strip().startswith("#"):
            values[name.strip()] = value.strip().strip("\"'")
    return values


def model_address(environ, env_file: Path) -> str:
    """Address of the model: the environment variable, the environment file, or the address of TypeSafe."""
    stored = environment_file_values(env_file)
    return (environ.get(URL_VARIABLE) or stored.get(URL_VARIABLE) or jev.API_URL).strip()


def model_settings(environ, env_file: Path) -> tuple[str, str]:
    """Key and address of the model; the environment variable comes before the environment file."""
    stored = environment_file_values(env_file)
    key = (environ.get(KEY_VARIABLE) or stored.get(KEY_VARIABLE) or "").strip()
    if not key:
        raise MissingKey(f"No key of the model: {KEY_VARIABLE} is set neither in the environment nor in the "
                         f"file {env_file.name} of the repository.")
    return key, model_address(environ, env_file)


def sample_datasets(sample_file: Path, snapshot: Path, limit: int | None = None) -> list[SampleDataset]:
    """The datasets of the sample in the order of their identifiers, with their records of the snapshot."""
    with open(sample_file, encoding="utf-8-sig", newline="") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: row["sample_id"])
    rows = rows[:limit] if limit else rows
    wanted = {row["name"] for row in rows}
    records = {}
    for record in iter_snapshot_records(snapshot):
        if record.get("name") in wanted and record_type(record) == "dataset":
            records[record["name"]] = record
            if len(records) == len(wanted):
                break
    missing = sorted(wanted - set(records))
    if missing:
        raise ValueError(f"the snapshot {snapshot.name} holds no record for: {', '.join(missing)}")
    return [SampleDataset(row["sample_id"], row["name"], row["title"], row["url"], records[row["name"]]) for row in rows]


def final_ai7_scores(decisions_text: str) -> dict[str, int]:
    """Final scores of AI7 by dataset, read from the sentence of DECISIONS.md #50 that lists them."""
    sentence = re.search(r"Final AI7 scores: (.*?)\. ", decisions_text)
    if not sentence:
        raise ValueError("DECISIONS.md holds no sentence that starts with 'Final AI7 scores:'")
    scores = {}
    for part in sentence.group(1).split(";"):
        score = re.match(r"\s*(\d) for ", part)
        if not score:
            raise ValueError(f"part of the sentence on the final scores of AI7 without a score: {part.strip()}")
        for sample_id in re.findall(r"S\d{2}", part):
            scores[sample_id] = int(score.group(1))
    return scores


def reviewed_statements(reference_file: Path) -> dict[str, dict[str, str]]:
    """Answer of the review to the four questions of AI7, by dataset."""
    reference = {}
    with open(reference_file, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            answers = {key: row[key] for key in AI7_KEYS}
            unknown = sorted(set(answers.values()) - set(REFERENCE_VALUES))
            if unknown:
                raise ValueError(f"{reference_file.name}, {row['sample_id']}: unknown value {', '.join(unknown)}")
            reference[row["sample_id"]] = answers
    return reference


@functools.lru_cache(maxsize=None)
def sample_metadata_rows(metadata_table: Path) -> dict[str, dict]:
    """Rows of the published table of the metadata checks for the datasets of the sample."""
    with open(metadata_table, encoding="utf-8-sig", newline="") as handle:
        return {row["sample_id"]: row for row in csv.DictReader(handle) if row["sample_id"]}


def contents_by_rule(metadata_table: Path) -> dict[str, str]:
    """Whether the description says more than a title by the rule of M1: at least 100 characters, not a repeat."""
    return {
        sample_id: "yes" if (int(row["m1_description_chars"]) >= MINIMUM_DESCRIPTION
                             and row["m1_description_repeats_title"] == "False") else "no"
        for sample_id, row in sample_metadata_rows(metadata_table).items()
    }


def m1_scores(metadata_table: Path) -> dict[str, str]:
    """Score of M1 in the published table, by dataset."""
    return {sample_id: row["m1_score"] for sample_id, row in sample_metadata_rows(metadata_table).items()}


def expected_answer(value: str) -> bool | None:
    """Answer expected from a reading of the metadata; None for a statement that is not compared."""
    return {"yes": True, "no": False, "outside": False, "contradicted": None}[value]


def statement_summary(key: str, probabilities: dict[str, dict[str, float]],
                      reference: dict[str, dict[str, str]]) -> StatementSummary:
    """Counts of agreement on one statement; a probability at or above the threshold counts as yes."""
    compared = agreed = reference_yes = model_yes = 0
    model_yes_only, reference_yes_only, unsure, not_compared = [], [], [], []
    for sample_id in sorted(probabilities):
        probability = probabilities[sample_id][key]
        expected = expected_answer(reference[sample_id][key])
        if jev.band(probability) == "unsure":
            unsure.append(sample_id)
        if expected is None:
            not_compared.append(sample_id)
            continue
        said_yes = probability >= jev.YES_THRESHOLD
        compared += 1
        reference_yes += expected
        model_yes += said_yes
        if said_yes == expected:
            agreed += 1
        elif said_yes:
            model_yes_only.append(sample_id)
        else:
            reference_yes_only.append(sample_id)
    return StatementSummary(key, compared, agreed, reference_yes, model_yes, model_yes_only, reference_yes_only,
                            unsure, not_compared)


def detail_of(response) -> str:
    """Text of the detail that the address of the model gives for a request it did not answer."""
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = response.text
    text = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
    return text[:DETAIL_CHARACTERS]


def ask_model(url: str, key: str, body: dict, wait=time.sleep) -> dict:
    """Reply of the model to one request. A request refused for the rate of requests (HTTP 429) is sent again."""
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(1, ATTEMPTS + 1):
        response = requests.post(url, headers=headers, json=body, timeout=TIMEOUT_SECONDS)
        if response.status_code != 429 or attempt == ATTEMPTS:
            break
        try:
            seconds = float(response.headers.get("Retry-After") or DEFAULT_WAIT_SECONDS)
        except ValueError:
            seconds = DEFAULT_WAIT_SECONDS
        wait(min(max(seconds, 0.0), LONGEST_WAIT_SECONDS))
    status = response.status_code
    if status in (401, 403):
        raise KeyRefused(f"HTTP {status}")
    if status in (400, 404, 413, 422):
        raise RequestRejected(f"HTTP {status}: {detail_of(response)}")
    if status != 200:
        raise ModelUnavailable(f"HTTP {status}")
    return response.json()


def browser_access(url: str) -> str:
    """What the address answers to the request that a browser sends before a call from a web page.

    Returns the value of the header Access-Control-Allow-Origin, or an empty text when the address does not
    send it: a web page can then call the address only through a server of its own.
    """
    headers = {"Origin": ANY_PAGE, "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "authorization,content-type"}
    try:
        response = requests.options(url, headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        return ""
    return response.headers.get("Access-Control-Allow-Origin", "")


def statement_reference(sample_ids, reference_file: Path, metadata_table: Path) -> dict[str, dict[str, str]]:
    """Reference of the five statements for the given datasets: the rule of M1 and the review of AI7."""
    reviewed = reviewed_statements(reference_file)
    contents = contents_by_rule(metadata_table)
    return {sample_id: {"contents": contents[sample_id], **reviewed[sample_id]} for sample_id in sample_ids}


def write_requests(path: Path, datasets: list[SampleDataset], address: str) -> int:
    """Writes the requests that the trial would send and returns the characters of the texts in them."""
    planned, characters = [], 0
    for dataset in datasets:
        texts = jev.publisher_texts(dataset.record)
        characters += len(texts.title) + len(texts.description) + sum(len(text) for text in texts.resource_descriptions)
        planned.append({"sample_id": dataset.sample_id, "name": dataset.name, "shortened": texts.shortened,
                        "request": jev.request_body(texts)})
    content = {"address": address, "datasets": planned}
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return characters


def write_answers(path: Path, answers: list[Answer], address: str, access: str, day: date) -> None:
    """Writes what was sent and what came back for every dataset, without the key."""
    content = {
        "date": day.isoformat(),
        "model_asked": jev.MODEL,
        "address": address,
        "browser_access": access,
        "threshold": jev.YES_THRESHOLD,
        "datasets": [
            {
                "sample_id": answer.dataset.sample_id,
                "name": answer.dataset.name,
                "request": answer.request,
                "model": answer.reading.model if answer.reading else "",
                "probabilities": answer.reading.probabilities if answer.reading else {},
                "input_tokens": answer.reading.input_tokens if answer.reading else 0,
                "error": answer.error,
            }
            for answer in answers
        ],
    }
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stored_probabilities(answers_file: Path) -> dict[str, dict[str, float]]:
    """Probabilities of a stored file of answers, by dataset; a dataset that got no answer is left out."""
    stored = json.loads(answers_file.read_text(encoding="utf-8"))
    return {entry["sample_id"]: entry["probabilities"] for entry in stored["datasets"] if entry["probabilities"]}


def write_workbook(path: Path, answers: list[Answer], reference: dict[str, dict[str, str]],
                   summaries: list[StatementSummary], address: str, access: str, day: date) -> None:
    """Writes the workbook of the trial: notes, agreement by statement, the datasets, the texts and the statements."""
    answered = [answer for answer in answers if answer.reading]
    scores_ai7 = final_ai7_scores(DECISIONS_FILE.read_text(encoding="utf-8"))
    scores_m1 = m1_scores(METADATA_TABLE)
    workbook = Workbook()

    notes = workbook.active
    notes.title = "Read me"
    for label, text in (
        ("Trial", "Readings of Jev on the datasets of the sample, next to the review of the study."),
        ("Date", day.isoformat()),
        ("Model asked", jev.MODEL),
        ("Model that answered", ", ".join(sorted({answer.reading.model for answer in answered})) or "none"),
        ("Address", address),
        ("Datasets", f"{len(answered)} of {len(answers)} answered"),
        ("Input tokens", sum(answer.reading.input_tokens for answer in answered)),
        ("Calls from a web page", f"allowed (Access-Control-Allow-Origin: {access})" if access
         else "not allowed by the answer of the address to the request of a browser"),
        ("Yes and no", f"A probability of {jev.YES_THRESHOLD} or more counts as yes. Probabilities above "
                       f"{jev.UNLIKELY} and below {jev.LIKELY} are listed as unsure."),
        ("contents", "Reference: the rule of M1, confirmed on the 36 datasets (DECISIONS.md #23): a description "
                     f"of at least {MINIMUM_DESCRIPTION} characters that does not repeat the title."),
        ("coverage, gaps, collection, errors", "Reference: the four questions of AI7 as answered in the review "
                                               "(DECISIONS.md #50), transcribed in aiready/jev_trial_reference.csv."),
        ("outside", "The statement is made only in a document or on a page outside the metadata. A reading of "
                    "the metadata is expected to answer no."),
        ("contradicted", "The metadata make the statement and the files contradict it. The review did not count "
                         "it and the cell is not compared."),
        ("Texts", "The sheet Texts holds what was sent for every dataset: the title, the description and the "
                  "descriptions of resources that say more than a name. No record of the data is sent or written."),
    ):
        notes.append([label, text])
    finish_sheet(notes, widths=(34, MAX_WIDTH + 30), header=False)

    summary = workbook.create_sheet("Summary")
    summary.append(["Statement", "Criterion", "Compared", "Agreed", "Yes in the reference", "Yes by Jev",
                    "Jev yes, reference no", "Jev no, reference yes", "Unsure", "Not compared"])
    criteria = {statement.key: statement.criterion for statement in jev.STATEMENTS}
    for item in summaries:
        summary.append([item.key, criteria[item.key], item.compared, item.agreed, item.reference_yes, item.model_yes,
                        ", ".join(item.model_yes_only), ", ".join(item.reference_yes_only), ", ".join(item.unsure),
                        ", ".join(item.not_compared)])
    finish_sheet(summary, widths=(14, 10, 11, 9, 12, 10, 34, 34, 34, 18))

    datasets = workbook.create_sheet("Datasets")
    header = ["ID", "Dataset", "AI7 score (review)", "M1 score (rule, confirmed)"]
    for statement in jev.STATEMENTS:
        header += [f"{statement.key}: Jev", f"{statement.key}: reference", f"{statement.key}: compared"]
    datasets.append(header + ["Answers of yes by Jev (AI7)", "Input tokens", "Error"])
    for answer in answers:
        sample_id = answer.dataset.sample_id
        row = [sample_id, answer.dataset.title, scores_ai7.get(sample_id), scores_m1.get(sample_id)]
        yes_answers = None
        if answer.reading:
            probabilities = answer.reading.probabilities
            yes_answers = sum(probabilities[key] >= jev.YES_THRESHOLD for key in AI7_KEYS)
        for statement in jev.STATEMENTS:
            value = reference[sample_id][statement.key]
            expected = expected_answer(value)
            if not answer.reading:
                row += [None, value, ""]
                continue
            probability = answer.reading.probabilities[statement.key]
            if expected is None:
                outcome = "not compared"
            else:
                outcome = "same" if (probability >= jev.YES_THRESHOLD) == expected else "different"
            row += [round(probability, 2), value, outcome]
        datasets.append(row + [yes_answers, answer.reading.input_tokens if answer.reading else None, answer.error])
        link = datasets.cell(row=datasets.max_row, column=2)
        link.hyperlink = answer.dataset.url
        link.style = "Hyperlink"
    finish_sheet(datasets, widths=(6, 46, 10, 12) + (10, 13, 13) * len(jev.STATEMENTS) + (12, 10, 40))
    for row in datasets.iter_rows(min_row=2):
        for cell in row:
            if cell.value == "different":
                cell.fill = DIFFERENT_FILL

    texts = workbook.create_sheet("Texts")
    texts.append(["ID", "Title", "Description", "Descriptions of resources", "Shortened"])
    for answer in answers:
        texts.append([answer.dataset.sample_id, answer.texts.title, answer.texts.description,
                      "\n".join(answer.texts.resource_descriptions), "yes" if answer.texts.shortened else "no"])
    finish_sheet(texts, widths=(6, 40, MAX_WIDTH + 30, MAX_WIDTH + 10, 11))

    statements = workbook.create_sheet("Statements")
    statements.append(["Statement", "Criterion", "Text of the statement", "Counts as true", "Counts as false"])
    for statement in jev.STATEMENTS:
        statements.append([statement.key, statement.criterion, statement.instructions, statement.when_true,
                           statement.when_false])
    finish_sheet(statements, widths=(14, 10, 50, MAX_WIDTH, MAX_WIDTH))
    workbook.save(path)


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m aiready.jev_trial",
        description="Asks Jev five statements about the texts of every dataset of the sample and sets the "
                    "answers next to the review of the study.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="write the requests in a file; ask nothing and need no key")
    parser.add_argument("--limit", type=int, metavar="N", help="ask only for the first N datasets of the sample")
    parser.add_argument("--out", type=Path, default=OUTPUT_FOLDER, metavar="FOLDER",
                        help="folder of the outputs (default: assessments)")
    parser.add_argument("--env-file", type=Path, default=ENV_FILE, metavar="FILE",
                        help="file with the line TYPESAFE_API_KEY=... (default: .env of the repository)")
    parser.add_argument("--pause", type=float, default=PAUSE_SECONDS, metavar="SECONDS",
                        help="pause between the requests of two datasets")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, environ=None) -> int:
    arguments = parse_arguments(argv)
    environ = os.environ if environ is None else environ
    address = model_address(environ, arguments.env_file)
    key = ""
    if not arguments.dry_run:
        try:
            key, address = model_settings(environ, arguments.env_file)
        except MissingKey as missing:
            print(missing)
            return 2
    datasets = sample_datasets(SAMPLE_FILE, SNAPSHOT, arguments.limit)
    arguments.out.mkdir(parents=True, exist_ok=True)

    if arguments.dry_run:
        requests_file = arguments.out / REQUESTS_FILE_NAME
        characters = write_requests(requests_file, datasets, address)
        print(f"Requests written for {len(datasets)} datasets: {characters:,} characters of texts, "
              f"{len(jev.STATEMENTS)} statements each. Nothing was sent.")
        print(f"Written: {requests_file}")
        return 0

    print(f"Model asked: {jev.MODEL} at {address}")
    access = browser_access(address)
    print("Calls from a web page: " + (f"allowed (Access-Control-Allow-Origin: {access})" if access
                                       else "not allowed by the answer of the address to the request of a browser"))
    answers: list[Answer] = []
    for index, dataset in enumerate(datasets):
        if index and arguments.pause > 0:
            time.sleep(arguments.pause)
        texts = jev.publisher_texts(dataset.record)
        body = jev.request_body(texts)
        reading, error = None, ""
        try:
            reading = jev.reading_in_reply(ask_model(address, key, body))
        except KeyRefused as refusal:
            print(f"The address of the model refused the key ({refusal}). Nothing was written.")
            return 2
        except RequestRejected as rejection:
            if not answers:
                print(f"The address of the model rejected the request ({rejection}). Nothing was written.")
                return 2
            error = str(rejection)
        except (ModelUnavailable, requests.RequestException, ValueError) as failure:
            error = str(failure) or type(failure).__name__
        answers.append(Answer(dataset, texts, body, reading, error))
        if reading:
            shown = ", ".join(f"{key_name} {value:.2f}" for key_name, value in reading.probabilities.items())
            print(f"{dataset.sample_id} {shown}")
        else:
            print(f"{dataset.sample_id} no answer: {error}")

    answered = [answer for answer in answers if answer.reading]
    tokens = sum(answer.reading.input_tokens for answer in answered)
    print(f"Answered: {len(answered)} of {len(answers)} datasets, {tokens:,} input tokens")
    reference = statement_reference([answer.dataset.sample_id for answer in answers], REFERENCE_FILE, METADATA_TABLE)
    probabilities = {answer.dataset.sample_id: answer.reading.probabilities for answer in answered}
    summaries = [statement_summary(statement.key, probabilities, reference) for statement in jev.STATEMENTS]
    print(f"Agreement with the reference (a probability of {jev.YES_THRESHOLD} or more counts as yes)")
    for item in summaries:
        print(f"  {item.key:<11}{item.agreed} of {item.compared}"
              f" | Jev yes, reference no: {', '.join(item.model_yes_only) or 'none'}"
              f" | Jev no, reference yes: {', '.join(item.reference_yes_only) or 'none'}")

    day = date.today()
    answers_file = arguments.out / f"jev_trial_{day.isoformat()}.json"
    workbook_file = arguments.out / f"jev_trial_{day.isoformat()}.xlsx"
    write_answers(answers_file, answers, address, access, day)
    write_workbook(workbook_file, answers, reference, summaries, address, access, day)
    print(f"Written: {workbook_file}")
    print(f"Written: {answers_file}")
    return 0 if len(answered) == len(answers) else 1


if __name__ == "__main__":
    raise SystemExit(main())
