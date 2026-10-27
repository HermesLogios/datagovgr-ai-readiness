r"""
02_catalog_profile.py
Phase 1: profile of the catalogue from one snapshot.

What it does, in order:
  1. Reads the newest snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz) or the one given
     with --snapshot.
  2. For every dataset (type = dataset) builds one row with its main characteristics:
     organisation, theme, high-value dataset (HVD) flags, licences, file formats,
     machine readability, usage statistics, link status, the portal's MQA score.
     The rows are saved to data/processed/catalog_flat_YYYY-MM-DD.csv, the working table
     used for sample selection and for the later checks.
  3. From that table it produces summary tables and a plain-language summary in
     outputs/profile_YYYY-MM-DD/:
        summary.md            summary of the main figures (also printed to the console)
        summary.json          the same figures in machine-readable form
        by_organization.csv   datasets per organisation
        by_license.csv        licences at dataset level and at resource level
        by_format.csv         file formats
        by_theme.csv          data themes
        by_hvd_category.csv   high-value dataset categories
        by_year.csv           datasets per year of registration
        top_viewed.csv        the 50 datasets with the most page views

Method notes:
  - The automatic "download all" ZIP bundles that the portal generates for every dataset
    are excluded from the format, machine-readability and link counts, so that only the
    files uploaded by the organisation are measured.
  - A dataset counts as machine-readable if at least one of its resources has a format in
    the MACHINE_READABLE list. PDF, Word documents, images and archives do not count.
  - Link status and the MQA score come from the portal's own qa and archiver plugins
    (CKAN) and are verified independently on the sample in a later phase.

Usage (from the project root, with the .venv activated):
    python scripts\02_catalog_profile.py
    python scripts\02_catalog_profile.py --snapshot data\raw\catalog_2026-10-24.jsonl.gz

Code licence: EUPL-1.2
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
# Settings and vocabularies
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"

HVD_TYPE = "http://publications.europa.eu/resource/authority/dataset-type/HVD"

# The six high-value dataset categories of Implementing Regulation (EU) 2023/138, with
# their codes in the EU vocabulary (http://data.europa.eu/bna/...).
HVD_CATEGORIES = {
    "c_ac64a52d": "Geospatial",
    "c_dd313021": "Earth observation and environment",
    "c_164e0bf5": "Meteorological",
    "c_e1da4e07": "Statistics",
    "c_a9135398": "Companies and company ownership",
    "c_b79e35eb": "Mobility",
}

# Data themes of the EU data-theme vocabulary.
THEMES = {
    "AGRI": "Agriculture, fisheries, forestry and food",
    "ECON": "Economy and finance",
    "EDUC": "Education, culture and sport",
    "ENER": "Energy",
    "ENVI": "Environment",
    "GOVE": "Government and public sector",
    "HEAL": "Health",
    "INTR": "International issues",
    "JUST": "Justice, legal system and public safety",
    "REGI": "Regions and cities",
    "SOCI": "Population and society",
    "TECH": "Science and technology",
    "TRAN": "Transport",
    "OP_DATPRO": "Provisional data",
}

# Formats that a program can read directly (structured data or geospatial services).
MACHINE_READABLE = {
    "CSV", "TSV", "JSON", "GEOJSON", "JSONLD", "JSON-LD", "XML", "RDF", "TTL", "N3", "NT",
    "XLS", "XLSX", "ODS", "PARQUET", "SDMX", "SDMX-ML", "NETCDF", "NC", "GRIB", "HDF5",
    "SHP", "SHAPE-ZIP", "SHAPEFILE", "KML", "KMZ", "GML", "GPKG", "GEOTIFF", "WMS", "WFS",
    "WCS", "WMTS", "OGC API", "API", "REST", "SQLITE", "SQL", "ICS", "GTFS", "ATOM", "RSS",
}

# Values meaning that no licence is declared at dataset level.
NO_LICENSE = {None, "", "notspecified"}

# Words in a licence identifier that indicate an open licence suitable for high-value
# datasets (CC0, CC BY 4.0) or generally open (CC BY, ODC-BY, PDDL, ODbL, "other-open", "other-pd").
OPEN_LICENSE_HINTS = ("cc0", "cc_by_4", "cc-by-4", "cc-by", "cc_by", "odc-by", "odc_by", "pddl", "odbl", "other-open", "other-pd")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def as_list(value) -> list:
    """Always returns a list: CKAN multi-value fields arrive sometimes as a list,
    sometimes as JSON text and sometimes as plain text."""
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
    """The last part of a vocabulary URI, e.g. .../data-theme/SOCI -> SOCI."""
    return str(uri).rstrip("/").rsplit("/", 1)[-1]


def is_bundle(resource: dict) -> bool:
    """The automatic "download all" ZIP bundle generated by the portal."""
    return bool(resource.get("downloadall_datapackage_hash"))


def norm_format(resource: dict) -> str:
    """A resource's format in upper case, without spaces; empty if not declared."""
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
    """Number with a thousands separator."""
    return f"{int(n):,}"


