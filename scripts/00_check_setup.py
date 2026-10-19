r"""
00_check_setup.py
Φάση 0: έλεγχος του περιβάλλοντος εργασίας και πρώτη διερεύνηση του API του data.gov.gr.

Λειτουργία, με τη σειρά:
  1. Καταγραφή της έκδοσης της Python και έλεγχος εκτέλεσης μέσα στο εικονικό περιβάλλον (.venv).
  2. Έλεγχος των βιβλιοθηκών του requirements.txt.
  3. Έλεγχος εγγραφής και ανάγνωσης ελληνικού κειμένου με κωδικοποίηση UTF-8.
  4. Κλήσεις ανάγνωσης στο API του data.gov.gr, με παύση ενός δευτερολέπτου μεταξύ τους:
       4.1 status_show     λογισμικό της πύλης (π.χ. CKAN) και ενεργά πρόσθετα (plugins)
       4.2 package_search  πλήθος συνόλων και δομή των μεταδεδομένων ενός συνόλου
       4.3 facets          συχνότεροι φορείς, άδειες και μορφές αρχείων στον κατάλογο
       4.4 package_show    διαθεσιμότητα στοιχείων χρήσης (προβολών) ανά σύνολο
       4.5 ταξινόμηση      δυνατότητα ταξινόμησης των συνόλων κατά προβολές
       4.6 Croissant/DCAT  διαθεσιμότητα περιγραφών Croissant και DCAT ανά σύνολο
  5. Αποθήκευση των απαντήσεων στο data/raw/api_probe_ΕΕΕΕ-ΜΜ-ΗΗ.json
     και της καταγραφής εκτέλεσης στο outputs/00_check_setup.log.

Εκτέλεση (από τον κεντρικό φάκελο του έργου, με ενεργό το .venv):
    python scripts\00_check_setup.py

Το script εκτελεί μόνο αναγνώσεις και δεν μεταβάλλει δεδομένα στην πύλη.
Άδεια κώδικα: EUPL-1.2
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
# Ρυθμίσεις
# ---------------------------------------------------------------------------

# Κεντρικός φάκελος του έργου: ο γονικός φάκελος του scripts/.
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "outputs"

# Διεύθυνση της πύλης. Διαφορετική διεύθυνση ορίζεται με τη μεταβλητή
# περιβάλλοντος DATAGOVGR_BASE_URL, χωρίς αλλαγή του κώδικα.
BASE_URL = os.environ.get("DATAGOVGR_BASE_URL", "https://data.gov.gr").rstrip("/")
API_URL = BASE_URL + "/api/3/action/"

# Αναγνωριστικό του προγράμματος προς την πύλη (μόνο λατινικοί χαρακτήρες).
HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}

PAUSE_SECONDS = 1.0          # παύση μετά από κάθε κλήση, για περιορισμό του φόρτου στην πύλη
TIMEOUT_SECONDS = 30         # μέγιστος χρόνος αναμονής απάντησης
MAX_STORED_BYTES = 300_000   # όριο μεγέθους πάνω από το οποίο μια απάντηση δεν αποθηκεύεται ολόκληρη

TODAY = dt.date.today().isoformat()
log_lines: list[str] = []    # αντίγραφο της εξόδου, για το αρχείο καταγραφής


# ---------------------------------------------------------------------------
# Έξοδος στην οθόνη
# ---------------------------------------------------------------------------

def say(text: str = "") -> None:
    """Τυπώνει μία γραμμή και τη διατηρεί για το αρχείο καταγραφής."""
    print(text, flush=True)
    log_lines.append(text)


def title(text: str) -> None:
    """Τυπώνει τίτλο ενότητας."""
    say()
    say("=" * 70)
    say(text)
    say("=" * 70)


# ---------------------------------------------------------------------------
# 1-3. Έλεγχοι του περιβάλλοντος εργασίας
# ---------------------------------------------------------------------------

def check_python() -> None:
    title("1. Python")
    say(f"Έκδοση: {platform.python_version()}")
    say(f"Εκτελέσιμο: {sys.executable}")
    if sys.version_info < (3, 11):
        say("[!] Απαιτείται Python 3.11 ή νεότερη (το pandas 3 δεν υποστηρίζει παλαιότερες εκδόσεις).")
    else:
        say("[OK] Συμβατή έκδοση.")
    # Σε εικονικό περιβάλλον, το sys.prefix (φάκελος του venv) διαφέρει από το sys.base_prefix.
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        say("[OK] Εκτέλεση μέσα στο εικονικό περιβάλλον (.venv).")
    else:
        say(r"[!] Εκτέλεση εκτός του εικονικού περιβάλλοντος. Ενεργοποίηση: .\.venv\Scripts\Activate.ps1")


def check_packages() -> bool:
    title("2. Βιβλιοθήκες")
    all_ok = True
    for name in ("requests", "pandas", "tqdm"):
        try:
            module = __import__(name)
            say(f"[OK] {name} {getattr(module, '__version__', '')}")
        except ImportError:
            all_ok = False
            say(f"[!] Δεν βρέθηκε η βιβλιοθήκη {name}. Εγκατάσταση: python -m pip install -r requirements.txt")
    return all_ok


def check_utf8() -> None:
    title("3. Κωδικοποίηση UTF-8")
    sample = "Δοκιμή ελληνικών: ά έ ή ί ό ύ ώ ϊ ϋ ΐ ΰ - Αθήνα, Θεσσαλονίκη, Ρόδος"
    test_file = RAW_DIR / "_utf8_test.txt"
    test_file.write_text(sample, encoding="utf-8")
    back = test_file.read_text(encoding="utf-8")
    test_file.unlink()
    if back == sample:
        say("[OK] Το ελληνικό κείμενο γράφτηκε και διαβάστηκε σωστά.")
    else:
        say("[!] Το κείμενο αλλοιώθηκε: πρόβλημα κωδικοποίησης.")
    say(f"Κωδικοποίηση εξόδου: {sys.stdout.encoding}")
    say(f"Προεπιλεγμένη κωδικοποίηση αρχείων: {locale.getpreferredencoding(False)}")
    say(f"PYTHONUTF8 = {os.environ.get('PYTHONUTF8', '(δεν έχει οριστεί)')}")


# ---------------------------------------------------------------------------
# 4. Κλήσεις στο API
# ---------------------------------------------------------------------------

def call(session, url: str, params: dict | None = None) -> tuple[dict, object]:
    """Εκτελεί μία κλήση GET.

    Επιστρέφει:
      - record: σύνοψη της κλήσης (διεύθυνση, κωδικός, τύπος και μέγεθος απάντησης),
        που αποθηκεύεται στο αρχείο αποτελεσμάτων·
      - data: το περιεχόμενο της απάντησης, αν είναι JSON· διαφορετικά None.
    """
    record: dict = {"url": url, "params": params or {}}
    try:
        response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except Exception as error:  # π.χ. αποτυχία δικτύου ή αποκλεισμός από τείχος προστασίας
        record["error"] = f"{type(error).__name__}: {error}"
        say(f"  [!] Αποτυχία σύνδεσης: {record['error']}")
        time.sleep(PAUSE_SECONDS)
        return record, None
    time.sleep(PAUSE_SECONDS)

    record["final_url"] = response.url
    record["status"] = response.status_code
    record["content_type"] = response.headers.get("Content-Type", "")
    record["size_bytes"] = len(response.content)
    say(f"  -> απάντηση {response.status_code} από {response.url}")

    try:
        data = response.json()
    except ValueError:
        # Απάντηση που δεν είναι JSON (π.χ. σελίδα HTML): διατηρείται η αρχή του κειμένου.
        record["text_start"] = response.text[:1000]
        return record, None

    if record["size_bytes"] <= MAX_STORED_BYTES:
        record["json"] = data
    else:
        record["note"] = "Μεγάλη απάντηση: δεν αποθηκεύτηκε ολόκληρη."
    return record, data


def ckan_result(data: object) -> object:
    """Επιστρέφει το περιεχόμενο («result») μιας επιτυχημένης απάντησης CKAN, αλλιώς None."""
    if isinstance(data, dict) and data.get("success") is True:
        return data.get("result")
    if isinstance(data, dict) and "error" in data:
        say(f"  [!] Η πύλη επέστρεψε σφάλμα: {data['error']}")
    return None


def matching_keys(keys, words) -> list[str]:
    """Ονόματα πεδίων που περιέχουν κάποια από τις λέξεις (χωρίς διάκριση πεζών-κεφαλαίων)."""
    return [key for key in keys if key and any(word in key.lower() for word in words)]


def describe_dataset(dataset: dict) -> None:
    """Τυπώνει τα βασικά μεταδεδομένα ενός συνόλου, για την καταγραφή της δομής τους."""
    organization = dataset.get("organization") or {}
    extras = [extra.get("key") for extra in dataset.get("extras") or [] if isinstance(extra, dict)]
    resources = dataset.get("resources") or []

    say(f"  Όνομα (name): {dataset.get('name')}")
    say(f"  Τίτλος: {dataset.get('title')}")
    say(f"  Φορέας: {organization.get('title') or organization.get('name')}")
    say(f"  Άδεια: {dataset.get('license_id')} | {dataset.get('license_title')}")
    say(f"  Τελευταία μεταβολή μεταδεδομένων: {dataset.get('metadata_modified')}")
    say(f"  Πεδία μεταδεδομένων: {', '.join(sorted(dataset.keys()))}")
    say(f"  Πρόσθετα πεδία (extras): {', '.join(k for k in extras if k) or '(κανένα)'}")
    say(f"  Αρχεία (resources): {len(resources)}")
    if resources:
        first = resources[0]
        say(f"  Πεδία αρχείου: {', '.join(sorted(first.keys()))}")
        say(f"  Πρώτο αρχείο: μορφή {first.get('format')} | {first.get('url')}")

    usage = matching_keys(dataset.keys(), ("view", "download", "track", "visit", "popular"))
    say(f"  Πεδία σχετικά με στοιχεία χρήσης: {', '.join(usage) or '(κανένα)'}")
    hvd = matching_keys(list(dataset.keys()) + extras, ("hvd", "legislation", "high_value", "highvalue"))
    say(f"  Πεδία σχετικά με σήμανση υψηλής αξίας (HVD): {', '.join(hvd) or '(κανένα)'}")


def probe_api() -> dict:
    import requests  # φορτώνεται εδώ, αφού επιβεβαιωθεί η εγκατάστασή του

    title(f"4. API του data.gov.gr ({API_URL})")
    results: dict = {}

    with requests.Session() as session:
        # 4.1 -------------------------------------------------------------
        say("4.1 Λογισμικό της πύλης (status_show)")
        record, data = call(session, API_URL + "status_show")
        results["status_show"] = record
        status = ckan_result(data)
        if isinstance(status, dict):
            extensions = status.get("extensions") or []
            say(f"  Λογισμικό: CKAN {status.get('ckan_version')}")
            say(f"  Τίτλος πύλης: {status.get('site_title')}")
            say(f"  Πρόσθετα (plugins): {', '.join(extensions) or '(δεν αναφέρονται)'}")
            for word, meaning in (
                ("dcat", "περιγραφές DCAT"),
                ("croissant", "περιγραφές Croissant"),
                ("tracking", "μέτρηση προβολών"),
                ("scheming", "προσαρμοσμένα πεδία μεταδεδομένων"),
            ):
                found = matching_keys(extensions, (word,))
                say(f"    {meaning}: {'ΝΑΙ (' + ', '.join(found) + ')' if found else 'όχι'}")
        else:
            say("  Η απάντηση δεν έχει τη μορφή του CKAN· η πλήρης απάντηση αποθηκεύεται για εξέταση.")

        # 4.2 -------------------------------------------------------------
        say()
        say("4.2 Δείγμα ενός συνόλου (package_search, rows=1)")
        record, data = call(session, API_URL + "package_search", {"rows": 1})
        results["package_search_one"] = record
        found = ckan_result(data)
        dataset = None
        if isinstance(found, dict):
            say(f"  Σύνολα δεδομένων στην πύλη: {found.get('count')}")
            if found.get("results"):
                dataset = found["results"][0]
                describe_dataset(dataset)

        # 4.3 -------------------------------------------------------------
        say()
        say("4.3 Συχνότεροι φορείς, άδειες και μορφές αρχείων (facets)")
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
            labels = {"organization": "Φορείς", "license_id": "Άδειες", "res_format": "Μορφές αρχείων"}
            for field in fields:
                items = (facets.get(field) or {}).get("items") or []
                items = sorted(items, key=lambda item: item.get("count", 0), reverse=True)
                say(f"  {labels[field]} (έως 15, κατά πλήθος συνόλων):")
                for item in items[:15]:
                    say(f"    {item.get('count', 0):>6}  {item.get('display_name') or item.get('name')}")

        if dataset:
            name = dataset.get("name")

            # 4.4 ---------------------------------------------------------
            say()
            say("4.4 Στοιχεία χρήσης του συνόλου-δείγματος (package_show με include_tracking)")
            record, data = call(session, API_URL + "package_show", {"id": name, "include_tracking": "true"})
            shown = ckan_result(data)
            tracking = shown.get("tracking_summary") if isinstance(shown, dict) else None
            record.pop("json", None)  # τα πλήρη μεταδεδομένα έχουν ήδη αποθηκευτεί στο 4.2
            record["tracking_summary"] = tracking
            results["package_show_tracking"] = record
            if tracking:
                say(f"  ΝΑΙ: συνολικές προβολές {tracking.get('total')}, πρόσφατες {tracking.get('recent')}")
            else:
                say("  Όχι: η απάντηση δεν περιέχει tracking_summary.")

            # 4.5 ---------------------------------------------------------
            say()
            say("4.5 Ταξινόμηση κατά πρόσφατες προβολές (sort=views_recent desc)")
            record, data = call(
                session,
                API_URL + "package_search",
                {"rows": 5, "sort": "views_recent desc", "include_tracking": "true"},
            )
            found = ckan_result(data)
            record.pop("json", None)  # τα πέντε πλήρη σύνολα δεν χρειάζεται να αποθηκευτούν
            if isinstance(found, dict):
                say("  Η ταξινόμηση έγινε δεκτή. Τα πρώτα 5 σύνολα:")
                record["top"] = []
                for item in found.get("results") or []:
                    views = (item.get("tracking_summary") or {}).get("total", "άγνωστο")
                    record["top"].append({"name": item.get("name"), "views_total": views})
                    say(f"    {item.get('name')}  (προβολές: {views})")
            results["sort_by_views"] = record

            # 4.6 ---------------------------------------------------------
            say()
            say("4.6 Περιγραφές Croissant και DCAT για το σύνολο-δείγμα")
            for key, label, url in (
                ("croissant", "Croissant", f"{BASE_URL}/dataset/{name}/croissant.jsonld"),
                ("dcat_jsonld", "DCAT (JSON-LD)", f"{BASE_URL}/dataset/{name}.jsonld"),
            ):
                record, data = call(session, url)
                results[key] = record
                if record.get("status") == 200 and data is not None:
                    say(f"  {label}: ΝΑΙ, διαθέσιμη")
                else:
                    say(f"  {label}: όχι (απάντηση {record.get('status', 'αποτυχία σύνδεσης')})")
        else:
            say()
            say("  Δεν βρέθηκε σύνολο-δείγμα· τα βήματα 4.4 έως 4.6 παραλείπονται.")

    return results


# ---------------------------------------------------------------------------
# Κύριο πρόγραμμα
# ---------------------------------------------------------------------------

def main() -> int:
    # Ασφαλής εκτύπωση ελληνικών, ανεξάρτητα από τη ρύθμιση της κονσόλας.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    say(f"Έλεγχος περιβάλλοντος εργασίας: {dt.datetime.now():%Y-%m-%d %H:%M}")
    say(f"Φάκελος έργου: {ROOT}")

    check_python()
    packages_ok = check_packages()
    check_utf8()

    results: dict = {"date": TODAY, "python": platform.python_version(), "base_url": BASE_URL}
    if packages_ok:
        results.update(probe_api())
    else:
        say()
        say("Οι κλήσεις στο API παραλείπονται μέχρι την εγκατάσταση των βιβλιοθηκών.")

    probe_file = RAW_DIR / f"api_probe_{TODAY}.json"
    log_file = OUT_DIR / "00_check_setup.log"

    title("5. Αποθήκευση αποτελεσμάτων")
    say(f"Απαντήσεις του API: {probe_file.relative_to(ROOT)}")
    say(f"Καταγραφή εκτέλεσης: {log_file.relative_to(ROOT)}")

    probe_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    say("Η αποθήκευση ολοκληρώθηκε.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
