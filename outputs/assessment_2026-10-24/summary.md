# Assessment of the sample, snapshot of 2026-10-24

Scores of the 36 datasets of the sample in the 23 criteria of `criteria/criteria.csv`: the scores given by the reviewer (`criteria/sample_scores.csv`) and, for the criteria checked on the metadata, the automated scores of `04_metadata_checks.py` (`data/processed/metadata_checks_2026-10-24.csv`). Scale: 2 fully met, 1 partly met, 0 not met, n/a not applicable. The rules of every criterion and the reviews of the scores are recorded in `DECISIONS.md`.

## Readiness groups

The six core criteria decide the group (DECISIONS.md #20): Ready, all of them score 2; Almost ready, every core criterion below 2 can be fixed with low effort; Not yet, at least one needs medium or high effort.

| Group | Datasets | High-value | Comparison | Datasets of the group |
| --- | ---: | ---: | ---: | --- |
| Ready | 2 | 2 | 0 | S07, S13 |
| Almost ready | 12 | 12 | 0 | S02, S03, S04, S10, S11, S12, S14, S15, S18, S19, S20, S23 |
| Not yet | 22 | 10 | 12 | S01, S05, S06, S08, S09, S16, S17, S21, S22, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34, S35, S36 |

## Score per level

Sum of the scores divided by the maximum possible score (2 for each applicable criterion). The levels are not combined into one number. Mean of the datasets of each group of the sample:

| Group of the sample | Datasets | Quality | Metadata and legal status | AI-readiness |
| --- | ---: | ---: | ---: | ---: |
| high-value | 24 | 79.2% | 86.7% | 61.2% |
| comparison | 12 | 52.5% | 83.4% | 29.3% |
| all | 36 | 70.3% | 85.6% | 50.5% |

Left out of the score of its level while provisional: Q5.

## Datasets

| Dataset | Title | Quality | Metadata and legal status | AI-readiness | Core criteria below 2, low effort | Core criteria below 2, medium or high effort | Group |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| S01 | [Γεωτεμάχια (όρια και ΚΑΕΚ) των περιοχών του "Λειτουργούντος Κτηματολογίου"](https://data.gov.gr/dataset/geotemachia-oria-kai-kaek-ton-periochon-toy-leitoyrgoyntos-ktimatologioy) | 90.0% | 80.0% | 64.3% | M4 | Q6 | Not yet |
| S02 | [Καλλικρατικοί Δήμοι](https://data.gov.gr/dataset/gis-ypen-wfd-wms-kallikratikoi_dimoi) | 100.0% | 80.0% | 75.0% | AI2 | - | Almost ready |
| S03 | [Δρομολόγια Σταθερών Συγκοινωνιών (ΜΕΤΡΟ, ΗΣΑΠ, ΤΡΑΜ)](https://data.gov.gr/dataset/dromologia-statheron-sygkoinonion-metro-isap-tram) | 90.0% | 85.0% | 71.4% | M4 | - | Almost ready |
| S04 | [Σημεία Υδροληψίας της Γεωβάσης ΕΜΣΥ (Εθνικό Μητρώο Σημείων Υδροληψίας) - περιοχή Ανατολικής Μακεδονίας & Θράκης](https://data.gov.gr/dataset/simeia-ydrolipsias-tis-geovasis-emsy-ethniko-mitroo-simeion-ydrolipsias-periochi-anatolikis-makedoni) | 70.0% | 85.0% | 64.3% | M1 AI2 | - | Almost ready |
| S05 | [Λίστα με Μονάδες Φροντίδας Ηλικιωμένων](https://data.gov.gr/dataset/attica-43-lista-me-monades-frontidas-hlikiwmenwn) | 60.0% | 75.0% | 35.7% | M4 AI2 | Q6 AI1 | Not yet |
| S06 | [Τροχαία ατυχήματα](https://data.gov.gr/dataset/troxaia-atyxhmata) | 80.0% | 85.0% | 50.0% | M1 | Q6 AI1 | Not yet |
| S07 | [Διαχείριση Στοιχείων Παραγωγής Νωπού Γάλακτος](https://data.gov.gr/dataset/diacheirisi-stoicheion-paragogis-nopoy-galaktos) | 100.0% | 95.0% | 85.7% | - | - | Ready |
| S08 | ["ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ ΔΗΜΟΣΙΑΣ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ, ΑΝΑ ΕΙΔΙΚΟΤΗΤΑ ΚΑΙ ΣΧΕΣΗ ΕΡΓΑΣΙΑΣ, ΑΝΑ ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΕΚΠΑΙΔΕΥΣΗΣ ΓΙΑ ΤΟ ΣΧΟΛΙΚΟ ΕΤΟΣ 2024-2025 "](https://data.gov.gr/dataset/arithmos-ekpaideytikon-deyterovathmia-eidikotita-schesi-ergasias-2025) | 80.0% | 95.0% | 50.0% | AI2 | AI1 | Not yet |
| S09 | [Λίστα αναμονής ιατρών για ειδίκευση στα νοσοκομεία Αττικής](https://data.gov.gr/dataset/attica-92-lista-anamonhs-iatrwn-gia-eidikeysh-sta-nosokomeia-attikhs-2020) | 60.0% | 75.0% | 42.9% | M1 M4 AI2 | Q6 | Not yet |
| S10 | [ΕΝΑΡΜΟΝΙΣΜΕΝΟΣ ΔΕΙΚΤΗΣ ΤΙΜΩΝ ΚΑΤΑΝΑΛΩΤΗ (ΕνΔΤΚ)](https://data.gov.gr/dataset/enarmonismenos-deiktis-timon-katanaloti-endtk) | 80.0% | 100.0% | 78.6% | AI2 | - | Almost ready |
| S11 | [Δρομολόγια Οδικών Συγκοινωνιών (Λεωφορεία, Τρόλεϊ)](https://data.gov.gr/dataset/dromologia-odikon-sygkoinonion-leoforeia-trolei) | 100.0% | 75.0% | 71.4% | M4 | - | Almost ready |
| S12 | [Δεδομένα αστικών συγκοινωνιών Π.Ε. Θεσσαλονίκης](https://data.gov.gr/dataset/dedomena-astikon-sygkoinonion-p-e-thessalonikis) | 80.0% | 80.0% | 64.3% | Q1 M1 AI2 | - | Almost ready |
| S13 | [Σύνολα Δεδομένων Οργανισμού Αστικών Συγκοινωνιών - GTFS](https://data.gov.gr/dataset/oasth-gtfs) | 100.0% | 90.0% | 71.4% | - | - | Ready |
| S14 | [Υπηρεσίες Δήμου Πατρέων](https://data.gov.gr/dataset/ypiresies-dimoy-patreon) | 60.0% | 75.0% | 64.3% | Q1 M1 AI2 | - | Almost ready |
| S15 | [ΧΩΡΟΙ - ΘΕΣΕΙΣ ΣΤΑΘΜΕΥΣΗΣ](https://data.gov.gr/dataset/https-www-nafpaktos-gr-el-prosvasi) | 70.0% | 100.0% | 57.1% | AI2 | - | Almost ready |
| S16 | [Θεσμοθετημένες περιοχές NATURA 2000](https://data.gov.gr/dataset/thesmothetimenes-perioches-natura-2000) | 70.0% | 90.0% | 57.1% | AI2 | Q6 | Not yet |
| S17 | [Σταθμοί Παραγωγής Ηλεκτρικής Ενέργειας από ΑΠΕ](https://data.gov.gr/dataset/apd-kritis-harv2-__) | 60.0% | 85.0% | 57.1% | AI2 | Q1 Q6 | Not yet |
| S18 | [Κάλυψη γης - Μεταβολές Corine Land Cover 2012 - 2018](https://data.gov.gr/dataset/gis-syros-ermoupolis-wms-syros-lcv_pol_corine_land_cover_2012_2018) | 90.0% | 85.0% | 64.3% | AI2 | - | Almost ready |
| S19 | [Μετεωρολογικά Δεδομένα σταθμού ΠΑΡΝΗΘΑ](https://data.gov.gr/dataset/emy-station-189) | 60.0% | 95.0% | 64.3% | M1 AI2 | - | Almost ready |
| S20 | [Ημερήσιες μετεωρολογικές παράμετροι για την περίοδο 2010-2023 από 54 μετεωρολογικούς σταθμούς](https://data.gov.gr/dataset/stations-data) | 90.0% | 90.0% | 78.6% | AI2 | - | Almost ready |
| S21 | [Βροχομετρικά στοιχεία 56 σταθμών της Νήσου Κρήτης](https://data.gov.gr/dataset/apd-kritis-harv2-56) | 70.0% | 95.0% | 64.3% | Q1 | Q6 AI1 | Not yet |
| S22 | [Προσωρινοί πίνακες κατάταξης - Γ.Πρ. 21487- 13-03-2024 - Έκδοση προσωρινού πίνακα κατάταξης επενδυτικών σχεδίων που υποβλήθηκαν προς υπαγωγή στο καθεστώς ενίσχυσης "Ενίσχυση Τουριστικών Επενδύσεων" (β΄ κύκλος) στο Υπουργείο Ανάπτυξης](https://data.gov.gr/dataset/prosorinoi-pinakes-katataxis-g-pr-21487-13-03-2024-ekdosi-prosorinoy-pinaka-katataxis-ependytikon-sc) | 80.0% | 95.0% | 50.0% | AI2 | Q6 AI1 | Not yet |
| S23 | [Athens Business Open Data - STIRData model](https://data.gov.gr/dataset/athens-business-open-data-stirdata-model) | 80.0% | 75.0% | 50.0% | AI2 | - | Almost ready |
| S24 | [ΑΠΟΦΑΣΕΙΣ ΕΓΚΡΙΣΗΣ ΠΕΡΙΒΑΛΛΟΝΤΙΚΩΝ ΟΡΩΝ (ΛΕΣΒΟΣ-ΛΗΜΝΟΣ)](https://data.gov.gr/dataset/apofaseis-egkrisis-perivallontikon-oron-lesvos-limnos) | 80.0% | 95.0% | 35.7% | AI2 | AI1 | Not yet |
| S25 | [ΣΤΑΤΙΣΤΙΚΑ ΔΙΑΤΡΟΦΗΣ ΦΕΒΡΟΥΑΡΙΟΥ 2017](https://data.gov.gr/dataset/statistika-diatrofhs-febroyarioy-2017) | 90.0% | 93.8% | 42.9% | M1 AI2 | Q6 AI1 | Not yet |
| S26 | [ΣΤΑΤΙΣΤΙΚΑ ΙΧΘΥΟΣΚΑΛΑΣ ΘΕΣΣΑΛΟΝΙΚΗΣ ΜΑΡΤΙΟΣ 2020](https://data.gov.gr/dataset/statistika-ix8yoskalas-8essalonikhs-martios-2020) | 80.0% | 93.8% | 42.9% | M1 AI2 | AI1 | Not yet |
| S27 | [ΤΡΟΠΟΠΟΙΗΣΗ ΡΥΜΟΤΟΜΙΚΟΥ (ΦΕΚ 463/Δ/1998-07-03)](https://data.gov.gr/dataset/gis-agrinio-wms-only-agriniotrm-trm_ras_123107fs000463_1998_geo) | 50.0% | 87.5% | 30.0% | - | Q6 AI1 | Not yet |
| S28 | [Σχέδιο ΠΕ περιοχής Ατσαλένιο \| Μωσαϊκό](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliopef-pef_ras_atsalenio_mosaic_geo) | 0.0% | 66.7% | 0.0% | M1 | Q1 Q6 AI1 | Not yet |
| S29 | [ΠΙΝΑΚΕΣ ΤΙΜΟΛΗΨΙΩΝ ΣΥΡΟΥ](https://data.gov.gr/dataset/pinakes-timolhpsiwn-syroy) | 80.0% | 87.5% | 35.7% | M1 AI2 | Q6 AI1 | Not yet |
| S30 | [Διάγραμμα Τροποποιήσεως του Ρυμοτομικού Σχεδίου της Πόλης Χανίων](https://data.gov.gr/dataset/gis-chania-wms-only-chaniatsp-tsp_ras_fek_2003_739_d_200_geo) | 50.0% | 81.3% | 20.0% | M1 | Q6 AI1 | Not yet |
| S31 | [ΠΡΟΓΡΑΜΜΑΤΙΚΕΣ ΣΥΜΒΑΣΕΙΣ ΠΕΡΙΦΕΡΕΙΑΣ ΑΤΤΙΚΗΣ](https://data.gov.gr/dataset/programmatikes-symbaseis-perifereias-attikhs) | 80.0% | 93.8% | 42.9% | M1 AI2 | Q6 AI1 | Not yet |
| S32 | [Περιβαλλοντικοί έλεγχοι έτους 2014 από τη Δ/νση Περιβάλλοντος & Χωρικού Σχεδιασμού Π.Δ.Ε.](https://data.gov.gr/dataset/periballontikoi-elegxoi-etoys-2014-apo-th-d-nsh-periballontos-and-xwrikoy-sxediasmoy-p-d-e) | 80.0% | 100.0% | 42.9% | AI2 | Q6 AI1 | Not yet |
| S33 | [Διάγραμμα - ΦΕΚ 130/Δ/2001-02-21](https://data.gov.gr/dataset/gis-maroussi-wms-only-maroussirym-rym_015784fs000130_2001e) | 50.0% | 87.5% | 30.0% | - | Q6 AI1 | Not yet |
| S34 | [Αποθετήριο ΤΕΧΝΗ](https://data.gov.gr/dataset/ekt-searchculture-dataset-__-15) | 20.0% | 83.3% | 21.4% | AI2 | Q1 AI1 | Not yet |
| S35 | [Συνεδριάσεις Επιτροπής Αθλητισμού & Παιδείας Περιφέρειας Αττικής](https://data.gov.gr/dataset/attica-443-synedriaseis-epitrophs-athlhtismoy-paideias-perifereias-attikhs) | 50.0% | 50.0% | 33.3% | M1 M4 | Q6 AI1 | Not yet |
| S36 | [Διάγραμμα Τροποποίησης - T1936A404_69912_500_01](https://data.gov.gr/dataset/gis-heraklion-wms-only-herakliotsp-t1936a404_69912_500_01) | 0.0% | 75.0% | 10.0% | - | Q1 Q6 AI1 | Not yet |

## Scores by criterion

| Criterion | Name | Core | 2 | 1 | 0 | n/a | Not measured | Basis |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Q1 | Availability | yes | 29 | 3 | 4 | 0 | 0 | reviewed 36 |
| Q2 | Completeness | no | 16 | 9 | 5 | 6 | 0 | reviewed 36 |
| Q3 | Consistency | no | 18 | 11 | 1 | 6 | 0 | reviewed 36 |
| Q4 | Plausibility of values | no | 20 | 6 | 4 | 6 | 0 | reviewed 36 |
| Q5 | Timeliness | no | 8 | 12 | 2 | 0 | 14 | automatic 36 (provisional) |
| Q6 | Format (5-star scale) | yes | 18 | 10 | 8 | 0 | 0 | automatic 34, reviewed 2 |
| M1 | Mandatory metadata | yes | 23 | 11 | 2 | 0 | 0 | automatic 36 |
| M2 | Recommended metadata | no | 17 | 19 | 0 | 0 | 0 | automatic 36 |
| M3 | Controlled vocabularies | no | 31 | 4 | 1 | 0 | 0 | automatic 36 |
| M4 | Licence | yes | 30 | 0 | 6 | 0 | 0 | automatic 36 |
| M5 | Free access | no | 33 | 0 | 0 | 3 | 0 | reviewed 36 |
| M6 | Mode of distribution | no | 27 | 6 | 3 | 0 | 0 | automatic 32, reviewed 4 |
| M7 | Persistent identifier | no | 33 | 3 | 0 | 0 | 0 | automatic 36 |
| M8 | Personal data | no | 28 | 5 | 0 | 3 | 0 | reviewed 36 |
| M9 | High-value designation | no | 21 | 0 | 3 | 12 | 0 | automatic 24 |
| M10 | API and bulk download | no | 9 | 15 | 0 | 12 | 0 | reviewed 36 |
| AI1 | Machine-readable structure | yes | 18 | 8 | 10 | 0 | 0 | reviewed 36 |
| AI2 | Documentation of the structure | yes | 7 | 23 | 0 | 6 | 0 | reviewed 36 |
| AI3 | Historical depth | no | 5 | 13 | 11 | 7 | 0 | reviewed 36 |
| AI4 | Description in Croissant or a datasheet | no | 4 | 28 | 4 | 0 | 0 | reviewed 36 |
| AI5 | Suitability for retrieval (RAG) | no | 11 | 19 | 6 | 0 | 0 | reviewed 36 |
| AI6 | Linkage through common identifiers | no | 19 | 13 | 4 | 0 | 0 | reviewed 36 |
| AI7 | Declared limitations | no | 1 | 14 | 21 | 0 | 0 | reviewed 36 |

## Effort of the fix for the scores below 2

Low: metadata and documentation only. Medium: a change in the file itself. High: a change in a system or in the source of the data. Open: the criterion names two levels and none is recorded yet for the dataset.

| Criterion | Scores below 2 | Low | Medium | High | Open |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1 | 7 | 3 | 4 | 0 | 0 |
| Q2 | 14 | 0 | 14 | 0 | 0 |
| Q3 | 12 | 0 | 12 | 0 | 0 |
| Q4 | 10 | 0 | 0 | 0 | 10 |
| Q5 | 0 | 0 | 0 | 0 | 0 |
| Q6 | 18 | 0 | 18 | 0 | 0 |
| M1 | 13 | 13 | 0 | 0 | 0 |
| M2 | 19 | 19 | 0 | 0 | 0 |
| M3 | 5 | 5 | 0 | 0 | 0 |
| M4 | 6 | 6 | 0 | 0 | 0 |
| M5 | 0 | 0 | 0 | 0 | 0 |
| M6 | 9 | 0 | 0 | 0 | 9 |
| M7 | 3 | 3 | 0 | 0 | 0 |
| M8 | 5 | 0 | 5 | 0 | 0 |
| M9 | 3 | 3 | 0 | 0 | 0 |
| M10 | 15 | 0 | 0 | 0 | 15 |
| AI1 | 18 | 0 | 18 | 0 | 0 |
| AI2 | 23 | 23 | 0 | 0 | 0 |
| AI3 | 24 | 0 | 24 | 0 | 0 |
| AI4 | 32 | 32 | 0 | 0 | 0 |
| AI5 | 25 | 0 | 25 | 0 | 0 |
| AI6 | 17 | 0 | 17 | 0 | 0 |
| AI7 | 35 | 35 | 0 | 0 | 0 |

## Open points

- Q5: provisional, metadata part of the criterion; the final scores follow the second snapshot (DECISIONS.md #36); 14 datasets are not measured from the metadata.
- Effort of the fix still open: 34 scores below 2 in criteria that name two levels.
