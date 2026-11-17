"""Reading of the dataset named on the command line or on the page: a name, an identifier or an address."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

PORTAL_HOSTS = ("data.gov.gr", "www.data.gov.gr")
NAME_PATTERN = re.compile(r"[a-z0-9_-]{2,100}")
UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
EXPORT_SUFFIX = re.compile(r"\.(jsonld|rdf|xml|ttl|n3)$")


class InvalidIdentifier(ValueError):
    """Text that names no dataset. The code says why: empty, other_site, not_dataset_page or not_a_name."""

    def __init__(self, code: str, explanation: str):
        super().__init__(explanation)
        self.code = code


@dataclass(frozen=True)
class DatasetIdentifier:
    kind: str   # "name" or "id": the field of the catalogue record that holds the value
    value: str


def parse_dataset_identifier(text: str) -> DatasetIdentifier:
    """Reads a dataset name, a dataset identifier or the address of a dataset page of data.gov.gr.

    Raises InvalidIdentifier, a ValueError with a one-line explanation, for anything else.
    """
    cleaned = text.strip()
    if not cleaned:
        raise InvalidIdentifier("empty", "no dataset given")
    if "/" in cleaned:
        cleaned = name_in_address(cleaned)
    value = cleaned.lower()
    if UUID_PATTERN.fullmatch(value):
        return DatasetIdentifier("id", value)
    if NAME_PATTERN.fullmatch(value):
        return DatasetIdentifier("name", value)
    raise InvalidIdentifier(
        "not_a_name", "not a dataset name, a dataset identifier or the address of a dataset of data.gov.gr"
    )


def name_in_address(address: str) -> str:
    """Name or identifier in the address of a dataset page, e.g. https://data.gov.gr/dataset/troxaia-atyxhmata."""
    parts = urlsplit(address if "://" in address else "https://" + address)
    host = (parts.hostname or "").lower()
    if host not in PORTAL_HOSTS:
        raise InvalidIdentifier("other_site", f"the address is not on data.gov.gr (found '{host}')")
    segments = [segment for segment in parts.path.split("/") if segment]
    if "dataset" not in segments or segments.index("dataset") + 1 >= len(segments):
        raise InvalidIdentifier(
            "not_dataset_page",
            "the address is not a dataset page of data.gov.gr (expected data.gov.gr/dataset/ and a name)",
        )
    return EXPORT_SUFFIX.sub("", segments[segments.index("dataset") + 1])
