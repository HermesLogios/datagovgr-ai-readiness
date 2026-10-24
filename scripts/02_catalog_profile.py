r"""
02_catalog_profile.py
Φάση 1: περιγραφή του καταλόγου από ένα στιγμιότυπο.

Λειτουργία, με τη σειρά:
  1. Ανάγνωση του νεότερου στιγμιοτύπου (data/raw/catalog_ΕΕΕΕ-ΜΜ-ΗΗ.jsonl.gz) ή αυτού που
     δίνεται με --snapshot.
  2. Για κάθε σύνολο δεδομένων (type = dataset) υπολογίζεται μία γραμμή με τα βασικά του
     χαρακτηριστικά: φορέας, θεματική, σημάνσεις υψηλής αξίας, άδειες, μορφές αρχείων,
     μηχαναγνωσιμότητα, στοιχεία χρήσης, κατάσταση συνδέσμων, βαθμολογία MQA της πύλης.
     Οι γραμμές αποθηκεύονται στο data/processed/catalog_flat_ΕΕΕΕ-ΜΜ-ΗΗ.csv, που είναι ο
     πίνακας εργασίας για την επιλογή του δείγματος και τους επόμενους ελέγχους.
  3. Από τον πίνακα αυτόν παράγονται συγκεντρωτικοί πίνακες και μια σύνοψη σε απλή γλώσσα,
     στον φάκελο outputs/profile_ΕΕΕΕ-ΜΜ-ΗΗ/:
        summary.md            σύνοψη των βασικών μεγεθών (τυπώνεται και στην οθόνη)
        summary.json          τα ίδια μεγέθη σε μορφή για πρόγραμμα
        by_organization.csv   σύνολα ανά φορέα
        by_license.csv        άδειες σε επίπεδο συνόλου και σε επίπεδο αρχείου
        by_format.csv         μορφές αρχείων
        by_theme.csv          θεματικές κατηγορίες
        by_hvd_category.csv   κατηγορίες υψηλής αξίας
        by_year.csv           σύνολα ανά έτος καταχώρισης
        top_viewed.csv        τα 50 σύνολα με τις περισσότερες προβολές

Σημειώσεις μεθόδου:
  - Οι αυτόματες δέσμες «Όλα τα δεδομένα πόρων» (ZIP που παράγει η ίδια η πύλη για κάθε σύνολο)
    εξαιρούνται από τις μετρήσεις μορφών, μηχαναγνωσιμότητας και συνδέσμων, ώστε να μετριούνται
    μόνο τα αρχεία που ανέβασε ο φορέας.
  - Ένα σύνολο θεωρείται μηχαναγνώσιμο αν τουλάχιστον ένα αρχείο του έχει μορφή από τη λίστα
    MACHINE_READABLE. Αρχεία PDF, Word, εικόνες και συμπιεσμένα αρχεία δεν μετρούν.
  - Η κατάσταση συνδέσμων και η βαθμολογία MQA προέρχονται από τα πρόσθετα qa και archiver της
    ίδιας της πύλης (CKAN) και επαληθεύονται στο δείγμα σε επόμενη φάση.

Εκτέλεση (από τον κεντρικό φάκελο του έργου, με ενεργό το .venv):
    python scripts\02_catalog_profile.py
    python scripts\02_catalog_profile.py --snapshot data\raw\catalog_2026-10-24.jsonl.gz

Άδεια κώδικα: EUPL-1.2
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Ρυθμίσεις και λεξιλόγια
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"

HVD_TYPE = "http://publications.europa.eu/resource/authority/dataset-type/HVD"

# Οι έξι κατηγορίες υψηλής αξίας του Κανονισμού (ΕΕ) 2023/138, με τους κωδικούς του
# λεξιλογίου της ΕΕ (http://data.europa.eu/bna/...).
HVD_CATEGORIES = {
    "c_ac64a52d": "Γεωχωρικά",
    "c_dd313021": "Γεωσκόπηση και περιβάλλον",
    "c_164e0bf5": "Μετεωρολογικά",
    "c_e1da4e07": "Στατιστικά",
    "c_a9135398": "Εταιρείες και ιδιοκτησία εταιρειών",
    "c_b79e35eb": "Κινητικότητα",
}

# Θεματικές κατηγορίες του λεξιλογίου data-theme της ΕΕ.
THEMES = {
    "AGRI": "Γεωργία, αλιεία, δασοκομία και τρόφιμα",
    "ECON": "Οικονομία και χρηματοοικονομικά",
    "EDUC": "Εκπαίδευση, πολιτισμός και αθλητισμός",
    "ENER": "Ενέργεια",
    "ENVI": "Περιβάλλον",
    "GOVE": "Κυβέρνηση και δημόσιος τομέας",
    "HEAL": "Υγεία",
    "INTR": "Διεθνή θέματα",
    "JUST": "Δικαιοσύνη, νομικό σύστημα και δημόσια ασφάλεια",
    "REGI": "Περιφέρειες και πόλεις",
    "SOCI": "Πληθυσμός και κοινωνία",
    "TECH": "Επιστήμη και τεχνολογία",
    "TRAN": "Μεταφορές",
    "OP_DATPRO": "Προσωρινά δεδομένα",
}

# Μορφές που διαβάζονται απευθείας από πρόγραμμα (δομημένα δεδομένα ή γεωχωρικές υπηρεσίες).
MACHINE_READABLE = {
    "CSV", "TSV", "JSON", "GEOJSON", "JSONLD", "JSON-LD", "XML", "RDF", "TTL", "N3", "NT",
    "XLS", "XLSX", "ODS", "PARQUET", "SDMX", "SDMX-ML", "NETCDF", "NC", "GRIB", "HDF5",
    "SHP", "SHAPE-ZIP", "SHAPEFILE", "KML", "KMZ", "GML", "GPKG", "GEOTIFF", "WMS", "WFS",
    "WCS", "WMTS", "OGC API", "API", "REST", "SQLITE", "SQL", "ICS", "GTFS", "ATOM", "RSS",
}

# Τιμές που σημαίνουν ότι δεν έχει δηλωθεί άδεια σε επίπεδο συνόλου.
NO_LICENSE = {None, "", "notspecified"}

# Λέξεις στο αναγνωριστικό της άδειας που δείχνουν ανοιχτή άδεια κατάλληλη για σύνολα υψηλής
# αξίας (CC0, CC BY 4.0) ή γενικά ανοιχτή (CC BY, ODC-BY, PDDL, ODbL, «other-open», «other-pd»).
OPEN_LICENSE_HINTS = ("cc0", "cc_by_4", "cc-by-4", "cc-by", "cc_by", "odc-by", "odc_by", "pddl", "odbl", "other-open", "other-pd")


# ---------------------------------------------------------------------------
# Βοηθητικές συναρτήσεις
# ---------------------------------------------------------------------------

def as_list(value) -> list:
    """Επιστρέφει πάντα λίστα: τα πεδία πολλαπλών τιμών του CKAN έρχονται άλλοτε ως λίστα,
    άλλοτε ως κείμενο JSON και άλλοτε ως απλό κείμενο."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                return parsed if isinstance(parsed, list) else [parsed]
            except ValueError:
                pass
        return [text]
    return [value]


