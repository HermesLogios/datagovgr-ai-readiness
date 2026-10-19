r"""
00_check_setup.py
Φάση 0: έλεγχος της εγκατάστασης και πρώτη γνωριμία με το API του data.gov.gr.

Τι κάνει, με τη σειρά:
  1. Δείχνει την έκδοση της Python και αν τρέχουμε μέσα στο εικονικό περιβάλλον (.venv).
  2. Ελέγχει ότι είναι εγκατεστημένες οι βιβλιοθήκες του requirements.txt.
  3. Γράφει και ξαναδιαβάζει ελληνικό κείμενο, για να βεβαιωθούμε ότι η κωδικοποίηση UTF-8 δουλεύει.
  4. Κάνει λίγες, ήπιες κλήσεις στο API του data.gov.gr (μία ανά δευτερόλεπτο) και καταγράφει τι απαντά:
       4.1 status_show     ποιο λογισμικό τρέχει η πύλη (π.χ. CKAN) και με ποια πρόσθετα (plugins)
       4.2 package_search  πόσα σύνολα υπάρχουν και πώς μοιάζουν τα μεταδεδομένα ενός από αυτά
       4.3 facets          οι συχνότεροι φορείς, άδειες και μορφές αρχείων σε όλο τον κατάλογο
       4.4 package_show    αν η πύλη δίνει στοιχεία χρήσης (προβολές) για ένα σύνολο
       4.5 ταξινόμηση      αν μπορούμε να ζητήσουμε τα σύνολα με τις περισσότερες προβολές
       4.6 Croissant/DCAT  αν η πύλη βγάζει ήδη τέτοιες περιγραφές για ένα σύνολο
  5. Σώζει όλες τις απαντήσεις στο data/raw/api_probe_ΕΕΕΕ-ΜΜ-ΗΗ.json
     και ό,τι τύπωσε στην οθόνη στο outputs/00_check_setup.log.

Πώς τρέχει (από τον κεντρικό φάκελο του έργου, με ενεργό το .venv):
    python scripts\00_check_setup.py

Το script μόνο διαβάζει από την πύλη· δεν αλλάζει τίποτα εκεί.
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

# Ο κεντρικός φάκελος του έργου είναι ο «γονιός» του φακέλου scripts/.
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "outputs"

# Η διεύθυνση της πύλης. Αν ποτέ αλλάξει, ορίζουμε τη μεταβλητή περιβάλλοντος
# DATAGOVGR_BASE_URL και δεν χρειάζεται να πειράξουμε τον κώδικα.
BASE_URL = os.environ.get("DATAGOVGR_BASE_URL", "https://data.gov.gr").rstrip("/")
API_URL = BASE_URL + "/api/3/action/"

# Με αυτό το «όνομα» συστηνόμαστε στην πύλη (εδώ επιτρέπονται μόνο λατινικοί χαρακτήρες).
HEADERS = {"User-Agent": "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)"}

PAUSE_SECONDS = 1.0          # παύση μετά από κάθε κλήση, για να μην επιβαρύνουμε την πύλη
TIMEOUT_SECONDS = 30         # πόσο περιμένουμε απάντηση πριν τα παρατήσουμε
MAX_STORED_BYTES = 300_000   # πιο μεγάλες απαντήσεις δεν σώζονται ολόκληρες στο αρχείο

TODAY = dt.date.today().isoformat()
log_lines: list[str] = []    # ό,τι τυπώνουμε, για να το σώσουμε και σε αρχείο


# ---------------------------------------------------------------------------
# Βοηθητικές συναρτήσεις για την οθόνη
# ---------------------------------------------------------------------------

def say(text: str = "") -> None:
    """Τυπώνει μια γραμμή στην οθόνη και κρατά αντίγραφο για το αρχείο καταγραφής."""
    print(text, flush=True)
    log_lines.append(text)


def title(text: str) -> None:
    """Τυπώνει έναν τίτλο ενότητας."""
    say()
    say("=" * 70)
    say(text)
    say("=" * 70)


# ---------------------------------------------------------------------------
# 1-3. Έλεγχοι του υπολογιστή
# ---------------------------------------------------------------------------

def check_python() -> None:
    title("1. Python")
    say(f"Έκδοση: {platform.python_version()}")
    say(f"Πρόγραμμα: {sys.executable}")
    if sys.version_info < (3, 11):
        say("[!] Χρειάζεται Python 3.11 ή νεότερη (το pandas 3 δεν τρέχει σε παλαιότερες).")
    else:
        say("[OK] Η έκδοση είναι κατάλληλη.")
    # Μέσα σε venv, το sys.prefix (φάκελος του venv) διαφέρει από το sys.base_prefix (η «κανονική» Python).
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        say("[OK] Τρέχουμε μέσα στο εικονικό περιβάλλον (.venv).")
    else:
        say(r"[!] ΔΕΝ τρέχουμε μέσα στο .venv. Ενεργοποίησέ το με:  .\.venv\Scripts\Activate.ps1")


def check_packages() -> bool:
    title("2. Βιβλιοθήκες")
    all_ok = True
    for name in ("requests", "pandas", "tqdm"):
        try:
            module = __import__(name)
            say(f"[OK] {name} {getattr(module, '__version__', '')}")
        except ImportError:
            all_ok = False
            say(f"[!] Λείπει η βιβλιοθήκη {name}. Τρέξε:  python -m pip install -r requirements.txt")
    return all_ok


def check_utf8() -> None:
    title("3. Ελληνικά και κωδικοποίηση UTF-8")
    sample = "Δοκιμή ελληνικών: ά έ ή ί ό ύ ώ ϊ ϋ ΐ ΰ - Αθήνα, Θεσσαλονίκη, Ρόδος"
    test_file = RAW_DIR / "_utf8_test.txt"
    test_file.write_text(sample, encoding="utf-8")
    back = test_file.read_text(encoding="utf-8")
    test_file.unlink()
    if back == sample:
        say("[OK] Ελληνικό κείμενο γράφτηκε σε αρχείο και διαβάστηκε σωστά.")
    else:
        say("[!] Το κείμενο άλλαξε στη διαδρομή: υπάρχει πρόβλημα κωδικοποίησης.")
    say(f"Κωδικοποίηση οθόνης: {sys.stdout.encoding}")
    say(f"Προεπιλεγμένη κωδικοποίηση αρχείων: {locale.getpreferredencoding(False)}")
    say(f"PYTHONUTF8 = {os.environ.get('PYTHONUTF8', '(δεν έχει οριστεί)')}")


# ---------------------------------------------------------------------------
# 4. Κλήσεις στο API
# ---------------------------------------------------------------------------

def call(session, url: str, params: dict | None = None) -> tuple[dict, object]:
    """Κάνει μία κλήση GET.

    Επιστρέφει δύο πράγματα:
      - ένα «δελτίο» (record) με ό,τι μάθαμε, που θα σωθεί στο αρχείο,
      - τα δεδομένα της απάντησης (data), αν ήταν JSON, αλλιώς None.
    """
    record: dict = {"url": url, "params": params or {}}
    try:
        response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except Exception as error:  # π.χ. δεν υπάρχει σύνδεση, ή τη μπλοκάρει κάποιο τείχος προστασίας
        record["error"] = f"{type(error).__name__}: {error}"
        say(f"  [!] Σφάλμα σύνδεσης: {record['error']}")
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
        # Δεν ήταν JSON (π.χ. σελίδα HTML): κρατάμε την αρχή του κειμένου για να δούμε τι ήταν.
        record["text_start"] = response.text[:1000]
        return record, None

    if record["size_bytes"] <= MAX_STORED_BYTES:
        record["json"] = data
    else:
        record["note"] = "Μεγάλη απάντηση: δεν σώθηκε ολόκληρη στο αρχείο."
    return record, data


def ckan_result(data: object) -> object:
    """Αν η απάντηση είναι επιτυχημένη απάντηση του CKAN, επιστρέφει το περιεχόμενό της («result»)."""
    if isinstance(data, dict) and data.get("success") is True:
        return data.get("result")
    if isinstance(data, dict) and "error" in data:
        say(f"  [!] Η πύλη απάντησε με σφάλμα: {data['error']}")
    return None


def matching_keys(keys, words) -> list[str]:
    """Βρίσκει ονόματα πεδίων που περιέχουν κάποια από τις λέξεις (χωρίς διάκριση πεζών-κεφαλαίων)."""
    return [key for key in keys if key and any(word in key.lower() for word in words)]


def describe_dataset(dataset: dict) -> None:
    """Τυπώνει τα βασικά μεταδεδομένα ενός συνόλου, για να δούμε τη μορφή τους."""
    organization = dataset.get("organization") or {}
    extras = [extra.get("key") for extra in dataset.get("extras") or [] if isinstance(extra, dict)]
    resources = dataset.get("resources") or []

    say(f"  Όνομα (name): {dataset.get('name')}")
    say(f"  Τίτλος: {dataset.get('title')}")
    say(f"  Φορέας: {organization.get('title') or organization.get('name')}")
    say(f"  Άδεια: {dataset.get('license_id')} | {dataset.get('license_title')}")
    say(f"  Τελευταία αλλαγή μεταδεδομένων: {dataset.get('metadata_modified')}")
    say(f"  Πεδία μεταδεδομένων: {', '.join(sorted(dataset.keys()))}")
    say(f"  Πρόσθετα πεδία (extras): {', '.join(k for k in extras if k) or '(κανένα)'}")
    say(f"  Αρχεία (resources): {len(resources)}")
    if resources:
        first = resources[0]
        say(f"  Πεδία αρχείου: {', '.join(sorted(first.keys()))}")
        say(f"  Πρώτο αρχείο: μορφή {first.get('format')} | {first.get('url')}")

    usage = matching_keys(dataset.keys(), ("view", "download", "track", "visit", "popular"))
    say(f"  Πεδία που μοιάζουν με στοιχεία χρήσης: {', '.join(usage) or '(κανένα)'}")
    hvd = matching_keys(list(dataset.keys()) + extras, ("hvd", "legislation", "high_value", "highvalue"))
    say(f"  Πεδία που μοιάζουν με σήμανση υψηλής αξίας (HVD): {', '.join(hvd) or '(κανένα)'}")


def probe_api() -> dict:
    import requests  # το φορτώνουμε εδώ, αφού βεβαιωθήκαμε ότι είναι εγκατεστημένο

    title(f"4. API του data.gov.gr ({API_URL})")
    results: dict = {}

    with requests.Session() as session:
        # 4.1 -------------------------------------------------------------
        say("4.1 Ποιο λογισμικό τρέχει η πύλη (status_show)")
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
            say("  Δεν πήραμε απάντηση τύπου CKAN. Θα το εξετάσουμε στο αρχείο που σώζεται.")

        # 4.2 -------------------------------------------------------------
        say()
        say("4.2 Ένα σύνολο ως δείγμα (package_search, rows=1)")
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
                say(f"  {labels[field]} (έως 15, με σειρά πλήθους συνόλων):")
                for item in items[:15]:
                    say(f"    {item.get('count', 0):>6}  {item.get('display_name') or item.get('name')}")

        if dataset:
            name = dataset.get("name")

            # 4.4 ---------------------------------------------------------
            say()
            say("4.4 Στοιχεία χρήσης για το δείγμα (package_show με include_tracking)")
            record, data = call(session, API_URL + "package_show", {"id": name, "include_tracking": "true"})
            shown = ckan_result(data)
            tracking = shown.get("tracking_summary") if isinstance(shown, dict) else None
            record.pop("json", None)  # τα πλήρη μεταδεδομένα τα σώσαμε ήδη στο 4.2
            record["tracking_summary"] = tracking
            results["package_show_tracking"] = record
            if tracking:
                say(f"  ΝΑΙ: προβολές συνολικά {tracking.get('total')}, πρόσφατα {tracking.get('recent')}")
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
            record.pop("json", None)  # δεν χρειάζεται να σώσουμε πέντε ολόκληρα σύνολα
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
            say("4.6 Περιγραφές Croissant και DCAT για το δείγμα")
            for key, label, url in (
                ("croissant", "Croissant", f"{BASE_URL}/dataset/{name}/croissant.jsonld"),
                ("dcat_jsonld", "DCAT (JSON-LD)", f"{BASE_URL}/dataset/{name}.jsonld"),
            ):
                record, data = call(session, url)
                results[key] = record
                if record.get("status") == 200 and data is not None:
                    say(f"  {label}: ΝΑΙ, υπάρχει")
                else:
                    say(f"  {label}: όχι (απάντηση {record.get('status', 'σφάλμα σύνδεσης')})")
        else:
            say()
            say("  Δεν βρέθηκε σύνολο-δείγμα, οπότε παραλείπω τα βήματα 4.4 έως 4.6.")

    return results


# ---------------------------------------------------------------------------
# Κύριο πρόγραμμα
# ---------------------------------------------------------------------------

def main() -> int:
    # Τα ελληνικά να τυπώνονται χωρίς σφάλμα, όπως κι αν είναι ρυθμισμένη η οθόνη.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    say(f"Έλεγχος εγκατάστασης: {dt.datetime.now():%Y-%m-%d %H:%M}")
    say(f"Φάκελος έργου: {ROOT}")

    check_python()
    packages_ok = check_packages()
    check_utf8()

    results: dict = {"date": TODAY, "python": platform.python_version(), "base_url": BASE_URL}
    if packages_ok:
        results.update(probe_api())
    else:
        say()
        say("Παραλείπω τις κλήσεις στο API μέχρι να εγκατασταθούν οι βιβλιοθήκες.")

    probe_file = RAW_DIR / f"api_probe_{TODAY}.json"
    log_file = OUT_DIR / "00_check_setup.log"

    title("5. Τι κάνεις τώρα")
    say(f"Στείλε στο Claude το αρχείο:  {probe_file.relative_to(ROOT)}")
    say(f"(ή το {log_file.relative_to(ROOT)}, ή όλο το κείμενο αυτής της οθόνης)")

    probe_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nΑποθηκεύτηκαν:\n  {probe_file}\n  {log_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
