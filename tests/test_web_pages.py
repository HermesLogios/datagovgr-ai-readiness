"""Checks of the HTML of the public pages.

Usage:
    python -m unittest discover -s tests
"""

import dataclasses
import re
import unittest

from aiready.texts import load_texts
from sample_pages import EXAMPLE, UNMARKED, page_model
from web import pages

STATUS_ICON = 'class="status-icon status-icon--'


def block(html: str, opening: str, closing: str) -> str:
    """Part of the HTML from an opening tag to the first closing tag after it."""
    start = html.index(opening)
    return html[start:html.index(closing, start) + len(closing)]


class AddressTest(unittest.TestCase):
    def test_greek_pages_sit_at_the_root_and_english_pages_under_en(self):
        self.assertEqual(pages.page_path("home", "el"), "/")
        self.assertEqual(pages.page_path("home", "en"), "/en/")
        self.assertEqual(pages.page_path("guide", "el"), "/guide/")
        self.assertEqual(pages.page_path("terms", "en"), "/en/terms/")

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
        self.assertIn('<a href="/terms/">Όροι χρήσης</a>', navigation)

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

    def test_index_links_every_check_with_its_status_and_every_other_section(self):
        index = block(self.result, '<nav class="index"', "</nav>")
        for check in self.model.checks:
            self.assertIn(f'<a href="#check-{check.criterion_id}">', index)
            self.assertIn(f"<span>{check.title}</span>", index)
        self.assertEqual(index.count(STATUS_ICON), 9 + 2)       # nine checks and the two counts above zero
        self.assertIn("<strong>5</strong> Εντάξει", index)
        self.assertIn("<strong>4</strong> Εν μέρει", index)
        for target in ("fixes", "checklist", "report-files"):
            self.assertIn(f'<a href="#{target}">', index)
            self.assertIn(f'id="{target}"', self.result)

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
        self.assertEqual(self.result.count("<details"), 9)

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
        self.assertIn("Οι έλεγχοι των μεταδεδομένων δεν βρήκαν κάτι προς διόρθωση.", html)

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
        checklist = block(self.result, '<section id="checklist"', "</section>")
        self.assertEqual(checklist.count('type="checkbox"'), 14)
        for item in self.model.checklist_files + self.model.checklist_judgement:
            self.assertIn(f'<input type="checkbox" id="tick-{item.criterion_id}"', checklist)
            self.assertIn(f'<label for="tick-{item.criterion_id}">', checklist)
        self.assertEqual(checklist.count("Αν όχι:"), 14)
        self.assertEqual(checklist.count("Βασικό κριτήριο."), 3)
        self.assertEqual(checklist.count("<fieldset"), 2)

    def test_report_is_offered_in_three_formats(self):
        files = block(self.result, '<section id="report-files"', "</section>")
        self.assertEqual(re.findall(r'<button type="button" class="button button--file" data-format="(\w+)"', files),
                         ["xlsx", "md", "json"])
        self.assertIn("Λήψη σε Excel", files)

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
            self.assertEqual(terms.count("<h2>"), 8)

    def test_no_page_leaves_a_field_of_a_text_unfilled(self):
        for language in ("el", "en"):
            texts = load_texts(language)
            model = page_model(EXAMPLE, language)
            parts = (pages.home_main_html(texts, model), pages.result_html(model, texts, example=True),
                     pages.guide_main_html(texts), pages.terms_main_html(texts))
            for part in parts:
                document = pages.document_html("home", texts, part, criteria_version="1.2")
                self.assertIsNone(re.search(r"\{[a-z_]+\}", document), language)


if __name__ == "__main__":
    unittest.main()
