"""HTML of the public pages: home, result of a check, guide and terms of use.

Every text is escaped before it enters the HTML: titles, publishers and values of the metadata
come from the portal and are shown as plain text. A status is always given by a word, a shape
and a colour. The pages carry no inline script or style and load only files of the site.
"""

from html import escape

from aiready.plain_language import STATUS_KEYS, CheckExplanation, ChecklistItem, PageModel
from aiready.texts import DEFAULT_LANGUAGE, LANGUAGES, Texts
from web.icons import line_icon, mark_icon, status_icon

REPOSITORY_URL = "https://github.com/HermesLogios/datagovgr-ai-readiness"
PAGE_FOLDERS = {"home": "", "guide": "guide/", "terms": "terms/"}
PAGE_TITLES = {"guide": "guide.title", "terms": "terms.title", "missing": "missing.title"}
MISSING_PAGE = "missing"
COUNTED_STATUSES = ("met", "partly", "not_met", "not_measured", "not_judged")
LEGEND_STATUSES = ("met", "partly", "not_met", "not_measured")
STEPS = (1, 2, 3, 4)
TERMS_SECTIONS = ("what", "result", "use", "data", "personal", "licences", "liability", "contact")
GLOSSARY = ("metadata", "format", "licence", "hvd")
EFFORT_CLASSES = {"Low": "low", "Medium": "medium", "High": "high"}
REPORT_FORMATS = (("xlsx", "download.excel", "file-spreadsheet"), ("md", "download.markdown", "file-text"),
                  ("json", "download.json", "braces"))
NEW_TAB = 'target="_blank" rel="noopener noreferrer"'
FONT_FILES = ("manrope-greek-wght-normal.woff2", "manrope-latin-wght-normal.woff2")


def page_path(page: str, language: str) -> str:
    """Address of a page: Greek pages at the root of the site, English pages under /en/."""
    if language not in LANGUAGES:
        raise ValueError(f"unknown language: {language}")
    return ("/" if language == DEFAULT_LANGUAGE else f"/{language}/") + PAGE_FOLDERS[page]


def document_html(page: str, texts: Texts, main: str, *, criteria_version: str, assets_version: str = "",
                  indexing: bool = False, settings: dict[str, str] | None = None) -> str:
    """Whole document of a page: head, header, the main part and the footer.

    The settings become data attributes of the body, where the script of the page reads them.
    """
    name = texts.text("app.name")
    title = f"{texts.text(PAGE_TITLES[page])} | {name}" if page in PAGE_TITLES else name
    linked_page = "home" if page == MISSING_PAGE else page
    version = f"?v={escape(assets_version)}" if assets_version else ""
    alternates = "".join(
        f'<link rel="alternate" hreflang="{language}" href="{page_path(linked_page, language)}">\n' for language in LANGUAGES
    )
    robots = "" if indexing and page != MISSING_PAGE else '<meta name="robots" content="noindex">\n'
    fonts = "".join(
        f'<link rel="preload" href="/assets/fonts/{name}" as="font" type="font/woff2" crossorigin>\n' for name in FONT_FILES
    )
    attributes = "".join(f' data-{key}="{escape(value)}"' for key, value in (settings or {}).items())
    return (
        f'<!DOCTYPE html>\n<html lang="{texts.language}">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{escape(title)}</title>\n'
        f'<meta name="description" content="{escape(texts.text("home.lead"))}">\n{robots}{alternates}'
        f'<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n{fonts}'
        f'<link rel="stylesheet" href="/assets/style.css{version}">\n'
        f'<script type="module" src="/assets/app.js{version}"></script>\n</head>\n'
        f'<body{attributes}>\n<a class="skip-link" href="#main">{escape(texts.text("nav.skip"))}</a>\n'
        f'{header_html(texts, page)}\n<main id="main">{main}</main>\n{footer_html(texts, criteria_version)}\n</body>\n</html>\n'
    )


