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
