"""Plain-language explanation of an assessment, in Greek or English.

Every scored result becomes a finding, an action and a short instruction for the list of
priorities. The case of a result is read from the reason that the check gives; the numbers
come from its measurements. A reason that matches no known case gets the general text of
its status. The texts are those of aiready/locales/<language>.json.
"""

import re
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date

from aiready.assessment import NOT_JUDGED, Assessment, ScoredResult
from aiready.criteria import Criterion, effort_levels, result_kind
from aiready.texts import Texts

# The nine checks in the two groups of the page, and the fourteen unscored criteria in the order of the checklist.
CHECK_GROUPS = (("description", ("M1", "M2", "M3", "M9", "Q5")), ("availability", ("M4", "M6", "M7", "Q6")))
CHECKLIST_FILES = ("Q1", "AI1", "Q2", "Q3", "Q4", "AI6")
CHECKLIST_JUDGEMENT = ("AI2", "M5", "M8", "M10", "AI3", "AI4", "AI5", "AI7")
CORE_ON_PAGE = ("M1", "M4", "Q6")     # the core criteria scored from the metadata, in the order of the page
STATUS_KEYS = {
    "met": "met", "partly met": "partly", "not met": "not_met", "not measured": "not_measured",
    NOT_JUDGED: "not_judged",
}
M2_PROPERTIES = ("keyword", "theme", "publisher", "contact", "spatial", "temporal", "frequency")
LISTED_VALUES = 5                     # free-text values quoted in a finding before the words "and more"
EXCEL_LEVEL = re.compile(r"vendor-specific format \.?(xlsx?|excel)\b", re.IGNORECASE)

# Case of a result, from the wording of the reason of scripts/04_metadata_checks.py: (pattern, case).
CASE_PATTERNS = {
    "M1": (
        (r"^no title", "no_title"),
        (r"^no description", "no_description"),
        (r"resources? without an access URL", "without_url"),
        (r"^description repeats the title", "repeats_title"),
        (r"^description of \d+ characters", "short_description"),
        (r"^title, description and access URLs present", "ok"),
    ),
    "M2": ((r"^\d+ of 7 present", "counted"),),
    "M3": (
        (r"^all from vocabularies", "all_vocab"),
        (r"^some free text", "some_free"),
        (r"^no vocabulary term", "no_vocab"),
        (r"^nothing declared", "nothing_declared"),
    ),
    "M4": (
        (r"^open licence on every resource", "open"),
        (r"^no licence", "none"),
        (r"^share-alike licence", "share_alike"),
        (r"^licence only as text", "text_only"),
        (r"^restrictive licence", "restrictive"),
        (r"^no resources", "no_resources"),
        (r"^licence missing on", "missing_some"),
        (r"^different licences", "different"),
        (r"^licence not classed", "unclassed"),
    ),
    "M6": (
        (r"^direct link to a file", "file"),
        (r"^API or data service", "api"),
        (r"^only a map view", "map_only"),
        (r"^only web pages", "pages_only"),
        (r"^no resources", "no_resources"),
        (r"^no address on any resource", "no_address"),
    ),
    "M7": (
        (r"^permanent identifier and stable addresses", "stable"),
        (r"^every resource through a changing address", "all_changing"),
        (r"^changing address on", "some_changing"),
        (r"^address missing on", "missing_some"),
        (r"^no resources", "no_resources"),
        (r"^no address on any resource", "no_address"),
    ),
    "M9": (
        (r"^category and Regulation", "full"),
        (r"^category without a reference", "category_only"),
        (r"^reference to Regulation", "regulation_only"),
        (r"^only the dataset type HVD", "type_only"),
        (r"^not marked", "not_judged"),
    ),
    "Q5": (
        (r"^no resources", "no_resources"),
        (r"declared as not updated, and the title or description states", "static_with_period"),
        (r"no upload date on the portal", "not_measurable"),
        (r"^[A-Z0-9_]+: last upload .* periods", "periodic"),
        (r"declared as not updated without a stated period: last upload", "static_no_period"),
        (r"^no period declared \(.*\): last upload", "no_frequency"),
    ),
    "Q6": (
        (r"^3 stars or more", "open"),
        (r"^2 stars", "vendor"),
        (r"^1 star", "unstructured"),
        (r"^undetermined", "undetermined"),
        (r"^no resources", "no_resources"),
    ),
}


