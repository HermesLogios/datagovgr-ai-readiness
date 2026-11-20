"""The parts of the home page for the search by words and for the recent checks, and what the page script gets
from the checks to keep a check."""

import json
import re
import unittest
from html import escape

from aiready.texts import load_texts
from fake_portal import found_reply
from sample_pages import EXAMPLE, SOURCE, page_model, snapshot_record
from web import browser, pages


def element(html: str, pattern: str) -> str:
    """The opening tag of the first element that matches a pattern."""
    found = re.search(pattern, html)
    if not found:
        raise AssertionError(f"no element matches {pattern}")
    return found[0]


class SearchPartsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.home = pages.home_main_html(cls.texts, page_model(EXAMPLE))

    def test_field_of_the_home_page_is_a_combobox_with_its_list_of_suggestions(self):
        field = element(self.home, r'<input id="dataset-address"[^>]*>')
        for attribute in ('role="combobox"', 'aria-autocomplete="list"', 'aria-expanded="false"',
                          'aria-controls="search-suggestions"', 'enterkeyhint="search"'):
            self.assertIn(attribute, field)
        self.assertNotIn("inputmode", field)
        listbox = element(self.home, r'<ul id="search-suggestions"[^>]*>')
        for attribute in ('role="listbox"', "hidden", f'aria-label="{escape(self.texts.text("search.suggestions"))}"',
                          f'data-status-many="{escape(self.texts.entries["search.status_many"])}"',
                          f'data-files-many="{escape(self.texts.entries["search.files_many"])}"'):
            self.assertIn(attribute, listbox)
        self.assertIn('<p id="search-status" class="visually-hidden" role="status"></p>', self.home)

    def test_form_of_another_page_takes_words_but_has_no_list_of_suggestions(self):
        form = pages.check_form_html(self.texts, action="/")
        self.assertNotIn("combobox", form)
        self.assertNotIn("search-suggestions", form)
        self.assertNotIn("inputmode", form)

    def test_templates_of_the_search_carry_the_texts_that_the_script_fills_in(self):
        listing = pages.search_list_html(self.texts)
        for key, attribute in (("search.title", "title"), ("search.count_one", "count-one"), ("search.count_all", "count-all"),
                               ("search.count_some", "count-some"), ("search.none", "none"), ("search.error", "error"),
                               ("search.modified", "modified"), ("search.files_one", "files-one")):
            self.assertIn(f'data-{attribute}="{escape(self.texts.entries[key])}"', listing, key)
        self.assertIn('<ol class="search-list"></ol>', listing)
        self.assertIn('<a class="search-link" data-goto href="">', pages.search_item_html())
        self.assertIn('role="option"', pages.suggestion_item_html())
        self.assertIn(escape(self.texts.text("search.loading")), pages.progress_html(self.texts, "search.loading"))


class RecentPartsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.home = pages.home_main_html(cls.texts, page_model(EXAMPLE))

    def test_recent_checks_stand_hidden_next_to_the_example_until_the_script_fills_them(self):
        side = self.home[self.home.index('<div class="hero-side">'):]
        self.assertLess(side.index('class="preview"'), side.index('<section class="recent"'))
        section = element(side, r'<section class="recent"[^>]*>')
        self.assertIn("hidden", section)
        self.assertIn('aria-labelledby="recent-title"', section)
        self.assertIn('<h2 id="recent-title">', side)
        self.assertIn(escape(self.texts.text("recent.title")), side)
        clear = element(side, r'<button type="button" class="recent-clear"[^>]*>')
        self.assertIn(f'data-confirm="{escape(self.texts.text("recent.confirm"))}"', clear)
        listing = element(side, r'<ol class="recent-list"[^>]*>')
        for key, attribute in (("recent.summary", "summary"), ("recent.remove", "remove")):
            self.assertIn(f'data-{attribute}="{escape(self.texts.entries[key])}"', listing)
        self.assertIn(escape(self.texts.text("recent.note")), side)

    def test_template_of_a_recent_check_opens_it_and_can_remove_it(self):
        item = pages.recent_item_html(self.texts)
        self.assertIn('<a class="recent-open" data-goto href="">', item)
        self.assertIn('<button type="button" class="recent-remove" data-recent-remove="" aria-label="">', item)
        link = item[item.index('<a class="recent-open"'):item.index("</a>")]
        self.assertIn(f'<span aria-hidden="true">{escape(self.texts.text("recent.badge"))}</span>', link)
        self.assertIn(f'<span class="visually-hidden">{escape(self.texts.text("recent.reading"))}</span>', link)

    def test_bar_of_a_kept_check_says_when_it_was_made_and_offers_a_new_check(self):
        bar = pages.stored_bar_html(self.texts)
        self.assertIn(f'data-text="{escape(self.texts.entries["stored.text"])}"', bar)
        self.assertIn(f'<a class="button button--dark stored-again" data-goto href="">{escape(self.texts.text("stored.again"))}</a>', bar)

    def test_terms_say_what_the_browser_keeps_and_what_the_search_asks(self):
        terms = pages.terms_main_html(self.texts)
        self.assertIn(f'<h2 id="storage">{escape(self.texts.text("terms.storage.title"))}</h2>', terms)
        self.assertLess(terms.index('id="data"'), terms.index('id="storage"'))
        for language in ("el", "en"):
            texts = load_texts(language)
            self.assertIn("localStorage", texts.text("terms.storage.text"))
            self.assertIn("Jev", texts.text("terms.storage.text"))
            self.assertIn("3", texts.text("terms.updated"))


