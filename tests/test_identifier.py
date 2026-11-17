"""Tests of the reading of a dataset name, identifier or address."""

import unittest

from aiready.identifier import DatasetIdentifier, parse_dataset_identifier

NAME = DatasetIdentifier("name", "troxaia-atyxhmata")
UUID_TEXT = "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9"


class IdentifierTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(parse_dataset_identifier("troxaia-atyxhmata"), NAME)
        self.assertEqual(parse_dataset_identifier("  Troxaia-Atyxhmata \n"), NAME)
        self.assertEqual(
            parse_dataset_identifier("gis-ypen-wfd-wms-kallikratikoi_dimoi"),
            DatasetIdentifier("name", "gis-ypen-wfd-wms-kallikratikoi_dimoi"),
        )

    def test_identifier(self):
        self.assertEqual(parse_dataset_identifier(UUID_TEXT), DatasetIdentifier("id", UUID_TEXT))
        self.assertEqual(parse_dataset_identifier(UUID_TEXT.upper()), DatasetIdentifier("id", UUID_TEXT))

    def test_addresses_of_the_portal(self):
        addresses = [
            "https://data.gov.gr/dataset/troxaia-atyxhmata",
            "https://data.gov.gr/dataset/troxaia-atyxhmata/",
            "http://www.data.gov.gr/dataset/troxaia-atyxhmata",
            "data.gov.gr/dataset/troxaia-atyxhmata",
            "https://data.gov.gr/el/dataset/troxaia-atyxhmata",
            "https://data.gov.gr/en/dataset/troxaia-atyxhmata?tab=resources#files",
            "https://data.gov.gr/dataset/troxaia-atyxhmata/resource/" + UUID_TEXT,
            "https://data.gov.gr/dataset/troxaia-atyxhmata.jsonld",
            "  https://DATA.GOV.GR/dataset/Troxaia-Atyxhmata  ",
        ]
        for address in addresses:
            with self.subTest(address=address):
                self.assertEqual(parse_dataset_identifier(address), NAME)
        self.assertEqual(
            parse_dataset_identifier("https://data.gov.gr/dataset/" + UUID_TEXT),
            DatasetIdentifier("id", UUID_TEXT),
        )

    def test_rejected_input(self):
        rejected = [
            "",
            "   ",
            "https://example.org/dataset/troxaia-atyxhmata",
            "https://data.gov.gr/organization/some-publisher",
            "https://data.gov.gr/",
            "Τροχαία ατυχήματα",
            "a",
            "name with spaces",
            'name"; DROP',
        ]
        for text in rejected:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_dataset_identifier(text)


if __name__ == "__main__":
    unittest.main()
