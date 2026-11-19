"""HTML of the public pages: home, result of a check with its tabs, second opinion of a model, guide and terms of use.

Every text is escaped before it enters the HTML: titles, publishers and values of the metadata
come from the portal and are shown as plain text. A status is always given by a word, a shape
and a colour. The pages carry no inline script or style and load only files of the site.
"""

from html import escape

from aiready import jev
from aiready.plain_language import STATUS_KEYS, CheckExplanation, ChecklistItem, PageModel
from aiready.second_reading import ReadingModel, ReadingRow, figure_of
from aiready.texts import DEFAULT_LANGUAGE, LANGUAGES, Texts
from web import release
from web.icons import SVG_ATTRIBUTES, band_icon, line_icon, mark_icon, status_icon

REPOSITORY_URL = "https://github.com/HermesLogios/datagovgr-ai-readiness"
OPINION_PAGE = "opinion"
PAGE_FOLDERS = {"home": "", OPINION_PAGE: "second-opinion/", "guide": "guide/", "terms": "terms/"}
PAGE_TITLES = {OPINION_PAGE: "opinion.title", "guide": "guide.title", "terms": "terms.title", "missing": "missing.title"}
NAVIGATION = (("home", "nav.check"), (OPINION_PAGE, "nav.opinion"), ("guide", "nav.how"), ("terms", "nav.terms"))
REPEATED_IN_FOOTER = ("terms",)                   # pages that the footer links too; narrow screens leave them out of the header
MISSING_PAGE = "missing"
OPINION_TAB = "second-opinion"                    # name of the tab of the second opinion; an address ending in #second-opinion opens it
TABS = (("checks", "tabs.checks"), (OPINION_TAB, "tabs.opinion"), ("checklist", "tabs.checklist"))
COUNTED_STATUSES = ("met", "partly", "not_met", "not_measured", "not_judged")
LEGEND_STATUSES = ("met", "partly", "not_met", "not_measured")
STEPS = (1, 2, 3, 4)
OPINION_STEPS = (1, 2, 3)
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


def reading_head_html(texts: Texts, tag_key: str, source: str = "") -> str:
    """Top line of the panel of the second reading: what the panel is and, for a reading, where it comes from."""
    named = f'<span class="reading-source">{escape(source)}</span>' if source else ""
    return (f'<div class="reading-head"><span class="reading-kind">{line_icon("text-search")}'
            f"{escape(texts.text(tag_key))}</span>{named}</div>")


def reading_preview_html(texts: Texts) -> str:
    """The five statements under their criterion, each with an empty meter: what a reading will answer."""
    groups = "".join(
        f'<h4 class="reading-group">{escape(texts.text(f"reading.group.{criterion}"))}</h4><ul class="reading-rows">'
        + "".join(
            f'<li class="reading-ask-row"><span class="reading-name">{escape(texts.text(f"reading.row.{statement.key}"))}</span>'
            f"{reading_meter_html(None)}</li>"
            for statement in jev.STATEMENTS if statement.criterion == criterion
        )
        + "</ul>"
        for criterion in dict.fromkeys(statement.criterion for statement in jev.STATEMENTS)
    )
    return (f'<div class="reading-preview"><p class="reading-preview-title">{escape(texts.text("reading.offer.preview"))}</p>'
            f"{groups}</div>")


def reading_offer_html(texts: Texts) -> str:
    """Offer of a second opinion in two columns: the field of the key with the button and what is sent and
    what is not kept, and next to them the five statements that the model will answer.

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
        f'</form><p class="reading-status" id="reading-status" role="status"></p><ul class="reading-facts">{facts}</ul>'
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
        f'<h4 class="reading-group">{escape(texts.text(f"reading.group.{criterion}"))}</h4><ul class="reading-rows">'
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
    notes = "".join(f'<p class="reading-note">{escape(texts.text(f"reading.note.{note}"))}</p>' for note in ("texts", "scores"))
    return (
        f'<div class="reading">{reading_head_html(texts, "reading.result.tag", model.source)}'
        f'<h3 tabindex="-1">{escape(texts.text("reading.result.title"))}</h3>'
        f'<p class="reading-lead">{escape(texts.text("reading.result.lead"))}</p>{groups}'
        f'<p class="reading-scale" aria-hidden="true"><span class="reading-scale-bands">{scale}</span></p>'
        f'<div class="reading-advice">{advice_box}</div>{notes}</div>'
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
        f'<section id="by-hand" class="block"><h2>{escape(texts.text("checklist.title"))}</h2>'
        f'<p class="block-intro">{escape(texts.text("checklist.intro"))}</p>'
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


def opinion_main_html(texts: Texts) -> str:
    """Page of the second opinion: what it is, the form that leads to it, the five statements, the steps, and
    what is needed and how far to trust the answer."""
    language = texts.language
    home = page_path("home", language)
    questions = "".join(
        f'<p class="question-group">{escape(texts.text(f"reading.group.{criterion}"))}</p><ul class="questions">'
        + "".join(f"<li>{escape(texts.text(f'reading.row.{statement.key}'))}</li>"
                  for statement in jev.STATEMENTS if statement.criterion == criterion)
        + "</ul>"
        for criterion in dict.fromkeys(statement.criterion for statement in jev.STATEMENTS)
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
        f'{paragraph("guide.read.kinds")}{paragraph("guide.read.core")}{paragraph("guide.read.details")}'
        f'{heading("guide.reading.title")}'
        f'{paragraph("guide.reading.text", likely=figure_of(jev.LIKELY, texts), unlikely=figure_of(jev.UNLIKELY, texts))}'
        f'{paragraph("guide.reading.trial")}'
        f'{heading("guide.after.title")}{paragraph("guide.after.text")}'
        f'{heading("guide.limits.title")}{paragraph("guide.limits.text")}'
        f'{heading("guide.words.title")}<ul class="glossary">{words}</ul></article>'
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
