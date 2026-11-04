# Automated metadata checks: snapshot of 2026-10-24

Source: catalog_2026-10-24.jsonl.gz. Datasets: 22,805. Proposed scores follow the rules of `criteria/criteria.csv`; the scores of the sample are confirmed or corrected in the manual assessment.

## M1 Mandatory metadata

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 9,130 | 40.0% |
| 1 | 12,928 | 56.7% |
| 0 | 747 | 3.3% |

| Reason | Datasets |
| --- | ---: |
| title, description and access URLs present | 9,130 |
| description shorter than 100 characters | 8,201 |
| description repeats the title | 4,727 |
| no description | 711 |
| resources without an access URL | 36 |

## M2 Recommended metadata

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 7,775 | 34.1% |
| 1 | 14,718 | 64.5% |
| 0 | 312 | 1.4% |

| Reason | Datasets |
| --- | ---: |
| 4 of 7 present | 12,286 |
| 7 of 7 present | 5,813 |
| 5 of 7 present | 2,065 |
| 6 of 7 present | 1,962 |
| 3 of 7 present | 367 |
| 2 of 7 present | 155 |
| 1 of 7 present | 153 |
| 0 of 7 present | 4 |

| Property | Datasets with a value | Share |
| --- | ---: | ---: |
| keyword | 22,456 | 98.5% |
| theme | 22,352 | 98.0% |
| publisher | 8,216 | 36.0% |
| contact point | 7,600 | 33.3% |
| geographical coverage | 22,019 | 96.6% |
| temporal coverage | 21,620 | 94.8% |
| update frequency | 9,233 | 40.5% |

Publisher in the DCAT-AP export of the portal (only the first case counts in M2):

| Source of the publisher | Datasets | Share |
| --- | ---: | ---: |
| publisher field of the dataset | 8,216 | 36.0% |
| organisation, exported when the field is absent | 13,981 | 61.3% |
| none: the field is present but empty | 608 | 2.7% |

## M3 Controlled vocabularies

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 22,053 | 96.7% |
| 1 | 671 | 2.9% |
| 0 | 81 | 0.4% |

| Reason | Datasets |
| --- | ---: |
| all from vocabularies | 22,053 |
| some free text | 671 |
| no vocabulary term | 75 |
| nothing declared | 6 |

Resources with a format or media type: 83,949. With a vocabulary term (format or media type): 83,076 (99.0%); with a format that is itself a term of the EU file-type vocabulary or an IANA media type: 78,725 (93.8%).

| Free-text format value (most frequent) | Datasets |
| --- | ---: |
| ASHX | 195 |
| URL | 144 |
| PHP | 128 |
| Unknown | 62 |
| csw | 44 |
| TIF | 42 |
| ASPX | 26 |
| LINK | 16 |
| shp zip | 13 |
| JSP | 12 |
| JSPX | 11 |
| cif | 10 |
| shape-zip | 5 |
| data | 4 |
| GZ | 4 |

## M4 Licence

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 21,855 | 95.8% |
| 1 | 377 | 1.7% |
| 0 | 573 | 2.5% |

| Reason | Datasets |
| --- | ---: |
| open licence on every resource | 21,855 |
| no licence | 387 |
| share-alike licence | 181 |
| licence only as text, without a link | 173 |
| restrictive licence on a resource | 113 |
| no resources | 73 |
| licence missing on resources | 22 |
| different licences between resources | 1 |

| Licence of the resources (EU vocabulary) | Class | Datasets |
| --- | --- | ---: |
| CC_BY_4_0 | permissive | 21,683 |
| CC0 | permissive | 194 |
| ODC_BL | share-alike | 147 |
| CC_BYNCND_4_0 | restrictive | 80 |
| CC_BYSA_4_0 | share-alike | 33 |
| CC_BYNC_4_0 | restrictive | 27 |
| CC_BYND_1_0 | restrictive | 5 |
| CC_BY_1_0 | permissive | 4 |
| CC_BYSA_1_0 | share-alike | 1 |
| OGL_NC_2_0 | restrictive | 1 |

Generic dataset-level licence field of CKAN (not shown on the portal, not exported, not scored): filled in 7,535 datasets (33.0%); it contradicts the licences of the resources in 1,650 datasets (7.2%).

## M6 Mode of distribution

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 13,974 | 61.3% |
| 1 | 8,732 | 38.3% |
| 0 | 99 | 0.4% |

| Reason | Datasets |
| --- | ---: |
| direct link to a file | 9,067 |
| only a map view (WMS) | 7,616 |
| API or data service | 4,907 |
| only web pages | 1,116 |
| no resources | 73 |
| no address on any resource | 26 |

Mode of access of the resources, read from the address, the declared format and the result of the portal's link checker; 1,049 resources are classed from the declared format alone (not verified). The dataset scores its best mode.

