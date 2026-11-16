# Suitability of the datasets of the sample for retrieval (AI5), snapshot of 2026-10-24

Produced by `scripts/11_retrieval_checks.py`. The tables collect the evidence for the review of the criterion; a score is proposed only where a rule decides without judgement, and the final scores are recorded in `DECISIONS.md`. Of the files only counts and names of columns are written: this report contains no value of a record.

## Proposals

Proposed AI5: 0: 6, 1: 16, 2: 12, by hand: 2.

| Dataset | Kind of data | Files | Proposal | Reason |
| --- | --- | --- | --- | --- |
| S01 Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος  | data files | parts | 1 | worst of 13 files: no identifier of the records in 4 of 14 tables: r001, file Periferia_Anatolikis_Makedonias_kai_Thrakis_20261029.shp: no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column; r004, file Periferia_Ditikis_Makedonias_20261029.shp: no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column; and 2 more |
| S02 Καλλικρατικοί Δήμοι | data files | formats | 2 | best of 4 formats, r002: records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (id); the file is a resource of the dataset |
| S03 Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ) | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in each of the 6 examined tables (one record; service_id + date; route_id; trip_id + stop_sequence; and 2 more); the file is a resource of the dataset |
| S04 Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υ | data files | series | 2 | best of 2 formats, r003: records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (KWDIKOS_EM); the file is a resource of the dataset |
| S05 Λίστα με Μονάδες Φροντίδας Ηλικιωμένων | no data file among the resources obtained | parts | 1 | worst of 2 files: rows that are not records in 2 of 2 tables: r001_manual, sheet "Sheet1": 1 title or note row above the header; r002_manual, sheet "Sheet1": 1 title or note row above the header; the examined tables are not resources of the dataset: no link to the source |
| S06 Τροχαία ατυχήματα | data files | series | 1 | rows that are not records in 1 of 1 table: r012, sheet "Τροχαία ατυχήματα 2025": 4 title or note rows above the header; 1 empty row inside the table; 2 totals rows |
| S07 Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (Έτος + Μήνας ID + Περιφερειακή Ενότητα + Είδος Γάλακτος ID); the file is a resource of the dataset |
| S08 "ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ,  | data files | single | 1 | rows that are not records in 1 of 1 table: r001, sheet "ΔΕ ΕΚΠΑΙΔ τελικό": 1 totals row |
| S09 Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής | data files | series | 1 | no identifier of the records in 1 of 3 tables: r001, sheet "2026": no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, ΝΟΣΟΚΟΜΕΙΟ, repeats an earlier value in 10 records; 10 records repeat an earlier one in every column |
| S10 ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ) | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (CODE); the file is a resource of the dataset |
| S11 Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ) | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in each of the 8 examined tables (one record; service_id; service_id + date; route_id; and 4 more); the file is a resource of the dataset |
| S12 Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης | data files | series | 1 | no identifier of the records in 1 of 9 tables: r013, file translations.txt: the key of the GTFS reference (table_name + field_name + language + record_id + record_sub_id + field_value) is met again in 2,196 records; 2,120 records repeat an earlier one in every column |
| S13 Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in each of the 7 examined tables (one record; service_id; route_id; shape_id + shape_pt_sequence; and 3 more); the file is a resource of the dataset |
| S14 Υπηρεσίες Δήμου Πατρέων | data files | series | 2 | worst of 11 files: records that can be split as they are, text without damaged characters and an identifier of every record in each of the 11 examined tables (sensorvar_description; sensorvar_id; id; one record; and 3 more); the file is a resource of the dataset |
| S15 ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ | data files | formats | 2 | best of 3 formats, r001: records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (address); the file is a resource of the dataset |
| S16 Θεσμοθετημένες περιοχές NATURA 2000 | data files | single | 1 | no identifier of the records in 1 of 1 table: r001, file gr_natura_v31_union_final.shp: no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, SITECODE, repeats an earlier value in 165 records; the rows are only numbered (OBJECTID_1) |
| S17 Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ | no data file among the resources obtained | formats | 1 | best of 2 formats, r002_csv_manual: the examined tables are not resources of the dataset: no link to the source |
| S18 Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018 | data files | formats | 2 | best of 4 formats, r002: records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (code_12); the file is a resource of the dataset |
| S19 Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in the examined table (yyyyMMddHHmm); the file is a resource of the dataset |
| S20 Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-202 | data files | single | 2 | records that can be split as they are, text without damaged characters and an identifier of every record in each of the 55 examined tables (Date; stations); the file is a resource of the dataset |
| S21 Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης | data files | parts | 1 | worst of 4 files: rows that are not records in 56 of 56 tables: r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αβδού Ηρακλείου 02.xls, sheet "ΑΒΔΟΥ": 7 title or note rows above the header; 3 totals rows; r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αγ. Βαρβάρα Ηρακλείου 02.xls, sheet "ΑΓ. ΒΑΡΒΑΡΑ": 7 title or note rows above the header; 3 totals rows; 1 sub-heading row inside the table; and 54 more |
| S22 Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδ | documents | none | 1 | PDF with text that can be extracted (3 of 3 pages): usable after the extraction of the text |
| S23 Athens Business Open Data - STIRData model | data files | single | by hand | r001: 160,554 subjects with a URI; damaged text in 3 cells |
| S24 ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ) | data files | parts | 1 | worst of 7 files: rows that are not records in 2 of 7 tables: r002: 3 empty rows inside the table; 2 note rows below the table; r004: 2 note rows below the table; no identifier of the records in 5 of 7 tables: r001: no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, column 2, repeats an earlier value in 7 records; r003: no column or combination of up to 4 columns is filled and different in every record; 9 records repeat an earlier one in every column other than those that number the rows; the rows are only numbered (column 1); and 3 more |
| S25 ΣΤΑΤΙΣΤΙΚΑ ΔΙΑΤΡΟΦΗΣ ΦΕΒΡΟΥΑΡΙΟΥ 2017 | data files | single | 1 | rows that are not records in 1 of 1 table: r001, sheet "ΙΑΝΟΥΑΡΙΟΣ - ΦΕΒΡΟΥΑΡΙΟΣ 2017": 1 title or note row above the header |
| S26 ΣΤΑΤΙΣΤΙΚΑ ΙΧΘΥΟΣΚΑΛΑΣ ΘΕΣΣΑΛΟΝΙΚΗΣ ΜΑΡΤΙΟΣ 2020 | data files | single | 1 | rows that are not records in 3 of 3 tables: r001, sheet "Εγχώρια": 5 title or note rows above the header; 6 totals rows; 6 sub-heading rows inside the table; 1 note row below the table; numbers stored as text in 1 column; r001, sheet "Ευρωπαϊκής Ένωσης": 5 title or note rows above the header; 5 totals rows; 5 sub-heading rows inside the table; 1 note row below the table; and 1 more |
| S27 ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 463/Δ/1998-07-03) | map images | none | 0 | images of maps: no text that can be extracted |
| S28 Σχέδιο ΠΕ περιοχής Ατσαλένιο \| Μωσαϊκό | map images | none | 0 | images of maps: no text that can be extracted |
| S29 ΠΙΝΑΚΕΣ ΤΙΜΟΛΗΨΙΩΝ ΣΥΡΟΥ | data files | single | 1 | rows that are not records in 1 of 1 table: r001, sheet "ΠΙΝΑΚΑΣ ΤΙΜΟΛΗΨΙΩΝ 18-01-2016": 4 tables in one sheet; 7 title or note rows above the header; 5 sub-heading rows inside the table; 1 note row below the table |
| S30 Διάγραμμα Τροποποιήσεως του Ρυμοτομικού Σχεδίου της Πόλης Χα | map images | none | 0 | images of maps: no text that can be extracted |
| S31 ΠΡΟΓΡΑΜΜΑΤΙΚΕΣ ΣΥΜΒΑΣΕΙΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ | data files | series | 1 | rows that are not records in 1 of 1 table: r003, sheet "ΥΠΟΓΕΓΡΑΜΜΕΝΕΣ ΣΥΜΒΑΣΕΙΣ (ΝΕΕΣ)": merged cells inside the data (6); 6 sub-heading rows inside the table; numbers stored as text in 1 column |
| S32 Περιβαλλοντικοί έλεγχοι έτους 2014 από τη Δ/νση Περιβάλλοντο | data files | series | 1 | rows that are not records in 2 of 2 tables: r002, sheet "Π.Ε. Αχαϊας": 1 title or note row above the header; r002, sheet "Π.Ε. Ηλείας": 1 title or note row above the header |
| S33 Διάγραμμα - ΦΕΚ 130/Δ/2001-02-21 | map images | none | 0 | images of maps: no text that can be extracted |
| S34 Αποθετήριο ΤΕΧΝΗ | unavailable | none | 0 | no file of the dataset was obtained: no content that can be extracted |
| S35 Συνεδριάσεις Επιτροπής Αθλητισμού & Παιδείας Περιφέρειας Αττ | documents | none | by hand | the documents are not among the files obtained: they are judged in the review, 1 when a document holds text that can be extracted, 0 when it is a scanned image |
| S36 Διάγραμμα Τροποποίησης - T1936A404_69912_500_01 | map images | none | 0 | images of maps: no text that can be extracted |

