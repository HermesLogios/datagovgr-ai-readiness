# API and bulk download of the high-value datasets of the sample (M10), snapshot of 2026-10-24

Produced by `scripts/07_api_checks.py`. Every API was called anonymously and asked only for its description and for the number of its records; this report contains no records of the data. The scores are proposals, reviewed and recorded in `DECISIONS.md`.

High-value datasets: 24. Proposed M10: 1: 15, 2: 9.

## Compliance columns (Regulation (EU) 2023/138, Article 3; DECISIONS.md #28)

| Dataset | Category | API | Bulk download | Terms of use and documentation of the API | M10 |
| --- | --- | --- | --- | --- | ---: |
| S01 Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος  | Geospatial | no | yes | - | 1 |
| S02 Καλλικρατικοί Δήμοι | Geospatial | yes | yes | no | 1 |
| S03 Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ) | Geospatial | no | yes | - | 1 |
| S04 Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υ | Geospatial | yes | yes | yes | 2 |
| S05 Λίστα με Μονάδες Φροντίδας Ηλικιωμένων | Geospatial | no | yes | - | 1 |
| S06 Τροχαία ατυχήματα | Statistics | no | yes | - | 1 |
| S07 Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος | Statistics | yes | yes | yes | 2 |
| S08 "ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ,  | Statistics | yes | yes | yes | 2 |
| S09 Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής | Statistics | no | yes | - | 1 |
| S10 ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ) | Statistics | yes | yes | yes | 2 |
| S11 Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ) | Mobility | no | yes | - | 1 |
| S12 Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης | Mobility | no | yes | - | 1 |
| S13 Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS | Mobility | partly | yes | yes | 1 |
| S14 Υπηρεσίες Δήμου Πατρέων | Mobility | no | yes | - | 1 |
| S15 ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ | Mobility | yes | yes | yes | 2 |
| S16 Θεσμοθετημένες περιοχές NATURA 2000 | Earth observation and environment | no | yes | - | 1 |
| S17 Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ | Earth observation and environment | no | yes | - | 1 |
| S18 Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018 | Earth observation and environment | yes | yes | yes | 2 |
| S19 Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ | Meteorological | yes | yes | yes | 2 |
| S20 Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-202 | Meteorological | no | yes | - | 1 |
| S21 Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης | Meteorological | yes | yes | yes | 2 |
| S22 Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδ | Companies and company ownership | no | yes | - | 1 |
| S23 Athens Business Open Data - STIRData model | Companies and company ownership | no | yes | - | 1 |
| S24 ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ) | Companies and company ownership | yes | yes | yes | 2 |

## Proposed scores

| Dataset | M10 | Reason | Notes |
| --- | ---: | --- | --- |
| S01 | 1 | no API; bulk download: 13 files behind direct links |  |
| S02 | 1 | WFS answers anonymously with 326 records (file: 326); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: no; bulk download: 4 files behind direct links (4 of them complete exports of a layer through WFS) |  |
| S03 | 1 | no API; bulk download: 1 file behind direct links |  |
| S04 | 2 | DataStore of the portal answers anonymously with 13,682 records (file: 13,682); DataStore of the portal answers anonymously with 14,439 records (file: 14,439); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 4 files behind direct links |  |
| S05 | 1 | no API; bulk download: export of the complete list from an application, by hand: the two lists of the application, exported to Excel by hand on 2026-11-05, since both resources are web pages |  |
| S06 | 1 | no API; bulk download: 12 files behind direct links |  |
| S07 | 2 | DataStore of the portal answers anonymously with 11,490 records (file: 11,490); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 1 file behind direct links |  |
| S08 | 2 | DataStore of the portal answers anonymously with 853 records (file: 852); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 1 file behind direct links |  |
| S09 | 1 | no API; bulk download: 6 files behind direct links |  |
| S10 | 2 | DataStore of the portal answers anonymously with 511 records (file: 511); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 1 file behind direct links |  |
| S11 | 1 | no API; bulk download: 1 file behind direct links |  |
| S12 | 1 | no API; bulk download: 12 files behind direct links |  |
| S13 | 1 | DataStore of the portal answers anonymously with 1 record (file: 2,086,873 in 7 tables); serves the dataset completely: no; documentation of the API: yes; terms of use of the API: yes; bulk download: 1 file behind direct links |  |
| S14 | 1 | no API; bulk download: 130 files behind direct links |  |
| S15 | 2 | DataStore of the portal answers anonymously with 11 records (file: 11); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 3 files behind direct links |  |
| S16 | 1 | no API; bulk download: 1 file behind direct links |  |
| S17 | 1 | ArcGIS REST declared but not usable: HTTP 200; error 499; Token Required; the service gave no description; ArcGIS REST declared but not usable: HTTP 200; error 403; You do not have permissions to access this resource or perform this operation.; bulk download: export of the complete list from an application, by hand: the list of the application linked in the description, exported by hand on 2026-11-15 (CSV and GeoJSON; JSON not judged) |  |
| S18 | 2 | WFS answers anonymously with 2 records (file: 2); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 4 files behind direct links (4 of them complete exports of a layer through WFS) |  |
| S19 | 2 | DataStore of the portal answers anonymously with 64,275 records (file: 62,437); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 1 file behind direct links |  |
| S20 | 1 | no API; bulk download: 1 file behind direct links |  |
| S21 | 2 | ArcGIS REST answers anonymously with 3,355 records, 2,369 of them in its largest layer or table (examined files of the dataset: 2,363); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 5 files behind direct links |  |
| S22 | 1 | no API; bulk download: 1 file behind direct links |  |
| S23 | 1 | no API; bulk download: 1 file behind direct links |  |
| S24 | 2 | DataStore of the portal answers anonymously with 148 records (file: 147); DataStore of the portal answers anonymously with 261 records (file: 255); DataStore of the portal answers anonymously with 28 records (file: 28); DataStore of the portal answers anonymously with 73 records (file: 70); DataStore of the portal answers anonymously with 47 records (file: 47); DataStore of the portal answers anonymously with 115 records (file: 115); DataStore of the portal answers anonymously with 253 records (file: 250); serves the dataset completely: yes; documentation of the API: yes; terms of use of the API: yes; bulk download: 7 files behind direct links |  |

