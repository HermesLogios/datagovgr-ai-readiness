# Croissant descriptions of the datasets of the sample (AI4), snapshot of 2026-10-24

Produced by `scripts/10_croissant_checks.py`. Every description is written only from the metadata of the portal and from the tables of the earlier checks, and is validated with the mlcroissant library (version 1.1.1); a score is proposed only where a rule decides without judgement, and the final scores are recorded in `DECISIONS.md`. The descriptions and this report contain no records of the data.

## Whole catalogue

Datasets and resources whose metadata can fill each property of a Croissant description. The automatic bundle that the portal adds to every dataset is not counted among the resources.

| Level | Property | Filled from | Count | Of | % | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| dataset | name | title | 22,805 | 22,805 | 100.0 | required |
| dataset | description | description (notes) | 22,094 | 22,805 | 96.9 | required |
| dataset | license | licence term on every resource | 22,150 | 22,805 | 97.1 | required; the licence of a dataset is that of its resources (DECISIONS.md #31) |
| dataset | license | licence field of the dataset (license_url, license_title) | 7,535 | 22,805 | 33.0 | the generic licence field of the software of the portal, which the Croissant profile of ckanext-dcat reads and the portal neither displays nor exports (DECISIONS.md #31) |
| dataset | license | the same field, other than "License not specified" | 3,895 | 22,805 | 17.1 | the entry "License not specified" would be written as the licence |
| dataset | creator | creator field of the dataset, otherwise its organisation | 22,805 | 22,805 | 100.0 | required |
| dataset | creator | creator field of the dataset with at least one name | 1,899 | 22,805 | 8.3 | what the Croissant profile of ckanext-dcat writes as the creator |
| dataset | creator | creator field filled without any name | 278 | 22,805 | 1.2 | the profile would write a creator without a name; the organisation is written here |
| dataset | datePublished | issued, otherwise the date of the record (metadata_created) | 22,805 | 22,805 | 100.0 | required |
| dataset | datePublished | issued | 0 | 22,805 | 0.0 | the field of the date of publication itself |
| dataset | keywords | tags | 22,456 | 22,805 | 98.5 | recommended |
| dataset | version | version | 226 | 22,805 | 1.0 | recommended |
| dataset | inLanguage | language of the dataset | 0 | 22,805 | 0.0 | recommended |
| dataset | distribution | at least one resource | 22,732 | 22,805 | 99.7 |  |
| dataset | contentUrl | every resource with an address (url) | 22,669 | 22,805 | 99.4 |  |
| dataset | encodingFormat | every resource with a media type (mimetype) | 2,034 | 22,805 | 8.9 |  |
| dataset | md5 or sha256 | every resource with a checksum of 32 or 64 characters (hash) | 6,539 | 22,805 | 28.7 | the validator asks for a checksum of every file |
| dataset | recordSet | at least one resource in the DataStore | 1,114 | 22,805 | 4.9 | the columns that the portal knows already |
| dataset | all the required properties | the licence read from the resources | 21,446 | 22,805 | 94.0 | name, description, licence, creator and date; the address of the page always exists |
| dataset | all the required properties | the licence read from the field of the dataset | 6,825 | 22,805 | 29.9 | what the Croissant profile of ckanext-dcat would write from the metadata as they are |
| dataset | all the required properties | the same field, other than "License not specified" | 3,640 | 22,805 | 16.0 |  |
| resource | name | name of the resource | 86,061 | 86,782 | 99.2 |  |
| resource | md5 | checksum of 32 characters (hash) | 17,846 | 86,782 | 20.6 |  |
| resource | sha256 | checksum of 64 characters (hash) | 0 | 86,782 | 0.0 |  |
| resource | checksum of another kind | checksum of another length (hash) | 897 | 86,782 | 1.0 | for example SHA-1, which a Croissant description does not accept |
| resource | no checksum | empty hash | 68,039 | 86,782 | 78.4 |  |
| resource | encodingFormat | media type (mimetype) | 46,869 | 86,782 | 54.0 |  |
| resource | recordSet | resource in the DataStore | 1,633 | 86,782 | 1.9 |  |

## The portal

Asked on 2026-11-11 (https://data.gov.gr/api/3/action/status_show): CKAN 2.11.3, 66 extensions; dcat plugin: yes; croissant plugin: no.

## Proposals

Proposed AI4: 1: 18, 2: 4, by hand: 14.

| Dataset | Data | Proposal | Reason |
| --- | --- | --- | --- |
| S01 Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος  | data files | by hand | no valid description at the level of the dataset (required by the specification and missing: license); 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S02 Καλλικρατικοί Δήμοι | data files | 1 | valid at the level of the dataset; 14 fields with the type, none of them with a documented meaning; 1 examined table without a list of columns in the file profiles |
| S03 Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ) | data files | by hand | no valid description at the level of the dataset (required by the specification and missing: license); 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S04 Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υ | data files | 1 | valid at the level of the dataset; 28 fields with the type, none of them with a documented meaning |
| S05 Λίστα με Μονάδες Φροντίδας Ηλικιωμένων | no data file among the resources obtained | by hand | no valid description at the level of the dataset (required by the specification and missing: license; no data file among the resources obtained (examined tables of files that are not resources of the dataset: 2)); 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S06 Τροχαία ατυχήματα | data files | 2 | valid, with the type and the meaning of all the 2 fields (criteria/field_descriptions.csv: 2) |
| S07 Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος | data files | 2 | valid, with the type and the meaning of all the 18 fields (criteria/field_descriptions.csv: 18) |
| S08 "ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ,  | data files | 1 | valid at the level of the dataset; 29 fields with the type, none of them with a documented meaning |
| S09 Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής | data files | by hand | no valid description at the level of the dataset (required by the specification and missing: license); 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: yes) |
| S10 ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ) | data files | 1 | valid at the level of the dataset; 363 fields with the type, none of them with a documented meaning |
| S11 Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ) | data files | by hand | no valid description at the level of the dataset (required by the specification and missing: license); 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S12 Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης | data files | 1 | valid at the level of the dataset; 74 fields with the type, 71 of them with a documented meaning |
| S13 Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS | data files | 2 | valid, with the type and the meaning of all the 48 fields (GTFS Schedule Reference: 48) |
| S14 Υπηρεσίες Δήμου Πατρέων | data files | 1 | valid at the level of the dataset; 118 fields with the type, none of them with a documented meaning |
| S15 ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ | data files | 1 | valid at the level of the dataset; 3 fields with the type, none of them with a documented meaning |
| S16 Θεσμοθετημένες περιοχές NATURA 2000 | data files | 1 | valid at the level of the dataset; 9 fields with the type, none of them with a documented meaning |
| S17 Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ | no data file among the resources obtained | by hand | no valid description at the level of the dataset (no resource of the dataset was obtained; examined tables of files that are not resources of the dataset: 2); 1 at most, since the examined files are not resources of the dataset: 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S18 Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018 | data files | 1 | valid at the level of the dataset; 28 fields with the type, none of them with a documented meaning; 1 examined table without a list of columns in the file profiles |
| S19 Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ | data files | 1 | valid at the level of the dataset; 57 fields with the type, none of them with a documented meaning |
| S20 Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-202 | data files | 1 | valid at the level of the dataset; 18 fields with the type, none of them with a documented meaning |
| S21 Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης | data files | 2 | valid, with the type and the meaning of all the 14 fields (criteria/field_descriptions.csv: 14) |
| S22 Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδ | documents | by hand | no valid description at the level of the dataset (no data file: documents); data without records, judged with a datasheet: 2 when the documentation says what the data contain, how they were collected and for which uses they are suitable; otherwise 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S23 Athens Business Open Data - STIRData model | data files | 1 | valid at the level of the dataset; 34 fields with the type, none of them with a documented meaning |
| S24 ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ) | data files | 1 | valid at the level of the dataset; the columns of 7 examined tables are not written, their names being withheld (DECISIONS.md #29) |
| S25 ΣΤΑΤΙΣΤΙΚΑ ΔΙΑΤΡΟΦΗΣ ΦΕΒΡΟΥΑΡΙΟΥ 2017 | data files | 1 | valid at the level of the dataset; 8 fields with the type, none of them with a documented meaning |
| S26 ΣΤΑΤΙΣΤΙΚΑ ΙΧΘΥΟΣΚΑΛΑΣ ΘΕΣΣΑΛΟΝΙΚΗΣ ΜΑΡΤΙΟΣ 2020 | data files | 1 | valid at the level of the dataset; 9 fields with the type, none of them with a documented meaning |
| S27 ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 463/Δ/1998-07-03) | map images | by hand | no valid description at the level of the dataset (no data file: map images); data without records, judged with a datasheet: 2 when the documentation says what the data contain, how they were collected and for which uses they are suitable; otherwise 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S28 Σχέδιο ΠΕ περιοχής Ατσαλένιο \| Μωσαϊκό | map images | by hand | no valid description at the level of the dataset (no file of the dataset was obtained (map images)); 1 at most, since no file was obtained: 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S29 ΠΙΝΑΚΕΣ ΤΙΜΟΛΗΨΙΩΝ ΣΥΡΟΥ | data files | 1 | valid at the level of the dataset; the columns of 1 examined table are not written, their names being withheld (DECISIONS.md #29) |
| S30 Διάγραμμα Τροποποιήσεως του Ρυμοτομικού Σχεδίου της Πόλης Χα | map images | by hand | no valid description at the level of the dataset (no data file: map images); data without records, judged with a datasheet: 2 when the documentation says what the data contain, how they were collected and for which uses they are suitable; otherwise 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: yes) |
| S31 ΠΡΟΓΡΑΜΜΑΤΙΚΕΣ ΣΥΜΒΑΣΕΙΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ | data files | 1 | valid at the level of the dataset; 8 fields with the type, none of them with a documented meaning |
| S32 Περιβαλλοντικοί έλεγχοι έτους 2014 από τη Δ/νση Περιβάλλοντο | data files | 1 | valid at the level of the dataset; 8 fields with the type, none of them with a documented meaning |
| S33 Διάγραμμα - ΦΕΚ 130/Δ/2001-02-21 | map images | by hand | no valid description at the level of the dataset (no data file: map images); data without records, judged with a datasheet: 2 when the documentation says what the data contain, how they were collected and for which uses they are suitable; otherwise 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S34 Αποθετήριο ΤΕΧΝΗ | unavailable | by hand | no valid description at the level of the dataset (no file of the dataset was obtained); 1 at most, since no file was obtained: 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |
| S35 Συνεδριάσεις Επιτροπής Αθλητισμού & Παιδείας Περιφέρειας Αττ | documents | by hand | no valid description at the level of the dataset (required by the specification and missing: license; no data file: documents); data without records, judged with a datasheet: 2 when the documentation says what the data contain, how they were collected and for which uses they are suitable; otherwise 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: yes) |
| S36 Διάγραμμα Τροποποίησης - T1936A404_69912_500_01 | map images | by hand | no valid description at the level of the dataset (no file of the dataset was obtained (map images)); 1 at most, since no file was obtained: 1 when the documentation says more than the title about what the data contain or how they were collected, 0 when it only repeats the title (the description repeats the title: no) |

