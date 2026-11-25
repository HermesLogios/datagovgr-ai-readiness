# Automated metadata checks: snapshot of 2026-11-25

Source: catalog_2026-11-25.jsonl.gz. Datasets: 23,157. Proposed scores follow the rules of `criteria/criteria.csv`; the scores of the sample are confirmed or corrected in the manual assessment.

## M1 Mandatory metadata

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 9,259 | 40.0% |
| 1 | 13,139 | 56.7% |
| 0 | 759 | 3.3% |

| Reason | Datasets |
| --- | ---: |
| title, description and access URLs present | 9,259 |
| description shorter than 100 characters | 8,400 |
| description repeats the title | 4,739 |
| no description | 711 |
| resources without an access URL | 48 |

## M2 Recommended metadata

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 8,090 | 34.9% |
| 1 | 14,748 | 63.7% |
| 0 | 319 | 1.4% |

| Reason | Datasets |
| --- | ---: |
| 4 of 7 present | 12,302 |
| 7 of 7 present | 6,085 |
| 5 of 7 present | 2,080 |
| 6 of 7 present | 2,005 |
| 3 of 7 present | 366 |
| 1 of 7 present | 157 |
| 2 of 7 present | 157 |
| 0 of 7 present | 5 |

| Property | Datasets with a value | Share |
| --- | ---: | ---: |
| keyword | 22,791 | 98.4% |
| theme | 22,678 | 97.9% |
| publisher | 8,534 | 36.9% |
| contact point | 7,925 | 34.2% |
| geographical coverage | 22,367 | 96.6% |
| temporal coverage | 21,970 | 94.9% |
| update frequency | 9,537 | 41.2% |

Publisher in the DCAT-AP export of the portal (only the first case counts in M2):

| Source of the publisher | Datasets | Share |
| --- | ---: | ---: |
| publisher field of the dataset | 8,534 | 36.9% |
| organisation, exported when the field is absent | 13,967 | 60.3% |
| none: the field is present but empty | 656 | 2.8% |

## M3 Controlled vocabularies

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 22,406 | 96.8% |
| 1 | 663 | 2.9% |
| 0 | 88 | 0.4% |

| Reason | Datasets |
| --- | ---: |
| all from vocabularies | 22,406 |
| some free text | 663 |
| no vocabulary term | 76 |
| nothing declared | 12 |

Resources with a format or media type: 84,960. With a vocabulary term (format or media type): 84,093 (99.0%); with a format that is itself a term of the EU file-type vocabulary or an IANA media type: 79,740 (93.9%).

| Free-text format value (most frequent) | Datasets |
| --- | ---: |
| ASHX | 195 |
| URL | 149 |
| PHP | 111 |
| Unknown | 62 |
| csw | 44 |
| TIF | 42 |
| ASPX | 26 |
| LINK | 14 |
| shp zip | 13 |
| JSP | 12 |
| cif | 10 |
| JSPX | 9 |
| shape-zip | 8 |
| data | 4 |
| GZ | 4 |

## M4 Licence

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 22,199 | 95.9% |
| 1 | 378 | 1.6% |
| 0 | 580 | 2.5% |

| Reason | Datasets |
| --- | ---: |
| open licence on every resource | 22,199 |
| no licence | 389 |
| share-alike licence | 181 |
| licence only as text, without a link | 173 |
| restrictive licence on a resource | 115 |
| no resources | 76 |
| licence missing on resources | 22 |
| different licences between resources | 2 |

| Licence of the resources (EU vocabulary) | Class | Datasets |
| --- | --- | ---: |
| CC_BY_4_0 | permissive | 22,024 |
| CC0 | permissive | 198 |
| ODC_BL | share-alike | 147 |
| CC_BYNCND_4_0 | restrictive | 80 |
| CC_BYSA_4_0 | share-alike | 33 |
| CC_BYNC_4_0 | restrictive | 28 |
| CC_BYND_1_0 | restrictive | 6 |
| CC_BY_1_0 | permissive | 5 |
| CC_BYSA_1_0 | share-alike | 1 |
| OGL_NC_2_0 | restrictive | 1 |

Generic dataset-level licence field of CKAN (not shown on the portal, not exported, not scored): filled in 7,415 datasets (32.0%); it contradicts the licences of the resources in 1,649 datasets (7.1%).

## M6 Mode of distribution

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 14,433 | 62.3% |
| 1 | 8,611 | 37.2% |
| 0 | 113 | 0.5% |

| Reason | Datasets |
| --- | ---: |
| direct link to a file | 9,503 |
| only a map view (WMS) | 7,616 |
| API or data service | 4,930 |
| only web pages | 995 |
| no resources | 76 |
| no address on any resource | 37 |

Mode of access of the resources, read from the address, the declared format and the result of the portal's link checker; 537 resources are classed from the declared format alone (not verified). The dataset scores its best mode.

