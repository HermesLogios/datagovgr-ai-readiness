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
from aiready.criteria import result_kind
from aiready.metadata_checks import CHECK_IDS
from aiready.plain_language import CHECKLIST_FILES, criterion_title, level_key
from aiready.second_reading import build_reading_model, figure_of
from aiready.texts import load_texts
from sample_pages import CRITERIA, EXAMPLE, UNMARKED, page_model
from web import icons, pages, release

STATUS_ICON = 'class="status-icon status-icon--'
COUNT_WORDS = {"el": {4: "τέσσερις", 5: "πέντε", 6: "έξι", 9: "εννέα", 10: "δέκα"},
               "en": {4: "four", 5: "five", 6: "six", 9: "nine", 10: "ten"}}
NEW_TAB = 'target="_blank" rel="noopener noreferrer"'


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
        self.assertEqual(pages.page_path("criteria", "el"), "/criteria/")
        self.assertEqual(pages.page_path("criteria", "en"), "/en/criteria/")

    def test_unknown_page_or_language_is_refused(self):
        with self.assertRaises(KeyError):
            pages.page_path("prices", "el")
        with self.assertRaises(ValueError):
            pages.page_path("home", "fr")


class DocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.document = pages.document_html("guide", cls.texts, "<p>main part</p>")

    def test_document_declares_its_language_and_its_name(self):
        self.assertTrue(self.document.startswith('<!DOCTYPE html>\n<html lang="el">'))
        self.assertIn("<title>Οδηγός χρήσης | Έλεγχος ετοιμότητας δεδομένων</title>", self.document)
        english = pages.document_html("home", load_texts("en"), "")
        self.assertIn('<html lang="en">', english)
        self.assertIn("<title>Data readiness check</title>", english)

    def test_head_links_the_icon_of_old_browsers_before_the_svg_icon_and_the_icon_of_phones(self):
        head = block(self.document, "<head>", "</head>")
        self.assertIn('<link rel="icon" href="/favicon.ico" sizes="32x32">', head)
        self.assertIn('<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">', head)
        self.assertIn('<link rel="apple-touch-icon" href="/apple-touch-icon.png">', head)
        self.assertLess(head.index('href="/favicon.ico"'), head.index('href="/assets/favicon.svg"'))

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

    def test_navigation_lists_the_five_pages_with_the_check_first(self):
        navigation = block(self.document, '<nav class="site-nav"', "</nav>")
        self.assertEqual(re.findall(r'<a href="([^"]+)"', navigation),
                         ["/", "/second-opinion/", "/guide/", "/criteria/", "/terms/"])
        self.assertIn('<a href="/">Έλεγχος</a>', navigation)
        self.assertIn('<a href="/second-opinion/" data-opinion-link>Δεύτερη γνώμη ΤΝ</a>', navigation)
        self.assertIn('<a href="/criteria/">Κριτήρια</a>', navigation)

    def test_page_of_the_criteria_is_marked_in_the_navigation_and_named_in_the_title(self):
        english = pages.document_html("criteria", load_texts("en"), "")
        self.assertIn('<a href="/en/criteria/" aria-current="page">Criteria</a>', english)
        self.assertIn("<title>Criteria | Data readiness check</title>", english)
        self.assertIn('<a href="/criteria/" lang="el" hreflang="el">Ελληνικά</a>', english)
        english = pages.document_html("opinion", load_texts("en"), "")
        self.assertIn('<a href="/en/second-opinion/" data-opinion-link aria-current="page">AI second opinion</a>', english)
        self.assertIn("<title>AI second opinion | Data readiness check</title>", english)

    def test_footer_shows_the_version_of_the_application_and_its_day(self):
        footer = block(self.document, "<footer", "</footer>")
        self.assertRegex(release.VERSION, r"^\d+\.\d+(\.\d+)?$")
        self.assertIn('<p class="site-version"><span class="visually-hidden">Έκδοση της εφαρμογής: </span>'
                      f"v{release.VERSION} · {self.texts.date(release.RELEASED)}</p>", footer)
        english = pages.document_html("home", load_texts("en"), "")
        self.assertIn(f"v{release.VERSION} · {load_texts('en').date(release.RELEASED)}</p>", english)

    def test_only_number_at_the_foot_of_a_page_is_the_version_of_the_application(self):
        for language in ("el", "en"):
            footer = block(pages.document_html("home", load_texts(language), ""), "<footer", "</footer>")
            self.assertNotRegex(block(footer, "<p>", "</p>"), r"\d", language)
            self.assertEqual(len(re.findall(r">[^<]*\d[^<]*<", footer)), 1, language)

    def test_footer_names_the_study_and_links_the_code_and_the_terms(self):
        footer = block(self.document, "<footer", "</footer>")
        self.assertTrue(block(footer, "<p>", "</p>").endswith("του Πανεπιστημίου Αιγαίου στην ΕΕΛΛΑΚ.</p>"))
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

    def test_every_check_carries_the_code_of_its_criterion_before_its_name(self):
        cards = re.findall(r'<article class="check .*?</article>', self.result, re.DOTALL)
        for card, check in zip(cards, self.model.checks):
            code = check.criterion_id
            tag = (f'<a class="code-tag" href="/criteria/#{code}" {NEW_TAB} '
                   f'title="Κριτήριο {code}: πώς βαθμολογείται (ανοίγει σε νέα καρτέλα)">{code}</a>')
            self.assertIn(f'<div class="check-name">{tag}<h4>{check.title}</h4></div>', card)

    def test_code_of_a_criterion_leads_to_the_page_of_the_language(self):
        english = pages.result_html(page_model(EXAMPLE, "en"), load_texts("en"))
        self.assertIn(f'<a class="code-tag" href="/en/criteria/#M1" {NEW_TAB} '
                      'title="Criterion M1: how it is scored (opens in a new tab)">M1</a>', english)

    def test_details_give_the_code_the_reason_and_the_rule_in_the_language_of_the_page(self):
        self.assertIn("Κριτήριο M1 της μελέτης, «Mandatory metadata». Βαθμός 1 από 2.", self.result)
        self.assertIn("Αιτιολογία του ελέγχου, όπως τη γράφει ο κώδικας: description of 76 characters (minimum 100)", self.result)
        self.assertIn("Κανόνας για τον βαθμό 1: Υπάρχουν όλα, αλλά η περιγραφή επαναλαμβάνει τον τίτλο ή έχει λιγότερους "
                      "από 100 χαρακτήρες.", self.result)
        self.assertEqual(self.result.count('<details class="check-details">'), 9)
        english = pages.result_html(page_model(EXAMPLE, "en"), load_texts("en"))
        self.assertIn("Criterion M1, Mandatory metadata. Score 1 out of 2.", english)
        self.assertIn(f"Rule for score 1: {CRITERIA['M1'].score_1}", english)

    def test_details_lead_to_all_the_scores_of_the_criterion(self):
        self.assertEqual(self.result.count('<p class="check-rules">'), 9)
        self.assertIn(f'<p class="check-rules"><a href="/criteria/#M1" {NEW_TAB}>'
                      "Όλοι οι βαθμοί του κριτηρίου M1, στη σελίδα «Κριτήρια»", self.result)
        self.assertNotIn("criteria.csv", self.result)

    def test_checks_and_checklist_say_what_the_codes_are(self):
        note = escape(self.texts.text("codes.note"))
        self.assertIn("M1", note)
        for name in ("checks", "checklist"):
            self.assertEqual(panel(self.result, name).count(f'<p class="block-intro">{note}</p>'), 1, name)

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

    def test_every_row_of_the_checklist_names_its_criterion_with_its_code_above_the_question(self):
        checklist = block(self.result, '<section id="by-hand"', "</section>")
        rows = re.findall(r'<div class="tick">.*?</div>', checklist, re.DOTALL)
        items = self.model.checklist_files + self.model.checklist_judgement
        self.assertEqual(len(rows), len(items))
        for row, item in zip(rows, items):
            code = item.criterion_id
            self.assertIn(f'<p class="tick-name"><a class="code-tag" href="/criteria/#{code}" {NEW_TAB} ', row)
            self.assertIn(f">{code}</a><span>{escape(item.name)}</span>", row)
            self.assertLess(row.index('<p class="tick-name">'), row.index(f'<label for="tick-{code}">'))
            self.assertNotIn("<a", block(row, "<label", "</label>"))
            self.assertEqual("Βασικό κριτήριο." in block(row, '<p class="tick-name">', "</p>"), item.core, code)
        self.assertIn("<span>Διαθεσιμότητα αρχείων</span>", rows[0])

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

    def test_note_under_a_result_names_no_version_of_the_criteria(self):
        for language in ("el", "en"):
            texts = load_texts(language)
            note = block(pages.result_html(page_model(EXAMPLE, language), texts), '<p class="result-disclaimer">', "<a ")
            self.assertEqual(note, f'<p class="result-disclaimer">{escape(texts.text("result.disclaimer"))} <a ')
            self.assertNotRegex(note, r"\d", language)


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
        self.assertIn('<label for="dataset-address">Σύνολο του data.gov.gr: σύνδεσμος ή λέξεις</label>', form)
        self.assertIn('<input id="dataset-address" name="dataset" type="text"', form)
        self.assertIn('placeholder="π.χ. τροχαία ατυχήματα ή https://data.gov.gr/dataset/..."', form)
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
            self.assertEqual(terms.count("<h2 id="), 10)

    def test_guide_leads_to_the_page_of_the_criteria(self):
        greek, english = pages.guide_main_html(load_texts("el")), pages.guide_main_html(load_texts("en"))
        self.assertIn('<p class="know-link"><a href="/criteria/">', greek)
        self.assertIn('<p class="know-link"><a href="/en/criteria/">', english)
        self.assertIn("στη σελίδα «Κριτήρια»", greek)

    def test_no_page_leaves_a_field_of_a_text_unfilled(self):
        for language in ("el", "en"):
            texts = load_texts(language)
            model = page_model(EXAMPLE, language)
            parts = (pages.home_main_html(texts, model), pages.result_html(model, texts, example=True),
                     pages.opinion_main_html(texts), pages.guide_main_html(texts), pages.terms_main_html(texts),
                     pages.criteria_main_html(texts, CRITERIA))
            for part in parts:
                document = pages.document_html("home", texts, part)
                shown = re.sub(r' data-[a-z-]+="[^"]*"', "", document)   # texts that the script of the page fills in
                self.assertIsNone(re.search(r"\{[a-z_]+\}", shown), language)


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

    def test_offer_shows_the_statements_with_empty_meters_under_their_criterion_and_the_category(self):
        preview = block(self.result, '<div class="reading-preview">', "</div>")
        self.assertIn('<p class="reading-preview-title">Οι ερωτήσεις</p>', preview)
        self.assertEqual(preview.count('<li class="reading-ask-row">'), len(jev.STATEMENTS) + 1)
        self.assertEqual(preview.count('<svg class="reading-meter"'), len(jev.STATEMENTS))
        self.assertNotIn("reading-fill", preview)
        marks = [preview.index(words) for words in ("Τίτλος και περιγραφή", "Λέει τι περιέχουν", "Περιορισμοί των δεδομένων",
                                                    "Αναφέρει περιοχή", "Λέει πόσο ακριβή είναι", "Σήμανση υψηλής αξίας")]
        self.assertEqual(marks, sorted(marks))

    def test_questions_stand_under_the_code_of_their_criterion(self):
        preview = block(self.result, '<div class="reading-preview">', "</div>")
        for code, name in (("M1", "Τίτλος και περιγραφή"), ("AI7", "Περιορισμοί των δεδομένων")):
            heading = f'<h4 class="reading-group"><a class="code-tag" href="/criteria/#{code}" {NEW_TAB} '
            self.assertIn(heading, preview)
            self.assertIn(heading, self.reading)
            self.assertIn(f">{code}</a><span>{name}</span></h4>", preview)
            self.assertIn(f">{code}</a><span>{name}</span></h4>", self.reading)

    def test_offer_leads_to_the_way_to_a_key_without_leaving_the_result(self):
        line = block(self.result, '<p class="reading-help">', "</p>")
        self.assertIn(f'<a href="/second-opinion/#key" {NEW_TAB}>Δεν έχετε κλειδί; Δείτε πώς αποκτάτε ένα', line)
        self.assertNotIn("data-opinion-link", line)
        self.assertLess(self.result.index("</form>"), self.result.index('<p class="reading-help">'))
        self.assertLess(self.result.index('<p class="reading-help">'), self.result.index('<ul class="reading-facts">'))
        english = pages.result_html(page_model(EXAMPLE, "en"), load_texts("en"))
        self.assertIn(f'<a href="/en/second-opinion/#key" {NEW_TAB}>No key yet? See how to get one', english)

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
        self.assertIn('<p class="article-note">Όροι χρήσης, έκδοση 3, Νοέμβριος 2026.', pages.terms_main_html(self.texts))
        self.assertIn('<p class="article-note">Terms of use, version 3, November 2026.',
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

    def test_page_lists_the_statements_under_their_criterion_and_the_category(self):
        card = block(self.page, '<div class="question-card">', "</div>")
        self.assertEqual(card.count("<li>"), len(jev.STATEMENTS) + 1)
        for key in [statement.key for statement in jev.STATEMENTS] + [jev.CATEGORY_QUESTION.key]:
            self.assertIn(escape(self.texts.text(f"reading.row.{key}")), card)
        self.assertLess(card.index("Τίτλος και περιγραφή"), card.index("Περιορισμοί των δεδομένων"))

    def test_texts_that_count_the_questions_agree_with_the_questions_of_the_model(self):
        english = load_texts("en")
        counted = {"opinion.lead": len(jev.STATEMENTS) + 1, "guide.reading.text": len(jev.STATEMENTS) + 1,
                   "opinion.how.sent": len(jev.STATEMENTS)}
        for key, count in counted.items():
            self.assertIn(COUNT_WORDS["el"][count], self.texts.text(key, likely="", unlikely=""), key)
            self.assertIn(COUNT_WORDS["en"][count], english.text(key, likely="", unlikely="").lower(), key)

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

    def test_page_explains_how_the_model_works_and_then_how_to_get_a_key(self):
        marks = [self.page.index(mark) for mark in ('<ol class="steps steps--three">', '<section class="explain" id="how">',
                                                    '<section class="explain explain--key" id="key">',
                                                    '<section class="notes">')]
        self.assertEqual(marks, sorted(marks))
        self.assertIn('<section class="explain" id="how">', self.english)
        self.assertIn('<section class="explain explain--key" id="key">', self.english)

    def test_page_says_what_the_model_does_with_the_texts(self):
        section = block(self.page, '<section class="explain" id="how">', "</section>")
        self.assertIn("<h2>Πώς δουλεύει το Jev</h2>", section)
        for key in ("opinion.how.model", "opinion.how.sent", "opinion.how.scores", "opinion.how.criteria"):
            self.assertIn(escape(self.texts.text(key)), section, key)
        self.assertIn("έναν αριθμό από 0 έως 1", section)
        self.assertIn(f"από {figure_of(jev.LIKELY, self.texts)} και πάνω «Μάλλον ναι», "
                      f"έως {figure_of(jev.UNLIKELY, self.texts)} «Μάλλον όχι»", section)
        self.assertIn("«Αβέβαιο»", section)

    def test_example_of_a_statement_is_a_statement_that_the_model_receives(self):
        self.assertIn(jev.STATEMENTS[0].instructions, load_texts("en").text("opinion.how.sent"))

    def test_page_names_the_criteria_of_the_questions_with_their_codes_and_their_numbers(self):
        section = block(self.page, '<section class="explain" id="how">', "</section>")
        rows = re.findall(r'<li><a class="code-tag" href="/criteria/#(\w+)" title="[^"]+">\w+</a><span>([^<]+)</span></li>', section)
        self.assertEqual([code for code, _ in rows], ["M1", "M2", "M8", "AI2", "AI7", "M9"])
        self.assertEqual(rows[0], ("M1", "Τίτλος και περιγραφή: μία ερώτηση"))
        self.assertEqual(rows[3], ("AI2", "Τεκμηρίωση της δομής: 2 ερωτήσεις"))
        self.assertEqual(rows[4], ("AI7", "Δηλωμένοι περιορισμοί: 4 ερωτήσεις"))
        self.assertNotIn("target=", block(section, '<ul class="explain-criteria">', "</ul>"))
        self.assertEqual(pages.statement_counts(), {"M1": 1, "M2": 1, "M8": 1, "AI2": 2, "AI7": 4, "M9": 1})

    def test_page_gives_four_steps_to_a_key_with_the_address_of_the_console(self):
        section = block(self.page, '<section class="explain explain--key" id="key">', "</section>")
        self.assertIn("<h2>Πώς αποκτάτε κλειδί</h2>", section)
        steps = block(section, '<ol class="key-steps">', "</ol>")
        self.assertEqual(re.findall(r'<li><span class="step-number">(\d)</span>', steps), ["1", "2", "3", "4"])
        self.assertIn(f'<a href="https://console.typesafe.ai/keys" {NEW_TAB}>console.typesafe.ai/keys', steps)
        for words in ("«API Keys»", "«Create key»", "«Το κλειδί σας για το Jev»", "«Δεύτερη γνώμη ΤΝ»"):
            self.assertIn(words, steps)
        english = block(self.english, '<ol class="key-steps">', "</ol>")
        for words in ("“API Keys”", "“Create key”", "“Your key for Jev”", "“AI second opinion”"):
            self.assertIn(words, english)

    def test_page_says_who_charges_the_use_and_when_the_steps_were_checked(self):
        section = block(self.page, '<section class="explain explain--key" id="key">', "</section>")
        self.assertIn(f'<a href="https://docs.typesafe.ai/models" {NEW_TAB}>', section)
        for key in ("opinion.key.lead", "opinion.key.care", "opinion.key.cost"):
            self.assertIn(escape(self.texts.text(key)), section, key)
        self.assertIn(f"Τα βήματα ελέγχθηκαν στις {self.texts.date(pages.KEY_STEPS_CHECKED)}.", section)
        self.assertIn(f"The steps were checked on {load_texts('en').date(pages.KEY_STEPS_CHECKED)}.", self.english)

    def test_sketch_of_the_console_holds_only_the_two_names_and_the_numbers_of_their_steps(self):
        figure = block(self.page, '<figure class="key-figure">', "</figure>")
        self.assertEqual(sorted(re.findall(r"<text[^>]*>([^<]+)</text>", figure)), ["2", "3", "API Keys", "Create key"])
        self.assertIn('aria-hidden="true"', block(figure, "<svg", ">"))
        caption = block(figure, "<figcaption>", "</figcaption>")
        self.assertIn("Σχέδιο της κονσόλας, όχι φωτογραφία της.", caption)
        self.assertIn("Το 2 δείχνει το «API Keys»", caption)
        self.assertIn("το 3 το «Create key»", caption)
        for mark in ("<image", "href=", "style=", "<script"):
            self.assertNotIn(mark, figure)
        self.assertEqual(figure, block(self.english, '<figure class="key-figure">', "</figure>").replace(
            block(block(self.english, '<figure class="key-figure">', "</figure>"), "<figcaption>", "</figcaption>"), caption))


class CriteriaPageTest(unittest.TestCase):
    KINDS = {"by rule": "Βαθμός από κανόνα", "proposal": "Πρόταση βαθμού", "files": "Λίστα ελέγχου: θέλει τα αρχεία",
             "judgement": "Λίστα ελέγχου: θέλει κρίση ανθρώπου"}

    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.page = pages.criteria_main_html(cls.texts, CRITERIA)
        cls.english = pages.criteria_main_html(load_texts("en"), CRITERIA)

    @staticmethod
    def kind_of(code: str) -> str:
        if code in CHECK_IDS:
            return result_kind(CRITERIA[code])
        return "files" if code in CHECKLIST_FILES else "judgement"

    def section(self, code: str, page: str | None = None) -> str:
        return block(page or self.page, f'<section class="criterion" id="{code}"', "</section>")

    def test_heading_names_the_number_of_the_criteria(self):
        self.assertEqual(len(CRITERIA), 23)
        self.assertIn(f"<h1>Τα {len(CRITERIA)} κριτήρια και πώς βαθμολογούνται</h1>", self.page)
        self.assertIn(f"<h1>The {len(CRITERIA)} criteria and how they are scored</h1>", self.english)

    def test_every_criterion_has_a_section_under_its_code_in_the_order_of_the_criteria_file(self):
        for page in (self.page, self.english):
            self.assertEqual(re.findall(r'<section class="criterion" id="(\w+)"', page), list(CRITERIA))

    def test_sections_stand_under_the_three_levels_with_their_first_and_last_code(self):
        self.assertEqual(re.findall(r'<h2 id="level-(\w+)">([^<]+)</h2>', self.page),
                         [("Q", "Ποιότητα (Q1 έως Q6)"), ("M", "Μεταδεδομένα και νομικό καθεστώς (M1 έως M10)"),
                          ("AI", "Ετοιμότητα για ΤΝ (AI1 έως AI7)")])
        self.assertLess(self.page.index('<h2 id="level-M">'), self.page.index('<section class="criterion" id="M1"'))
        self.assertLess(self.page.index('<section class="criterion" id="Q6"'), self.page.index('<h2 id="level-M">'))

    def test_section_gives_the_name_the_question_and_the_rule_of_every_score(self):
        for code, criterion in CRITERIA.items():
            section = self.section(code)
            self.assertIn(f'<h3 id="name-{code}">{escape(criterion_title(code, self.texts))}</h3>', section)
            self.assertIn(f'<span class="code-tag code-tag--plain">{code}</span>', section)
            self.assertIn(f'<span lang="en">{escape(criterion.name)}</span>', section)
            for field in ("question", "score_2", "score_1", "score_0"):
                self.assertIn(escape(self.texts.text(f"criterion.{code}.{field}")), section, f"{code} {field}")
            self.assertEqual(re.findall(r"</span>(\d)</dt>", section), ["2", "1", "0"], code)
            self.assertEqual("<dt>Δεν εφαρμόζεται</dt>" in section, bool(criterion.not_applicable), code)
            if criterion.not_applicable:
                self.assertIn(escape(self.texts.text(f"criterion.{code}.not_applicable")), section, code)

    def test_score_is_shown_with_the_sign_that_a_result_uses_for_it(self):
        section = self.section("M1")
        signs = re.findall(r'<dt><svg class="status-icon status-icon--(\w+)"', section)
        self.assertEqual(signs, ["met", "partly", "not_met"])

    def test_section_says_how_the_application_treats_the_criterion(self):
        for code, criterion in CRITERIA.items():
            section = self.section(code)
            self.assertIn(f'<span class="badge badge--kind">{self.KINDS[self.kind_of(code)]}</span>', section, code)
            self.assertEqual('<span class="badge">Βασικό κριτήριο</span>' in section, criterion.core, code)
            self.assertEqual('<span class="badge badge--scope">Μόνο για σύνολα υψηλής αξίας</span>' in section,
                             criterion.applies_to == "high-value", code)

    def test_section_says_what_the_application_checks_or_why_it_gives_no_score(self):
        tab = self.texts.quoted(self.texts.text("tabs.checklist"))
        for code in CRITERIA:
            section = self.section(code)
            kind = self.kind_of(code)
            if code in CHECK_IDS:
                self.assertIn(escape(self.texts.text(f"criterion.{code}.how")), section, code)
            else:
                self.assertIn(escape(self.texts.text(f"criteria.app.{kind}", tab=tab)), section, code)
        self.assertIn("στην καρτέλα «Λίστα ελέγχου» του αποτελέσματος", self.section("Q1"))

    def test_criteria_of_the_second_opinion_say_how_many_questions_it_asks_about_them(self):
        asked = {code: pages.statement_counts().get(code, 0) for code in CRITERIA}
        for code, count in asked.items():
            self.assertEqual('<a href="/second-opinion/#how">' in self.section(code), count > 0, code)
        self.assertIn("Η δεύτερη γνώμη ΤΝ έχει μία ερώτηση για αυτό το κριτήριο.", self.section("M1"))
        self.assertIn(f"Η δεύτερη γνώμη ΤΝ έχει {asked['AI7']} ερωτήσεις για αυτό το κριτήριο.", self.section("AI7"))
        self.assertIn('<a href="/en/second-opinion/#how">', self.section("AI7", self.english))

    def test_page_has_no_table_of_the_criteria(self):
        for page in (self.page, self.english):
            self.assertNotIn("<table", page)
            self.assertNotIn('id="all"', page)

    def test_criteria_of_a_level_stand_in_one_grid_under_the_heading_of_the_level(self):
        chunks = self.page.split('<h2 id="level-')[1:]
        self.assertEqual(len(chunks), 3)
        for chunk, level in zip(chunks, ("Q", "M", "AI")):
            after_heading = chunk[chunk.index("</h2>") + len("</h2>"):]
            self.assertTrue(after_heading.startswith('<div class="criteria-grid">'), level)
            self.assertEqual(re.findall(r'<section class="criterion" id="(\w+)"', chunk),
                             [code for code in CRITERIA if level_key(code) == level])
        self.assertEqual(self.page.count('<div class="criteria-grid">'), 3)

    def test_every_criterion_shows_its_names_and_opens_its_rules_under_them(self):
        toggle = f'<summary><span>Πώς βαθμολογείται</span>{icons.line_icon("chevron-down")}</summary>'
        for code in CRITERIA:
            head, opened = self.section(code).split('<details class="criterion-more">')
            for part in (f'<h3 id="name-{code}">', '<p class="criterion-study">', '<span class="badge badge--kind">'):
                self.assertIn(part, head, code)
            self.assertTrue(opened.startswith(toggle), code)
            for field in ("question", "score_2", "score_1", "score_0"):
                self.assertIn(escape(self.texts.text(f"criterion.{code}.{field}")), opened, f"{code} {field}")
            self.assertIn('<div class="criterion-app">', opened)
        self.assertNotIn("<details open", self.page)
        self.assertIn("<summary><span>How it is scored</span>", self.english)

    def test_button_that_opens_all_the_criteria_waits_for_the_script(self):
        tools = block(self.page, '<div class="criteria-tools">', "</div>")
        self.assertIn('<button type="button" class="criteria-toggle" data-toggle-all aria-expanded="false" '
                      'data-open-label="Άνοιγμα όλων" data-close-label="Κλείσιμο όλων" hidden>', tools)
        self.assertIn("<span>Άνοιγμα όλων</span>", tools)
        self.assertLess(self.page.index('<div class="criteria-tools">'), self.page.index('<h2 id="level-Q">'))
        self.assertIn('data-open-label="Open all" data-close-label="Close all"', self.english)

    def test_scale_names_the_criteria_of_every_treatment_and_the_core_ones(self):
        scale = self.page[self.page.index('<h2 id="scale">'):self.page.index('<div class="criteria-tools">')]
        by_kind = {kind: ", ".join(code for code in CRITERIA if self.kind_of(code) == kind) for kind in self.KINDS}
        self.assertEqual(by_kind["by rule"], "M2, M3, M9")
        self.assertEqual(by_kind["proposal"], "Q5, Q6, M1, M4, M6, M7")
        checklist = ", ".join(code for code in CRITERIA if code not in CHECK_IDS)
        for codes in (by_kind["by rule"], by_kind["proposal"], checklist):
            self.assertIn(f"Κριτήρια: {codes}.", scale)
        self.assertIn("Βασικά κριτήρια είναι τα Q1, Q6, M1, M4, AI1, AI2.", scale)
        self.assertEqual(", ".join(code for code, criterion in CRITERIA.items() if criterion.core), "Q1, Q6, M1, M4, AI1, AI2")
        self.assertIn("Τα M9, M10 ισχύουν μόνο για τα σύνολα υψηλής αξίας.", scale)
        self.assertIn("το 2 φαίνεται ως «Εντάξει», το 1 ως «Εν μέρει» και το 0 ως «Όχι»", scale)
        self.assertIn("γράφει «Δεν μετριέται»", scale)

    def test_english_page_gives_the_rules_of_the_criteria_file(self):
        for code, criterion in CRITERIA.items():
            section = self.section(code, self.english)
            for text in (criterion.question, criterion.score_2, criterion.score_1, criterion.score_0, criterion.not_applicable):
                self.assertIn(escape(text), section, code)

    def test_page_leads_to_the_full_text_of_the_criteria_in_the_repository(self):
        self.assertIn('<a href="https://github.com/HermesLogios/datagovgr-ai-readiness/blob/main/criteria/criteria.md" '
                      f"{NEW_TAB}>", self.page)
        self.assertIn("έκδοση 1.3", self.page[self.page.index('<h2 id="source">'):])

    def test_no_address_of_the_page_is_used_twice_and_no_style_is_written_inline(self):
        addresses = re.findall(r' id="([^"]+)"', self.page)
        self.assertEqual(len(addresses), len(set(addresses)))
        self.assertNotIn("style=", self.page)


if __name__ == "__main__":
    unittest.main()