def header_html(texts: Texts, page: str) -> str:
    """Name of the tool, the two other pages and the switch between the languages."""
    language = texts.language
    linked_page = "home" if page == MISSING_PAGE else page

    def page_link(target: str, key: str) -> str:
        current = ' aria-current="page"' if target == page else ""
        return f'<a href="{page_path(target, language)}"{current}>{escape(texts.text(key))}</a>'

    def language_link(other: str) -> str:
        current = ' aria-current="true"' if other == language else ""
        return (f'<a href="{page_path(linked_page, other)}" lang="{other}" hreflang="{other}"{current}>'
                f'{escape(texts.text(f"language.{other}"))}</a>')

    return (
        f'<header class="site-header"><div class="wrap site-header-inner">'
        f'<a class="brand" href="{page_path("home", language)}">{mark_icon()}<span>{escape(texts.text("app.name"))}</span></a>'
        f'<nav class="site-nav" aria-label="{escape(texts.text("nav.pages"))}">'
        f'{page_link("guide", "nav.how")}{page_link("terms", "nav.terms")}</nav>'
        f'<div class="language" role="group" aria-label="{escape(texts.text("nav.language"))}">'
        f'{"".join(language_link(other) for other in LANGUAGES)}</div></div></header>'
    )


def footer_html(texts: Texts, criteria_version: str) -> str:
    return (
        f'<footer class="site-footer"><div class="wrap site-footer-inner">'
        f'<p>{escape(texts.text("footer.credit", criteria_version=criteria_version))}</p>'
        f'<ul class="footer-links"><li><a href="{REPOSITORY_URL}" {NEW_TAB}>{line_icon("code-xml")}'
        f'{escape(texts.text("footer.source"))}</a></li>'
        f'<li><a href="{page_path("terms", texts.language)}">{escape(texts.text("footer.terms"))}</a></li></ul>'
        f"</div></footer>"
    )


def meter_html(model: PageModel) -> str:
    """One cell per check, in the two groups of the page, with the counts in words for screen readers."""
    groups = list(dict.fromkeys(check.group for check in model.checks))
    cells = '<span class="meter-gap"></span>'.join(
        '<span class="meter-group">'
        + "".join(f'<span class="meter-cell meter-cell--{STATUS_KEYS[check.status]}"></span>'
                  for check in model.checks if check.group == group)
        + "</span>"
        for group in groups
    )
    return f'<div class="meter" role="img" aria-label="{escape(model.strip_label)}">{cells}</div>'


def check_rows_html(model: PageModel, texts: Texts, linked: bool) -> str:
    """Names of the nine checks with the icon of their status, under the title of their group."""
    parts = []
    for group in dict.fromkeys(check.group for check in model.checks):
        rows = []
        for check in model.checks:
            if check.group != group:
                continue
            row = f"{status_icon(STATUS_KEYS[check.status])}<span>{escape(check.title)}</span>"
            if linked:
                rows.append(f'<li><a href="#check-{escape(check.criterion_id)}">{row}</a></li>')
            else:
                rows.append(f'<span class="preview-row">{row}</span>')
        title = escape(texts.text(f"checks.group.{group}"))
        if linked:
            parts.append(f'<p class="index-group">{title}</p><ol class="index-checks">{"".join(rows)}</ol>')
        else:
            parts.append(f'<span class="index-group">{title}</span>{"".join(rows)}')
    return "".join(parts)


def index_html(model: PageModel, texts: Texts) -> str:
    """Summary of a result that also leads to each of its parts."""
    statuses = [STATUS_KEYS[check.status] for check in model.checks]
    counts = "".join(
        f'<li>{status_icon(status)}<span><strong>{statuses.count(status)}</strong> {escape(texts.text(f"status.{status}"))}</span></li>'
        for status in COUNTED_STATUSES if status in statuses
    )
    sections = "".join(
        f'<li><a href="#{target}">{escape(texts.text(key))}</a></li>'
        for target, key in (("fixes", "fix.title"), ("checklist", "checklist.title"), ("report-files", "download.title"))
    )
    title = escape(texts.text("index.title"))
    return (
        f'<nav class="index" aria-label="{title}"><p class="index-title">{title}</p>{meter_html(model)}'
        f'<ul class="index-counts">{counts}</ul>{check_rows_html(model, texts, linked=True)}'
        f'<ul class="index-sections">{sections}</ul></nav>'
    )


def preview_html(model: PageModel, texts: Texts) -> str:
    """Small picture of the result of the example; the link with the same target stands in the text next to it."""
    return (
        f'<a class="preview" href="?example=1" data-example aria-hidden="true" tabindex="-1">'
        f'<span class="preview-label">{escape(texts.text("home.preview"))}</span>'
        f'<strong class="preview-title">{escape(model.title)}</strong>'
        f'<span class="preview-publisher">{escape(model.publisher)}</span>'
        f'{meter_html(model).replace("<div", "<span").replace("</div>", "</span>")}'
        f"{check_rows_html(model, texts, linked=False)}</a>"
    )


