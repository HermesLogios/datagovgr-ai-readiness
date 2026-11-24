# datagovgr-ai-readiness

Quality and AI-readiness assessment of the open datasets published on [data.gov.gr](https://data.gov.gr/), Greece's national open data portal.

Internship project of the MSc in Electronic Governance (University of the Aegean) at the Open Technologies Alliance (GFOSS / ΕΕΛΛΑΚ), supervised by Mr Alexandros Melidis. October – December 2026.

> **Περίληψη στα ελληνικά.** Μελέτη της ποιότητας και της ετοιμότητας για τεχνητή νοημοσύνη (ΤΝ) των ανοιχτών δεδομένων του data.gov.gr, στο πλαίσιο πρακτικής άσκησης του ΠΜΣ «Ηλεκτρονική Διακυβέρνηση» του Πανεπιστημίου Αιγαίου στην ΕΕΛΛΑΚ. Αξιολογούνται 36 σύνολα δεδομένων σε τρία επίπεδα (ποιότητα, μεταδεδομένα και νομικό καθεστώς, ετοιμότητα για ΤΝ), ελέγχεται η συμμόρφωση των συνόλων υψηλής αξίας με τον Κανονισμό (ΕΕ) 2023/138 και εντοπίζονται τα σύνολα που γίνονται «έτοιμα για ΤΝ» με μικρή προσπάθεια. Το αποθετήριο περιέχει και εργαλείο αξιολόγησης, ως εντολή και ως δημόσια σελίδα, που εφαρμόζει σε οποιοδήποτε σύνολο της πύλης τους εννέα ελέγχους των μεταδεδομένων. Ο κώδικας, τα δεδομένα και κάθε απόφαση καταγράφονται σε αυτό το αποθετήριο, ώστε η εργασία να μπορεί να επαναληφθεί. Τα παραδοτέα προς τον επιβλέποντα συντάσσονται στα ελληνικά· το αποθετήριο τηρείται στα αγγλικά.

## Scope

- Assessment of a sample of 36 data.gov.gr datasets on three levels: data quality; metadata and legal status; AI-readiness.
- Compliance check of the high-value datasets against Implementing Regulation (EU) 2023/138, reported separately from the scores as a compliance table (yes or no for each requirement).
- Identification of the datasets that can become "AI-ready" with little effort, and of the data missing from the portal.
- An open assessment tool for any dataset of the portal, as a command and as a public page: it scores the nine criteria that the metadata decide and lists the other fourteen as a checklist (see [Assessment tool](#assessment-tool)).

The methodology and every decision are recorded in this repository, so that the work can be reproduced or continued by others.

## Limitations

- The sample is selected by page views, so it leans towards the better-maintained datasets and its picture of the portal is likely more favourable than the whole catalogue. The automated checks on the whole catalogue are reported next to the sample as the counterweight (DECISIONS.md #27).
- The results describe the catalogue at the dates of the snapshots (24 October and 25 November 2026); the base figure is the 22,805 datasets of the first snapshot (DECISIONS.md #26).
- Datasets that appear to contain personal data are recorded as findings without reproducing any record (DECISIONS.md #29).

## Repository layout

| Folder or file | Content |
| --- | --- |
| `scripts/` | The scripts of the analysis, numbered in the order they run (`00_`, `01_`, ...), and helper scripts without a number |
| `aiready/` | Library and command of the assessment tool |
| `web/` | Public page of the assessment tool, with its own `README.md` |
| `tests/` | Tests of the assessment tool |
| `assessments/` | Reports written by the command of the tool; they stay outside the repository |
| `data/raw/` | Raw data downloaded from the portal, unmodified |
| `data/processed/` | Processed tables and scores |
| `data/reference/` | Reference lists used by the checks, e.g. the EU file-type vocabulary, with their source and date |
| `criteria/` | Assessment criteria (`criteria.csv`), manual classification of high-value content (`hvd_by_content.csv`) and the scores given by the reviewer to the datasets of the sample (`sample_scores.csv`) |
| `outputs/` | Tables, charts, Croissant files, RAG collection |
| `DECISIONS.md` | Decision log, with date and rationale |
| `requirements.txt` | Python libraries, with pinned versions |

## How to run (Windows, PowerShell)

```powershell
git clone https://github.com/HermesLogios/datagovgr-ai-readiness.git
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

## Assessment tool

The tool applies the checks of `04_metadata_checks.py` to any dataset of the portal, given by its name, its identifier or its address. It scores the nine criteria that the metadata decide (M1, M2, M3, M4, M6, M7, M9, Q6 and the metadata part of Q5) and lists the other fourteen as a checklist without a score, because they need the files or judgement (`DECISIONS.md` #53).

```powershell
python -m aiready troxaia-atyxhmata
python -m aiready https://data.gov.gr/dataset/troxaia-atyxhmata --lang el --out assessments --format md json xlsx
python -m aiready troxaia-atyxhmata --snapshot data\raw\catalog_2026-10-24.jsonl.gz
```

The first command reads the metadata from the portal and prints the summary. `--lang` prints the summary in plain language, in Greek or English; `--out` writes a report per dataset; `--snapshot` reads the stored snapshot instead of the portal, which gives the scores of the published table.

The public page (`web/`) runs the same checks inside the browser of the visitor and explains every finding in plain Greek or English. `web/README.md` describes how the page is built and published; `python web\preview.py` serves it on the local computer. The tests of the tool run with `python -m unittest discover -s tests`.

On the page a visitor may also ask for a second reading of the description of a dataset by Jev, a model of TypeSafe AI, with a key of their own. The model answers five statements on what the description says, one for M1 and four for AI7, each with a probability. The reading gives no score and changes none, and it is not used in the study (`DECISIONS.md` #54). `python -m aiready.jev_trial` repeats the trial of the model on the 36 datasets of the sample; the answers of the trial of 18 November 2026 are kept in `data/processed/jev_trial_2026-11-18.json`.

## Licences

- **Code:** EUPL-1.2 (file `LICENSE`).
- **Data and results produced by the project:** CC BY 4.0 (file `LICENSE-DATA`).
- The original data.gov.gr datasets belong to the organisations that publish them and remain under their own licences.

## Status

Phases 1 and 2 (catalogue snapshot, first profile, selection of the sample and assessment criteria) are complete. Phase 3, the assessment, is in progress: the automated checks of the metadata are complete for the whole catalogue (`04_metadata_checks.py`, all the criteria that the metadata allow, each rule approved and its proposed scores examined on the 36 datasets of the sample); the files of the 36 datasets have been downloaded and tested (`05_resource_download.py`, Q1) and their examination with `06_file_checks.py` is complete for AI1, Q2, Q3, Q4 and AI6 (each rule approved before it was coded, the proposed scores reviewed one by one on the 36 datasets, the differences and the manual look at the records recorded in `DECISIONS.md` #38 to #42); of the manual criteria, M8 (personal data), M5 (free access), M10 (API and bulk download, tested with `07_api_checks.py`), AI2 (documentation of the structure, reviewed with the evidence of `08_documentation_checks.py`), AI3 (historical depth, reviewed with the evidence of `09_history_checks.py`), AI4 (description in Croissant or with a datasheet, reviewed with the evidence of `10_croissant_checks.py`), AI5 (suitability for retrieval, reviewed with the evidence of `11_retrieval_checks.py`) and AI7 (declared limitations, reviewed with the evidence of `12_limitation_checks.py`) are complete (`DECISIONS.md` #43 to #50); S17, whose listed resources deliver no data, was examined again on 16 criteria after its list was exported by hand from an application of its publisher (`DECISIONS.md` #51); version 1.2 of the criteria records the rules under which every criterion was applied (`DECISIONS.md` #52); the scores of the 36 datasets are assembled by `13_assessment.py` into the assessment workbook, with the score per level, the effort of the fix and the readiness group of every dataset (`DECISIONS.md` #55 to #57 and #59): 2 datasets are ready, 12 almost ready and 22 not yet; Q5 stays provisional until the second snapshot; the compliance of the high-value datasets with Regulation (EU) 2023/138 is reported separately by `14_hvd_compliance.py` (`DECISIONS.md` #58): the content of 12 of the 24 datasets of the high-value group is listed in the Annex of the Regulation, 6 are marked by their publishers without being listed and 6 are doubtful. The gaps of the sample and of the catalogue are counted by `15_gap_analysis.py` (`DECISIONS.md` #60): 313 of the 731 scores of the sample are below 2, 143 of them fixable with low effort, and eight datasets are one low-effort fix from the ready group. Of the 66 datasets that the Annex of the Regulation names, 20 are on the portal for the whole country, 33 in part and 13 are missing (`16_hvd_annex_coverage.py`, `DECISIONS.md` #61). The broad reading of point 2.1 of the Annex, which adds all the environmental information of Directive 2003/4/EC, would make 10,188 of the 11,938 map layers that the portal harvests from GIS servers high-value instead of 3,383, most of the difference being scans of single town-planning acts; the rule agrees with the check of 30 layers in 27 (`17_hvd_broad_reading.py`, `DECISIONS.md` #62). The assessment tool is available as a command and as a public page (`DECISIONS.md` #53).

| Script | Function | Output |
| --- | --- | --- |
| `00_check_setup.py` | Environment check and first exploration of the API | `data/raw/api_probe_YYYY-MM-DD.json` |
| `01_snapshot.py` | Snapshot of the complete catalogue | `data/raw/catalog_YYYY-MM-DD.jsonl.gz` and `.manifest.json` |
| `02_catalog_profile.py` | Catalogue profile: one row per dataset and summary tables | `data/processed/catalog_flat_YYYY-MM-DD.csv` and `outputs/profile_YYYY-MM-DD/` |
| `03_sample.py` | Selection of the 36 datasets of the sample: 24 high-value, 12 for comparison | `data/processed/sample.csv`, `sample_reserves.csv` and `outputs/sample_YYYY-MM-DD/` |
| `04_metadata_checks.py` | Automated checks of the metadata on the whole catalogue, with a proposed score and the reason for every dataset (M1, M2, M3, M4, M6, M7, M9, Q6 and the metadata part of Q5) | `data/processed/metadata_checks_YYYY-MM-DD.csv` and `outputs/checks_YYYY-MM-DD/` |
| `05_resource_download.py` | Download test of every resource of the 36 datasets of the sample (criterion Q1); the files stay outside the repository, and the results depend on the day of the download, so they are not reproduced from the snapshot | `data/processed/resource_downloads_YYYY-MM-DD.csv` and `outputs/resources_YYYY-MM-DD/downloads.md` |
| `06_file_checks.py` | Examination of the downloaded files of the sample: read test of every data file and layout of every table (criterion AI1), the empty cells of the records (criterion Q2), the kinds and forms of the values of every column and the columns of the files of the same table (criterion Q3), and the plausibility of the values (criterion Q4: coordinates inside Greece, dates not after the download of the file, non-negative quantities, weather elements inside their physical range, duplicate records) and the identifiers and coordinates that allow linkage with other data (criterion AI6: standard codes such as KAEK, Kallikratis, NACE or GEMI, coordinates in a declared reference system), following the organisation of the files of each dataset in `criteria/file_organisation.csv`; the outputs contain no records of the data; a random sample of records for the manual look is written to a local review file in the folder `review`, which is not part of the repository | `data/processed/file_profiles_YYYY-MM-DD.csv`, `data/processed/file_columns_YYYY-MM-DD.csv`, `data/processed/file_formats_YYYY-MM-DD.csv`, `data/processed/file_structures_YYYY-MM-DD.csv`, `data/processed/file_plausibility_YYYY-MM-DD.csv`, `data/processed/file_keys_YYYY-MM-DD.csv`, `data/processed/file_checks_YYYY-MM-DD.csv` and `outputs/files_YYYY-MM-DD/` (summary and one fact sheet per dataset) |
| `07_api_checks.py` | Test of the APIs of the high-value datasets of the sample (criterion M10): every DataStore table of the portal, WFS layer and ArcGIS service that the resources or the descriptions of a dataset declare is called anonymously and asked for its description and for the number of its records, which is compared with the downloaded file; with the bulk download of the download test, it proposes the score and fills the columns API, bulk download, and terms of use and documentation of the API of the compliance table; the answers depend on the day of the call | `data/processed/api_endpoints_YYYY-MM-DD.csv`, `api_checks_YYYY-MM-DD.csv` and `outputs/api_YYYY-MM-DD/` |
| `08_documentation_checks.py` | Evidence on the documentation of the structure of the datasets of the sample (criterion AI2): where the fields could be explained (descriptions, documents next to the data, pages of the publisher, declared standards), what the names of the columns show, the columns of the GTFS feeds against the GTFS reference, and the data dictionary of every DataStore table of the sample, asked from the portal without any record; it proposes a score only where a rule decides without judgement, and counts in the whole catalogue the datasets that fill a metadata field for documentation or for a standard (in the dataset, in a resource or among the additional metadata of the record) and those whose additional metadata list their columns | `data/processed/documentation_checks_YYYY-MM-DD.csv`, `datastore_dictionaries_YYYY-MM-DD.csv` and `outputs/documentation_YYYY-MM-DD/` |
| `09_history_checks.py` | Evidence on the historical depth of the datasets of the sample (criterion AI3): what the metadata say about time, the periods in the names of the resources and those missing among them, the periods inside the downloaded tables (dates, years and months, labels of two years, period names in the header), read without keeping any record, the comparison of the columns made by `06_file_checks.py`, and the other periods published as separate datasets of the same publisher; it proposes a score only where a rule decides without judgement | `data/processed/history_checks_YYYY-MM-DD.csv`, `history_series_YYYY-MM-DD.csv`, `history_siblings_YYYY-MM-DD.csv` and `outputs/history_YYYY-MM-DD/` |
| `10_croissant_checks.py` | A Croissant description of every dataset of the sample (criterion AI4), written only from the metadata of the portal and the tables of the earlier checks: the properties of the dataset as the Croissant profile of the software of the portal maps them, with the licence of the resources; the files that were obtained, with their address, media type, size and SHA-256; the columns of the examined tables as fields, with the type found by `06_file_checks.py` and, where the documentation gives it, their meaning (`criteria/field_descriptions.csv`, or the GTFS reference); every description is validated with the mlcroissant library; the portal is asked whether the Croissant plugin of its software is enabled; the whole catalogue is counted for the datasets whose metadata can fill each property of a description; it proposes a score only where a rule decides without judgement; the descriptions contain no records of the data | `data/processed/croissant_checks_YYYY-MM-DD.csv`, `croissant_catalogue_YYYY-MM-DD.csv`, `croissant_portal_YYYY-MM-DD.csv` and `outputs/croissant_YYYY-MM-DD/` (report and one description per dataset) |
| `11_retrieval_checks.py` | Evidence on the suitability of the datasets of the sample for retrieval (criterion AI5): which of the tables examined for AI1 can be split into records as they are, by the layout that `06_file_checks.py` recorded; in every such table, read again from the downloaded file, the cells whose text is damaged (a replacement character, characters of another encoding in the place of Greek letters, question marks in the place of letters) and an identifier of the records: a column, or the smallest combination of up to four columns, that is filled and different in every record, with the number of the row and the measures left aside; in the files of a GTFS feed the primary key of the GTFS reference, in an RDF file the URI of the subject; whether the text of the PDF documents among the files can be extracted; it proposes a score only where a rule decides without judgement; the outputs contain no value of a record | `data/processed/retrieval_checks_YYYY-MM-DD.csv`, `retrieval_tables_YYYY-MM-DD.csv` and `outputs/retrieval_YYYY-MM-DD/` |
| `12_limitation_checks.py` | Evidence on the limitations that the publishers declare for the datasets of the sample (criterion AI7): the texts in which a limitation could be stated (the description of the dataset, the descriptions of its resources that differ from the name of the resource, the documents among the resources, the pages of the publisher that the metadata link to, the fields on the origin of the data), with the words in them that point to a statement about what is missing, about the source or the method, about accuracy or errors; the pages of the PDF documents among the files on which the same words are found; next to them what the earlier checks found in the examined files (empty cells, implausible values, the period covered and the periods missing from it) and, in the examined GTFS feeds, the stop times that record a restriction on boarding or alighting; the whole catalogue is counted for the descriptions that are missing or only repeat the title, for the same words, for the fields on the origin of the data and for the datasets whose type is declared as synthetic data; it proposes a score only where a rule decides without judgement; the outputs contain no value of a record and, of the documents, only numbers of pages | `data/processed/limitation_checks_YYYY-MM-DD.csv`, `limitation_catalogue_YYYY-MM-DD.csv` and `outputs/limitations_YYYY-MM-DD/` |
| `13_assessment.py` | Assessment of the 36 datasets of the sample: the score of every dataset in each of the 23 criteria (the scores given by the reviewer in `criteria/sample_scores.csv`, otherwise the automated scores of `04_metadata_checks.py`), the score per level, the effort of the fix for every score below 2 and the readiness group from the six core criteria | `data/processed/assessment_YYYY-MM-DD.csv`, `assessment_scores_YYYY-MM-DD.csv` and `outputs/assessment_YYYY-MM-DD/` (summary and assessment workbook) |
| `14_hvd_compliance.py` | Compliance of the high-value datasets with Implementing Regulation (EU) 2023/138, reported separately from the scores: for the 24 datasets of the high-value group of the sample, the judgement of the reviewer on their marking (`criteria/hvd_marking.csv`: content in the Annex of the Regulation or not, and declared category) and the answer to every requirement (free of charge, open licence, API, bulk download, terms and documentation of the API, point of contact, marking, documentation of the structure), counted over the datasets whose content is in the Annex; for every dataset of the catalogue marked as high-value, the requirements that the metadata allow to check | `data/processed/hvd_compliance_YYYY-MM-DD.csv`, `hvd_compliance_catalogue_YYYY-MM-DD.csv` and `outputs/hvd_compliance_YYYY-MM-DD/` (summary and workbook) |
| `15_gap_analysis.py` | Gap analysis from the recorded scores, efforts of the fix and answers on compliance: the scores below 2 of every criterion in the sample with the effort of their fix, the same counts in the catalogue for the nine criteria that the metadata decide, what each dataset of the sample lacks for the ready group, and the requirements of Regulation (EU) 2023/138 that the high-value datasets of its Annex do not meet | `data/processed/gap_criteria_YYYY-MM-DD.csv`, `gap_catalogue_YYYY-MM-DD.csv`, `gap_datasets_YYYY-MM-DD.csv`, `gap_hvd_YYYY-MM-DD.csv` and `outputs/gap_analysis_YYYY-MM-DD/` (summary and workbook) |
| `16_hvd_annex_coverage.py` | Part 4 of the gap analysis: which datasets named by the Annex of Regulation (EU) 2023/138 are on the portal; searches the title, the description and the tags of every dataset and data service of the snapshot for the 66 datasets of `criteria/hvd_annex_items.csv` and reports the judgement of the reviewer (`criteria/hvd_annex_coverage.csv`) | `data/processed/hvd_annex_candidates_YYYY-MM-DD.csv`, `hvd_annex_coverage_YYYY-MM-DD.csv` and `outputs/hvd_annex_coverage_YYYY-MM-DD/` (summary and workbook) |
| `17_hvd_broad_reading.py` | Part 4b of the gap analysis: what the broad reading of point 2.1 of the Annex of Regulation (EU) 2023/138 would add to the high-value datasets; places each map layer harvested from GIS servers in a group (both readings, broad reading only, neither) by a rule on its title and the name of its source, and reports the agreement of the rule with the judgement of 30 layers drawn at random (`criteria/hvd_broad_reading_check.csv`) | `data/processed/hvd_broad_reading_YYYY-MM-DD.csv`, `hvd_broad_reading_sample_YYYY-MM-DD.csv` and `outputs/hvd_broad_reading_YYYY-MM-DD/summary.md` |
| `criteria_views.py` | Readable versions of the assessment criteria; run whenever `criteria/criteria.csv` changes | `criteria/criteria.xlsx` and `criteria/criteria.md` |