## APIs tested

| Dataset | Resource | Kind | Tested on | Works anonymously | Answer | Records through the API | Records of the file | Comparison | Documentation | Terms of use | Notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| S02 | r002 | WFS | 2026-11-10 | yes | number of features of the layer | 326 | 326 | complete | yes (capabilities document of the service (78 layers, the layer among them)) | no (capabilities: Fees empty, AccessConstraints empty) | provider: Special Secretariat for Water |
| S04 | r002 | DataStore of the portal | 2026-11-10 | yes | table with 14 fields | 13682 | 13682 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S04 | r004 | DataStore of the portal | 2026-11-10 | yes | table with 14 fields | 14439 | 14439 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S07 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 18 fields | 11490 | 11490 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S08 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 29 fields | 853 | 852 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S10 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 363 fields | 511 | 511 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S13 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 8 fields | 1 | 2086873 | partial | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S15 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 3 fields | 11 | 11 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S15 | r002 | DataStore of the portal | 2026-11-10 | yes | table with 3 fields | 11 | 11 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S17 | description | ArcGIS REST | 2026-11-16 | no | HTTP 200; error 499; Token Required; the service gave no description |  |  |  | no | no | address written in the description of the dataset; the service is not open to everyone: it asks for a token or an account with permission |
| S17 | r002 | ArcGIS REST | 2026-11-16 | no | HTTP 200; error 403; You do not have permissions to access this resource or perform this operation. |  |  |  | no | no | the item is not shared with everyone: the portal asks for an account with permission |
| S18 | r002 | WFS | 2026-11-10 | yes | number of features of the layer | 2 | 2 | complete | yes (capabilities document of the service (172 layers, the layer among them)) | yes (capabilities: Fees "NONE", AccessConstraints "NONE") | provider: Municipality of Syros - Ermoupolis |
| S19 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 57 fields | 64275 | 62437 | more records | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S21 | r006 | ArcGIS REST | 2026-11-10 | yes | records of 5 of 5 layers and tables | 3355 | 2363 | complete | yes (description of the service (1 layer, 4 tables)) | yes (terms of use of the item: "CC BY 4.0 License") | item of kind Feature Service, access public; records per layer or table: layer 0: 56, table 1: 389, table 2: 35, table 3: 506, table 4: 2,369 |
| S24 | r001 | DataStore of the portal | 2026-11-10 | yes | table with 6 fields | 148 | 147 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r002 | DataStore of the portal | 2026-11-10 | yes | table with 7 fields | 261 | 255 | more records | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r003 | DataStore of the portal | 2026-11-10 | yes | table with 7 fields | 28 | 28 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r004 | DataStore of the portal | 2026-11-10 | yes | table with 7 fields | 73 | 70 | more records | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r005 | DataStore of the portal | 2026-11-10 | yes | table with 6 fields | 47 | 47 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r006 | DataStore of the portal | 2026-11-10 | yes | table with 7 fields | 115 | 115 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
| S24 | r007 | DataStore of the portal | 2026-11-10 | yes | table with 6 fields | 253 | 250 | complete | yes (https://data-gov-gr.gitbook.io/guides/texnika-egxeiridia/data.gov.gr/dedomena/tekmiriosi-api) | yes (https://data.gov.gr/pages/terms-of-use) |  |