def check_form_html(texts: Texts) -> str:
    return (
        f'<form class="check-form" id="check-form" method="get" novalidate>'
        f'<label for="dataset-address">{escape(texts.text("form.label"))}</label>'
        f'<span class="field">{line_icon("link")}'
        f'<input id="dataset-address" name="dataset" type="text" inputmode="url" autocomplete="off" autocapitalize="none" '
        f'spellcheck="false" placeholder="{escape(texts.text("form.placeholder"))}">'
        f'<button type="submit" class="button button--primary">{escape(texts.text("form.submit"))}</button></span></form>'
    )


def steps_html(texts: Texts) -> str:
    steps = "".join(
        f'<li><span class="step-number">{number}</span><h3>{escape(texts.text(f"how.{number}.title"))}</h3>'
        f'<p>{escape(texts.text(f"how.{number}.text"))}</p></li>'
        for number in STEPS
    )
    return f'<ol class="steps">{steps}</ol>'


def legend_html(texts: Texts) -> str:
    rows = "".join(
        f'<p class="legend-row">{status_icon(status)}<span><strong>{escape(texts.text(f"status.{status}"))}.</strong> '
        f'{escape(texts.text(f"legend.{status}"))}</span></p>'
        for status in LEGEND_STATUSES
    )
    return f'<div class="legend"><h2>{escape(texts.text("legend.title"))}</h2>{rows}</div>'


def home_main_html(texts: Texts, example: PageModel) -> str:
    """Form of the check, the place of the result, and what the tool does and does not do."""
    notes = "".join(f"<li>{escape(texts.text(f'know.{number}'))}</li>" for number in STEPS)
    return (
        f'<section class="hero"><div class="wrap hero-inner"><div class="hero-copy">'
        f'<h1>{escape(texts.text("home.title"))}</h1><p class="lead">{escape(texts.text("home.lead"))}</p>'
        f"{check_form_html(texts)}"
        f'<p class="example-prompt">{escape(texts.text("form.example_prompt"))} '
        f'<a href="?example=1" data-example>{escape(texts.text("form.example"))}</a></p></div>'
        f"{preview_html(example, texts)}</div></section>"
        f'<div class="wrap"><div id="result" class="result-region" aria-live="polite"></div></div>'
        f'<section class="how"><div class="wrap"><h2>{escape(texts.text("how.title"))}</h2>{steps_html(texts)}</div></section>'
        f'<section class="notes"><div class="wrap notes-inner">{legend_html(texts)}'
        f'<div class="know-block"><h2>{escape(texts.text("know.title"))}</h2><ul class="know">{notes}</ul></div>'
        f"</div></section>"
    )


def progress_html(texts: Texts, key: str) -> str:
    """What is happening while the visitor waits, with the nine cells moving."""
    cells = '<span class="meter-cell"></span>' * 9
    return (f'<div class="progress" role="status"><span class="meter meter--busy" aria-hidden="true">{cells}</span>'
            f"<p>{escape(texts.text(key))}</p></div>")


def error_html(texts: Texts, code: str) -> str:
    """What went wrong with the check and what to do, for the error code of the check."""
    return (f'<div class="notice notice--error" role="alert"><strong>{escape(texts.text("error.title"))}</strong>'
            f'<p>{escape(texts.text(f"error.{code}"))}</p></div>')