## The description at the level of the dataset

| Dataset | Required and missing | Licence of the resources | Licence field of the dataset | Creator read from | Date of publication | Resources | Files described | Named by the address | Data files | Checksums in the metadata | Media types in the metadata | Errors | Warnings | Messages of the validator |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| S01 | license | none (0 of 13) | cc-by | organisation of the dataset | 2026-09-03 (metadata_created) | 13 | 13 |  | 13 | 0 of 13 | 0 of 13 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S02 | none | CC_BY_4_0 (7 of 7) |  | organisation of the dataset | 2026-05-25 (metadata_created) | 7 | 7 |  | 4 | 0 of 7 | 6 of 7 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S03 | license | none (0 of 1) |  | organisation of the dataset (the creator field holds no name) | 2026-02-27 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S04 | none | CC_BY_4_0 (4 of 4) |  | creator field of the dataset | 2026-07-01 (metadata_created) | 4 | 4 |  | 4 | 2 of 4 | 0 of 4 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S05 | license | none (0 of 2) |  | creator field of the dataset | 2025-11-24 (metadata_created) | 2 | 2 |  | 0 | 0 of 2 | 0 of 2 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S06 | none | CC_BY_4_0 (12 of 12) |  | organisation of the dataset | 2025-11-18 (metadata_created) | 12 | 12 |  | 12 | 6 of 12 | 0 of 12 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S07 | none | CC_BY_4_0 (1 of 1) |  | creator field of the dataset | 2026-03-31 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 1 of 1 | 0 | 1 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. |
| S08 | none | CC_BY_4_0 (1 of 1) |  | creator field of the dataset | 2026-04-29 (metadata_created) | 1 | 1 | 1 | 1 | 1 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S09 | license | none (0 of 6) |  | creator field of the dataset | 2025-11-24 (metadata_created) | 6 | 6 |  | 6 | 0 of 6 | 6 of 6 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S10 | none | CC_BY_4_0 (1 of 1) |  | creator field of the dataset | 2026-03-19 (metadata_created) | 1 | 1 |  | 1 | 1 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S11 | license | none (0 of 1) |  | organisation of the dataset | 2026-02-27 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S12 | none | CC_BY_4_0 (13 of 13) |  | creator field of the dataset | 2026-03-06 (metadata_created) | 13 | 12 |  | 12 | 0 of 13 | 13 of 13 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S13 | none | CC_BY_4_0 (1 of 1) |  | organisation of the dataset (the creator field holds no name) | 2026-04-02 (metadata_created) | 1 | 1 |  | 1 | 1 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S14 | none | CC_BY_4_0 (132 of 132) |  | creator field of the dataset | 2026-04-08 (metadata_created) | 132 | 130 |  | 130 | 0 of 132 | 132 of 132 | 0 | 1 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. |
| S15 | none | CC_BY_4_0 (3 of 3) |  | creator field of the dataset | 2026-06-15 (metadata_created) | 3 | 3 |  | 3 | 2 of 3 | 3 of 3 | 0 | 1 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. |
| S16 | none | CC_BY_4_0 (1 of 1) |  | organisation of the dataset (the creator field holds no name) | 2026-04-27 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 1 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. |
| S17 | none | CC_BY_4_0 (2 of 2) |  | organisation of the dataset | 2026-03-14 (metadata_created) | 2 | 0 |  | 0 | 0 of 2 | 1 of 2 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S18 | none | CC_BY_4_0 (7 of 7) |  | organisation of the dataset | 2026-05-21 (metadata_created) | 7 | 7 |  | 4 | 0 of 7 | 6 of 7 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S19 | none | CC_BY_4_0 (1 of 1) | cc-by | organisation of the dataset | 2026-05-13 (metadata_created) | 1 | 1 |  | 1 | 1 of 1 | 1 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S20 | none | CC_BY_4_0 (1 of 1) |  | organisation of the dataset (the creator field holds no name) | 2026-03-30 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S21 | none | CC_BY_4_0 (6 of 6) |  | organisation of the dataset | 2026-03-14 (metadata_created) | 6 | 5 |  | 4 | 0 of 6 | 5 of 6 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S22 | none | CC_BY_4_0 (1 of 1) |  | organisation of the dataset (the creator field holds no name) | 2026-05-14 (metadata_created) | 1 | 1 |  | 0 | 0 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S23 | none | CC_BY_4_0 (1 of 1) | cc-zero | organisation of the dataset | 2025-11-17 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S24 | none | CC_BY_4_0 (7 of 7) |  | organisation of the dataset | 2025-11-18 (metadata_created) | 7 | 7 |  | 7 | 7 of 7 | 7 of 7 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S25 | none | CC_BY_4_0 (1 of 1) | other-open | organisation of the dataset | 2025-11-18 (metadata_created) | 1 | 1 |  | 1 | 1 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S26 | none | CC_BY_4_0 (1 of 1) | notspecified | organisation of the dataset | 2025-11-18 (metadata_created) | 1 | 1 |  | 1 | 0 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S27 | none | CC_BY_4_0 (3 of 3) |  | organisation of the dataset | 2026-05-22 (metadata_created) | 3 | 3 |  | 0 | 0 of 3 | 2 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S28 | none | CC_BY_4_0 (3 of 3) |  | organisation of the dataset | 2026-05-23 (metadata_created) | 3 | 0 |  | 0 | 0 of 3 | 2 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S29 | none | CC_BY_4_0 (1 of 1) | notspecified | organisation of the dataset | 2025-11-18 (metadata_created) | 1 | 1 |  | 1 | 1 of 1 | 0 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S30 | none | CC_BY_4_0 (3 of 3) |  | organisation of the dataset | 2026-05-22 (metadata_created) | 3 | 3 |  | 0 | 0 of 3 | 2 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S31 | none | CC_BY_4_0 (3 of 3) | notspecified | organisation of the dataset | 2025-11-18 (metadata_created) | 3 | 3 |  | 3 | 3 of 3 | 0 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S32 | none | CC_BY_4_0 (2 of 2) | notspecified | organisation of the dataset | 2025-11-17 (metadata_created) | 2 | 2 |  | 2 | 2 of 2 | 0 of 2 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S33 | none | CC_BY_4_0 (3 of 3) |  | organisation of the dataset | 2026-05-22 (metadata_created) | 3 | 3 |  | 0 | 0 of 3 | 2 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S34 | none | CC0 (1 of 1) |  | creator field of the dataset | 2026-05-05 (metadata_created) | 1 | 0 |  | 0 | 0 of 1 | 1 of 1 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S35 | license | none (0 of 1) |  | creator field of the dataset | 2026-06-13 (metadata_created) | 1 | 1 |  | 0 | 0 of 1 | 0 of 1 | 0 | 3 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/license" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |
| S36 | none | CC_BY_4_0 (3 of 3) |  | organisation of the dataset | 2026-05-22 (metadata_created) | 3 | 0 |  | 0 | 0 of 3 | 2 of 3 | 0 | 2 | Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist. ; Property "https://schema.org/version" is recommended, but does not exist. |

