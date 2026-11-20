"""HTML of the public pages: home, result of a check with its tabs, second opinion of a model, guide, criteria and
terms of use.

Every text is escaped before it enters the HTML: titles, publishers and values of the metadata
come from the portal and are shown as plain text. A status is always given by a word, a shape
and a colour. The pages carry no inline script or style and load only files of the site.
"""

from datetime import date
from html import escape

from aiready import jev
from aiready.criteria import CRITERIA_VERSION, Criterion
from aiready.plain_language import (STATUS_KEYS, CheckExplanation, ChecklistItem, PageModel, criterion_kind,
                                    criterion_title, level_key)
from aiready.second_reading import ReadingModel, ReadingRow, figure_of
from aiready.texts import DEFAULT_LANGUAGE, LANGUAGES, Texts
from web import release
from web.icons import SVG_ATTRIBUTES, band_icon, line_icon, mark_icon, status_icon

REPOSITORY_URL = "https://github.com/HermesLogios/datagovgr-ai-readiness"
CRITERIA_TEXT_URL = f"{REPOSITORY_URL}/blob/main/criteria/criteria.md"
CONSOLE_URL = "https://console.typesafe.ai/keys"       # page of the keys in the console of TypeSafe AI
PRICES_URL = "https://docs.typesafe.ai/models"         # models and prices of TypeSafe AI
KEY_STEPS_CHECKED = date(2026, 11, 19)                 # day on which the steps to a key were checked in the console
OPINION_PAGE = "opinion"
CRITERIA_PAGE = "criteria"
PAGE_FOLDERS = {"home": "", OPINION_PAGE: "second-opinion/", "guide": "guide/", CRITERIA_PAGE: "criteria/",
                "terms": "terms/"}
PAGE_TITLES = {OPINION_PAGE: "opinion.title", "guide": "guide.title", CRITERIA_PAGE: "criteria.title",
               "terms": "terms.title", "missing": "missing.title"}
NAVIGATION = (("home", "nav.check"), (OPINION_PAGE, "nav.opinion"), ("guide", "nav.how"), (CRITERIA_PAGE, "nav.criteria"),
              ("terms", "nav.terms"))
REPEATED_IN_FOOTER = ("terms",)                   # pages that the footer links too; narrow screens leave them out of the header
MISSING_PAGE = "missing"
OPINION_TAB = "second-opinion"                    # name of the tab of the second opinion; an address ending in #second-opinion opens it
TABS = (("checks", "tabs.checks"), (OPINION_TAB, "tabs.opinion"), ("checklist", "tabs.checklist"))
COUNTED_STATUSES = ("met", "partly", "not_met", "not_measured", "not_judged")
LEGEND_STATUSES = ("met", "partly", "not_met", "not_measured")
STEPS = (1, 2, 3, 4)
OPINION_STEPS = (1, 2, 3)
KEY_STEPS = (1, 2, 3, 4)
SCORE_STATUSES = ((2, "met"), (1, "partly"), (0, "not_met"))     # each score with the status that shows it in a result
KIND_KEYS = {"by rule": "by_rule", "proposal": "proposal", "files": "files", "judgement": "judgement"}
TERMS_SECTIONS = ("what", "result", "use", "data", "reading", "personal", "licences", "liability", "contact")
GLOSSARY = ("metadata", "format", "licence", "hvd")
EFFORT_CLASSES = {"Low": "low", "Medium": "medium", "High": "high"}
REPORT_FORMATS = (("xlsx", "download.excel", "file-spreadsheet"), ("md", "download.markdown", "file-text"),
                  ("json", "download.json", "braces"))
NEW_TAB = 'target="_blank" rel="noopener noreferrer"'
FONT_FILES = ("manrope-greek-wght-normal.woff2", "manrope-latin-wght-normal.woff2")
READING_FACTS = ("sent", "key_use", "scores")
# Messages that the script of the page shows next to the form of the second reading, by data attribute.
READING_MESSAGES = (("waiting", "reading.waiting"), ("key-missing", "reading.error.key_missing"),
                    ("key", "reading.error.key"), ("limit", "reading.error.limit"),
                    ("service", "reading.error.service"), ("engine", "reading.error.engine"))
METER_WIDTH = 100                                 # units of the drawing of a meter, from probability 0 to probability 1
# Sketch of the page of the keys in the console of TypeSafe AI: the menu on the left, the list of the keys and the
# button above it. Only the two names that a visitor presses are written, each with the number of its step.
KEY_SKETCH = (
    f'<svg class="key-sketch" viewBox="0 0 440 260" {SVG_ATTRIBUTES}>'
    '<rect class="sketch-frame" x="0.5" y="0.5" width="439" height="259" rx="14" />'
    '<path class="sketch-side" d="M1 53H128V259H15A14 14 0 0 1 1 245Z" />'
    '<path class="sketch-rule" d="M1 52.5H439M128.5 53V259M176 104.5H416M176 140.5H416M176 176.5H416M176 212.5H416" />'
    '<rect class="sketch-bar sketch-bar--dark" x="18" y="21" width="70" height="12" rx="6" />'
    '<rect class="sketch-bar" x="18" y="72" width="80" height="10" rx="5" />'
    '<rect class="sketch-bar" x="18" y="98" width="64" height="10" rx="5" />'
    '<rect class="sketch-active" x="8" y="119" width="112" height="32" rx="8" />'
    '<text class="sketch-label" x="20" y="141">API Keys</text>'
    '<rect class="sketch-bar" x="18" y="166" width="72" height="10" rx="5" />'
    '<rect class="sketch-bar" x="18" y="192" width="58" height="10" rx="5" />'
    '<rect class="sketch-bar" x="18" y="218" width="66" height="10" rx="5" />'
    '<rect class="sketch-bar sketch-bar--dark" x="176" y="74" width="120" height="14" rx="7" />'
    '<rect class="sketch-bar" x="176" y="117" width="84" height="10" rx="5" />'
    '<rect class="sketch-bar" x="280" y="117" width="118" height="10" rx="5" />'
    '<rect class="sketch-bar" x="176" y="153" width="70" height="10" rx="5" />'
    '<rect class="sketch-bar" x="280" y="153" width="118" height="10" rx="5" />'
    '<rect class="sketch-bar" x="176" y="189" width="92" height="10" rx="5" />'
    '<rect class="sketch-bar" x="280" y="189" width="118" height="10" rx="5" />'
    '<rect class="sketch-button" x="292" y="11" width="132" height="32" rx="16" />'
    '<text class="sketch-button-label" x="358" y="33" text-anchor="middle">Create key</text>'
    '<rect class="sketch-ring" x="4" y="115" width="120" height="40" rx="11" />'
    '<rect class="sketch-ring" x="286" y="5" width="144" height="44" rx="22" />'
    '<circle class="sketch-marker" cx="146" cy="135" r="13" />'
    '<text class="sketch-marker-label" x="146" y="140.5" text-anchor="middle">2</text>'
    '<circle class="sketch-marker" cx="266" cy="27" r="13" />'
    '<text class="sketch-marker-label" x="266" y="32.5" text-anchor="middle">3</text>'
    "</svg>"
)


