# Compliance of the high-value datasets with Implementing Regulation (EU) 2023/138, snapshot of 2026-10-24

Source of the requirements: Commission Implementing Regulation (EU) 2023/138 of 21 December 2022 laying down a list of specific high-value datasets and the arrangements for their publication and re-use (OJ L 19, 20.1.2023, p. 43), Articles 3 and 4 and the Annex; free of charge follows Article 14(1) of Directive (EU) 2019/1024. The table is reported separately from the scores of the assessment (DECISIONS.md #28). Every answer comes from a score or a test that is already recorded; the reading of the Annex and the judgement on the marking of each dataset are recorded in DECISIONS.md #58 and in `criteria/hvd_marking.csv`.

## Marking of the high-value group of the sample

The group holds 24 datasets: those that their publishers mark as high-value and those counted as high-value by their content. The obligations of the Regulation apply to a dataset when its content corresponds to a dataset of the Annex.

| Content in the Annex | Datasets | Datasets of the group |
| --- | ---: | --- |
| yes | 12 | S01, S02, S04, S10, S16, S17, S18, S19, S20, S21, S23, S24 |
| no: marked by the publisher, not listed in the Annex | 6 | S05, S06, S07, S08, S09, S22 |
| doubtful: the text of the Annex gives no clear answer | 6 | S03, S11, S12, S13, S14, S15 |

Declared category of the datasets whose content is in the Annex:

| Marking | Datasets | Datasets of the group |
| --- | ---: | --- |
| correct | 4 | S01, S10, S19, S20 |
| correct with one more category | 2 | S17, S24 |
| other category | 3 | S04, S16, S21 |
| not marked | 3 | S02, S18, S23 |

## Compliance of the 12 datasets whose content is in the Annex

| Requirement | Legal basis | Answer taken from | Yes | Partly | No | Not applicable or not asked |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Free of charge | Directive (EU) 2019/1024, Article 14(1) | criterion M5 | 12 | 0 | 0 | 0 |
| Open licence: CC BY 4.0, equivalent or less restrictive | Regulation, Article 4(3) | criterion M4 | 11 | 0 | 1 | 0 |
| API | Regulation, Article 3(1) | test of criterion M10 | 7 | 0 | 5 | 0 |
| Bulk download | Regulation, Article 3(1) and the Annex | test of criterion M10 | 12 | 0 | 0 | 0 |
| Terms of use and documentation of the API | Regulation, Article 3(2) and 3(3) | test of criterion M10 | 6 | 0 | 1 | 5 |
| Point of contact | Regulation, Article 3(4) | contact point of the metadata, criterion M2 | 6 | 0 | 6 | 0 |
| Marked as a high-value dataset | Regulation, Article 3(5) | criterion M9 | 9 | 0 | 3 | 0 |
| Documentation of the structure | Regulation, Annex, points 2.2(c), 3.2(c), 4.2(c), 5.2(b) and 6.2(c) | criterion AI2 | 1 | 9 | 0 | 2 |

## The table

The datasets outside the Annex and the doubtful ones are listed with their answers and are not counted above.

| Dataset | Title | In the Annex | Declared category | Marking | Free | Licence | API | Bulk download | API terms and documentation | Contact | Marked | Documentation of the structure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | [Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος Κτηματολογίου"](https://data.gov.gr/dataset/geotemachia-oria-kai-kaek-ton-periochon-toy-leitoyrgoyntos-ktimatologioy) | yes | Geospatial | correct | yes | no | no | yes | not applicable | no | yes | not asked by the Annex |
| S02 | [Καλλικρατικοί Δήμοι](https://data.gov.gr/dataset/gis-ypen-wfd-wms-kallikratikoi_dimoi) | yes | - | not marked | yes | yes | yes | yes | no | no | no | not asked by the Annex |
| S03 | [Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ)](https://data.gov.gr/dataset/dromologia-statheron-sygkoinonion-metro-isap-tram) | doubtful | Geospatial | - | yes | no | no | yes | not applicable | yes | yes | yes |
| S04 | [Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υδροληψίας) - περιοχή Ανατολικής Μακεδονίας & Θράκης](https://data.gov.gr/dataset/simeia-ydrolipsias-tis-geovasis-emsy-ethniko-mitroo-simeion-ydrolipsias-periochi-anatolikis-makedoni) | yes | Geospatial | other category | yes | yes | yes | yes | yes | yes | yes | partly |
| S05 | [Λίστα με Μονάδες Φροντίδας Ηλικιωμένων](https://data.gov.gr/dataset/attica-43-lista-me-monades-frontidas-hlikiwmenwn) | no | Geospatial | - | yes | no | no | yes | not applicable | yes | yes | not asked by the Annex |
| S06 | [Τροχαία ατυχήματα](https://data.gov.gr/dataset/troxaia-atyxhmata) | no | Statistics | - | yes | yes | no | yes | not applicable | yes | yes | yes |
| S07 | [Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος](https://data.gov.gr/dataset/diacheirisi-stoicheion-paragogis-nopoy-galaktos) | no | Statistics | - | yes | yes | yes | yes | yes | yes | yes | yes |
| S08 | ["ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ, ΑΝΑ ΕΙΔΙΚΟΤΗΤΑ ΚΑΙ ΣΧΕΣΗ ΕΡΓΑΣΙΑΣ, ΑΝΑ ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΕΚΠΑΙΔΕΥΣΗΣ ΓΙΑ ΤΟ ΣΧΟΛΙΚΟ ΕΤΟΣ 2024-2025 "](https://data.gov.gr/dataset/arithmos-ekpaideytikon-deyterovathmia-eidikotita-schesi-ergasias-2025) | no | Statistics | - | yes | yes | yes | yes | yes | no | yes | partly |
| S09 | [Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής](https://data.gov.gr/dataset/attica-92-lista-anamonhs-iatrwn-gia-eidikeysh-sta-nosokomeia-attikhs-2020) | no | Statistics | - | yes | no | no | yes | not applicable | yes | yes | partly |
| S10 | [ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ)](https://data.gov.gr/dataset/enarmonismenos-deiktis-timon-katanaloti-endtk) | yes | Statistics | correct | yes | yes | yes | yes | yes | yes | yes | partly |
| S11 | [Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ)](https://data.gov.gr/dataset/dromologia-odikon-sygkoinonion-leoforeia-trolei) | doubtful | Mobility | - | yes | no | no | yes | not applicable | no | yes | yes |
| S12 | [Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης](https://data.gov.gr/dataset/dedomena-astikon-sygkoinonion-p-e-thessalonikis) | doubtful | Mobility | - | yes | yes | no | yes | not applicable | yes | yes | partly |
| S13 | [Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS](https://data.gov.gr/dataset/oasth-gtfs) | doubtful | Mobility | - | yes | yes | partly | yes | yes | no | yes | yes |
| S14 | [Υπηρεσίες Δήμου Πατρέων](https://data.gov.gr/dataset/ypiresies-dimoy-patreon) | doubtful | Mobility | - | yes | yes | no | yes | not applicable | yes | yes | partly |
| S15 | [ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ](https://data.gov.gr/dataset/https-www-nafpaktos-gr-el-prosvasi) | doubtful | Mobility | - | yes | yes | yes | yes | yes | yes | yes | partly |
| S16 | [Θεσμοθετημένες περιοχές NATURA 2000](https://data.gov.gr/dataset/thesmothetimenes-perioches-natura-2000) | yes | Geospatial | other category | yes | yes | no | yes | not applicable | no | yes | partly |
| S17 | [Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ](https://data.gov.gr/dataset/apd-kritis-harv2-__) | yes | Earth observation and environment; Geospatial | correct with one more category | yes | yes | no | yes | not applicable | yes | yes | partly |
| S18 | [Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018](https://data.gov.gr/dataset/gis-syros-ermoupolis-wms-syros-lcv_pol_corine_land_cover_2012_2018) | yes | - | not marked | yes | yes | yes | yes | yes | no | no | partly |
| S19 | [Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ](https://data.gov.gr/dataset/emy-station-189) | yes | Meteorological | correct | yes | yes | yes | yes | yes | yes | yes | partly |
| S20 | [Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-2023 από 54 μετεωρολογικούς σταθμούς](https://data.gov.gr/dataset/stations-data) | yes | Meteorological | correct | yes | yes | no | yes | not applicable | no | yes | partly |
| S21 | [Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης](https://data.gov.gr/dataset/apd-kritis-harv2-56) | yes | Earth observation and environment; Geospatial | other category | yes | yes | yes | yes | yes | yes | yes | yes |
| S22 | [Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδοση προσωρινού πίνακα κατάταξης επενδυτικών σχεδίων που υποβλήθηκαν προς υπαγωγή στο καθεστώς ενίσχυσης "Ενίσχυση Τουριστικών Επενδύσεων" (β΄ κύκλος) στο Υπουργείο Ανάπτυξης](https://data.gov.gr/dataset/prosorinoi-pinakes-katataxis-g-pr-21487-13-03-2024-ekdosi-prosorinoy-pinaka-katataxis-ependytikon-sc) | no | Companies and company ownership | - | yes | yes | no | yes | not applicable | yes | yes | partly |
| S23 | [Athens Business Open Data - STIRData model](https://data.gov.gr/dataset/athens-business-open-data-stirdata-model) | yes | - | not marked | yes | yes | no | yes | not applicable | no | no | partly |
| S24 | [ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ)](https://data.gov.gr/dataset/apofaseis-egkrisis-perivallontikon-oron-lesvos-limnos) | yes | Companies and company ownership; Earth observation and environment | correct with one more category | yes | yes | yes | yes | yes | yes | yes | partly |

## Datasets of the catalogue marked as high-value (1,302)

What the metadata allow to check for every marked dataset. A dataset that declares two categories is counted in both. Whether the content of a marked dataset is in the Annex cannot be judged automatically: in the sample it holds for 9 of the 21 marked datasets.

| Declared category | Datasets | Open licence | Point of contact | Complete marking |
| --- | ---: | ---: | ---: | ---: |
| Statistics | 606 | 546 (90.1%) | 408 (67.3%) | 606 (100.0%) |
| Mobility | 264 | 262 (99.2%) | 254 (96.2%) | 264 (100.0%) |
| Geospatial | 220 | 177 (80.5%) | 194 (88.2%) | 220 (100.0%) |
| Earth observation and environment | 209 | 209 (100.0%) | 198 (94.7%) | 209 (100.0%) |
| (none) | 180 | 178 (98.9%) | 180 (100.0%) | 0 (0.0%) |
| Meteorological | 129 | 129 (100.0%) | 108 (83.7%) | 129 (100.0%) |
| Companies and company ownership | 30 | 29 (96.7%) | 29 (96.7%) | 30 (100.0%) |
| all marked datasets | 1,302 | 1,195 (91.8%) | 1,041 (80.0%) | 1,122 (86.2%) |
