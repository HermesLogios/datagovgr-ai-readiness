# Public page of the assessment tool

A static site that checks one dataset of data.gov.gr with the nine metadata checks of the study.
The checks are the Python files of this repository. They run inside the browser of the visitor
with Pyodide, so the scores are those of `scripts/04_metadata_checks.py`.

## How it works

- `build.py` writes the site into `web/dist`: the pages in Greek and English, the Python files
  of the checks packed for the browser, the Python runtime (Pyodide) and the library of the
  Excel report. Each fetched file is checked against a pinned SHA-256 and kept in `web/.cache`.
- `assets/app.js` reads what is typed in the form. For an address or the name of a dataset it asks
  the catalogue for the record of the dataset, with one call to the action `package_search`. The
  portal is called directly from the browser. A browser that is refused asks the relay
  `functions/api/record.js`, which passes the same question to the portal and keeps nothing.
  Words are searched for in the catalogue (see [Search and recent checks](#search-and-recent-checks)).
- `browser.py` receives the reply as text and returns the HTML of the result and the reports.
- `pages.py` and `icons.py` produce all HTML. Every text comes from `aiready/locales`.
- The site sets no cookies and keeps no history of checks on the server. The ten latest checks of
  a visitor are kept only in the storage of the browser of that visitor (see below).

## Search and recent checks

The field of the home page takes an address, the name of a dataset or words.

- Words go to the relay `functions/api/record.js` as `?q=<words>&rows=<number>`. The relay asks
  the catalogue with `package_search` and passes on, for each dataset found, only its name, title,
  publisher, day of the last change and number of files. It accepts from 2 to 100 characters and at
  most 20 datasets, and leaves out the signs of the search language of the portal.
- While the visitor types (3 characters or more, after a pause of 300 ms), up to 8 datasets are
  proposed under the field, which is a combobox: the arrow keys move through the proposals, Enter
  checks the chosen one and Escape closes them. Enter without a proposal lists up to 20 datasets at
  `?search=<words>`, and every dataset of the list leads to its check. Words sent from the form of
  the page of the second opinion become a search too, and its datasets open at that tab.
- `assets/search.js` decides what is words and what names a dataset, and reads the reply of the
  relay; `assets/recent.js` keeps the recent checks. Both touch no page and are tested with Node.
- After a check the page keeps, in `localStorage` under the key `datagovgr-ai-readiness.recent`, the
  record of the catalogue without the contact details that its metadata name, the result as it was
  shown, its day and time, the number of checks met, the ticks of the checklist and, once it is asked
  for, the second opinion. `browser.py` writes that record: the people named as author or maintainer
  and their e-mail addresses are left out, a contact point keeps only a placeholder name, the e-mail
  address of the publisher and the description of the organisation are left out, and every other
  e-mail address is masked by as many characters. On the 22,805 datasets of the snapshot of
  24 October 2026 the nine checks give the same results on the kept record as on the full one, and no
  e-mail address is left in it (checked on 21 November 2026). A new check of the same
  dataset takes the place of the old one, and at most ten checks are kept; when the storage is
  full, the oldest are left out. The key of the model is never part of it, and the example is not
  kept.
- The home page lists the recent checks in the place of the example. A kept check opens at
  `?dataset=<name>&saved=1` as it was first shown, under a bar with its day and time and a link
  that checks the dataset again now; it opens without the Python runtime, which loads only for a
  report or a new second opinion, from the kept reply of the catalogue. A check opens in the
  language in which it was made. Each check can be deleted, and so can all of them.

## Pages and tabs

The site has five pages in each language: the check (`/`), the second opinion
(`/second-opinion/`), the guide (`/guide/`), the criteria (`/criteria/`) and the terms
(`/terms/`). The English pages stand under `/en/`.

A result is shown on the page of the check. Its head names the dataset and shows the nine checks
at a glance. Under the head a bar holds three tabs and the menu of the report files, and stays at
the top of the window while a panel is read.

| Tab | Address ends in | Holds |
| --- | --- | --- |
| Checks | `#checks` | what to correct first, and the nine checks |
| AI second opinion | `#second-opinion` | the offer of a second opinion, and its answer |
| Checklist | `#checklist` | the fourteen criteria that need the files or human judgement |

The address of the page keeps the dataset and the open tab, so a link opens the same view. The
form of the page of the second opinion leads to a result with that tab open. On paper all three
panels are printed.

## Codes of the criteria

Every check, every row of the checklist and every group of statements of the second opinion
carries the code of its criterion in the study (M1, Q5, AI7 and so on). The code leads to the
criterion on the page of the criteria; inside a result it opens a new tab, because a result exists
only in the open page.

The page of the criteria shows how a score is read and one card per criterion, three, two or one
in a row as the width allows. A closed card shows the code of the criterion, its name in the
application and in the study, and how the application treats it; its line "How it is scored"
opens the question, the rule of every score, the case in which it does not apply, and what the
application does with it. A card that opens grows alone, so the cards next to it keep their
place. With the script of the page a click anywhere on a card opens or closes it, a button opens
or closes all the cards, an address with the code of a criterion after the # opens its card, and
on paper every card is printed open; without the script the cards open from their line and the
button stays hidden. The English rules are those of `criteria/criteria.csv`; the Greek rules are their translation in
`aiready/locales/el.json` (keys `criterion.<code>.*`). `tests/test_criteria_texts.py` checks that
both languages hold every rule of the file, that the English rules are the texts of the file, and
that every Greek rule carries the numbers and the names of formats and standards of the English
one. The texts on what the application checks for the nine criteria scored from the metadata
(keys `criterion.<code>.how`) follow `scripts/04_metadata_checks.py`.

## Version

The footer of every page shows the version of the page and its day, from `release.py`. Both
change with every published change, so the footer of the published site tells whether a change
has arrived.

## Second opinion of a model

In the tab of the second opinion a visitor may ask Jev, a model of TypeSafe AI, to read the
description of the dataset (`DECISIONS.md` #54). The reading is optional and needs a key of the
visitor. It gives no score and changes none.

- `aiready/jev.py` holds the statements and the question of choice on the category of high-value
  data, selects the texts that are sent (the title, the description and the descriptions of the
  resources that say more than a name) and reads the reply. Five statements were compared with the
  review of the study (`aiready/jev_trial.py`); the four added on 20 November 2026 (M2, M8, AI2)
  and the category (M9) are not compared yet, and the page says so.
  `aiready/second_reading.py` turns the probabilities into the rows of the page and the hint of the
  category.
- When the DataStore of the portal holds tables of the dataset, the page first asks the relay
  `functions/api/fields.js` for the columns of at most three of them. The relay asks the portal
  for the structure of each table only (`datastore_search` with `limit=0`) and passes on the names,
  the types and the data dictionary of the columns, never a row. The names go to the model with
  the texts, and the statement on the names of the columns is asked only then.
- `browser.py` builds the request for the dataset on the page. `assets/app.js` sends it, with the
  key that the visitor typed, in the body of a POST request to the relay
  `functions/api/reading.js`. The address of the model does not accept calls from a web page.
- The relay accepts only a request of the shape that the page sends, passes it on with the key in
  the Authorization header and returns the reply. Any other field is dropped.
- The key is kept nowhere: the page does not store it, it is never part of an address, the relay
  writes nothing, and `wrangler.jsonc` switches off the logs and the traces of the Worker.
- The page of the second opinion explains how the model works and how a key is issued in the
  console of TypeSafe AI, with a drawing of the console made for the page. The steps in the
  console were checked on 19 November 2026 (`KEY_STEPS_CHECKED` in `pages.py`).
- The model is named by its version (`jev-1.14.0`). `python -m aiready.jev_trial` repeats the
  trial of the model on the 36 datasets of the sample before a new version is adopted.

## Files

| File | Purpose |
| --- | --- |
| `build.py` | builds the site into `web/dist` |
| `preview.py` | builds the site and serves it on this computer, the three relays included |
| `pages.py` | HTML of the home page, the result with its tabs, the page of the second opinion, the guide, the page of the criteria and the terms; in the head of every page the tags of a shared link (Open Graph), and in the footer and under every result a link that opens an issue about a mistake on GitHub, with the page, the dataset and the version already written |
| `release.py` | version of the page and its day, as the footer shows them |
| `icons.py` | status icons, line icons and the mark of the tool (a gauge of readiness) as inline SVG, and the SVG icon of the browser tab |
| `icon_images.py` | PNG and ICO copies of the mark, written with the standard library: `favicon.ico` (16 and 32 px) for browsers without SVG icons and `apple-touch-icon.png` (180 px) for the home screen of phones, both at the root of the site, and `assets/social-preview.png` (1200 by 630 px), the picture that social networks show for a shared link |
| `browser.py` | entry points that the page calls inside the browser |
| `shims/pandas.py` | reader of CSV tables that stands in for pandas inside the browser |
| `assets/` | stylesheet, script (`app.js`, with the modules `search.js` and `recent.js`), typeface and licence texts |
| `example/` | catalogue record of the example, without contact details |
| `functions/api/record.js` | relay to the catalogue: the record of one dataset, or the datasets found for words |
| `functions/api/reading.js` | relay to the model of the second opinion |
| `functions/api/fields.js` | relay to the structure of the tables in the DataStore of the portal |
| `worker.js` | entry of the site on Cloudflare Workers: the three relays, and the files of the build for every other address |
| `wrangler.jsonc` | settings of the Worker: its name, the folder of the build, the entry, and no logs |

## Commands

```
python web/build.py
python web/preview.py
python -m unittest discover -s tests
node --test tests/js/record_relay.test.mjs
node --test tests/js/search_relay.test.mjs
node --test tests/js/search.test.mjs
node --test tests/js/recent.test.mjs
node --test tests/js/reading_relay.test.mjs
node --test tests/js/fields_relay.test.mjs
node --test tests/js/site_worker.test.mjs
```

`preview.py` serves the site at http://localhost:8788. The build needs only the standard
library of Python; the preview and the tests need the packages of `requirements.txt`. After a
build, `npx wrangler dev` inside `web` serves the same files with the Worker of the relays.
The preview and the Worker send a second reading to the address in the variable
`TYPESAFE_API_URL` when it is set, and otherwise to the address of the model.

## Publishing on Cloudflare

The site is published as a Cloudflare Worker with static assets, built from the repository by
Workers Builds. `wrangler.jsonc` names the Worker, the folder of the build and the entry
`worker.js`. Only the addresses under `/api/` reach the Worker; every other address is answered
with the files of the build.

| Setting | Value |
| --- | --- |
| Project name | `datagovgr-ai-readiness`, the name in `wrangler.jsonc` |
| Build command | `python3 build.py` |
| Deploy command | `npx wrangler deploy` |
| Root directory | `web` |

Every push to the production branch builds and publishes the site, as long as the GitHub
application of Cloudflare has access to the repository. A build can also be started by hand with
a Deploy Hook of the Worker; the address of a hook is a secret and is kept out of the repository.
Two build variables change the build: `SITE_PUBLIC=1` lets search engines list the site (the
default asks them not to), and `DATAGOVGR_BASE_URL` sets another address for the portal.

The Worker keeps no logs and no traces (`observability` in `wrangler.jsonc`), because a request
of the second reading carries the key of a visitor in its body.

## Third-party components

| Component | Version | Licence | Source |
| --- | --- | --- | --- |
| Pyodide | 314.0.8 | MPL-2.0 | https://github.com/pyodide/pyodide |
| openpyxl | 3.1.5 | MIT | https://foss.heptapod.net/openpyxl/openpyxl |
| et_xmlfile | 2.0.0 | MIT | https://foss.heptapod.net/openpyxl/et_xmlfile |
| Manrope | files of @fontsource-variable/manrope 5.3.0 | OFL-1.1 | https://github.com/sharanda/manrope |
| Lucide icons | 1.74.0 | ISC | https://lucide.dev |

Pyodide and the two libraries are fetched at build time and are not part of the repository.

The page calls two outside services, and only when a visitor asks: the catalogue of data.gov.gr
for the metadata of a dataset, and the model Jev of TypeSafe AI (api.typesafe.ai) for a second
reading.

## Limits

- The relays have no rate limit of their own.
- The second opinion is not part of the downloaded reports.
- The model of the second opinion is trained mainly on English; it was tried on the Greek
  descriptions of the 36 datasets of the sample (`DECISIONS.md` #54).
- The plain-language texts follow the wording of the reasons of `scripts/04_metadata_checks.py`;
  the tests of `tests/test_plain_language.py` show a change of that wording.
- A change of the rules in `criteria/criteria.csv` makes `tests/test_criteria_texts.py` fail until
  the copy of the rules in `aiready/locales/en.json` is updated; the Greek translation of the
  changed rules has to be written again at the same time.
