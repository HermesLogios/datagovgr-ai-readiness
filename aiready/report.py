"""Reports of an assessment: text for the console, Markdown and JSON."""

import dataclasses
import json
from datetime import date
from pathlib import Path

from aiready.assessment import Assessment

FORMATS = ("md", "json")
NOTES = (
    "The scores come from the metadata checks of the study (scripts/04_metadata_checks.py) and the criteria from "
    "criteria/criteria.csv. A result marked 'proposal' is confirmed with a look at the dataset. The criteria that "
    "are not scored need the files of the dataset or human judgement. The result is indicative."
)


def counts_text(assessment: Assessment) -> str:
    """Status counts in words, e.g. '5 met, 4 partly met'."""
    return ", ".join(f"{count} {status}" for status, count in assessment.status_counts().items())


def score_text(score: int | None) -> str:
    return "-" if score is None else str(score)


def reason_text(result) -> str:
    """Reason of a result; a result without a score starts with its status."""
    return result.reason if result.score is not None else f"{result.status}: {result.reason}"


def scope_text(entry) -> str:
    """What an unscored criterion needs, with the datasets it applies to when these are not all."""
    scope = "" if entry.applies_to == "all" else f" ({entry.applies_to} datasets only)"
    return f"needs {entry.needs}{scope}"


def core_scores_text(assessment: Assessment) -> str:
    return ", ".join(
        f"{code} {'not measured' if score is None else score}" for code, score in assessment.core.scores.items()
    )


def console_text(assessment: Assessment) -> str:
    """Summary of the assessment for the console."""
    dataset = assessment.dataset
    name_width = max(len(result.name) for result in assessment.scored)
    lines = [
        dataset.title or dataset.name,
        f"Publisher: {dataset.publisher or 'not stated'}",
        dataset.url,
        f"Metadata: {assessment.source.description}",
        f"Criteria version {assessment.criteria_version}, tool version {assessment.tool_version}",
        "",
        f"Scored from the metadata: {assessment.scored_count} of {len(assessment.scored)} criteria"
        f" ({counts_text(assessment)})",
    ]
    for result in assessment.scored:
        lines.append(
            f"  {result.criterion_id:<4}{result.name:<{name_width}}  {score_text(result.score):<2}"
            f"{result.kind:<9} {reason_text(result)}"
        )
    lines += ["", "Core criteria", f"  {core_scores_text(assessment)}", f"  {assessment.core.message}"]
    lines += ["", "Problems and typical fixes"]
    if not assessment.problems:
        lines.append("  None found by the checks of the metadata.")
    for order, problem in enumerate(assessment.problems, start=1):
        core = ", core criterion" if problem.core else ""
        lines += [
            f"  {order}. {problem.criterion_id} {problem.name}: score {problem.score}{core}",
            f"     Problem: {problem.reason}",
            f"     Typical fix: {problem.typical_fix}",
        ]
    lines += ["", f"Not scored by this tool: {len(assessment.unscored)} criteria"]
    unscored_width = max(len(entry.name) for entry in assessment.unscored)
    for entry in assessment.unscored:
        lines.append(f"  {entry.criterion_id:<5}{entry.name:<{unscored_width}}  {scope_text(entry)}")
    return "\n".join(lines) + "\n"


def cell(value) -> str:
    """Text of a Markdown table cell: backslashes and column separators are escaped, line breaks become spaces."""
    return " ".join(str(value).replace("\\", "\\\\").replace("|", "\\|").split())


def table(header: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(cell(value) for value in row) + " |" for row in rows]
    return lines


def markdown_text(assessment: Assessment) -> str:
    """Report of the assessment in Markdown."""
    dataset = assessment.dataset
    marking = f"yes ({dataset.high_value_categories})" if dataset.high_value_marked else "none"
    lines = [
        f"# {dataset.title or dataset.name}",
        "",
        f"- Publisher: {dataset.publisher or 'not stated'}",
        f"- Address: {dataset.url}",
        f"- Metadata: {assessment.source.description}",
        f"- High-value marking: {marking}",
        f"- Criteria version {assessment.criteria_version}, tool version {assessment.tool_version}",
        "",
        "## Scored from the metadata",
        "",
        f"{assessment.scored_count} of {len(assessment.scored)} criteria scored: {counts_text(assessment)}.",
        "",
    ]
    lines += table(
        ["Criterion", "Name", "Score", "Status", "Result", "Reason"],
        [
            [result.criterion_id, result.name, score_text(result.score), result.status, result.kind, result.reason]
            for result in assessment.scored
        ],
    )
    lines += ["", "## Core criteria", "", f"{core_scores_text(assessment)}. {assessment.core.message}", ""]
    lines += ["## Problems and typical fixes", ""]
    if assessment.problems:
        lines += table(
            ["Order", "Criterion", "Name", "Score", "Core", "Problem", "Typical fix"],
            [
                [
                    order,
                    problem.criterion_id,
                    problem.name,
                    problem.score,
                    "yes" if problem.core else "no",
                    problem.reason,
                    problem.typical_fix,
                ]
                for order, problem in enumerate(assessment.problems, start=1)
            ],
        )
    else:
        lines.append("None found by the checks of the metadata.")
    lines += ["", "## Not scored by this tool", ""]
    lines += table(
        ["Criterion", "Name", "Question", "Needs"],
        [[entry.criterion_id, entry.name, entry.question, scope_text(entry)] for entry in assessment.unscored],
    )
    lines += ["", NOTES, ""]
    return "\n".join(lines)


def json_text(assessment: Assessment) -> str:
    """Complete assessment as JSON, with the measurements of every check."""
    content = dataclasses.asdict(assessment)
    content["status_counts"] = assessment.status_counts()
    content["scored_count"] = assessment.scored_count
    return json.dumps(content, ensure_ascii=False, indent=2, default=json_value) + "\n"


def json_value(value):
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"value of type {type(value).__name__} has no JSON form")


def write_reports(assessment: Assessment, out_dir: Path, formats=FORMATS) -> list[Path]:
    """Writes the reports in the given formats and returns their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{assessment.dataset.name}_{assessment.source.date.isoformat()}"
    texts = {"md": markdown_text, "json": json_text}
    written = []
    for name in formats:
        path = out_dir / f"{stem}.{name}"
        path.write_text(texts[name](assessment), encoding="utf-8", newline="\n")
        written.append(path)
    return written