def code_of(uri: str) -> str:
    """Το τελευταίο τμήμα ενός URI λεξιλογίου, π.χ. .../data-theme/SOCI -> SOCI."""
    return str(uri).rstrip("/").rsplit("/", 1)[-1]


def is_bundle(resource: dict) -> bool:
    """Η αυτόματη δέσμη ZIP «Όλα τα δεδομένα πόρων» που παράγει η πύλη."""
    return bool(resource.get("downloadall_datapackage_hash"))


def norm_format(resource: dict) -> str:
    """Η μορφή ενός αρχείου σε κεφαλαία, χωρίς κενά· κενή αν δεν έχει δηλωθεί."""
    return (resource.get("format") or "").strip().upper()


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_open_license(identifier) -> bool:
    text = str(identifier or "").lower()
    return any(hint in text for hint in OPEN_LICENSE_HINTS)


def fmt_int(n) -> str:
    """Αριθμός με τελεία ως διαχωριστικό χιλιάδων (ελληνική γραφή)."""
    return f"{int(n):,}".replace(",", ".")


def fmt_pct(part, whole) -> str:
    if not whole:
        return "–"
    return f"{100 * part / whole:.1f}".replace(".", ",") + "%"


def newest_snapshot() -> Path:
    candidates = sorted(
        p for p in RAW_DIR.glob("catalog_*.jsonl.gz") if "_test" not in p.name
    )
    if not candidates:
        raise SystemExit("Δεν βρέθηκε στιγμιότυπο στο data/raw. Εκτέλεση πρώτα του 01_snapshot.py.")
    return candidates[-1]


