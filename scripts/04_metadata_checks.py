r"""
04_metadata_checks.py
Phase 3: automated checks of the metadata, on the whole catalogue.

What it does, in order:
  1. Reads the catalogue snapshot (data/raw/catalog_YYYY-MM-DD.jsonl.gz, the newest one or the
     one given with --snapshot) and the sample (data/processed/sample.csv).
  2. Applies to every dataset the checks of the criteria that can be measured from the metadata.
     Each check records what it measured, a proposed score (0, 1 or 2) and the reason, following
     the rules of criteria/criteria.csv. The proposed scores of the 36 datasets of the sample are
     confirmed or corrected in the manual assessment; the scores of the rest of the catalogue are
     indicative and place the sample in the picture of the whole portal.
  3. Writes:
        data/processed/metadata_checks_YYYY-MM-DD.csv   one row per dataset: measurements, proposed
                                                         score and reason of every check
        outputs/checks_YYYY-MM-DD/summary.md            distribution of the proposed scores in the
                                                         catalogue, per check
        outputs/checks_YYYY-MM-DD/sample.md             the sample with links, proposed scores and
                                                         reasons, for the review of each dataset

Checks implemented so far:
  M1  Mandatory metadata (DCAT-AP): title, description, access URL of every resource.
  M2  Recommended metadata (DCAT-AP): keyword, theme, publisher, contact point, geographical
      coverage, temporal coverage, update frequency.
  M3  Controlled vocabularies: theme, update frequency and the format of every resource given
      with terms of the EU vocabularies (data-theme, frequency, file-type) or the IANA media types.
  M4  Licence: an open licence declared clearly for every resource.
  M7  Persistent identifier: a permanent identifier for the dataset and stable addresses for its
      resources.
  M9  High-value designation: the marking of a dataset as high-value in its metadata.
  The other checks of the metadata (M6, Q6 and the metadata part of Q5) are added one by one, as
  the rule of each criterion is approved.

Method notes:
  - The automatic "download all" ZIP bundle that the portal generates for every dataset is not a
    resource of the publisher and is ignored, as in 02_catalog_profile.py (DECISIONS.md #13).
  - M1. The description is measured as visible text: HTML tags are removed and runs of white
    space are collapsed. It "repeats the title" when the two are identical after lower-casing and
    removal of punctuation and extra spaces. A resource has an access URL when its url or
    access_url is filled, or when it is an active DataStore table of the portal, which the DCAT
    export of the portal publishes with an access URL and an access service. A dataset without
    resources is judged on its title and description only; the absence of resources is scored
    by Q1 (availability).
  - M2. A property is present when its field holds a value, whatever the value (DECISIONS.md #21):
    a broad or default geographical coverage, a temporal coverage from 1900 to 2099, a frequency
    "unknown" or "not planned" all count. A field that exists but whose entries are all empty
    (e.g. a publisher or contact point structure with every element blank) counts as absent.
    The publisher is the publisher field of the portal's metadata; the organisation that owns the
    dataset is not counted (DECISIONS.md #24), although the DCAT-AP export of the portal publishes
    it as the publisher when the field is absent (and publishes no publisher when the field is
    present but empty). The source of the publisher in the export is recorded separately, in the
    column m2_publisher_source: "field", "organisation" or "none".
  - M3. Only what is present is judged; a missing theme, frequency or format is scored by M2, not
    here. The theme and the frequency use a vocabulary when their values are URIs of the EU
    data-theme and frequency vocabularies (the portal's form offers them from these lists). A
    resource uses a vocabulary when its format, compared without regard to case and without a
    leading dot, is exactly a code or the English label of the EU file-type vocabulary
    (data/reference/eu_file_type.csv) or an IANA media type (type/subtype), or when its media type
    field holds an IANA media type (the portal's form offers the IANA list). No approximate
    matches: "SHAPE-ZIP", "shp zip", "TIF", "GZ" or "xl" are free text, since the vocabulary terms
    are SHP, TIFF, GZIP and XLS or XLSX (DECISIONS.md #25). A dataset with nothing to judge scores 0.
  - M4. The licence of a dataset is the licence of each of its resources: the licence field of the
    resource, which holds a term of the EU licence vocabulary, is shown on the page of the resource
    and is exported in DCAT-AP (DECISIONS.md #31). Licences are classed as permissive (CC0, CC BY of
    any version, ODC-BY, PDDL: CC BY 4.0 or an equivalent or less restrictive open licence),
    share-alike (CC BY-SA, ODbL, GFDL: open, but more restrictive than CC BY 4.0) or restrictive
    (non-commercial, no derivatives, closed). Every resource with the same permissive licence scores
    2; a restrictive licence on any resource scores 0; resources without a licence among licensed
    ones, different licences, or a share-alike licence score 1; a licence named only in the free
    text of the rights field, without a link, scores 1; no licence at all, or no resources, scores
    0. The generic dataset-level licence field of CKAN (license_id), which the current schema of the
    portal neither shows nor exports, does not count: most of its values come from the migration from
    the previous portal, the rest from automated publication. It is recorded in m4_dataset_field, and
    a contradiction with the licences of the resources is recorded in m4_dataset_field_conflict.
  - M7. The portal gives every dataset a permanent identifier (UUID) and a URI built on it
    (https://data.gov.gr/dataset/<uuid>), both exported in DCAT-AP (dct:identifier and the URI of
    the dataset), and every resource a URI of its own; a renamed dataset keeps them. The criterion
    is therefore decided by the addresses of the resources (DECISIONS.md #33). An address is stable
    when it is a file uploaded on the portal (.../resource/<id>/download/...), an active DataStore
    table of the portal, a request to a standard service (OGC WMS, WFS, WCS, CSW or OAI-PMH: the
    query parameters are the standard address of the service), or a plain address on another site,
    including a file on a third-party storage service (recorded, not penalised). An address changes
    when it depends on an opaque token, ticket or session parameter (e.g. ?fdl=...), on a URL
    shortener, or on a redirect through a search engine. Every resource with a stable address
    scores 2; a changing address or a missing address on any resource scores 1 (the dataset keeps
    its permanent address on the portal, also when every resource has a changing address); no
    address on any resource, or no resources, scores 0. Whether an address actually changes over
    time (a new address with every upload) is measured by comparing the snapshots of the two dates
    of the study, when the second snapshot is taken.
  - M9. Three fields mark a dataset as high-value: the high-value category (hvd_category, a term of
    the EU vocabulary of high-value categories), the applicable legislation (applicable_legislation,
    the ELI of Regulation (EU) 2023/138) and the dataset type HVD (dcat_type). Category and
    legislation together score 2; any of the three alone, or legislation with the type but without
    the category, scores 1; no marking scores 0. The criterion applies to the high-value datasets:
    in the sample, the 24 datasets of the high-value group (the comparison group is not applicable);
    in the catalogue, the scores 2 and 1 are counted over the marked datasets, while an unmarked
    dataset is reported as "not marked" and not as 0, since whether it is high-value by content
    cannot be judged automatically (DECISIONS.md #32). The marking is the declaration of the
    publisher, which the portal accepts without validation: whether the declared category is the
    right one, and whether a marked dataset belongs to the Annex of the Regulation at all, is judged
    by hand, in the compliance table of the high-value datasets (#28).

Usage (from the project root, with the .venv activated):
    python scripts\04_metadata_checks.py
    python scripts\04_metadata_checks.py --snapshot data\raw\catalog_2026-10-24.jsonl.gz

Code licence: EUPL-1.2
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pandas as pd

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs"
SAMPLE_FILE = PROCESSED_DIR / "sample.csv"
DATASET_URL = "https://data.gov.gr/dataset/"

MIN_DESCRIPTION_CHARS = 100     # M1: shortest description that counts as meaningful (criteria.csv)

# M2: the seven recommended properties, as (column key, name in the reports, field of the record).
M2_PROPERTIES = [
    ("keyword", "keyword", "tags"),
    ("theme", "theme", "theme"),
    ("publisher", "publisher", "publisher"),
    ("contact", "contact point", "contact"),
    ("spatial", "geographical coverage", "spatial_coverage"),
    ("temporal", "temporal coverage", "temporal_coverage"),
    ("frequency", "update frequency", "frequency"),
]
M2_SCORE_2 = 6      # six or seven properties present (criteria.csv)
M2_SCORE_1 = 3      # three to five

# M3: the vocabularies. The EU file-type vocabulary is kept as a reference file in the repository.
REFERENCE_DIR = ROOT / "data" / "reference"
FILE_TYPE_FILE = REFERENCE_DIR / "eu_file_type.csv"
DATA_THEME_PREFIX = "http://publications.europa.eu/resource/authority/data-theme/"
FREQUENCY_PREFIX = "http://publications.europa.eu/resource/authority/frequency/"
IANA_PREFIX = "https://www.iana.org/assignments/media-types/"
IANA_TOP_LEVEL_TYPES = {"application", "audio", "example", "font", "haptics", "image", "message",
                        "model", "multipart", "text", "video"}
MEDIA_TYPE = re.compile(r"([a-z]+)/([A-Za-z0-9][\w.+-]*)")
FILE_TYPES: dict[str, str] = {}      # upper-cased code or English label -> code; filled by load_file_types()

# M4: licences. Classes of the terms of the EU licence vocabulary (resource field) and of the
# licence identifiers of the dataset field of the previous portal schema.
LICENCE_PREFIX = "http://publications.europa.eu/resource/authority/licence/"
PERMISSIVE, SHARE_ALIKE, RESTRICTIVE = "permissive", "share-alike", "restrictive"
EU_LICENCE_CLASSES = {
    "CC0": PERMISSIVE, "CC_PDM": PERMISSIVE, "ODC_PDDL": PERMISSIVE, "ODC_BY": PERMISSIVE,
    "CC_BY": PERMISSIVE, "CC_BY_1_0": PERMISSIVE, "CC_BY_2_0": PERMISSIVE, "CC_BY_2_5": PERMISSIVE,
    "CC_BY_3_0": PERMISSIVE, "CC_BY_4_0": PERMISSIVE,
    "CC_BYSA": SHARE_ALIKE, "CC_BYSA_1_0": SHARE_ALIKE, "CC_BYSA_2_0": SHARE_ALIKE, "CC_BYSA_2_5": SHARE_ALIKE,
    "CC_BYSA_3_0": SHARE_ALIKE, "CC_BYSA_4_0": SHARE_ALIKE, "ODC_BL": SHARE_ALIKE, "GFDL": SHARE_ALIKE,
    "CC_BYNC": RESTRICTIVE, "CC_BYNC_1_0": RESTRICTIVE, "CC_BYNC_2_0": RESTRICTIVE, "CC_BYNC_2_5": RESTRICTIVE,
    "CC_BYNC_3_0": RESTRICTIVE, "CC_BYNC_4_0": RESTRICTIVE, "CC_BYND": RESTRICTIVE, "CC_BYND_1_0": RESTRICTIVE,
    "CC_BYND_2_0": RESTRICTIVE, "CC_BYND_2_5": RESTRICTIVE, "CC_BYND_3_0": RESTRICTIVE, "CC_BYND_4_0": RESTRICTIVE,
    "CC_BYNCND": RESTRICTIVE, "CC_BYNCND_1_0": RESTRICTIVE, "CC_BYNCND_2_0": RESTRICTIVE, "CC_BYNCND_2_5": RESTRICTIVE,
    "CC_BYNCND_3_0": RESTRICTIVE, "CC_BYNCND_4_0": RESTRICTIVE, "CC_BYNCSA": RESTRICTIVE, "CC_BYNCSA_1_0": RESTRICTIVE,
    "CC_BYNCSA_2_0": RESTRICTIVE, "CC_BYNCSA_2_5": RESTRICTIVE, "CC_BYNCSA_3_0": RESTRICTIVE, "CC_BYNCSA_4_0": RESTRICTIVE,
    "OGL_NC_2_0": RESTRICTIVE,
}
DATASET_FIELD_CLASSES = {          # license_id: the generic dataset-level field of CKAN, not shown by the portal
    "cc-zero": PERMISSIVE, "other-pd": PERMISSIVE, "odc-pddl": PERMISSIVE, "cc-by": PERMISSIVE,
    "odc-by": PERMISSIVE, "other-at": PERMISSIVE, "CC_BY_4_0": PERMISSIVE, LICENCE_PREFIX + "CC_BY_4_0": PERMISSIVE,
    "cc-by-sa": SHARE_ALIKE, "odc-odbl": SHARE_ALIKE, "gfdl": SHARE_ALIKE,
    "cc-nc": RESTRICTIVE, "other-nc": RESTRICTIVE, "other-closed": RESTRICTIVE,
    "other-open": "open-unspecified", "notspecified": "none", "": "none",
}
# Families, to detect a contradiction between the dataset field and the licences of the resources.
LICENCE_FAMILIES = {
    "cc-zero": "cc0", "CC0": "cc0", "other-pd": "cc0", "odc-pddl": "cc0", "ODC_PDDL": "cc0", "CC_PDM": "cc0",
    "cc-by": "cc-by", "other-at": "cc-by", "odc-by": "cc-by", "ODC_BY": "cc-by", "CC_BY": "cc-by",
    "CC_BY_1_0": "cc-by", "CC_BY_2_0": "cc-by", "CC_BY_2_5": "cc-by", "CC_BY_3_0": "cc-by", "CC_BY_4_0": "cc-by",
    LICENCE_PREFIX + "CC_BY_4_0": "cc-by",
    "cc-by-sa": "cc-by-sa", "CC_BYSA": "cc-by-sa", "CC_BYSA_1_0": "cc-by-sa", "CC_BYSA_4_0": "cc-by-sa",
    "odc-odbl": "odbl", "ODC_BL": "odbl", "gfdl": "gfdl", "GFDL": "gfdl",
    "cc-nc": "nc", "other-nc": "nc", "other-closed": "closed",
}

# M7: persistent identifiers. The portal gives every dataset and resource a permanent identifier
# and URI; the criterion is decided by the addresses of the resources (DECISIONS.md #33).
PORTAL_HOST = "data.gov.gr"
PORTAL_DOWNLOAD = re.compile(r"/resource/[0-9a-f-]{36}/download/")   # a file uploaded on the portal
SERVICE_PARAMETERS = ({"service", "request"}, {"verb"})   # OGC services (WMS, WFS, WCS, CSW); OAI-PMH
OPAQUE_PARAMETERS = {       # query parameters that carry a token, a ticket or a session, not an address
    "fdl", "fileticket", "ticket", "token", "access_token", "auth_token", "sessionid", "jsessionid",
    "phpsessid", "session", "sid", "expires", "signature", "sig", "x-amz-signature", "nonce", "ved",
}
URL_SHORTENERS = {"bit.ly", "goo.gl", "tinyurl.com", "t.ly", "1drv.ms", "shorturl.at", "cutt.ly", "is.gd", "rb.gy"}
SEARCH_ENGINES = {"google.com", "google.gr", "bing.com"}       # a redirect through .../url?q=...
THIRD_PARTY_STORAGE = ("drive.google.com", "docs.google.com", "dropbox.com", "onedrive.live.com",
                       "sharepoint.com", "wetransfer.com", "mega.nz", "box.com")
# kind of address: (stable or not, column of the CSV, name in the reports)
ADDRESS_KINDS = {
    "portal": (True, "m7_portal", "uploaded on the portal"),
    "datastore": (True, "m7_datastore", "in a DataStore table of the portal"),
    "service": (True, "m7_service", "through a standard service request (WMS, WFS, OAI-PMH)"),
    "external": (True, "m7_external", "at a plain address on another site"),
    "third-party": (True, "m7_third_party", "on a third-party storage service"),
    "token": (False, "m7_token", "with a token, ticket or session parameter"),
    "shortener": (False, "m7_shortener", "through a URL shortener"),
    "redirect": (False, "m7_redirect", "through a search-engine redirect"),
    "none": (None, "m7_without_address", "without an address"),
}

# M9: high-value marking. The six categories of the Annex of Regulation (EU) 2023/138, with their
# codes in the EU vocabulary (http://data.europa.eu/bna/...), as in 02_catalog_profile.py.
HVD_CATEGORIES = {
    "c_ac64a52d": "Geospatial",
    "c_dd313021": "Earth observation and environment",
    "c_164e0bf5": "Meteorological",
    "c_e1da4e07": "Statistics",
    "c_a9135398": "Companies and company ownership",
    "c_b79e35eb": "Mobility",
}
HVD_REGULATION = "2023/138"      # the ELI of the Regulation is http://data.europa.eu/eli/reg_impl/2023/138/oj
HVD_TYPE = "http://publications.europa.eu/resource/authority/dataset-type/HVD"

TAG = re.compile(r"<[^>]+>")
NOT_WORD = re.compile(r"[\W_]+", re.UNICODE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_int(n) -> str:
    """Number with a thousands separator."""
    return f"{int(n):,}"


def fmt_pct(part, whole) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def newest_snapshot() -> Path:
    candidates = sorted(p for p in RAW_DIR.glob("catalog_*.jsonl.gz") if "_test" not in p.name)
    if not candidates:
        raise SystemExit("No snapshot found in data/raw. Run 01_snapshot.py first.")
    return candidates[-1]


def snapshot_date(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if not match:
        raise SystemExit(f"The file name {path.name} does not contain a date (YYYY-MM-DD).")
    return match.group(1)


def visible_text(value) -> str:
    """Text as a reader sees it: without HTML tags, entities decoded, white space collapsed."""
    text = html.unescape(TAG.sub(" ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()


def normalised(text: str) -> str:
    """Lower case, punctuation removed, single spaces: for comparing a description with a title."""
    return NOT_WORD.sub(" ", text.lower()).strip()


def is_bundle(resource: dict) -> bool:
    """The automatic "download all" ZIP bundle generated by the portal (same rule as 02_catalog_profile.py)."""
    return bool(resource.get("downloadall_datapackage_hash"))


def own_resources(dataset: dict) -> list[dict]:
    resources = [r for r in dataset.get("resources") or [] if isinstance(r, dict)]
    return [r for r in resources if not is_bundle(r)]


def has_access_url(resource: dict) -> bool:
    """A resource can be reached: a URL, an access URL, or an active DataStore table of the portal."""
    url = str(resource.get("url") or "").strip()
    access_url = str(resource.get("access_url") or "").strip()
    return bool(url or access_url or resource.get("datastore_active"))


def has_value(value) -> bool:
    """A field holds a value: a non-blank string, a number, or a list or dict with a value inside."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(has_value(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_value(v) for v in value)
    return bool(value)


