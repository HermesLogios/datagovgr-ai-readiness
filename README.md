# datagovgr-ai-readiness

Quality and AI-readiness assessment of the open datasets published on [data.gov.gr](https://data.gov.gr/), Greece's national open data portal.

Internship project of the MSc in Electronic Governance (University of the Aegean) at the Open Technologies Alliance (GFOSS / ΕΕΛΛΑΚ), supervised by Mr Alexandros Melidis. October – December 2026.

> **Περίληψη στα ελληνικά.** Μελέτη της ποιότητας και της ετοιμότητας για τεχνητή νοημοσύνη (ΤΝ) των ανοιχτών δεδομένων του data.gov.gr, στο πλαίσιο πρακτικής άσκησης του ΠΜΣ «Ηλεκτρονική Διακυβέρνηση» του Πανεπιστημίου Αιγαίου στην ΕΕΛΛΑΚ. Αξιολογούνται 36 σύνολα δεδομένων σε τρία επίπεδα (ποιότητα, μεταδεδομένα και νομικό καθεστώς, ετοιμότητα για ΤΝ), ελέγχεται η συμμόρφωση των συνόλων υψηλής αξίας με τον Κανονισμό (ΕΕ) 2023/138 και εντοπίζονται τα σύνολα που γίνονται «έτοιμα για ΤΝ» με μικρή προσπάθεια. Ο κώδικας, τα δεδομένα και κάθε απόφαση καταγράφονται σε αυτό το αποθετήριο, ώστε η εργασία να μπορεί να επαναληφθεί. Τα παραδοτέα προς τον επιβλέποντα συντάσσονται στα ελληνικά· το αποθετήριο τηρείται στα αγγλικά.

## Scope

- Assessment of a sample of 36 data.gov.gr datasets on three levels: data quality; metadata and legal status; AI-readiness.
- Compliance check of the high-value datasets against Implementing Regulation (EU) 2023/138.
- Identification of the datasets that can become "AI-ready" with little effort, and of the data missing from the portal.
- An open assessment tool (web app) that applies the same criteria to any dataset.

The methodology and every decision are recorded in this repository, so that the work can be reproduced or continued by others.

## Repository layout

| Folder or file | Content |
| --- | --- |
| `scripts/` | The scripts, numbered in the order they run (`00_`, `01_`, ...) |
| `data/raw/` | Raw data downloaded from the portal, unmodified |
| `data/processed/` | Processed tables and scores |
| `criteria/` | Assessment criteria (`criteria.csv`) |
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

## Licences

- **Code:** EUPL-1.2 (file `LICENSE`).
- **Data and results produced by the project:** CC BY 4.0 (file `LICENSE-DATA`).
- The original data.gov.gr datasets belong to the organisations that publish them and remain under their own licences.

## Status

Phase 1: catalogue snapshot and first profile (October 2026).

| Script | Function | Output |
| --- | --- | --- |
| `00_check_setup.py` | Environment check and first exploration of the API | `data/raw/api_probe_YYYY-MM-DD.json` |
| `01_snapshot.py` | Snapshot of the complete catalogue | `data/raw/catalog_YYYY-MM-DD.jsonl.gz` and `.manifest.json` |
| `02_catalog_profile.py` | Catalogue profile: one row per dataset and summary tables | `data/processed/catalog_flat_YYYY-MM-DD.csv` and `outputs/profile_YYYY-MM-DD/` |
