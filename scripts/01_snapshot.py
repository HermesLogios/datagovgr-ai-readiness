r"""
01_snapshot.py
Φάση 1: στιγμιότυπο ολόκληρου του καταλόγου του data.gov.gr.

Λειτουργία, με τη σειρά:
  1. Ανάγνωση του πλήθους των εγγραφών του καταλόγου (package_search με rows=0).
  2. Λήψη όλων των εγγραφών σε σελίδες των 1.000, με σταθερή ταξινόμηση κατά ημερομηνία
     δημιουργίας και αναγνωριστικό. Με αυτή τη σειρά, όσες εγγραφές προστίθενται κατά τη
     διάρκεια της λήψης εμφανίζονται στο τέλος και δεν μετατοπίζουν τις προηγούμενες σελίδες.
  3. Αποθήκευση κάθε εγγραφής, ακριβώς όπως την επιστρέφει το API, σε μία γραμμή JSON
     (μορφή JSON Lines), σε συμπιεσμένο αρχείο: data/raw/catalog_ΕΕΕΕ-ΜΜ-ΗΗ.jsonl.gz.
  4. Παράλειψη τυχόν διπλοεγγραφών (ίδιο αναγνωριστικό), που μπορεί να προκύψουν από
     μεταβολές του καταλόγου κατά τη λήψη.
  5. Σύνταξη αρχείου τεκμηρίωσης (manifest): data/raw/catalog_ΕΕΕΕ-ΜΜ-ΗΗ.manifest.json,
     με χρόνους λήψης, παραμέτρους, πλήθη ανά τύπο εγγραφής και αποτύπωμα SHA-256 του αρχείου.

Το στιγμιότυπο περιλαμβάνει όλους τους τύπους εγγραφών της πύλης: σύνολα δεδομένων
(dataset), υπηρεσίες δεδομένων (data-service) και αποφάσεις διάθεσης (decision).

Εκτέλεση (από τον κεντρικό φάκελο του έργου, με ενεργό το .venv):
    python scripts\01_snapshot.py
Δοκιμαστική εκτέλεση με περιορισμένο πλήθος εγγραφών (δεν προορίζεται για το αποθετήριο):
    python scripts\01_snapshot.py --limit 2000

Διάρκεια πλήρους λήψης: περίπου 5 λεπτά. Μέγεθος αρχείου: περίπου 45 MB.
Το script εκτελεί μόνο αναγνώσεις και δεν μεταβάλλει δεδομένα στην πύλη.
Άδεια κώδικα: EUPL-1.2
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
# Ρυθμίσεις
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

BASE_URL = os.environ.get("DATAGOVGR_BASE_URL", "https://data.gov.gr").rstrip("/")
API_URL = BASE_URL + "/api/3/action/"
HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}

PAGE_SIZE = 1000                              # μέγιστο πλήθος εγγραφών ανά κλήση στο CKAN
SORT_ORDER = "metadata_created asc, id asc"   # σταθερή σειρά· οι νέες εγγραφές μπαίνουν στο τέλος
PAUSE_SECONDS = 1.0                           # παύση πριν από κάθε κλήση, για περιορισμό του φόρτου
TIMEOUT_SECONDS = 180                         # μέγιστος χρόνος αναμονής για μία σελίδα
MAX_ATTEMPTS = 4                              # προσπάθειες ανά κλήση σε προσωρινό σφάλμα


# ---------------------------------------------------------------------------
# Βοηθητικές συναρτήσεις
# ---------------------------------------------------------------------------

def api_get(session: requests.Session, action: str, params: dict) -> dict:
    """Κλήση μιας ενέργειας (action) του CKAN API.

    Σε προσωρινά σφάλματα (δίκτυο, HTTP 429 ή 5xx, ελλιπής απάντηση) η κλήση επαναλαμβάνεται
    με αυξανόμενη αναμονή. Σε μόνιμα σφάλματα (π.χ. HTTP 400 ή 404) η εκτέλεση διακόπτεται.
    Επιστρέφει το περιεχόμενο «result» της απάντησης.
    """
    url = API_URL + action
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} από {response.url}: {response.text[:300]}")
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Αποτυχία μετά από {MAX_ATTEMPTS} προσπάθειες ({url}): {error}") from error
            wait = 10 * attempt
            tqdm.write(f"  Προσωρινό σφάλμα ({error}). Νέα προσπάθεια σε {wait} δευτερόλεπτα.")
            time.sleep(wait)
            continue
        if not data.get("success"):
            raise RuntimeError(f"Η πύλη επέστρεψε σφάλμα: {data.get('error')}")
        return data["result"]
    raise RuntimeError("Μη αναμενόμενη ροή εκτέλεσης.")  # δεν φτάνει ποτέ εδώ


def sha256_of(path: Path) -> str:
    """Αποτύπωμα SHA-256 ενός αρχείου: επιτρέπει σε τρίτους να επαληθεύσουν ότι έχουν το ίδιο αρχείο."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Στιγμιότυπο του καταλόγου του data.gov.gr.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Μέγιστο πλήθος εγγραφών, για δοκιμαστική εκτέλεση.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Κύριο πρόγραμμα
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    today = dt.date.today().isoformat()
    suffix = "" if args.limit is None else f"_test{args.limit}"
    out_file = RAW_DIR / f"catalog_{today}{suffix}.jsonl.gz"
    part_file = out_file.with_name(out_file.name + ".part")   # προσωρινό όνομα μέχρι την ολοκλήρωση
    manifest_file = RAW_DIR / f"catalog_{today}{suffix}.manifest.json"

    started = dt.datetime.now(dt.timezone.utc)
    print(f"Στιγμιότυπο καταλόγου: {BASE_URL}")
    print(f"Έναρξη: {started:%Y-%m-%d %H:%M:%S} UTC")

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
            print(f"Εγγραφές στον κατάλογο: {reported_start}. Προς λήψη: {target}.")

            start = 0
            with gzip.open(part_file, "wt", encoding="utf-8", newline="\n") as handle, \
                    tqdm(total=target, desc="Λήψη", unit=" εγγρ.") as bar:
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
                        by_type[record.get("type") or "(χωρίς τύπο)"] += 1
                        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                        written += 1
                        bar.update(1)
                    start += len(batch)
                    if len(batch) < rows:   # τελευταία σελίδα
                        break

            time.sleep(PAUSE_SECONDS)
            reported_end = api_get(session, "package_search", {"rows": 0})["count"]
    except (Exception, KeyboardInterrupt) as error:
        if part_file.exists():
            part_file.unlink()   # δεν διατηρείται μισό αρχείο
        print(f"\nΗ λήψη διακόπηκε: {error}")
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
        "format": "JSON Lines: μία εγγραφή του CKAN API ανά γραμμή, χωρίς αλλαγές· συμπίεση gzip· UTF-8",
        "software": {
            "script": "scripts/01_snapshot.py",
            "python": platform.python_version(),
            "requests": requests.__version__,
        },
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("Η λήψη ολοκληρώθηκε.")
    print(f"  Εγγραφές: {written} (διπλοεγγραφές που παραλείφθηκαν: {duplicates})")
    for record_type, count in by_type.most_common():
        print(f"    {record_type}: {count}")
    print(f"  Αρχείο: {out_file.relative_to(ROOT)} ({out_file.stat().st_size / 1e6:.1f} MB)")
    print(f"  Τεκμηρίωση: {manifest_file.relative_to(ROOT)}")
    print(f"  Διάρκεια: {(finished - started).total_seconds() / 60:.1f} λεπτά")
    if args.limit is None and written != reported_end:
        print(
            f"  [!] Οι εγγραφές ({written}) διαφέρουν από το πλήθος που δήλωνε η πύλη στο τέλος "
            f"({reported_end}), λόγω μεταβολών κατά τη λήψη. Η διαφορά καταγράφεται στο manifest."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
