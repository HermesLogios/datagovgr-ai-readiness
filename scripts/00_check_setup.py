r"""
00_check_setup.py
Phase 0: environment check and first exploration of the data.gov.gr API.

What it does, in order:
  1. Records the Python version and checks that the script runs inside the virtual environment (.venv).
  2. Checks that the libraries listed in requirements.txt are installed.
  3. Checks that Greek text can be written to and read from a file as UTF-8.
  4. Makes a few read-only calls to the data.gov.gr API, pausing one second between calls:
       4.1 status_show     portal software (e.g. CKAN) and enabled plugins
       4.2 package_search  number of records and the metadata structure of one record
       4.3 facets          most frequent organisations, licences and file formats in the catalogue
       4.4 package_show    whether usage statistics (page views) are available per dataset
       4.5 sorting         whether the search API accepts sorting by page views
       4.6 Croissant/DCAT  whether Croissant and DCAT descriptions are served per dataset
  5. Saves the responses to data/raw/api_probe_YYYY-MM-DD.json
     and the console log to outputs/00_check_setup.log.

Usage (from the project root, with the .venv activated):
    python scripts\00_check_setup.py

The script only reads from the portal; it never modifies anything there.
Code licence: EUPL-1.2
"""

from __future__ import annotations

import datetime as dt
import json
import locale
import os
import platform
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Project root: the parent folder of scripts/.
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "outputs"

# Portal address. A different address can be set through the environment
# variable DATAGOVGR_BASE_URL without changing the code.
BASE_URL = os.environ.get("DATAGOVGR_BASE_URL", "https://data.gov.gr").rstrip("/")
API_URL = BASE_URL + "/api/3/action/"

# How the script identifies itself to the portal (ASCII characters only).
HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}

PAUSE_SECONDS = 1.0          # pause after every call, to keep the load on the portal low
TIMEOUT_SECONDS = 30         # maximum wait for a response
MAX_STORED_BYTES = 300_000   # responses larger than this are not stored in full

TODAY = dt.date.today().isoformat()
log_lines: list[str] = []    # copy of the console output, for the log file


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

def say(text: str = "") -> None:
    """Prints one line and keeps a copy for the log file."""
    print(text, flush=True)
    log_lines.append(text)


def title(text: str) -> None:
    """Prints a section title."""
    say()
    say("=" * 70)
    say(text)
    say("=" * 70)


# ---------------------------------------------------------------------------
# 1-3. Environment checks
# ---------------------------------------------------------------------------

def check_python() -> None:
    title("1. Python")
    say(f"Version: {platform.python_version()}")
    say(f"Executable: {sys.executable}")
    if sys.version_info < (3, 11):
        say("[!] Python 3.11 or newer is required (pandas 3 does not support older versions).")
    else:
        say("[OK] Compatible version.")
    # Inside a virtual environment, sys.prefix (the venv folder) differs from sys.base_prefix.
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        say("[OK] Running inside the virtual environment (.venv).")
    else:
        say(r"[!] Not running inside the virtual environment. Activate it with: .\.venv\Scripts\Activate.ps1")


def check_packages() -> bool:
    title("2. Libraries")
    all_ok = True
    for name in ("requests", "pandas", "tqdm"):
        try:
            module = __import__(name)
            say(f"[OK] {name} {getattr(module, '__version__', '')}")
        except ImportError:
            all_ok = False
            say(f"[!] Library {name} not found. Install with: python -m pip install -r requirements.txt")
    return all_ok


def check_utf8() -> None:
    title("3. UTF-8 encoding")
    # The sample is deliberately Greek: the portal's metadata is in Greek.
    sample = "Δοκιμή ελληνικών: ά έ ή ί ό ύ ώ ϊ ϋ ΐ ΰ - Αθήνα, Θεσσαλονίκη, Ρόδος"
    test_file = RAW_DIR / "_utf8_test.txt"
    test_file.write_text(sample, encoding="utf-8")
    back = test_file.read_text(encoding="utf-8")
    test_file.unlink()
    if back == sample:
        say("[OK] Greek text was written and read back correctly.")
    else:
        say("[!] The text was altered on the way: encoding problem.")
    say(f"Console output encoding: {sys.stdout.encoding}")
    say(f"Default file encoding: {locale.getpreferredencoding(False)}")
    say(f"PYTHONUTF8 = {os.environ.get('PYTHONUTF8', '(not set)')}")