def snapshot_date(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else dt.date.today().isoformat()


# ---------------------------------------------------------------------------
# Μία γραμμή ανά σύνολο δεδομένων
# ---------------------------------------------------------------------------

def flatten(dataset: dict) -> dict:
    organization = dataset.get("organization") or {}
    resources = [r for r in dataset.get("resources") or [] if isinstance(r, dict)]
    own_resources = [r for r in resources if not is_bundle(r)]

    themes = [code_of(t) for t in as_list(dataset.get("theme"))]
    hvd_categories = [code_of(c) for c in as_list(dataset.get("hvd_category"))]
    dcat_types = as_list(dataset.get("dcat_type"))
    legislation = as_list(dataset.get("applicable_legislation"))

    formats = sorted({norm_format(r) for r in own_resources if norm_format(r)})
    resource_licenses = sorted({str(r.get("license")).strip() for r in own_resources if r.get("license")})

    checked = [r for r in own_resources if isinstance(r.get("archiver"), dict)]
    broken = [r for r in checked if r["archiver"].get("is_broken") is True]

    mqa_scores = [to_float(r["qa"].get("mqa_score")) for r in resources if isinstance(r.get("qa"), dict)]
    mqa_scores = [s for s in mqa_scores if s is not None]
    openness = [to_float(r["qa"].get("openness_score")) for r in resources if isinstance(r.get("qa"), dict)]
    openness = [s for s in openness if s is not None]

    tracking = dataset.get("tracking_summary") or {}
    resource_views = sum(int((r.get("tracking_summary") or {}).get("total") or 0) for r in resources)

    license_id = dataset.get("license_id")
    license_dataset_ok = license_id not in NO_LICENSE
    license_any = license_dataset_ok or bool(resource_licenses)
    license_open = is_open_license(license_id) or any(is_open_license(l) for l in resource_licenses)

    return {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "title": (dataset.get("title") or "").strip(),
        "organization": organization.get("name"),
        "organization_title": organization.get("title"),
        "metadata_created": (dataset.get("metadata_created") or "")[:10],
        "metadata_modified": (dataset.get("metadata_modified") or "")[:10],
        "year_created": (dataset.get("metadata_created") or "")[:4],
        "themes": ";".join(themes),
        "hvd_type": HVD_TYPE in dcat_types,
        "hvd_categories": ";".join(hvd_categories),
        "hvd_legislation": any("2023/138" in str(x) for x in legislation),
        "is_hvd": HVD_TYPE in dcat_types or bool(hvd_categories) or any("2023/138" in str(x) for x in legislation),
        "license_id": license_id or "",
        "license_dataset_ok": license_dataset_ok,
        "resource_licenses": ";".join(resource_licenses),
        "license_any": license_any,
        "license_open": license_open,
        "n_resources": len(own_resources),
        "formats": ";".join(formats),
        "machine_readable": any(f in MACHINE_READABLE for f in formats),
        "n_resources_checked": len(checked),
        "n_resources_broken": len(broken),
        "mqa_max": max(mqa_scores) if mqa_scores else None,
        "openness_max": max(openness) if openness else None,
        "views_total": int(tracking.get("total") or 0),
        "views_recent": int(tracking.get("recent") or 0),
        "resource_views_total": resource_views,
        "has_description": bool((dataset.get("notes") or "").strip()),
        "has_keywords": int(dataset.get("num_tags") or 0) > 0,
        "has_theme": bool(themes),
        "has_contact": bool(as_list(dataset.get("contact"))),
        "has_spatial": bool(as_list(dataset.get("spatial_coverage"))),
        "has_temporal": bool(as_list(dataset.get("temporal_coverage"))),
        "has_frequency": bool(dataset.get("frequency")),
        "frequency": code_of(dataset.get("frequency") or ""),
    }


# ---------------------------------------------------------------------------
# Συγκεντρωτικοί πίνακες
# ---------------------------------------------------------------------------

def explode_counts(frame: pd.DataFrame, column: str) -> Counter:
    """Μετρά σύνολα ανά τιμή σε στήλη με τιμές χωρισμένες με «;» (ένα σύνολο μετρά σε κάθε τιμή του)."""
    counts: Counter = Counter()
    for cell in frame[column]:
        for value in str(cell).split(";"):
            if value and value != "nan":
                counts[value] += 1
    return counts


def build_tables(frame: pd.DataFrame, n: int) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}

    org = frame.groupby(["organization", "organization_title"], dropna=False).agg(
        datasets=("id", "count"),
        hvd_datasets=("is_hvd", "sum"),
        without_license=("license_any", lambda s: int((~s).sum())),
        not_machine_readable=("machine_readable", lambda s: int((~s).sum())),
        views_total=("views_total", "sum"),
    ).reset_index().sort_values("datasets", ascending=False)
    tables["by_organization"] = org

    lic_ds = frame["license_id"].replace("", "(καμία)").value_counts().rename_axis("license").reset_index(name="datasets")
    lic_ds.insert(0, "level", "σύνολο")
    lic_res = pd.Series(explode_counts(frame, "resource_licenses")).rename_axis("license").reset_index(name="datasets")
    lic_res.insert(0, "level", "αρχείο")
    tables["by_license"] = pd.concat([lic_ds, lic_res], ignore_index=True)

    fmt = pd.Series(explode_counts(frame, "formats")).rename_axis("format").reset_index(name="datasets")
    fmt["machine_readable"] = fmt["format"].isin(MACHINE_READABLE)
    fmt["share"] = (fmt["datasets"] / n).round(4)
    tables["by_format"] = fmt.sort_values("datasets", ascending=False)

    theme = pd.Series(explode_counts(frame, "themes")).rename_axis("theme").reset_index(name="datasets")
    theme["label"] = theme["theme"].map(THEMES).fillna("(άλλη)")
    theme["share"] = (theme["datasets"] / n).round(4)
    tables["by_theme"] = theme.sort_values("datasets", ascending=False)

    hvd = pd.Series(explode_counts(frame, "hvd_categories")).rename_axis("category").reset_index(name="datasets")
    hvd["label"] = hvd["category"].map(HVD_CATEGORIES).fillna("(άλλη ή υποκατηγορία)")
    tables["by_hvd_category"] = hvd.sort_values("datasets", ascending=False)

    year = frame["year_created"].value_counts().sort_index().rename_axis("year").reset_index(name="datasets")
    tables["by_year"] = year

    top = frame.sort_values("views_total", ascending=False).head(50)[
        ["name", "title", "organization_title", "views_total", "views_recent", "is_hvd", "hvd_categories", "formats"]
    ]
    tables["top_viewed"] = top
    return tables


