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

Phases 1 and 2 (catalogue snapshot, first profile, selection of the sample and assessment criteria) are complete. Phase 3, the assessment, is in progress: the automated checks of the metadata are complete for the whole catalogue (`04_metadata_checks.py`, all the criteria that the metadata allow, each rule approved and its proposed scores examined on the 36 datasets of the sample); the files of the 36 datasets have been downloaded and tested (`05_resource_download.py`, Q1) and their examination with `06_file_checks.py` is complete for AI1, Q2, Q3, Q4 and AI6 (each rule approved before it was coded, the proposed scores reviewed one by one on the 36 datasets, the differences and the manual look at the records recorded in `DECISIONS.md` #38 to #42); the manual criteria (M5, M8, M10, AI2 to AI5, AI7), the assessment workbook and the table of compliance of the high-value datasets with Regulation (EU) 2023/138 follow (November 2026).

| Script | Function | Output |
| --- | --- | --- |
| `00_check_setup.py` | Environment check and first exploration of the API | `data/raw/api_probe_YYYY-MM-DD.json` |
| `01_snapshot.py` | Snapshot of the complete catalogue | `data/raw/catalog_YYYY-MM-DD.jsonl.gz` and `.manifest.json` |
| `02_catalog_profile.py` | Catalogue profile: one row per dataset and summary tables | `data/processed/catalog_flat_YYYY-MM-DD.csv` and `outputs/profile_YYYY-MM-DD/` |
| `03_sample.py` | Selection of the 36 datasets of the sample: 24 high-value, 12 for comparison | `data/processed/sample.csv`, `sample_reserves.csv` and `outputs/sample_YYYY-MM-DD/` |
| `04_metadata_checks.py` | Automated checks of the metadata on the whole catalogue, with a proposed score and the reason for every dataset (M1, M2, M3, M4, M6, M7, M9, Q6 and the metadata part of Q5) | `data/processed/metadata_checks_YYYY-MM-DD.csv` and `outputs/checks_YYYY-MM-DD/` |
| `05_resource_download.py` | Download test of every resource of the 36 datasets of the sample (criterion Q1); the files stay outside the repository, and the results depend on the day of the download, so they are not reproduced from the snapshot | `data/processed/resource_downloads_YYYY-MM-DD.csv` and `outputs/resources_YYYY-MM-DD/downloads.md` |
| `06_file_checks.py` | Examination of the downloaded files of the sample: read test of every data file and layout of every table (criterion AI1), the empty cells of the records (criterion Q2), the kinds and forms of the values of every column and the columns of the files of the same table (criterion Q3), and the plausibility of the values (criterion Q4: coordinates inside Greece, dates not after the download of the file, non-negative quantities, weather elements inside their physical range, duplicate records) and the identifiers and coordinates that allow linkage with other data (criterion AI6: standard codes such as KAEK, Kallikratis, NACE or GEMI, coordinates in a declared reference system), following the organisation of the files of each dataset in `criteria/file_organisation.csv`; the outputs contain no records of the data; a random sample of records for the manual look is written to a local review file in the folder `review`, which is not part of the repository | `data/processed/file_profiles_YYYY-MM-DD.csv`, `data/processed/file_columns_YYYY-MM-DD.csv`, `data/processed/file_formats_YYYY-MM-DD.csv`, `data/processed/file_structures_YYYY-MM-DD.csv`, `data/processed/file_plausibility_YYYY-MM-DD.csv`, `data/processed/file_keys_YYYY-MM-DD.csv`, `data/processed/file_checks_YYYY-MM-DD.csv` and `outputs/files_YYYY-MM-DD/` (summary and one fact sheet per dataset) |
| `criteria_views.py` | Readable versions of the assessment criteria; run whenever `criteria/criteria.csv` changes | `criteria/criteria.xlsx` and `criteria/criteria.md` |