## The fields

Fields by the format of their file: csv: 482, geojson: 19, gtfs: 223, json: 118, rdf: 34, shapefile: 25, xls: 68, xlsx: 29. The column is given as the way to read the values only for delimited text (csv, gtfs).

| Dataset | Tables examined | Outside the described files | Names withheld | Without a list of columns | Record sets | Fields | Types | Formats | With a documented meaning | Source of the meaning | DataStore tables |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | ---: |
| S01 | 14 |  |  |  | 1 | 2 | date: 1, text: 1 | shapefile: 2 | 2 | criteria/field_descriptions.csv: 2 |  |
| S02 | 4 |  |  | 1 | 2 | 14 | number: 4, text: 10 | csv: 8, geojson: 6 | 0 |  |  |
| S03 | 6 |  |  |  | 6 | 50 | date: 1, integer: 10, number: 3, text: 36 | gtfs: 50 | 50 | GTFS Schedule Reference: 50 |  |
| S04 | 2 |  |  |  | 2 | 28 | number: 6, text: 22 | shapefile: 14, xls: 14 | 0 |  | 2 |
| S05 | 2 | 2 |  |  | 0 | 0 |  |  | 0 |  |  |
| S06 | 1 |  |  |  | 1 | 2 | number: 1, text: 1 | xls: 2 | 2 | criteria/field_descriptions.csv: 2 |  |
| S07 | 1 |  |  |  | 1 | 18 | integer: 4, number: 9, text: 5 | csv: 18 | 18 | criteria/field_descriptions.csv: 18 | 1 |
| S08 | 1 |  |  |  | 1 | 29 | number: 26, text: 3 | xlsx: 29 | 0 |  | 1 |
| S09 | 3 |  |  |  | 2 | 5 | number: 3, text: 2 | xls: 5 | 0 |  |  |
| S10 | 1 |  |  |  | 1 | 363 | number: 361, text: 2 | csv: 363 | 0 |  | 1 |
| S11 | 8 |  |  |  | 8 | 51 | date: 3, integer: 14, number: 5, text: 29 | gtfs: 51 | 51 | GTFS Schedule Reference: 51 |  |
| S12 | 9 |  |  |  | 9 | 74 | date: 3, integer: 12, number: 6, text: 53 | gtfs: 74 | 71 | GTFS Schedule Reference: 71 |  |
| S13 | 7 |  |  |  | 7 | 48 | date: 2, integer: 13, number: 5, text: 28 | gtfs: 48 | 48 | GTFS Schedule Reference: 48 | 1 |
| S14 | 11 |  |  |  | 11 | 118 | boolean: 7, date and time: 3, integer: 5, number: 24, text: 78, time: 1 | json: 118 | 0 |  |  |
| S15 | 3 |  |  |  | 1 | 3 | number: 2, text: 1 | csv: 3 | 0 |  | 2 |
| S16 | 1 |  |  |  | 1 | 9 | number: 2, text: 7 | shapefile: 9 | 0 |  |  |
| S17 | 2 | 2 |  |  | 0 | 0 |  |  | 0 |  |  |
| S18 | 4 |  |  | 1 | 2 | 28 | integer: 1, number: 7, text: 20 | csv: 15, geojson: 13 | 0 |  |  |
| S19 | 1 |  |  |  | 1 | 57 | integer: 12, number: 25, text: 18, time: 2 | csv: 57 | 0 |  | 1 |
| S20 | 55 |  |  |  | 2 | 18 | date: 1, integer: 2, number: 13, text: 2 | csv: 18 | 0 |  |  |
| S21 | 56 |  |  |  | 1 | 14 | number: 13, text: 1 | xls: 14 | 14 | criteria/field_descriptions.csv: 14 |  |
| S22 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S23 | 1 |  |  |  | 1 | 34 | date: 2, date and time: 1, integer: 1, link: 15, text: 15 | rdf: 34 | 0 |  |  |
| S24 | 7 |  | 7 |  | 0 | 0 |  |  | 0 |  | 7 |
| S25 | 1 |  |  |  | 1 | 8 | number: 4, text: 4 | xls: 8 | 0 |  |  |
| S26 | 3 |  |  |  | 1 | 9 | integer: 1, number: 6, text: 2 | xls: 9 | 0 |  | 1 |
| S27 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S28 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S29 | 1 |  | 1 |  | 0 | 0 |  |  | 0 |  |  |
| S30 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S31 | 1 |  |  |  | 1 | 8 | number: 1, text: 7 | xls: 8 | 0 |  |  |
| S32 | 2 |  |  |  | 2 | 8 | date: 2, text: 6 | xls: 8 | 0 |  |  |
| S33 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S34 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S35 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |
| S36 | 0 |  |  |  | 0 | 0 |  |  | 0 |  |  |