| Mode of access | Score as best mode | Resources | Datasets |
| --- | ---: | ---: | ---: |
| API or data service (WFS, DataStore, OAI-PMH, ArcGIS REST, data service of the portal) | 2 | 22,460 | 4,930 |
| direct link to a file | 2 | 31,753 | 9,575 |
| map view (WMS) | 1 | 31,713 | 12,003 |
| web page | 1 | 1,795 | 1,326 |
| no address | 0 | 81 | 76 |

| Best mode of the dataset | Datasets | Share |
| --- | ---: | ---: |
| API or data service | 4,930 | 21.3% |
| direct link to a file | 9,503 | 41.0% |
| map view | 7,616 | 32.9% |
| web page | 995 | 4.3% |
| no address | 37 | 0.2% |

| Organisation with the most datasets offered only as a map view | Datasets | Of its datasets |
| --- | ---: | ---: |
| Δήμος Χανίων | 1,811 | 81.4% |
| Δήμος Αγρινίου | 944 | 78.9% |
| Δήμος Αμαρουσίου | 783 | 89.0% |
| Δήμος Ηρακλείου Κρήτης | 783 | 83.5% |
| Δήμος Καλαμάτας | 675 | 83.7% |
| Δήμος Κερατσινίου – Δραπετσώνας | 583 | 74.3% |
| Δήμος Ιλίου | 467 | 77.4% |
| Περιφέρεια Κρήτης | 302 | 31.9% |
| Δήμος Ωραιοκάστρου | 226 | 57.9% |
| Υπουργείο Περιβάλλοντος και Ενέργειας | 224 | 36.7% |

## M7 Persistent identifier

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 22,738 | 98.2% |
| 1 | 306 | 1.3% |
| 0 | 113 | 0.5% |

| Reason | Datasets |
| --- | ---: |
| permanent identifier and stable addresses | 22,738 |
| every resource through a changing address | 248 |
| no resources | 76 |
| address missing on resources | 39 |
| no address on any resource | 37 |
| changing address on resources | 19 |

The portal gives every dataset a permanent identifier (UUID) and a URI built on it, both exported in DCAT-AP, and every resource a URI of its own; the criterion is decided by the addresses of the resources (the automatic ZIP bundle of the portal is not counted).

| Resources | Stable address | Resources | Datasets |
| --- | --- | ---: | ---: |
| uploaded on the portal | yes | 19,644 | 7,467 |
| in a DataStore table of the portal | yes | 5 | 3 |
| through a standard service request (WMS, WFS, OAI-PMH) | yes | 41,938 | 12,176 |
| at a plain address on another site | yes | 25,085 | 15,088 |
| on a third-party storage service | yes | 90 | 66 |
| with a token, ticket or session parameter | no | 906 | 244 |
| through a URL shortener | no | 49 | 28 |
| through a search-engine redirect | no | 4 | 3 |
| without an address | - | 81 | 76 |

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

The criterion applies to the high-value datasets. In the catalogue it is counted over the 1,363 datasets that carry any high-value marking; the other 21,794 datasets are not marked, and whether they are high-value by content is judged by hand (in the sample: the high-value group only).

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 1,180 | 86.6% |
| 1 | 183 | 13.4% |
| 0 | 0 | 0.0% |

| Reason | Datasets |
| --- | ---: |
| category and Regulation 2023/138 declared | 1,180 |
| only the dataset type HVD | 162 |
| reference to Regulation 2023/138 without a category | 18 |
| reference to Regulation 2023/138 without a category (type HVD only otherwise) | 3 |

| Marking | Datasets |
| --- | ---: |
| category and Regulation 2023/138 | 1,180 |
| category, Regulation 2023/138 and type HVD | 389 |
| only the type HVD | 162 |
| Regulation 2023/138 without a category | 21 |

| Declared high-value category | Datasets |
| --- | ---: |
| Statistics | 646 |
| Mobility | 273 |
| Geospatial | 238 |
| Earth observation and environment | 208 |
| Meteorological | 132 |
| Companies and company ownership | 25 |

## Q5 Timeliness (metadata part)

Metadata part only: the declared frequency against the last upload known to the portal. Declared frequency: periodic 1,596 datasets (continuous counted with a period of one day), not updated 7,451 (of which 7,327 carry the keyword of the migration from the previous portal, whose default value it is), no usable period 14,034. An upload date exists for 7,607 datasets; in 5,841 of them the date written by the migration copy is replaced by the original upload date. The others carry only the date of their portal record, which is the history of the portal and not of the data. A dataset declared as not updated scores 2 when its title or description states the period of its data; otherwise the rule of no period applies. Counted over the 8,147 measurable datasets; 14,934 datasets are not measurable from the metadata and 76 have no resources. The final scores of the sample come from the dates inside the data and from the second snapshot.

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 3,787 | 46.5% |
| 1 | 962 | 11.8% |
| 0 | 3,398 | 41.7% |