def page_path(page: str, language: str) -> str:
    """Address of a page: Greek pages at the root of the site, English pages under /en/."""
    if language not in LANGUAGES:
        raise ValueError(f"unknown language: {language}")
    return ("/" if language == DEFAULT_LANGUAGE else f"/{language}/") + PAGE_FOLDERS[page]


def new_tab_note(texts: Texts) -> str:
    """Words for screen readers at the end of a link that opens in a new tab."""
    return f'<span class="visually-hidden"> {escape(texts.text("new_tab"))}</span>'


def code_tag_html(code: str, texts: Texts, new_tab: bool = True) -> str:
    """Code of a criterion of the study, as a link to its rules on the page of the criteria.

    Inside a result the link opens a new tab, so that the result, which exists only in the open page, stays where it is.
    """
    target = f" {NEW_TAB}" if new_tab else ""
    title = texts.text("code.title" if new_tab else "code.title_same", id=code)
    return (f'<a class="code-tag" href="{page_path(CRITERIA_PAGE, texts.language)}#{escape(code)}"{target} '
            f'title="{escape(title)}">{escape(code)}</a>')


def text_with_link(texts: Texts, key: str, link: str, **values) -> str:
    """Text of a key with the HTML of a link in the place of its field {link}, if it has one; the rest is escaped."""
    return link.join(escape(part) for part in texts.text(key, link="\0", **values).split("\0"))


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
        f'<link rel="icon" href="/favicon.ico" sizes="32x32">\n'
        f'<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n'
        f'<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n{fonts}'
        f'<link rel="stylesheet" href="/assets/style.css{version}">\n'
        f'<script type="module" src="/assets/app.js{version}"></script>\n</head>\n'
        f'<body{attributes}>\n<a class="skip-link" href="#main">{escape(texts.text("nav.skip"))}</a>\n'
        f'{header_html(texts, page)}\n<main id="main">{main}</main>\n{footer_html(texts, criteria_version)}\n</body>\n</html>\n'
    )


def header_html(texts: Texts, page: str) -> str:
    """Name of the tool, the pages of the site and the switch between the languages.

    The link of the second opinion carries a mark: on a page that shows a result, the script of the page
    opens the tab of the second opinion instead of leaving the result. A link that the footer repeats
    carries a class, so that the stylesheet can leave it out of the header where the header is narrow.
    """
    language = texts.language
    linked_page = "home" if page == MISSING_PAGE else page

    def page_link(target: str, key: str) -> str:
        mark = " data-opinion-link" if target == OPINION_PAGE else ""
        repeated = ' class="nav-repeated"' if target in REPEATED_IN_FOOTER else ""
        current = ' aria-current="page"' if target == page else ""
        return f'<a href="{page_path(target, language)}"{mark}{repeated}{current}>{escape(texts.text(key))}</a>'

    def language_link(other: str) -> str:
        current = ' aria-current="true"' if other == language else ""
        return (f'<a href="{page_path(linked_page, other)}" lang="{other}" hreflang="{other}"{current}>'
                f'{escape(texts.text(f"language.{other}"))}</a>')

    return (
        f'<header class="site-header"><div class="wrap site-header-inner">'
        f'<a class="brand" href="{page_path("home", language)}">{mark_icon()}<span>{escape(texts.text("app.name"))}</span></a>'
        f'<nav class="site-nav" aria-label="{escape(texts.text("nav.pages"))}">'
        f'{"".join(page_link(target, key) for target, key in NAVIGATION)}</nav>'
        f'<div class="language" role="group" aria-label="{escape(texts.text("nav.language"))}">'
        f'{"".join(language_link(other) for other in LANGUAGES)}</div></div></header>'
    )


