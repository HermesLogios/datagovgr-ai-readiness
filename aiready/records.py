"""Record types of the catalogue and the errors raised while a dataset record is looked up."""


class DatasetNotFound(LookupError):
    """No record of the catalogue has the requested name or identifier."""


class NotADataset(LookupError):
    """The record exists but is a data service or a decision, not a dataset."""

    def __init__(self, record_type: str):
        super().__init__(record_type)
        self.record_type = record_type


class PortalError(RuntimeError):
    """The portal did not give a usable answer."""


def record_type(record: dict) -> str:
    """Type of a catalogue record; a record without a type counts as a dataset, as in the scripts."""
    return record.get("type") or "dataset"


def require_dataset(record: dict) -> dict:
    """Returns the record when it is a dataset and raises NotADataset otherwise."""
    found_type = record_type(record)
    if found_type != "dataset":
        raise NotADataset(found_type)
    return record


def records_in_reply(reply) -> list:
    """Records held by a reply of the catalogue action package_search; ValueError for any other reply."""
    if not isinstance(reply, dict) or not reply.get("success"):
        raise ValueError("the reply reports no success")
    result = reply.get("result")
    records = result.get("results") if isinstance(result, dict) else None
    if not isinstance(records, list):
        raise ValueError("the reply holds no list of results")
    return records


def dataset_in_records(records: list, requested: str) -> dict:
    """First record of a search when it is a dataset.

    Raises DatasetNotFound for an empty search and NotADataset for a data service or a decision.
    """
    if not records:
        raise DatasetNotFound(requested)
    return require_dataset(records[0])