## Layout and text of the examined tables

A table is read when every row after its header is a record; the other tables need cleaning first. The cells with text include the names of the columns.

| Dataset | Tables examined | Read | Rows that are not records | Not read | Records read | Encoding | Cells with text | With Greek letters | With damaged text | Kinds of damage |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| S01 | 14 | 14 | 0 | 0 | 13,987,154 | utf-8: 14 tables | 473,853 | 473,825 | 0 |  |
| S02 | 4 | 3 | 0 | 1 | 978 | utf-8-sig: 2 tables, utf-8: 1 table | 1,650 | 652 | 326 | question marks in the place of letters: 326 |
| S03 | 6 | 6 | 0 | 0 | 1,710,510 | utf-8-sig: 6 tables | 17,440 | 17,129 | 0 |  |
| S04 | 2 | 1 | 1 | 0 | 14,439 | utf-8: 1 table | 106,466 | 106,450 | 0 |  |
| S05 | 2 | 0 | 2 | 0 | 0 |  | 0 | 0 | 0 |  |
| S06 | 1 | 0 | 1 | 0 | 0 |  | 0 | 0 | 0 |  |
| S07 | 1 | 1 | 0 | 0 | 11,490 | utf-8-sig: 1 table | 34,489 | 34,488 | 0 |  |
| S08 | 1 | 0 | 1 | 0 | 0 |  | 0 | 0 | 0 |  |
| S09 | 3 | 3 | 0 | 0 | 183 |  | 190 | 190 | 0 |  |
| S10 | 1 | 1 | 0 | 0 | 511 | utf-8-sig: 1 table | 514 | 506 | 0 |  |
| S11 | 8 | 8 | 0 | 0 | 4,344,597 | utf-8-sig: 8 tables | 4,464,931 | 104,009 | 0 |  |
| S12 | 9 | 9 | 0 | 0 | 1,112,170 | utf-8-sig: 9 tables | 62,205 | 32,695 | 0 |  |
| S13 | 7 | 7 | 0 | 0 | 2,086,873 | utf-8-sig: 7 tables | 2,160,701 | 65,286 | 0 |  |
| S14 | 11 | 11 | 0 | 0 | 926 | utf-8-sig: 11 tables | 7,907 | 1,161 | 0 |  |
| S15 | 3 | 2 | 1 | 0 | 22 | utf-8-sig: 2 tables | 28 | 22 | 0 |  |
| S16 | 1 | 1 | 0 | 0 | 593 | utf-8: 1 table | 2,373 | 788 | 0 |  |
| S17 | 2 | 2 | 0 | 0 | 90 | utf-8-sig: 2 tables | 479 | 462 | 0 |  |
| S18 | 4 | 3 | 0 | 1 | 6 | utf-8-sig: 2 tables, utf-8: 1 table | 63 | 8 | 4 | question marks in the place of letters: 4 |
| S19 | 1 | 1 | 0 | 0 | 62,437 | utf-8-sig: 1 table | 57 | 0 | 0 |  |
| S20 | 55 | 55 | 0 | 0 | 276,156 | utf-8-sig: 55 tables | 265,682 | 0 | 0 |  |
| S21 | 56 | 0 | 56 | 0 | 0 |  | 0 | 0 | 0 |  |
| S23 | 1 | 1 | 0 | 0 | 160,554 |  | 260,708 | 127,816 | 3 | characters of another encoding (control characters): 3 |
| S24 | 7 | 5 | 2 | 0 | 587 | utf-8-sig: 5 tables | 2,533 | 2,527 | 0 |  |
| S25 | 1 | 0 | 1 | 0 | 0 |  | 0 | 0 | 0 |  |
| S26 | 3 | 0 | 3 | 0 | 0 |  | 0 | 0 | 0 |  |
| S29 | 1 | 0 | 1 | 0 | 0 |  | 0 | 0 | 0 |  |
| S31 | 1 | 0 | 1 | 0 | 0 |  | 0 | 0 | 0 |  |
| S32 | 2 | 0 | 2 | 0 | 0 |  | 0 | 0 | 0 |  |

