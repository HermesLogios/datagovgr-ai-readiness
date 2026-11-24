# Assessment criteria

This folder holds the assessment grid and the manual classifications used in the project.

| File | Content |
| --- | --- |
| `criteria.csv` | The 23 criteria, with the point of the instructions that each one implements, the scoring rule for each score, the method of checking and the sources (source file) |
| `criteria.xlsx` | The same criteria as a formatted workbook, for reading |
| `criteria.md` | The same criteria as a document, one section per criterion, for reading online |
| `hvd_by_content.csv` | Datasets counted, or not counted, as high-value by content, with the reasons (DECISIONS.md #17) |
| `file_organisation.csv` | How the files of each dataset of the sample are organised (one file, the same data in several formats, a series of editions, parts of one edition, no data file) and which files are judged for the criteria of the files, starting with AI1 (DECISIONS.md #38) and Q2 (#39); for the datasets without a data file, the column `no_data_file` records what is published instead: documents, map images, or nothing available; the column `tables` records which files hold the same table, for the comparison of their columns under Q3 (#40): empty, all the data files hold the same table; `file name`, the files with the same name (the files of the GTFS feeds of a series); `cycle N`, the N resources of every edition, always in the same order; `resource`, every resource holds a table of its own; `one; apart NAME`, one table apart from the files named |
| `api_providers.csv` | Observations made by hand on the pages of the providers of an API whose documentation and terms of use are not part of the answer of the service itself: for the DataStore of the portal, whether a page documents the API and whether terms of use of the API are published, with their addresses and the date of the check; read by `07_api_checks.py` for M10 (DECISIONS.md #45) |
| `field_descriptions.csv` | The meaning of every column of the examined files of the datasets whose documentation explains every column (AI2 score 2, DECISIONS.md #46), one row per column, in the words of the documentation of the publisher and with its source; read by `10_croissant_checks.py`, which writes the meanings in the Croissant descriptions of the datasets (criterion AI4); the columns of the GTFS feeds are not listed, since the description of each one points to the GTFS reference |
| `sample_scores.csv` | The scores that the reviewer gave to the datasets of the sample, one row per dataset and criterion, with the decision of `DECISIONS.md` that records each one: the 14 criteria judged on the files, the documentation and the pages of the publishers (Q1 to Q4, M5, M8, M10, AI1 to AI7) and the automated scores that the download test corrected (M6, Q6); read by `13_assessment.py`, which takes the other scores from the table of `04_metadata_checks.py` |
| `sample_effort.csv` | The effort of the fix of a score below 2, where the criterion names two levels or the dataset needs another level than the usual one, with the decision that records it; read by `13_assessment.py` |
| `hvd_marking.csv` | The judgement of the reviewer on the marking of the 24 datasets of the high-value group of the sample: whether the content of each dataset corresponds to a dataset of the Annex of Implementing Regulation (EU) 2023/138 (yes, no or doubtful), the point of the Annex, the category of the content and whether the declared category is the right one, with the reason (DECISIONS.md #58); read by `14_hvd_compliance.py` |
| `hvd_annex_items.csv` | The 66 datasets that the Annex of Regulation (EU) 2023/138 names, by point of the Annex, with the patterns that search them in the catalogue; read by `16_hvd_annex_coverage.py` |
| `hvd_annex_coverage.csv` | The judgement of the reviewer on whether each dataset of the Annex is on the portal (present, partly or missing), with the datasets that show it and the reason (DECISIONS.md #61); read by `16_hvd_annex_coverage.py` |
| `hvd_broad_reading_check.csv` | The judgement of 30 map layers drawn at random for the check of the rule of part 4b (both readings, broad reading only or neither), with the reason (DECISIONS.md #62); read by `17_hvd_broad_reading.py` |

`criteria.csv` is the source. The workbook and the document are generated from it with `python scripts\criteria_views.py` and are not edited by hand: a change is made in the CSV file and the script is run again. Excel with Greek regional settings expects semicolons in CSV files and shows a comma-separated file in a single column, so the workbook is the convenient way to read the criteria in Excel.

## The grid

The criteria are grouped in three levels, following the instructions of the supervisor:

| Level | Criteria | IDs |
| --- | --- | --- |
| Quality | 6 | Q1-Q6 |
| Metadata and legal status | 10 | M1-M10 |
| AI-readiness | 7 | AI1-AI7 |

M9 and M10 apply only to the high-value datasets.

The column `instruction` states the point of the written instructions of the supervisor (18 October 2026) that each criterion implements. Fifteen criteria implement points of the instructions; the other eight are marked as additions, followed by the source from which they were added.

The columns `mqa_datagovgr` and `mqa_dataeuropa` name the indicators of the Metadata Quality Assessment (MQA) that check the same aspect as each criterion. The national portal monitors the quality of metadata with the MQA and the 5-star scale (Circular 24849/2026, section 1.5).

- `mqa_datagovgr`: the previous methodology of data.europa.eu (405 points, five dimensions), which data.gov.gr applied at the time of the snapshot. Nine criteria have such indicators.
- `mqa_dataeuropa`: the current methodology of data.europa.eu (DCAT-AP 3, a score from 0 to 7.5 for each dataset, distribution and data service). Fourteen criteria have such indicators.

Almost all of these indicators check only the presence of a property. "None" marks a criterion that the MQA does not cover: by its own description, the MQA does not assess the quality, correctness or completeness of the data themselves.

## Scoring rules

- **Scale.** Each criterion is scored 0 (not met), 1 (partly met) or 2 (fully met), following the rule written in `criteria.csv`. A score of "n/a" is allowed only where the column `not_applicable` says so.
- **Evidence.** Every score comes with one sentence that states what was observed. Where a script suggests a score, the suggestion is confirmed or corrected, and a correction states the reason.
- **Datasets with several resources.** The metadata criteria are checked on all resources. For the criteria on the content of the data, the files that are judged are recorded in `file_organisation.csv`: AI1, Q2 and AI5 judge the single data file, the best one of the same data in several formats, the latest edition of a series and the worst one of the parts of an edition (in Q2 the parts of an edition count together and the most complete format counts); Q3, Q4 and AI6 examine all the data files of the dataset.
- **Effort.** For every score below 2 the effort of the fix is recorded: low (metadata and documentation only), medium (a change in the file itself) or high (a change in a system or in the source of the data). The column `typical_fix` gives the usual case; the recorded effort may differ when the dataset requires it.

## Thresholds

The numeric thresholds of the rules are choices of the project: the sources define what is measured, not the level that is sufficient. They are:

- Q2: 5% and 20% of empty cells.
- Q4: 1% of implausible values, and a manual review of 10 records.
- Q5: one period of tolerance, one to three periods of delay, and 12 months for datasets without a declared frequency.
- M1: a description of at least 100 characters.
- M2: six or seven, and three to five, of the seven recommended properties.
- Q6: the correspondence of the 5-star scale to the scores.

They were stated before the assessment, together with the core criteria and the rule of the groups (DECISIONS.md #22), and none of them was changed. One threshold was added with the rules of its criterion, before its check: in AI3 a series has at least three periods or versions, and two alone score 1 (DECISIONS.md #47).

## Results

- **Score per level.** The sum of the scores divided by the maximum possible score (2 for each applicable criterion), as a percentage. The three levels are reported separately and are not combined into one number, so that the weak points of each dataset remain visible.
- **Groups.** Six core criteria decide the group of each dataset: Q1 availability, Q6 format, M1 mandatory metadata, M4 licence, AI1 machine-readable structure and AI2 documentation of the structure.
  - **Ready:** all core criteria score 2.
  - **Almost ready:** every core criterion below 2 can be fixed with low effort. These datasets are the candidates for the "Data for AI" section of the portal.
  - **Not yet:** at least one core criterion below 2 needs medium or high effort.

## Versions

Version 1 of the criteria was written on 27 October 2026. Version 1.1, of 29 October 2026, adds the columns `instruction`, `mqa_datagovgr` and `mqa_dataeuropa` and further sources, and clarifies M2 and M10 (DECISIONS.md #21). Version 1.2, of 16 November 2026, writes into the criteria the rules under which each criterion was applied to the sample (DECISIONS.md #52): the column `how_to_check` of all 23 criteria states them in short and names the decisions that record them in full, and the wording of some scores and of the column `not_applicable` follows them. The rules of each criterion were written and approved before its check, applied to the 36 datasets of the sample and fixed with the review of that criterion (DECISIONS.md #23 to #51); this took the place of the test on three datasets that had been planned. No score of the sample changes with version 1.2. Version 1.3, of 22 November 2026, adds to Q6 the rule for a file that the portal has also loaded in its DataStore (DECISIONS.md #56): it raises the Q6 score of three datasets of the sample from 1 to 2 and the level of 609 datasets of the catalogue from 2 to 3 stars. The core criteria and the rule of the groups were fixed before any dataset was scored and have not changed.

## Main sources

- ISO/IEC 25012:2008, Data quality model.
- W3C (2017), Data on the Web Best Practices (BP1-BP35).
- Berners-Lee, 5-star Open Data.
- SEMIC, DCAT-AP 3.0.1 (2025) and DCAT-AP HVD.
- Directive (EU) 2019/1024 on open data; Implementing Regulation (EU) 2023/138 on high-value datasets.
- Ministerial Decision 11654/2026 and Circular 24849/2026 of the Ministry of Digital Governance.
- data.europa.eu, Metadata Quality Assessment (MQA), current and previous methodology (columns `mqa_datagovgr` and `mqa_dataeuropa`).
- Publications Office of the European Union (2021), data.europa.eu data quality guidelines, doi:10.2830/79367.
- Wilkinson et al. (2016), The FAIR Guiding Principles (column `fair`).
- MLCommons, Croissant 1.0 (AI2) and 1.1 (AI4); Gebru et al. (2021), Datasheets for Datasets.
- Government Digital Service (2026), Guidelines and best practices for making government datasets ready for AI.
- Wickham (2014), Tidy Data.