@dataclass(frozen=True)
class Parts:
    """Texts of one result: what was found, what to do, and the short instruction for the priorities."""
    finding: str
    action: str = ""
    fix: str = ""


@dataclass(frozen=True)
class CheckExplanation:
    criterion_id: str
    title: str             # name of the check in everyday words
    group: str             # "description" or "availability"
    status: str            # status of the assessment, e.g. "partly met"
    status_label: str
    finding: str
    action: str            # empty when nothing is to be done
    fix_first: str         # empty unless the score is 0 or 1
    kind_label: str        # score by rule, or proposal
    core: bool
    effort_level: str      # Low, Medium or High when the score is 0 or 1, otherwise empty
    effort_label: str
    why: str               # why the check matters
    score: int | None
    reason: str            # reason of the check, as the script gives it
    rule: str              # rule of the criterion for this score in the language of the texts; empty without a score
    criterion_name: str    # name of the criterion in the study, from criteria.csv
    case: str
    generic: bool          # True when the general text of the status was used


@dataclass(frozen=True)
class FixItem:
    criterion_id: str
    action: str
    note: str              # core criterion and usual effort


@dataclass(frozen=True)
class ChecklistItem:
    criterion_id: str
    name: str              # name of the criterion in the application
    question: str
    if_not: str
    core: bool


@dataclass(frozen=True)
class PageModel:
    """Everything the page, or a report in plain language, says about one dataset."""
    language: str
    name: str
    title: str
    publisher: str
    url: str
    source_kind: str
    reference_date: date
    source_sentence: str
    marking_sentence: str
    strip_label: str
    headline: str
    summary_note: str
    group_note: str
    fix_first: tuple[FixItem, ...]
    checks: tuple[CheckExplanation, ...]
    checklist_files: tuple[ChecklistItem, ...]
    checklist_judgement: tuple[ChecklistItem, ...]
    criteria_version: str
    tool_version: str


def build_page_model(assessment: Assessment, texts: Texts, criteria: dict[str, Criterion]) -> PageModel:
    """Explanation of the whole assessment in the language of the texts."""
    by_id = {result.criterion_id: result for result in assessment.scored}
    checks = tuple(explain_check(by_id[code], texts, criteria) for _, codes in CHECK_GROUPS for code in codes)
    explained = {check.criterion_id: check for check in checks}
    counts = Counter(STATUS_KEYS[check.status] for check in checks)
    dataset = assessment.dataset
    source_key = "result.source.snapshot" if assessment.source.kind == "snapshot" else "result.source.portal"
    marking = ""
    if dataset.high_value_marked:
        categories = category_names(dataset.high_value_categories, texts)
        marking = (texts.text("result.marking", categories=categories) if categories
                   else texts.text("result.marking_no_category"))
    return PageModel(
        language=texts.language,
        name=dataset.name,
        title=dataset.title or dataset.name,
        publisher=dataset.publisher or texts.text("result.publisher_missing"),
        url=dataset.url,
        source_kind=assessment.source.kind,
        reference_date=assessment.source.date,
        source_sentence=texts.text(source_key, date=texts.date(assessment.source.date)),
        marking_sentence=marking,
        strip_label=texts.text(
            "summary.strip", total=len(checks), met=counts["met"], partly=counts["partly"],
            not_met=counts["not_met"], open=counts["not_measured"] + counts["not_judged"],
        ),
        headline=headline_text(counts, texts),
        summary_note=texts.text("summary.not_judged") if counts["not_judged"] else "",
        group_note=group_note_text(explained, texts),
        fix_first=tuple(
            FixItem(problem.criterion_id, explained[problem.criterion_id].fix_first,
                    fix_note(explained[problem.criterion_id], texts))
            for problem in assessment.problems
        ),
        checks=checks,
        checklist_files=checklist_items(CHECKLIST_FILES, texts, criteria),
        checklist_judgement=checklist_items(CHECKLIST_JUDGEMENT, texts, criteria),
        criteria_version=assessment.criteria_version,
        tool_version=assessment.tool_version,
    )