def publisher_source(dataset: dict) -> str:
    """Where the DCAT-AP export of the portal takes the publisher from (see the method notes on M2):
    "field" (the publisher field holds a value), "organisation" (the field is absent and the
    organisation is exported as publisher) or "none" (the field is present but empty)."""
    publisher = dataset.get("publisher")
    if has_value(publisher):
        return "field"
    if publisher in (None, "", []) and dataset.get("organization"):
        return "organisation"
    return "none"


def load_file_types(path: Path = FILE_TYPE_FILE) -> dict[str, str]:
    """The EU file-type vocabulary as {upper-cased code or English label: code}."""
    if not path.exists():
        raise SystemExit(f"{relative(path)} not found; the M3 check needs the EU file-type vocabulary.")
    table = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    mapping = {}
    for row in table.to_dict("records"):
        mapping[row["code"].strip().upper()] = row["code"]
        mapping[row["label_en"].strip().upper()] = row["code"]
    return mapping


def media_type(value) -> str | None:
    """The IANA media type held by a value (an IANA URI or a type/subtype string), or None."""
    text = str(value or "").strip()
    if text.startswith(IANA_PREFIX):
        text = text[len(IANA_PREFIX):]
    match = MEDIA_TYPE.fullmatch(text)
    if match and match.group(1) in IANA_TOP_LEVEL_TYPES and not match.group(2).lower().startswith("x-"):
        return text
    return None