# ---------------------------------------------------------------------------
# 4. API calls
# ---------------------------------------------------------------------------

def call(session, url: str, params: dict | None = None) -> tuple[dict, object]:
    """Makes one GET request.

    Returns:
      - record: a summary of the call (address, status code, content type, size),
        stored in the results file;
      - data: the response body if it is JSON, otherwise None.
    """
    record: dict = {"url": url, "params": params or {}}
    try:
        response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except Exception as error:  # e.g. network failure or a firewall blocking the request
        record["error"] = f"{type(error).__name__}: {error}"
        say(f"  [!] Connection failure: {record['error']}")
        time.sleep(PAUSE_SECONDS)
        return record, None
    time.sleep(PAUSE_SECONDS)

    record["final_url"] = response.url
    record["status"] = response.status_code
    record["content_type"] = response.headers.get("Content-Type", "")
    record["size_bytes"] = len(response.content)
    say(f"  -> response {response.status_code} from {response.url}")

    try:
        data = response.json()
    except ValueError:
        # Not JSON (e.g. an HTML page): keep the beginning of the text.
        record["text_start"] = response.text[:1000]
        return record, None

    if record["size_bytes"] <= MAX_STORED_BYTES:
        record["json"] = data
    else:
        record["note"] = "Large response: not stored in full."
    return record, data


def ckan_result(data: object) -> object:
    """Returns the 'result' part of a successful CKAN response, otherwise None."""
    if isinstance(data, dict) and data.get("success") is True:
        return data.get("result")
    if isinstance(data, dict) and "error" in data:
        say(f"  [!] The portal returned an error: {data['error']}")
    return None


def matching_keys(keys, words) -> list[str]:
    """Field names that contain any of the given words (case-insensitive)."""
    return [key for key in keys if key and any(word in key.lower() for word in words)]


def describe_dataset(dataset: dict) -> None:
    """Prints the main metadata of one dataset, to document its structure."""
    organization = dataset.get("organization") or {}
    extras = [extra.get("key") for extra in dataset.get("extras") or [] if isinstance(extra, dict)]
    resources = dataset.get("resources") or []

    say(f"  Name: {dataset.get('name')}")
    say(f"  Title: {dataset.get('title')}")
    say(f"  Organisation: {organization.get('title') or organization.get('name')}")
    say(f"  Licence: {dataset.get('license_id')} | {dataset.get('license_title')}")
    say(f"  Metadata last modified: {dataset.get('metadata_modified')}")
    say(f"  Metadata fields: {', '.join(sorted(dataset.keys()))}")
    say(f"  Extra fields (extras): {', '.join(k for k in extras if k) or '(none)'}")
    say(f"  Resources: {len(resources)}")
    if resources:
        first = resources[0]
        say(f"  Resource fields: {', '.join(sorted(first.keys()))}")
        say(f"  First resource: format {first.get('format')} | {first.get('url')}")

    usage = matching_keys(dataset.keys(), ("view", "download", "track", "visit", "popular"))
    say(f"  Fields related to usage statistics: {', '.join(usage) or '(none)'}")
    hvd = matching_keys(list(dataset.keys()) + extras, ("hvd", "legislation", "high_value", "highvalue"))
    say(f"  Fields related to high-value dataset (HVD) flags: {', '.join(hvd) or '(none)'}")


