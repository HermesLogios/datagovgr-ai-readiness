r"""
03_sample.py
Phase 2: selection of the 36 datasets of the assessment sample.

What it does, in order:
  1. Reads the working table of 02_catalog_profile.py (data/processed/catalog_flat_YYYY-MM-DD.csv,
     the newest one or the one given with --flat) and the manual classification
     criteria/hvd_by_content.csv.
  2. High-value group, 24 datasets. A dataset belongs to a high-value category if the publisher
     declares the category in its metadata, or if its content corresponds to a dataset of the
     Annex of Implementing Regulation (EU) 2023/138 (decision "yes" in
     criteria/hvd_by_content.csv). The categories are filled in the order of DECISIONS.md #2.
     Within each category the datasets are ranked by page views and the most viewed dataset of
     each organisation is selected, until the quota of the category is filled.
  3. Comparison group, 12 datasets: random draw with a fixed seed from the datasets without any
     high-value flag. A drawn dataset counted as high-value by content is skipped and the next
     one in the random order is taken.
  4. Content screening: finds datasets whose title suggests content of a category's Annex items
     and that could enter the sample, either because their page views are enough to enter a
     high-value category or because they are drawn for the comparison group. Each of them needs
     a decision in criteria/hvd_by_content.csv. While decisions are missing, only the screening
     list is written and the sample is not drawn.
  5. Writes:
        data/processed/sample.csv                the 36 datasets, with the reason for each selection
        data/processed/sample_reserves.csv       replacements, in order of use
        outputs/sample_YYYY-MM-DD/summary.md     the sample in readable form, with links
        outputs/sample_YYYY-MM-DD/screening.csv  the screened datasets and the decisions on them

Method notes:
  - Only datasets with at least one resource of their own are eligible (the automatic
    "download all" bundle does not count).
  - Ranking: page views, then downloads, then recent views, then name, so that ties are always
    resolved in the same way.
  - The random draw uses NumPy's RandomState, whose sequence of numbers stays the same across
    NumPy versions, on the datasets sorted by id: the same table and seed always give the same
    sample.
  - Reserves replace, in order, datasets that are removed from the portal before their
    assessment: for a high-value category, the next datasets of the same ranking; for the
    comparison group, the next datasets of the same random order.
  - The sample is drawn once. If data/processed/sample.csv already exists, the script stops
    unless --force is given; every new draw is recorded in DECISIONS.md.

Usage (from the project root, with the .venv activated):
    python scripts\03_sample.py
    python scripts\03_sample.py --flat data\processed\catalog_flat_2026-10-24.csv
    python scripts\03_sample.py --force

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
CONTENT_FILE = ROOT / "criteria" / "hvd_by_content.csv"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
RESERVES_FILE = PROCESSED_DIR / "sample_reserves.csv"
DATASET_URL = "https://data.gov.gr/dataset/"

SAMPLE_VERSION = 1         # increased with every new draw recorded in DECISIONS.md

# High-value categories and the number of datasets of each, in the order of DECISIONS.md #2.
QUOTAS = [
    ("c_ac64a52d", "Geospatial", 5),
    ("c_e1da4e07", "Statistics", 5),
    ("c_b79e35eb", "Mobility", 5),
    ("c_dd313021", "Earth observation and environment", 3),
    ("c_164e0bf5", "Meteorological", 3),
    ("c_a9135398", "Companies and company ownership", 3),
]
RANDOM_SIZE = 12           # datasets of the comparison group
RANDOM_SEED = 20261024     # fixed before the draw (date of the snapshot)
MAX_PER_ORGANIZATION = 1   # datasets of the same organisation in one category; None = no limit
CATEGORY_RESERVES = 3      # reserves kept for each high-value category
RANDOM_RESERVES = 6        # reserves kept for the comparison group

# Ranking order: page views, downloads, recent views (descending), name (ascending).
RANK_COLUMNS = ["views_total", "resource_views_total", "views_recent", "name"]
RANK_ASCENDING = [False, False, False, True]

# Title terms that suggest content of each category's Annex items. Titles are compared in lower
# case and without accents. The terms only select datasets for manual review; the decision
# itself is recorded, with its reason, in criteria/hvd_by_content.csv.
SCREEN_TERMS = {
    # Administrative units, geographical names, addresses, buildings, cadastral parcels,
    # reference parcels, agricultural parcels.
    "c_ac64a52d": [
        "καλλικρατ", "καποδιστρ", "διοικητικ", r"ορια (δημ|περιφερ|νομ|κοινοτ)", r"\bδημοι\b",
        r"\bπεριφερειες\b", r"\bνομοι\b", "περιφερειακες ενοτητες", "δημοτικες (ενοτητες|κοινοτητες)",
        "τοπωνυμ", "γεωγραφικο λεξικο", "διευθυνσεις", r"\bοδων\b", "οδωνυμ", "ταχυδρομικ(οι|ων) κωδικ",
        "κτιρι", "κτηρι", "γεωτεμαχ", "κτηματολ", "κτηματογραφ", r"\bκαεκ\b", "αγροτεμαχ", r"\bοσδε\b",
        r"\blpis\b", "administrative", "boundar", "municipalit", "address", "building", "cadastr",
        "parcel", "gazetteer", "place names",
    ],
    # Statistics listed in the Annex: industry, trade, tourism, prices, national and government
    # accounts, environmental accounts, population, health expenditure, poverty, labour market.
    "c_e1da4e07": [
        "βιομηχανικη παραγωγ", "δεικτης βιομηχανικ", "prodcom", "τιμων παραγωγου",
        "λιανικ(ο|ου) εμποριο", "κυκλου εργασιων", "εμποριο αγαθων", "διεθνες εμποριο",
        "εξωτερικο εμποριο", "αφιξ", "διανυκτερευσ", "τουριστικη κινηση", "τιμων καταναλωτη",
        "εναρμονισμεν", "εθνικοι λογαριασμ", r"\bαεπ\b", "ακαθαριστο εγχωριο",
        "περιφερειακοι λογαριασμ", "δημοσιονομ", "δημοσιο χρεος", "ελλειμμ", "γενικης κυβερνησης",
        "περιβαλλοντικ(οι|ων|ους) λογαριασμ", "λογαριασμοι εκπομπων", "στατιστικες αποβλητων",
        "πληθυσμ", "γεννησ", "γονιμοτ", "θνησιμ", r"θανατοι\b", r"θανατων\b", "δαπανες υγει",
        "υγειονομικης περιθαλψης", "φτωχει", "ανισοτ", "συνθηκες διαβιωσης", "απασχολ", "ανεργ",
        "εργατικο δυναμικ", "population", "census", r"\bgdp\b", "unemployment", "employment",
        "poverty", "inflation", "consumer price", "tourism", "trade in goods", "industrial production",
    ],
    # Transport networks (road, rail, water, air, cycle) and inland waterways.
    "c_b79e35eb": [
        "οδικο δικτυο", "οδικου δικτυου", "δικτυο οδων", "σιδηροδρομ", "λιμαν", "λιμεν(?!ικ)",
        "αεροδρομ", "αερολιμ", "ποδηλατοδρομ", "δικτυο ποδηλατ", "γεφυρ", "σηραγγ", "πορθμ",
        "ακτοπλοι", "road network", "railway", "airport", r"\bports?\b", "transport network",
        "cycle (lane|path)", "bike lane",
    ],
    # INSPIRE themes of the Annex (hydrography, protected sites, elevation, geology, land cover
    # and use, orthoimagery, habitats, species, energy and mineral resources, natural risk zones,
    # sea, soil) and the environmental domains (air, climate, emissions, noise, waste, water).
    "c_dd313021": [
        "υδρογραφ", "ποταμ", "λιμν", "υδατικ", "λεκαν(ες|η) απορροης", r"\bρεμα", "προστατευομεν",
        "natura", "δρυμ", "υψομετρ", "ψηφιακο μοντελο εδαφους", "ισουψ", "γεωλογ", "σεισμ", "ρηγμ",
        "καλυψη γης", "corine", "ορθοφωτ", "δορυφορικ", "αεροφωτογραφ", r"\buav\b", "drone",
        "οικοτοπ", "ενδιαιτημ", "χλωριδ", "πανιδ", "βιοποικιλ", "κατανομη ειδων",
        "ενεργειακ(οι|ων) πορ", "γεωθερμ", "αιολικ", "φωτοβολταικ", "ανανεωσιμ", r"\bαπε\b",
        "χρησεις γης", "χρηση γης", "ορια οικισμ", "πολεοδομ", "ρυμοτομ", "ορυκτ", "λατομ",
        "μεταλλει", "πλημμυρ", "κατολισθ", "διαβρωσ", "πυρκαγι", "θαλασσ", "ακτογραμμ", "αιγιαλ",
        "εδαφ", "ποιοτητα (του )?αερα", "ατμοσφαιρ", "ρυπανσ", "ρυπων", "ρυποι", "κλιματικ",
        "εκπομπ", "θορυβ", "ηχορυπ", "αποβλητ", "απορριμ", "ανακυκλ", "υδατ", r"\bνερ(ο|ου|α)\b",
        "ποσιμ", "κολυμβ", "λυματ", "land cover", "land use", "hydro", "river", "protected",
        "elevation", "geolog", "soil", "orthophoto", "satellite", "air quality", "noise", "waste",
        "water", "emission", "habitat", "species",
    ],
    # Observations of weather stations, validated climate observations, weather alerts, radar
    # data, numerical weather prediction data.
    "c_164e0bf5": [
        "μετεωρολογ", r"\bκαιρ", "θερμοκρασ", "βροχ", r"\bυετ", "ανεμ", "κλιματ", "ρανταρ", "υγρασ",
        "χιον", "ηλιοφαν", "προγνωσ", "weather", "meteo", "temperature", "rainfall", "precipitation",
        r"\bwind\b", "sunshine", "climate", "radar", "forecast",
    ],
    # Basic company information; company documents and accounts.
    "c_a9135398": [
        "γεμη", "εμπορικο μητρωο", "μητρωο (επιχειρησ|εταιρ)", "ανωνυμων εταιρ",
        "αναζητηση επιχειρησ", "εγγραφες επιχειρησ", "business", "compan", "stirdata",
    ],
}

# Columns of the working table that hold numbers or True/False values.
INT_COLUMNS = ["views_total", "views_recent", "resource_views_total", "n_resources"]
BOOL_COLUMNS = ["is_hvd", "machine_readable", "license_any"]

# Columns of sample.csv and sample_reserves.csv.
OUTPUT_COLUMNS = [
    "sample_id", "group", "category_code", "category", "position", "hvd_basis", "annex_item",
    "id", "name", "title", "organization", "organization_title", "url", "views_total",
    "views_recent", "downloads", "n_resources", "formats", "machine_readable", "license_any",
    "mqa_max", "snapshot_date", "selection_reason",
]

CONTENT_COLUMNS = ["name", "hvd_category", "counts_as_hvd", "annex_item", "reason"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fold(text) -> str:
    """Lower case without accents, so that "Καλλικρατικοί" and "ΚΑΛΛΙΚΡΑΤΙΚΟΙ" compare equal."""
    decomposed = unicodedata.normalize("NFD", str(text).lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def fmt_int(n) -> str:
    """Number with a thousands separator."""
    return f"{int(n):,}"


def newest_flat() -> Path:
    candidates = sorted(PROCESSED_DIR.glob("catalog_flat_*.csv"))
    if not candidates:
        raise SystemExit("No working table found in data/processed. Run 02_catalog_profile.py first.")
    return candidates[-1]


def snapshot_date(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if not match:
        raise SystemExit(f"The file name {path.name} does not contain a date (YYYY-MM-DD).")
    return match.group(1)


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read_csv_text(path: Path) -> pd.DataFrame:
    """Reads a CSV file as text. Files saved by Excel without the "CSV UTF-8" option are
    stored in the Windows Greek encoding and are read with it."""
    try:
        return pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    except UnicodeDecodeError:
        print(f"Note: {relative(path)} is not in UTF-8; it is read as Windows-1253. "
              "Saving it as \"CSV UTF-8\" is recommended.")
        return pd.read_csv(path, encoding="cp1253", dtype=str, keep_default_na=False)


def load_flat(path: Path) -> pd.DataFrame:
    frame = read_csv_text(path)
    missing = [c for c in ["id", "name", "title", "organization", "hvd_categories"] + INT_COLUMNS
               + BOOL_COLUMNS if c not in frame.columns]
    if missing:
        raise SystemExit(f"{relative(path)} lacks the columns {missing}. Run 02_catalog_profile.py again.")
    for column in INT_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
    for column in BOOL_COLUMNS:
        frame[column] = frame[column].str.strip().str.lower() == "true"
    frame["folded_title"] = frame["title"].map(fold)
    frame["category_set"] = frame["hvd_categories"].map(lambda v: {c for c in v.split(";") if c})
    return frame


def load_decisions(path: Path, known_names: set[str]) -> dict[tuple[str, str], dict]:
    """Manual decisions on high-value content: {(name, category code): row}."""
    if not path.exists():
        return {}
    frame = read_csv_text(path)
    missing = [c for c in CONTENT_COLUMNS if c not in frame.columns]
    if missing:
        raise SystemExit(f"{relative(path)} lacks the columns {missing}.")
    codes = {code for code, _, _ in QUOTAS}
    decisions: dict[tuple[str, str], dict] = {}
    problems = []
    for number, row in enumerate(frame.to_dict("records"), start=2):
        name, code = row["name"].strip(), row["hvd_category"].strip()
        answer = row["counts_as_hvd"].strip().lower()
        if code not in codes:
            problems.append(f"line {number}: unknown category code '{code}'")
        if answer not in ("yes", "no"):
            problems.append(f"line {number}: counts_as_hvd must be yes or no, not '{row['counts_as_hvd']}'")
        if (name, code) in decisions:
            problems.append(f"line {number}: second decision for {name} in {code}")
        if name not in known_names:
            print(f"Note: {relative(path)}, line {number}: {name} is not in the working table "
                  "(removed from the portal or without resources); the line is ignored.")
        decisions[(name, code)] = {**row, "name": name, "hvd_category": code, "counts_as_hvd": answer}
    if problems:
        raise SystemExit(f"Errors in {relative(path)}:\n  " + "\n  ".join(problems))
    return decisions


def blocked_by_limit(organization: str, views: int, picked_views: dict[str, list[int]]) -> bool:
    """True if the organisation already has the maximum number of datasets in the category,
    all with at least as many page views."""
    if not MAX_PER_ORGANIZATION:
        return False
    views_of_org = picked_views.get(organization, [])
    return len(views_of_org) >= MAX_PER_ORGANIZATION and min(views_of_org) >= views


# ---------------------------------------------------------------------------
# High-value group
# ---------------------------------------------------------------------------

def category_pool(eligible: pd.DataFrame, code: str, decisions: dict) -> pd.DataFrame:
    """Eligible datasets of a category, ranked: declared by the publisher or counted by content."""
    declared = eligible["category_set"].map(lambda s: code in s)
    by_content = eligible["name"].map(
        lambda n: decisions.get((n, code), {}).get("counts_as_hvd") == "yes"
    )
    pool = eligible[declared | by_content].copy()
    pool["hvd_basis"] = np.where(declared[declared | by_content], "declared", "content")
    return pool


def select_high_value(eligible: pd.DataFrame, decisions: dict):
    """Returns the selected datasets, the reserves, the screened datasets and per-category counts."""
    taken: set[str] = set()
    picks: dict[str, list[dict]] = {}
    stats: dict[str, dict] = {}

    # First pass: the datasets of the sample, category by category.
    for code, label, quota in QUOTAS:
        pool = category_pool(eligible, code, decisions)
        available = pool[~pool["id"].isin(taken)]
        stats[code] = {"datasets": len(available), "organizations": available["organization"].nunique()}
        chosen: list[dict] = []
        counts: dict[str, int] = {}
        for row in available.to_dict("records"):
            if len(chosen) == quota:
                break
            organization = row["organization"]
            if MAX_PER_ORGANIZATION and counts.get(organization, 0) >= MAX_PER_ORGANIZATION:
                continue
            counts[organization] = counts.get(organization, 0) + 1
            chosen.append(row)
            taken.add(row["id"])
        picks[code] = chosen

    # Second pass: reserves, from the datasets not selected in any category.
    reserves: dict[str, list[dict]] = {}
    for code, label, quota in QUOTAS:
        pool = category_pool(eligible, code, decisions)
        counts = {}
        for row in picks[code]:
            counts[row["organization"]] = counts.get(row["organization"], 0) + 1
        chosen = []
        for row in pool[~pool["id"].isin(taken)].to_dict("records"):
            if len(chosen) == CATEGORY_RESERVES:
                break
            organization = row["organization"]
            if MAX_PER_ORGANIZATION and counts.get(organization, 0) >= MAX_PER_ORGANIZATION:
                continue
            counts[organization] = counts.get(organization, 0) + 1
            chosen.append(row)
        reserves[code] = chosen

    # Screening: datasets that could enter a category if their content corresponds to the Annex.
    screened: list[dict] = []
    for code, label, quota in QUOTAS:
        chosen = picks[code]
        threshold = chosen[-1]["views_total"] if len(chosen) == quota else 0
        chosen_ids = {row["id"] for row in chosen}
        picked_views: dict[str, list[int]] = {}
        for row in chosen:
            picked_views.setdefault(row["organization"], []).append(row["views_total"])
        pattern = re.compile("|".join(SCREEN_TERMS[code]))
        candidates = eligible[
            ~eligible["category_set"].map(lambda s: code in s)
            & (eligible["views_total"] >= threshold)
            & eligible["folded_title"].map(lambda t: pattern.search(t) is not None)
        ]
        for row in candidates.to_dict("records"):
            selected_here = row["id"] in chosen_ids
            if row["id"] in taken and not selected_here:
                continue  # already selected in an earlier category
            if not selected_here and blocked_by_limit(row["organization"], row["views_total"], picked_views):
                continue  # the organisation already has a more viewed dataset in the category
            decision = decisions.get((row["name"], code), {})
            screened.append({
                "context": "category ranking",
                "category_code": code,
                "category": label,
                "name": row["name"],
                "title": row["title"],
                "organization_title": row["organization_title"],
                "views_total": row["views_total"],
                "declared_categories": row["hvd_categories"],
                "decision": decision.get("counts_as_hvd", "pending"),
                "annex_item": decision.get("annex_item", ""),
                "reason": decision.get("reason", ""),
                "selected": "yes" if selected_here else "no",
            })
    return picks, reserves, screened, stats


# ---------------------------------------------------------------------------
# Comparison group
# ---------------------------------------------------------------------------

def draw_comparison(eligible: pd.DataFrame, decisions: dict) -> tuple[list[dict], int, list[dict]]:
    """Random draw from the datasets that are high-value in neither way.

    The random order is computed once on the datasets without any high-value flag, sorted by id.
    The datasets are then taken in that order; a dataset counted as high-value by content is
    skipped, so that a new decision changes only the place of that dataset and not the rest of
    the draw. A dataset whose title suggests Annex content needs a decision before it is used."""
    pool = eligible[~eligible["is_hvd"]].sort_values("id").reset_index(drop=True)
    order = np.random.RandomState(RANDOM_SEED).permutation(len(pool))
    patterns = {code: re.compile("|".join(SCREEN_TERMS[code])) for code, _, _ in QUOTAS}
    labels = {code: label for code, label, _ in QUOTAS}
    content_yes = {name for (name, _), d in decisions.items() if d["counts_as_hvd"] == "yes"}

    accepted: list[dict] = []
    screened: list[dict] = []
    for index in order:
        if len(accepted) == RANDOM_SIZE + RANDOM_RESERVES:
            break
        row = pool.iloc[index].to_dict()
        matched = [code for code, pattern in patterns.items() if pattern.search(row["folded_title"])]
        skipped = row["name"] in content_yes
        for code in matched:
            decision = decisions.get((row["name"], code), {})
            screened.append({
                "context": "comparison draw",
                "category_code": code,
                "category": labels[code],
                "name": row["name"],
                "title": row["title"],
                "organization_title": row["organization_title"],
                "views_total": row["views_total"],
                "declared_categories": row["hvd_categories"],
                "decision": decision.get("counts_as_hvd", "pending"),
                "annex_item": decision.get("annex_item", ""),
                "reason": decision.get("reason", ""),
                "selected": "no" if skipped else ("yes" if len(accepted) < RANDOM_SIZE else "reserve"),
            })
        if not skipped:
            accepted.append(row)
    return accepted, len(pool), screened


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def output_row(row: dict, sample_id: str, group: str, code: str, label: str, position: int,
               basis: str, annex_item: str, date: str, reason: str) -> dict:
    return {
        "sample_id": sample_id,
        "group": group,
        "category_code": code,
        "category": label,
        "position": position,
        "hvd_basis": basis,
        "annex_item": annex_item,
        "id": row["id"],
        "name": row["name"],
        "title": row["title"],
        "organization": row["organization"],
        "organization_title": row["organization_title"],
        "url": DATASET_URL + row["name"],
        "views_total": row["views_total"],
        "views_recent": row["views_recent"],
        "downloads": row["resource_views_total"],
        "n_resources": row["n_resources"],
        "formats": row["formats"],
        "machine_readable": row["machine_readable"],
        "license_any": row["license_any"],
        "mqa_max": row["mqa_max"],
        "snapshot_date": date,
        "selection_reason": reason,
    }


def build_rows(picks, reserves, drawn, pool_size, decisions, stats, date):
    sample_rows, reserve_rows = [], []
    number = 0
    for code, label, quota in QUOTAS:
        for position, row in enumerate(picks[code], start=1):
            number += 1
            basis = row["hvd_basis"]
            annex_item = decisions.get((row["name"], code), {}).get("annex_item", "") if basis == "content" else ""
            source = ("category declared by the publisher" if basis == "declared"
                      else f"content corresponds to the Annex item '{annex_item}'")
            reason = (f"{label}, position {position} of {stats[code]['organizations']} organisations: "
                      f"most viewed dataset of its organisation ({fmt_int(row['views_total'])} page views); {source}.")
            sample_rows.append(output_row(row, f"S{number:02d}", "high-value", code, label, position,
                                          basis, annex_item, date, reason))
    for position, row in enumerate(drawn[:RANDOM_SIZE], start=1):
        number += 1
        reason = (f"Random draw {position} of {RANDOM_SIZE} (seed {RANDOM_SEED}) from "
                  f"{fmt_int(pool_size)} datasets without a high-value flag; datasets counted "
                  "as high-value by content are skipped.")
        sample_rows.append(output_row(row, f"S{number:02d}", "comparison", "", "", position,
                                      "", "", date, reason))

    number = 0
    for code, label, quota in QUOTAS:
        for offset, row in enumerate(reserves[code], start=1):
            number += 1
            basis = row["hvd_basis"]
            annex_item = decisions.get((row["name"], code), {}).get("annex_item", "") if basis == "content" else ""
            reason = (f"Reserve {offset} for {label}: next in the same ranking "
                      f"({fmt_int(row['views_total'])} page views).")
            reserve_rows.append(output_row(row, f"R{number:02d}", "high-value", code, label,
                                           quota + offset, basis, annex_item, date, reason))
    for offset, row in enumerate(drawn[RANDOM_SIZE:], start=1):
        number += 1
        reason = f"Reserve {offset} for the comparison group: next in the same random order."
        reserve_rows.append(output_row(row, f"R{number:02d}", "comparison", "", "",
                                       RANDOM_SIZE + offset, "", "", date, reason))
    return sample_rows, reserve_rows


def md_cell(text) -> str:
    """Text safe for a cell of a Markdown table."""
    return str(text).replace("|", "/").replace("\n", " ").strip()


def link(row: dict) -> str:
    title = md_cell(row["title"]).replace("[", "(").replace("]", ")")
    return f"[{title}]({row['url']})"


def build_summary(sample_rows, reserve_rows, screened, stats, pool_size, date, flat_name) -> str:
    high = [r for r in sample_rows if r["group"] == "high-value"]
    comparison = [r for r in sample_rows if r["group"] == "comparison"]
    examined = {(s["name"], s["category_code"]): s["decision"] for s in screened}
    yes = sum(1 for d in examined.values() if d == "yes")
    no = sum(1 for d in examined.values() if d == "no")
    lines = [
        f"# Assessment sample, version {SAMPLE_VERSION}",
        "",
        f"- Snapshot of {date}; working table `data/processed/{flat_name}`.",
        "- Rules: DECISIONS.md #2, #8, #17 and #18.",
        f"- High-value group: {len(high)} datasets. In each category the datasets are ranked by "
        "page views and the most viewed dataset of each organisation is selected.",
        f"- Comparison group: {len(comparison)} datasets, random draw (seed {RANDOM_SEED}) from "
        f"{fmt_int(pool_size)} datasets without a high-value flag; datasets counted as high-value "
        "by content are skipped.",
        "",
        "## High-value datasets",
    ]
    for code, label, quota in QUOTAS:
        rows = [r for r in high if r["category_code"] == code]
        lines += [
            "",
            f"### {label}: {len(rows)} of {fmt_int(stats[code]['datasets'])} eligible datasets "
            f"from {fmt_int(stats[code]['organizations'])} organisations",
            "",
            "| ID | Dataset | Organisation | Page views | Basis |",
            "| --- | --- | --- | ---: | --- |",
        ]
        for r in rows:
            basis = "declared" if r["hvd_basis"] == "declared" else f"content: {r['annex_item']}"
            lines.append(f"| {r['sample_id']} | {link(r)} | {md_cell(r['organization_title'])} | "
                         f"{fmt_int(r['views_total'])} | {basis} |")
    lines += [
        "",
        "## Comparison group",
        "",
        "| ID | Dataset | Organisation | Page views |",
        "| --- | --- | --- | ---: |",
    ]
    for r in comparison:
        lines.append(f"| {r['sample_id']} | {link(r)} | {md_cell(r['organization_title'])} | "
                     f"{fmt_int(r['views_total'])} |")
    lines += [
        "",
        "## Reserves",
        "",
        "| ID | For | Dataset | Organisation | Page views |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for r in reserve_rows:
        target = r["category"] or "Comparison group"
        lines.append(f"| {r['sample_id']} | {target} | {link(r)} | {md_cell(r['organization_title'])} | "
                     f"{fmt_int(r['views_total'])} |")
    lines += [
        "",
        "## Content screening",
        "",
        f"- Decisions on content corresponding to the Annex used in this draw: {len(examined)}; "
        f"counted as high-value: {yes}; not counted: {no}.",
        "- Decisions and reasons: `criteria/hvd_by_content.csv`; list of this run: `screening.csv`.",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Selection of the 36 datasets of the assessment sample.")
    parser.add_argument("--flat", type=Path, default=None,
                        help="Working table (catalog_flat_YYYY-MM-DD.csv). Default: the newest one.")
    parser.add_argument("--force", action="store_true",
                        help="Draws the sample again even if data/processed/sample.csv exists.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if SAMPLE_FILE.exists() and not args.force:
        print(f"{relative(SAMPLE_FILE)} already exists: the sample is drawn once.")
        print("A new draw requires --force and an entry in DECISIONS.md with the reason.")
        return 1

    flat = args.flat or newest_flat()
    date = snapshot_date(flat)
    print(f"Working table: {relative(flat)}")
    frame = load_flat(flat)
    eligible = frame[frame["n_resources"] > 0].sort_values(RANK_COLUMNS, ascending=RANK_ASCENDING)
    print(f"Datasets: {fmt_int(len(frame))}; eligible (with at least one resource): {fmt_int(len(eligible))}")

    decisions = load_decisions(CONTENT_FILE, set(eligible["name"]))
    print(f"Content decisions in {relative(CONTENT_FILE)}: {len(decisions)}")

    picks, reserves, screened, stats = select_high_value(eligible, decisions)
    drawn, pool_size, screened_draw = draw_comparison(eligible, decisions)
    screened += screened_draw

    out_dir = OUT_DIR / f"sample_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    screening_file = out_dir / "screening.csv"
    pd.DataFrame(screened, columns=[
        "context", "category_code", "category", "name", "title", "organization_title", "views_total",
        "declared_categories", "decision", "annex_item", "reason", "selected",
    ]).to_csv(screening_file, index=False, encoding="utf-8-sig")

    pending = [s for s in screened if s["decision"] == "pending"]
    if pending:
        print()
        print(f"Decisions are needed for {len(pending)} datasets whose title suggests content of the Annex:")
        for s in pending:
            print(f"  {s['category']} ({s['context']}): {s['name']} "
                  f"({fmt_int(s['views_total'])} page views), {s['title'][:70]}")
        print()
        print(f"Each one is added to {relative(CONTENT_FILE)} with counts_as_hvd = yes or no, the Annex item")
        print("and the reason. The sample is drawn once all decisions are recorded.")
        print(f"List of this run: {relative(screening_file)}")
        return 1

    sample_rows, reserve_rows = build_rows(picks, reserves, drawn, pool_size, decisions, stats, date)

    expected = sum(q for _, _, q in QUOTAS) + RANDOM_SIZE
    if len(sample_rows) != expected:
        print(f"Warning: the sample has {len(sample_rows)} datasets instead of {expected}.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sample_rows, columns=OUTPUT_COLUMNS).to_csv(SAMPLE_FILE, index=False, encoding="utf-8-sig")
    pd.DataFrame(reserve_rows, columns=OUTPUT_COLUMNS).to_csv(RESERVES_FILE, index=False, encoding="utf-8-sig")
    text = build_summary(sample_rows, reserve_rows, screened, stats, pool_size, date, flat.name)
    (out_dir / "summary.md").write_text(text, encoding="utf-8")

    print()
    print(text)
    print("Files:")
    print(f"  {relative(SAMPLE_FILE)}  ({len(sample_rows)} datasets)")
    print(f"  {relative(RESERVES_FILE)}  ({len(reserve_rows)} reserves)")
    print(f"  {relative(out_dir)}\\  (summary.md, screening.csv)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