def result_html(model: PageModel, texts: Texts, example: bool = False) -> str:
    """Whole result of one dataset: who it is, the summary, the priorities, the checks, the checklist, the files."""
    facts = [("calendar-days", model.source_sentence), ("badge-check", model.marking_sentence)]
    if example:
        facts.append(("info", texts.text("result.example_note")))
    fact_rows = "".join(f"<li>{line_icon(icon)}<span>{escape(sentence)}</span></li>" for icon, sentence in facts if sentence)
    note = f'<p class="result-note">{escape(model.summary_note)}</p>' if model.summary_note else ""
    head = (
        f'<header class="result-head"><h1>{escape(model.title)}</h1>'
        f'<p class="result-publisher">{line_icon("landmark")}<span>{escape(model.publisher)}</span></p>'
        f'<p class="result-headline">{escape(model.headline)}</p>{note}'
        f'<ul class="result-facts">{fact_rows}</ul>'
        f'<a class="button button--ghost" href="{escape(model.url)}" {NEW_TAB}>{escape(texts.text("result.open"))}'
        f'{line_icon("external-link")}</a></header>'
    )
    body = (
        f'<p class="group-note">{escape(model.group_note)}</p>{fixes_html(model, texts)}{checks_html(model, texts)}'
        f"{checklist_html(model, texts)}{report_files_html(texts)}"
        f'<p class="result-disclaimer">{escape(texts.text("footer.disclaimer", criteria_version=model.criteria_version))}</p>'
    )
    return (
        f'<article class="result" data-dataset="{escape(model.name)}">{head}'
        f'<div class="result-layout"><aside class="result-aside">{index_html(model, texts)}</aside>'
        f'<div class="result-body">{body}</div></div></article>'
    )


def fixes_html(model: PageModel, texts: Texts) -> str:
    """What to correct, in the order of priority, each item leading to its check."""
    efforts = {check.criterion_id: EFFORT_CLASSES.get(check.effort_level) for check in model.checks}
    items = []
    for order, item in enumerate(model.fix_first, start=1):
        effort = efforts.get(item.criterion_id)
        bars = (f'<span class="effort effort--{effort}" aria-hidden="true"><span></span><span></span><span></span></span>'
                if effort else "")
        items.append(
            f'<li class="fix"><span class="fix-number">{order}</span><div class="fix-text">'
            f'<a href="#check-{escape(item.criterion_id)}">{escape(item.action)}</a>'
            f'<p>{escape(item.note)}</p></div>{bars}</li>'
        )
    content = f'<ol class="fixes">{"".join(items)}</ol>' if items else f'<p>{escape(texts.text("fix.none"))}</p>'
    return f'<section id="fixes" class="block"><h2>{escape(texts.text("fix.title"))}</h2>{content}</section>'


def checks_html(model: PageModel, texts: Texts) -> str:
    groups = "".join(
        f'<h3 class="group-title">{escape(texts.text(f"checks.group.{group}"))}</h3>'
        + "".join(check_html(check, texts) for check in model.checks if check.group == group)
        for group in dict.fromkeys(check.group for check in model.checks)
    )
    return (f'<section id="checks" class="block"><h2>{escape(texts.text("checks.title"))}</h2>'
            f'<p class="block-intro">{escape(texts.text("checks.intro"))}</p>{groups}</section>')


def check_html(check: CheckExplanation, texts: Texts) -> str:
    """One check: icon, name, status in words, finding, action, and the details closed at first."""
    status = STATUS_KEYS[check.status]
    labels = [check.kind_label, texts.text("card.core") if check.core else "", check.effort_label]
    action = (f'<p class="check-action"><strong>{escape(texts.text("card.action"))}</strong> {escape(check.action)}</p>'
              if check.action else "")
    if check.score is None:
        criterion = texts.text("details.criterion_no_score", id=check.criterion_id, name=check.criterion_name)
    else:
        criterion = texts.text("details.criterion", id=check.criterion_id, name=check.criterion_name, score=check.score)
    details = [criterion, texts.text("details.why", why=check.why), texts.text("details.reason", reason=check.reason)]
    if check.rule:
        details.append(texts.text("details.rule", score=check.score, rule=check.rule))
    details.append(texts.text("details.source"))
    lines = "".join(f"<p>{escape(line)}</p>" for line in details)
    return (
        f'<article class="check check--{status}" id="check-{escape(check.criterion_id)}">{status_icon(status)}'
        f'<div class="check-main"><div class="check-head"><h4>{escape(check.title)}</h4>'
        f'<span class="status-chip status-chip--{status}">{escape(check.status_label)}</span></div>'
        f'<p class="check-finding">{escape(check.finding)}</p>{action}'
        f'<details class="check-details"><summary><span class="check-meta">'
        f'{escape(" ".join(label for label in labels if label))}</span>'
        f'<span class="check-toggle">{escape(texts.text("card.details"))}{line_icon("chevron-down")}</span></summary>'
        f'<div class="check-details-box">{lines}</div></details></div></article>'
    )


