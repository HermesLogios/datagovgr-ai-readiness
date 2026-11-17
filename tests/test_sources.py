"""Tests of the two sources of a dataset record: the portal and a stored snapshot."""

import unittest
from pathlib import Path
from unittest import mock

from aiready import portal
from aiready.identifier import DatasetIdentifier
from aiready.records import DatasetNotFound, NotADataset, PortalError
from aiready.snapshot import find_dataset_record, iter_snapshot_records
from fake_portal import FakePortal, found_reply

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "raw" / "catalog_2026-10-24.jsonl.gz"
DATASET = {"id": "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9", "name": "sample-dataset", "type": "dataset", "title": "Sample"}
SERVICE = {"id": "1b2c3d4e-5f60-7182-93a4-b5c6d7e8f9a0", "name": "sample-service", "type": "data-service"}
REPLIES = {
    'name:"sample-dataset"': (200, found_reply([DATASET])),
    'id:"0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9"': (200, found_reply([DATASET])),
    'name:"sample-service"': (200, found_reply([SERVICE])),
    'name:"server-error"': (500, "{}"),
    'name:"broken-reply"': (200, "this is not JSON"),
    'name:"refused-request"': (200, '{"success": false, "error": {"message": "refused"}}'),
}


class PortalTest(unittest.TestCase):
    def setUp(self):
        pause = mock.patch.object(portal, "PAUSE_SECONDS", 0)
        pause.start()
        self.addCleanup(pause.stop)

    def test_dataset_is_fetched_with_one_filtered_search(self):
        with FakePortal(REPLIES) as fake:
            record = portal.fetch_dataset_record(DatasetIdentifier("name", "sample-dataset"), base_url=fake.url)
            self.assertEqual(record, DATASET)
            self.assertEqual(len(fake.requests), 1)
            request = fake.requests[0]
            self.assertEqual(request["path"], "/api/3/action/package_search")
            self.assertEqual(request["query"], {"fq": 'name:"sample-dataset"', "rows": "1"})
            self.assertEqual(request["user_agent"], portal.USER_AGENT)

    def test_dataset_is_fetched_by_identifier(self):
        with FakePortal(REPLIES) as fake:
            record = portal.fetch_dataset_record(DatasetIdentifier("id", DATASET["id"]), base_url=fake.url + "/")
            self.assertEqual(record["name"], "sample-dataset")

    def test_base_address_is_read_from_the_environment(self):
        with FakePortal(REPLIES) as fake, mock.patch.dict("os.environ", {portal.BASE_URL_VARIABLE: fake.url}):
            record = portal.fetch_dataset_record(DatasetIdentifier("name", "sample-dataset"))
            self.assertEqual(record, DATASET)

    def test_unknown_dataset(self):
        with FakePortal(REPLIES) as fake:
            with self.assertRaises(DatasetNotFound):
                portal.fetch_dataset_record(DatasetIdentifier("name", "unknown-dataset"), base_url=fake.url)

    def test_record_of_another_type(self):
        with FakePortal(REPLIES) as fake:
            with self.assertRaises(NotADataset) as raised:
                portal.fetch_dataset_record(DatasetIdentifier("name", "sample-service"), base_url=fake.url)
            self.assertEqual(raised.exception.record_type, "data-service")

    def test_failures_of_the_portal(self):
        with FakePortal(REPLIES) as fake:
            for name in ("server-error", "broken-reply", "refused-request"):
                with self.subTest(name=name):
                    fake.requests.clear()
                    with self.assertRaises(PortalError):
                        portal.fetch_dataset_record(DatasetIdentifier("name", name), base_url=fake.url)
                    self.assertEqual(len(fake.requests), portal.MAX_ATTEMPTS)

    def test_portal_that_cannot_be_reached(self):
        with FakePortal(REPLIES) as fake:
            closed_address = fake.url
        with self.assertRaises(PortalError):
            portal.fetch_dataset_record(DatasetIdentifier("name", "sample-dataset"), base_url=closed_address)


class SnapshotTest(unittest.TestCase):
    def test_dataset_is_found_by_name_and_by_identifier(self):
        by_name = find_dataset_record(SNAPSHOT, DatasetIdentifier("name", "troxaia-atyxhmata"))
        self.assertEqual(by_name["title"], "Τροχαία ατυχήματα")
        by_identifier = find_dataset_record(SNAPSHOT, DatasetIdentifier("id", by_name["id"]))
        self.assertEqual(by_identifier["name"], "troxaia-atyxhmata")

    def test_unknown_dataset(self):
        with self.assertRaises(DatasetNotFound):
            find_dataset_record(SNAPSHOT, DatasetIdentifier("name", "no-such-dataset-in-the-snapshot"))

    def test_record_of_another_type(self):
        service = next(record for record in iter_snapshot_records(SNAPSHOT) if record.get("type") == "data-service")
        with self.assertRaises(NotADataset) as raised:
            find_dataset_record(SNAPSHOT, DatasetIdentifier("name", service["name"]))
        self.assertEqual(raised.exception.record_type, "data-service")


if __name__ == "__main__":
    unittest.main()
