"""Assessment of one dataset of data.gov.gr with the criteria of the study.

The package applies the metadata checks of the study to a single dataset, named by its name,
its identifier or its address on the portal, and reports the result. The scores are those of
scripts/04_metadata_checks.py; the criteria are read from criteria/criteria.csv.

Usage:
    python -m aiready troxaia-atyxhmata
    python -m aiready troxaia-atyxhmata --snapshot data/raw/catalog_2026-10-24.jsonl.gz
"""

__version__ = "0.1.0"
