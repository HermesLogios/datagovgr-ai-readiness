# Timeliness (Q5) with the second snapshot, 2026-10-24 and 2026-11-25

Comparison of the snapshots `catalog_2026-10-24.jsonl.gz` and `catalog_2026-11-25.jsonl.gz` by the identifier of every dataset, and proposed scores of Q5 for the 36 datasets of the sample (`DECISIONS.md` #36, rule e). A change of the files is a new file or a newer upload date; a resource record created again for the same address is not a new file. A dataset without an uploaded file and without a new file is not measurable, because a change behind an external address does not show in the catalogue. The scores are proposals until the review.

## The two snapshots

| Datasets | Count |
| --- | ---: |
| in the first snapshot (2026-10-24) | 22,805 |
| in the second snapshot (2026-11-25) | 23,157 |
| in both | 22,751 |
| only in the first (removed from the catalogue) | 54 |
| only in the second (new) | 406 |

## Files of the datasets present in both snapshots

| Files between the snapshots | Datasets | Share |
| --- | ---: | ---: |
| changed | 364 | 1.6% |
| unchanged | 7,155 | 31.4% |
| not measurable | 15,232 | 67.0% |

## Datasets that declare an update of one month or less (rule 2, counts for the study)

Declared in the first snapshot and present in both: 795. Measurable: 120; of these, without any new or updated file in the month: 40 (33.3%).

| Declared frequency | Datasets | Changed | Unchanged | Not measurable |
| --- | ---: | ---: | ---: | ---: |
| MONTHLY | 343 | 5 | 21 | 317 |
| DAILY | 251 | 0 | 0 | 251 |
| CONT | 102 | 75 | 13 | 14 |
| HOURLY | 79 | 0 | 0 | 79 |
| UPDATE_CONT | 15 | 0 | 2 | 13 |
| WEEKLY | 2 | 0 | 2 | 0 |
| 5MIN | 1 | 0 | 1 | 0 |
| MONTHLY_3 | 1 | 0 | 1 | 0 |
| WEEKLY_2 | 1 | 0 | 0 | 1 |

## The sample

Rule 1: the newest date inside the data, counted to the day of the download of the files. Otherwise the metadata part on the second snapshot. Rule 2: a declared period of one month or shorter without any new or updated file between the snapshots does not score 2. The dates issued and modified of the source catalogue are not used.

| Score | Provisional (metadata, first snapshot) | Proposed |
| --- | ---: | ---: |
| 2 | 8 | 7 |
| 1 | 12 | 12 |
| 0 | 2 | 5 |
| not measurable | 14 | 12 |

| Dataset | Title | Frequency | Newest data | Files in the month | Provisional | Proposed | Reason |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| S01 | [Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος Κτηματολογίου"](https://data.gov.gr/dataset/geotemachia-oria-kai-kaek-ton-periochon-toy-leitoyrgoyntos-ktimatologioy) | IRREG | 2026-10-22 (names of the files) | changed | 1 | 1 | no period declared (IRREG): newest data 2026-10-22, 13 days before the download of 2026-11-04 (names of the files) |
| S02 | [Καλλικρατικοί Δήμοι](https://data.gov.gr/dataset/gis-ypen-wfd-wms-kallikratikoi_dimoi) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S03 | [Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ)](https://data.gov.gr/dataset/dromologia-statheron-sygkoinonion-metro-isap-tram) | ANNUAL_3 | - | changed | 2 | 2 | ANNUAL_3: last upload 7 days ago, 0.1 periods |
| S04 | [Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υδροληψίας) - περιοχή Ανατολικής Μακεδονίας & Θράκης](https://data.gov.gr/dataset/simeia-ydrolipsias-tis-geovasis-emsy-ethniko-mitroo-simeion-ydrolipsias-periochi-anatolikis-makedoni) | - | 2026-06-23 (names of the files) | unchanged | 1 | 1 | no period declared (none): newest data 2026-06-23, 134 days before the download of 2026-11-04 (names of the files) |
| S05 | [Λίστα με Μονάδες Φροντίδας Ηλικιωμένων](https://data.gov.gr/dataset/attica-43-lista-me-monades-frontidas-hlikiwmenwn) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S06 | [Τροχαία ατυχήματα](https://data.gov.gr/dataset/troxaia-atyxhmata) | NOT_PLANNED | 2025-12-31 (names of the files) | unchanged | 1 | 1 | NOT_PLANNED: declared as not updated without a stated period: newest data 2025-12-31, 308 days before the download of 2026-11-04 (names of the files) |
| S07 | [Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος](https://data.gov.gr/dataset/diacheirisi-stoicheion-paragogis-nopoy-galaktos) | MONTHLY | 2026-08-31 (inside the files) | changed | 2 | 1 | MONTHLY: newest data 2026-08-31, 2.1 periods before the download of 2026-11-04 (inside the files) |
| S08 | ["ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ, ΑΝΑ ΕΙΔΙΚΟΤΗΤΑ ΚΑΙ ΣΧΕΣΗ ΕΡΓΑΣΙΑΣ, ΑΝΑ ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΕΚΠΑΙΔΕΥΣΗΣ ΓΙΑ ΤΟ ΣΧΟΛΙΚΟ ΕΤΟΣ 2024-2025 "](https://data.gov.gr/dataset/arithmos-ekpaideytikon-deyterovathmia-eidikotita-schesi-ergasias-2025) | - | - | unchanged | 1 | 1 | no period declared (none): last upload 210 days ago |
| S09 | [Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής](https://data.gov.gr/dataset/attica-92-lista-anamonhs-iatrwn-gia-eidikeysh-sta-nosokomeia-attikhs-2020) | - | 2026-12-31 (names of the files) | changed | - | 1 | no period declared (none): newest data 2026-12-31, a period that ends after the download of 2026-11-04 (names of the files) |
| S10 | [ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ)](https://data.gov.gr/dataset/enarmonismenos-deiktis-timon-katanaloti-endtk) | MONTHLY | 2025-12-31 (inside the files) | unchanged | 0 | 0 | MONTHLY: newest data 2025-12-31, 10.1 periods before the download of 2026-11-04 (inside the files); no new or updated file between 2026-10-24 and 2026-11-25: at most 1 (rule 2) |
| S11 | [Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ)](https://data.gov.gr/dataset/dromologia-odikon-sygkoinonion-leoforeia-trolei) | - | - | changed | 1 | 1 | no period declared (none): last upload 7 days ago |
| S12 | [Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης](https://data.gov.gr/dataset/dedomena-astikon-sygkoinonion-p-e-thessalonikis) | AS_NEEDED | 2026-10-25 (names of the files) | changed | 1 | 1 | no period declared (AS_NEEDED): newest data 2026-10-25, 10 days before the download of 2026-11-04 (names of the files) |
| S13 | [Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS](https://data.gov.gr/dataset/oasth-gtfs) | ANNUAL | - | unchanged | 2 | 2 | ANNUAL: last upload 237 days ago, 0.6 periods |
| S14 | [Υπηρεσίες Δήμου Πατρέων](https://data.gov.gr/dataset/ypiresies-dimoy-patreon) | NOT_PLANNED | 2025-12-01 (names of the files) | unchanged | 1 | 1 | NOT_PLANNED: declared as not updated without a stated period: newest data 2025-12-01, 338 days before the download of 2026-11-04 (names of the files) |
| S15 | [ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ](https://data.gov.gr/dataset/https-www-nafpaktos-gr-el-prosvasi) | IRREG | - | unchanged | 1 | 1 | no period declared (IRREG): last upload 107 days ago |
| S16 | [Θεσμοθετημένες περιοχές NATURA 2000](https://data.gov.gr/dataset/thesmothetimenes-perioches-natura-2000) | UNKNOWN | - | unchanged | 1 | 1 | no period declared (UNKNOWN): last upload 212 days ago |
| S17 | [Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ](https://data.gov.gr/dataset/apd-kritis-harv2-__) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S18 | [Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018](https://data.gov.gr/dataset/gis-syros-ermoupolis-wms-syros-lcv_pol_corine_land_cover_2012_2018) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S19 | [Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ](https://data.gov.gr/dataset/emy-station-189) | CONT | 2026-11-03 (inside the files) | changed | 2 | 2 | CONT: newest data 2026-11-03, 1.0 periods before the download of 2026-11-04 (inside the files) |
| S20 | [Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-2023 από 54 μετεωρολογικούς σταθμούς](https://data.gov.gr/dataset/stations-data) | - | 2023-12-31 (inside the files) | unchanged | 1 | 0 | no period declared (none): newest data 2023-12-31, 1039 days before the download of 2026-11-04 (inside the files) |
| S21 | [Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης](https://data.gov.gr/dataset/apd-kritis-harv2-56) | - | 2006-07-31 (inside the files) | not measurable | - | 0 | no period declared (none): newest data 2006-07-31, 7401 days before the download of 2026-11-04 (inside the files) |
| S22 | [Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδοση προσωρινού πίνακα κατάταξης επενδυτικών σχεδίων που υποβλήθηκαν προς υπαγωγή στο καθεστώς ενίσχυσης "Ενίσχυση Τουριστικών Επενδύσεων" (β΄ κύκλος) στο Υπουργείο Ανάπτυξης](https://data.gov.gr/dataset/prosorinoi-pinakes-katataxis-g-pr-21487-13-03-2024-ekdosi-prosorinoy-pinaka-katataxis-ependytikon-sc) | AS_NEEDED | 2024-03-13 (names of the files) | unchanged | 1 | 0 | no period declared (AS_NEEDED): newest data 2024-03-13, 966 days before the download of 2026-11-04 (names of the files) |
| S23 | [Athens Business Open Data - STIRData model](https://data.gov.gr/dataset/athens-business-open-data-stirdata-model) | NOT_PLANNED | - | not measurable | - | - | NOT_PLANNED: declared as not updated without a stated period: no upload date on the portal, not measurable from the metadata |
| S24 | [ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ)](https://data.gov.gr/dataset/apofaseis-egkrisis-perivallontikon-oron-lesvos-limnos) | NOT_PLANNED | - | unchanged | 1 | 1 | NOT_PLANNED: declared as not updated without a stated period: last upload 212 days ago |
| S25 | [ΣΤΑΤΙΣΤΙΚΑ ΔΙΑΤΡΟΦΗΣ ΦΕΒΡΟΥΑΡΙΟΥ 2017](https://data.gov.gr/dataset/statistika-diatrofhs-febroyarioy-2017) | NOT_PLANNED | 2017-02-28 (names of the files) | unchanged | 2 | 2 | NOT_PLANNED: declared as not updated, and the title or description states the period of the data (names of the files) |
| S26 | [ΣΤΑΤΙΣΤΙΚΑ ΙΧΘΥΟΣΚΑΛΑΣ ΘΕΣΣΑΛΟΝΙΚΗΣ ΜΑΡΤΙΟΣ 2020](https://data.gov.gr/dataset/statistika-ix8yoskalas-8essalonikhs-martios-2020) | NOT_PLANNED | - | not measurable | 2 | 2 | NOT_PLANNED: declared as not updated, and the title or description states the period of the data |
| S27 | [ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 463/Δ/1998-07-03)](https://data.gov.gr/dataset/gis-agrinio-wms-only-agriniotrm-trm_ras_123107fs000463_1998_geo) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S28 | [Σχέδιο ΠΕ περιοχής Ατσαλένιο / Μωσαϊκό](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliopef-pef_ras_atsalenio_mosaic_geo) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S29 | [ΠΙΝΑΚΕΣ ΤΙΜΟΛΗΨΙΩΝ ΣΥΡΟΥ](https://data.gov.gr/dataset/pinakes-timolhpsiwn-syroy) | NOT_PLANNED | 2015-02-01 (names of the files) | unchanged | 2 | 2 | NOT_PLANNED: declared as not updated, and the title or description states the period of the data (names of the files) |
| S30 | [Διάγραμμα Τροποποιήσεως του Ρυμοτομικού Σχεδίου της Πόλης Χανίων](https://data.gov.gr/dataset/gis-chania-wms-only-chaniatsp-tsp_ras_fek_2003_739_d_200_geo) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S31 | [ΠΡΟΓΡΑΜΜΑΤΙΚΕΣ ΣΥΜΒΑΣΕΙΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ](https://data.gov.gr/dataset/programmatikes-symbaseis-perifereias-attikhs) | NOT_PLANNED | 2019-12-31 (names of the files) | unchanged | 0 | 0 | NOT_PLANNED: declared as not updated without a stated period: newest data 2019-12-31, 2500 days before the download of 2026-11-04 (names of the files) |
| S32 | [Περιβαλλοντικοί έλεγχοι έτους 2014 από τη Δ/νση Περιβάλλοντος & Χωρικού Σχεδιασμού Π.Δ.Ε.](https://data.gov.gr/dataset/periballontikoi-elegxoi-etoys-2014-apo-th-d-nsh-periballontos-and-xwrikoy-sxediasmoy-p-d-e) | NOT_PLANNED | 2014-12-31 (inside the files) | unchanged | 2 | 2 | NOT_PLANNED: declared as not updated, and the title or description states the period of the data (inside the files) |
| S33 | [Διάγραμμα - ΦΕΚ 130/Δ/2001-02-21](https://data.gov.gr/dataset/gis-maroussi-wms-only-maroussirym-rym_015784fs000130_2001e) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S34 | [Αποθετήριο ΤΕΧΝΗ](https://data.gov.gr/dataset/ekt-searchculture-dataset-__-15) | IRREG | - | not measurable | - | - | no period declared (IRREG): no upload date on the portal, not measurable from the metadata |
| S35 | [Συνεδριάσεις Επιτροπής Αθλητισμού & Παιδείας Περιφέρειας Αττικής](https://data.gov.gr/dataset/attica-443-synedriaseis-epitrophs-athlhtismoy-paideias-perifereias-attikhs) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
| S36 | [Διάγραμμα Τροποποίησης - T1936A404_69912_500_01](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliotsp-t1936a404_69912_500_01) | - | - | not measurable | - | - | no period declared (none): no upload date on the portal, not measurable from the metadata |
