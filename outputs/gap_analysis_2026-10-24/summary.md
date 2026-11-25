# Gap analysis, snapshot of 2026-10-24

A gap is a score below 2 in a criterion that applies to the dataset, read with the effort of its fix: low, metadata and documentation only; medium, a change in the file itself; high, a change in a system or in the source of the data. Nothing is judged here: the scores, the effort of the fix and the answers on compliance come from `13_assessment.py`, `04_metadata_checks.py` and `14_hvd_compliance.py` (DECISIONS.md #57 to #60). Which high-value datasets are missing from the portal is examined separately.

## 1. Gaps by criterion

### Sample (36 datasets)

Datasets: those to which the criterion applies. Share: the scores below 2 of these datasets. Ordered by share.

| Criterion | Level | Core | Datasets | 2 | 1 | 0 | Below 2 | Share | Low effort | Medium effort | High effort |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI7 Declared limitations | AI-readiness | no | 36 | 1 | 14 | 21 | 35 | 97.2% | 35 | 0 | 0 |
| AI4 Description in Croissant or a datasheet | AI-readiness | no | 36 | 4 | 28 | 4 | 32 | 88.9% | 32 | 0 | 0 |
| AI3 Historical depth | AI-readiness | no | 29 | 5 | 13 | 11 | 24 | 82.8% | 0 | 24 | 0 |
| AI2 Documentation of the structure | AI-readiness | yes | 30 | 7 | 23 | 0 | 23 | 76.7% | 23 | 0 | 0 |
| Q5 Timeliness | Quality | no | 24 | 7 | 12 | 5 | 17 | 70.8% | 15 | 0 | 2 |
| AI5 Suitability for retrieval (RAG) | AI-readiness | no | 36 | 11 | 19 | 6 | 25 | 69.4% | 0 | 25 | 0 |
| M10 API and bulk download | Metadata and legal status | no | 24 | 9 | 15 | 0 | 15 | 62.5% | 1 | 1 | 13 |
| M2 Recommended metadata | Metadata and legal status | no | 36 | 17 | 19 | 0 | 19 | 52.8% | 19 | 0 | 0 |
| Q6 Format (5-star scale) | Quality | yes | 36 | 18 | 10 | 8 | 18 | 50.0% | 0 | 18 | 0 |
| AI1 Machine-readable structure | AI-readiness | yes | 36 | 18 | 8 | 10 | 18 | 50.0% | 0 | 18 | 0 |
| AI6 Linkage through common identifiers | AI-readiness | no | 36 | 19 | 13 | 4 | 17 | 47.2% | 0 | 17 | 0 |
| Q2 Completeness | Quality | no | 30 | 16 | 9 | 5 | 14 | 46.7% | 0 | 14 | 0 |
| Q3 Consistency | Quality | no | 30 | 18 | 11 | 1 | 12 | 40.0% | 0 | 12 | 0 |
| M1 Mandatory metadata | Metadata and legal status | yes | 36 | 23 | 11 | 2 | 13 | 36.1% | 13 | 0 | 0 |
| Q4 Plausibility of values | Quality | no | 30 | 20 | 6 | 4 | 10 | 33.3% | 0 | 7 | 3 |
| M6 Mode of distribution | Metadata and legal status | no | 36 | 27 | 6 | 3 | 9 | 25.0% | 0 | 9 | 0 |
| Q1 Availability | Quality | yes | 36 | 29 | 3 | 4 | 7 | 19.4% | 3 | 4 | 0 |
| M4 Licence | Metadata and legal status | yes | 36 | 30 | 0 | 6 | 6 | 16.7% | 6 | 0 | 0 |
| M8 Personal data | Metadata and legal status | no | 33 | 28 | 5 | 0 | 5 | 15.2% | 0 | 5 | 0 |
| M3 Controlled vocabularies | Metadata and legal status | no | 36 | 31 | 4 | 1 | 5 | 13.9% | 5 | 0 | 0 |
| M9 High-value designation | Metadata and legal status | no | 24 | 21 | 0 | 3 | 3 | 12.5% | 3 | 0 | 0 |
| M7 Persistent identifier | Metadata and legal status | no | 36 | 33 | 3 | 0 | 3 | 8.3% | 3 | 0 | 0 |
| M5 Free access | Metadata and legal status | no | 33 | 33 | 0 | 0 | 0 | 0.0% | 0 | 0 | 0 |

All the criteria that are not provisional: 330 scores below 2 of 755 (43.7%); effort of the fix low 158, medium 154, high 18.

Q5 Timeliness: 12 datasets not measurable, left out of its datasets and of the totals (DECISIONS.md #63).

### Catalogue (22,805 datasets)

The nine criteria that the metadata decide (`04_metadata_checks.py`); the other criteria need the files and are judged in the sample only. A score that could not be determined is counted apart, and the share is taken over the datasets with a score. Ordered by share.

| Criterion | Counted over | Datasets | 2 | 1 | 0 | Not determined | Below 2 | Share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q6 Format (5-star scale) | every dataset of the snapshot | 22,805 | 7,214 | 4,715 | 10,243 | 633 | 14,958 | 67.5% |
| M2 Recommended metadata | every dataset of the snapshot | 22,805 | 7,775 | 14,718 | 312 | 0 | 15,030 | 65.9% |
| M1 Mandatory metadata | every dataset of the snapshot | 22,805 | 9,130 | 12,928 | 747 | 0 | 13,675 | 60.0% |
| Q5 Timeliness (metadata part) | every dataset of the snapshot | 22,805 | 3,520 | 900 | 3,408 | 14,977 | 4,308 | 55.0% |
| M6 Mode of distribution | every dataset of the snapshot | 22,805 | 13,974 | 8,732 | 99 | 0 | 8,831 | 38.7% |
| M9 High-value designation | datasets with a high-value marking | 1,302 | 1,122 | 180 | 0 | 0 | 180 | 13.8% |
| M4 Licence | every dataset of the snapshot | 22,805 | 21,855 | 377 | 573 | 0 | 950 | 4.2% |
| M3 Controlled vocabularies | every dataset of the snapshot | 22,805 | 22,053 | 671 | 81 | 0 | 752 | 3.3% |
| M7 Persistent identifier | every dataset of the snapshot | 22,805 | 22,405 | 301 | 99 | 0 | 400 | 1.8% |

## 2. What each dataset lacks for the ready group

Rule of the groups (DECISIONS.md #20): Ready, every core criterion scores 2; Almost ready, every core criterion below 2 can be fixed with low effort; Not yet, at least one core criterion below 2 needs medium or high effort. Groups: Ready 2, Almost ready 12, Not yet 22.

- One core criterion of low effort from the ready group: M4: S03, S11; AI2: S02, S10, S15, S18, S20, S23.
- One core criterion of medium or high effort from the ready group, with or without core criteria of low effort: Q6: S01, S09, S16; AI1: S08, S24, S26.
- Core criteria of medium or high effort in the group Not yet: Q6 18, AI1 18, Q1 4.

| Dataset | Title | Group | Core below 2, low effort | Core below 2, medium or high effort | Other below 2, low | Other below 2, medium | Other below 2, high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S07 | [Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος](https://data.gov.gr/dataset/diacheirisi-stoicheion-paragogis-nopoy-galaktos) | Ready | - | - | AI7 | M8 AI6 | Q5 |
| S13 | [Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS](https://data.gov.gr/dataset/oasth-gtfs) | Ready | - | - | M2 AI7 | M10 AI3 | - |
| S02 | [Καλλικρατικοί Δήμοι](https://data.gov.gr/dataset/gis-ypen-wfd-wms-kallikratikoi_dimoi) | Almost ready | AI2 | - | M2 M9 M10 AI4 AI7 | - | - |
| S03 | [Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ)](https://data.gov.gr/dataset/dromologia-statheron-sygkoinonion-metro-isap-tram) | Almost ready | M4 | - | AI4 AI7 | Q4 AI3 | M10 |
| S04 | [Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υδροληψίας) - περιοχή Ανατολικής Μακεδονίας & Θράκης](https://data.gov.gr/dataset/simeia-ydrolipsias-tis-geovasis-emsy-ethniko-mitroo-simeion-ydrolipsias-periochi-anatolikis-makedoni) | Almost ready | M1 AI2 | - | Q5 M2 M3 AI4 AI7 | Q2 Q3 Q4 AI3 | - |
| S10 | [ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ)](https://data.gov.gr/dataset/enarmonismenos-deiktis-timon-katanaloti-endtk) | Almost ready | AI2 | - | AI4 AI7 | Q2 | Q5 |
| S11 | [Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ)](https://data.gov.gr/dataset/dromologia-odikon-sygkoinonion-leoforeia-trolei) | Almost ready | M4 | - | Q5 M2 M3 AI4 AI7 | AI3 | M10 |
| S12 | [Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης](https://data.gov.gr/dataset/dedomena-astikon-sygkoinonion-p-e-thessalonikis) | Almost ready | Q1 M1 AI2 | - | Q5 M7 AI4 AI7 | AI3 AI5 | Q4 M10 |
| S14 | [Υπηρεσίες Δήμου Πατρέων](https://data.gov.gr/dataset/ypiresies-dimoy-patreon) | Almost ready | Q1 M1 AI2 | - | Q5 M2 M7 AI4 AI7 | Q2 Q3 AI3 AI6 | Q4 M10 |
| S15 | [ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ](https://data.gov.gr/dataset/https-www-nafpaktos-gr-el-prosvasi) | Almost ready | AI2 | - | Q5 AI4 AI7 | Q3 Q4 AI3 | - |
| S18 | [Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018](https://data.gov.gr/dataset/gis-syros-ermoupolis-wms-syros-lcv_pol_corine_land_cover_2012_2018) | Almost ready | AI2 | - | M2 M9 AI4 AI7 | Q2 AI3 AI5 | - |
| S19 | [Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ](https://data.gov.gr/dataset/emy-station-189) | Almost ready | M1 AI2 | - | AI4 AI7 | Q2 AI6 | Q4 |
| S20 | [Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-2023 από 54 μετεωρολογικούς σταθμούς](https://data.gov.gr/dataset/stations-data) | Almost ready | AI2 | - | Q5 M2 AI4 | Q4 AI6 | M10 |
| S23 | [Athens Business Open Data - STIRData model](https://data.gov.gr/dataset/athens-business-open-data-stirdata-model) | Almost ready | AI2 | - | M2 M9 AI4 AI7 | Q2 Q4 M8 AI3 AI5 | M10 |
| S01 | [Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος Κτηματολογίου"](https://data.gov.gr/dataset/geotemachia-oria-kai-kaek-ton-periochon-toy-leitoyrgoyntos-ktimatologioy) | Not yet | M4 | Q6 | Q5 M2 AI4 AI7 | AI3 AI5 | M10 |
| S05 | [Λίστα με Μονάδες Φροντίδας Ηλικιωμένων](https://data.gov.gr/dataset/attica-43-lista-me-monades-frontidas-hlikiwmenwn) | Not yet | M4 AI2 | Q6 AI1 | M3 AI4 AI7 | Q2 Q3 M6 AI3 AI5 AI6 | M10 |
| S06 | [Τροχαία ατυχήματα](https://data.gov.gr/dataset/troxaia-atyxhmata) | Not yet | M1 | Q6 AI1 | Q5 M3 AI7 | Q3 AI3 AI5 AI6 | M10 |
| S08 | ["ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ, ΑΝΑ ΕΙΔΙΚΟΤΗΤΑ ΚΑΙ ΣΧΕΣΗ ΕΡΓΑΣΙΑΣ, ΑΝΑ ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΕΚΠΑΙΔΕΥΣΗΣ ΓΙΑ ΤΟ ΣΧΟΛΙΚΟ ΕΤΟΣ 2024-2025 "](https://data.gov.gr/dataset/arithmos-ekpaideytikon-deyterovathmia-eidikotita-schesi-ergasias-2025) | Not yet | AI2 | AI1 | Q5 M2 AI4 AI7 | Q2 AI3 AI5 | - |
| S09 | [Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής](https://data.gov.gr/dataset/attica-92-lista-anamonhs-iatrwn-gia-eidikeysh-sta-nosokomeia-attikhs-2020) | Not yet | M1 M4 AI2 | Q6 | Q5 M7 AI4 AI7 | Q3 Q4 AI3 AI5 AI6 | M10 |
| S16 | [Θεσμοθετημένες περιοχές NATURA 2000](https://data.gov.gr/dataset/thesmothetimenes-perioches-natura-2000) | Not yet | AI2 | Q6 | Q5 M2 AI4 AI7 | Q2 AI3 AI5 | M10 |
| S17 | [Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ](https://data.gov.gr/dataset/apd-kritis-harv2-__) | Not yet | AI2 | Q1 Q6 | M2 AI4 AI7 | Q2 M6 AI3 AI5 | M10 |
| S21 | [Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης](https://data.gov.gr/dataset/apd-kritis-harv2-56) | Not yet | Q1 | Q6 AI1 | Q5 M2 AI7 | Q3 AI3 AI5 AI6 | - |
| S22 | [Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδοση προσωρινού πίνακα κατάταξης επενδυτικών σχεδίων που υποβλήθηκαν προς υπαγωγή στο καθεστώς ενίσχυσης "Ενίσχυση Τουριστικών Επενδύσεων" (β΄ κύκλος) στο Υπουργείο Ανάπτυξης](https://data.gov.gr/dataset/prosorinoi-pinakes-katataxis-g-pr-21487-13-03-2024-ekdosi-prosorinoy-pinaka-katataxis-ependytikon-sc) | Not yet | AI2 | Q6 AI1 | Q5 AI4 AI7 | AI5 | M10 |
| S24 | [ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ)](https://data.gov.gr/dataset/apofaseis-egkrisis-perivallontikon-oron-lesvos-limnos) | Not yet | AI2 | AI1 | Q5 AI4 AI7 | Q2 Q3 M8 AI3 AI5 AI6 | - |
| S25 | [ΣΤΑΤΙΣΤΙΚΑ ΔΙΑΤΡΟΦΗΣ ΦΕΒΡΟΥΑΡΙΟΥ 2017](https://data.gov.gr/dataset/statistika-diatrofhs-febroyarioy-2017) | Not yet | M1 AI2 | Q6 AI1 | AI4 AI7 | AI3 AI5 AI6 | - |
| S26 | [ΣΤΑΤΙΣΤΙΚΑ ΙΧΘΥΟΣΚΑΛΑΣ ΘΕΣΣΑΛΟΝΙΚΗΣ ΜΑΡΤΙΟΣ 2020](https://data.gov.gr/dataset/statistika-ix8yoskalas-8essalonikhs-martios-2020) | Not yet | M1 AI2 | AI1 | AI4 AI7 | Q2 Q3 AI3 AI5 AI6 | - |
| S27 | [ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 463/Δ/1998-07-03)](https://data.gov.gr/dataset/gis-agrinio-wms-only-agriniotrm-trm_ras_123107fs000463_1998_geo) | Not yet | - | Q6 AI1 | M2 AI4 AI7 | M6 AI5 | - |
| S28 | [Σχέδιο ΠΕ περιοχής Ατσαλένιο \| Μωσαϊκό](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliopef-pef_ras_atsalenio_mosaic_geo) | Not yet | M1 | Q1 Q6 AI1 | M2 AI4 AI7 | M6 AI5 AI6 | - |
| S29 | [ΠΙΝΑΚΕΣ ΤΙΜΟΛΗΨΙΩΝ ΣΥΡΟΥ](https://data.gov.gr/dataset/pinakes-timolhpsiwn-syroy) | Not yet | M1 AI2 | Q6 AI1 | AI4 AI7 | Q2 M8 AI3 AI5 AI6 | - |
| S30 | [Διάγραμμα Τροποποιήσεως του Ρυμοτομικού Σχεδίου της Πόλης Χανίων](https://data.gov.gr/dataset/gis-chania-wms-only-chaniatsp-tsp_ras_fek_2003_739_d_200_geo) | Not yet | M1 | Q6 AI1 | M2 AI4 AI7 | M6 AI5 | - |
| S31 | [ΠΡΟΓΡΑΜΜΑΤΙΚΕΣ ΣΥΜΒΑΣΕΙΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ](https://data.gov.gr/dataset/programmatikes-symbaseis-perifereias-attikhs) | Not yet | M1 AI2 | Q6 AI1 | Q5 AI4 AI7 | Q3 AI3 AI5 | - |
| S32 | [Περιβαλλοντικοί έλεγχοι έτους 2014 από τη Δ/νση Περιβάλλοντος & Χωρικού Σχεδιασμού Π.Δ.Ε.](https://data.gov.gr/dataset/periballontikoi-elegxoi-etoys-2014-apo-th-d-nsh-periballontos-and-xwrikoy-sxediasmoy-p-d-e) | Not yet | AI2 | Q6 AI1 | AI4 AI7 | Q3 AI3 AI5 AI6 | - |
| S33 | [Διάγραμμα - ΦΕΚ 130/Δ/2001-02-21](https://data.gov.gr/dataset/gis-maroussi-wms-only-maroussirym-rym_015784fs000130_2001e) | Not yet | - | Q6 AI1 | M2 AI4 AI7 | M6 AI5 | - |
| S34 | [Αποθετήριο ΤΕΧΝΗ](https://data.gov.gr/dataset/ekt-searchculture-dataset-__-15) | Not yet | AI2 | Q1 AI1 | AI4 AI7 | Q2 Q3 Q4 M6 AI3 AI5 AI6 | - |
| S35 | [Συνεδριάσεις Επιτροπής Αθλητισμού & Παιδείας Περιφέρειας Αττικής](https://data.gov.gr/dataset/attica-443-synedriaseis-epitrophs-athlhtismoy-paideias-perifereias-attikhs) | Not yet | M1 M4 | Q6 AI1 | M2 M3 AI4 AI7 | M6 M8 AI5 AI6 | - |
| S36 | [Διάγραμμα Τροποποίησης - T1936A404_69912_500_01](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliotsp-t1936a404_69912_500_01) | Not yet | - | Q1 Q6 AI1 | M2 AI4 AI7 | M6 AI5 AI6 | - |

## 3. Gaps of compliance of the high-value datasets

Over the 12 datasets whose content is in the Annex of Implementing Regulation (EU) 2023/138 (DECISIONS.md #58). Not applicable and not asked by the Annex are not gaps.

| Requirement | No | Partly | Datasets answered no | Datasets answered partly |
| --- | ---: | ---: | --- | --- |
| Free of charge | 0 | 0 | - | - |
| Open licence | 1 | 0 | S01 | - |
| API | 5 | 0 | S01 S16 S17 S20 S23 | - |
| Bulk download | 0 | 0 | - | - |
| Terms of use and documentation of the API | 1 | 0 | S02 | - |
| Point of contact | 6 | 0 | S01 S02 S16 S18 S20 S23 | - |
| Marked as a high-value dataset | 3 | 0 | S02 S18 S23 | - |
| Documentation of the structure | 0 | 9 | - | S04 S10 S16 S17 S18 S19 S20 S23 S24 |

| Dataset | Title | Point of the Annex | Not met | Partly met |
| --- | --- | --- | --- | --- |
| S01 | [Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος Κτηματολογίου"](https://data.gov.gr/dataset/geotemachia-oria-kai-kaek-ton-periochon-toy-leitoyrgoyntos-ktimatologioy) | 1.1 Cadastral parcels | Open licence; API; Point of contact | - |
| S02 | [Καλλικρατικοί Δήμοι](https://data.gov.gr/dataset/gis-ypen-wfd-wms-kallikratikoi_dimoi) | 1.1 Administrative units | Terms of use and documentation of the API; Point of contact; Marked as a high-value dataset | - |
| S04 | [Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υδροληψίας) - περιοχή Ανατολικής Μακεδονίας & Θράκης](https://data.gov.gr/dataset/simeia-ydrolipsias-tis-geovasis-emsy-ethniko-mitroo-simeion-ydrolipsias-periochi-anatolikis-makedoni) | 2.1 Water (Directive 2000/60/EC) and environmental information | - | Documentation of the structure |
| S10 | [ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ)](https://data.gov.gr/dataset/enarmonismenos-deiktis-timon-katanaloti-endtk) | 4.1 Harmonised indices of consumer prices | - | Documentation of the structure |
| S16 | [Θεσμοθετημένες περιοχές NATURA 2000](https://data.gov.gr/dataset/thesmothetimenes-perioches-natura-2000) | 2.1 Protected sites | API; Point of contact | Documentation of the structure |
| S17 | [Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ](https://data.gov.gr/dataset/apd-kritis-harv2-__) | 2.1 Energy resources, Production and industrial facilities and environmental information | API | Documentation of the structure |
| S18 | [Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018](https://data.gov.gr/dataset/gis-syros-ermoupolis-wms-syros-lcv_pol_corine_land_cover_2012_2018) | 2.1 Land cover | Point of contact; Marked as a high-value dataset | Documentation of the structure |
| S19 | [Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ](https://data.gov.gr/dataset/emy-station-189) | 3.1 Observations data measured by weather stations | - | Documentation of the structure |
| S20 | [Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-2023 από 54 μετεωρολογικούς σταθμούς](https://data.gov.gr/dataset/stations-data) | 3.1 Climate data: validated observations | API; Point of contact | Documentation of the structure |
| S21 | [Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης](https://data.gov.gr/dataset/apd-kritis-harv2-56) | 3.1 Climate data: validated observations | - | - |
| S23 | [Athens Business Open Data - STIRData model](https://data.gov.gr/dataset/athens-business-open-data-stirdata-model) | 5.1 Basic company information | API; Point of contact; Marked as a high-value dataset | Documentation of the structure |
| S24 | [ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ)](https://data.gov.gr/dataset/apofaseis-egkrisis-perivallontikon-oron-lesvos-limnos) | 2.1 Environmental information (Directive 2003/4/EC) | - | Documentation of the structure |

Catalogue: what the metadata allow to check for the 1,302 datasets marked as high-value (`14_hvd_compliance.py`).

| Requirement | Datasets without it | Share |
| --- | ---: | ---: |
| Open licence | 107 | 8.2% |
| Point of contact | 261 | 20.0% |
| Complete marking | 180 | 13.8% |