def footer_html(texts: Texts, criteria_version: str) -> str:
    """Credit of the study, the two links, and the version of the page with the day of that version."""
    version = texts.text("footer.version", version=release.VERSION, date=texts.date(release.RELEASED))
    return (
        f'<footer class="site-footer"><div class="wrap site-footer-inner">'
        f'<p>{escape(texts.text("footer.credit", criteria_version=criteria_version))}</p>'
        f'<div class="footer-row"><ul class="footer-links"><li><a href="{REPOSITORY_URL}" {NEW_TAB}>{line_icon("code-xml")}'
        f'{escape(texts.text("footer.source"))}</a></li>'
        f'<li><a href="{page_path("terms", texts.language)}">{escape(texts.text("footer.terms"))}</a></li></ul>'
        f'<p class="site-version"><span class="visually-hidden">{escape(texts.text("footer.version_label"))}: </span>'
        f"{escape(version)}</p></div>"
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
            parts.append(f'<div class="index-part"><p class="index-group">{title}</p>'
                         f'<ol class="index-checks">{"".join(rows)}</ol></div>')
        else:
            parts.append(f'<span class="index-group">{title}</span>{"".join(rows)}')
    return "".join(parts)


def index_html(model: PageModel, texts: Texts) -> str:
    """Card in the head of a result: the nine checks at a glance, each leading to its own card."""
    statuses = [STATUS_KEYS[check.status] for check in model.checks]
    counts = "".join(
        f'<li>{status_icon(status)}<span><strong>{statuses.count(status)}</strong> {escape(texts.text(f"status.{status}"))}</span></li>'
        for status in COUNTED_STATUSES if status in statuses
    )
    title = escape(texts.text("index.title"))
    return (
        f'<nav class="index" aria-label="{title}"><p class="index-title">{title}</p>{meter_html(model)}'
        f'<ul class="index-counts">{counts}</ul>'
        f'<div class="index-parts">{check_rows_html(model, texts, linked=True)}</div></nav>'
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


def check_form_html(texts: Texts, action: str = "", submit: str = "form.submit") -> str:
    """Form of the address of a dataset.

    On the home page the script of the page sends it. With an action, the browser sends it to that address
    with the address of the dataset in the query.
    """
    target = f' action="{escape(action)}"' if action else ""
    return (
        f'<form class="check-form" id="check-form" method="get"{target} novalidate>'
        f'<label for="dataset-address">{escape(texts.text("form.label"))}</label>'
        f'<span class="field">{line_icon("link")}'
        f'<input id="dataset-address" name="dataset" type="text" inputmode="url" autocomplete="off" autocapitalize="none" '
        f'spellcheck="false" placeholder="{escape(texts.text("form.placeholder"))}">'
        f'<button type="submit" class="button button--primary">{escape(texts.text(submit))}</button></span></form>'
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
        f'<a href="?example=1" data-example>{escape(texts.text("form.example"))}</a></p>'
        f'<p class="opinion-prompt"><a href="{page_path(OPINION_PAGE, texts.language)}">{line_icon("text-search")}'
        f'<span>{escape(texts.text("home.opinion"))}</span></a></p></div>'
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


def tab_counts(model: PageModel) -> dict[str, int]:
    """How many checks and how many criteria of the checklist a result holds, by the name of their tab."""
    return {"checks": len(model.checks), "checklist": len(model.checklist_files) + len(model.checklist_judgement)}


def tabs_html(model: PageModel, texts: Texts) -> str:
    """Bar under the head of a result: the three tabs and, next to them, the menu of the files of the report.

    The first tab is the open one. The script of the page opens the others and keeps the address of the
    page in step with the open tab. The link of a tab names the tab and not its panel: no part of the page
    carries that name, so the browser does not move the page by itself and the script alone shows the panel.
    """
    counts = tab_counts(model)
    tabs = []
    for position, (name, key) in enumerate(TABS):
        selected = position == 0
        icon = line_icon("text-search") if name == OPINION_TAB else ""
        count = f'<span class="tab-count">{counts[name]}</span>' if name in counts else ""
        order = "" if selected else ' tabindex="-1"'
        tabs.append(
            f'<a class="tab" role="tab" id="tab-{name}" href="#{name}" aria-controls="panel-{name}" '
            f'aria-selected="{str(selected).lower()}"{order}>{icon}<span>{escape(texts.text(key))}</span>{count}</a>'
        )
    return (f'<div class="result-bar"><div class="tabs" role="tablist" aria-label="{escape(texts.text("tabs.label"))}">'
            f'{"".join(tabs)}</div>{report_menu_html(texts)}</div>')


def panel_html(name: str, content: str, shown: bool) -> str:
    """Panel of a tab. Every panel but the open one is hidden on the screen; all of them are printed."""
    hidden = "" if shown else " hidden"
    return (f'<div class="tab-panel" role="tabpanel" id="panel-{name}" aria-labelledby="tab-{name}" tabindex="0"{hidden}>'
            f"{content}</div>")


def panel_next_html(model: PageModel, texts: Texts, names: tuple[str, ...]) -> str:
    """Links at the end of a panel to the tabs that come after it, each with a line on what the tab holds."""
    keys, counts = dict(TABS), tab_counts(model)
    links = "".join(
        f'<a href="#{name}"><strong>{escape(texts.text(keys[name]))}</strong>'
        f'<span>{escape(texts.text(f"tabs.next.{name}", count=counts.get(name, 0)))}</span></a>'
        for name in names
    )
    return f'<nav class="panel-next" aria-label="{escape(texts.text("tabs.next"))}">{links}</nav>'


def result_html(model: PageModel, texts: Texts, example: bool = False) -> str:
    """Whole result of one dataset: the head with the summary and the nine checks at a glance, the tabs, and
    one panel per tab: the priorities with the checks, the second opinion of a model, and the checklist."""
    facts = [("calendar-days", model.source_sentence), ("badge-check", model.marking_sentence)]
    if example:
        facts.append(("info", texts.text("result.example_note")))
    fact_rows = "".join(f"<li>{line_icon(icon)}<span>{escape(sentence)}</span></li>" for icon, sentence in facts if sentence)
    note = f'<p class="result-note">{escape(model.summary_note)}</p>' if model.summary_note else ""
    head = (
        f'<header class="result-head"><div class="result-summary"><h1>{escape(model.title)}</h1>'
        f'<p class="result-publisher">{line_icon("landmark")}<span>{escape(model.publisher)}</span></p>'
        f'<p class="result-headline">{escape(model.headline)}</p>{note}'
        f'<ul class="result-facts">{fact_rows}</ul>'
        f'<a class="button button--ghost" href="{escape(model.url)}" {NEW_TAB}>{escape(texts.text("result.open"))}'
        f'{line_icon("external-link")}</a></div>{index_html(model, texts)}</header>'
    )
    panels = {
        "checks": f'<p class="group-note">{escape(model.group_note)}</p>{fixes_html(model, texts)}'
                  f'{checks_html(model, texts)}{panel_next_html(model, texts, (OPINION_TAB, "checklist"))}',
        OPINION_TAB: f'{reading_section_html(texts)}{panel_next_html(model, texts, ("checklist",))}',
        "checklist": checklist_html(model, texts),
    }
    return (
        f'<article class="result" data-dataset="{escape(model.name)}">{head}{tabs_html(model, texts)}'
        + "".join(panel_html(name, panels[name], shown=position == 0) for position, (name, _) in enumerate(TABS))
        + f'<p class="result-disclaimer">{escape(texts.text("footer.disclaimer", criteria_version=model.criteria_version))}</p>'
        f"</article>"
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
    return (f'<section id="nine-checks" class="block"><h2>{escape(texts.text("checks.title"))}</h2>'
            f'<p class="block-intro">{escape(texts.text("checks.intro"))}</p>'
            f'<p class="block-intro">{escape(texts.text("codes.note"))}</p>{groups}</section>')


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
    lines = "".join(f"<p>{escape(line)}</p>" for line in details)
    code = escape(check.criterion_id)
    rules = (f'<p class="check-rules"><a href="{page_path(CRITERIA_PAGE, texts.language)}#{code}" {NEW_TAB}>'
             f'{escape(texts.text("details.rules", id=check.criterion_id, page=texts.quoted(texts.text("nav.criteria"))))}'
             f"{new_tab_note(texts)}</a></p>")
    return (
        f'<article class="check check--{status}" id="check-{code}">{status_icon(status)}'
        f'<div class="check-main"><div class="check-head"><div class="check-name">'
        f"{code_tag_html(check.criterion_id, texts)}<h4>{escape(check.title)}</h4></div>"
        f'<span class="status-chip status-chip--{status}">{escape(check.status_label)}</span></div>'
        f'<p class="check-finding">{escape(check.finding)}</p>{action}'
        f'<details class="check-details"><summary><span class="check-meta">'
        f'{escape(" ".join(label for label in labels if label))}</span>'
        f'<span class="check-toggle">{escape(texts.text("card.details"))}{line_icon("chevron-down")}</span></summary>'
        f'<div class="check-details-box">{lines}{rules}</div></details></div></article>'
    )


def reading_head_html(texts: Texts, tag_key: str, source: str = "") -> str:
    """Top line of the panel of the second reading: what the panel is and, for a reading, where it comes from."""
    named = f'<span class="reading-source">{escape(source)}</span>' if source else ""
    return (f'<div class="reading-head"><span class="reading-kind">{line_icon("text-search")}'
            f"{escape(texts.text(tag_key))}</span>{named}</div>")


def reading_group_html(criterion: str, texts: Texts) -> str:
    """Heading of the statements of one criterion in the panel of the second reading, with the code of the criterion."""
    return (f'<h4 class="reading-group">{code_tag_html(criterion, texts)}'
            f'<span>{escape(texts.text(f"reading.group.{criterion}"))}</span></h4>')


def reading_preview_html(texts: Texts) -> str:
    """The statements under their criterion, each with an empty meter, and the question of the category: what a
    reading will answer."""
    groups = "".join(
        f'{reading_group_html(criterion, texts)}<ul class="reading-rows">'
        + "".join(
            f'<li class="reading-ask-row"><span class="reading-name">{escape(texts.text(f"reading.row.{statement.key}"))}</span>'
            f"{reading_meter_html(None)}</li>"
            for statement in jev.STATEMENTS if statement.criterion == criterion
        )
        + "</ul>"
        for criterion in dict.fromkeys(statement.criterion for statement in jev.STATEMENTS)
    )
    category = (f'{reading_group_html(jev.CATEGORY_QUESTION.criterion, texts)}<ul class="reading-rows">'
                f'<li class="reading-ask-row"><span class="reading-name">'
                f'{escape(texts.text(f"reading.row.{jev.CATEGORY_QUESTION.key}"))}</span></li></ul>')
    return (f'<div class="reading-preview"><p class="reading-preview-title">{escape(texts.text("reading.offer.preview"))}</p>'
            f"{groups}{category}</div>")


def reading_offer_html(texts: Texts) -> str:
    """Offer of a second opinion in two columns: the field of the key with the button and what is sent and
    what is not kept, and next to them the questions that the model will answer.

    The script of the page sends the form itself. The method is POST so that, if the form were ever sent by
    the browser, the key would not become part of an address.
    """
    messages = "".join(f' data-{name}="{escape(texts.text(key))}"' for name, key in READING_MESSAGES)
    facts = "".join(
        f'<li>{line_icon("check")}<span>{escape(texts.text(f"reading.offer.{fact}"))}</span></li>' for fact in READING_FACTS
    )
    return (
        f'<div class="reading">{reading_head_html(texts, "reading.offer.tag")}'
        f'<div class="reading-columns"><div class="reading-ask"><h3>{escape(texts.text("reading.offer.title"))}</h3>'
        f'<p class="reading-lead">{escape(texts.text("reading.offer.lead"))}</p>'
        f'<form class="reading-form" id="reading-form" method="post" novalidate{messages}>'
        f'<label for="reading-key">{escape(texts.text("reading.offer.key"))}</label>'
        f'<span class="reading-field">{line_icon("key-round")}'
        f'<input id="reading-key" name="key" type="password" autocomplete="off" autocapitalize="none" spellcheck="false" '
        f'aria-describedby="reading-status">'
        f'</span><button type="submit" class="button button--primary">{escape(texts.text("reading.offer.submit"))}</button>'
        f'</form><p class="reading-status" id="reading-status" role="status"></p>'
        f'<p class="reading-help"><a href="{page_path(OPINION_PAGE, texts.language)}#key" {NEW_TAB}>'
        f'{escape(texts.text("reading.offer.help"))}{new_tab_note(texts)}{line_icon("external-link")}</a></p>'
        f'<ul class="reading-facts">{facts}</ul>'
        f'<p class="reading-terms"><a href="{page_path("terms", texts.language)}#reading">'
        f'{escape(texts.text("reading.offer.terms"))}</a></p></div>{reading_preview_html(texts)}</div></div>'
    )


def reading_section_html(texts: Texts) -> str:
    """Section of the second opinion inside its tab; the script of the page puts the reading in the place of the offer.

    The dark panel carries its own heading, so the heading of the section is kept for the outline of the
    page and for screen readers only.
    """
    return (f'<section id="reading" class="block"><h2 class="visually-hidden">{escape(texts.text("reading.title"))}</h2>'
            f"{reading_offer_html(texts)}</section>")


def reading_meter_html(probability: float | None) -> str:
    """Bar of a probability on a track from 0 to 1, cut at the two limits of the bands.

    Without a probability the track stays empty. The bar is an SVG drawing, because the pages carry no
    inline style that could give it a width. Its value stands next to it as text, so the drawing is hidden
    from screen readers.
    """
    fill = ("" if probability is None else
            f'<line class="reading-fill" x1="0" y1="5" x2="{round(probability * METER_WIDTH)}" y2="5" />')
    marks = "".join(
        f'<line class="reading-mark" x1="{round(limit * METER_WIDTH)}" y1="-3" x2="{round(limit * METER_WIDTH)}" y2="13" />'
        for limit in (jev.UNLIKELY, jev.LIKELY)
    )
    return (
        f'<svg class="reading-meter" viewBox="0 0 {METER_WIDTH} 10" preserveAspectRatio="none" {SVG_ATTRIBUTES}>'
        f'<line class="reading-track" x1="0" y1="5" x2="{METER_WIDTH}" y2="5" />{fill}{marks}</svg>'
    )


def reading_row_html(row: ReadingRow) -> str:
    """One statement: its name, the band in words with its icon, the bar and the probability."""
    return (
        f'<li class="reading-row reading-row--{row.band}"><span class="reading-name">{escape(row.label)}</span>'
        f'<span class="reading-band">{band_icon(row.band)}{escape(row.band_label)}</span>'
        f'{reading_meter_html(row.probability)}<span class="reading-figure">{escape(row.figure)}</span></li>'
    )


def reading_result_html(model: ReadingModel, texts: Texts) -> str:
    """Panel of a second reading: the statements under their criterion, what to add, and what the reading is not."""
    groups = "".join(
        f'{reading_group_html(criterion, texts)}<ul class="reading-rows">'
        + "".join(reading_row_html(row) for row in model.rows if row.criterion == criterion)
        + "</ul>"
        for criterion in dict.fromkeys(row.criterion for row in model.rows)
    )
    scale = "".join(f"<span>{escape(texts.text(f'reading.band.{band}'))}</span>" for band in ("unlikely", "unsure", "likely"))
    advice = [row.advice for row in model.rows if row.advice]
    if advice:
        items = "".join(f"<li>{escape(item)}</li>" for item in advice)
        advice_box = f'<h4>{escape(texts.text("reading.advice.title"))}</h4><ul>{items}</ul>'
    else:
        advice_box = f'<p>{escape(texts.text("reading.advice.none"))}</p>'
    hint = ""
    if model.hint:
        detail = f'<p class="reading-lead">{escape(model.hint_detail)}</p>' if model.hint_detail else ""
        hint = (f'{reading_group_html(jev.CATEGORY_QUESTION.criterion, texts)}<p class="reading-lead">{escape(model.hint)}</p>'
                f'{detail}<p class="reading-note">{escape(texts.text("reading.hvd.disclaimer"))}</p>')
    note_keys = ("texts", "scores", "new") + (() if model.columns_read else ("no_columns",))
    notes = "".join(f'<p class="reading-note">{escape(texts.text(f"reading.note.{note}"))}</p>' for note in note_keys)
    return (
        f'<div class="reading">{reading_head_html(texts, "reading.result.tag", model.source)}'
        f'<h3 tabindex="-1">{escape(texts.text("reading.result.title"))}</h3>'
        f'<p class="reading-lead">{escape(texts.text("reading.result.lead"))}</p>{groups}'
        f'<p class="reading-scale" aria-hidden="true"><span class="reading-scale-bands">{scale}</span></p>'
        f'{hint}<div class="reading-advice">{advice_box}</div>{notes}</div>'
    )


def checklist_group_html(legend: str, items: tuple[ChecklistItem, ...], texts: Texts) -> str:
    """Criteria of one group of the checklist: the code and the name of each, then its question with a box and an advice."""
    rows = "".join(
        f'<div class="tick"><p class="tick-name">{code_tag_html(item.criterion_id, texts)}<span>{escape(item.name)}</span>'
        + (f' <span class="badge">{escape(texts.text("checklist.core"))}</span>' if item.core else "")
        + f'</p><input type="checkbox" id="tick-{escape(item.criterion_id)}">'
        f'<label for="tick-{escape(item.criterion_id)}">{escape(item.question)}</label>'
        f'<p class="tick-hint"><span>{escape(texts.text("checklist.if_not"))}</span> {escape(item.if_not)}</p></div>'
        for item in items
    )
    return f"<fieldset><legend>{escape(legend)}</legend>{rows}</fieldset>"


def checklist_html(model: PageModel, texts: Texts) -> str:
    """The fourteen criteria without a score, as questions with a box to tick and an advice."""
    return (
        f'<section id="by-hand" class="block"><h2>{escape(texts.text("checklist.title"))}</h2>'
        f'<p class="block-intro">{escape(texts.text("checklist.intro"))}</p>'
        f'<p class="block-intro">{escape(texts.text("codes.note"))}</p>'
        f'{checklist_group_html(texts.text("checklist.files"), model.checklist_files, texts)}'
        f'{checklist_group_html(texts.text("checklist.judgement"), model.checklist_judgement, texts)}</section>'
    )


def report_menu_html(texts: Texts) -> str:
    """Menu of the three files of the report, next to the tabs; the script of the page prepares the file that is asked for."""
    buttons = "".join(
        f'<button type="button" class="button button--file" data-format="{name}">{line_icon(icon)}'
        f"<span>{escape(texts.text(key))}</span></button>"
        for name, key, icon in REPORT_FORMATS
    )
    return (
        f'<details class="report-menu"><summary class="button button--report">{line_icon("download")}'
        f'<span>{escape(texts.text("download.menu"))}</span>{line_icon("chevron-down")}</summary>'
        f'<div class="report-menu-box"><div class="file-buttons" data-preparing="{escape(texts.text("download.preparing"))}" '
        f'data-failed="{escape(texts.text("download.failed"))}">{buttons}</div>'
        f'<p class="file-status" role="status"></p><p class="report-note">{escape(texts.text("download.note"))}</p></div></details>'
    )


def statement_counts() -> dict[str, int]:
    """Number of questions of the model for each criterion: the statements in their order, then the question of
    the category of high-value data."""
    counts: dict[str, int] = {}
    for statement in jev.STATEMENTS:
        counts[statement.criterion] = counts.get(statement.criterion, 0) + 1
    category = jev.CATEGORY_QUESTION.criterion
    counts[category] = counts.get(category, 0) + 1
    return counts


def opinion_how_html(texts: Texts) -> str:
    """How the model works: what it reads, what it answers, how the page shows the answer, and the criteria it serves."""
    bands = texts.text(
        "opinion.how.bands", likely=figure_of(jev.LIKELY, texts), unlikely=figure_of(jev.UNLIKELY, texts),
        likely_word=texts.quoted(texts.text("reading.band.likely")),
        unlikely_word=texts.quoted(texts.text("reading.band.unlikely")),
        unsure_word=texts.quoted(texts.text("reading.band.unsure")),
    )
    paragraphs = "".join(f"<p>{escape(text)}</p>" for text in (
        texts.text("opinion.how.model"), texts.text("opinion.how.sent"), bands, texts.text("opinion.how.scores")))
    rows = "".join(
        f"<li>{code_tag_html(code, texts, new_tab=False)}<span>"
        f'{escape(texts.counted("opinion.how.count", count, name=criterion_title(code, texts), n=count))}</span></li>'
        for code, count in statement_counts().items()
    )
    return (
        f'<section class="explain" id="how"><div class="wrap explain-inner"><div class="explain-text">'
        f'<h2>{escape(texts.text("opinion.how.title"))}</h2>{paragraphs}</div>'
        f'<div class="explain-side"><p class="explain-side-title">{escape(texts.text("opinion.how.criteria"))}</p>'
        f'<ul class="explain-criteria">{rows}</ul></div></div></section>'
    )


def opinion_key_html(texts: Texts) -> str:
    """How to get a key in the console of TypeSafe AI, in four steps next to a sketch of the console."""
    console = (f'<a href="{CONSOLE_URL}" {NEW_TAB}>{escape(CONSOLE_URL.removeprefix("https://"))}'
               f"{new_tab_note(texts)}</a>")
    places = {"field": texts.quoted(texts.text("reading.offer.key")), "tab": texts.quoted(texts.text("tabs.opinion")),
              "button": texts.quoted(texts.text("reading.offer.submit"))}
    steps = "".join(
        f'<li><span class="step-number">{number}</span>'
        f'<p>{text_with_link(texts, f"opinion.key.step.{number}", console, **places)}</p></li>'
        for number in KEY_STEPS
    )
    prices = f'<a href="{PRICES_URL}" {NEW_TAB}>{escape(texts.text("opinion.key.prices"))}{new_tab_note(texts)}</a>'
    return (
        f'<section class="explain explain--key" id="key"><div class="wrap explain-inner"><div class="explain-text">'
        f'<h2>{escape(texts.text("opinion.key.title"))}</h2><p>{escape(texts.text("opinion.key.lead"))}</p>'
        f'<ol class="key-steps">{steps}</ol><p>{escape(texts.text("opinion.key.care"))}</p>'
        f'<p>{escape(texts.text("opinion.key.cost"))} {prices}.</p>'
        f'<p class="explain-note">{escape(texts.text("opinion.key.checked", date=texts.date(KEY_STEPS_CHECKED)))}</p></div>'
        f'<figure class="key-figure">{KEY_SKETCH}<figcaption>{escape(texts.text("opinion.key.figure"))}</figcaption></figure>'
        f"</div></section>"
    )


def opinion_main_html(texts: Texts) -> str:
    """Page of the second opinion: what it is, the form that leads to it, the questions, the steps, how the
    model works, how to get a key, and what is needed and how far to trust the answer."""
    language = texts.language
    home = page_path("home", language)
    questions = "".join(
        f'<p class="question-group">{code_tag_html(criterion, texts, new_tab=False)}'
        f'<span>{escape(texts.text(f"reading.group.{criterion}"))}</span></p><ul class="questions">'
        + "".join(f"<li>{escape(texts.text(f'reading.row.{statement.key}'))}</li>"
                  for statement in jev.STATEMENTS if statement.criterion == criterion)
        + "</ul>"
        for criterion in dict.fromkeys(statement.criterion for statement in jev.STATEMENTS)
    ) + (
        f'<p class="question-group">{code_tag_html(jev.CATEGORY_QUESTION.criterion, texts, new_tab=False)}'
        f'<span>{escape(texts.text(f"reading.group.{jev.CATEGORY_QUESTION.criterion}"))}</span></p>'
        f'<ul class="questions"><li>{escape(texts.text(f"reading.row.{jev.CATEGORY_QUESTION.key}"))}</li></ul>'
    )
    words = {
        "tab": texts.quoted(texts.text("tabs.opinion")), "button": texts.quoted(texts.text("reading.offer.submit")),
        "likely": texts.quoted(texts.text("reading.band.likely")), "unsure": texts.quoted(texts.text("reading.band.unsure")),
        "unlikely": texts.quoted(texts.text("reading.band.unlikely")),
    }
    steps = "".join(
        f'<li><span class="step-number">{number}</span><h3>{escape(texts.text(f"opinion.step.{number}.title"))}</h3>'
        f'<p>{escape(texts.text(f"opinion.step.{number}.text", **words))}</p></li>'
        for number in OPINION_STEPS
    )
    needs = "".join(f"<li>{escape(texts.text(key))}</li>"
                    for key in ("opinion.need.key", "reading.offer.sent", "reading.offer.key_use", "reading.offer.scores"))
    return (
        f'<section class="hero hero--page"><div class="wrap hero-inner"><div class="hero-copy">'
        f'<p class="hero-kind">{line_icon("text-search")}<span>{escape(texts.text("opinion.kind"))}</span></p>'
        f'<h1>{escape(texts.text("opinion.heading"))}</h1><p class="lead">{escape(texts.text("opinion.lead"))}</p>'
        f'{check_form_html(texts, action=f"{home}#{OPINION_TAB}", submit="opinion.submit")}'
        f'<p class="example-prompt">{escape(texts.text("form.example_prompt"))} '
        f'<a href="{home}?example=1#{OPINION_TAB}">{escape(texts.text("form.example"))}</a></p></div>'
        f'<div class="question-card"><p class="question-title">{escape(texts.text("reading.offer.preview"))}</p>{questions}</div>'
        f"</div></section>"
        f'<section class="how"><div class="wrap"><h2>{escape(texts.text("opinion.steps.title"))}</h2>'
        f'<ol class="steps steps--three">{steps}</ol></div></section>'
        f"{opinion_how_html(texts)}{opinion_key_html(texts)}"
        f'<section class="notes"><div class="wrap notes-inner">'
        f'<div class="know-block"><h2>{escape(texts.text("opinion.need.title"))}</h2><ul class="know">{needs}</ul>'
        f'<p class="know-link"><a href="{page_path("terms", language)}#reading">{escape(texts.text("reading.offer.terms"))}</a></p></div>'
        f'<div class="know-block"><h2>{escape(texts.text("opinion.trust.title"))}</h2>'
        f'<p>{escape(texts.text("opinion.trust.lead"))}</p><p>{escape(texts.text("guide.reading.trial"))}</p></div>'
        f"</div></section>"
    )


def guide_main_html(texts: Texts) -> str:
    def paragraph(key: str, **values) -> str:
        return f"<p>{escape(texts.text(key, **values))}</p>"

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
        f'{paragraph("guide.read.kinds")}{paragraph("guide.read.core")}'
        f'{paragraph("guide.read.details", page=texts.quoted(texts.text("nav.criteria")))}'
        f'<p class="know-link"><a href="{page_path(CRITERIA_PAGE, texts.language)}">'
        f'{escape(texts.text("guide.read.criteria_link"))}</a></p>'
        f'{heading("guide.reading.title")}'
        f'{paragraph("guide.reading.text", likely=figure_of(jev.LIKELY, texts), unlikely=figure_of(jev.UNLIKELY, texts))}'
        f'{paragraph("guide.reading.trial")}'
        f'{heading("guide.after.title")}{paragraph("guide.after.text")}'
        f'{heading("guide.limits.title")}{paragraph("guide.limits.text")}'
        f'{heading("guide.words.title")}<ul class="glossary">{words}</ul></article>'
    )


def criterion_section_html(criterion: Criterion, texts: Texts) -> str:
    """One criterion on the page of the criteria, as a card: its code and names and how the application treats it,
    then a closed box that opens on its question, the rule of every score and what the application does with it."""
    code = escape(criterion.id)
    kind = criterion_kind(criterion)
    badges = [f'<span class="badge badge--kind">{escape(texts.text(f"criteria.kind.{KIND_KEYS[kind]}"))}</span>']
    if criterion.core:
        badges.append(f'<span class="badge">{escape(texts.text("criteria.core"))}</span>')
    if criterion.applies_to == "high-value":
        badges.append(f'<span class="badge badge--scope">{escape(texts.text("criteria.high_value"))}</span>')
    scores = "".join(
        f'<div class="score-row"><dt>{status_icon(status)}<span class="visually-hidden">'
        f'{escape(texts.text("criteria.score"))} </span>{score}</dt>'
        f'<dd>{escape(texts.text(f"criterion.{criterion.id}.score_{score}"))}</dd></div>'
        for score, status in SCORE_STATUSES
    )
    if criterion.not_applicable:
        scores += (f'<div class="score-row score-row--na"><dt>{escape(texts.text("criteria.not_applicable"))}</dt>'
                   f'<dd>{escape(texts.text(f"criterion.{criterion.id}.not_applicable"))}</dd></div>')
    if kind in ("files", "judgement"):
        application = texts.text(f"criteria.app.{kind}", tab=texts.quoted(texts.text("tabs.checklist")))
    else:
        application = texts.text(f"criterion.{criterion.id}.how")
    asked = statement_counts().get(criterion.id, 0)
    opinion = ""
    if asked:
        opinion = (f'<p class="criterion-opinion">{line_icon("text-search")}<span>'
                   f'{escape(texts.counted("criteria.opinion", asked, n=asked))} '
                   f'<a href="{page_path(OPINION_PAGE, texts.language)}#how">{escape(texts.text("criteria.opinion_link"))}</a>'
                   f"</span></p>")
    return (
        f'<section class="criterion" id="{code}" aria-labelledby="name-{code}"><div class="criterion-top">'
        f'<div class="criterion-head"><span class="code-tag code-tag--plain">{code}</span>'
        f'<h3 id="name-{code}">{escape(criterion_title(criterion.id, texts))}</h3></div>'
        f'<p class="criterion-study">{escape(texts.text("criteria.study"))} <span lang="en">{escape(criterion.name)}</span></p>'
        f'<p class="criterion-badges">{"".join(badges)}</p></div>'
        f'<details class="criterion-more"><summary><span>{escape(texts.text("criteria.more"))}</span>'
        f'{line_icon("chevron-down")}</summary><div class="criterion-body">'
        f'<p class="criterion-question">{escape(texts.text(f"criterion.{criterion.id}.question"))}</p>'
        f'<dl class="criterion-scores">{scores}</dl>'
        f'<div class="criterion-app"><p class="criterion-app-title">{escape(texts.text("criteria.app.title"))}</p>'
        f"<p>{escape(application)}</p></div>{opinion}</div></details></section>"
    )


def criteria_main_html(texts: Texts, criteria: dict[str, Criterion]) -> str:
    """Page of the criteria: how a score is read, then the cards of the criteria in one grid per level, with a button
    that opens or closes them all once the script of the page runs."""
    kinds = {code: criterion_kind(criterion) for code, criterion in criteria.items()}

    def codes(selected) -> str:
        return ", ".join(code for code in criteria if selected(code))

    tab = texts.quoted(texts.text("tabs.checklist"))
    treatments = (
        ("criteria.kind.by_rule", "criteria.kind.by_rule.text", codes(lambda code: kinds[code] == "by rule")),
        ("criteria.kind.proposal", "criteria.kind.proposal.text", codes(lambda code: kinds[code] == "proposal")),
        ("tabs.checklist", "criteria.kind.checklist.text", codes(lambda code: kinds[code] in ("files", "judgement"))),
    )
    treatment_items = "".join(
        f'<li><strong>{escape(texts.text(label))}.</strong> {escape(texts.text(explanation, tab=tab))} '
        f'{escape(texts.text("criteria.codes", codes=listed))}</li>'
        for label, explanation, listed in treatments
    )
    statuses = {status: texts.quoted(texts.text(f"status.{status}")) for status in ("met", "partly", "not_met", "not_measured")}
    open_all = escape(texts.text("criteria.open_all"))
    tools = (f'<div class="criteria-tools"><button type="button" class="criteria-toggle" data-toggle-all aria-expanded="false" '
             f'data-open-label="{open_all}" data-close-label="{escape(texts.text("criteria.close_all"))}" hidden>'
             f'<span>{open_all}</span>{line_icon("chevron-down")}</button></div>')
    levels = []
    for level in dict.fromkeys(level_key(code) for code in criteria):
        members = [code for code in criteria if level_key(code) == level]
        heading = texts.text("criteria.level.range", level=texts.text(f"criteria.level.{level}"), first=members[0],
                             last=members[-1])
        levels.append(f'<h2 id="level-{escape(level)}">{escape(heading)}</h2><div class="criteria-grid">'
                      + "".join(criterion_section_html(criteria[code], texts) for code in members) + "</div>")
    return (
        f'<article class="wrap article criteria-page"><h1>{escape(texts.text("criteria.heading", count=len(criteria)))}</h1>'
        f'<p class="lead">{escape(texts.text("criteria.lead"))}</p>'
        f'<h2 id="scale">{escape(texts.text("criteria.scale.title"))}</h2>'
        f'<p>{escape(texts.text("criteria.scale.scores", **statuses))}</p>'
        f'<p>{escape(texts.text("criteria.scale.kinds"))}</p><ul class="kinds">{treatment_items}</ul>'
        f'<p>{escape(texts.text("criteria.scale.core", codes=codes(lambda code: criteria[code].core)))}</p>'
        f'<p>{escape(texts.text("criteria.scale.high_value", codes=codes(lambda code: criteria[code].applies_to == "high-value")))}</p>'
        f"{tools}{''.join(levels)}"
        f'<h2 id="source">{escape(texts.text("criteria.source.title"))}</h2>'
        f'<p>{escape(texts.text("criteria.source.text", version=CRITERIA_VERSION))}</p>'
        f'<p class="know-link"><a href="{CRITERIA_TEXT_URL}" {NEW_TAB}>{escape(texts.text("criteria.source.link"))}'
        f"{new_tab_note(texts)}</a></p></article>"
    )


def terms_main_html(texts: Texts) -> str:
    sections = "".join(
        f'<h2 id="{section}">{escape(texts.text(f"terms.{section}.title"))}</h2>'
        f'<p>{escape(texts.text(f"terms.{section}.text"))}</p>'
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
