# Assessment criteria

> Generated from `criteria.csv` by `scripts/criteria_views.py`. Changes are made in `criteria.csv`; this file is not edited by hand.

Each criterion is scored 0 (not met), 1 (partly met) or 2 (fully met). The core criteria (Q1, Q6, M1, M4, AI1, AI2) decide the group of each dataset; the rules are in [README.md](README.md).

## Overview

| ID | Criterion | Level | Core | Method |
| --- | --- | --- | --- | --- |
| [Q1](#q1-availability) | Availability | Quality | yes | automatic, confirmed manually |
| [Q2](#q2-completeness) | Completeness | Quality |  | automatic for machine-readable files; manual otherwise |
| [Q3](#q3-consistency) | Consistency | Quality |  | semi-automatic |
| [Q4](#q4-plausibility-of-values) | Plausibility of values | Quality |  | semi-automatic |
| [Q5](#q5-timeliness) | Timeliness | Quality |  | semi-automatic |
| [Q6](#q6-format-5-star-scale) | Format (5-star scale) | Quality | yes | automatic, confirmed manually |
| [M1](#m1-mandatory-metadata) | Mandatory metadata | Metadata and legal status | yes | automatic, confirmed manually |
| [M2](#m2-recommended-metadata) | Recommended metadata | Metadata and legal status |  | automatic |
| [M3](#m3-controlled-vocabularies) | Controlled vocabularies | Metadata and legal status |  | automatic |
| [M4](#m4-licence) | Licence | Metadata and legal status | yes | automatic, confirmed manually |
| [M5](#m5-free-access) | Free access | Metadata and legal status |  | manual |
| [M6](#m6-mode-of-distribution) | Mode of distribution | Metadata and legal status |  | automatic, confirmed manually |
| [M7](#m7-persistent-identifier) | Persistent identifier | Metadata and legal status |  | automatic, confirmed manually |
| [M8](#m8-personal-data) | Personal data | Metadata and legal status |  | manual |
| [M9](#m9-high-value-designation) | High-value designation | Metadata and legal status |  | automatic |
| [M10](#m10-api-and-bulk-download) | API and bulk download | Metadata and legal status |  | semi-automatic |
| [AI1](#ai1-machine-readable-structure) | Machine-readable structure | AI-readiness | yes | semi-automatic |
| [AI2](#ai2-documentation-of-the-structure) | Documentation of the structure | AI-readiness | yes | manual |
| [AI3](#ai3-historical-depth) | Historical depth | AI-readiness |  | manual |
| [AI4](#ai4-description-in-croissant-or-a-datasheet) | Description in Croissant or a datasheet | AI-readiness |  | semi-automatic |
| [AI5](#ai5-suitability-for-retrieval-rag) | Suitability for retrieval (RAG) | AI-readiness |  | manual |
| [AI6](#ai6-linkage-through-common-identifiers) | Linkage through common identifiers | AI-readiness |  | semi-automatic |
| [AI7](#ai7-declared-limitations) | Declared limitations | AI-readiness |  | manual |

## Quality

### Q1 Availability

*Level: Quality · core criterion · applies to all datasets*

**Question.** Can the dataset's own resources be downloaded and opened?

| Score | Rule |
| --- | --- |
| 0 | No resource can be downloaded or opened. |
| 1 | At least one resource can be downloaded and opened, but at least one other fails (broken link, error page, empty or wrong file). |
| 2 | Every resource can be downloaded and opens without error. |

**How to check** (automatic, confirmed manually). Download test of every resource except the portal's 'download all' bundle, repeated on a second day before a failure is recorded (fact sheet). A link that leads to a web page instead of the declared file counts as a failure.

**Typical fix.** Low: correct the link. Medium: restore or upload the file again.

**Sources.** ISO/IEC 25012:2008 (availability) · **FAIR:** A1

### Q2 Completeness

*Level: Quality · applies to all datasets*

**Question.** How many values are missing?

| Score | Rule |
| --- | --- |
| 0 | More than 20% of the cells are empty, or no file can be opened. |
| 1 | 5-20% of the cells are empty, or at least one column is entirely empty. |
| 2 | Less than 5% of the cells are empty and no column is entirely empty. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (automatic for machine-readable files; manual otherwise). Share of empty cells in the most recent machine-readable file (fact sheet). Placeholders such as '-', 'N/A' or '..' count as empty. For data published only as documents (e.g. tables in PDF), estimated by inspection.

**Typical fix.** Medium: complete the file or state why values are missing.

**Sources.** ISO/IEC 25012:2008 (completeness) · **FAIR:** R1

### Q3 Consistency

*Level: Quality · applies to all datasets*

**Question.** Are the values recorded in the same way throughout the dataset?

| Score | Rule |
| --- | --- |
| 0 | Inconsistencies that prevent analysis without manual work (e.g. values shifted between columns, different units mixed in one column), or no file can be opened. |
| 1 | Minor inconsistencies: mixed date or number formats in a column, numbers stored as text, different column names or order between files of the same dataset. |
| 2 | Each column has one type, format and unit, and all files of the dataset share the same structure. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (semi-automatic). Column types and formats (fact sheet); comparison of the headers of the files of the dataset; inspection of a sample of rows.

**Typical fix.** Medium: harmonise the files.

**Sources.** ISO/IEC 25012:2008 (consistency); W3C Data on the Web Best Practices (2017), BP13 · **FAIR:** R1.3

### Q4 Plausibility of values

*Level: Quality · applies to all datasets*

**Question.** Are the values plausible?

| Score | Rule |
| --- | --- |
| 0 | Systematic errors: coordinates outside Greece or in an undeclared reference system, dates in the future, values in the wrong columns; or no file can be opened. |
| 1 | Isolated implausible values (fewer than 1% of the records), e.g. negative counts or outliers that look like typing errors. |
| 2 | No implausible values in the automatic checks and in a manual review of 10 random records. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (semi-automatic). Range checks (fact sheet): coordinates, dates, negative values, duplicates; review of 10 random records; comparison with the publisher's website where the same figures appear. Accuracy against reality cannot be verified in general, so the criterion records plausibility.

**Typical fix.** Medium: correct the values. High: correct the source system.

**Sources.** ISO/IEC 25012:2008 (accuracy) · **FAIR:** R1

### Q5 Timeliness

*Level: Quality · applies to all datasets*

**Question.** Is the dataset updated as often as its metadata declare?

| Score | Rule |
| --- | --- |
| 0 | The newest data are older than three update periods, or no frequency is declared and there has been no update for more than 12 months. |
| 1 | The newest data are one to three periods late, or no frequency is declared but the dataset was updated in the last 12 months. |
| 2 | Updated within the declared frequency (with one period of tolerance), or declared as not updated (one-off or historical data) with a description that says so. |

**How to check** (semi-automatic). Declared update frequency (metadata) against the date of the newest data: the latest date inside the data where there is one, otherwise the modification date of the newest resource.

**Typical fix.** Low: declare the actual frequency. High: set up regular updates.

**Sources.** ISO/IEC 25012:2008 (currentness); W3C Data on the Web Best Practices (2017), BP21; DCAT-AP 3.0.1 (frequency) · **FAIR:** R1

### Q6 Format (5-star scale)

*Level: Quality · core criterion · applies to all datasets*

**Question.** What is the most open format in which the data are offered?

| Score | Rule |
| --- | --- |
| 0 | Only unstructured formats (PDF, word-processor documents, images, web pages) or map views without data (WMS): 1 star. |
| 1 | Structured but vendor-specific formats (XLS, XLSX, SHP, MDB) or vendor-specific services (Esri REST): 2 stars. |
| 2 | At least one open, non-proprietary structured format (CSV, JSON, GeoJSON, XML, GML, KML, GeoPackage, GeoTIFF, NetCDF, RDF) or a download service in such a format (WFS, API): 3 stars or more. |

**How to check** (automatic, confirmed manually). Formats of the resources (fact sheet), checked against the actual content of the files: a file declared as CSV that is in fact a PDF counts as PDF.

**Typical fix.** Medium: publish an open format next to the existing one.

**Sources.** 5-star Open Data (Berners-Lee); W3C Data on the Web Best Practices (2017), BP12 and BP14; Directive (EU) 2019/1024, Art. 5 · **FAIR:** I1

## Metadata and legal status

### M1 Mandatory metadata

*Level: Metadata and legal status · core criterion · applies to all datasets*

**Question.** Are the metadata that DCAT-AP makes mandatory present and meaningful?

| Score | Rule |
| --- | --- |
| 0 | A mandatory element is missing: title, description, or an access URL for a resource. |
| 1 | All are present, but the description repeats the title or is shorter than 100 characters. |
| 2 | Title, a meaningful description (at least 100 characters, saying what the data contain) and an access URL for every resource. |

**How to check** (automatic, confirmed manually). Portal metadata (fact sheet): title, length of the description, access URL of each resource. Whether the description is meaningful is confirmed by reading it.

**Typical fix.** Low: complete the metadata.

**Sources.** DCAT-AP 3.0.1 (mandatory properties of Dataset and Distribution); Ministerial Decision 11654/2026 · **FAIR:** F2

### M2 Recommended metadata

*Level: Metadata and legal status · applies to all datasets*

**Question.** How many of seven descriptive metadata are present: keyword, theme, publisher, contact point, geographical coverage, temporal coverage, update frequency?

| Score | Rule |
| --- | --- |
| 0 | Two or fewer. |
| 1 | Three to five. |
| 2 | Six or seven. |

**How to check** (automatic). Portal metadata (fact sheet). The first six are recommended properties of DCAT-AP; the update frequency is optional in DCAT-AP and is checked because the assessment of timeliness (Q5) depends on it.

**Typical fix.** Low: complete the metadata.

**Sources.** DCAT-AP 3.0.1; W3C Data on the Web Best Practices (2017), BP1 and BP2; Circular 24849/2026 · **FAIR:** F2

### M3 Controlled vocabularies

*Level: Metadata and legal status · applies to all datasets*

**Question.** Are theme, file format and update frequency given with terms of the controlled vocabularies?

| Score | Rule |
| --- | --- |
| 0 | None of them. |
| 1 | Some of them; the rest are free text. |
| 2 | All of those present use controlled vocabularies. |

**How to check** (automatic). DCAT export of the dataset (data.gov.gr/dataset/&lt;name&gt;.jsonld): theme from the EU data-theme vocabulary, format from the EU file-type vocabulary or the IANA media types, frequency from the EU frequency vocabulary.

**Typical fix.** Low: select the terms from the vocabularies.

**Sources.** DCAT-AP 3.0.1 (controlled vocabularies); W3C Data on the Web Best Practices (2017), BP15 · **FAIR:** I2

### M4 Licence

*Level: Metadata and legal status · core criterion · applies to all datasets*

**Question.** Is an open licence declared clearly for all resources?

| Score | Rule |
| --- | --- |
| 0 | No licence, or a licence that restricts re-use (non-commercial, no derivatives, permission required). |
| 1 | An open licence, but not declared for every resource, given only as text without a link, conflicting between resources, or more restrictive than CC BY 4.0 (e.g. share-alike). |
| 2 | Every resource carries, directly or through the dataset, the link of CC0, CC BY 4.0 or an equivalent or less restrictive open licence. |

**How to check** (automatic, confirmed manually). Licence of the dataset and of each resource in the portal metadata; in case of conflict, the terms on the publisher's website.

**Typical fix.** Low: declare the licence in the metadata.

**Sources.** Directive (EU) 2019/1024, Art. 8; Regulation (EU) 2023/138, Art. 4; Ministerial Decision 11654/2026, Art. 8; W3C Data on the Web Best Practices (2017), BP4 · **FAIR:** R1.1

### M5 Free access

*Level: Metadata and legal status · applies to all datasets*

**Question.** Can the data be obtained free of charge and without registration?

| Score | Rule |
| --- | --- |
| 0 | A charge applies, or access requires an account that is not open to everyone. |
| 1 | Free of charge, but registration, an API key or acceptance of additional terms is required. |
| 2 | Free of charge and without registration. |

**How to check** (manual). During the download test and on the publisher's pages linked from the dataset.

**Typical fix.** High: change of the access policy.

**Sources.** Directive (EU) 2019/1024, Art. 6 and Art. 14; Ministerial Decision 11654/2026, Art. 8 · **FAIR:** A1

### M6 Mode of distribution

*Level: Metadata and legal status · applies to all datasets*

**Question.** How are the data made available, in the order of preference of the Ministerial Decision: API, direct link, structured file, unstructured file?

| Score | Rule |
| --- | --- |
| 0 | Only through a web page or an application without download, or no working access. |
| 1 | Files that do not give the complete data through a direct link: split into many parts, or reachable only through an intermediate page, form or map viewer. |
| 2 | An API, or a stable direct link to the complete data. |

**How to check** (automatic, confirmed manually). Type and address of each resource (fact sheet): API or download service; direct download link; landing page or viewer.

**Typical fix.** Medium: publish a direct link to the complete data. High: build an API.

**Sources.** Ministerial Decision 11654/2026, Art. 5; W3C Data on the Web Best Practices (2017), BP17 and BP23 · **FAIR:** A1

### M7 Persistent identifier

*Level: Metadata and legal status · applies to all datasets*

**Question.** Do the dataset and its resources have stable identifiers?

| Score | Rule |
| --- | --- |
| 0 | No stable address: the dataset or its resources are reachable only through temporary or session-based links. |
| 1 | The dataset has a stable address, but its resources point to links that change (new address with every upload, query or session parameters). |
| 2 | The dataset has a stable URI and identifier, and its resources have stable links. |

**How to check** (automatic, confirmed manually). URI and identifier of the dataset in the DCAT export; addresses of the resources (fact sheet).

**Typical fix.** Low: assign stable addresses.

**Sources.** W3C Data on the Web Best Practices (2017), BP9 and BP10; DCAT-AP 3.0.1 (identifier) · **FAIR:** F1

### M8 Personal data

*Level: Metadata and legal status · applies to all datasets*

**Question.** Does the dataset avoid exposing personal data?

| Score | Rule |
| --- | --- |
| 0 | Personal data of natural persons (names, identity or tax numbers, home addresses, personal contact details) are published without a stated legal basis. |
| 1 | Indirect identification is possible (e.g. very small counts, exact locations linked to individuals) and the dataset does not state how it was anonymised. |
| 2 | No personal data; or personal data published under a legal obligation that the metadata state; or data aggregated or anonymised, as stated. |

**How to check** (manual). Inspection of the columns and of 10 random records; description and documentation of the dataset.

**Typical fix.** Medium: remove or aggregate the fields.

**Sources.** Regulation (EU) 2016/679 (GDPR); Directive (EU) 2019/1024, Art. 1(4); Ministerial Decision 11654/2026, Art. 7

### M9 High-value designation

*Level: Metadata and legal status · applies to high-value datasets only*

**Question.** Do the metadata mark the dataset as high-value?

| Score | Rule |
| --- | --- |
| 0 | No marking: the dataset is high-value by content only. |
| 1 | Partial marking: the category without a reference to Regulation 2023/138, the reference without the category, or only the high-value dataset type. |
| 2 | High-value category and a reference to Regulation 2023/138 as applicable legislation. |
| n/a | Datasets of the comparison group. |

**How to check** (automatic). Fields hvd_category, applicable_legislation and dcat_type of the portal metadata.

**Typical fix.** Low: complete the metadata.

**Sources.** Regulation (EU) 2023/138, Art. 3; DCAT-AP HVD · **FAIR:** F2

### M10 API and bulk download

*Level: Metadata and legal status · applies to high-value datasets only*

**Question.** Is the dataset available both through an API and as a bulk download, as the Regulation requires?

| Score | Rule |
| --- | --- |
| 0 | Neither an API nor a bulk download of the complete dataset. |
| 1 | Only one of the two, or an API without public documentation and terms of use. |
| 2 | An API with public documentation and terms of use, and a bulk download of the complete dataset. |
| n/a | Datasets of the comparison group. |

**How to check** (semi-automatic). Data services of the portal linked to the dataset (access_services), services of the publisher, and download links of the complete data.

**Typical fix.** Medium: publish a complete download. High: build an API.

**Sources.** Regulation (EU) 2023/138, Art. 3 and Annex; W3C Data on the Web Best Practices (2017), BP17, BP23 and BP25 · **FAIR:** A1

## AI-readiness

### AI1 Machine-readable structure

*Level: AI-readiness · core criterion · applies to all datasets*

**Question.** Can a program read the data directly, without manual cleaning?

| Score | Rule |
| --- | --- |
| 0 | Not without manual work: PDF or scanned documents, images, spreadsheets laid out for printing (merged cells, several tables in one sheet), or no data file. |
| 1 | Readable after minor cleaning: title or note rows above the table, a totals row, numbers stored as text, a header split over two rows. |
| 2 | One header row, one record per row and one value per cell, without notes or totals inside the table; or a standard structured format (GeoJSON, JSON, XML) that is read without errors. |

**How to check** (semi-automatic). Automatic read test of the most recent machine-readable file (fact sheet), then a look at the file.

**Typical fix.** Medium: restructure the file.

**Sources.** W3C Data on the Web Best Practices (2017), BP12; GDS (2026), Guidelines and best practices for making government datasets ready for AI; Wickham (2014), Tidy Data · **FAIR:** I1

### AI2 Documentation of the structure

*Level: AI-readiness · core criterion · applies to all datasets*

**Question.** Is the meaning, type and unit of every field documented (data dictionary)?

| Score | Rule |
| --- | --- |
| 0 | No documentation: the meaning of the fields or codes has to be guessed. |
| 1 | Partial: the field names are clear but units or codes are not explained, or only some fields are documented. |
| 2 | Every field has a description, type and unit, and the codes are explained, in the metadata, in a data dictionary or on a page linked from the metadata. |

**How to check** (manual). Description, documentation resources and publisher pages linked from the dataset, compared with the columns of the file.

**Typical fix.** Low: write a data dictionary.

**Sources.** W3C Data on the Web Best Practices (2017), BP3; GDS (2026), Guidelines and best practices for making government datasets ready for AI; Gebru et al. (2021), Datasheets for Datasets; MLCommons Croissant 1.0 (RecordSet, Field) · **FAIR:** R1

### AI3 Historical depth

*Level: AI-readiness · applies to all datasets*

**Question.** Are earlier periods or versions of the data available?

| Score | Rule |
| --- | --- |
| 0 | Only the current state; earlier data have been replaced or removed. |
| 1 | Some earlier periods or versions, with gaps or in a different structure. |
| 2 | A continuous series of earlier periods or versions in the same structure. |
| n/a | The dataset describes a single fixed moment by design (e.g. a historical map) and is not updated. |

**How to check** (manual). Resources per period, temporal coverage in the metadata, archive pages of the publisher.

**Typical fix.** Medium: publish the archive.

**Sources.** W3C Data on the Web Best Practices (2017), BP7 and BP8; GDS (2026), Guidelines and best practices for making government datasets ready for AI · **FAIR:** R1

### AI4 Description in Croissant or a datasheet

*Level: AI-readiness · applies to all datasets*

**Question.** Can the dataset be described in Croissant, or with a datasheet, from the information available?

| Score | Rule |
| --- | --- |
| 0 | Neither: a licence or a machine-readable distribution is missing, and the documentation does not say what the data contain or how they were collected. |
| 1 | A valid Croissant description at dataset level only, without the fields, or a datasheet with major gaps. |
| 2 | A valid Croissant description that includes the fields with their types and meaning, or, for data without records, a datasheet that states what the data contain, how they were collected and for which uses they are suitable. |

**How to check** (semi-automatic). Croissant file generated from the portal metadata and the file structure and validated with the mlcroissant library; the fields are described with the information found under AI2.

**Typical fix.** Low: complete the metadata and the data dictionary.

**Sources.** MLCommons Croissant 1.0; Gebru et al. (2021), Datasheets for Datasets · **FAIR:** R1.3

### AI5 Suitability for retrieval (RAG)

*Level: AI-readiness · applies to all datasets*

**Question.** Can the content be split into self-contained pieces that an AI system can retrieve and cite?

| Score | Rule |
| --- | --- |
| 0 | Not usable: scanned images or maps without text, or no content that can be extracted. |
| 1 | Usable after conversion (text extraction from a born-digital PDF, flattening of a spreadsheet), or the pieces lack a stable identifier or a link to the source. |
| 2 | Records or text passages with a stable identifier and a link to the source, in text that is extracted cleanly in UTF-8, Greek included. |

**How to check** (manual). Text extraction test and check of the Greek encoding (fact sheet); presence of an identifier per record.

**Typical fix.** Medium: publish the content as structured text or records.

**Sources.** GDS (2026), Guidelines and best practices for making government datasets ready for AI (unstructured data); W3C Data on the Web Best Practices (2017), BP10 · **FAIR:** F1

### AI6 Linkage through common identifiers

*Level: AI-readiness · applies to all datasets*

**Question.** Can the data be joined with other datasets through common codes or coordinates?

| Score | Rule |
| --- | --- |
| 0 | No identifiers or location information that allow linkage. |
| 1 | Only names (e.g. municipality names) or codes internal to the publisher, or coordinates without a declared reference system. |
| 2 | Standard codes (e.g. municipality codes of the Kallikratis classification, NUTS or LAU codes, KAD/NACE activity codes, tax or GEMI numbers, KAEK cadastral codes) or coordinates in a declared reference system. |

**How to check** (semi-automatic). Column names and values (fact sheet); reference system of the geospatial files.

**Typical fix.** Medium: add the standard codes.

**Sources.** W3C Data on the Web Best Practices (2017), BP10 and BP15; FAIR I3 · **FAIR:** I3

### AI7 Declared limitations

*Level: AI-readiness · applies to all datasets*

**Question.** Do the metadata or the documentation state the known limitations of the data?

| Score | Rule |
| --- | --- |
| 0 | No statement about coverage, gaps, collection method or known errors. |
| 1 | A partial statement, e.g. only the source or only the coverage. |
| 2 | Coverage, gaps, collection method and known errors or changes of method are stated. |

**How to check** (manual). Description, documentation resources and linked publisher pages.

**Typical fix.** Low: add a short note on limitations.

**Sources.** Gebru et al. (2021), Datasheets for Datasets; GDS (2026), Guidelines and best practices for making government datasets ready for AI; W3C Data on the Web Best Practices (2017), BP6 · **FAIR:** R1.2
