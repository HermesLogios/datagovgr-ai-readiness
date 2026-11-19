# Public page of the assessment tool

A static site that checks one dataset of data.gov.gr with the nine metadata checks of the study.
The checks are the Python files of this repository. They run inside the browser of the visitor
with Pyodide, so the scores are those of `scripts/04_metadata_checks.py`.

## How it works

- `build.py` writes the site into `web/dist`: the pages in Greek and English, the Python files
  of the checks packed for the browser, the Python runtime (Pyodide) and the library of the
  Excel report. Each fetched file is checked against a pinned SHA-256 and kept in `web/.cache`.
- `assets/app.js` reads the address typed in the form and asks the catalogue for the record of
  the dataset, with one call to the action `package_search`. The portal is called directly from
  the browser. A browser that is refused asks the relay `functions/api/record.js`, which passes
  the same question to the portal and keeps nothing.
- `browser.py` receives the reply as text and returns the HTML of the result and the reports.
- `pages.py` and `icons.py` produce all HTML. Every text comes from `aiready/locales`.
- The site stores nothing: no cookies, no browser storage, no history of checks.

## Pages and tabs

The site has four pages in each language: the check (`/`), the second opinion
(`/second-opinion/`), the guide (`/guide/`) and the terms (`/terms/`). The English pages stand
under `/en/`.

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

## Version

The footer of every page shows the version of the page and its day, from `release.py`. Both
change with every published change, so the footer of the published site tells whether a change
has arrived.

## Second opinion of a model

In the tab of the second opinion a visitor may ask Jev, a model of TypeSafe AI, to read the
description of the dataset (`DECISIONS.md` #54). The reading is optional and needs a key of the
visitor. It gives no score and changes none.

- `aiready/jev.py` holds the five statements, selects the texts that are sent (the title, the
  description and the descriptions of the resources that say more than a name) and reads the
  reply. `aiready/second_reading.py` turns the probabilities into the rows of the page.
- `browser.py` builds the request for the dataset on the page. `assets/app.js` sends it, with the
  key that the visitor typed, in the body of a POST request to the relay
  `functions/api/reading.js`. The address of the model does not accept calls from a web page.
- The relay accepts only a request of the shape that the page sends, passes it on with the key in
  the Authorization header and returns the reply. Any other field is dropped.
- The key is kept nowhere: the page does not store it, it is never part of an address, the relay
  writes nothing, and `wrangler.jsonc` switches off the logs and the traces of the Worker.
- The model is named by its version (`jev-1.14.0`). `python -m aiready.jev_trial` repeats the
  trial of the model on the 36 datasets of the sample before a new version is adopted.

## Files

| File | Purpose |
| --- | --- |
| `build.py` | builds the site into `web/dist` |
| `preview.py` | builds the site and serves it on this computer, the two relays included |
| `pages.py` | HTML of the home page, the result with its tabs, the page of the second opinion, the guide and the terms |
| `release.py` | version of the page and its day, as the footer shows them |
| `icons.py` | status icons, line icons and the mark of the tool as inline SVG |
| `browser.py` | entry points that the page calls inside the browser |
| `shims/pandas.py` | reader of CSV tables that stands in for pandas inside the browser |
| `assets/` | stylesheet, script, typeface and licence texts |
| `example/` | catalogue record of the example, without contact details |
| `functions/api/record.js` | relay to the catalogue |
| `functions/api/reading.js` | relay to the model of the second opinion |
| `worker.js` | entry of the site on Cloudflare Workers: the two relays, and the files of the build for every other address |
| `wrangler.jsonc` | settings of the Worker: its name, the folder of the build, the entry, and no logs |

## Commands

```
python web/build.py
python web/preview.py
python -m unittest discover -s tests
node --test tests/js/record_relay.test.mjs
node --test tests/js/reading_relay.test.mjs
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