| Mode of access | Score as best mode | Resources | Datasets |
| --- | ---: | ---: | ---: |
| API or data service (WFS, DataStore, OAI-PMH, ArcGIS REST, data service of the portal) | 2 | 22,430 | 4,907 |
| direct link to a file | 2 | 30,681 | 9,139 |
| map view (WMS) | 1 | 31,713 | 12,003 |
| web page | 1 | 1,895 | 1,434 |
| no address | 0 | 63 | 60 |

| Best mode of the dataset | Datasets | Share |
| --- | ---: | ---: |
| API or data service | 4,907 | 21.5% |
| direct link to a file | 9,067 | 39.8% |
| map view | 7,616 | 33.4% |
| web page | 1,116 | 4.9% |
| no address | 26 | 0.1% |

| Organisation with the most datasets offered only as a map view | Datasets | Of its datasets |
| --- | ---: | ---: |
| Δήμος Χανίων | 1,811 | 81.4% |
| Δήμος Αγρινίου | 944 | 78.9% |
| Δήμος Αμαρουσίου | 783 | 89.0% |
| Δήμος Ηρακλείου Κρήτης | 783 | 83.6% |
| Δήμος Καλαμάτας | 675 | 83.7% |
| Δήμος Κερατσινίου – Δραπετσώνας | 583 | 74.3% |
| Δήμος Ιλίου | 467 | 77.4% |
| Περιφέρεια Κρήτης | 302 | 31.9% |
| Δήμος Ωραιοκάστρου | 226 | 57.9% |
| Υπουργείο Περιβάλλοντος και Ενέργειας | 224 | 36.7% |

## M7 Persistent identifier

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 22,405 | 98.2% |
| 1 | 301 | 1.3% |
| 0 | 99 | 0.4% |

| Reason | Datasets |
| --- | ---: |
| permanent identifier and stable addresses | 22,405 |
| every resource through a changing address | 249 |
| no resources | 73 |
| address missing on resources | 34 |
| no address on any resource | 26 |
| changing address on resources | 18 |

The portal gives every dataset a permanent identifier (UUID) and a URI built on it, both exported in DCAT-AP, and every resource a URI of its own; the criterion is decided by the addresses of the resources (the automatic ZIP bundle of the portal is not counted).

| Resources | Stable address | Resources | Datasets |
| --- | --- | ---: | ---: |
| uploaded on the portal | yes | 18,829 | 7,153 |
| in a DataStore table of the portal | yes | 5 | 3 |
| through a standard service request (WMS, WFS, OAI-PMH) | yes | 41,938 | 12,176 |
| at a plain address on another site | yes | 24,907 | 15,052 |
| on a third-party storage service | yes | 87 | 64 |
| with a token, ticket or session parameter | no | 900 | 244 |
| through a URL shortener | no | 49 | 28 |
| through a search-engine redirect | no | 4 | 3 |
| without an address | - | 63 | 60 |

| Site of the changing addresses (most frequent) | Datasets |
| --- | ---: |
| opendata.attica.gov.gr | 241 |
| goo.gl | 13 |
| shorturl.at | 12 |
| tinyurl.com | 9 |
| bit.ly | 8 |
| google.com | 2 |
| ypeka.gr | 2 |
| google.gr | 1 |
| 1drv.ms | 1 |
| ministryofjustice.gr | 1 |

## M9 High-value designation

The criterion applies to the high-value datasets. In the catalogue it is counted over the 1,302 datasets that carry any high-value marking; the other 21,503 datasets are not marked, and whether they are high-value by content is judged by hand (in the sample: the high-value group only).

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 1,122 | 86.2% |
| 1 | 180 | 13.8% |
| 0 | 0 | 0.0% |

| Reason | Datasets |
| --- | ---: |
| category and Regulation 2023/138 declared | 1,122 |
| only the dataset type HVD | 161 |
| reference to Regulation 2023/138 without a category | 16 |
| reference to Regulation 2023/138 without a category (type HVD only otherwise) | 3 |

| Marking | Datasets |
| --- | ---: |
| category and Regulation 2023/138 | 1,122 |
| category, Regulation 2023/138 and type HVD | 372 |
| only the type HVD | 161 |
| Regulation 2023/138 without a category | 19 |

| Declared high-value category | Datasets |
| --- | ---: |
| Statistics | 606 |
| Mobility | 264 |
| Geospatial | 220 |
| Earth observation and environment | 209 |
| Meteorological | 129 |
| Companies and company ownership | 30 |

## Q5 Timeliness (metadata part)

Metadata part only: the declared frequency against the last upload known to the portal. Declared frequency: periodic 1,283 datasets (continuous counted with a period of one day), not updated 7,483 (of which 7,368 carry the keyword of the migration from the previous portal, whose default value it is), no usable period 13,966. An upload date exists for 7,286 datasets; in 5,853 of them the date written by the migration copy is replaced by the original upload date. The others carry only the date of their portal record, which is the history of the portal and not of the data. A dataset declared as not updated scores 2 when its title or description states the period of its data; otherwise the rule of no period applies. Counted over the 7,828 measurable datasets; 14,904 datasets are not measurable from the metadata and 73 have no resources. The final scores of the sample come from the dates inside the data and from the second snapshot.

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 3,520 | 45.0% |
| 1 | 900 | 11.5% |
| 0 | 3,408 | 43.5% |

