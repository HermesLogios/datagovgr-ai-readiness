"""Checks of the HTML of the public pages.

Usage:
    python -m unittest discover -s tests
"""

import dataclasses
import re
import unittest
from datetime import date
from html import escape

from aiready import jev
from aiready.second_reading import build_reading_model
from aiready.texts import load_texts
from sample_pages import EXAMPLE, UNMARKED, page_model
from web import icons, pages, release

STATUS_ICON = 'class="status-icon status-icon--'
COUNT_WORDS = {"el": {4: "τέσσερις", 5: "πέντε", 6: "έξι"}, "en": {4: "four", 5: "five", 6: "six"}}


def block(html: str, opening: str, closing: str) -> str:
    """Part of the HTML from an opening tag to the first closing tag after it."""
    start = html.index(opening)
    return html[start:html.index(closing, start) + len(closing)]


def panel(html: str, name: str) -> str:
    """Panel of a tab of a result, from its opening tag to the next panel or to the end of the panels."""
    start = html.index(f'<div class="tab-panel" role="tabpanel" id="panel-{name}"')
    following = [html.find(mark, start + 1) for mark in ('<div class="tab-panel"', '<p class="result-disclaimer">')]
    return html[start:min(position for position in following if position > 0)]


class AddressTest(unittest.TestCase):
    def test_greek_pages_sit_at_the_root_and_english_pages_under_en(self):
        self.assertEqual(pages.page_path("home", "el"), "/")
        self.assertEqual(pages.page_path("home", "en"), "/en/")
        self.assertEqual(pages.page_path("guide", "el"), "/guide/")
        self.assertEqual(pages.page_path("terms", "en"), "/en/terms/")
        self.assertEqual(pages.page_path("opinion", "el"), "/second-opinion/")
        self.assertEqual(pages.page_path("opinion", "en"), "/en/second-opinion/")

    def test_unknown_page_or_language_is_refused(self):
        with self.assertRaises(KeyError):
            pages.page_path("prices", "el")
        with self.assertRaises(ValueError):
            pages.page_path("home", "fr")


class DocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.document = pages.document_html("guide", cls.texts, "<p>main part</p>", criteria_version="1.2")

    def test_document_declares_its_language_and_its_name(self):
        self.assertTrue(self.document.startswith('<!DOCTYPE html>\n<html lang="el">'))
        self.assertIn("<title>Οδηγός χρήσης | Έλεγχος ετοιμότητας δεδομένων</title>", self.document)
        english = pages.document_html("home", load_texts("en"), "", criteria_version="1.2")
        self.assertIn('<html lang="en">', english)
        self.assertIn("<title>Data readiness check</title>", english)

    def test_main_part_follows_a_link_that_skips_the_header(self):
        self.assertLess(self.document.index('<a class="skip-link" href="#main">'), self.document.index("<header"))
        self.assertIn('<main id="main"><p>main part</p></main>', self.document)

    def test_language_switch_leads_to_the_same_page_in_the_other_language(self):
        switch = block(self.document, '<div class="language"', "</div>")
        self.assertIn('<a href="/guide/" lang="el" hreflang="el" aria-current="true">Ελληνικά</a>', switch)
        self.assertIn('<a href="/en/guide/" lang="en" hreflang="en">English</a>', switch)
        self.assertIn('<link rel="alternate" hreflang="en" href="/en/guide/">', self.document)

    def test_navigation_marks_the_page_that_is_open(self):
        navigation = block(self.document, '<nav class="site-nav"', "</nav>")
        self.assertIn('<a href="/guide/" aria-current="page">Πώς δουλεύει</a>', navigation)
        self.assertIn('<a href="/terms/" class="nav-repeated">Όροι χρήσης</a>', navigation)

    def test_only_the_link_that_the_footer_repeats_is_marked_so_that_narrow_screens_can_leave_it_out(self):
        navigation = block(self.document, '<nav class="site-nav"', "</nav>")
        self.assertEqual(navigation.count('class="nav-repeated"'), 1)
        self.assertIn(f'<a href="/terms/">{self.texts.text("footer.terms")}</a>', block(self.document, "<footer", "</footer>"))

    def test_navigation_lists_the_four_pages_with_the_check_first(self):
        navigation = block(self.document, '<nav class="site-nav"', "</nav>")
        self.assertEqual(re.findall(r'<a href="([^"]+)"', navigation), ["/", "/second-opinion/", "/guide/", "/terms/"])
        self.assertIn('<a href="/">Έλεγχος</a>', navigation)
        self.assertIn('<a href="/second-opinion/" data-opinion-link>Δεύτερη γνώμη ΤΝ</a>', navigation)
        english = pages.document_html("opinion", load_texts("en"), "", criteria_version="1.2")
        self.assertIn('<a href="/en/second-opinion/" data-opinion-link aria-current="page">AI second opinion</a>', english)
        self.assertIn("<title>AI second opinion | Data readiness check</title>", english)

    def test_footer_shows_the_version_of_the_application_and_its_day(self):
        footer = block(self.document, "<footer", "</footer>")
        self.assertRegex(release.VERSION, r"^\d+\.\d+$")
        self.assertIn('<p class="site-version"><span class="visually-hidden">Έκδοση της εφαρμογής: </span>'
                      f"v{release.VERSION} · {self.texts.date(release.RELEASED)}</p>", footer)
        english = pages.document_html("home", load_texts("en"), "", criteria_version="1.2")
        self.assertIn(f"v{release.VERSION} · {load_texts('en').date(release.RELEASED)}</p>", english)

    def test_footer_names_the_study_and_links_the_code_and_the_terms(self):
        footer = block(self.document, "<footer", "</footer>")
        self.assertIn("Κριτήρια αξιολόγησης, έκδοση 1.2.", footer)
        self.assertIn('href="https://github.com/HermesLogios/datagovgr-ai-readiness" target="_blank" rel="noopener noreferrer"',
                      footer)
        self.assertIn('<a href="/terms/">Όροι χρήσης και δεδομένα</a>', footer)

    def test_document_loads_only_files_of_the_site(self):
        addresses = re.findall(r'(?:src|href)="([^"]+)"', self.document.split("<body", 1)[0])
        for address in addresses:
            self.assertTrue(address.startswith("/"), address)


class ResultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.model = page_model(EXAMPLE)
        cls.result = pages.result_html(cls.model, cls.texts)

    def test_head_names_the_dataset_its_publisher_and_the_source_of_the_metadata(self):
        head = block(self.result, '<header class="result-head">', "</header>")
        self.assertIn("<h1>Τροχαία ατυχήματα</h1>", head)
        self.assertIn("Υπουργείο Προστασίας του Πολίτη", head)
        self.assertIn("5 από τους 9 ελέγχους είναι εντάξει. Οι άλλοι 4 πληρούνται εν μέρει.", head)
        self.assertIn("Τα μεταδεδομένα διαβάστηκαν από το στιγμιότυπο της 24/10/2026.", head)
        self.assertIn("Το σύνολο έχει σήμανση υψηλής αξίας, στην κατηγορία «Στατιστικά».", head)

    def test_dataset_link_opens_the_portal_in_a_new_tab(self):
        self.assertIn('href="https://data.gov.gr/dataset/troxaia-atyxhmata" target="_blank" rel="noopener noreferrer"',
                      self.result)

    def test_meter_has_one_cell_per_check_in_two_groups_and_a_label_in_words(self):
        meter = block(self.result, '<div class="meter"', "</div>")
        self.assertEqual(meter.count('class="meter-cell '), 9)
        self.assertEqual(meter.count("meter-cell--met"), 5)
        self.assertEqual(meter.count("meter-cell--partly"), 4)
        self.assertEqual(meter.count('class="meter-group"'), 2)
        self.assertIn('role="img" aria-label="9 έλεγχοι: 5 εντάξει, 4 εν μέρει, 0 όχι, 0 χωρίς αποτέλεσμα"', meter)

    def test_head_lists_every_check_with_its_status_as_a_link_to_its_card(self):
        index = block(block(self.result, '<header class="result-head">', "</header>"), '<nav class="index"', "</nav>")
        for check in self.model.checks:
            self.assertIn(f'<a href="#check-{check.criterion_id}">', index)
            self.assertIn(f"<span>{check.title}</span>", index)
        self.assertEqual(index.count(STATUS_ICON), 9 + 2)       # nine checks and the two counts above zero
        self.assertIn("<strong>5</strong> Εντάξει", index)
        self.assertIn("<strong>4</strong> Εν μέρει", index)
        self.assertNotIn("index-sections", self.result)

    def test_head_keeps_the_checks_of_each_group_together_under_the_name_of_the_group(self):
        index = block(self.result, '<nav class="index"', "</nav>")
        self.assertEqual(index.count('<div class="index-parts">'), 1)
        parts = re.findall(r'<div class="index-part"><p class="index-group">([^<]+)</p><ol class="index-checks">(.*?)</ol></div>', index)
        self.assertEqual([name for name, _ in parts], ["Η περιγραφή του συνόλου", "Η διάθεση των δεδομένων"])
        self.assertEqual([rows.count("<li>") for _, rows in parts], [5, 4])

    def test_result_has_three_tabs_and_the_first_is_open(self):
        tabs = block(self.result, '<div class="tabs" role="tablist"', "</div>")
        self.assertIn('aria-label="Μέρη του αποτελέσματος"', tabs)
        found = re.findall(r'class="tab" role="tab" id="tab-([\w-]+)" href="#([\w-]+)" aria-controls="([\w-]+)" '
                           r'aria-selected="(\w+)"', tabs)
        self.assertEqual(found, [("checks", "checks", "panel-checks", "true"),
                                 ("second-opinion", "second-opinion", "panel-second-opinion", "false"),
                                 ("checklist", "checklist", "panel-checklist", "false")])
        self.assertIn('<span>Έλεγχοι</span><span class="tab-count">9</span>', tabs)
        self.assertIn("<span>Δεύτερη γνώμη ΤΝ</span>", tabs)
        self.assertIn('<span>Λίστα ελέγχου</span><span class="tab-count">14</span>', tabs)
        self.assertEqual(tabs.count('tabindex="-1"'), 2)

    def test_every_tab_has_its_panel_and_only_the_first_panel_is_shown(self):
        panels = re.findall(r'<div class="tab-panel" role="tabpanel" id="panel-([\w-]+)" aria-labelledby="tab-([\w-]+)" '
                            r'tabindex="0"( hidden)?>', self.result)
        self.assertEqual(panels, [("checks", "checks", ""), ("second-opinion", "second-opinion", " hidden"),
                                  ("checklist", "checklist", " hidden")])

    def test_no_part_of_a_result_is_named_like_a_tab_so_that_the_script_alone_moves_the_page_to_a_tab(self):
        for name in ("checks", "second-opinion", "checklist"):
            self.assertIn(f'href="#{name}"', self.result)
            self.assertNotIn(f' id="{name}"', self.result)

    def test_panels_hold_the_priorities_and_the_checks_then_the_opinion_then_the_checklist(self):
        checks, opinion, checklist = (panel(self.result, name) for name in ("checks", "second-opinion", "checklist"))
        self.assertLess(checks.index('<section id="fixes"'), checks.index('<section id="nine-checks"'))
        self.assertEqual(checks.count('<article class="check '), 9)
        self.assertIn('<section id="reading"', opinion)
        self.assertNotIn('<article class="check ', opinion)
        self.assertIn('<section id="by-hand"', checklist)
        self.assertEqual(checklist.count('type="checkbox"'), 14)

    def test_every_panel_but_the_last_ends_with_the_way_to_the_next_ones(self):
        checks, opinion, checklist = (panel(self.result, name) for name in ("checks", "second-opinion", "checklist"))
        self.assertEqual(re.findall(r'<a href="#([\w-]+)">', block(checks, '<nav class="panel-next"', "</nav>")),
                         ["second-opinion", "checklist"])
        self.assertEqual(re.findall(r'<a href="#([\w-]+)">', block(opinion, '<nav class="panel-next"', "</nav>")), ["checklist"])
        self.assertNotIn("panel-next", checklist)

    def test_way_to_the_checklist_names_the_number_of_its_boxes(self):
        boxes = panel(self.result, "checklist").count('type="checkbox"')
        ways = block(panel(self.result, "checks"), '<nav class="panel-next"', "</nav>")
        self.assertIn(f"<span>Άλλα {boxes} κριτήρια θέλουν", ways)
        self.assertNotIn("{", ways)

    def test_no_address_inside_a_result_is_used_twice(self):
        addresses = re.findall(r' id="([^"]+)"', self.result)
        self.assertEqual(len(addresses), len(set(addresses)))

    def test_every_check_has_an_address_an_icon_a_name_and_a_status_in_words(self):
        cards = re.findall(r'<article class="check .*?</article>', self.result, re.DOTALL)
        self.assertEqual(len(cards), 9)
        for card, check in zip(cards, self.model.checks):
            self.assertIn(f'id="check-{check.criterion_id}"', card)
            self.assertEqual(card.count(STATUS_ICON), 1)
            self.assertIn(f"<h4>{check.title}</h4>", card)
            self.assertIn(f">{check.status_label}</span>", card)

    def test_details_give_the_code_the_reason_and_the_rule(self):
        self.assertIn("Κριτήριο M1, Mandatory metadata. Βαθμός 1 από 2.", self.result)
        self.assertIn("Αιτιολογία του ελέγχου: description of 76 characters (minimum 100)", self.result)
        self.assertIn("Κανόνας για τον βαθμό 1: All are present, but the description repeats the title", self.result)
        self.assertEqual(self.result.count('<details class="check-details">'), 9)

    def test_priorities_are_numbered_in_order_and_lead_to_their_check(self):
        fixes = block(self.result, '<ol class="fixes">', "</ol>")
        self.assertEqual(re.findall(r'<span class="fix-number">(\d+)</span>', fixes), ["1", "2", "3", "4"])
        self.assertIn('<a href="#check-M1">Γράψτε πληρέστερη περιγραφή.</a>', fixes)
        self.assertLess(fixes.index("Γράψτε πληρέστερη περιγραφή."), fixes.index("Γράψτε ποια περίοδο καλύπτουν τα δεδομένα."))
        self.assertEqual(fixes.count('class="effort effort--'), 4)

    def test_dataset_without_problems_gets_a_sentence_instead_of_priorities(self):
        clean = dataclasses.replace(self.model, fix_first=())
        html = pages.result_html(clean, self.texts)
        self.assertNotIn('<ol class="fixes">', html)
        self.assertIn("Οι έλεγχοι των μεταδεδομένων δεν βρήκαν κάτι προς διόρθωση. Δείτε και τη λίστα ελέγχου.</p>", html)

    def test_result_names_the_checklist_without_saying_where_it_stands(self):
        for language, place in (("el", "πιο κάτω"), ("en", "below")):
            model = dataclasses.replace(page_model(EXAMPLE, language), fix_first=())
            html = panel(pages.result_html(model, load_texts(language)), "checks")
            self.assertNotIn(place, html[:html.index('<section id="nine-checks"')], language)

    def test_text_from_the_portal_is_shown_as_text(self):
        hostile = dataclasses.replace(
            self.model, title='<script>alert("x")</script>', publisher="<b>bold</b>", name='x" onclick="y',
            url='https://data.gov.gr/dataset/x" onclick="y',
            checks=(dataclasses.replace(self.model.checks[0], finding="<img src=x onerror=alert(1)>", reason="<i>reason</i>"),)
            + self.model.checks[1:],
        )
        html = pages.result_html(hostile, self.texts)
        for fragment in ("<script", "<img", "<b>bold</b>", "<i>reason</i>", '" onclick="y'):
            self.assertNotIn(fragment, html)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)
        self.assertIn("&lt;i&gt;reason&lt;/i&gt;", html)

    def test_example_is_announced_only_for_the_example(self):
        note = self.texts.text("result.example_note")
        self.assertNotIn(note, self.result)
        self.assertIn(note, pages.result_html(self.model, self.texts, example=True))

    def test_unjudged_check_is_shown_with_its_own_words(self):
        html = pages.result_html(page_model(UNMARKED), self.texts)
        self.assertIn(">Δεν κρίνεται αυτόματα</span>", html)
        self.assertIn("Η σήμανση υψηλής αξίας δεν κρίνεται αυτόματα και δεν μετρά εδώ.", html)
        self.assertEqual(html.count("meter-cell--not_judged"), 1)
        self.assertNotIn("σήμανση υψηλής αξίας, στην κατηγορία", block(html, '<header class="result-head">', "</header>"))

    def test_checklist_has_a_labelled_box_and_an_advice_for_each_of_the_fourteen(self):
        checklist = block(self.result, '<section id="by-hand"', "</section>")
        self.assertEqual(checklist.count('type="checkbox"'), 14)
        for item in self.model.checklist_files + self.model.checklist_judgement:
            self.assertIn(f'<input type="checkbox" id="tick-{item.criterion_id}"', checklist)
            self.assertIn(f'<label for="tick-{item.criterion_id}">', checklist)
        self.assertEqual(checklist.count("Αν όχι:"), 14)
        self.assertEqual(checklist.count("Βασικό κριτήριο."), 3)
        self.assertEqual(checklist.count("<fieldset"), 2)

    def test_report_is_offered_in_three_formats_from_a_menu_next_to_the_tabs(self):
        bar = self.result[self.result.index('<div class="result-bar">'):self.result.index('<div class="tab-panel"')]
        menu = block(bar, '<details class="report-menu">', "</details>")
        self.assertIn("<span>Λήψη αναφοράς</span>", block(menu, "<summary", "</summary>"))
        self.assertEqual(re.findall(r'<button type="button" class="button button--file" data-format="(\w+)"', menu),
                         ["xlsx", "md", "json"])
        self.assertIn("Λήψη σε Excel", menu)
        self.assertIn('<p class="file-status" role="status"></p>', menu)
        self.assertLess(bar.index('role="tablist"'), bar.index('<details class="report-menu">'))

    def test_result_ends_with_what_the_result_is_not(self):
        self.assertIn("Το αποτέλεσμα είναι ενδεικτικό και δεν είναι επίσημη αξιολόγηση.", self.result)