## Evidence for the datasets judged by hand

From `08_documentation_checks.py`: what the metadata offer beyond the title.

| Dataset | Description (characters) | Repeats the title | Documents next to the data | Pages of the publisher |
| --- | ---: | --- | --- | --- |
| S01 | 407 | no |  |  |
| S03 | 2027 | no |  |  |
| S05 | 665 | no |  | https://opendata.attica.gov.gr/content/genikh-dieythynsh-dhmosias-ygeias-kai-koinwnikhs-merimnas/d-nsh-koinwnikhs-merimnas/43-lista-me-monades-frontidas-hlikiwmenwn |
| S09 | 58 | yes |  | https://opendata.attica.gov.gr/content/genikh-dieythynsh-dhmosias-ygeias-kai-koinwnikhs-merimnas/d-nsh-dhmosias-ygeias/92-lista-anamonhs-iatrwn-gia-eidikeysh-sta-nosokomeia-attikhs-2020 |
| S11 | 2040 | no |  |  |
| S17 | 956 | no |  | https://www.apdkritis.gov.gr/ ; https://www.apdkritis.gov.gr/el/διοικητική-δομή/γενική-διεύθυνση-χωροταξικής-περιβαλλοντικής-αγροτικης-πολιτικής/διεύθυνση-τεχνικού-ελέγχου/τμήμα-φυσικών-πόρων ; https://geoportal.apdkritis.gov.gr/webgis/rest/services/ape/ape_polites/MapServer/0 ; https://geoportal.apdkritis.gov.gr/webgis/rest/services/ape/ape_polites/MapServer/1 ; https://geoportal.apdkritis.gov.gr/webgis/rest/services/ape/ape_polites/MapServer/2 ; https://geoportal.apdkritis.gov.gr/gis/home/item.html?id=6d4747620fcd41d9a07ff152a86dd326 ; and 1 more |
| S22 | 486 | no |  |  |
| S27 | 173 | no |  |  |
| S28 | 61 | no |  |  |
| S30 | 81 | yes |  |  |
| S33 | 112 | no |  |  |
| S34 | 841 | no |  | http://repository-tehni-thes.ekt.gr/tehni-thes ; https://www.searchculture.gr/aggregator/portal/collections/tehni_thes |
| S35 | 64 | yes |  | https://opendata.attica.gov.gr/content/genikh-dieythynsh-eswterikhs-leitoyrgias/d-nsh-anthrwpinoy-dynamikoy/443-synedriaseis-epitrophs-athlhtismoy-paideias-perifereias-attikhs |
| S36 | 277 | no |  |  |