def explain_check(result: ScoredResult, texts: Texts, criteria: dict[str, Criterion]) -> CheckExplanation:
    """Explanation of one scored result."""
    code = result.criterion_id
    criterion = criteria[code]
    title = texts.text(f"check.{code}.title")
    status_key = STATUS_KEYS[result.status]
    below = result.score in (0, 1)
    case = case_of(result)
    parts = BUILDERS[code](case, result, texts) if case else None
    generic = parts is None
    if generic:
        general = "not_measured" if status_key == "not_judged" else status_key
        parts = Parts(
            texts.text(f"generic.finding.{general}"),
            texts.text("generic.action") if below else "",
            texts.text("generic.fix", title=title) if below else "",
        )
    efforts = effort_levels(criterion.typical_fix) if below else []
    return CheckExplanation(
        criterion_id=code,
        title=title,
        group=next(group for group, codes in CHECK_GROUPS if code in codes),
        status=result.status,
        status_label=texts.text(f"status.{status_key}"),
        finding=parts.finding,
        action=parts.action,
        fix_first=parts.fix if below else "",
        kind_label=texts.text("kind.by_rule" if result.kind == "by rule" else "kind.proposal"),
        core=result.core,
        effort_level=efforts[0] if efforts else "",
        effort_label=texts.text(f"effort.{efforts[0]}") if efforts else "",
        why=texts.text(f"check.{code}.why"),
        score=result.score,
        reason=result.reason,
        rule=texts.text(f"criterion.{code}.score_{result.score}") if result.score is not None else "",
        criterion_name=criterion.name,
        case=case or "",
        generic=generic,
    )


def case_of(result: ScoredResult) -> str | None:
    """Case of the result among those that have a text of their own, or None."""
    if result.status == NOT_JUDGED:
        return "not_judged"
    for pattern, case in CASE_PATTERNS[result.criterion_id]:
        if re.search(pattern, result.reason):
            return case
    return None


def headline_text(counts: Counter, texts: Texts) -> str:
    """How many of the judged checks are met, and what holds for the rest."""
    total = sum(counts.values()) - counts["not_judged"]
    met = counts["met"]
    if met == total:
        return texts.text("summary.all", total=total)
    first = texts.counted("summary.met", met, met=met, total=total)
    rest = [(key, counts[key]) for key in ("partly", "not_met", "not_measured") if counts[key]]
    if len(rest) == 1 and rest[0][0] == "partly":
        second = texts.counted("summary.rest_partly", rest[0][1], n=rest[0][1])
    else:
        listed = ", ".join(texts.counted(f"summary.part.{key}", count, n=count) for key, count in rest)
        second = texts.text("summary.rest_mixed", parts=listed)
    return f"{first} {second}"


def group_note_text(explained: dict[str, CheckExplanation], texts: Texts) -> str:
    """What the three core criteria of the page say about the group of the dataset. No group is named as a result."""
    names = {code: lower_initial(explained[code].title) for code in CORE_ON_PAGE}
    below = [names[code] for code in CORE_ON_PAGE if explained[code].score in (0, 1)]
    unmeasured = [names[code] for code in CORE_ON_PAGE if explained[code].score is None]
    sentences = [texts.text("group.intro")]
    if below:
        sentences.append(texts.counted("group.below", len(below), names=", ".join(below)))
    if unmeasured:
        sentences.append(texts.text("group.not_measured", names=", ".join(unmeasured)))
    if not below and not unmeasured:
        sentences.append(texts.text("group.all_met"))
    sentences.append(texts.text("group.rest"))
    return " ".join(sentences)


def fix_note(check: CheckExplanation, texts: Texts) -> str:
    notes = [texts.text("fix.core")] if check.core else []
    if check.effort_level:
        notes.append(texts.text(f"effort_long.{check.effort_level}"))
    return " ".join(notes)


