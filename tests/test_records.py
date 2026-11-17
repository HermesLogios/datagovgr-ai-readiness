"""Checks of the reading of a reply of the catalogue action package_search.

Usage:
    python -m unittest discover -s tests
"""

import unittest

from aiready.records import DatasetNotFound, NotADataset, dataset_in_records, records_in_reply


class ReplyTest(unittest.TestCase):
    def test_successful_reply_gives_its_records(self):
        reply = {"success": True, "result": {"count": 1, "results": [{"name": "troxaia-atyxhmata"}]}}
        self.assertEqual(records_in_reply(reply), [{"name": "troxaia-atyxhmata"}])

    def test_reply_without_success_or_without_results_is_refused(self):
        for reply in ({"success": False}, {"success": True}, {"success": True, "result": {"results": "none"}}, [], None, "text"):
            with self.subTest(reply=reply):
                with self.assertRaises(ValueError):
                    records_in_reply(reply)


class FirstRecordTest(unittest.TestCase):
    def test_dataset_is_returned(self):
        record = {"name": "troxaia-atyxhmata", "type": "dataset"}
        self.assertIs(dataset_in_records([record], "troxaia-atyxhmata"), record)

    def test_empty_search_names_what_was_asked(self):
        with self.assertRaises(DatasetNotFound) as raised:
            dataset_in_records([], "no-such-dataset")
        self.assertEqual(str(raised.exception), "no-such-dataset")

    def test_data_service_is_refused_with_its_type(self):
        with self.assertRaises(NotADataset) as raised:
            dataset_in_records([{"name": "api-kykloforias", "type": "data-service"}], "api-kykloforias")
        self.assertEqual(raised.exception.record_type, "data-service")


if __name__ == "__main__":
    unittest.main()
