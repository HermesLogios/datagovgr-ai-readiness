"""Assessment of one dataset: the scored criteria, the criteria left to people, and the problems found.

Nine criteria are scored from the metadata. The other fourteen need the files of the dataset
or human judgement and are listed without a score. No group (Ready, Almost ready, Not yet) is
assigned: the group needs all six core criteria, and three of them are not scored here.
"""

from dataclasses import dataclass
from datetime import date

from aiready import __version__
from aiready.criteria import (
    CRITERIA_VERSION,
    EFFORT_ORDER,
    NEEDS_FILES,
    Criterion,
    effort_levels,
    result_kind,
)
from aiready.metadata_checks import CHECK_IDS, CheckOutput, visible_text

DATASET_PAGE = "https://data.gov.gr/dataset/"
STATUS_BY_SCORE = {2: "met", 1: "partly met", 0: "not met", None: "not measured"}
NOT_JUDGED = "not judged automatically"
STATUS_ORDER = ("met", "partly met", "not met", "not measured", NOT_JUDGED)
UNMARKED_REASON = (
    "no high-value marking in the metadata; the marking is missing if the content falls under the Annex of "
    "Regulation (EU) 2023/138, otherwise the criterion does not apply"
)


@dataclass(frozen=True)
class Source:
    kind: str          # "portal" or "snapshot"
    description: str   # where and when the metadata were read
    date: date         # reference date of the checks


@dataclass(frozen=True)
class DatasetSummary:
    id: str
    name: str
    title: str
    publisher: str
    url: str
    high_value_marked: bool
    high_value_categories: str


@dataclass(frozen=True)
class ScoredResult:
    criterion_id: str
    name: str
    kind: str                 # "by rule" or "proposal"
    score: int | None
    status: str
    reason: str
    core: bool
    typical_fix: str
    check_score: int | None   # score returned by the check of the script, before the rule on unmarked datasets
    measurements: dict


@dataclass(frozen=True)
class UnscoredCriterion:
    criterion_id: str
    name: str
    question: str
    needs: str                # "the files" or "judgement"
    core: bool
    applies_to: str


@dataclass(frozen=True)
class Problem:
    criterion_id: str
    name: str
    score: int
    reason: str
    typical_fix: str
    effort: tuple[str, ...]
    core: bool


@dataclass(frozen=True)
class CoreSummary:
    scores: dict
    below: tuple[str, ...]
    not_measured: tuple[str, ...]
    ready_ruled_out: bool
    message: str


@dataclass(frozen=True)
class Assessment:
    dataset: DatasetSummary
    source: Source
    criteria_version: str
    tool_version: str
    scored: tuple[ScoredResult, ...]
    unscored: tuple[UnscoredCriterion, ...]
    problems: tuple[Problem, ...]
    core: CoreSummary

    @property
    def scored_count(self) -> int:
        """Number of criteria that received a score."""
        return sum(1 for result in self.scored if result.score is not None)

    def status_counts(self) -> dict[str, int]:
        """Number of scored criteria per status, in the order of STATUS_ORDER, without the empty ones."""
        counts = {status: sum(1 for result in self.scored if result.status == status) for status in STATUS_ORDER}
        return {status: count for status, count in counts.items() if count}


def build_assessment(
    record: dict,
    criteria: dict[str, Criterion],
    check_outputs: dict[str, CheckOutput],
    source: Source,
) -> Assessment:
    """Puts together the assessment of a dataset record from the outputs of the metadata checks."""
    scored = tuple(scored_result(criteria[code], check_outputs[code]) for code in CHECK_IDS)
    unscored = tuple(
        UnscoredCriterion(
            criterion_id=criterion.id,
            name=criterion.name,
            question=criterion.question,
            needs="the files" if criterion.id in NEEDS_FILES else "judgement",
            core=criterion.core,
            applies_to=criterion.applies_to,
        )
        for criterion in criteria.values()
        if criterion.id not in CHECK_IDS
    )
    marking = check_outputs["M9"].measurements
    organization = record.get("organization") or {}
    name = record.get("name") or ""
    dataset = DatasetSummary(
        id=record.get("id") or "",
        name=name,
        title=visible_text(record.get("title")),
        publisher=visible_text(organization.get("title")),
        url=DATASET_PAGE + name,
        high_value_marked=bool(marking.get("marked")),
        high_value_categories=marking.get("categories") or "",
    )
    return Assessment(
        dataset=dataset,
        source=source,
        criteria_version=CRITERIA_VERSION,
        tool_version=__version__,
        scored=scored,
        unscored=unscored,
        problems=problems_in_order(scored),
        core=core_summary(scored, criteria),
    )


def scored_result(criterion: Criterion, output: CheckOutput) -> ScoredResult:
    """Result of one check. A dataset without any high-value marking gets no score on M9:
    whether its content is high-value cannot be judged from the metadata."""
    score, status, reason = output.score, STATUS_BY_SCORE[output.score], output.reason
    if criterion.id == "M9" and not output.measurements.get("marked"):
        score, status, reason = None, NOT_JUDGED, UNMARKED_REASON
    return ScoredResult(
        criterion_id=criterion.id,
        name=criterion.name,
        kind=result_kind(criterion),
        score=score,
        status=status,
        reason=reason,
        core=criterion.core,
        typical_fix=criterion.typical_fix,
        check_score=output.score,
        measurements=output.measurements,
    )


def problems_in_order(scored: tuple[ScoredResult, ...]) -> tuple[Problem, ...]:
    """Checks below score 2, core criteria first, then by the effort of the typical fix, then in the order of the checks."""
    problems = [
        Problem(
            criterion_id=result.criterion_id,
            name=result.name,
            score=result.score,
            reason=result.reason,
            typical_fix=result.typical_fix,
            effort=tuple(effort_levels(result.typical_fix)),
            core=result.core,
        )
        for result in scored
        if result.score in (0, 1)
    ]

    def priority(problem: Problem) -> tuple[int, int, int]:
        effort = EFFORT_ORDER.index(problem.effort[0]) if problem.effort else len(EFFORT_ORDER)
        return (0 if problem.core else 1, effort, CHECK_IDS.index(problem.criterion_id))

    return tuple(sorted(problems, key=priority))


def core_summary(scored: tuple[ScoredResult, ...], criteria: dict[str, Criterion]) -> CoreSummary:
    """What the core criteria scored from the metadata say about the group of the dataset."""
    by_id = {result.criterion_id: result for result in scored}
    visible = [criterion.id for criterion in criteria.values() if criterion.core and criterion.id in by_id]
    others = [criterion.id for criterion in criteria.values() if criterion.core and criterion.id not in by_id]
    scores = {code: by_id[code].score for code in visible}
    below = tuple(code for code in visible if scores[code] in (0, 1))
    not_measured = tuple(code for code in visible if scores[code] is None)
    sentences = []
    if below:
        verb = "reaches" if len(below) == 1 else "reach"
        sentences.append(f'"Ready" is ruled out until {listed(below)} {verb} score 2.')
    if not_measured:
        sentences.append(f"{listed(not_measured)} could not be measured from the metadata.")
    if not below and not not_measured:
        sentences.append(f"{listed(visible)} score 2.")
    sentences.append(
        f"The other core criteria ({listed(others)}) need the files or human judgement and are not scored by this tool."
    )
    return CoreSummary(
        scores=scores,
        below=below,
        not_measured=not_measured,
        ready_ruled_out=bool(below),
        message=" ".join(sentences),
    )


def listed(items) -> str:
    """Items as an English list: 'Q6', 'Q6 and M1', 'Q6, M1 and M4'."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]