def checklist_items(codes: tuple[str, ...], texts: Texts, criteria: dict[str, Criterion]) -> tuple[ChecklistItem, ...]:
    return tuple(
        ChecklistItem(code, criterion_title(code, texts), texts.text(f"checklist.{code}.question"),
                      texts.text(f"checklist.{code}.if_not"), criteria[code].core)
        for code in codes
    )


def criterion_title(code: str, texts: Texts) -> str:
    """Name of a criterion in the application: the name of its check, or its name in the checklist."""
    key = f"check.{code}.title"
    return texts.text(key) if texts.has(key) else texts.text(f"checklist.{code}.name")


def level_key(code: str) -> str:
    """Letters of the code of a criterion, which name its level in the study: Q, M or AI."""
    return re.match(r"[A-Z]+", code).group()


def criterion_kind(criterion: Criterion) -> str:
    """How the application treats a criterion: 'by rule', 'proposal', 'files' or 'judgement'.

    The last two are the criteria of the checklist, which need the files of the dataset or the judgement of a person.
    """
    if criterion.id in CHECKLIST_FILES:
        return "files"
    if criterion.id in CHECKLIST_JUDGEMENT:
        return "judgement"
    return result_kind(criterion)


def lower_initial(text: str) -> str:
    return text[:1].lower() + text[1:]


def licence_label(code: str) -> str:
    """Licence term in readable form: CC_BY_4_0 becomes CC BY 4.0."""
    return re.sub(r"(\d) (\d)", r"\1.\2", code.replace("_", " "))


def category_names(categories: str, texts: Texts) -> str:
    """High-value categories in the language of the texts; an unknown category stays as the metadata give it."""
    names = [name for name in categories.split("; ") if name]
    return ", ".join(texts.text(f"hvd.{name}") if texts.has(f"hvd.{name}") else name for name in names)


def quoted_values(values: str, texts: Texts) -> str:
    """The first free-text values in quotation marks, followed by the words "and more" when some are left out."""
    items = [value for value in values.split("; ") if value]
    listed = ", ".join(texts.quoted(value) for value in items[:LISTED_VALUES])
    return f"{listed}, {texts.text('common.and_more')}" if len(items) > LISTED_VALUES else listed


def no_resources_parts(texts: Texts) -> Parts:
    return Parts(texts.text("common.no_resources"), texts.text("common.no_resources_action"),
                 texts.text("common.no_resources_fix"))


def no_address_parts(texts: Texts) -> Parts:
    return Parts(texts.text("common.no_address"), texts.text("common.address_action"), texts.text("common.address_fix"))


def m1_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    without_files = measures["resources"] == 0
    describe = (texts.text("m1.action_description"), texts.text("m1.fix_description"))
    if case == "ok":
        return Parts(texts.text("m1.ok_no_resources" if without_files else "m1.ok"))
    if case == "no_title":
        parts = Parts(texts.text("m1.no_title"), texts.text("m1.action_title"), texts.text("m1.fix_title"))
    elif case == "no_description":
        parts = Parts(texts.text("m1.no_description"), *describe)
    elif case == "without_url":
        count = measures["resources_without_url"]
        finding = texts.counted("m1.without_url", count, n=texts.number(count), resources=texts.number(measures["resources"]))
        parts = Parts(finding, texts.text("common.address_action"), texts.text("common.address_fix"))
    elif case == "repeats_title":
        parts = Parts(texts.text("m1.repeats_title"), *describe)
    else:
        minimum = re.search(r"minimum (\d+)", result.reason)
        if not minimum:
            return None
        finding = texts.text("m1.short_description", chars=texts.number(measures["description_chars"]),
                             minimum=minimum.group(1))
        parts = Parts(finding, *describe)
    if without_files:
        parts = replace(parts, finding=f"{parts.finding} {texts.text('common.no_resources')}")
    return parts


def m2_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    present = measures["present"]
    if present == len(M2_PROPERTIES):
        return Parts(texts.text("m2.all"))
    missing = ", ".join(texts.text(f"m2.name.{key}") for key in M2_PROPERTIES if not measures[key])
    if present == 0:
        finding = texts.text("m2.none", missing=missing)
    else:
        finding = texts.counted("m2.partial", present, present=present, missing=missing)
    if result.score in (0, 1):
        return Parts(finding, texts.text("m2.action"), texts.text("m2.fix"))
    return Parts(finding)


