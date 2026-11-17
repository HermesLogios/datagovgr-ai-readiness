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

## Files

| File | Purpose |
| --- | --- |
| `build.py` | builds the site into `web/dist` |
| `preview.py` | builds the site and serves it on this computer, relay included |
| `pages.py` | HTML of the home page, the result, the guide and the terms |
| `icons.py` | status icons, line icons and the mark of the tool as inline SVG |
| `browser.py` | entry points that the page calls inside the browser |
| `shims/pandas.py` | reader of CSV tables that stands in for pandas inside the browser |
| `assets/` | stylesheet, script, typeface and licence texts |
| `example/` | catalogue record of the example, without contact details |
| `functions/api/record.js` | relay to the catalogue, run by Cloudflare Pages |

## Commands

```
python web/build.py
python web/preview.py
python -m unittest discover -s tests
node --test tests/js/record_relay.test.mjs
```

`preview.py` serves the site at http://localhost:8788. The build needs only the standard
library of Python; the preview and the tests need the packages of `requirements.txt`.

## Publishing on Cloudflare Pages

Settings of the Pages project, with the repository connected through the Git integration:

| Setting | Value |
| --- | --- |
| Root directory | `web` |
| Build command | `python3 build.py` |
| Build output directory | `dist` |

Every push to the production branch builds and publishes the site. Two environment variables
change the build: `SITE_PUBLIC=1` lets search engines list the site (the default asks them not
to), and `DATAGOVGR_BASE_URL` sets another address for the portal.

## Third-party components

| Component | Version | Licence | Source |
| --- | --- | --- | --- |
| Pyodide | 314.0.8 | MPL-2.0 | https://github.com/pyodide/pyodide |
| openpyxl | 3.1.5 | MIT | https://foss.heptapod.net/openpyxl/openpyxl |
| et_xmlfile | 2.0.0 | MIT | https://foss.heptapod.net/openpyxl/et_xmlfile |
| Manrope | files of @fontsource-variable/manrope 5.3.0 | OFL-1.1 | https://github.com/sharanda/manrope |
| Lucide icons | 1.74.0 | ISC | https://lucide.dev |

Pyodide and the two libraries are fetched at build time and are not part of the repository.

## Limits

- The relay has no rate limit of its own.
- The plain-language texts follow the wording of the reasons of `scripts/04_metadata_checks.py`;
  the tests of `tests/test_plain_language.py` show a change of that wording.
