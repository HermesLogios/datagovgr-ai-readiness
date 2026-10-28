# Assessment criteria

This folder holds the assessment grid and the manual classifications used in the project.

| File | Content |
| --- | --- |
| `criteria.csv` | The 23 criteria, with the point of the instructions that each one implements, the scoring rule for each score, the method of checking and the sources (source file) |
| `criteria.xlsx` | The same criteria as a formatted workbook, for reading |
| `criteria.md` | The same criteria as a document, one section per criterion, for reading online |
| `hvd_by_content.csv` | Datasets counted, or not counted, as high-value by content, with the reasons (DECISIONS.md #17) |

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
- **Datasets with several resources.** The metadata criteria are checked on all resources. The criteria on the content of the data (Q2-Q4, AI1, AI5, AI6) are checked on the most recent machine-readable resource; where there is none, on the most recent resource.
- **Effort.** For every score below 2 the effort of the fix is recorded: low (metadata and documentation only), medium (a change in the file itself) or high (a change in a system or in the source of the data). The column `typical_fix` gives the usual case; the recorded effort may differ when the dataset requires it.

## Thresholds

The numeric thresholds of the rules are choices of the project: the sources define what is measured, not the level that is sufficient. They are:

- Q2: 5% and 20% of empty cells.
- Q4: 1% of implausible values, and a manual review of 10 records.
- Q5: one period of tolerance, one to three periods of delay, and 12 months for datasets without a declared frequency.
- M1: a description of at least 100 characters.
- M2: six or seven, and three to five, of the seven recommended properties.
- Q6: the correspondence of the 5-star scale to the scores.

Together with the core criteria and the rule of the groups, they are tested on three datasets with the wording of the rules, and fixed before the assessment of the full sample (DECISIONS.md #22).

## Results

- **Score per level.** The sum of the scores divided by the maximum possible score (2 for each applicable criterion), as a percentage. The three levels are reported separately and are not combined into one number, so that the weak points of each dataset remain visible.
- **Groups.** Six core criteria decide the group of each dataset: Q1 availability, Q6 format, M1 mandatory metadata, M4 licence, AI1 machine-readable structure and AI2 documentation of the structure.
  - **Ready:** all core criteria score 2.
  - **Almost ready:** every core criterion below 2 can be fixed with low effort. These datasets are the candidates for the "Data for AI" section of the portal.
  - **Not yet:** at least one core criterion below 2 needs medium or high effort.

## Versions

Version 1 of the criteria was written on 27 October 2026. Version 1.1, of 29 October 2026, adds the columns `instruction`, `mqa_datagovgr` and `mqa_dataeuropa` and further sources, and clarifies M2 and M10 (DECISIONS.md #21). The criteria are first applied to three datasets of the sample, to test whether the rules are clear and lead to the same score when applied twice. Changes to the wording after this test are recorded in DECISIONS.md, and the criteria are fixed before the assessment of the full sample. The core criteria and the rule of the groups do not change after the results are known.

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
- MLCommons, Croissant 1.0; Gebru et al. (2021), Datasheets for Datasets.
- Government Digital Service (2026), Guidelines and best practices for making government datasets ready for AI.
- Wickham (2014), Tidy Data.