def m3_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    free_formats = measures["resources_with_format"] - measures["resources_vocab"]
    free_terms = measures["theme_vocab"] is False or measures["frequency_vocab"] is False
    actions = []
    if free_formats:
        actions.append(texts.text("m3.action_formats"))
    if free_terms:
        actions.append(texts.text("m3.action_terms"))
    fix = texts.text("m3.fix_formats" if free_formats else "m3.fix_terms")
    if case == "all_vocab":
        return Parts(texts.text("m3.all_vocab"))
    if case == "nothing_declared":
        return Parts(texts.text("m3.nothing_declared"), texts.text("m3.action_declare"), texts.text("m3.fix_terms"))
    if case == "no_vocab":
        return Parts(texts.text("m3.no_vocab"), " ".join(actions), fix)
    findings = []
    if free_formats:
        findings.append(texts.text(
            "m3.free_formats", n=texts.number(free_formats), with_format=texts.number(measures["resources_with_format"]),
            values=quoted_values(measures["free_text"], texts),
        ))
    if measures["theme_vocab"] is False:
        findings.append(texts.text("m3.free_theme"))
    if measures["frequency_vocab"] is False:
        findings.append(texts.text("m3.free_frequency"))
    if not findings:
        return None
    return Parts(" ".join(findings), " ".join(actions), fix)


def m4_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    resources = measures["resources"]
    labels = [licence_label(code) for code in measures["licences"].split("; ") if code]
    first = labels[0] if labels else ""
    declare = (texts.text("m4.action_declare"), texts.text("m4.fix_declare"))
    if case == "open":
        return Parts(texts.counted("m4.open", resources, licence=first))
    if case in ("none", "text_only"):
        return Parts(texts.text(f"m4.{case}"), *declare)
    if case == "missing_some":
        count = resources - measures["resources_with_licence"]
        finding = texts.counted("m4.missing_some", count, n=texts.number(count), resources=texts.number(resources))
        return Parts(finding, *declare)
    if case == "no_resources":
        return no_resources_parts(texts)
    fields = {"licence": first} if case in ("share_alike", "unclassed") else {"licences": ", ".join(labels)}
    return Parts(texts.text(f"m4.{case}", **fields), texts.text(f"m4.action_{case}"), texts.text(f"m4.fix_{case}"))


def m6_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    resources = measures["resources"]
    if case == "file":
        files = measures["file"]
        if files == resources:
            finding = texts.counted("m6.file_all", resources, resources=texts.number(resources))
        else:
            finding = texts.counted("m6.file_some", files, n=texts.number(files), resources=texts.number(resources))
        if "not verified" in result.reason:
            finding = f"{finding} {texts.text('m6.note_unverified')}"
        return Parts(finding)
    if case == "api":
        return Parts(texts.text("m6.api", n=texts.number(measures["api"]), resources=texts.number(resources)))
    if case == "map_only":
        return Parts(texts.text("m6.map_only"), texts.text("m6.action_map"), texts.text("m6.fix_map"))
    if case == "pages_only":
        return Parts(texts.text("m6.pages_only"), texts.text("m6.action_pages"), texts.text("m6.fix_pages"))
    return no_resources_parts(texts) if case == "no_resources" else no_address_parts(texts)


def m7_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    resources = measures["resources"]
    changing = (texts.text("m7.action_changing"), texts.text("m7.fix_changing"))
    if case == "stable":
        if measures["portal"] == resources:
            return Parts(texts.counted("m7.stable_portal", resources, resources=texts.number(resources)))
        return Parts(texts.text("m7.stable"))
    if case == "all_changing":
        return Parts(texts.text("m7.all_changing"), *changing)
    if case == "some_changing":
        count = measures["token"] + measures["shortener"] + measures["redirect"]
        finding = texts.counted("m7.some_changing", count, n=texts.number(count), resources=texts.number(resources))
        return Parts(finding, *changing)
    if case == "missing_some":
        count = measures["without_address"]
        finding = texts.counted("m7.missing_some", count, n=texts.number(count), resources=texts.number(resources))
        return Parts(finding, texts.text("common.address_action"), texts.text("common.address_fix"))
    return no_resources_parts(texts) if case == "no_resources" else no_address_parts(texts)