def checklist_group_html(legend: str, items: tuple[ChecklistItem, ...], texts: Texts) -> str:
    rows = "".join(
        f'<div class="tick"><input type="checkbox" id="tick-{escape(item.criterion_id)}">'
        f'<label for="tick-{escape(item.criterion_id)}">{escape(item.question)}'
        + (f' <span class="badge">{escape(texts.text("checklist.core"))}</span>' if item.core else "")
        + f'</label><p class="tick-hint"><span>{escape(texts.text("checklist.if_not"))}</span> {escape(item.if_not)}</p></div>'
        for item in items
    )
    return f"<fieldset><legend>{escape(legend)}</legend>{rows}</fieldset>"


def checklist_html(model: PageModel, texts: Texts) -> str:
    """The fourteen criteria without a score, as questions with a box to tick and an advice."""
    return (
        f'<section id="checklist" class="block"><h2>{escape(texts.text("checklist.title"))}</h2>'
        f'<p class="block-intro">{escape(texts.text("checklist.intro"))}</p>'
        f'{checklist_group_html(texts.text("checklist.files"), model.checklist_files, texts)}'
        f'{checklist_group_html(texts.text("checklist.judgement"), model.checklist_judgement, texts)}</section>'
    )


def report_files_html(texts: Texts) -> str:
    """Buttons of the three files of the report; the script of the page prepares the file that is asked for."""
    buttons = "".join(
        f'<button type="button" class="button button--file" data-format="{name}">{line_icon(icon)}'
        f"<span>{escape(texts.text(key))}</span></button>"
        for name, key, icon in REPORT_FORMATS
    )
    return (
        f'<section id="report-files" class="block"><h2>{escape(texts.text("download.title"))}</h2>'
        f'<div class="file-buttons" data-preparing="{escape(texts.text("download.preparing"))}" '
        f'data-failed="{escape(texts.text("download.failed"))}">{buttons}</div>'
        f'<p class="file-status" role="status"></p><p class="block-intro">{escape(texts.text("download.note"))}</p></section>'
    )


def guide_main_html(texts: Texts) -> str:
    def paragraph(key: str) -> str:
        return f"<p>{escape(texts.text(key))}</p>"

    def heading(key: str) -> str:
        return f"<h2>{escape(texts.text(key))}</h2>"

    words = "".join(f"<li>{escape(texts.text(f'guide.words.{word}'))}</li>" for word in GLOSSARY)
    legend = "".join(
        f'<p class="legend-row">{status_icon(status)}<span><strong>{escape(texts.text(f"status.{status}"))}.</strong> '
        f'{escape(texts.text(f"legend.{status}"))}</span></p>'
        for status in LEGEND_STATUSES
    )
    return (
        f'<article class="wrap article"><h1>{escape(texts.text("guide.title"))}</h1>'
        f'<p class="lead">{escape(texts.text("guide.intro"))}</p>'
        f'{heading("guide.steps.title")}{steps_html(texts)}'
        f'{heading("guide.read.title")}{paragraph("guide.read.marks")}<div class="article-legend">{legend}</div>'
        f'{paragraph("guide.read.kinds")}{paragraph("guide.read.core")}{paragraph("guide.read.details")}'
        f'{heading("guide.after.title")}{paragraph("guide.after.text")}'
        f'{heading("guide.limits.title")}{paragraph("guide.limits.text")}'
        f'{heading("guide.words.title")}<ul class="glossary">{words}</ul></article>'
    )


def terms_main_html(texts: Texts) -> str:
    sections = "".join(
        f'<h2>{escape(texts.text(f"terms.{section}.title"))}</h2><p>{escape(texts.text(f"terms.{section}.text"))}</p>'
        for section in TERMS_SECTIONS
    )
    return (f'<article class="wrap article"><h1>{escape(texts.text("terms.title"))}</h1>'
            f'<p class="article-note">{escape(texts.text("terms.updated"))}</p>{sections}</article>')


def missing_main_html(texts: Texts) -> str:
    """Page shown for an address that matches no page of the site."""
    return (f'<article class="wrap article"><h1>{escape(texts.text("missing.title"))}</h1>'
            f'<p class="lead">{escape(texts.text("missing.text"))}</p>'
            f'<p><a class="button button--dark" href="{page_path("home", texts.language)}">'
            f'{escape(texts.text("missing.home"))}</a></p></article>')