def format_term(value) -> str | None:
    """The vocabulary term that a format value is: an EU file-type code, an IANA media type, or None."""
    text = str(value or "").strip().lstrip(".").strip()
    if not text:
        return None
    return FILE_TYPES.get(text.upper()) or media_type(text)


def licence_code(value) -> str | None:
    """The code of a term of the EU licence vocabulary held by a value, or None."""
    text = str(value or "").strip()
    return text[len(LICENCE_PREFIX):] if text.startswith(LICENCE_PREFIX) and len(text) > len(LICENCE_PREFIX) else None


def licence_class(code: str) -> str:
    """Class of an EU licence term: permissive, share-alike, restrictive, or unknown for a term not listed."""
    if code in EU_LICENCE_CLASSES:
        return EU_LICENCE_CLASSES[code]
    if "NC" in code or "ND" in code:
        return RESTRICTIVE
    if "SA" in code:
        return SHARE_ALIKE
    return "unknown"


def licence_family(value: str) -> str:
    return LICENCE_FAMILIES.get(value, value)


def address_kind(resource: dict) -> str:
    """The kind of address of a resource, for M7 (the keys of ADDRESS_KINDS)."""
    url = str(resource.get("url") or "").strip()
    if not url:
        return "datastore" if resource.get("datastore_active") else "none"
    parts = urlsplit(url)
    host = parts.netloc.lower().rsplit("@", 1)[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.lower()
    query = parts.query.lower()
    keys = set(parse_qs(query, keep_blank_values=True))
    if host in URL_SHORTENERS:
        return "shortener"
    if host in SEARCH_ENGINES and path.startswith("/url"):
        return "redirect"
    if keys & OPAQUE_PARAMETERS or path.endswith("linkclick.aspx"):
        return "token"
    if host == PORTAL_HOST and PORTAL_DOWNLOAD.search(parts.path):
        return "portal"
    if any(group <= keys for group in SERVICE_PARAMETERS):
        return "service"
    if any(host == site or host.endswith("." + site) for site in THIRD_PARTY_STORAGE):
        return "third-party"
    return "external"


def address_host(resource: dict) -> str:
    host = urlsplit(str(resource.get("url") or "").strip()).netloc.lower().rsplit("@", 1)[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def md_cell(text) -> str:
    """Text safe for a cell of a Markdown table."""
    return str(text).replace("|", "/").replace("\n", " ").strip()


def link(title: str, name: str) -> str:
    label = md_cell(title).replace("[", "(").replace("]", ")")
    return f"[{label}]({DATASET_URL}{name})"


# ---------------------------------------------------------------------------
# Checks: one function per criterion. Each returns the measurements, the proposed
# score ("<id>_score") and the reason ("<id>_reason"), with the criterion id as prefix.
# ---------------------------------------------------------------------------

def check_m1(dataset: dict) -> dict:
    """M1 Mandatory metadata: title, meaningful description, access URL of every resource."""
    title = visible_text(dataset.get("title"))
    description = visible_text(dataset.get("notes"))
    resources = own_resources(dataset)
    without_url = [r for r in resources if not has_access_url(r)]
    repeats_title = bool(description) and normalised(description) == normalised(title)

    if not title:
        score, reason = 0, "no title"
    elif not description:
        score, reason = 0, "no description"
    elif without_url:
        names = "; ".join(visible_text(r.get("name")) or "(unnamed)" for r in without_url[:3])
        more = f" and {len(without_url) - 3} more" if len(without_url) > 3 else ""
        score = 0
        reason = (f"{len(without_url)} of {len(resources)} resources without an access URL: "
                  f"{names}{more}")
    elif repeats_title:
        score, reason = 1, "description repeats the title"
    elif len(description) < MIN_DESCRIPTION_CHARS:
        score, reason = 1, f"description of {len(description)} characters (minimum {MIN_DESCRIPTION_CHARS})"
    else:
        score, reason = 2, "title, description and access URLs present"
    if not resources:
        reason += "; no resources (scored by Q1)"

    return {
        "m1_title_chars": len(title),
        "m1_description_chars": len(description),
        "m1_description_repeats_title": repeats_title,
        "m1_resources": len(resources),
        "m1_resources_without_url": len(without_url),
        "m1_score": score,
        "m1_reason": reason,
    }


def check_m2(dataset: dict) -> dict:
    """M2 Recommended metadata: how many of the seven recommended properties hold a value."""
    present = {key: has_value(dataset.get(field)) for key, _, field in M2_PROPERTIES}
    count = sum(present.values())
    score = 2 if count >= M2_SCORE_2 else 1 if count >= M2_SCORE_1 else 0
    missing = [name for key, name, _ in M2_PROPERTIES if not present[key]]
    reason = f"{count} of 7 present" + (f"; missing {', '.join(missing)}" if missing else "")

    result = {f"m2_{key}": present[key] for key, _, _ in M2_PROPERTIES}
    result.update({
        "m2_publisher_source": publisher_source(dataset),
        "m2_present": count,
        "m2_score": score,
        "m2_reason": reason,
    })
    return result


def check_m3(dataset: dict) -> dict:
    """M3 Controlled vocabularies: theme, frequency and resource formats given with vocabulary terms."""
    judged = []                      # one True/False per item that is present
    parts = []                       # what was found to be from the vocabularies, for the reason

    themes = [t for t in (dataset.get("theme") or []) if has_value(t)]
    theme_ok = all(str(t).startswith(DATA_THEME_PREFIX) for t in themes) if themes else None
    if theme_ok is not None:
        judged.append(theme_ok)
        parts.append("theme")
    frequency = dataset.get("frequency")
    frequency_ok = str(frequency).startswith(FREQUENCY_PREFIX) if has_value(frequency) else None
    if frequency_ok is not None:
        judged.append(frequency_ok)
        parts.append("frequency")

    resources = own_resources(dataset)
    with_format = vocab = format_vocab = 0
    free_text = Counter()
    for resource in resources:
        fmt = str(resource.get("format") or "").strip()
        mime = media_type(resource.get("mimetype"))
        if not fmt and not mime:
            continue                 # no format at all: scored by M2 and Q6, not here
        with_format += 1
        term = format_term(fmt)
        format_vocab += term is not None
        ok = term is not None or mime is not None
        vocab += ok
        judged.append(ok)
        if not ok:
            free_text[fmt] += 1
    if with_format:
        parts.append(f"{with_format} resource formats")

    free_text_list = "; ".join(sorted(free_text, key=str.lower))
    if not judged:
        score, reason = 0, "nothing declared: no theme, frequency or format"
    elif all(judged):
        score, reason = 2, "all from vocabularies: " + ", ".join(parts)
    elif any(judged):
        score = 1
        bad = [] if theme_ok in (None, True) else ["theme"]
        bad += [] if frequency_ok in (None, True) else ["frequency"]
        if free_text:
            bad.append(f"{with_format - vocab} of {with_format} resource formats ({free_text_list})")
        reason = "some free text: " + "; ".join(bad)
    else:
        score, reason = 0, f"no vocabulary term: {free_text_list or 'theme or frequency outside the vocabularies'}"

    return {
        "m3_theme_vocab": theme_ok,
        "m3_frequency_vocab": frequency_ok,
        "m3_resources_with_format": with_format,
        "m3_resources_vocab": vocab,
        "m3_resources_format_vocab": format_vocab,
        "m3_free_text": free_text_list,
        "m3_score": score,
        "m3_reason": reason,
    }


def check_m4(dataset: dict) -> dict:
    """M4 Licence: an open licence declared clearly for every resource."""
    resources = own_resources(dataset)
    codes = []                       # EU licence terms of the resources, in order
    without = text_only = 0
    for resource in resources:
        code = licence_code(resource.get("license"))
        if code:
            codes.append(code)
        else:
            without += 1
            if has_value(resource.get("rights")) or has_value(resource.get("license_id")) \
                    or has_value(resource.get("license_title")):
                text_only += 1
    classes = {licence_class(code) for code in codes}
    distinct = sorted(set(codes))

    if not resources:
        score, reason = 0, "no resources: nothing declared"
    elif codes and not without:
        if RESTRICTIVE in classes:
            score, reason = 0, f"restrictive licence on a resource: {'; '.join(distinct)}"
        elif len(distinct) > 1:
            score, reason = 1, f"different licences between resources: {'; '.join(distinct)}"
        elif SHARE_ALIKE in classes:
            score, reason = 1, f"share-alike licence: {distinct[0]}"
        elif "unknown" in classes:
            score, reason = 1, f"licence not classed, to be checked by hand: {distinct[0]}"
        else:
            score, reason = 2, f"open licence on every resource: {distinct[0]}"
    elif codes:
        if RESTRICTIVE in classes:
            score, reason = 0, f"restrictive licence on a resource: {'; '.join(distinct)}"
        else:
            score, reason = 1, f"licence missing on {without} of {len(resources)} resources"
    elif text_only:
        score, reason = 1, "licence only as text, without a link"
    else:
        score, reason = 0, "no licence"

    dataset_field = str(dataset.get("license_id") or "").strip()
    field_class = DATASET_FIELD_CLASSES.get(dataset_field, "unknown")
    conflict = bool(codes) and field_class not in ("none", "open-unspecified") \
        and licence_family(dataset_field) not in {licence_family(code) for code in codes}

    return {
        "m4_resources": len(resources),
        "m4_resources_with_licence": len(codes),
        "m4_licences": "; ".join(distinct),
        "m4_licence_class": ("mixed" if len(classes) > 1 else next(iter(classes)) if classes
                             else "text" if text_only else "none"),
        "m4_dataset_field": dataset_field,
        "m4_dataset_field_conflict": conflict,
        "m4_score": score,
        "m4_reason": reason,
    }


def check_m7(dataset: dict) -> dict:
    """M7 Persistent identifier: a permanent identifier for the dataset, stable addresses for its resources."""
    resources = own_resources(dataset)
    kinds = [address_kind(resource) for resource in resources]
    counts = Counter(kinds)
    stable = sum(count for kind, count in counts.items() if ADDRESS_KINDS[kind][0] is True)
    changing = sum(count for kind, count in counts.items() if ADDRESS_KINDS[kind][0] is False)
    without = counts["none"]
    total = len(resources)
    summary = ", ".join(f"{count} {ADDRESS_KINDS[kind][2]}" for kind, count in counts.most_common())
    changing_hosts = sorted({address_host(resource) for resource, kind in zip(resources, kinds)
                             if ADDRESS_KINDS[kind][0] is False})

    if not resources:
        score, reason = 0, "no resources: no address to keep"
    elif not stable and not changing:
        score, reason = 0, "no address on any resource"
    elif not stable:
        score, reason = 1, f"every resource through a changing address: {summary}"
    elif changing:
        score, reason = 1, f"changing address on {changing} of {total} resources: {summary}"
    elif without:
        score, reason = 1, f"address missing on {without} of {total} resources: {summary}"
    else:
        score, reason = 2, f"permanent identifier and stable addresses: {summary}"

    row = {"m7_resources": total}
    row.update({column: counts[kind] for kind, (_, column, _) in ADDRESS_KINDS.items()})
    row.update({
        "m7_changing_hosts": "; ".join(changing_hosts),
        "m7_score": score,
        "m7_reason": reason,
    })
    return row


def check_m9(dataset: dict) -> dict:
    """M9 High-value designation: category, applicable legislation and type HVD in the metadata."""
    categories = [str(c).rstrip("/").rsplit("/", 1)[-1] for c in (dataset.get("hvd_category") or []) if has_value(c)]
    legislation = [str(l) for l in (dataset.get("applicable_legislation") or []) if has_value(l)]
    has_category = bool(categories)
    has_regulation = any(HVD_REGULATION in l for l in legislation)
    has_type = HVD_TYPE in [str(x) for x in (dataset.get("dcat_type") or [])]
    names = "; ".join(HVD_CATEGORIES.get(code, code) for code in categories)

    if has_category and has_regulation:
        score, reason = 2, f"category and Regulation 2023/138 declared: {names}"
    elif has_category:
        score, reason = 1, f"category without a reference to Regulation 2023/138: {names}"
    elif has_regulation:
        score, reason = 1, "reference to Regulation 2023/138 without a category" + (" (type HVD only otherwise)" if has_type else "")
    elif has_type:
        score, reason = 1, "only the dataset type HVD"
    else:
        score, reason = 0, "not marked"
    return {
        "m9_category": has_category,
        "m9_categories": names,
        "m9_regulation": has_regulation,
        "m9_type_hvd": has_type,
        "m9_marked": has_category or has_regulation or has_type,
        "m9_score": score,
        "m9_reason": reason,
    }


# (criterion id, criterion name, function); the order is the order of the reports.
CHECKS = [
    ("M1", "Mandatory metadata", check_m1),
    ("M2", "Recommended metadata", check_m2),
    ("M3", "Controlled vocabularies", check_m3),
    ("M4", "Licence", check_m4),
    ("M7", "Persistent identifier", check_m7),
    ("M9", "High-value designation", check_m9),
]


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def load_sample(path: Path) -> dict[str, dict]:
    """The sample as {dataset id: row}; empty if the sample has not been drawn yet."""
    if not path.exists():
        print(f"Note: {relative(path)} not found; the sample report is skipped.")
        return {}
    frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    return {row["id"]: row for row in frame.to_dict("records")}


def read_datasets(snapshot: Path):
    """Yields the datasets of the snapshot (data services and other record types are skipped)."""
    with gzip.open(snapshot, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if (record.get("type") or "dataset") == "dataset":
                yield record


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def build_summary(frame: pd.DataFrame, date: str, snapshot_name: str) -> str:
    n = len(frame)
    lines = [
        f"# Automated metadata checks: snapshot of {date}",
        "",
        f"Source: {snapshot_name}. Datasets: {fmt_int(n)}. Proposed scores follow the rules of "
        "`criteria/criteria.csv`; the scores of the sample are confirmed or corrected in the manual assessment.",
    ]
    for code, name, _ in CHECKS:
        key = code.lower()
        subset = frame
        lines += ["", f"## {code} {name}"]
        if code == "M9":
            subset = frame[frame["m9_marked"]]
            unmarked = n - len(subset)
            lines += ["", f"The criterion applies to the high-value datasets. In the catalogue it is counted over the "
                      f"{fmt_int(len(subset))} datasets that carry any high-value marking; the other "
                      f"{fmt_int(unmarked)} datasets are not marked, and whether they are high-value by content "
                      "is judged by hand (in the sample: the high-value group only)."]
        total = len(subset)
        scores = subset[f"{key}_score"].value_counts()
        lines += ["", "| Proposed score | Datasets | Share |", "| --- | ---: | ---: |"]
        for score in (2, 1, 0):
            count = int(scores.get(score, 0))
            lines.append(f"| {score} | {fmt_int(count)} | {fmt_pct(count, total)} |")
        # Reasons, without the dataset-specific details (resource names, character counts,
        # the list of missing properties).
        general = (subset[f"{key}_reason"].str.replace(r":.*$", "", regex=True)
                   .str.replace(r"\d+ of \d+ resources", "resources", regex=True)
                   .str.replace(r"description of \d+ characters \(minimum \d+\)",
                                f"description shorter than {MIN_DESCRIPTION_CHARS} characters", regex=True)
                   .str.replace("; no resources (scored by Q1)", "", regex=False)
                   .str.replace(r"; missing .*$", "", regex=True))
        lines += ["", "| Reason | Datasets |", "| --- | ---: |"]
        for reason, count in general.value_counts().items():
            lines.append(f"| {md_cell(reason)} | {fmt_int(count)} |")
        if code == "M2":
            lines += ["", "| Property | Datasets with a value | Share |", "| --- | ---: | ---: |"]
            for prop_key, prop_name, _ in M2_PROPERTIES:
                count = int(frame[f"m2_{prop_key}"].sum())
                lines.append(f"| {prop_name} | {fmt_int(count)} | {fmt_pct(count, n)} |")
            sources = frame["m2_publisher_source"].value_counts()
            lines += ["", "Publisher in the DCAT-AP export of the portal (only the first case counts in M2):", "",
                      "| Source of the publisher | Datasets | Share |", "| --- | ---: | ---: |"]
            for source, label in (("field", "publisher field of the dataset"),
                                  ("organisation", "organisation, exported when the field is absent"),
                                  ("none", "none: the field is present but empty")):
                count = int(sources.get(source, 0))
                lines.append(f"| {label} | {fmt_int(count)} | {fmt_pct(count, n)} |")
        if code == "M3":
            with_format = int(frame["m3_resources_with_format"].sum())
            vocab = int(frame["m3_resources_vocab"].sum())
            format_vocab = int(frame["m3_resources_format_vocab"].sum())
            lines += ["", f"Resources with a format or media type: {fmt_int(with_format)}. With a vocabulary term "
                      f"(format or media type): {fmt_int(vocab)} ({fmt_pct(vocab, with_format)}); with a format that "
                      f"is itself a term of the EU file-type vocabulary or an IANA media type: {fmt_int(format_vocab)} "
                      f"({fmt_pct(format_vocab, with_format)}).",
                      "", "| Free-text format value (most frequent) | Datasets |", "| --- | ---: |"]
            values = Counter()
            for text in frame["m3_free_text"]:
                for value in filter(None, (part.strip() for part in str(text).split(";"))):
                    values[value] += 1
            for value, count in values.most_common(15):
                lines.append(f"| {md_cell(value)} | {fmt_int(count)} |")
        if code == "M4":
            licences = Counter()
            for text in frame["m4_licences"]:
                for value in filter(None, (part.strip() for part in str(text).split(";"))):
                    licences[value] += 1
            lines += ["", "| Licence of the resources (EU vocabulary) | Class | Datasets |", "| --- | --- | ---: |"]
            for value, count in licences.most_common():
                lines.append(f"| {value} | {licence_class(value)} | {fmt_int(count)} |")
            with_field = int((frame["m4_dataset_field"] != "").sum())
            conflicts = int(frame["m4_dataset_field_conflict"].sum())
            lines += ["", f"Generic dataset-level licence field of CKAN (not shown on the portal, not exported, "
                      f"not scored): filled in {fmt_int(with_field)} datasets ({fmt_pct(with_field, n)}); "
                      f"it contradicts the licences of the resources in {fmt_int(conflicts)} datasets "
                      f"({fmt_pct(conflicts, n)})."]
        if code == "M7":
            lines += ["", "The portal gives every dataset a permanent identifier (UUID) and a URI built on it, both "
                      "exported in DCAT-AP, and every resource a URI of its own; the criterion is decided by the "
                      "addresses of the resources (the automatic ZIP bundle of the portal is not counted).",
                      "", "| Resources | Stable address | Resources | Datasets |", "| --- | --- | ---: | ---: |"]
            for kind, (stable, column, label) in ADDRESS_KINDS.items():
                lines.append(f"| {label} | {'yes' if stable else 'no' if stable is False else '-'} | "
                             f"{fmt_int(int(frame[column].sum()))} | {fmt_int(int((frame[column] > 0).sum()))} |")
            hosts = Counter()
            for text in frame["m7_changing_hosts"]:
                for value in filter(None, (part.strip() for part in str(text).split(";"))):
                    hosts[value] += 1
            lines += ["", "| Site of the changing addresses (most frequent) | Datasets |", "| --- | ---: |"]
            for value, count in hosts.most_common(10):
                lines.append(f"| {md_cell(value)} | {fmt_int(count)} |")
        if code == "M9":
            lines += ["", "| Marking | Datasets |", "| --- | ---: |"]
            for label, mask in (("category and Regulation 2023/138", subset["m9_category"] & subset["m9_regulation"]),
                                ("category, Regulation 2023/138 and type HVD",
                                 subset["m9_category"] & subset["m9_regulation"] & subset["m9_type_hvd"]),
                                ("only the type HVD", subset["m9_type_hvd"] & ~subset["m9_category"] & ~subset["m9_regulation"]),
                                ("Regulation 2023/138 without a category", subset["m9_regulation"] & ~subset["m9_category"])):
                lines.append(f"| {label} | {fmt_int(int(mask.sum()))} |")
            categories = Counter()
            for text in subset["m9_categories"]:
                for value in filter(None, (part.strip() for part in str(text).split(";"))):
                    categories[value] += 1
            lines += ["", "| Declared high-value category | Datasets |", "| --- | ---: |"]
            for value, count in categories.most_common():
                lines.append(f"| {value} | {fmt_int(count)} |")
    return "\n".join(lines) + "\n"


def build_sample_report(frame: pd.DataFrame, sample: dict[str, dict], date: str) -> str:
    rows = frame[frame["sample_id"] != ""].sort_values("sample_id")
    missing = sorted(set(r["sample_id"] for r in sample.values()) - set(rows["sample_id"]))
    lines = [
        f"# Automated metadata checks on the sample: snapshot of {date}",
        "",
        "Proposed scores and the reason of each one, for the review of every dataset. A proposed "
        "score is confirmed or corrected in the manual assessment, with the reason of the correction.",
    ]
    if missing:
        lines += ["", f"Not found in the snapshot: {', '.join(missing)}."]
    for code, name, _ in CHECKS:
        key = code.lower()
        lines += ["", f"## {code} {name}", "", "| ID | Dataset | Proposed | Reason |", "| --- | --- | ---: | --- |"]
        applicable = rows if code != "M9" else rows[rows["sample_group"] == "high-value"]
        for row in rows.to_dict("records"):
            if code == "M9" and row["sample_group"] != "high-value":
                lines.append(f"| {row['sample_id']} | {link(row['title'], row['name'])} | n/a | comparison group |")
                continue
            lines.append(f"| {row['sample_id']} | {link(row['title'], row['name'])} | "
                         f"{row[f'{key}_score']} | {md_cell(row[f'{key}_reason'])} |")
        counts = applicable[f"{key}_score"].value_counts()
        lines += ["", "Sample: " + ", ".join(
            f"{fmt_int(counts.get(s, 0))} dataset{'s' if counts.get(s, 0) != 1 else ''} with {s}" for s in (2, 1, 0)) + "."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Automated checks of the metadata, on the whole catalogue.")
    parser.add_argument("--snapshot", type=Path, default=None,
                        help="catalogue snapshot (default: the newest in data/raw)")
    parser.add_argument("--sample", type=Path, default=SAMPLE_FILE,
                        help="sample file (default: data/processed/sample.csv)")
    args = parser.parse_args()

    snapshot = args.snapshot or newest_snapshot()
    if not snapshot.exists():
        raise SystemExit(f"{relative(snapshot)} not found.")
    date = snapshot_date(snapshot)
    sample = load_sample(args.sample)
    FILE_TYPES.update(load_file_types())
    print(f"Snapshot: {relative(snapshot)}")
    print("Checks: " + ", ".join(f"{code} {name}" for code, name, _ in CHECKS))

    rows = []
    for dataset in read_datasets(snapshot):
        organization = dataset.get("organization") or {}
        row = {
            "id": dataset.get("id"),
            "name": dataset.get("name"),
            "title": visible_text(dataset.get("title")),
            "organization_title": organization.get("title") or "",
            "sample_id": sample.get(dataset.get("id"), {}).get("sample_id", ""),
            "sample_group": sample.get(dataset.get("id"), {}).get("group", ""),
        }
        for _, _, check in CHECKS:
            row.update(check(dataset))
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values("id").reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = OUT_DIR / f"checks_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_file = PROCESSED_DIR / f"metadata_checks_{date}.csv"
    frame.to_csv(checks_file, index=False, encoding="utf-8-sig", lineterminator="\n")
    (out_dir / "summary.md").write_text(build_summary(frame, date, snapshot.name), encoding="utf-8", newline="\n")
    if sample:
        (out_dir / "sample.md").write_text(build_sample_report(frame, sample, date), encoding="utf-8", newline="\n")

    print(f"Datasets checked: {fmt_int(len(frame))}; in the sample: {fmt_int((frame['sample_id'] != '').sum())}")
    for code, name, _ in CHECKS:
        subset = frame[frame["m9_marked"]] if code == "M9" else frame
        counts = subset[f"{code.lower()}_score"].value_counts()
        note = " (marked datasets only)" if code == "M9" else ""
        print(f"  {code} {name}: " + ", ".join(f"score {s}: {fmt_int(counts.get(s, 0))}" for s in (2, 1, 0)) + note)
    print("Files:")
    for path in (checks_file, out_dir / "summary.md", out_dir / "sample.md"):
        if path.exists():
            print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