class StatusIconTest(unittest.TestCase):
    def test_every_status_has_its_own_drawing_hidden_from_screen_readers(self):
        drawings = set()
        for status in ("met", "partly", "not_met", "not_measured", "not_judged"):
            icon = pages.status_icon(status)
            self.assertTrue(icon.startswith(f'<svg class="status-icon status-icon--{status}"'))
            self.assertIn('aria-hidden="true"', icon)
            drawings.add(icon.split(">", 1)[1])
        self.assertEqual(len(drawings), 5)

    def test_unknown_status_is_refused(self):
        with self.assertRaises(KeyError):
            pages.status_icon("perfect")


class HomeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.home = pages.home_main_html(cls.texts, page_model(EXAMPLE))

    def test_form_has_a_labelled_field_for_the_address_and_one_button(self):
        form = block(self.home, "<form", "</form>")
        self.assertIn('<label for="dataset-address">Διεύθυνση του συνόλου</label>', form)
        self.assertIn('<input id="dataset-address" name="dataset" type="text"', form)
        self.assertIn('placeholder="https://data.gov.gr/dataset/..."', form)
        self.assertEqual(form.count("<button"), 1)
        self.assertIn(">Έλεγχος</button>", form)

    def test_example_is_one_link_and_a_preview_that_stays_out_of_the_tab_order(self):
        self.assertIn('<a href="?example=1" data-example>Δοκιμάστε με το παράδειγμα «Τροχαία ατυχήματα»</a>', self.home)
        preview = block(self.home, '<a class="preview"', "</a>")
        self.assertIn('aria-hidden="true" tabindex="-1"', preview)
        self.assertEqual(preview.count(STATUS_ICON), 9)
        self.assertEqual(preview.count('class="meter-cell '), 9)

    def test_result_has_its_place_after_the_form(self):
        self.assertLess(self.home.index("</form>"), self.home.index('<div id="result" class="result-region" aria-live="polite">'))

    def test_steps_are_an_ordered_list_of_four(self):
        steps = block(self.home, '<ol class="steps">', "</ol>")
        self.assertEqual(steps.count("<li"), 4)
        self.assertIn("<h3>Αντιγράψτε τη διεύθυνση</h3>", steps)

    def test_home_names_the_second_opinion_and_leads_to_its_page(self):
        self.assertIn('<p class="opinion-prompt"><a href="/second-opinion/">', self.home)
        self.assertIn('<a href="/en/second-opinion/">', pages.home_main_html(load_texts("en"), page_model(EXAMPLE, "en")))

    def test_legend_explains_the_four_statuses_and_four_notes_say_what_to_know(self):
        legend = block(self.home, '<div class="legend">', "</div>")
        self.assertEqual(legend.count(STATUS_ICON), 4)
        for word in ("Εντάξει", "Εν μέρει", "Όχι", "Δεν μετριέται"):
            self.assertIn(f"<strong>{word}.</strong>", legend)
        self.assertEqual(block(self.home, '<ul class="know">', "</ul>").count("<li"), 4)