def m9_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    if case == "not_judged":
        return Parts(texts.text("m9.not_judged"), texts.text("m9.action_not_judged"))
    categories = category_names(result.measurements["categories"], texts)
    if case == "full":
        return Parts(texts.text("m9.full", categories=categories))
    complete = (texts.text("m9.action_complete"), texts.text("m9.fix_complete"))
    if case == "category_only":
        return Parts(texts.text("m9.category_only", categories=categories), *complete)
    return Parts(texts.text(f"m9.{case}"), *complete)


def q5_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    if case == "no_resources":
        return Parts(texts.text("common.no_resources"), texts.text("common.no_resources_action"))
    if case == "static_with_period":
        return Parts(texts.text("q5.static_with_period"))
    group = measures["frequency_group"]
    if group == "periodic":
        code = measures["frequency"]
        known = f"q5.frequency.{code}"
        frequency = texts.text(known) if texts.has(known) else texts.text("q5.frequency.other", code=code)
        lead = texts.text("q5.lead_periodic", frequency=frequency)
    else:
        lead = texts.text("q5.lead_static" if group == "not updated" else "q5.lead_none")
    if case == "not_measurable":
        return Parts(f"{lead} {texts.text('q5.not_measurable')}", texts.text("q5.action_check"))
    age = measures["age_days"]
    if age is None or result.score is None:
        return None
    days = texts.counted("common.days", age, n=texts.number(age))
    if case == "periodic":
        finding = f"{lead} {texts.text({2: 'q5.on_time', 1: 'q5.late', 0: 'q5.very_late'}[result.score], days=days)}"
        if result.score == 2:
            return Parts(finding)
        return Parts(finding, texts.text("q5.action_update"), texts.text("q5.fix_update"))
    finding = f"{lead} {texts.text('q5.recent' if result.score == 1 else 'q5.old', days=days)}"
    kind = "period" if case == "static_no_period" else "frequency"
    return Parts(finding, texts.text(f"q5.action_{kind}"), texts.text(f"q5.fix_{kind}"))


def q6_parts(case: str, result: ScoredResult, texts: Texts) -> Parts | None:
    measures = result.measurements
    resources = measures["resources"]
    if case == "no_resources":
        return Parts(texts.text("common.no_resources"), texts.text("common.no_resources_action"))
    if case == "undetermined":
        return Parts(texts.text("q6.undetermined"), texts.text("q6.action_declare"))
    if case == "open":
        return Parts(texts.text("q6.open", n=texts.number(measures["stars_3"]), resources=texts.number(resources)))
    fix = texts.text("q6.fix_open")
    if case == "vendor":
        levels = [level for level in measures["levels"].split("; ") if level]
        if measures["stars_2"] == resources and levels and all(EXCEL_LEVEL.search(level) for level in levels):
            finding = texts.counted("q6.excel_only", resources, resources=texts.number(resources))
            parts = Parts(finding, texts.text("q6.action_open_excel"), fix)
        else:
            finding = texts.text("q6.vendor", n=texts.number(measures["stars_2"]), resources=texts.number(resources))
            parts = Parts(finding, texts.text("q6.action_open"), fix)
    else:
        parts = Parts(texts.text("q6.unstructured"), texts.text("q6.action_structured"), fix)
    if measures["provisional"]:
        count = measures["undetermined"]
        note = texts.counted("q6.note_provisional", count, n=texts.number(count))
        parts = replace(parts, finding=f"{parts.finding} {note}")
    return parts


BUILDERS = {
    "M1": m1_parts, "M2": m2_parts, "M3": m3_parts, "M4": m4_parts, "M6": m6_parts, "M7": m7_parts,
    "M9": m9_parts, "Q5": q5_parts, "Q6": q6_parts,
}