def probe_api() -> dict:
    import requests  # imported here, after its installation has been confirmed

    title(f"4. data.gov.gr API ({API_URL})")
    results: dict = {}

    with requests.Session() as session:
        # 4.1 -------------------------------------------------------------
        say("4.1 Portal software (status_show)")
        record, data = call(session, API_URL + "status_show")
        results["status_show"] = record
        status = ckan_result(data)
        if isinstance(status, dict):
            extensions = status.get("extensions") or []
            say(f"  Software: CKAN {status.get('ckan_version')}")
            say(f"  Portal title: {status.get('site_title')}")
            say(f"  Plugins: {', '.join(extensions) or '(not reported)'}")
            for word, meaning in (
                ("dcat", "DCAT descriptions"),
                ("croissant", "Croissant descriptions"),
                ("tracking", "page-view tracking"),
                ("scheming", "custom metadata fields"),
            ):
                found = matching_keys(extensions, (word,))
                say(f"    {meaning}: {'YES (' + ', '.join(found) + ')' if found else 'no'}")
        else:
            say("  The response is not in CKAN format; the full response is stored for inspection.")

        # 4.2 -------------------------------------------------------------
        say()
        say("4.2 One sample record (package_search, rows=1)")
        record, data = call(session, API_URL + "package_search", {"rows": 1})
        results["package_search_one"] = record
        found = ckan_result(data)
        dataset = None
        if isinstance(found, dict):
            say(f"  Records in the portal: {found.get('count')}")
            if found.get("results"):
                dataset = found["results"][0]
                describe_dataset(dataset)

        # 4.3 -------------------------------------------------------------
        say()
        say("4.3 Most frequent organisations, licences and file formats (facets)")
        fields = ["organization", "license_id", "res_format"]
        record, data = call(
            session,
            API_URL + "package_search",
            {"rows": 0, "facet.field": json.dumps(fields), "facet.limit": 15},
        )
        results["facets"] = record
        found = ckan_result(data)
        if isinstance(found, dict):
            facets = found.get("search_facets") or {}
            labels = {"organization": "Organisations", "license_id": "Licences", "res_format": "File formats"}
            for field in fields:
                items = (facets.get(field) or {}).get("items") or []
                items = sorted(items, key=lambda item: item.get("count", 0), reverse=True)
                say(f"  {labels[field]} (up to 15, by number of records):")
                for item in items[:15]:
                    say(f"    {item.get('count', 0):>6}  {item.get('display_name') or item.get('name')}")

        if dataset:
            name = dataset.get("name")

            # 4.4 ---------------------------------------------------------
            say()
            say("4.4 Usage statistics for the sample record (package_show with include_tracking)")
            record, data = call(session, API_URL + "package_show", {"id": name, "include_tracking": "true"})
            shown = ckan_result(data)
            tracking = shown.get("tracking_summary") if isinstance(shown, dict) else None
            record.pop("json", None)  # the full metadata were already stored in 4.2
            record["tracking_summary"] = tracking
            results["package_show_tracking"] = record
            if tracking:
                say(f"  YES: total views {tracking.get('total')}, recent views {tracking.get('recent')}")
            else:
                say("  No: the response contains no tracking_summary.")

            # 4.5 ---------------------------------------------------------
            say()
            say("4.5 Sorting by recent views (sort=views_recent desc)")
            record, data = call(
                session,
                API_URL + "package_search",
                {"rows": 5, "sort": "views_recent desc", "include_tracking": "true"},
            )
            found = ckan_result(data)
            record.pop("json", None)  # five full records do not need to be stored
            if isinstance(found, dict):
                say("  Sorting accepted. First 5 records:")
                record["top"] = []
                for item in found.get("results") or []:
                    views = (item.get("tracking_summary") or {}).get("total", "unknown")
                    record["top"].append({"name": item.get("name"), "views_total": views})
                    say(f"    {item.get('name')}  (views: {views})")
            results["sort_by_views"] = record

            # 4.6 ---------------------------------------------------------
            say()
            say("4.6 Croissant and DCAT descriptions for the sample record")
            for key, label, url in (
                ("croissant", "Croissant", f"{BASE_URL}/dataset/{name}/croissant.jsonld"),
                ("dcat_jsonld", "DCAT (JSON-LD)", f"{BASE_URL}/dataset/{name}.jsonld"),
            ):
                record, data = call(session, url)
                results[key] = record
                if record.get("status") == 200 and data is not None:
                    say(f"  {label}: YES, available")
                else:
                    say(f"  {label}: no (response {record.get('status', 'connection failure')})")
        else:
            say()
            say("  No sample record found; steps 4.4 to 4.6 are skipped.")

    return results


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    # Print Greek text safely, whatever the console is set to.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    say(f"Environment check: {dt.datetime.now():%Y-%m-%d %H:%M}")
    say(f"Project folder: {ROOT}")

    check_python()
    packages_ok = check_packages()
    check_utf8()

    results: dict = {"date": TODAY, "python": platform.python_version(), "base_url": BASE_URL}
    if packages_ok:
        results.update(probe_api())
    else:
        say()
        say("API calls are skipped until the libraries are installed.")

    probe_file = RAW_DIR / f"api_probe_{TODAY}.json"
    log_file = OUT_DIR / "00_check_setup.log"

    title("5. Saving results")
    say(f"API responses: {probe_file.relative_to(ROOT)}")
    say(f"Console log: {log_file.relative_to(ROOT)}")

    probe_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    say("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