| Reason | Datasets |
| --- | ---: |
| declared as not updated without a stated period, no upload for more than 12 months | 3,228 |
| declared as not updated, period of the data stated | 3,155 |
| no usable period, upload in the last 12 months | 803 |
| periodic frequency, upload within two periods | 632 |
| declared as not updated without a stated period, upload in the last 12 months | 149 |
| no usable period, no upload for more than 12 months | 136 |
| periodic frequency, more than four periods late | 34 |
| periodic frequency, two to four periods late | 10 |

| Declared frequency (EU vocabulary) | Group | Datasets | Share |
| --- | --- | ---: | ---: |
| (none) | no period | 13,620 | 58.8% |
| NOT_PLANNED | not updated | 7,448 | 32.2% |
| MONTHLY | periodic | 542 | 2.3% |
| ANNUAL | periodic | 446 | 1.9% |
| DAILY | periodic | 250 | 1.1% |
| IRREG | no period | 243 | 1.0% |
| AS_NEEDED | no period | 213 | 0.9% |
| CONT | periodic | 107 | 0.5% |
| QUARTERLY | periodic | 90 | 0.4% |
| HOURLY | periodic | 79 | 0.3% |
| BIENNIAL | periodic | 28 | 0.1% |
| UPDATE_CONT | periodic | 16 | 0.1% |
| ANNUAL_2 | periodic | 15 | 0.1% |
| NEVER | not updated | 13 | 0.1% |
| TRIENNIAL | periodic | 11 | 0.0% |
| ANNUAL_3 | periodic | 8 | 0.0% |
| OTHER | no period | 8 | 0.0% |
| UNKNOWN | no period | 6 | 0.0% |
| QUINQUENNIAL | periodic | 4 | 0.0% |
| BIMONTHLY | periodic | 3 | 0.0% |

| Last change known to the portal | Datasets |
| --- | ---: |
| upload date of a resource (measurable) | 7,607 |
| date of the resource record only (history of the portal) | 15,474 |
| date of the metadata only | 76 |
| none (no resources) | 0 |

| Group | Score 2 | Score 1 | Score 0 | Not measurable |
| --- | ---: | ---: | ---: | ---: |
| periodic | 632 | 10 | 34 | 920 |
| not updated, period stated | 3,155 | 0 | 0 | 0 |
| not updated, no period stated | 0 | 149 | 3,228 | 919 |
| no usable period | 0 | 803 | 136 | 13,095 |

## Q6 Format (5-star scale)

Rated from the declared formats and the DataStore tables of the portal; the content of the files is verified only in the sample (DECISIONS.md #35, #56). Counted over the 22,510 datasets whose best resource has a known level; 571 datasets are undetermined (compressed archives whose content is not named, or no format) and 76 have no resources. 648 of the rated datasets are provisional: an archive with unknown content could raise their level. 631 datasets reach 3 stars only through the DataStore of the portal, which serves as JSON the records of files uploaded in a vendor-specific format.

| Proposed score | Datasets | Share |
| --- | ---: | ---: |
| 2 | 7,359 | 32.7% |
| 1 | 4,903 | 21.8% |
| 0 | 10,248 | 45.5% |

| Reason | Datasets |
| --- | ---: |
| 1 star | 10,248 |
| 3 stars or more | 7,359 |
| 2 stars | 4,903 |

| Level of the resources | Resources | Datasets with at least one |
| --- | ---: | ---: |
| 3 stars or more: open structured format | 22,871 | 7,359 |
| 2 stars: vendor-specific structured format | 21,602 | 9,500 |
| 1 star: unstructured format or map view | 41,464 | 15,117 |
| undetermined | 1,784 | 736 |

| Best level of the dataset | Datasets | Share |
| --- | ---: | ---: |
| 3 stars or more: open structured format | 7,359 | 31.8% |
| 2 stars: vendor-specific structured format | 4,903 | 21.2% |
| 1 star: unstructured format or map view | 10,248 | 44.3% |
| undetermined | 571 | 2.5% |
| no resources | 76 | 0.3% |

| How the level of the resources was decided (most frequent) | Resources |
| --- | ---: |
| map view (WMS): a picture of the map, not the data | 31,713 |
| vendor-specific format XLSX | 9,605 |
| vendor-specific format XLS | 6,269 |
| unstructured format PDF | 5,488 |
| WFS download in csv | 4,343 |
| WFS download in shape-zip | 4,321 |
| WFS service (GML or GeoJSON on request) | 4,302 |
| WFS download in application/json | 4,300 |
| WFS download in kml | 4,219 |
| open format CSV | 2,391 |
| web page | 1,795 |
| archive (ZIP) with unknown content | 1,298 |
| unstructured format DOC | 615 |
| vendor-specific format .xls (address) | 591 |
| open format ODS | 525 |
| DataStore table of the portal next to a file (vendor-specific format XLSX) | 475 |
| vendor-specific format .xlsx (address) | 443 |
| unstructured format JPEG | 369 |
| unstructured format DOCX | 365 |
| data service | 362 |
| DataStore table of the portal next to a file (vendor-specific format XLS) | 342 |
| unstructured format .pdf (address) | 335 |
| archive (RAR) with unknown content | 303 |
| open format JSON | 295 |
| open format XML | 287 |