class OtherPagesTest(unittest.TestCase):
    def test_error_says_what_happened_and_what_to_do(self):
        html = pages.error_html(load_texts("el"), "portal")
        self.assertIn('role="alert"', html)
        self.assertIn("Ο έλεγχος δεν έγινε", html)
        self.assertIn("Η πύλη data.gov.gr δεν απάντησε. Δοκιμάστε ξανά σε λίγα λεπτά.", html)

    def test_guide_and_terms_exist_in_both_languages(self):
        for language in ("el", "en"):
            texts = load_texts(language)
            guide = pages.guide_main_html(texts)
            self.assertIn(f"<h1>{texts.text('guide.title')}</h1>", guide)
            self.assertEqual(block(guide, '<ol class="steps">', "</ol>").count("<li"), 4)
            terms = pages.terms_main_html(texts)
            self.assertIn(texts.text("terms.liability.text"), terms)
            self.assertEqual(terms.count("<h2 id="), 9)

    def test_no_page_leaves_a_field_of_a_text_unfilled(self):
        for language in ("el", "en"):
            texts = load_texts(language)
            model = page_model(EXAMPLE, language)
            parts = (pages.home_main_html(texts, model), pages.result_html(model, texts, example=True),
                     pages.opinion_main_html(texts), pages.guide_main_html(texts), pages.terms_main_html(texts))
            for part in parts:
                document = pages.document_html("home", texts, part, criteria_version="1.2")
                self.assertIsNone(re.search(r"\{[a-z_]+\}", document), language)