# ---------------------------------------------------------------------------
# Σύνοψη σε απλή γλώσσα
# ---------------------------------------------------------------------------

def build_summary(frame: pd.DataFrame, counts_by_type: Counter, tables: dict, date: str, source: str) -> tuple[dict, str]:
    n = len(frame)
    views = frame["views_total"].tolist()
    checked = int(frame["n_resources_checked"].sum())
    broken = int(frame["n_resources_broken"].sum())
    hvd_any = int(frame["is_hvd"].sum())
    hvd_type = int(frame["hvd_type"].sum())
    hvd_cat = int((frame["hvd_categories"] != "").sum())
    hvd_leg = int(frame["hvd_legislation"].sum())
    mqa = frame["mqa_max"].dropna().tolist()

    summary = {
        "snapshot_date": date,
        "source_file": source,
        "records_total": int(sum(counts_by_type.values())),
        "records_by_type": dict(counts_by_type),
        "datasets": n,
        "organizations": int(frame["organization"].nunique()),
        "hvd_any_flag": hvd_any,
        "hvd_type_flag": hvd_type,
        "hvd_category_flag": hvd_cat,
        "hvd_legislation_flag": hvd_leg,
        "hvd_all_three_flags": int((frame["hvd_type"] & (frame["hvd_categories"] != "") & frame["hvd_legislation"]).sum()),
        "license_dataset_level": int(frame["license_dataset_ok"].sum()),
        "license_any_level": int(frame["license_any"].sum()),
        "license_none": int((~frame["license_any"]).sum()),
        "license_open": int(frame["license_open"].sum()),
        "machine_readable": int(frame["machine_readable"].sum()),
        "not_machine_readable": int((~frame["machine_readable"]).sum()),
        "without_resources": int((frame["n_resources"] == 0).sum()),
        "resources_checked": checked,
        "resources_broken": broken,
        "datasets_with_broken": int((frame["n_resources_broken"] > 0).sum()),
        "views_median": statistics.median(views) if views else None,
        "views_mean": round(statistics.mean(views), 1) if views else None,
        "views_zero": int((frame["views_total"] == 0).sum()),
        "mqa_median": statistics.median(mqa) if mqa else None,
        "has_description": int(frame["has_description"].sum()),
        "has_keywords": int(frame["has_keywords"].sum()),
        "has_theme": int(frame["has_theme"].sum()),
        "has_contact": int(frame["has_contact"].sum()),
        "has_spatial": int(frame["has_spatial"].sum()),
        "has_temporal": int(frame["has_temporal"].sum()),
        "has_frequency": int(frame["has_frequency"].sum()),
    }

    lines = [
        f"# Προφίλ καταλόγου data.gov.gr — στιγμιότυπο {date}",
        "",
        f"Πηγή: {source}. Όλα τα ποσοστά αναφέρονται στα {fmt_int(n)} σύνολα δεδομένων.",
        "",
        "## Μέγεθος",
        f"- Εγγραφές συνολικά: {fmt_int(summary['records_total'])} "
        f"(σύνολα δεδομένων {fmt_int(counts_by_type.get('dataset', 0))}, "
        f"υπηρεσίες δεδομένων {fmt_int(counts_by_type.get('data-service', 0))}, "
        f"αποφάσεις διάθεσης {fmt_int(counts_by_type.get('decision', 0))}).",
        f"- Φορείς με τουλάχιστον ένα σύνολο: {fmt_int(summary['organizations'])}.",
        "",
        "## Σύνολα υψηλής αξίας (HVD)",
        f"- Με οποιαδήποτε σήμανση HVD: {fmt_int(hvd_any)} ({fmt_pct(hvd_any, n)}).",
        f"- Με τύπο HVD: {fmt_int(hvd_type)} · με κατηγορία HVD: {fmt_int(hvd_cat)} · "
        f"με αναφορά στον Κανονισμό 2023/138: {fmt_int(hvd_leg)} · και με τα τρία: {fmt_int(summary['hvd_all_three_flags'])}.",
    ]
    for _, row in tables["by_hvd_category"].iterrows():
        lines.append(f"  - {row['label']}: {fmt_int(row['datasets'])}")
    lines += [
        "",
        "## Άδειες",
        f"- Άδεια δηλωμένη στο σύνολο: {fmt_int(summary['license_dataset_level'])} ({fmt_pct(summary['license_dataset_level'], n)}).",
        f"- Άδεια δηλωμένη στο σύνολο ή σε αρχείο του: {fmt_int(summary['license_any_level'])} ({fmt_pct(summary['license_any_level'], n)}).",
        f"- Χωρίς καμία άδεια: {fmt_int(summary['license_none'])} ({fmt_pct(summary['license_none'], n)}).",
        f"- Με ανοιχτή άδεια (CC0, CC BY, ODC, δημόσιο πεδίο): {fmt_int(summary['license_open'])} ({fmt_pct(summary['license_open'], n)}).",
        "",
        "## Μορφές αρχείων",
        f"- Με τουλάχιστον ένα μηχαναγνώσιμο αρχείο: {fmt_int(summary['machine_readable'])} ({fmt_pct(summary['machine_readable'], n)}).",
        f"- Χωρίς καμία μηχαναγνώσιμη μορφή: {fmt_int(summary['not_machine_readable'])} ({fmt_pct(summary['not_machine_readable'], n)}), "
        f"εκ των οποίων χωρίς κανένα αρχείο: {fmt_int(summary['without_resources'])}.",
        "- Συχνότερες μορφές (σύνολα που τις περιέχουν):",
    ]
    for _, row in tables["by_format"].head(10).iterrows():
        lines.append(f"  - {row['format']}: {fmt_int(row['datasets'])} ({fmt_pct(row['datasets'], n)})")
    lines += [
        "",
        "## Σύνδεσμοι και ποιότητα μεταδεδομένων κατά την πύλη",
        f"- Αρχεία που έχει ελέγξει ο ελεγκτής συνδέσμων της πύλης: {fmt_int(checked)} · μη προσβάσιμα: {fmt_int(broken)} ({fmt_pct(broken, checked)}).",
        f"- Σύνολα με τουλάχιστον ένα μη προσβάσιμο αρχείο: {fmt_int(summary['datasets_with_broken'])} ({fmt_pct(summary['datasets_with_broken'], n)}).",
        f"- Διάμεση βαθμολογία MQA (0–100): {summary['mqa_median'] if summary['mqa_median'] is not None else '–'}.",
        "",
        "## Πληρότητα βασικών μεταδεδομένων",
        f"- Περιγραφή: {fmt_pct(summary['has_description'], n)} · λέξεις-κλειδιά: {fmt_pct(summary['has_keywords'], n)} · "
        f"θεματική: {fmt_pct(summary['has_theme'], n)} · επαφή: {fmt_pct(summary['has_contact'], n)}.",
        f"- Χωρική κάλυψη: {fmt_pct(summary['has_spatial'], n)} · χρονική κάλυψη: {fmt_pct(summary['has_temporal'], n)} · "
        f"συχνότητα ενημέρωσης: {fmt_pct(summary['has_frequency'], n)}.",
        "",
        "## Χρήση (προβολές σελίδων στην πύλη)",
        f"- Διάμεσος προβολών ανά σύνολο: {summary['views_median']} · μέσος όρος: {summary['views_mean']} · "
        f"χωρίς καμία προβολή: {fmt_int(summary['views_zero'])} ({fmt_pct(summary['views_zero'], n)}).",
        "- Τα 10 σύνολα με τις περισσότερες προβολές:",
    ]
    for _, row in tables["top_viewed"].head(10).iterrows():
        lines.append(f"  - {fmt_int(row['views_total'])} · {row['title'][:80]} ({row['organization_title']})")
    lines += ["", "## Θεματικές κατηγορίες (ένα σύνολο μπορεί να έχει περισσότερες)"]
    for _, row in tables["by_theme"].head(8).iterrows():
        lines.append(f"- {row['label']} ({row['theme']}): {fmt_int(row['datasets'])} ({fmt_pct(row['datasets'], n)})")
    lines += ["", "## Φορείς με τα περισσότερα σύνολα"]
    for _, row in tables["by_organization"].head(10).iterrows():
        lines.append(f"- {row['organization_title']}: {fmt_int(row['datasets'])} (HVD: {fmt_int(row['hvd_datasets'])})")
    lines += ["", "## Σύνολα ανά έτος καταχώρισης στην πύλη"]
    for _, row in tables["by_year"].iterrows():
        lines.append(f"- {row['year'] or '(άγνωστο)'}: {fmt_int(row['datasets'])}")
    return summary, "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Κύριο πρόγραμμα
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Προφίλ του καταλόγου από ένα στιγμιότυπο.")
    parser.add_argument("--snapshot", type=Path, default=None, help="Αρχείο στιγμιοτύπου (.jsonl.gz). Προεπιλογή: το νεότερο.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    snapshot = args.snapshot or newest_snapshot()
    date = snapshot_date(snapshot)
    out_dir = OUT_DIR / f"profile_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Στιγμιότυπο: {snapshot.relative_to(ROOT) if snapshot.is_relative_to(ROOT) else snapshot}")

    counts_by_type: Counter = Counter()
    rows = []
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            record_type = record.get("type") or "(χωρίς τύπο)"
            counts_by_type[record_type] += 1
            if record_type == "dataset":
                rows.append(flatten(record))

    frame = pd.DataFrame(rows)
    flat_file = PROCESSED_DIR / f"catalog_flat_{date}.csv"
    frame.to_csv(flat_file, index=False, encoding="utf-8-sig")

    tables = build_tables(frame, len(frame))
    for name, table in tables.items():
        table.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8-sig")

    summary, text = build_summary(frame, counts_by_type, tables, date, snapshot.name)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.md").write_text(text, encoding="utf-8")

    print()
    print(text)
    print("Αρχεία:")
    print(f"  {flat_file.relative_to(ROOT)}  ({len(frame)} γραμμές)")
    print(f"  {out_dir.relative_to(ROOT)}\\  (summary.md, summary.json και {len(tables)} πίνακες CSV)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
