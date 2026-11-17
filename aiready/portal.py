"""Reading of one dataset record from the catalogue API of data.gov.gr.

One call is made per dataset, to the same action that the catalogue snapshot uses
(package_search), so that the record has the form on which the checks were tested. The terms
of use of the portal allow automated retrieval through the API without registration.
"""

import os
import time

import requests

from aiready.identifier import DatasetIdentifier
from aiready.records import PortalError, dataset_in_records, records_in_reply

BASE_URL_VARIABLE = "DATAGOVGR_BASE_URL"
DEFAULT_BASE_URL = "https://data.gov.gr"
USER_AGENT = "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"
TIMEOUT_SECONDS = 60     # maximum wait for the answer of the portal
MAX_ATTEMPTS = 2         # attempts per dataset on a failed call
PAUSE_SECONDS = 1.0      # pause between calls, to keep the load low


def portal_base_url() -> str:
    """Address of the portal: data.gov.gr, or the value of the environment variable DATAGOVGR_BASE_URL."""
    return os.environ.get(BASE_URL_VARIABLE, DEFAULT_BASE_URL).rstrip("/")


def fetch_dataset_record(
    identifier: DatasetIdentifier, base_url: str | None = None, timeout_seconds: float | None = None
) -> dict:
    """Returns the catalogue record of the dataset with the given name or identifier.

    Raises DatasetNotFound when the catalogue has no such record, NotADataset when the record
    is a data service or a decision, and PortalError when the portal gives no usable answer.
    """
    base = (base_url or portal_base_url()).rstrip("/")
    url = base + "/api/3/action/package_search"
    params = {"fq": f'{identifier.kind}:"{identifier.value}"', "rows": 1}
    failure = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout_seconds or TIMEOUT_SECONDS
            )
            if response.status_code != 200:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            records = records_in_reply(response.json())
            break
        except (requests.RequestException, ValueError) as error:
            failure = f"{type(error).__name__}: {error}"
            if attempt < MAX_ATTEMPTS:
                time.sleep(PAUSE_SECONDS)
    else:
        raise PortalError(f"no usable answer from {base} after {MAX_ATTEMPTS} attempts ({failure})")
    return dataset_in_records(records, identifier.value)
