"""What a shared link of the site shows, and the links that open an issue about a mistake on GitHub."""

import re
import unittest
from html import escape, unescape
from urllib.parse import parse_qs, urlsplit

from aiready.texts import load_texts
from sample_pages import EXAMPLE, page_model
from test_icons import read_png
from web import icon_images, pages, release

SITE = "https://datagovgr-ai-readiness.hermeslogios.workers.dev"
NAVY, GOLD = (0x0D, 0x1B, 0x3E), (0xF5, 0x9E, 0x0B)
ISSUES = "https://github.com/HermesLogios/datagovgr-ai-readiness/issues/new?"


def meta(document: str, name: str) -> str:
    """Content of a meta element of the head, by its property or its name."""
    found = re.search(rf'<meta (?:property|name)="{re.escape(name)}" content="([^"]*)">', document)
    return unescape(found[1]) if found else ""


def issue_of(link: str) -> dict[str, str]:
    """Title and body of the issue that a link of the page opens."""
    parts = urlsplit(unescape(link))
    return {key: values[0] for key, values in parse_qs(parts.query).items()}


class PreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.document = pages.document_html("criteria", cls.texts, "<p>κείμενο</p>")
        cls.english = pages.document_html("guide", load_texts("en"), "<p>text</p>")

    def test_shared_link_shows_the_title_the_description_and_the_address_of_the_page(self):
        title = re.search(r"<title>([^<]+)</title>", self.document)[1]
        self.assertEqual(meta(self.document, "og:title"), unescape(title))
        self.assertEqual(meta(self.document, "og:description"), self.texts.text("home.lead"))
        self.assertEqual(meta(self.document, "og:site_name"), self.texts.text("app.name"))
        self.assertEqual(meta(self.document, "og:url"), f"{SITE}/criteria/")
        self.assertEqual(meta(self.document, "og:type"), "website")
        self.assertEqual(meta(self.document, "og:locale"), "el_GR")
        self.assertEqual(meta(self.english, "og:url"), f"{SITE}/en/guide/")
        self.assertEqual(meta(self.english, "og:locale"), "en_GB")

    def test_shared_link_shows_the_large_picture_of_the_mark_with_its_size_and_description(self):
        self.assertEqual(meta(self.document, "og:image"), f"{SITE}/assets/social-preview.png")
        self.assertEqual((meta(self.document, "og:image:width"), meta(self.document, "og:image:height")), ("1200", "630"))
        self.assertEqual(meta(self.document, "og:image:alt"), self.texts.text("preview.image_alt"))
        self.assertEqual(meta(self.document, "twitter:card"), "summary_large_image")

    def test_picture_is_the_mark_in_the_middle_of_the_dark_ground(self):
        width, height, pixels = read_png(icon_images.social_image_png())
        self.assertEqual((width, height), (1200, 630))
        self.assertTrue(all(pixel == NAVY + (255,) for pixel in (pixels[0][0], pixels[629][1199], pixels[315][100])))
        self.assertEqual(pixels[334][600], GOLD + (255,))


class ReportLinkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = load_texts("el")
        cls.document = pages.document_html("criteria", cls.texts, "<p>κείμενο</p>")
        cls.model = page_model(EXAMPLE)
        cls.result = pages.result_html(cls.model, cls.texts)

    def link(self, html: str, text: str) -> str:
        found = re.search(rf'<a href="({re.escape(ISSUES)}[^"]+)" target="_blank" rel="noopener noreferrer">(?:<[^>]+>)*'
                          rf'{re.escape(escape(text))}', html)
        self.assertIsNotNone(found, text)
        return found[1]

    def test_footer_opens_an_issue_with_the_page_and_the_version_already_written(self):
        footer = self.document[self.document.index('<footer class="site-footer">'):]
        issue = issue_of(self.link(footer, self.texts.text("footer.report")))
        self.assertEqual(issue["title"], self.texts.text("report.title"))
        for line in (self.texts.text("report.page", address=f"{SITE}/criteria/"),
                     self.texts.text("report.version", version=release.VERSION),
                     self.texts.text("report.seen"), self.texts.text("report.expected"), self.texts.text("report.public")):
            self.assertIn(line, issue["body"])

    def test_result_opens_an_issue_about_its_dataset(self):
        issue = issue_of(self.link(self.result, self.texts.text("report.result_link")))
        self.assertEqual(issue["title"], self.texts.text("report.result_title", dataset=self.model.name))
        self.assertIn(self.texts.text("report.dataset", address=self.model.url), issue["body"])
        self.assertIn(self.texts.text("report.page", address=f"{SITE}/?dataset={self.model.name}"), issue["body"])
        self.assertIn(self.texts.text("report.public"), issue["body"])

    def test_links_open_in_a_new_tab_and_say_so(self):
        for html, text in ((self.document, self.texts.text("footer.report")),
                           (self.result, self.texts.text("report.result_link"))):
            start = html.index(self.link(html, text))
            self.assertIn(self.texts.text("new_tab"), html[start:html.index("</a>", start)])


if __name__ == "__main__":
    unittest.main()
