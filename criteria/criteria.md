# Assessment criteria

> Generated from `criteria.csv` by `scripts/criteria_views.py`. Changes are made in `criteria.csv`; this file is not edited by hand.

Each criterion is scored 0 (not met), 1 (partly met) or 2 (fully met). The core criteria (Q1, Q6, M1, M4, AI1, AI2) decide the group of each dataset; the rules are in [README.md](README.md). The column Instruction gives the point of the written instructions of the supervisor that each criterion implements; 'Addition' marks a criterion added to those points, followed by its source. MQA names the indicators of the Metadata Quality Assessment that check the same aspect, in the previous methodology, applied by data.gov.gr, and in the current methodology of data.europa.eu; 'None' marks a criterion that no indicator covers.

## Overview

| ID | Criterion | Level | Core | Method | Instruction |
| --- | --- | --- | --- | --- | --- |
| [Q1](#q1-availability) | Availability | Quality | yes | automatic, confirmed manually | Addition: ISO/IEC 25012 (availability) |
| [Q2](#q2-completeness) | Completeness | Quality |  | automatic for machine-readable files; manual otherwise | Level (a): completeness |
| [Q3](#q3-consistency) | Consistency | Quality |  | semi-automatic | Level (a): consistency |
| [Q4](#q4-plausibility-of-values) | Plausibility of values | Quality |  | semi-automatic | Addition: ISO/IEC 25012 (accuracy) |
| [Q5](#q5-timeliness) | Timeliness | Quality |  | semi-automatic | Level (a): timeliness |
| [Q6](#q6-format-5-star-scale) | Format (5-star scale) | Quality | yes | automatic, confirmed manually | Level (a): format; 5-star scale |
| [M1](#m1-mandatory-metadata) | Mandatory metadata | Metadata and legal status | yes | automatic, confirmed manually | Level (b): DCAT-AP (mandatory properties) |
| [M2](#m2-recommended-metadata) | Recommended metadata | Metadata and legal status |  | automatic | Level (b): DCAT-AP (recommended properties) |
| [M3](#m3-controlled-vocabularies) | Controlled vocabularies | Metadata and legal status |  | automatic | Level (b): DCAT-AP (controlled vocabularies) |
| [M4](#m4-licence) | Licence | Metadata and legal status | yes | automatic, confirmed manually | Level (b): clarity of the licence; CC BY 4.0 or a more permissive licence |
| [M5](#m5-free-access) | Free access | Metadata and legal status |  | manual | Level (b): free of charge |
| [M6](#m6-mode-of-distribution) | Mode of distribution | Metadata and legal status |  | automatic, confirmed manually | Addition: Ministerial Decision 11654/2026, Art. 5 |
| [M7](#m7-persistent-identifier) | Persistent identifier | Metadata and legal status |  | automatic, confirmed manually | Addition: FAIR F1; W3C Data on the Web Best Practices, BP9 and BP10 |
| [M8](#m8-personal-data) | Personal data | Metadata and legal status |  | manual | Addition: legal status (GDPR; Directive (EU) 2019/1024) |
| [M9](#m9-high-value-designation) | High-value designation | Metadata and legal status |  | automatic | Addition: Regulation (EU) 2023/138, Art. 3(5) |
| [M10](#m10-api-and-bulk-download) | API and bulk download | Metadata and legal status |  | semi-automatic | Level (b): API and bulk download |
| [AI1](#ai1-machine-readable-structure) | Machine-readable structure | AI-readiness | yes | semi-automatic | Level (c): machine readability |
| [AI2](#ai2-documentation-of-the-structure) | Documentation of the structure | AI-readiness | yes | manual | Level (c): schema documentation |
| [AI3](#ai3-historical-depth) | Historical depth | AI-readiness |  | manual | Level (c): historical series |
| [AI4](#ai4-description-in-croissant-or-a-datasheet) | Description in Croissant or a datasheet | AI-readiness |  | semi-automatic | Level (c): description with Croissant or Datasheets |
| [AI5](#ai5-suitability-for-retrieval-rag) | Suitability for retrieval (RAG) | AI-readiness |  | manual | Level (c): suitability for RAG |
| [AI6](#ai6-linkage-through-common-identifiers) | Linkage through common identifiers | AI-readiness |  | semi-automatic | Addition: FAIR I3; W3C Data on the Web Best Practices, BP10 and BP15 |
| [AI7](#ai7-declared-limitations) | Declared limitations | AI-readiness |  | manual | Addition: Datasheets for Datasets; GDS (2026) |

## Quality

### Q1 Availability

*Level: Quality · core criterion · applies to all datasets*

**Instruction.** Addition: ISO/IEC 25012 (availability)

**Question.** Can the dataset's own resources be downloaded and opened?

| Score | Rule |
| --- | --- |
| 0 | No resource can be downloaded or opened. |
| 1 | At least one resource can be downloaded and opened, but at least one other fails (broken link, error page, empty or wrong file). |
| 2 | Every resource can be downloaded and opens without error. |

**How to check** (automatic, confirmed manually). Download test of every resource except the automatic 'download all' bundle of the portal. A resource is available when the server answers with HTTP 2xx, the file is not empty and it opens. A failure is recorded only when it is repeated on a second day; a resource without an address fails at once. A link declared as a file or as a data service that returns a web page fails; a link declared as a web page is available when the page opens. Requests to map services are tested as they are, and an exception report of the service fails; the bare address of a service is tested with the standard GetCapabilities request. A data file of another type than the declared one is available, and the difference is scored by Q6: the 'wrong file' of score 1 is a file that is not the data. An answer of a service without any record counts as an empty file. The score measures the resources listed on the portal: data exported by hand from an application that the dataset points to do not change it. Rules in full: DECISIONS.md #37 and #51.

**Typical fix.** Low: correct the link. Medium: restore or upload the file again.

**Sources.** ISO/IEC 25012:2008 (availability) · **FAIR:** A1

**MQA (data.gov.gr).** Accessibility: access URL accessibility; download URL accessibility

**MQA (data.europa.eu).** Distribution: access URL accessibility test; download URL accessibility test

### Q2 Completeness

*Level: Quality · applies to all datasets*

**Instruction.** Level (a): completeness

**Question.** How many values are missing?

| Score | Rule |
| --- | --- |
| 0 | More than 20% of the cells are empty, or no file can be opened. |
| 1 | 5-20% of the cells are empty, or at least one column is entirely empty. |
| 2 | Less than 5% of the cells are empty and no column is entirely empty. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (automatic for machine-readable files; manual otherwise). Share of empty cells in the files judged for AI1 (criteria/file_organisation.csv): the parts of an edition count together, of the same data in several formats the most complete one counts, of a series the latest edition; a field that more than half of the formats carry and one format leaves out counts in that format as a column without any value. Only the cells of the records count: not the title, note, totals or sub-heading rows, nor the column that the DataStore of the portal adds. A cell is empty when it holds nothing, only spaces, or a symbol or word that stands for a missing value ('-', '..', 'N/A', 'null', an error value of a spreadsheet, -999 or -9999); a unit or currency sign on its own is a value. Every empty cell counts, whatever it may mean to a reader. In GeoJSON, shapefiles and KML the geometry is one more column; in GTFS feeds and RDF in the STIRData model only the fields that the standard makes mandatory count. Data published only as documents (e.g. tables in PDF) are estimated by inspection; when nothing is available the score is 0. Of the formats that an application exports, an export in the nested layout of a service is not judged. Rules in full: DECISIONS.md #39 and #51.

**Typical fix.** Medium: complete the file or state why values are missing.

**Sources.** ISO/IEC 25012:2008 (completeness); Publications Office of the EU (2021), data.europa.eu data quality guidelines, section 1.1.1.2 · **FAIR:** R1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### Q3 Consistency

*Level: Quality · applies to all datasets*

**Instruction.** Level (a): consistency

**Question.** Are the values recorded in the same way throughout the dataset?

| Score | Rule |
| --- | --- |
| 0 | Inconsistencies that prevent analysis without manual work (e.g. values shifted between columns, different units mixed in one column), or no file can be opened. |
| 1 | Minor inconsistencies: mixed date or number formats in a column, numbers stored as text, different column names or order between files of the same dataset. |
| 2 | Each column has one type, format and unit, and all files of the dataset share the same structure. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (semi-automatic). All the data files of the dataset count: every edition, part, format and visible sheet. The values of every column are read by kind (number, date, text) and form, and the columns of the files that hold the same table (criteria/file_organisation.csv, column tables) are compared; different formats of the same data are not compared with each other, and columns of codes and identifiers are not judged. Minor inconsistencies score 1 already from a single value: several date formats or decimal marks in one column, numbers stored as text, numbers written with their unit, values of another kind in a column of numbers or dates, values outside the formats of the GTFS reference, columns that differ in name, order or number between the files of the same table. Major inconsistencies score 0: different units in one column, values shifted between columns. Recorded as findings, without a score: scientific notation in some values of a column, the same value written in different ways (case, accents, spaces, punctuation), and two fields of a record that state the same quantity and disagree, unless one of them is shown to be wrong. Ten random records of every dataset are inspected, together with Q4. Tables in documents are judged by inspection. Rules in full: DECISIONS.md #40 and #51.

**Typical fix.** Medium: harmonise the files.

**Sources.** ISO/IEC 25012:2008 (consistency); W3C Data on the Web Best Practices (2017), BP13; Publications Office of the EU (2021), data.europa.eu data quality guidelines, sections 1.1.3.1, 1.2.1.5 and 1.2.1.6 · **FAIR:** R1.3

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### Q4 Plausibility of values

*Level: Quality · applies to all datasets*

**Instruction.** Addition: ISO/IEC 25012 (accuracy)

**Question.** Are the values plausible?

| Score | Rule |
| --- | --- |
| 0 | Systematic errors (1% of the records or more): coordinates outside Greece, dates in the future, values in the wrong columns; or no file can be opened. |
| 1 | Isolated implausible values (fewer than 1% of the records), e.g. negative counts or outliers that look like typing errors. |
| 2 | No implausible values in the automatic checks and in a manual review of 10 random records. |
| n/a | The resources contain no records or attributes, e.g. a raster image or a scanned map; the reason is recorded. |

**How to check** (semi-automatic). Range checks on all the data files of the dataset, the shares being shares of all their records. Coordinates must lie inside Greece, in degrees or in the Greek Grid according to the declared reference system; a bare X or Y without a declared system is accepted when its values fall in one of the two ranges, and the missing declaration is scored by AI6. Dates must exist and lie between 1800 and the day of the download; dates of an end, of validity or of a schedule may lie in the future. Quantities recognised by the name of their column must not be negative; differences, balances, percentages, rates and indices are not judged. Weather elements must lie inside their physical range. Records identical to an earlier record of the same table are duplicates, and rows of a CSV file with values shifted between columns are implausible records. Outliers are not judged automatically: ten random records of every dataset are inspected, together with Q3, and a wrong value found there counts. Two fields of a record that state the same quantity and disagree are recorded as a finding, unless one of them is shown to be wrong. Accuracy against reality cannot be verified in general, so the criterion records plausibility. Rules in full: DECISIONS.md #41 and #51.

**Typical fix.** Medium: correct the values. High: correct the source system.

**Sources.** ISO/IEC 25012:2008 (accuracy) · **FAIR:** R1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### Q5 Timeliness

*Level: Quality · applies to all datasets*

**Instruction.** Level (a): timeliness

**Question.** Is the dataset updated as often as its metadata declare?

| Score | Rule |
| --- | --- |
| 0 | The newest data are older than three update periods, or no frequency is declared and there has been no update for more than 12 months. |
| 1 | The newest data are one to three periods late, or no frequency is declared but the dataset was updated in the last 12 months. |
| 2 | Updated within the declared frequency (with one period of tolerance), or declared as not updated (one-off or historical data) with a description that says so. |

**How to check** (semi-automatic). Declared update frequency (a term of the EU frequency vocabulary) against the last change. The frequencies are read in three groups: periodic (with the period in days; a continuous frequency counts as one day), not updated, and without a usable period (none, unknown, irregular, as needed, other). The last change is the newest upload date of a resource; for a file copied from the previous portal, the original upload date. A periodic frequency scores 2 within two periods, 1 up to four periods and 0 beyond; without a usable period the score is 1 when the last upload is within 12 months and 0 otherwise. A dataset declared as not updated scores 2 when its title or description states the past period of its data; otherwise it is judged as a dataset without a usable period. The score of the sample becomes final with the newest date inside the data and with the changes between the two snapshots of the catalogue. Rules in full: DECISIONS.md #36.

**Typical fix.** Low: declare the actual frequency. High: set up regular updates.

**Sources.** ISO/IEC 25012:2008 (currentness); W3C Data on the Web Best Practices (2017), BP21; DCAT-AP 3.0.1 (frequency) · **FAIR:** R1

**MQA (data.gov.gr).** Contextuality: date of issue; modification date (presence only)

**MQA (data.europa.eu).** Dataset and distribution: modification date; date of issue (presence only)

### Q6 Format (5-star scale)

*Level: Quality · core criterion · applies to all datasets*

**Instruction.** Level (a): format; 5-star scale

**Question.** What is the most open format in which the data are offered?

| Score | Rule |
| --- | --- |
| 0 | Only unstructured formats (PDF, word-processor documents, images, web pages) or map views without data (WMS): 1 star. |
| 1 | Structured but vendor-specific formats (XLS, XLSX, SHP, MDB) or vendor-specific services (Esri REST): 2 stars. |
| 2 | At least one open, non-proprietary structured format (CSV, JSON, GeoJSON, XML, GML, KML, GeoPackage, GeoTIFF, NetCDF, RDF) or a download service in such a format (WFS, API): 3 stars or more. |

**How to check** (automatic, confirmed manually). Each resource is placed on the 5-star scale from its metadata: by its declared format, failing that by the extension of its address, failing that by the media type that the link checker of the portal received. A map view (WMS) or a web page is 1 star; an ArcGIS REST service 2 stars; a WFS service, a DataStore table of the portal or an OAI-PMH request 3 stars; a WFS request is rated by its output format. A compressed archive is rated only when its name, its declared format or its address says what it holds; otherwise it is undetermined, as is a resource without any format. The dataset scores its best resource; a score that undetermined archives could raise is provisional. In the sample the declared format is verified against the content of the downloaded files, which can change the score in either direction: a file declared as CSV that is in fact a PDF counts as PDF, a text file that holds a delimited table counts as CSV, a TIFF with georeferencing counts as GeoTIFF. The score measures the resources listed on the portal: data exported by hand from an application do not change it. Rules in full: DECISIONS.md #35 and #51.

**Typical fix.** Medium: publish an open format next to the existing one.

**Sources.** 5-star Open Data (Berners-Lee); W3C Data on the Web Best Practices (2017), BP12 and BP14; Directive (EU) 2019/1024, Art. 5; Circular 24849/2026, section 1.5 · **FAIR:** I1

**MQA (data.gov.gr).** Interoperability: format; machine readable; non-proprietary

**MQA (data.europa.eu).** Distribution: non-proprietary; machine readable

## Metadata and legal status

### M1 Mandatory metadata

*Level: Metadata and legal status · core criterion · applies to all datasets*

**Instruction.** Level (b): DCAT-AP (mandatory properties)

**Question.** Are the metadata that DCAT-AP makes mandatory present and meaningful?

| Score | Rule |
| --- | --- |
| 0 | A mandatory element is missing: title, description, or an access URL for a resource. |
| 1 | All are present, but the description repeats the title or is shorter than 100 characters. |
| 2 | Title, a meaningful description (at least 100 characters, saying what the data contain) and an access URL for every resource. |

**How to check** (automatic, confirmed manually). Portal metadata (fact sheet): title, description and access URL of each resource. Title and description are measured as visible text, after removal of HTML tags and collapsing of white space. A description repeats the title when the two are identical after lower-casing and removal of punctuation. A resource has an access URL when its address field holds a value or when it is an active DataStore table of the portal. The automatic bundles of the portal are left out, and a dataset without resources of its own is judged on its title and description only, the absence of resources being scored by Q1. Whether the description is meaningful is confirmed by reading it. Rules in full: DECISIONS.md #23.

**Typical fix.** Low: complete the metadata.

**Sources.** DCAT-AP 3.0.1 (mandatory properties of Dataset and Distribution); Ministerial Decision 11654/2026 · **FAIR:** F2

**MQA (data.gov.gr).** Interoperability: DCAT-AP compliance

**MQA (data.europa.eu).** Dataset: title; description. Distribution: access URL

### M2 Recommended metadata

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Level (b): DCAT-AP (recommended properties)

**Question.** How many of seven descriptive metadata are present: keyword, theme, publisher, contact point, geographical coverage, temporal coverage, update frequency?

| Score | Rule |
| --- | --- |
| 0 | Two or fewer. |
| 1 | Three to five. |
| 2 | Six or seven. |

**How to check** (automatic). Portal metadata (fact sheet). The first six are recommended properties of DCAT-AP; the update frequency is optional in DCAT-AP and is checked because the assessment of timeliness (Q5) depends on it. Geographical coverage is the area to which the data refer; for national data, the country (Greece) is sufficient. A property counts as present whenever it holds a value, including a broad, default or erroneous one (e.g. the whole of Greece for local data, a temporal coverage from 1900 to 2099, a bounding box of the whole world or outside Greece); a frequency 'unknown' or 'not planned' is a value, and a field whose elements are all empty counts as absent. The publisher is the publisher field of the metadata of the portal: the organisation that owns the dataset is not counted, although the DCAT-AP export of the portal gives it as the publisher when the field is absent. Rules in full: DECISIONS.md #21 and #24.

**Typical fix.** Low: complete the metadata.

**Sources.** DCAT-AP 3.0.1; W3C Data on the Web Best Practices (2017), BP1 and BP2; Circular 24849/2026 · **FAIR:** F2

**MQA (data.gov.gr).** Findability: keyword usage; categories; geo search; time-based search. Reusability: contact point; publisher

**MQA (data.europa.eu).** Dataset: keyword usage; categories; geo search; temporal coverage; publisher; contact point

### M3 Controlled vocabularies

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Level (b): DCAT-AP (controlled vocabularies)

**Question.** Are theme, file format and update frequency given with terms of the controlled vocabularies?

| Score | Rule |
| --- | --- |
| 0 | None of them. |
| 1 | Some of them; the rest are free text. |
| 2 | All of those present use controlled vocabularies. |

**How to check** (automatic). DCAT export of the dataset (data.gov.gr/dataset/&lt;name&gt;.jsonld): theme from the EU data-theme vocabulary, format from the EU file-type vocabulary or the IANA media types, frequency from the EU frequency vocabulary. Only what is present is judged: a missing theme, frequency or format is scored by M2, and a dataset with nothing to judge scores 0. Theme and frequency use a vocabulary when their values are URIs of the EU vocabularies. A resource uses a vocabulary when its format, compared without regard to case and without a leading dot, is exactly a code or the English label of the EU file-type vocabulary or an IANA media type, or when its media type field holds an IANA media type; approximate matches (e.g. 'shp zip', 'TIF') are free text. The copy of the file-type vocabulary that the check uses is stored in data/reference/eu_file_type.csv. Rules in full: DECISIONS.md #25.

**Typical fix.** Low: select the terms from the vocabularies.

**Sources.** DCAT-AP 3.0.1 (controlled vocabularies); W3C Data on the Web Best Practices (2017), BP15 · **FAIR:** I2

**MQA (data.gov.gr).** Interoperability: format or media type from vocabulary

**MQA (data.europa.eu).** Distribution: format from vocabulary; media type from vocabulary

### M4 Licence

*Level: Metadata and legal status · core criterion · applies to all datasets*

**Instruction.** Level (b): clarity of the licence; CC BY 4.0 or a more permissive licence

**Question.** Is an open licence declared clearly for all resources?

| Score | Rule |
| --- | --- |
| 0 | No licence, or a licence that restricts re-use (non-commercial, no derivatives, permission required). |
| 1 | An open licence, but not declared for every resource, given only as text without a link, conflicting between resources, or more restrictive than CC BY 4.0 (e.g. share-alike). |
| 2 | Every resource carries the same permissive licence as a term of the licence vocabulary: CC0, CC BY 4.0 or an equivalent or less restrictive open licence. |

**How to check** (automatic, confirmed manually). Licence field of each resource in the portal metadata, a term of the EU licence vocabulary that is shown on the page of the resource and exported in DCAT-AP. Licences are classed as permissive (CC0, CC BY of any version, ODC-BY, PDDL), share-alike (CC BY-SA, ODbL, GFDL) or restrictive (non-commercial, no derivatives, closed). The same permissive licence on every resource scores 2; a restrictive licence on any resource scores 0; resources without a licence among licensed ones, different licences between resources or a share-alike licence score 1, and so does a licence named only in free text, without a term of the vocabulary; a dataset without resources scores 0. The licence field at the level of the dataset, which the portal neither displays nor exports, is not scored: it is recorded, and a contradiction with the licences of the resources is reported as a finding. Rules in full: DECISIONS.md #31.

**Typical fix.** Low: declare the licence in the metadata.

**Sources.** Directive (EU) 2019/1024, Art. 8; Regulation (EU) 2023/138, Art. 4; Ministerial Decision 11654/2026, Art. 8; W3C Data on the Web Best Practices (2017), BP4 · **FAIR:** R1.1

**MQA (data.gov.gr).** Reusability: licence information; licence vocabulary

**MQA (data.europa.eu).** Distribution: license information; license vocabulary

### M5 Free access

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Level (b): free of charge

**Question.** Can the data be obtained free of charge and without registration?

| Score | Rule |
| --- | --- |
| 0 | A charge applies, or access requires an account that is not open to everyone. |
| 1 | Free of charge, but registration, an API key or acceptance of additional terms is required. |
| 2 | Free of charge and without registration. |
| n/a | No resource delivers data and nothing points to a charge or to registration (e.g. HTTP 404, HTTP 503, an empty list). |

**How to check** (manual). The evidence is the download test, which fetches every resource anonymously, without an account, a cookie or a key; for the datasets whose files are served by the sites of their publishers, one resource of each is also opened in a browser. Registration means an account or sign-in, an API key, a form that asks for an e-mail address before the download, or a mandatory acceptance of terms; a licence that is merely displayed is not registration. One complete route is enough: when all the data can be obtained anonymously through at least one resource the score is 2, even if another resource asks for sign-in. A manual export from an application that asks for no registration scores 2, the absence of a direct link being a matter for M6 and Q1. When no resource delivers data, the answer of the server is judged: a sign-in page or a refusal of permission scores 0, or 1 when anyone can open an account. M5 gives the column 'free of charge' of the table of compliance of the high-value datasets: yes for 2 or 1 (with the note 'registration' for 1), no for 0. Rules in full: DECISIONS.md #44 and #51.

**Typical fix.** High: change of the access policy.

**Sources.** Directive (EU) 2019/1024, Art. 6 and Art. 14; Ministerial Decision 11654/2026, Art. 8 · **FAIR:** A1

**MQA (data.gov.gr).** Reusability: access restrictions; access restrictions vocabulary (declaration only)

**MQA (data.europa.eu).** Dataset: access rights; access rights vocabulary (declaration only)

### M6 Mode of distribution

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Addition: Ministerial Decision 11654/2026, Art. 5

**Question.** How are the data made available, in the order of preference of the Ministerial Decision: API, direct link, structured file, unstructured file?

| Score | Rule |
| --- | --- |
| 0 | Only through a web page or an application without download, or no working access. |
| 1 | Files that do not give the complete data through a direct link: split into many parts, or reachable only through an intermediate page, form or map viewer. |
| 2 | An API, or a stable direct link to the complete data. |

**How to check** (automatic, confirmed manually). The mode of access of each resource is read from its address, its declared format and the result of the link checker of the portal: an API or data service (a WFS, WCS or OAI-PMH request, an ArcGIS REST endpoint, an active DataStore table), a direct link to a file, a map view (WMS), a web page, or no address. The dataset scores its best mode: an API or a direct link to a file scores 2; only map views or only web pages score 1; no address on any resource, or no resources, scores 0. A web page falls to 0 when it is found to offer no download at all. Whether a link delivers the complete data, whether the data are split into arbitrary parts and whether the links work is verified in the download test of the sample, which can lower the score; one file per year or per region is a normal organisation of the data. Data that are reached only through the export of an application score 1 at most. Rules in full: DECISIONS.md #34 and #51.

**Typical fix.** Medium: publish a direct link to the complete data. High: build an API.

**Sources.** Ministerial Decision 11654/2026, Art. 5; W3C Data on the Web Best Practices (2017), BP17 and BP23 · **FAIR:** A1

**MQA (data.gov.gr).** Accessibility: download URL (presence only)

**MQA (data.europa.eu).** Distribution: download URL (presence only)

### M7 Persistent identifier

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Addition: FAIR F1; W3C Data on the Web Best Practices, BP9 and BP10

**Question.** Do the dataset and its resources have stable identifiers?

| Score | Rule |
| --- | --- |
| 0 | No resource has an address, or the dataset has no resources. |
| 1 | The dataset has a stable address, but at least one resource has no address or an address that changes (new address with every upload, query or session parameters). |
| 2 | The dataset has a stable URI and identifier, and its resources have stable links. |

**How to check** (automatic, confirmed manually). The portal gives every dataset a permanent identifier and a URI built on it, and every resource a URI of its own, so that the score is decided by the addresses of the resources (fact sheet). An address is stable when it is a file uploaded on the portal, an active DataStore table, a request to a standard service (WMS, WFS, WCS, CSW, OAI-PMH) or a plain address on another site; a file on a third-party storage service is recorded as a finding and not penalised. An address changes when it depends on an opaque token, ticket or session parameter, on a URL shortener or on a redirect through a search engine. Whether an address actually changes over time is measured by comparing the two snapshots of the catalogue, and the scores concerned are revised then. Rules in full: DECISIONS.md #33.

**Typical fix.** Low: assign stable addresses.

**Sources.** W3C Data on the Web Best Practices (2017), BP9 and BP10; DCAT-AP 3.0.1 (identifier) · **FAIR:** F1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** Dataset: identifier (dct:identifier; adms:identifier) (presence only)

### M8 Personal data

*Level: Metadata and legal status · applies to all datasets*

**Instruction.** Addition: legal status (GDPR; Directive (EU) 2019/1024)

**Question.** Does the dataset avoid exposing personal data?

| Score | Rule |
| --- | --- |
| 0 | Personal data of natural persons (names, identity or tax numbers, home addresses, personal contact details) are published without any legal obligation. |
| 1 | Indirect identification is possible (e.g. very small counts, exact locations linked to individuals) and the dataset does not state how it was anonymised; or personal data are published under a legal obligation that the metadata state nowhere. |
| 2 | No personal data; or personal data published under a legal obligation that the metadata state; or data aggregated or anonymised, as stated. |
| n/a | No file of the dataset is available, so that nothing can be inspected; the failure is counted in Q1. |

**How to check** (manual). Inspection of the columns and of 10 random records; of two or three pages or decisions for documents; of the map image for map services; description and documentation of the dataset. Personal data are any information relating to an identified or identifiable natural person (Regulation (EU) 2016/679, Article 4(1)); legal persons are out of scope, and a sole proprietorship counts as a natural person. Professional contact details of units and bodies are not personal data, unless they are the personal e-mail or mobile number of a named person, or a home address. A cell with a count of 1 or 2 counts as indirect identification only when it comes with another measure of the unit (quantity, value, income). The legal basis counts when the dataset or its metadata state the law or procedure under which the data are published. A dataset that holds personal data is recorded by dataset, file, kind of information and column, never by value, and no record of it is reproduced in the repository, in the reports or in the study. Rules in full: DECISIONS.md #29 and #43.

**Typical fix.** Medium: remove or aggregate the fields.

**Sources.** Regulation (EU) 2016/679 (GDPR); Directive (EU) 2019/1024, Art. 1(4); Ministerial Decision 11654/2026, Art. 7

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### M9 High-value designation

*Level: Metadata and legal status · applies to high-value datasets only*

**Instruction.** Addition: Regulation (EU) 2023/138, Art. 3(5)

**Question.** Do the metadata mark the dataset as high-value?

| Score | Rule |
| --- | --- |
| 0 | No marking: the dataset is high-value by content only. |
| 1 | Partial marking: the category without a reference to Regulation 2023/138, the reference without the category, or only the high-value dataset type. |
| 2 | High-value category and a reference to Regulation 2023/138 as applicable legislation. |
| n/a | Datasets of the comparison group. |

**How to check** (automatic). Fields hvd_category, applicable_legislation and dcat_type of the portal metadata, all three shown on the page of the dataset and exported in DCAT-AP. The category together with the reference to Regulation (EU) 2023/138 scores 2, with or without the dataset type; the category alone, the reference alone or the type alone scores 1. The criterion scores the presence of the marking, not its correctness: whether the declared category is the right one, and whether a marked dataset belongs to the Annex of the Regulation at all, is judged by hand and recorded in the table of compliance of the high-value datasets. Rules in full: DECISIONS.md #28 and #32.

**Typical fix.** Low: complete the metadata.

**Sources.** Regulation (EU) 2023/138, Art. 3; DCAT-AP HVD · **FAIR:** F2

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** Dataset: applicable legislation (presence only)

### M10 API and bulk download

*Level: Metadata and legal status · applies to high-value datasets only*

**Instruction.** Level (b): API and bulk download

**Question.** Is the dataset available both through an API and as a bulk download, as the Regulation requires?

| Score | Rule |
| --- | --- |
| 0 | Neither an API nor a bulk download of the complete dataset. |
| 1 | Only one of the two, or an API without public documentation and terms of use. |
| 2 | An API with public documentation and terms of use, and a bulk download of the complete dataset. |
| n/a | Datasets of the comparison group. |

**How to check** (semi-automatic). An API is a service that answers queries with the data themselves: a WFS, an ArcGIS service that answers queries, the DataStore of the portal, an API of the publisher; a map view (WMS), the API of the catalogue and a plain link to a file are not APIs. An API belongs to a dataset when the dataset declares it, as a resource or as the address of a service written in a description. It counts when it answers anonymously and gives all the records of the dataset, which is tested by calling it for its description and for the number of its records, never for the records. Documentation is a public description of the API in a recognised open format (the capabilities document of a WFS, the description that an ArcGIS service gives of itself, a page of the portal for the DataStore); terms of use are a published text on the use of the API, and the licence of the data in the catalogue is not enough. A bulk download is one or more files that give the complete dataset: files behind direct links, the complete export of a layer through WFS, or the export of the complete list from an application; the automatic bundle of the portal is not counted. Exceptions of the Annex of the Regulation: numerical weather prediction (NWP) model data are required only through an API (point 3.2(a)), and historical versions of Earth observation and environment datasets through an API or a bulk download (point 2.2(a)); in these cases the required means of access alone scores 2, and only for the datasets that the points name. M10 gives three columns of the table of compliance of the high-value datasets: API, bulk download, and terms of use and documentation of the API. Rules in full: DECISIONS.md #45.

**Typical fix.** Medium: publish a complete download. High: build an API.

**Sources.** Regulation (EU) 2023/138, Art. 3(1) to 3(4) and Annex (exceptions in points 2.2(a) and 3.2(a)); W3C Data on the Web Best Practices (2017), BP17, BP23 and BP25 · **FAIR:** A1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** Data service: endpoint URL; endpoint description; serves dataset. Distribution: download URL

## AI-readiness

### AI1 Machine-readable structure

*Level: AI-readiness · core criterion · applies to all datasets*

**Instruction.** Level (c): machine readability

**Question.** Can a program read the data directly, without manual cleaning?

| Score | Rule |
| --- | --- |
| 0 | Not without manual work: PDF or scanned documents, images, spreadsheets laid out for printing (merged cells, several tables in one sheet), or no data file. |
| 1 | Readable after minor cleaning: title or note rows above the table, a totals row, numbers stored as text, a header split over two rows. |
| 2 | One header row, one record per row and one value per cell, without notes or totals inside the table; or a standard structured format (GeoJSON, JSON, XML) that is read without errors. |

**How to check** (semi-automatic). Automatic read test, then a look at the file. The files judged follow the organisation of the files of each dataset (criteria/file_organisation.csv): the single data file; the best one of the same data in several formats; the latest edition of a series; the worst one of the parts of an edition. Data files are delimited text, spreadsheets, JSON and GeoJSON, XML with data (GML, KML), RDF, shapefiles and GTFS feeds; shapefiles, GTFS feeds and RDF in Turtle count as standard structured formats, which score 2 when they are parsed without error and 0 otherwise. A table scores 1 with title or note rows above or below it, a header over two rows, totals or sub-heading rows, repeated header rows, empty rows inside the table, or numbers stored as text in a spreadsheet; it scores 0 with merged cells inside the data, several tables in one sheet, rows with values beyond the columns of the header, or when it cannot be read. A spreadsheet scores its worst visible sheet with a table. Of the formats that an application exports by hand, those judged are named in the same file, and an export in the nested layout of a service is not judged. Rules in full: DECISIONS.md #38 and #51.

**Typical fix.** Medium: restructure the file.

**Sources.** W3C Data on the Web Best Practices (2017), BP12; GDS (2026), Guidelines and best practices for making government datasets ready for AI; Wickham (2014), Tidy Data; Publications Office of the EU (2021), data.europa.eu data quality guidelines, sections 1.2.1.2 to 1.2.1.4 · **FAIR:** I1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### AI2 Documentation of the structure

*Level: AI-readiness · core criterion · applies to all datasets*

**Instruction.** Level (c): schema documentation

**Question.** Is the meaning and the unit of every field documented, and are the codes explained (data dictionary)?

| Score | Rule |
| --- | --- |
| 0 | No documentation: the meaning of the fields or codes has to be guessed. |
| 1 | Partial: the field names are clear but units or codes are not explained, or only some fields are documented. |
| 2 | A written explanation gives the meaning of every field, the unit of every measure and every code or abbreviation, in the metadata, in a data dictionary, in a declared public standard, in the file itself or on a page linked from the metadata. The type of a field is not asked for separately. |
| n/a | The dataset has no fields: map images and documents of running text. |

**How to check** (manual). Description, documentation resources and publisher pages linked from the dataset, compared with the columns of the files judged for AI1. An explanation counts wherever a user of the dataset can find it and the public can open it: in the description of the dataset or of a resource, in a documentation file among the resources, on a page of the publisher that the metadata link to, in a public standard that the dataset declares, and in the file itself (a header that carries the unit, a column with the label next to the code, a row of text above or below the table). A written explanation names the items of information that the columns hold; clear names of columns without it score 1. A declared standard gives 2 when every column is a field of the standard and 1 when columns outside it are left unexplained. A table inside a document is judged by a look at the document. Datasets of which no file was obtained are judged on their metadata and score 1 at most. AI2 gives the column 'documentation of the structure' of the table of compliance of the high-value datasets: yes for 2, partly for 1, no for 0. Rules in full: DECISIONS.md #46 and #51.

**Typical fix.** Low: write a data dictionary.

**Sources.** W3C Data on the Web Best Practices (2017), BP3; GDS (2026), Guidelines and best practices for making government datasets ready for AI; Gebru et al. (2021), Datasheets for Datasets; MLCommons Croissant 1.0 (RecordSet, Field); Regulation (EU) 2023/138, Annex, points 2.2(c), 3.2(c), 4.2(c), 5.2(b) and 6.2(c) · **FAIR:** R1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** Distribution: documentation (presence only)

### AI3 Historical depth

*Level: AI-readiness · applies to all datasets*

**Instruction.** Level (c): historical series

**Question.** Are earlier periods or versions of the data available?

| Score | Rule |
| --- | --- |
| 0 | Only the current state; earlier data have been replaced or removed. |
| 1 | Some earlier periods or versions, with gaps or in a different structure; or only two periods or versions; or a single period, when the other periods are published as separate datasets of the same publisher. |
| 2 | A continuous series of at least three periods or versions in the same structure: every period from the first to the last is there, with the same columns. |
| n/a | The data have by nature no before and after: the image of the map of one act, the document of one act, a product with fixed reference years that does not recur. |

**How to check** (manual). Earlier periods or versions count wherever a user of the dataset can find them: inside the file (a column of dates, years or months, or periods as the names of the columns), in separate files of the dataset, and on a page of the publisher that the metadata link to; the temporal coverage of the metadata is only an indication. A gap is a whole period missing between the first and the last: that a series has stopped is a matter of Q5, and a few missing readings of a sensor a matter of Q2. The same structure is the result of the comparison of the columns made for Q3. Registers, lists and timetables show the present state: their past is their earlier versions, and a dataset whose every update replaces the previous file scores 0. A product with fixed reference years that is one period of a product that recurs, the other periods being separate datasets of the publisher, scores 1. Datasets of which no file was obtained are judged on the list of their resources and on their metadata and score 1 at most. The length of a series is recorded and does not change the score. Rules in full: DECISIONS.md #47.

**Typical fix.** Medium: publish the archive.

**Sources.** W3C Data on the Web Best Practices (2017), BP7 and BP8; GDS (2026), Guidelines and best practices for making government datasets ready for AI · **FAIR:** R1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### AI4 Description in Croissant or a datasheet

*Level: AI-readiness · applies to all datasets*

**Instruction.** Level (c): description with Croissant or Datasheets

**Question.** Can the dataset be described in Croissant, or with a datasheet, from the information available?

| Score | Rule |
| --- | --- |
| 0 | Neither a valid Croissant description nor a datasheet can be written, and the documentation only repeats the title. |
| 1 | A valid Croissant description whose fields are missing or do not all carry a meaning; or a datasheet with major gaps; or, where neither can be written, documentation that says more than the title about what the data contain or how they were collected. |
| 2 | A valid Croissant description in which every field has its type and its meaning, or, for data without records, a datasheet that states what the data contain, how they were collected and for which uses they are suitable. |

**How to check** (semi-automatic). A Croissant description is written only from what exists: the metadata of the portal and the results of the earlier checks (the licence read for M4, the files obtained for Q1, the columns and types found for AI1, the meaning of the columns judged for AI2), and it is validated with the mlcroissant library. It is valid at the level of the dataset when it holds every property that the specification requires (name, description, licence, address, creator, date of publication), describes at least one data file that was obtained and passes the validator without an error; the specification decides and not the validator alone, so that a dataset without a licence has no valid description. Data without records (images of maps, documents) are judged with a datasheet. Documentation counts where the public can open it, and a description that only spells out an abbreviation of the title repeats the title. Datasets of which no file was obtained, and data exported by hand that are not among the resources of the dataset, score 1 at most. Rules in full: DECISIONS.md #48 and #51.

**Typical fix.** Low: complete the metadata and the data dictionary.

**Sources.** MLCommons Croissant 1.1; Gebru et al. (2021), Datasheets for Datasets · **FAIR:** R1.3

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### AI5 Suitability for retrieval (RAG)

*Level: AI-readiness · applies to all datasets*

**Instruction.** Level (c): suitability for RAG

**Question.** Can the content be split into self-contained pieces that an AI system can retrieve and cite?

| Score | Rule |
| --- | --- |
| 0 | Not usable: scanned images or maps without text, or no content that can be extracted. |
| 1 | Usable after conversion (text extraction from a born-digital PDF, flattening of a spreadsheet), or the pieces lack a stable identifier or a link to the source. |
| 2 | Records or text passages with a stable identifier and a link to the source, in text that is extracted cleanly in UTF-8, Greek included. |

**How to check** (manual). The files judged are those of AI1: of the same data in several formats the best one, of the parts of a dataset the worst one. A piece is one record with the names of its columns, or one passage of a document. Reading a standard structured format with a library is not a conversion; the extraction of the text of a PDF document and the cleaning of a sheet laid out for printing are. A stable identifier is a column, or a combination of up to four columns, with a value in every record and without any repetition, which names or codes the thing that the record describes; the number of the row, a column that gives only a class of the thing and the columns of measures do not count. The link to the source is the permanent address of the resource on the portal; data that are not among the resources of the dataset have none. Every case counts: one record that repeats the identifier, or one cell with damaged text, is enough for score 2 not to be met. PDF documents score 1 when their text can be extracted and 0 when they are scanned images; for a document that was not obtained this is judged by the look of its letters when the page is enlarged. Images of maps and datasets of which no file was obtained score 0; data exported by hand from an application score 1 at most. The datasets that are posted with names of persons enter no retrieval collection of the study, whatever their score. Rules in full: DECISIONS.md #49 and #51.

**Typical fix.** Medium: publish the content as structured text or records.

**Sources.** GDS (2026), Guidelines and best practices for making government datasets ready for AI (unstructured data); W3C Data on the Web Best Practices (2017), BP10 · **FAIR:** F1

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### AI6 Linkage through common identifiers

*Level: AI-readiness · applies to all datasets*

**Instruction.** Addition: FAIR I3; W3C Data on the Web Best Practices, BP10 and BP15

**Question.** Can the data be joined with other datasets through common codes or coordinates?

| Score | Rule |
| --- | --- |
| 0 | No identifiers or location information that allow linkage. |
| 1 | Only names (e.g. municipality names) or codes internal to the publisher, or coordinates without a declared reference system. |
| 2 | Standard codes (e.g. municipality codes of the Kallikratis classification, NUTS or LAU codes, KAD/NACE activity codes, tax or GEMI numbers, KAEK cadastral codes) or coordinates in a declared reference system. |

**How to check** (semi-automatic). Column names and values of all the data files of the dataset (fact sheet); the best file counts. A reference system is declared when the file or its standard states it: a .prj file, the crs member of GeoJSON, KML and GTFS by their standards, or a column whose name states the system; latitude and longitude without any declaration, and a bare X or Y accepted by its range, are coordinates without a declared system. Standard codes are those defined outside the publisher and used by many, recognised by the name of the column and by the form of the values. Codes that only the publisher defines (serial numbers, protocol and file numbers, the ids of stops or sensors) are internal codes, and places, bodies, shops and stations given as text are names; a name that stands only outside the records, in the title of the dataset or in the names of its sheets or files, counts as a name. Map services (WMS) are judged by the reference systems that their capabilities document declares; documents are estimated by inspection; datasets without a data file score 0. Rules in full: DECISIONS.md #42.

**Typical fix.** Medium: add the standard codes.

**Sources.** W3C Data on the Web Best Practices (2017), BP10 and BP15; FAIR I3 · **FAIR:** I3

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** None

### AI7 Declared limitations

*Level: AI-readiness · applies to all datasets*

**Instruction.** Addition: Datasheets for Datasets; GDS (2026)

**Question.** Do the metadata or the documentation state the known limitations of the data?

| Score | Rule |
| --- | --- |
| 0 | No statement about coverage, gaps, collection method or known errors. |
| 1 | One to three of the four elements are stated, e.g. only the source or only the coverage. |
| 2 | All four elements are stated: coverage, gaps, collection method, and known errors or changes of method. |

**How to check** (manual). The evidence is what a publisher writes in words: the description of the dataset and of its resources, the documents published with the data, and the pages and documents of the publisher that the dataset points to and that open for a visitor, which is tested in a browser. The fields of temporal and geographical coverage are not counted again (M2). Four questions are asked: what the data cover, what is missing, how the data were collected, and which errors or changes are known; the number of questions answered is recorded. The name is not a statement: a description that says only which dataset it is answers no question, and neither does the general phrase that the data are given as they are, nor a phrase that names the publisher itself as the provider of the data. Where a description says more, each question is judged on its own. A sentence that tells the users of a service of a restriction is not a statement of gaps; a method that is named and not described, and the word by which a table is declared provisional, are partial statements. A statement that the files contradict does not count and is recorded as a finding. Datasets of which no file was obtained score 1 at most. Rules in full: DECISIONS.md #50.

**Typical fix.** Low: add a short note on limitations.

**Sources.** Gebru et al. (2021), Datasheets for Datasets; GDS (2026), Guidelines and best practices for making government datasets ready for AI; W3C Data on the Web Best Practices (2017), BP6 · **FAIR:** R1.2

**MQA (data.gov.gr).** None

**MQA (data.europa.eu).** Dataset: provenance (presence only)