| Reason | Datasets |
| --- | ---: |
| declared as not updated without a stated period, no upload for more than 12 months | 3,241 |
| declared as not updated, period of the data stated | 3,159 |
| no usable period, upload in the last 12 months | 750 |
| periodic frequency, upload within two periods | 361 |
| declared as not updated without a stated period, upload in the last 12 months | 145 |
| no usable period, no upload for more than 12 months | 133 |
| periodic frequency, more than four periods late | 34 |
| periodic frequency, two to four periods late | 5 |

| Declared frequency (EU vocabulary) | Group | Datasets | Share |
| --- | --- | ---: | ---: |
| (none) | no period | 13,572 | 59.5% |
| NOT_PLANNED | not updated | 7,485 | 32.8% |
| ANNUAL | periodic | 349 | 1.5% |
| MONTHLY | periodic | 343 | 1.5% |
| DAILY | periodic | 251 | 1.1% |
| IRREG | no period | 236 | 1.0% |
| AS_NEEDED | no period | 197 | 0.9% |
| CONT | periodic | 102 | 0.4% |
| QUARTERLY | periodic | 84 | 0.4% |
| HOURLY | periodic | 79 | 0.3% |
| BIENNIAL | periodic | 28 | 0.1% |
| UPDATE_CONT | periodic | 20 | 0.1% |
| TRIENNIAL | periodic | 11 | 0.0% |
| NEVER | not updated | 8 | 0.0% |
| OTHER | no period | 8 | 0.0% |
| ANNUAL_3 | periodic | 7 | 0.0% |
| UNKNOWN | no period | 6 | 0.0% |
| ANNUAL_2 | periodic | 6 | 0.0% |
| QUINQUENNIAL | periodic | 4 | 0.0% |
| BIMONTHLY | periodic | 3 | 0.0% |

| Last change known to the portal | Datasets |
| --- | ---: |
| upload date of a resource (measurable) | 7,286 |
| date of the resource record only (history of the portal) | 15,446 |
| date of the metadata only | 73 |
| none (no resources) | 0 |

| Group | Score 2 | Score 1 | Score 0 | Not measurable |
| --- | ---: | ---: | ---: | ---: |
| periodic | 361 | 5 | 34 | 883 |
| not updated, period stated | 3,159 | 0 | 0 | 0 |
| not updated, no period stated | 0 | 145 | 3,241 | 938 |
| no usable period | 0 | 750 | 133 | 13,083 |

## Q6 Format (5-star scale)

Rated from the declared formats, pending the content check of the sample. Counted over the 22,172 datasets whose best resource has a known level; 560 datasets are undetermined (compressed archives whose content is not named, or no format) and 73 have no resources. 647 of the rated datasets are provisional: an archive with unknown content could raise their level.

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 6,605 | 29.8% |
| 1 | 5,324 | 24.0% |
| 0 | 10,243 | 46.2% |

| Reason | Datasets |
| --- | ---: |
| 1 star | 10,243 |
| 3 stars or more | 6,605 |
| 2 stars | 5,324 |

| Level of the resources | Resources | Datasets with at least one |
| --- | ---: | ---: |
| 3 stars or more: open structured format | 21,603 | 6,605 |
| 2 stars: vendor-specific structured format | 22,034 | 9,928 |
| 1 star: unstructured format or map view | 41,315 | 15,072 |
| undetermined | 1,767 | 734 |

| Best level of the dataset | Datasets | Share |
| --- | ---: | ---: |
| 3 stars or more: open structured format | 6,605 | 29.0% |
| 2 stars: vendor-specific structured format | 5,324 | 23.3% |
| 1 star: unstructured format or map view | 10,243 | 44.9% |
| undetermined | 560 | 2.5% |
| no resources | 73 | 0.3% |

| How the level of the resources was decided (most frequent) | Resources |
| --- | ---: |
| map view (WMS): a picture of the map, not the data | 31,713 |
| vendor-specific format XLSX | 9,812 |
| vendor-specific format XLS | 6,524 |
| unstructured format PDF | 5,361 |
| WFS download in csv | 4,343 |
| WFS download in shape-zip | 4,321 |
| WFS service (GML or GeoJSON on request) | 4,302 |
| WFS download in application/json | 4,300 |
| WFS download in kml | 4,219 |
| open format CSV | 2,100 |
| web page | 1,895 |
| archive (ZIP) with unknown content | 1,279 |
| unstructured format DOC | 621 |
| vendor-specific format .xls (address) | 591 |
| open format ODS | 525 |
| vendor-specific format .xlsx (address) | 443 |
| unstructured format JPEG | 369 |
| unstructured format DOCX | 348 |
| unstructured format .pdf (address) | 335 |
| data service | 332 |
| archive (RAR) with unknown content | 303 |
| open format JSON | 278 |
| open format XML | 267 |
| unstructured format TXT | 178 |
| OAI-PMH request (XML) | 156 |
