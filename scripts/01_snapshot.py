r"""
01_snapshot.py
Phase 1: snapshot of the complete data.gov.gr catalogue.

What it does, in order:
  1. Reads the number of records in the catalogue (package_search with rows=0).
  2. Downloads all records in pages of 1,000, with a stable sort order (creation date, then id).
     With this order, records added while the download runs appear at the end and do not
     shift the pages already downloaded.
  3. Stores every record exactly as the API returns it, one JSON object per line
     (JSON Lines), in a compressed file: data/raw/catalog_YYYY-MM-DD.jsonl.gz.
  4. Skips duplicate records (same id), which can appear if the catalogue changes during
     the download.
  5. Writes a manifest file, data/raw/catalog_YYYY-MM-DD.manifest.json, with the download
     times, the parameters, the number of records per type and the SHA-256 checksum of the file.

The snapshot includes every record type of the portal: datasets (dataset), data services
(data-service) and data availability decisions (decision).

Usage (from the project root, with the .venv activated):
    python scripts\01_snapshot.py
Test run with a limited number of records (not meant for the repository):
    python scripts\01_snapshot.py --limit 2000

A full download takes about 5 minutes and produces a file of about 30 MB.
The script only reads from the portal; it never modifies anything there.
Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

BASE_URL = os.environ.get("DATAGOVGR_BASE_URL", "https://data.gov.gr").rstrip("/")
API_URL = BASE_URL + "/api/3/action/"
HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}

PAGE_SIZE = 1000                              # maximum number of records per CKAN call
SORT_ORDER = "metadata_created asc, id asc"   # stable order; new records are appended at the end
PAUSE_SECONDS = 1.0                           # pause before every call, to keep the load low
TIMEOUT_SECONDS = 180                         # maximum wait for one page
MAX_ATTEMPTS = 4                              # attempts per call on a temporary error


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_get(session: requests.Session, action: str, params: dict) -> dict:
    """Calls one CKAN API action.

    Temporary errors (network, HTTP 429 or 5xx, incomplete response) are retried with an
    increasing wait. Permanent errors (e.g. HTTP 400 or 404) stop the run.
    Returns the 'result' part of the response.
    """
    url = API_URL + action
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from {response.url}: {response.text[:300]}")
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Failed after {MAX_ATTEMPTS} attempts ({url}): {error}") from error
            wait = 10 * attempt
            tqdm.write(f"  Temporary error ({error}). Retrying in {wait} seconds.")
            time.sleep(wait)
            continue
        if not data.get("success"):
            raise RuntimeError(f"The portal returned an error: {data.get('error')}")
        return data["result"]
    raise RuntimeError("Unexpected control flow.")  # never reached


def sha256_of(path: Path) -> str:
    """SHA-256 checksum of a file: lets others verify that they hold the identical file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot of the data.gov.gr catalogue.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records, for a test run.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    today = dt.date.today().isoformat()
    suffix = "" if args.limit is None else f"_test{args.limit}"
    out_file = RAW_DIR / f"catalog_{today}{suffix}.jsonl.gz"
    part_file = out_file.with_name(out_file.name + ".part")   # temporary name until the download completes
    manifest_file = RAW_DIR / f"catalog_{today}{suffix}.manifest.json"

    started = dt.datetime.now(dt.timezone.utc)
    print(f"Catalogue snapshot: {BASE_URL}")
    print(f"Started: {started:%Y-%m-%d %H:%M:%S} UTC")

    written = 0
    duplicates = 0
    by_type: Counter = Counter()
    seen_ids: set[str] = set()

    try:
        with requests.Session() as session:
            status = api_get(session, "status_show", {})
            time.sleep(PAUSE_SECONDS)
            reported_start = api_get(session, "package_search", {"rows": 0})["count"]
            target = reported_start if args.limit is None else min(args.limit, reported_start)
            print(f"Records in the catalogue: {reported_start}. To download: {target}.")

            start = 0
            with gzip.open(part_file, "wt", encoding="utf-8", newline="\n") as handle, \
                    tqdm(total=target, desc="Download", unit=" rec") as bar:
                while True:
                    rows = PAGE_SIZE if args.limit is None else min(PAGE_SIZE, args.limit - written)
                    if rows <= 0:
                        break
                    time.sleep(PAUSE_SECONDS)
                    result = api_get(
                        session,
                        "package_search",
                        {"rows": rows, "start": start, "sort": SORT_ORDER},
                    )
                    batch = result.get("results") or []
                    for record in batch:
                        record_id = record.get("id")
                        if record_id in seen_ids:
                            duplicates += 1
                            continue
                        seen_ids.add(record_id)
                        by_type[record.get("type") or "(no type)"] += 1
                        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                        written += 1
                        bar.update(1)
                    start += len(batch)
                    if len(batch) < rows:   # last page
                        break

            time.sleep(PAUSE_SECONDS)
            reported_end = api_get(session, "package_search", {"rows": 0})["count"]
    except (Exception, KeyboardInterrupt) as error:
        if part_file.exists():
            part_file.unlink()   # no half-written file is kept
        print(f"\nThe download was interrupted: {error}")
        return 1

    part_file.replace(out_file)
    finished = dt.datetime.now(dt.timezone.utc)

    manifest = {
        "snapshot_date": today,
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "source": API_URL + "package_search",
        "parameters": {"rows_per_page": PAGE_SIZE, "sort": SORT_ORDER, "limit": args.limit},
        "ckan_version": status.get("ckan_version"),
        "reported_count_at_start": reported_start,
        "reported_count_at_end": reported_end,
        "records_written": written,
        "duplicates_skipped": duplicates,
        "records_by_type": dict(by_type.most_common()),
        "file": out_file.name,
        "file_size_bytes": out_file.stat().st_size,
        "sha256": sha256_of(out_file),
        "format": "JSON Lines: one CKAN API record per line, unmodified; gzip compression; UTF-8",
        "software": {
            "script": "scripts/01_snapshot.py",
            "python": platform.python_version(),
            "requests": requests.__version__,
        },
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("Download complete.")
    print(f"  Records: {written} (duplicates skipped: {duplicates})")
    for record_type, count in by_type.most_common():
        print(f"    {record_type}: {count}")
    print(f"  File: {out_file.relative_to(ROOT)} ({out_file.stat().st_size / 1e6:.1f} MB)")
    print(f"  Manifest: {manifest_file.relative_to(ROOT)}")
    print(f"  Duration: {(finished - started).total_seconds() / 60:.1f} minutes")
    if args.limit is None and written != reported_end:
        print(
            f"  [!] The records written ({written}) differ from the count reported by the portal "
            f"at the end ({reported_end}), because the catalogue changed during the download. "
            f"Both numbers are recorded in the manifest."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