EMAIL_ADDRESS = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Datasets of the snapshot with e-mail addresses in the contact point, the publisher, the creator, the description of
# the organisation, the description of the dataset and the address of a resource.
WITH_CONTACT_DETAILS = (EXAMPLE, "apologismos2016", "apofaseis-oikonomikoy-periexomenoy-ths-adae",
                        "apofash-dia8eshs-anoiktwn-dedomenwn-kai-epikairopoihshs-ths", "anarthsh-kenwn-8esewn-adei", "kl1",
                        "prokhry3eis-diagwnismoi-dhmoy-agrinioy")


class KeptCheckTest(unittest.TestCase):
    def test_kept_reply_holds_no_contact_details_and_gives_the_same_result(self):
        for name in WITH_CONTACT_DETAILS:
            record = snapshot_record(name)
            self.assertRegex(json.dumps(record, ensure_ascii=False), EMAIL_ADDRESS, name)
            day = SOURCE.date.isoformat()
            shown = json.loads(browser.assess_reply(found_reply([record]), name, "el", day))
            kept_text = shown["kept"]
            self.assertNotRegex(kept_text, EMAIL_ADDRESS, name)
            [kept] = json.loads(kept_text)["result"]["results"]
            for field in ("author", "author_email", "maintainer", "maintainer_email"):
                self.assertIsNone(kept.get(field), (name, field))
            again = json.loads(browser.assess_reply(kept_text, name, "el", day))
            self.assertEqual(again["html"], shown["html"], name)
            self.assertEqual(again["counts"], shown["counts"], name)

    def test_contact_point_keeps_a_value_only_where_it_had_one(self):
        record = dict(snapshot_record(EXAMPLE), contact=[{"name": "", "email": "", "uri": "", "url": ""}])
        [kept] = json.loads(json.loads(browser.result(record, SOURCE, "el", example=False))["kept"])["result"]["results"]
        self.assertEqual(kept["contact"], [{"name": "", "email": "", "uri": "", "url": ""}])
        record = dict(record, contact=[{"name": "Τμήμα", "email": "", "uri": "", "url": ""}])
        [kept] = json.loads(json.loads(browser.result(record, SOURCE, "el", example=False))["kept"])["result"]["results"]
        self.assertEqual(kept["contact"], [{"name": browser.CONTACT_PLACEHOLDER, "email": "", "uri": "", "url": ""}])

    def test_publisher_with_only_an_e_mail_address_keeps_a_value(self):
        record = dict(snapshot_record(EXAMPLE), publisher=[{"name": "", "email": "grafeio@example.gr"}])
        shown = json.loads(browser.result(record, SOURCE, "el", example=False))
        [kept] = json.loads(shown["kept"])["result"]["results"]
        self.assertEqual(kept["publisher"], [{"name": browser.PUBLISHER_PLACEHOLDER, "email": ""}])
        self.assertEqual(json.loads(browser.result(kept, SOURCE, "el", example=False))["html"], shown["html"])

    def test_result_gives_the_script_how_many_checks_are_met_out_of_all(self):
        shown = json.loads(browser.result(snapshot_record(EXAMPLE), SOURCE, "el", example=False))
        model = page_model(EXAMPLE)
        met = sum(pages.STATUS_KEYS[check.status] == "met" for check in model.checks)
        self.assertEqual(shown["counts"], {"met": met, "total": len(model.checks)})


if __name__ == "__main__":
    unittest.main()