## Identifiers of the records

| Dataset | Tables with an identifier | Without | Identifiers | Kinds of their columns | With a column of text | Columns that number the rows | Records that repeat an earlier one, the numbers of the rows left out | Link to the source |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | --- |
| S01 | 10 | 4 | KAEK (code) | code: 10 tables | no |  | 4 | permanent address of the resource on the portal (DECISIONS.md #33) |
| S02 | 3 | 0 | id (code) | code: 3 tables | no | objectid, FID |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S03 | 6 | 0 | service_id + date (code); route_id (code); trip_id + stop_sequence (code); stop_id (code); and 1 more | code: 5 tables | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S04 | 1 | 0 | KWDIKOS_EM (code) | code: 1 table | no | OBJECTID |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S07 | 1 | 0 | Έτος + Μήνας ID + Περιφερειακή Ενότητα + Είδος Γάλακτος ID (period, text, code) | period, text, code: 1 table | yes | _id |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S09 | 2 | 1 | ΝΟΣΟΚΟΜΕΙΟ (text) | text: 2 tables | yes |  | 10 | permanent address of the resource on the portal (DECISIONS.md #33) |
| S10 | 1 | 0 | CODE (code) | code: 1 table | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S11 | 8 | 0 | service_id (code); service_id + date (code); route_id (code); shape_id + shape_pt_sequence (code); and 3 more | code: 7 tables | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S12 | 8 | 1 | service_id + date (code); route_id (code); shape_id + shape_pt_sequence (code); trip_id + stop_sequence (code); and 2 more | code: 6 tables | no |  | 2120 | permanent address of the resource on the portal (DECISIONS.md #33) |
| S13 | 7 | 0 | service_id (code); route_id (code); shape_id + shape_pt_sequence (code); trip_id + stop_sequence (code); and 2 more | code: 6 tables | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S14 | 11 | 0 | sensorvar_description (text); sensorvar_id (code); id (code); mysensor_id (code); and 2 more | code: 7 tables, text: 2 tables | yes |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S15 | 2 | 0 | address (text) | text: 2 tables | yes |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S16 | 0 | 1 |  |  |  | OBJECTID_1 |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S17 | 1 | 1 | Συντεταγμένες Χ (ΕΓΣΑ) (text) | text: 1 table | yes | objectid, Α/Α, OBJECTID |  | none: the examined tables are not resources of the dataset |
| S18 | 3 | 0 | code_12 (code) | code: 3 tables | no | cid, objectid_1, objectid, FID |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S19 | 1 | 0 | yyyyMMddHHmm (period) | period: 1 table | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S20 | 55 | 0 | Date (period); stations (text) | period: 54 tables, text: 1 table | yes |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S23 | 1 | 0 | URI of the subject (link) | link: 1 table | no |  |  | permanent address of the resource on the portal (DECISIONS.md #33) |
| S24 | 0 | 5 |  |  |  | column 1 | 9 | permanent address of the resource on the portal (DECISIONS.md #33) |

## Tables that are not read, have no identifier or have damaged text

| Dataset | Table | Format | Layout | Records | Damaged cells | Outcome | Note |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| S01 | r001, file Periferia_Anatolikis_Makedonias_kai_Thrakis_20261029.shp | shapefile | records | 1343363 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column |
| S01 | r004, file Periferia_Ditikis_Makedonias_20261029.shp | shapefile | records | 871750 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column |
| S01 | r008, file Periferia_Kritis_20261029.shp | shapefile | records | 1308685 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column |
| S01 | r010, file Periferia_Peloponnisou_20261029.shp | shapefile | records | 1909312 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, KAEK, repeats an earlier value in 1 record; 1 record repeats an earlier one in every column |
| S02 | r004, file kallikratikoi_dimoi.shp | shapefile | records | 326 | 326 | by hand | damaged text in 326 cells |
| S02 | r005 | kml | records | 326 |  | not judged | not read: no list of columns for the format kml |
| S04 | r004, sheet "Φύλλο1" | xls | rows that are not records | 14439 |  | 1 | numbers stored as text in 1 column |
| S05 | r001_manual, sheet "Sheet1" | xlsx | rows that are not records | 9 |  | 1 | 1 title or note row above the header |
| S05 | r002_manual, sheet "Sheet1" | xlsx | rows that are not records | 143 |  | 1 | 1 title or note row above the header |
| S06 | r012, sheet "Τροχαία ατυχήματα 2025" | xls | rows that are not records | 7 |  | 1 | 4 title or note rows above the header; 1 empty row inside the table; 2 totals rows |
| S08 | r001, sheet "ΔΕ ΕΚΠΑΙΔ τελικό" | xlsx | rows that are not records | 852 |  | 1 | 1 totals row |
| S09 | r001, sheet "2026" | xls | records | 73 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, ΝΟΣΟΚΟΜΕΙΟ, repeats an earlier value in 10 records; 10 records repeat an earlier one in every column |
| S12 | r013, file translations.txt | gtfs | records | 4510 | 0 | 1 | the key of the GTFS reference (table_name + field_name + language + record_id + record_sub_id + field_value) is met again in 2,196 records; 2,120 records repeat an earlier one in every column |
| S15 | r002, sheet "Βιβλίο1" | xlsx | rows that are not records | 11 |  | 1 | numbers stored as text in 2 columns |
| S16 | r001, file gr_natura_v31_union_final.shp | shapefile | records | 593 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, SITECODE, repeats an earlier value in 165 records; the rows are only numbered (OBJECTID_1) |
| S17 | r002_csv_manual | csv | records | 45 | 0 | 1 | not a resource of the dataset, no link to the source |
| S17 | r002_geojson_manual | geojson | records | 45 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, topothesia, repeats an earlier value in 1 record; the rows are only numbered (OBJECTID) |
| S18 | r004, file lcv_pol_corine_land_cover_2012_2018.shp | shapefile | records | 2 | 4 | by hand | damaged text in 4 cells |
| S18 | r005 | kml | records | 2 |  | not judged | not read: no list of columns for the format kml |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αβδού Ηρακλείου 02.xls, sheet "ΑΒΔΟΥ" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αγ. Βαρβάρα Ηρακλείου 02.xls, sheet "ΑΓ. ΒΑΡΒΑΡΑ" | xls | rows that are not records | 40 |  | 1 | 7 title or note rows above the header; 3 totals rows; 1 sub-heading row inside the table |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αγ. Κύριλλος Ηρακλείου 02.xls, sheet "ΑΓΙΟΣ ΚΥΡΙΛΛΟΣ" | xls | rows that are not records | 44 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αρμάχα Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 43 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Ασήμι 02.xls, sheet "AGGALI95" | xls | rows that are not records | 43 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Αχεντριάς Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Βαγιωνιά Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Βορίζια Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 39 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Βόνη Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 38 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Γέργερη Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Δεματιι Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Ζαρός Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 53 |  | 1 | 7 title or note rows above the header; 28 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Καλύβια Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Καπετανιανά Ηρακλείου            02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Κασσάνοι Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 43 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Καστέλι Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 69 |  | 1 | 7 title or note rows above the header; 12 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Καψάλοι 02.xls, sheet "ΚΑΨΑΛΟΙ" | xls | rows that are not records | 20 |  | 1 | 7 title or note rows above the header; 19 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Κρουσώνας Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Λαγολιό 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Μεταξοχώρι Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 37 |  | 1 | 7 title or note rows above the header; 2 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Μορόνι  Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Παρτηρα Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Πραιτώρεια Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 38 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Προφήτης Ηλίας 02.xls, sheet "AGGALI95" | xls | rows that are not records | 40 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Πόμπια 02.xls, sheet "AGGALI95" | xls | rows that are not records | 60 |  | 1 | 7 title or note rows above the header; 21 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Τεφελι Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 43 |  | 1 | 7 title or note rows above the header; 4 empty rows inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Υ.Ε.Β. 02.xls, sheet "ΥΕΒ" | xls | rows that are not records | 30 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r002, file Ν. ΗΡΑΚΛΕΙΟΥ/Φοινικιά Ηρακλείου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 39 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Αγιος Γεώργιος 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/ΕΞΩ ΠΟΤΑΜΟΙ 02.xls, sheet "AGGALI95" | xls | rows that are not records | 70 |  | 1 | 7 title or note rows above the header; 12 empty rows inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Καλό Χωριό Λασιθίου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 67 |  | 1 | 7 title or note rows above the header; 13 empty rows inside the table; 3 totals rows; 1 sub-heading row inside the table; numbers stored as text in 1 column |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Κατσιδόνι 02.xls, sheet "AGGALI95" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Μάλλες Λασιθίου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Μαρωνιά Λασιθίου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 68 |  | 1 | 7 title or note rows above the header; 7 empty rows inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Μύθοι 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Νεάπολη Λασιθίου 02.xls, sheet "AGGALI95 (2)" | xls | rows that are not records | 66 |  | 1 | 7 title or note rows above the header; 15 empty rows inside the table; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Παλαιόκαστρο 02.xls, sheet "AGGALI95" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Παχειά Αμμος 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Σητεία Λασιθίου 02.xls, sheet "AGGALI95" | xls | rows that are not records | 84 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r003, file Ν. ΛΑΣΙΘΙΟΥ/Σταυροχωρι 02.xls, sheet "AGGALI95" | xls | rows that are not records | 38 |  | 1 | 7 title or note rows above the header; 3 totals rows; 1 sub-heading row inside the table |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Αγια Γαληνη  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Ανώγεια  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 78 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Βολεώνες Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 40 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Βυζάρι  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Γαράζο  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 10 |  | 1 | 7 title or note rows above the header; 29 empty rows inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Γερακάρι Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 38 |  | 1 | 7 title or note rows above the header; 1 empty row inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Καβούσι Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 36 |  | 1 | 7 title or note rows above the header; 3 empty rows inside the table; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Λευκόγεια Ρεθύμνης  02.xls, sheet "AGGALI95" | xls | rows that are not records | 39 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Μέλαμπες  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r004, file Ν. ΡΕΘΥΜΝΗΣ/Σπήλι  Ρεθύμνης 02.xls, sheet "AGGALI95" | xls | rows that are not records | 41 |  | 1 | 7 title or note rows above the header; 3 totals rows |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Ασκύφου Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 45 |  | 1 | 7 title or note rows above the header; 36 empty rows inside the table; 3 totals rows |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Γαύδος  Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 12 |  | 1 | 7 title or note rows above the header; 26 empty rows inside the table; 3 totals rows; 1 sub-heading row inside the table |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Καλύβες Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 32 |  | 1 | 7 title or note rows above the header; 7 empty rows inside the table; 3 totals rows |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Μουρί Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 42 |  | 1 | 7 title or note rows above the header; 4 empty rows inside the table; 3 totals rows |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Παλαιά Ρούματα Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 45 |  | 1 | 7 title or note rows above the header; 36 empty rows inside the table; 3 totals rows |
| S21 | r005, file Ν. ΧΑΝΙΩΝ/Πρασσές  Χανίων 02.xls, sheet "AGGALI95" | xls | rows that are not records | 15 |  | 1 | 7 title or note rows above the header; 24 empty rows inside the table; 3 totals rows |
| S23 | r001 | rdf | records | 160554 | 3 | by hand | 160,554 subjects with a URI; damaged text in 3 cells |
| S24 | r001 | csv | records, with empty rows | 147 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, column 2, repeats an earlier value in 7 records |
| S24 | r002 | csv | rows that are not records | 255 |  | 1 | 3 empty rows inside the table; 2 note rows below the table |
| S24 | r003 | csv | records | 28 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; 9 records repeat an earlier one in every column other than those that number the rows; the rows are only numbered (column 1) |
| S24 | r004 | csv | rows that are not records | 70 |  | 1 | 2 note rows below the table |
| S24 | r005 | csv | records | 47 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record |
| S24 | r006 | csv | records | 115 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, column 1, repeats an earlier value in 1 record |
| S24 | r007 | csv | records, with empty rows | 250 | 0 | 1 | no column or combination of up to 4 columns is filled and different in every record; the column nearest to an identifier, column 2, repeats an earlier value in 14 records |
| S25 | r001, sheet "ΙΑΝΟΥΑΡΙΟΣ - ΦΕΒΡΟΥΑΡΙΟΣ 2017" | xls | rows that are not records | 131 |  | 1 | 1 title or note row above the header |
| S26 | r001, sheet "Εγχώρια" | xls | rows that are not records | 95 |  | 1 | 5 title or note rows above the header; 6 totals rows; 6 sub-heading rows inside the table; 1 note row below the table; numbers stored as text in 1 column |
| S26 | r001, sheet "Ευρωπαϊκής Ένωσης" | xls | rows that are not records | 18 |  | 1 | 5 title or note rows above the header; 5 totals rows; 5 sub-heading rows inside the table; 1 note row below the table |
| S26 | r001, sheet "Τρίτων Χωρών" | xls | rows that are not records | 49 |  | 1 | 5 title or note rows above the header; 6 totals rows; 6 sub-heading rows inside the table; 1 note row below the table; numbers stored as text in 1 column |
| S29 | r001, sheet "ΠΙΝΑΚΑΣ ΤΙΜΟΛΗΨΙΩΝ 18-01-2016" | xls | rows that are not records | 24 |  | 1 | 4 tables in one sheet; 7 title or note rows above the header; 5 sub-heading rows inside the table; 1 note row below the table |
| S31 | r003, sheet "ΥΠΟΓΕΓΡΑΜΜΕΝΕΣ ΣΥΜΒΑΣΕΙΣ (ΝΕΕΣ)" | xls | rows that are not records | 45 |  | 1 | merged cells inside the data (6); 6 sub-heading rows inside the table; numbers stored as text in 1 column |
| S32 | r002, sheet "Π.Ε. Αχαϊας" | xls | rows that are not records | 126 |  | 1 | 1 title or note row above the header |
| S32 | r002, sheet "Π.Ε. Ηλείας" | xls | rows that are not records | 102 |  | 1 | 1 title or note row above the header |

## Documents

| Dataset | PDF documents among the files obtained |
| --- | --- |
| S21 | r001: PDF of 13 pages, text extracted from 13, 9,139 letters, 100% of them Greek |
| S22 | r001: PDF of 3 pages, text extracted from 3, 4,009 letters, 75% of them Greek |

Every examined table is listed in `data/processed/retrieval_tables_2026-10-24.csv` (208 rows).
