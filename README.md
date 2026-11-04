# datagovgr-ai-readiness

Quality and AI-readiness assessment of the open datasets published on [data.gov.gr](https://data.gov.gr/), Greece's national open data portal.

Internship project of the MSc in Electronic Governance (University of the Aegean) at the Open Technologies Alliance (GFOSS / ΕΕΛΛΑΚ), supervised by Mr Alexandros Melidis. October – December 2026.

> **Περίληψη στα ελληνικά.** Μελέτη της ποιότητας και της ετοιμότητας για τεχνητή νοημοσύνη (ΤΝ) των ανοιχτών δεδομένων του data.gov.gr, στο πλαίσιο πρακτικής άσκησης του ΠΜΣ «Ηλεκτρονική Διακυβέρνηση» του Πανεπιστημίου Αιγαίου στην ΕΕΛΛΑΚ. Αξιολογούνται 36 σύνολα δεδομένων σε τρία επίπεδα (ποιότητα, μεταδεδομένα και νομικό καθεστώς, ετοιμότητα για ΤΝ), ελέγχεται η συμμόρφωση των συνόλων υψηλής αξίας με τον Κανονισμό (ΕΕ) 2023/138 και εντοπίζονται τα σύνολα που γίνονται «έτοιμα για ΤΝ» με μικρή προσπάθεια. Ο κώδικας, τα δεδομένα και κάθε απόφαση καταγράφονται σε αυτό το αποθετήριο, ώστε η εργασία να μπορεί να επαναληφθεί. Τα παραδοτέα προς τον επιβλέποντα συντάσσονται στα ελληνικά· το αποθετήριο τηρείται στα αγγλικά.

## Scope

- Assessment of a sample of 36 data.gov.gr datasets on three levels: data quality; metadata and legal status; AI-readiness.
- Compliance check of the high-value datasets against Implementing Regulation (EU) 2023/138, reported separately from the scores as a compliance table (yes or no for each requirement).
- Identification of the datasets that can become "AI-ready" with little effort, and of the data missing from the portal.
- An open assessment tool that applies the same criteria to any dataset: at minimum a command-line run for one dataset; a web application if time allows.

The methodology and every decision are recorded in this repository, so that the work can be reproduced or continued by others.

## Limitations

- The sample is selected by page views, so it leans towards the better-maintained datasets and its picture of the portal is likely more favourable than the whole catalogue. The automated checks on the whole catalogue are reported next to the sample as the counterweight (DECISIONS.md #27).
- The results describe the catalogue at the dates of the snapshots (24 October and 25 November 2026); the base figure is the 22,805 datasets of the first snapshot (DECISIONS.md #26).
- Datasets that appear to contain personal data are recorded as findings without reproducing any record (DECISIONS.md #29).

## Repository layout

| Folder or file | Content |
| --- | --- |
| `scripts/` | The scripts of the analysis, numbered in the order they run (`00_`, `01_`, ...), and helper scripts without a number |
| `data/raw/` | Raw data downloaded from the portal, unmodified |
| `data/processed/` | Processed tables and scores |
| `data/reference/` | Reference lists used by the checks, e.g. the EU file-type vocabulary, with their source and date |
| `criteria/` | Assessment criteria (`criteria.csv`) and manual classification of high-value content (`hvd_by_content.csv`) |
| `outputs/` | Tables, charts, Croissant files, RAG collection |
| `DECISIONS.md` | Decision log, with date and rationale |
| `requirements.txt` | Python libraries, with pinned versions |

## How to run (Windows, PowerShell)

```powershell
git clone <repository address>
cd datagovgr-ai-readiness
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONUTF8 = "1"
python scripts\00_check_setup.py
```

On Linux or macOS use `python3 -m venv .venv` and `source .venv/bin/activate`; the other commands are the same.

The published results can be reproduced from the stored snapshot. `01_snapshot.py` is skipped, because it downloads a new snapshot of the current catalogue:

```powershell
python scripts\02_catalog_profile.py --snapshot data\raw\catalog_2026-10-24.jsonl.gz
python scripts\03_sample.py --flat data\processed\catalog_flat_2026-10-24.csv --force
python scripts\04_metadata_checks.py --snapshot data\raw\catalog_2026-10-24.jsonl.gz
git status
```

If the results are identical to the published ones, `git status` shows no changed files.

## Licences

- **Code:** EUPL-1.2 (file `LICENSE`).
- **Data and results produced by the project:** CC BY 4.0 (file `LICENSE-DATA`).
- The original data.gov.gr datasets belong to the organisations that publish them and remain under their own licences.

## Status

Phases 1 and 2 (catalogue snapshot, first profile, selection of the sample and assessment criteria) are complete. Phase 3, the assessment, is in progress: the automated checks of the metadata are complete for the whole catalogue (`04_metadata_checks.py`, all the criteria that the metadata allow, each rule approved and its proposed scores examined on the 36 datasets of the sample); the checks of the files of the sample and the manual criteria follow (November 2026).

| Script | Function | Output |
| --- | --- | --- |
| `00_check_setup.py` | Environment check and first exploration of the API | `data/raw/api_probe_YYYY-MM-DD.json` |
| `01_snapshot.py` | Snapshot of the complete catalogue | `data/raw/catalog_YYYY-MM-DD.jsonl.gz` and `.manifest.json` |
| `02_catalog_profile.py` | Catalogue profile: one row per dataset and summary tables | `data/processed/catalog_flat_YYYY-MM-DD.csv` and `outputs/profile_YYYY-MM-DD/` |
| `03_sample.py` | Selection of the 36 datasets of the sample: 24 high-value, 12 for comparison | `data/processed/sample.csv`, `sample_reserves.csv` and `outputs/sample_YYYY-MM-DD/` |
| `04_metadata_checks.py` | Automated checks of the metadata on the whole catalogue, with a proposed score and the reason for every dataset (M1, M2, M3, M4, M6, M7, M9, Q6 and the metadata part of Q5) | `data/processed/metadata_checks_YYYY-MM-DD.csv` and `outputs/checks_YYYY-MM-DD/` |
| `criteria_views.py` | Readable versions of the assessment criteria; run whenever `criteria/criteria.csv` changes | `criteria/criteria.xlsx` and `criteria/criteria.md` |