class ReadingTest(unittest.TestCase):
    PROBABILITIES = {"contents": 0.94, "coverage": 0.41, "gaps": 0.03, "collection": 0.7, "errors": 0.3}
    DAY = date(2026, 11, 18)

    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.result = pages.result_html(page_model(EXAMPLE), cls.texts)
        cls.reading = cls.reading_html(jev.Reading("jev-1.14.0", cls.PROBABILITIES, 812))

    @classmethod
    def reading_html(cls, reading: jev.Reading) -> str:
        return pages.reading_result_html(build_reading_model(reading, cls.texts, cls.DAY), cls.texts)

    def test_result_offers_the_second_opinion_in_its_own_tab_under_its_name(self):
        opinion = panel(self.result, "second-opinion")
        self.assertIn('<section id="reading" class="block"><h2 class="visually-hidden">Δεύτερη γνώμη ΤΝ</h2>', opinion)
        self.assertIn("<h3>Δεύτερη γνώμη από μοντέλο ΤΝ</h3>", opinion)
        self.assertEqual(self.result.count('<form class="reading-form"'), 1)

    def test_offer_shows_the_five_statements_with_empty_meters_under_their_criterion(self):
        preview = block(self.result, '<div class="reading-preview">', "</div>")
        self.assertIn('<p class="reading-preview-title">Οι πέντε ερωτήσεις</p>', preview)
        self.assertEqual(preview.count('<li class="reading-ask-row">'), 5)
        self.assertEqual(preview.count('<svg class="reading-meter"'), 5)
        self.assertNotIn("reading-fill", preview)
        marks = [preview.index(words) for words in ("Τίτλος και περιγραφή", "Λέει τι περιέχουν", "Περιορισμοί των δεδομένων",
                                                    "Αναφέρει περιοχή", "Λέει πόσο ακριβή είναι")]
        self.assertEqual(marks, sorted(marks))

    def test_offer_stands_in_two_columns_with_the_form_first(self):
        columns = block(self.result, '<div class="reading-columns">', "</form>")
        self.assertLess(columns.index('<div class="reading-ask">'), columns.index('<form class="reading-form"'))
        self.assertLess(self.result.index('<form class="reading-form"'), self.result.index('<div class="reading-preview">'))

    def test_offer_has_a_labelled_field_for_the_key_that_browsers_do_not_fill(self):
        form = block(self.result, '<form class="reading-form"', "</form>")
        self.assertIn('<label for="reading-key">Το κλειδί σας για το Jev</label>', form)
        self.assertIn('<input id="reading-key" name="key" type="password" autocomplete="off"', form)
        self.assertEqual(form.count("<button"), 1)

    def test_offer_carries_the_messages_of_the_script_and_says_what_is_sent(self):
        opening = block(self.result, '<form class="reading-form"', ">")
        for name, key in (("waiting", "reading.waiting"), ("key-missing", "reading.error.key_missing"),
                          ("key", "reading.error.key"), ("limit", "reading.error.limit"),
                          ("service", "reading.error.service"), ("engine", "reading.error.engine")):
            self.assertIn(f'data-{name}="{escape(self.texts.text(key))}"', opening)
        for fact in ("sent", "key_use", "scores"):
            self.assertIn(escape(self.texts.text(f"reading.offer.{fact}")), self.result)
        self.assertIn('<p class="reading-status" id="reading-status" role="status"></p>', self.result)
        self.assertIn('aria-describedby="reading-status"', block(self.result, '<input id="reading-key"', ">"))

    def test_form_of_the_key_would_never_put_the_key_in_an_address(self):
        opening = block(self.result, '<form class="reading-form"', ">")
        self.assertIn('method="post"', opening)
        self.assertNotIn("action=", opening)
        self.assertIn('<a href="/terms/#reading">', self.result)
        self.assertIn('<a href="/en/terms/#reading">', pages.result_html(page_model(EXAMPLE, "en"), load_texts("en")))

    def test_reading_has_one_row_per_statement_with_the_band_in_words_before_the_number(self):
        rows = re.findall(r'<li class="reading-row reading-row--(\w+)">(.*?)</li>', self.reading)
        self.assertEqual([band for band, _ in rows], ["likely", "unsure", "unlikely", "likely", "unlikely"])
        first = rows[0][1]
        self.assertIn('<span class="reading-name">Λέει τι περιέχουν τα δεδομένα</span>', first)
        self.assertLess(first.index("Μάλλον ναι"), first.index("0,94"))
        self.assertIn('<span class="reading-figure">0,94</span>', first)
        self.assertIn('class="band-icon band-icon--likely"', first)

    def test_every_band_has_its_own_drawing_hidden_from_screen_readers(self):
        drawings = [icons.band_icon(band) for band in ("likely", "unsure", "unlikely")]
        self.assertEqual(len(set(drawing.split(">", 1)[1] for drawing in drawings)), 3)
        for drawing in drawings:
            self.assertIn('aria-hidden="true"', drawing)
        with self.assertRaises(KeyError):
            icons.band_icon("certain")

    def test_meter_is_drawn_without_inline_styles_and_its_value_stands_as_text(self):
        self.assertNotIn("style=", self.reading)
        self.assertNotIn("style=", block(self.result, '<section id="reading"', "</section>"))
        self.assertIn('<line class="reading-fill" x1="0" y1="5" x2="94" y2="5" />', self.reading)
        self.assertIn('<line class="reading-fill" x1="0" y1="5" x2="3" y2="5" />', self.reading)
        meters = re.findall(r'<svg class="reading-meter"[^>]*>', self.reading)
        self.assertEqual(len(meters), 5)
        for meter in meters:
            self.assertIn('aria-hidden="true"', meter)

    def test_meter_is_cut_at_the_limits_of_the_bands(self):
        meter = block(self.reading, '<svg class="reading-meter"', "</svg>")
        self.assertEqual(re.findall(r'<line class="reading-mark" x1="(\d+)"', meter), ["30", "70"])
        scale = block(self.reading, '<p class="reading-scale" aria-hidden="true">', "</p>")
        self.assertEqual(re.findall(r"<span>([^<]+)</span>", scale), ["Μάλλον όχι", "Αβέβαιο", "Μάλλον ναι"])

    def test_rows_stand_under_the_criterion_they_belong_to(self):
        self.assertLess(self.reading.index("Τίτλος και περιγραφή"), self.reading.index("Λέει τι περιέχουν"))
        self.assertLess(self.reading.index("Λέει τι περιέχουν"), self.reading.index("Περιορισμοί των δεδομένων"))
        self.assertLess(self.reading.index("Περιορισμοί των δεδομένων"), self.reading.index("Αναφέρει περιοχή"))

    def test_advice_lists_what_is_not_clearly_stated(self):
        advice = block(self.reading, '<div class="reading-advice">', "</div>")
        self.assertEqual(advice.count("<li>"), 3)
        self.assertIn(f"<h4>{escape(self.texts.text('reading.advice.title'))}</h4>", advice)
        self.assertIn(escape(self.texts.text("reading.advice.gaps")), advice)
        self.assertNotIn(escape(self.texts.text("reading.advice.contents")), advice)

    def test_reading_that_states_everything_gets_a_sentence_instead_of_a_list(self):
        html = self.reading_html(jev.Reading("jev-1.14.0", dict.fromkeys(self.PROBABILITIES, 0.9), 1))
        advice = block(html, '<div class="reading-advice">', "</div>")
        self.assertNotIn("<li>", advice)
        self.assertNotIn("<h4>", advice)
        self.assertIn(escape(self.texts.text("reading.advice.none")), advice)

    def test_reading_says_what_it_is_not_and_names_the_model(self):
        for sentence in ("Πρόταση ΤΝ, χωρίς βαθμό", "Μοντέλο jev-1.14.0, 18/11/2026",
                         self.texts.text("reading.note.texts"), self.texts.text("reading.note.scores")):
            self.assertIn(escape(sentence), self.reading)

    def test_heading_of_the_reading_can_take_the_focus(self):
        self.assertIn(f'<h3 tabindex="-1">{escape(self.texts.text("reading.result.title"))}</h3>', self.reading)

    def test_name_of_the_model_is_shown_as_text(self):
        html = self.reading_html(jev.Reading("<script>alert(1)</script>", self.PROBABILITIES, 1))
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_terms_have_a_section_on_the_reading_and_name_the_person_in_charge(self):
        greek, english = pages.terms_main_html(self.texts), pages.terms_main_html(load_texts("en"))
        for terms in (greek, english):
            self.assertIn('<h2 id="reading">', terms)
            self.assertIn("TypeSafe AI", terms)
        self.assertIn("Υπεύθυνος της σελίδας είναι ο Μιχαήλ Σκανδαλίδης", greek)
        self.assertIn("Michail Skandalidis", english)

    def test_terms_name_their_own_version_apart_from_the_version_of_the_application(self):
        self.assertIn('<p class="article-note">Όροι χρήσης, έκδοση 2, Νοέμβριος 2026.', pages.terms_main_html(self.texts))
        self.assertIn('<p class="article-note">Terms of use, version 2, November 2026.',
                      pages.terms_main_html(load_texts("en")))
        self.assertIn("<h2 id=\"reading\">Δεύτερη γνώμη από μοντέλο ΤΝ</h2>", pages.terms_main_html(self.texts))

    def test_guide_explains_the_reading_with_the_limits_of_the_bands(self):
        greek, english = pages.guide_main_html(self.texts), pages.guide_main_html(load_texts("en"))
        self.assertIn("<h2>Η δεύτερη γνώμη ΤΝ</h2>", greek)
        self.assertIn("Στην καρτέλα «Δεύτερη γνώμη ΤΝ» του αποτελέσματος", greek)
        self.assertNotIn("Κάτω από τους εννέα ελέγχους", greek)
        self.assertIn("από 0,70 και πάνω γράφει «Μάλλον ναι», έως 0,30 «Μάλλον όχι»", greek)
        self.assertIn("<h2>The AI second opinion</h2>", english)
        self.assertIn("from 0.70 upwards it writes “Likely”, up to 0.30 “Unlikely”", english)


class OpinionPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.page = pages.opinion_main_html(cls.texts)
        cls.english = pages.opinion_main_html(load_texts("en"))

    def test_page_says_in_its_heading_what_the_second_opinion_is(self):
        self.assertIn("<h1>Δεύτερη γνώμη από μοντέλο ΤΝ</h1>", self.page)
        self.assertIn("<h1>A second opinion from an AI model</h1>", self.english)

    def test_form_leads_to_the_result_with_the_tab_of_the_second_opinion_open(self):
        form = block(self.page, "<form", "</form>")
        self.assertIn('method="get" action="/#second-opinion"', form)
        self.assertIn('<input id="dataset-address" name="dataset" type="text"', form)
        self.assertIn(">Έλεγχος και δεύτερη γνώμη</button>", form)
        self.assertIn('action="/en/#second-opinion"', block(self.english, "<form", "</form>"))

    def test_example_opens_with_the_tab_of_the_second_opinion(self):
        self.assertIn('<a href="/?example=1#second-opinion">Δοκιμάστε με το παράδειγμα «Τροχαία ατυχήματα»</a>', self.page)
        self.assertIn('<a href="/en/?example=1#second-opinion">', self.english)

    def test_page_lists_the_five_statements_under_their_criterion(self):
        card = block(self.page, '<div class="question-card">', "</div>")
        self.assertEqual(card.count("<li>"), 5)
        for statement in jev.STATEMENTS:
            self.assertIn(escape(self.texts.text(f"reading.row.{statement.key}")), card)
        self.assertLess(card.index("Τίτλος και περιγραφή"), card.index("Περιορισμοί των δεδομένων"))

    def test_texts_that_count_the_statements_agree_with_the_statements_of_the_model(self):
        english = load_texts("en")
        for key in ("reading.offer.preview", "opinion.lead", "opinion.step.3.title"):
            self.assertIn(COUNT_WORDS["el"][len(jev.STATEMENTS)], self.texts.text(key), key)
            self.assertIn(COUNT_WORDS["en"][len(jev.STATEMENTS)], english.text(key).lower(), key)

    def test_page_has_three_numbered_steps(self):
        steps = block(self.page, '<ol class="steps steps--three">', "</ol>")
        self.assertEqual(re.findall(r'<span class="step-number">(\d)</span>', steps), ["1", "2", "3"])

    def test_page_says_what_is_needed_what_is_sent_and_how_far_to_trust_the_answer(self):
        for key in ("opinion.need.key", "reading.offer.sent", "reading.offer.key_use", "reading.offer.scores",
                    "opinion.trust.lead", "guide.reading.trial"):
            self.assertIn(escape(self.texts.text(key)), self.page, key)
        self.assertIn("TypeSafe AI", self.page)
        self.assertIn('<a href="/terms/#reading">', self.page)
        self.assertIn('<a href="/en/terms/#reading">', self.english)

    def test_page_carries_no_inline_style(self):
        self.assertNotIn("style=", self.page)


if __name__ == "__main__":
    unittest.main()
