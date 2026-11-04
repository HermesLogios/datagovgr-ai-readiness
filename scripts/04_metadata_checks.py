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
  M6  Mode of distribution: API, direct link to a file, map view or web page.
  M7  Persistent identifier: a permanent identifier for the dataset and stable addresses for its
      resources.
  M9  High-value designation: the marking of a dataset as high-value in its metadata.
  Q5  Timeliness, metadata part: the declared update frequency against the last change known to the
      portal; the final score of the sample comes from the dates inside the data and the second
      snapshot.
  Q6  Format (5-star scale): the most open format among the resources, from the declared formats.
  These are all the checks that the metadata allow; the other criteria are assessed on the files of
  the sample (05_resource_profile.py) and by hand.

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
  - M6. The mode of access of each resource is read from its address, its declared format and the
    result of the portal's own link checker (DECISIONS.md #34): an API or data service (a WFS, WCS
    or OAI-PMH request, an ArcGIS REST endpoint, an active DataStore table of the portal, a link to
    a data service of the portal); a direct link to a file (a file uploaded on the portal, an
    address ending in a file extension, an address that the link checker downloaded as a file, or,
    without any such sign, a declared file format, which is recorded as not verified); a map view (a
    WMS request or endpoint); a web page (an address that the link checker received as HTML, a
    declared format URL, HTML or LINK or no format, a service format declared on an address that is
    not a service endpoint, a dynamic page address such as .php or .aspx); or no address. The
    dataset scores the best mode of its resources: an API or a direct file link scores 2, only map
    views or web pages score 1, no address on any resource or no resources scores 0. Whether a link
    delivers the complete data, whether a dataset is split into arbitrary parts, whether a web page
    offers a download, and whether the links work are verified by the download test of the sample
    (Q1), which can lower the score; the links of the Region of Attica with a token (?fdl=...) count
    as direct file links here, since the link delivers the file (their persistence is scored by M7).
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
  - Q5. The declared frequency (frequency, a term of the EU frequency vocabulary) is read in three
    groups (DECISIONS.md #36): a periodic frequency (annual, monthly, daily..., with its period in
    days; continuous counts with a period of one day), "not updated" (not planned, never) and no
    usable period (no frequency, unknown as decided in #24, irregular, as needed, other). The last
    change is the newest upload date of a resource (last_modified). The migration from the previous
    portal (November 2025) copied the files and wrote the date of the copy into last_modified, while
    keeping the original upload date in created: for a resource created before its dataset was
    created on the portal and modified within a day of that creation, the upload date is its created
    date. When no resource was uploaded, only the date of the resource record or of the metadata
    exists, which is the history of the portal and not of the data, and the dataset is not measurable
    from the metadata. With an upload date, a periodic frequency scores 2 within two periods (the
    declared one plus one of tolerance), 1 up to four periods and 0 beyond; no usable period scores 1
    within 12 months and 0 beyond. A dataset declared as not updated scores 2 when its title or
    description states the past period of its data (a year or a date, numbers of laws and decisions
    such as 4727/2020 excluded); otherwise the declaration is not supported and the no-period rule
    applies. Almost every "not planned" in the catalogue is the default value written by the
    migration (keyword "Από μετάπτωση"), recorded in q5_migrated. The final score of the sample uses
    the newest date inside the data (Step 2) and the changes between the two snapshots.
  - Q6. Each resource is placed on the 5-star scale from what the metadata say (DECISIONS.md #35):
    a map view (WMS) or a web page is 1 star; a WFS request is rated by its outputFormat (CSV,
    JSON, KML, GML 3 stars; shape-zip, Excel 2 stars), a WFS service, a DataStore table or an
    OAI-PMH request 3 stars, an ArcGIS REST service 2 stars; a file is rated by its declared format
    (open structured formats such as CSV, JSON, GeoJSON, XML, GML, KML, GeoPackage, GeoTIFF,
    NetCDF, RDF, ODS 3 stars; vendor-specific structured formats such as XLS, XLSX, SHP, MDB, DWG
    2 stars; unstructured formats such as PDF, DOC, TXT, images, HTML 1 star), failing that by the
    extension of its address, failing that by the media type that the portal's link checker
    received. A compressed archive (ZIP, RAR, GZ) is rated only when its name says what it holds
    (GTFS, shapefile, CSV...); otherwise it is undetermined, and so is a resource without any
    format. The dataset scores its best resource: 3 stars or more scores 2, 2 stars scores 1,
    1 star scores 0; a dataset whose resources are all undetermined has no proposed score, and a
    score that undetermined archives could raise is marked provisional. The declared format is
    verified against the content of the files in the download test of the sample (Step 2), which
    can change the score in either direction: a file declared CSV that is a PDF counts as PDF, a
    TXT file that holds a delimited table counts as CSV, a TIFF with georeferencing counts as
    GeoTIFF.

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
from datetime import date, datetime
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

# M6: mode of distribution. The mode of each resource is read from its address, its declared
# format and the result of the portal's link checker (DECISIONS.md #34).
FILE_EXTENSIONS = {
    "csv", "tsv", "txt", "json", "geojson", "topojson", "xml", "gml", "kml", "kmz", "gpkg", "rdf", "ttl", "nt",
    "jsonld", "xls", "xlsx", "xlsm", "xlsb", "ods", "doc", "docx", "odt", "pdf", "rtf", "zip", "gz", "7z", "rar",
    "tar", "tgz", "shp", "dbf", "shx", "prj", "tif", "tiff", "img", "nc", "hdf", "las", "laz", "dxf", "dwg",
    "mdb", "accdb", "sql", "sqlite", "db", "parquet", "jpg", "jpeg", "png", "gif", "svg", "mp4", "mp3", "wav",
    "xsd", "ppt", "pptx", "epub", "ics", "osm", "pbf", "dat", "sav", "dta", "cif",
}
PAGE_EXTENSIONS = {"html", "htm", "php", "asp", "aspx", "ashx", "jsp", "jspx", "cfm", "do", "action", "cgi"}
PAGE_FORMATS = {"", "HTML", "URL", "LINK", "WEB", "WEBPAGE", "WEB PAGE", "UNKNOWN", "ΙΣΤΟΣΕΛΙΔΑ", "TASK-FLOW", "RSS"}
MAP_FORMATS = {"WMS", "WMTS", "TMS", "XYZ"}
SERVICE_FORMATS = {"WFS", "WCS", "API", "REST", "ESRI REST", "ARCGIS", "ARCGIS GEOSERVICES REST API", "ARCGIS REST",
                   "OGC API", "SPARQL", "OAI-PMH", "ODATA", "JSON API", "GEOSERVICES"}
DATA_SERVICE_URI = "data-service"           # a link to a data service record of the portal
HTML_MEDIA_TYPES = {"text/html", "application/xhtml+xml"}
# mode of access: (score when it is the best mode of the dataset, column of the CSV, name in the reports)
MODES = {
    "api": (2, "m6_api", "API or data service (WFS, DataStore, OAI-PMH, ArcGIS REST, data service of the portal)"),
    "file": (2, "m6_file", "direct link to a file"),
    "map": (1, "m6_map", "map view (WMS)"),
    "page": (1, "m6_page", "web page"),
    "none": (0, "m6_without_address", "no address"),
}
MODE_WORDS = {   # singular and plural, for the reason of each dataset
    "api": ("API", "API"), "file": ("file", "files"), "map": ("map view", "map views"),
    "page": ("web page", "web pages"), "none": ("without an address", "without an address"),
}

# Q5: timeliness, metadata part (DECISIONS.md #36). Period of the EU frequency codes, in days.
FREQUENCY_PERIOD_DAYS = {
    "1MIN": 1 / 1440, "5MIN": 5 / 1440, "10MIN": 10 / 1440, "15MIN": 15 / 1440, "30MIN": 30 / 1440,
    "HOURLY": 1 / 24, "BIHOURLY": 2 / 24, "TRIHOURLY": 3 / 24, "DAILY": 1, "DAILY_2": 0.5,
    "WEEKLY": 7, "WEEKLY_2": 3.5, "WEEKLY_3": 7 / 3, "BIWEEKLY": 14,
    "MONTHLY": 30.44, "MONTHLY_2": 15.22, "MONTHLY_3": 10.15, "BIMONTHLY": 60.88, "QUARTERLY": 91.31,
    "ANNUAL": 365.25, "ANNUAL_2": 182.63, "ANNUAL_3": 121.75, "BIENNIAL": 730.5, "TRIENNIAL": 1095.75,
    "QUADRENNIAL": 1461, "QUINQUENNIAL": 1826.25, "DECENNIAL": 3652.5, "BIDECENNIAL": 7305, "TRIDECENNIAL": 10957.5,
    "CONT": 1, "UPDATE_CONT": 1,      # continuous: the data should be current within a day
}
FREQUENCY_NOT_UPDATED = {"NOT_PLANNED", "NEVER"}
MIGRATION_KEYWORD = "Από μετάπτωση"   # keyword of the datasets migrated from the previous portal
MIGRATION_COPY_SECONDS = 86400        # a file modified within a day of the creation of its dataset was copied
PERIOD_YEAR = re.compile(r"(?<![\d/])(19[5-9]\d|20[0-2]\d)(?!\d)")   # a year from 1950 to 2029
ACT_NUMBER = re.compile(r"\d+\s*/\s*(?:19|20)\d\d")                  # numbers of laws and decisions, e.g. 4727/2020
Q5_WITHIN_PERIODS = 2      # the declared period plus one period of tolerance
Q5_LATE_PERIODS = 4        # one to three periods late
Q5_NO_PERIOD_DAYS = 365    # no usable period: updated in the last 12 months
REFERENCE_DATE: date | None = None   # the date of the snapshot, set by main()

# Q6: format on the 5-star scale, from the declared formats (DECISIONS.md #35). Formats are compared
# in upper case, without surrounding dots.
OPEN_FORMATS = {           # 3 stars or more: open, non-proprietary, structured
    "CSV", "TSV", "JSON", "GEOJSON", "TOPOJSON", "XML", "GML", "GML2", "GML3", "KML", "KMZ", "GPKG", "GEOPACKAGE",
    "GEOTIFF", "NETCDF", "HDF5", "RDF", "RDF_XML", "RDF_TURTLE", "RDF_TTL", "RDF_N_TRIPLES", "N_TRIPLES", "RDF_N_QUADS",
    "TURTLE", "TTL", "N3", "JSON_LD", "JSONLD", "ODS", "PARQUET", "SQLITE", "SQL", "ATOM", "RSS", "GRIB", "LAS", "LAZ",
    "ICS", "OSM", "PBF", "GTFS", "GPX", "CIF", "YAML", "WFS", "WCS", "CSW", "API", "REST", "JSON API", "ODATA", "SPARQL",
    "OAI-PMH",
}
PROPRIETARY_FORMATS = {    # 2 stars: structured, but vendor-specific
    "XLS", "XLSX", "XLSM", "XLSB", "EXCEL", "SHP", "SHAPE-ZIP", "SHAPEZIP", "SHP ZIP", "SHP-ZIP", "ZIP SHP", "SHAPEFILE",
    "ESRI SHAPEFILE", "DBF", "SHX",
    "PRJ", "SBN", "SBX", "MDB", "ACCDB", "DWG", "DXF", "DGN", "GDB", "FILEGDB", "E00", "SAV", "DTA", "MXD", "TAB", "MIF",
    "ECW", "IMG", "LYR", "QGS", "SLD", "SXC", "WK1", "NUMBERS", "ESRI REST", "ARCGIS", "ARCGIS REST",
    "ARCGIS GEOSERVICES REST API", "GEOSERVICES",
}
UNSTRUCTURED_FORMATS = {   # 1 star
    "PDF", "DOC", "DOCX", "ODT", "RTF", "TXT", "MD", "MARKDOWN", "LOG", "HTML", "HTM", "URL", "LINK", "WEB", "WEBPAGE",
    "WEB PAGE", "ΙΣΤΟΣΕΛΙΔΑ", "TASK-FLOW", "JPEG", "JPG", "PNG", "GIF", "BMP", "TIF", "TIFF", "SVG", "PPT", "PPTX",
    "ODP", "MP4", "MP3", "WAV", "AVI", "WMS", "WMTS", "EPUB", "XPS", "MSG", "EML", "PHP", "ASHX", "ASPX", "JSP",
}
ARCHIVE_FORMATS = {"ZIP", "RAR", "7Z", "GZ", "GZIP", "TAR", "TGZ", "TAR.GZ", "BZ2"}
WFS_OUTPUT_STARS = {       # outputFormat of a WFS GetFeature request
    "csv": 3, "text/csv": 3, "json": 3, "application/json": 3, "geojson": 3, "kml": 3, "gml2": 3, "gml3": 3,
    "gml32": 3, "application/vnd.google-earth.kml+xml": 3, "shape-zip": 2, "shapezip": 2, "excel": 2, "excel2007": 2,
}
MEDIA_TYPE_STARS = {       # media type received by the portal's link checker, when nothing else is known
    "text/csv": 3, "application/json": 3, "application/geo+json": 3, "application/xml": 3, "text/xml": 3,
    "application/gml+xml": 3, "application/vnd.google-earth.kml+xml": 3, "application/rdf+xml": 3,
    "application/vnd.oasis.opendocument.spreadsheet": 3, "application/vnd.ms-excel": 2,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": 2, "application/pdf": 1, "text/html": 1,
    "application/msword": 1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 1,
    "image/jpeg": 1, "image/png": 1, "image/tiff": 1,
}
NAME_HINTS = [             # a format named in the resource name or at the end of its address (archives, no format)
    ("gtfs", 3, "GTFS (zipped CSV)"), ("turtle", 3, "RDF Turtle"), ("ttl", 3, "RDF Turtle"), ("rdf", 3, "RDF"),
    ("geojson", 3, "GeoJSON"), ("json", 3, "JSON"), ("csv", 3, "CSV"), ("xml", 3, "XML"), ("kml", 3, "KML"),
    ("shapefile", 2, "shapefile"), ("shape", 2, "shapefile"), ("shp", 2, "shapefile"), ("xlsx", 2, "Excel"),
    ("xls", 2, "Excel"), ("excel", 2, "Excel"), ("pdf", 1, "PDF"),
]
STARS = {3: "3 stars or more: open structured format", 2: "2 stars: vendor-specific structured format",
         1: "1 star: unstructured format or map view", 0: "undetermined"}
Q6_SCORE = {3: 2, 2: 1, 1: 0}

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


def distribution_mode(resource: dict) -> tuple[str, str, bool]:
    """The mode of access of a resource, for M6: (mode, how it was decided, verified).

    Verified is False when the mode rests on the declared format alone, without a sign in the
    address or a result of the portal's link checker."""
    kind = address_kind(resource)
    if kind == "none":
        return "none", "no address", True
    if kind == "datastore":
        return "api", "DataStore table of the portal (API and download)", True
    url = str(resource.get("url") or "").strip()
    parts = urlsplit(url)
    path = parts.path.lower()
    query = {key: values[0] for key, values in parse_qs(parts.query.lower(), keep_blank_values=True).items()}
    declared = str(resource.get("format") or "").strip().upper()
    for service in resource.get("access_services") or []:
        if DATA_SERVICE_URI in str((service or {}).get("uri") or ""):
            return "api", "linked to a data service of the portal", True
    service = query.get("service", "")
    if service in ("wfs", "wcs", "sos", "wps") or "verb" in query:
        return "api", f"{service.upper() or 'OAI-PMH'} request", True
    if service in ("wms", "wmts"):
        return "map", f"{service.upper()} request ({query.get('request', '') or 'no request'})", True
    if service == "csw":
        return "page", "catalogue service (CSW), metadata not data", True
    if path.rstrip("/").endswith(("/wfs", "/wcs")) or "/featureserver" in path or "/mapserver" in path \
            or "/arcgis/rest/" in path:
        return "api", "service endpoint in the address", True
    if path.rstrip("/").endswith(("/wms", "/wmts")) or declared in MAP_FORMATS:
        return "map", "map service endpoint", True
    if kind == "portal":
        return "file", "uploaded on the portal", True
    if declared in SERVICE_FORMATS:
        return "page", f"declared as a service ({declared}) on an address that is not a service endpoint", True
    last = path.rsplit("/", 1)[-1]
    extension = last.rsplit(".", 1)[-1] if "." in last else ""
    archiver = resource.get("archiver") or {}
    media = ""
    if archiver.get("status") == "Archived successfully":
        media = str(archiver.get("mimetype") or "").split(";")[0].strip().lower()
    if extension in FILE_EXTENSIONS:
        return "file", f"file extension (.{extension})", True
    if media:
        if media in HTML_MEDIA_TYPES:
            return "page", "the link checker of the portal received a web page", True
        return "file", f"the link checker of the portal downloaded a file ({media})", True
    if extension in PAGE_EXTENSIONS:
        return "page", f"dynamic page address (.{extension}), not verified", False
    if declared in PAGE_FORMATS:
        return "page", f"declared as a page ({declared or 'no format'}), not verified", False
    return "file", f"declared format {declared}, not verified", False


def parse_date(value) -> date | None:
    """The date of an ISO timestamp of the portal (None when absent or malformed)."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text[:19]).date()
    except ValueError:
        return None


def parse_timestamp(value) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text[:26])
    except ValueError:
        return None


def upload_date(resource: dict, dataset_created: datetime | None) -> tuple[date | None, bool]:
    """The date of the last upload of a resource and whether it was corrected for the migration copy."""
    modified = parse_timestamp(resource.get("last_modified"))
    if not modified:
        return None, False
    created = parse_timestamp(resource.get("created"))
    if created and dataset_created and created < dataset_created \
            and abs((modified - dataset_created).total_seconds()) < MIGRATION_COPY_SECONDS:
        return created.date(), True
    return modified.date(), False


def last_change(dataset: dict, resources: list[dict]) -> tuple[date | None, str, int]:
    """The last change known to the portal: (date, source, files corrected for the migration copy).

    The source is "upload", "record", "metadata" or ""."""
    dataset_created = parse_timestamp(dataset.get("metadata_created"))
    uploads = [upload_date(r, dataset_created) for r in resources]
    dates = [d for d, _ in uploads if d]
    copies = sum(1 for d, corrected in uploads if d and corrected)
    if dates:
        return max(dates), "upload", copies
    records = [d for d in (parse_date(r.get("created")) for r in resources) if d]
    if records:
        return max(records), "record", 0
    modified = parse_date(dataset.get("metadata_modified"))
    return (modified, "metadata", 0) if modified else (None, "", 0)


def period_stated(dataset: dict) -> bool:
    """The title or the description states a year or a date (numbers of laws and decisions excluded)."""
    text = f"{visible_text(dataset.get('title'))} {visible_text(dataset.get('notes'))}"
    return bool(PERIOD_YEAR.search(ACT_NUMBER.sub(" ", text)))


def declared_format(resource: dict) -> str:
    return str(resource.get("format") or "").strip().upper().strip(".")


def format_hint(resource: dict) -> tuple[int, str] | None:
    """A format named in the resource name or at the end of its address (for archives and empty formats)."""
    name = f"{resource.get('name') or ''} {resource.get('format') or ''}".lower()
    words = set(re.split(r"[\s()\[\]_.,;:/-]+", name))
    last = urlsplit(str(resource.get("url") or "").strip()).path.lower().rstrip("/").rsplit("/", 1)[-1]
    for word, level, label in NAME_HINTS:
        if word in words or last == word:
            return level, label
    return None


def format_stars(resource: dict) -> tuple[int, str]:
    """The level of a resource on the 5-star scale, from the metadata: (3, 2, 1 or 0 = undetermined, reason)."""
    mode, _, _ = distribution_mode(resource)
    if mode == "none":
        return 0, "no address"
    if mode == "map":
        return 1, "map view (WMS): a picture of the map, not the data"
    if mode == "page":
        return 1, "web page"
    url = str(resource.get("url") or "").strip()
    parts = urlsplit(url)
    path = parts.path.lower()
    query = {key: values[0] for key, values in parse_qs(parts.query.lower(), keep_blank_values=True).items()}
    declared = declared_format(resource)
    if query.get("service") == "wfs":
        output = query.get("outputformat", "").split(";")[0].strip()
        if output:
            return WFS_OUTPUT_STARS.get(output, 3), f"WFS download in {output}"
        return 3, "WFS service (GML or GeoJSON on request)"
    if mode == "api":
        if "verb" in query:
            return 3, "OAI-PMH request (XML)"
        if address_kind(resource) == "datastore":
            return 3, "DataStore table of the portal (CSV and JSON through the API)"
        if "/arcgis/rest/" in path or "/featureserver" in path or "/mapserver" in path:
            return 2, "ArcGIS REST service (vendor-specific)"
        return 3, "data service"
    if declared in ARCHIVE_FORMATS:
        hint = format_hint(resource)
        if hint:
            return hint[0], f"archive ({declared}) named as {hint[1]}"
        return 0, f"archive ({declared}) with unknown content"
    if declared in OPEN_FORMATS:
        return 3, f"open format {declared}"
    if declared in PROPRIETARY_FORMATS:
        return 2, f"vendor-specific format {declared}"
    if declared in UNSTRUCTURED_FORMATS:
        return 1, f"unstructured format {declared}"
    last = path.rsplit("/", 1)[-1]
    extension = last.rsplit(".", 1)[-1].upper() if "." in last else ""
    if extension in ARCHIVE_FORMATS:
        hint = format_hint(resource)
        if hint:
            return hint[0], f"archive (.{extension.lower()}) named as {hint[1]}"
        return 0, f"archive (.{extension.lower()}) with unknown content"
    if extension in OPEN_FORMATS:
        return 3, f"open format .{extension.lower()} (address)"
    if extension in PROPRIETARY_FORMATS:
        return 2, f"vendor-specific format .{extension.lower()} (address)"
    if extension in UNSTRUCTURED_FORMATS:
        return 1, f"unstructured format .{extension.lower()} (address)"
    archiver = resource.get("archiver") or {}
    if archiver.get("status") == "Archived successfully":
        media = str(archiver.get("mimetype") or "").split(";")[0].strip().lower()
        if media in MEDIA_TYPE_STARS:
            return MEDIA_TYPE_STARS[media], f"media type received by the portal's link checker: {media}"
    hint = format_hint(resource)
    if hint:
        return hint[0], f"no format declared, named as {hint[1]}"
    if declared:
        return 0, f"format {declared} not classed"
    return 0, "no format declared"


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


def check_m6(dataset: dict) -> dict:
    """M6 Mode of distribution: the best mode of access among the resources."""
    resources = own_resources(dataset)
    modes = [distribution_mode(resource) for resource in resources]
    counts = Counter(mode for mode, _, _ in modes)
    unverified = sum(1 for _, _, verified in modes if not verified)
    order = list(MODES)
    best = min((mode for mode, _, _ in modes), key=order.index, default="none")
    summary = ", ".join(f"{count} {MODE_WORDS[mode][count != 1]}" for mode, count in counts.most_common())

    if not resources:
        score, reason = 0, "no resources: no access"
    elif best == "none":
        score, reason = 0, "no address on any resource"
    elif best == "api":
        score, reason = 2, f"API or data service: {summary}"
    elif best == "file":
        score, reason = 2, f"direct link to a file: {summary}"
    elif best == "map":
        score, reason = 1, f"only a map view (WMS): {summary}"
    else:
        score, reason = 1, f"only web pages: {summary}"
    if unverified and score == 2 and counts["api"] == 0 and counts["file"] == unverified:
        reason += " (declared format only, not verified)"

    row = {"m6_resources": len(resources)}
    row.update({column: counts[mode] for mode, (_, column, _) in MODES.items()})
    row.update({
        "m6_unverified": unverified,
        "m6_best_mode": best if resources else "",
        "m6_score": score,
        "m6_reason": reason,
    })
    return row


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


def check_q5(dataset: dict) -> dict:
    """Q5 Timeliness, metadata part: declared frequency against the last upload known to the portal."""
    resources = own_resources(dataset)
    code = str(dataset.get("frequency") or "").strip().rstrip("/").rsplit("/", 1)[-1].upper()
    period = FREQUENCY_PERIOD_DAYS.get(code)
    group = "periodic" if period else "not updated" if code in FREQUENCY_NOT_UPDATED else "no period"
    stated = period_stated(dataset) if group == "not updated" else None
    changed, source, copies = last_change(dataset, resources)
    age = (REFERENCE_DATE - changed).days if (changed and REFERENCE_DATE) else None
    periods = round(age / period, 1) if (period and age is not None) else None
    declared = code or "none"
    days = f"{age} day{'s' if age != 1 else ''}" if age is not None else ""
    tags = {str(tag.get("name") or "").strip() for tag in dataset.get("tags") or [] if isinstance(tag, dict)}

    if not resources:
        score, reason = None, "no resources: nothing to measure"
    elif group == "not updated" and stated:
        score, reason = 2, f"{declared}: declared as not updated, and the title or description states the period of the data"
    elif group == "periodic" and source == "upload":
        score = 2 if periods <= Q5_WITHIN_PERIODS else 1 if periods <= Q5_LATE_PERIODS else 0
        reason = f"{declared}: last upload {days} ago, {periods} periods"
    elif source != "upload":
        prefix = (f"{declared}" if group == "periodic" else
                  f"{declared}: declared as not updated without a stated period" if group == "not updated" else
                  f"no period declared ({declared})")
        score, reason = None, f"{prefix}: no upload date on the portal, not measurable from the metadata"
    else:
        score = 1 if age <= Q5_NO_PERIOD_DAYS else 0
        prefix = (f"{declared}: declared as not updated without a stated period" if group == "not updated"
                  else f"no period declared ({declared})")
        reason = f"{prefix}: last upload {days} ago"
    if copies and resources:
        reason += f" (original upload date for {copies} file{'s' if copies != 1 else ''} copied by the migration)"

    return {
        "q5_frequency": code,
        "q5_frequency_group": group if resources else "",
        "q5_period_days": round(period, 2) if period else None,
        "q5_period_stated": stated,
        "q5_migrated": MIGRATION_KEYWORD in tags,
        "q5_last_change": changed.isoformat() if changed else "",
        "q5_last_change_source": source,
        "q5_migration_copies": copies,
        "q5_age_days": age,
        "q5_periods": periods,
        "q5_score": score,
        "q5_reason": reason,
    }


def check_q6(dataset: dict) -> dict:
    """Q6 Format (5-star scale): the most open format among the resources, from the declared formats."""
    resources = own_resources(dataset)
    levels = [format_stars(resource) for resource in resources]
    counts = Counter(level for level, _ in levels)
    undetermined = sum(1 for (level, reason) in levels if level == 0 and reason != "no address")
    known = [level for level, _ in levels if level]
    best = max(known, default=0)
    formats = sorted({declared_format(resource) or "(none)" for resource in resources})
    provisional = bool(undetermined) and best < 3

    if not resources:
        score, reason = None, "no resources: nothing to rate"
    elif best == 0:
        score, reason = None, (f"undetermined: {undetermined} archive(s) or resource(s) without a known format"
                               if undetermined else "undetermined: no resource with an address")
    else:
        score, reason = Q6_SCORE[best], STARS[best]
        details = ", ".join(f"{counts[level]} at {level} star{'s' if level != 1 else ''}" for level in (3, 2, 1) if counts[level])
        reason += f": {details}"
        if provisional:
            reason += f"; provisional, {undetermined} archive(s) with unknown content could raise it"

    grouped = Counter(reason for _, reason in levels)
    return {
        "q6_resources": len(resources),
        "q6_levels": "; ".join(f"{count} {reason}" for reason, count in grouped.most_common()),
        "q6_stars_3": counts[3],
        "q6_stars_2": counts[2],
        "q6_stars_1": counts[1],
        "q6_undetermined": undetermined,
        "q6_best_stars": best,
        "q6_provisional": provisional,
        "q6_formats": "; ".join(formats),
        "q6_score": score,
        "q6_reason": reason,
    }


# (criterion id, criterion name, function); the order is the order of the reports.
CHECKS = [
    ("M1", "Mandatory metadata", check_m1),
    ("M2", "Recommended metadata", check_m2),
    ("M3", "Controlled vocabularies", check_m3),
    ("M4", "Licence", check_m4),
    ("M6", "Mode of distribution", check_m6),
    ("M7", "Persistent identifier", check_m7),
    ("M9", "High-value designation", check_m9),
    ("Q5", "Timeliness (metadata part)", check_q5),
    ("Q6", "Format (5-star scale)", check_q6),
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

def q5_general_reason(row) -> str:
    """The reason of a Q5 score without the dataset-specific details, for the summary."""
    group, score = row["q5_frequency_group"], row["q5_score"]
    if group == "periodic":
        return {2: "periodic frequency, upload within two periods", 1: "periodic frequency, two to four periods late",
                0: "periodic frequency, more than four periods late"}[int(score)]
    if group == "not updated" and row["q5_period_stated"] == True:  # noqa: E712
        return "declared as not updated, period of the data stated"
    prefix = "declared as not updated without a stated period" if group == "not updated" else "no usable period"
    return f"{prefix}, " + ("upload in the last 12 months" if int(score) == 1 else "no upload for more than 12 months")


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
        if code == "Q5":
            subset = frame[frame["q5_score"].notna()]
            groups = frame["q5_frequency_group"].value_counts()
            not_updated = frame[frame["q5_frequency_group"] == "not updated"]
            migrated_default = int((not_updated["q5_migrated"] == True).sum())  # noqa: E712
            uploads = int((frame["q5_last_change_source"] == "upload").sum())
            corrected = int((frame["q5_migration_copies"] > 0).sum())
            no_resources = int((frame["q5_frequency_group"] == "").sum())
            not_measurable = n - len(subset) - no_resources
            lines += ["", "Metadata part only: the declared frequency against the last upload known to the portal. "
                      f"Declared frequency: periodic {fmt_int(int(groups.get('periodic', 0)))} datasets (continuous "
                      f"counted with a period of one day), not updated {fmt_int(int(groups.get('not updated', 0)))} (of "
                      f"which {fmt_int(migrated_default)} carry the keyword of the migration from the previous portal, "
                      "whose default value it is), no usable period "
                      f"{fmt_int(int(groups.get('no period', 0)))}. An upload date exists for {fmt_int(uploads)} datasets; "
                      f"in {fmt_int(corrected)} of them the date written by the migration copy is replaced by the original "
                      "upload date. The others carry only the date of their portal record, which is the history of the "
                      "portal and not of the data. A dataset declared as not updated scores 2 when its title or description "
                      "states the period of its data; otherwise the rule of no period applies. Counted over the "
                      f"{fmt_int(len(subset))} measurable datasets; {fmt_int(not_measurable)} datasets are not measurable "
                      f"from the metadata and {fmt_int(no_resources)} have no resources. The final scores of the sample "
                      "come from the dates inside the data and from the second snapshot."]
        if code == "Q6":
            subset = frame[frame["q6_score"].notna()]
            no_resources = int((frame["q6_resources"] == 0).sum())
            undetermined = n - len(subset) - no_resources
            provisional = int(frame["q6_provisional"].sum())
            lines += ["", f"Rated from the declared formats, pending the content check of the sample. Counted over the "
                      f"{fmt_int(len(subset))} datasets whose best resource has a known level; {fmt_int(undetermined)} "
                      "datasets are undetermined (compressed archives whose content is not named, or no format) and "
                      f"{fmt_int(no_resources)} have no resources. {fmt_int(provisional)} of the rated datasets are "
                      "provisional: an archive with unknown content could raise their level."]
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
        if code == "Q5":
            general = subset.apply(q5_general_reason, axis=1)
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
        if code == "M6":
            unverified = int(frame["m6_unverified"].sum())
            lines += ["", "Mode of access of the resources, read from the address, the declared format and the result "
                      f"of the portal's link checker; {fmt_int(unverified)} resources are classed from the declared "
                      "format alone (not verified). The dataset scores its best mode.",
                      "", "| Mode of access | Score as best mode | Resources | Datasets |", "| --- | ---: | ---: | ---: |"]
            for mode, (score, column, label) in MODES.items():
                lines.append(f"| {label} | {score} | {fmt_int(int(frame[column].sum()))} | "
                             f"{fmt_int(int((frame[column] > 0).sum()))} |")
            lines += ["", "| Best mode of the dataset | Datasets | Share |", "| --- | ---: | ---: |"]
            best = frame["m6_best_mode"].value_counts()
            for mode, (_, _, label) in MODES.items():
                count = int(best.get(mode, 0))
                lines.append(f"| {label.split(' (')[0]} | {fmt_int(count)} | {fmt_pct(count, n)} |")
            lines += ["", "| Organisation with the most datasets offered only as a map view | Datasets | Of its datasets |",
                      "| --- | ---: | ---: |"]
            map_only = frame[frame["m6_best_mode"] == "map"]["organization_title"].value_counts()
            totals = frame["organization_title"].value_counts()
            for organisation, count in map_only.head(10).items():
                lines.append(f"| {md_cell(organisation)} | {fmt_int(count)} | {fmt_pct(count, totals.get(organisation, 0))} |")
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
        if code == "Q5":
            lines += ["", "| Declared frequency (EU vocabulary) | Group | Datasets | Share |", "| --- | --- | ---: | ---: |"]
            for value, count in frame["q5_frequency"].replace("", "(none)").value_counts().head(20).items():
                group = ("periodic" if value in FREQUENCY_PERIOD_DAYS else "not updated" if value in FREQUENCY_NOT_UPDATED
                         else "no period")
                lines.append(f"| {value} | {group} | {fmt_int(int(count))} | {fmt_pct(int(count), n)} |")
            lines += ["", "| Last change known to the portal | Datasets |", "| --- | ---: |"]
            for value, label in (("upload", "upload date of a resource (measurable)"),
                                 ("record", "date of the resource record only (history of the portal)"),
                                 ("metadata", "date of the metadata only"), ("", "none (no resources)")):
                count = int((frame["q5_last_change_source"] == value).sum())
                lines.append(f"| {label} | {fmt_int(count)} |")
            lines += ["", "| Group | Score 2 | Score 1 | Score 0 | Not measurable |", "| --- | ---: | ---: | ---: | ---: |"]
            parts = (("periodic", frame["q5_frequency_group"] == "periodic"),
                     ("not updated, period stated", (frame["q5_frequency_group"] == "not updated") & (frame["q5_period_stated"] == True)),  # noqa: E712
                     ("not updated, no period stated", (frame["q5_frequency_group"] == "not updated") & (frame["q5_period_stated"] != True)),  # noqa: E712
                     ("no usable period", frame["q5_frequency_group"] == "no period"))
            for label, mask in parts:
                part = frame[mask]
                counts = part["q5_score"].value_counts()
                lines.append(f"| {label} | {fmt_int(int(counts.get(2, 0)))} | {fmt_int(int(counts.get(1, 0)))} | "
                             f"{fmt_int(int(counts.get(0, 0)))} | {fmt_int(int(part['q5_score'].isna().sum()))} |")
        if code == "Q6":
            lines += ["", "| Level of the resources | Resources | Datasets with at least one |", "| --- | ---: | ---: |"]
            for level, column in ((3, "q6_stars_3"), (2, "q6_stars_2"), (1, "q6_stars_1"), (0, "q6_undetermined")):
                lines.append(f"| {STARS[level]} | {fmt_int(int(frame[column].sum()))} | "
                             f"{fmt_int(int((frame[column] > 0).sum()))} |")
            lines += ["", "| Best level of the dataset | Datasets | Share |", "| --- | ---: | ---: |"]
            best = frame[frame["q6_resources"] > 0]["q6_best_stars"].value_counts()
            for level in (3, 2, 1, 0):
                count = int(best.get(level, 0))
                lines.append(f"| {STARS[level]} | {fmt_int(count)} | {fmt_pct(count, n)} |")
            lines.append(f"| no resources | {fmt_int(no_resources)} | {fmt_pct(no_resources, n)} |")
            decided = Counter()
            for text in frame["q6_levels"]:
                for part in filter(None, (part.strip() for part in str(text).split(";"))):
                    count, _, reason = part.partition(" ")
                    decided[reason] += int(count)
            lines += ["", "| How the level of the resources was decided (most frequent) | Resources |", "| --- | ---: |"]
            for reason, count in decided.most_common(25):
                lines.append(f"| {md_cell(reason)} | {fmt_int(count)} |")
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
            score = row[f"{key}_score"]
            shown = "n/d" if pd.isna(score) else int(score)
            lines.append(f"| {row['sample_id']} | {link(row['title'], row['name'])} | "
                         f"{shown} | {md_cell(row[f'{key}_reason'])} |")
        counts = applicable[f"{key}_score"].value_counts()
        undetermined = int(applicable[f"{key}_score"].isna().sum())
        lines += ["", "Sample: " + ", ".join(
            f"{fmt_int(counts.get(s, 0))} dataset{'s' if counts.get(s, 0) != 1 else ''} with {s}" for s in (2, 1, 0))
            + (f", {undetermined} not determined" if undetermined else "") + "."]
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
    global REFERENCE_DATE
    REFERENCE_DATE = datetime.strptime(date, "%Y-%m-%d").date()
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
        if code == "Q6":
            note = f", not determined: {fmt_int(int(subset['q6_score'].isna().sum()))}"
        if code == "Q5":
            note = f", not measurable: {fmt_int(int(subset['q5_score'].isna().sum()))}"
        print(f"  {code} {name}: " + ", ".join(f"score {s}: {fmt_int(counts.get(s, 0))}" for s in (2, 1, 0)) + note)
    print("Files:")
    for path in (checks_file, out_dir / "summary.md", out_dir / "sample.md"):
        if path.exists():
            print(f"  {relative(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