def fmt_pct(part, whole) -> str:
    if not whole:
        return "n/a"
    return f"{100 * part / whole:.1f}%"


def newest_snapshot() -> Path:
    candidates = sorted(
        p for p in RAW_DIR.glob("catalog_*.jsonl.gz") if "_test" not in p.name
    )
    if not candidates:
        raise SystemExit("No snapshot found in data/raw. Run 01_snapshot.py first.")
    return candidates[-1]


def snapshot_date(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else dt.date.today().isoformat()


# ---------------------------------------------------------------------------
# One row per dataset
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
# Summary tables
# ---------------------------------------------------------------------------

def explode_counts(frame: pd.DataFrame, column: str) -> Counter:
    """Counts datasets per value in a column of ";"-separated values (a dataset counts once per value)."""
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

    lic_ds = frame["license_id"].replace("", "(none)").value_counts().rename_axis("license").reset_index(name="datasets")
    lic_ds.insert(0, "level", "dataset")
    lic_res = pd.Series(explode_counts(frame, "resource_licenses")).rename_axis("license").reset_index(name="datasets")
    lic_res.insert(0, "level", "resource")
    tables["by_license"] = pd.concat([lic_ds, lic_res], ignore_index=True)

    fmt = pd.Series(explode_counts(frame, "formats")).rename_axis("format").reset_index(name="datasets")
    fmt["machine_readable"] = fmt["format"].isin(MACHINE_READABLE)
    fmt["share"] = (fmt["datasets"] / n).round(4)
    tables["by_format"] = fmt.sort_values("datasets", ascending=False)

    theme = pd.Series(explode_counts(frame, "themes")).rename_axis("theme").reset_index(name="datasets")
    theme["label"] = theme["theme"].map(THEMES).fillna("(other)")
    theme["share"] = (theme["datasets"] / n).round(4)
    tables["by_theme"] = theme.sort_values("datasets", ascending=False)

    hvd = pd.Series(explode_counts(frame, "hvd_categories")).rename_axis("category").reset_index(name="datasets")
    hvd["label"] = hvd["category"].map(HVD_CATEGORIES).fillna("(other or sub-category)")
    tables["by_hvd_category"] = hvd.sort_values("datasets", ascending=False)

    year = frame["year_created"].value_counts().sort_index().rename_axis("year").reset_index(name="datasets")
    tables["by_year"] = year

    top = frame.sort_values("views_total", ascending=False).head(50)[
        ["name", "title", "organization_title", "views_total", "views_recent", "is_hvd", "hvd_categories", "formats"]
    ]
    tables["top_viewed"] = top
    return tables


# ---------------------------------------------------------------------------
# Plain-language summary
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
        f"# data.gov.gr catalogue profile: snapshot of {date}",
        "",
        f"Source: {source}. All percentages refer to the {fmt_int(n)} datasets.",
        "",
        "## Size",
        f"- Records in total: {fmt_int(summary['records_total'])} "
        f"(datasets {fmt_int(counts_by_type.get('dataset', 0))}, "
        f"data services {fmt_int(counts_by_type.get('data-service', 0))}, "
        f"data availability decisions {fmt_int(counts_by_type.get('decision', 0))}).",
        f"- Organisations with at least one dataset: {fmt_int(summary['organizations'])}.",
        "",
        "## High-value datasets (HVD)",
        f"- With any HVD flag: {fmt_int(hvd_any)} ({fmt_pct(hvd_any, n)}).",
        f"- With the HVD type: {fmt_int(hvd_type)}; with an HVD category: {fmt_int(hvd_cat)}; "
        f"with a reference to Regulation 2023/138: {fmt_int(hvd_leg)}; with all three: {fmt_int(summary['hvd_all_three_flags'])}.",
    ]
    for _, row in tables["by_hvd_category"].iterrows():
        lines.append(f"  - {row['label']}: {fmt_int(row['datasets'])}")
    lines += [
        "",
        "## Licences",
        f"- Licence declared at dataset level: {fmt_int(summary['license_dataset_level'])} ({fmt_pct(summary['license_dataset_level'], n)}).",
        f"- Licence declared at dataset or resource level: {fmt_int(summary['license_any_level'])} ({fmt_pct(summary['license_any_level'], n)}).",
        f"- No licence at all: {fmt_int(summary['license_none'])} ({fmt_pct(summary['license_none'], n)}).",
        f"- Open licence (CC0, CC BY, ODC, public domain): {fmt_int(summary['license_open'])} ({fmt_pct(summary['license_open'], n)}).",
        "",
        "## File formats",
        f"- With at least one machine-readable resource: {fmt_int(summary['machine_readable'])} ({fmt_pct(summary['machine_readable'], n)}).",
        f"- Without any machine-readable format: {fmt_int(summary['not_machine_readable'])} ({fmt_pct(summary['not_machine_readable'], n)}), "
        f"of which without any resource: {fmt_int(summary['without_resources'])}.",
        "- Most frequent formats (datasets containing them; a dataset may have several):",
    ]
    for _, row in tables["by_format"].head(10).iterrows():
        lines.append(f"  - {row['format']}: {fmt_int(row['datasets'])} ({fmt_pct(row['datasets'], n)})")
    lines += [
        "",
        "## Links and metadata quality according to the portal",
        f"- Resources checked by the portal's link checker: {fmt_int(checked)}; not accessible: {fmt_int(broken)} ({fmt_pct(broken, checked)}).",
        f"- Datasets with at least one inaccessible resource: {fmt_int(summary['datasets_with_broken'])} ({fmt_pct(summary['datasets_with_broken'], n)}).",
        f"- Median MQA score (0-100): {summary['mqa_median'] if summary['mqa_median'] is not None else 'n/a'}.",
        "",
        "## Completeness of basic metadata",
        f"- Description: {fmt_pct(summary['has_description'], n)}; keywords: {fmt_pct(summary['has_keywords'], n)}; "
        f"theme: {fmt_pct(summary['has_theme'], n)}; contact point: {fmt_pct(summary['has_contact'], n)}.",
        f"- Spatial coverage: {fmt_pct(summary['has_spatial'], n)}; temporal coverage: {fmt_pct(summary['has_temporal'], n)}; "
        f"update frequency: {fmt_pct(summary['has_frequency'], n)}.",
        "",
        "## Usage (page views on the portal)",
        f"- Median views per dataset: {summary['views_median']}; mean: {summary['views_mean']}; "
        f"with no views at all: {fmt_int(summary['views_zero'])} ({fmt_pct(summary['views_zero'], n)}).",
        "- The 10 datasets with the most views:",
    ]
    for _, row in tables["top_viewed"].head(10).iterrows():
        lines.append(f"  - {fmt_int(row['views_total'])}: {row['title'][:80]} ({row['organization_title']})")
    lines += ["", "## Data themes (a dataset may have several)"]
    for _, row in tables["by_theme"].head(8).iterrows():
        lines.append(f"- {row['label']} ({row['theme']}): {fmt_int(row['datasets'])} ({fmt_pct(row['datasets'], n)})")
    lines += ["", "## Organisations with the most datasets"]
    for _, row in tables["by_organization"].head(10).iterrows():
        lines.append(f"- {row['organization_title']}: {fmt_int(row['datasets'])} (HVD: {fmt_int(row['hvd_datasets'])})")
    lines += ["", "## Datasets per year of registration on the portal"]
    for _, row in tables["by_year"].iterrows():
        lines.append(f"- {row['year'] or '(unknown)'}: {fmt_int(row['datasets'])}")
    return summary, "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Profile of the catalogue from one snapshot.")
    parser.add_argument("--snapshot", type=Path, default=None, help="Snapshot file (.jsonl.gz). Default: the newest one.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    snapshot = args.snapshot or newest_snapshot()
    date = snapshot_date(snapshot)
    out_dir = OUT_DIR / f"profile_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Snapshot: {snapshot.relative_to(ROOT) if snapshot.is_relative_to(ROOT) else snapshot}")

    counts_by_type: Counter = Counter()
    rows = []
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            record_type = record.get("type") or "(no type)"
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
    print("Files:")
    print(f"  {flat_file.relative_to(ROOT)}  ({len(frame)} rows)")
    print(f"  {out_dir.relative_to(ROOT)}\\  (summary.md, summary.json and {len(tables)} CSV tables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
