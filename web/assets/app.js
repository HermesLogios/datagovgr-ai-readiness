/* Script of the public page.
   Reads the address typed in the form, asks the catalogue of data.gov.gr for the metadata of the
   dataset and runs the checks of the study inside the browser, with the Python files of the
   repository. Nothing is stored and nothing is sent anywhere but to the portal. */

const settings = document.body.dataset;
const region = document.getElementById("result");
const form = document.getElementById("check-form");
const field = document.getElementById("dataset-address");
const pageTitle = document.title;

const PORTAL_TIMEOUT = 20000;   // milliseconds to wait for the portal, or for the relay of the site
const EXCEL_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
const TEXT_TYPES = { md: "text/markdown;charset=utf-8", json: "application/json" };

let engine = null;         // promise of the Python runtime with the checks loaded
let engineLoaded = false;
let excelLibrary = null;   // promise of the library of the Excel report
let directCalls = true;    // false once the browser was refused a direct call to the portal
let latestRun = 0;         // number of the latest check, so that a late answer never replaces a newer one
let shown = null;          // the result on the page: { example, assessed }, or null when there is none
let shownSearch = null;    // query of the address that the page shows

function template(name) {
  return document.getElementById(name).content.cloneNode(true);
}

function today() {
  const now = new Date();
  const two = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())}`;
}

async function fetched(address, options = {}) {
  const reply = await fetch(address, options);
  if (!reply.ok) {
    throw new Error(`${address}: HTTP ${reply.status}`);
  }
  return reply;
}

async function startEngine() {
  const { loadPyodide } = await import(`${settings.engine}pyodide.mjs`);
  const pyodide = await loadPyodide({ indexURL: settings.engine });
  const bundle = await fetched(settings.checks);
  pyodide.unpackArchive(await bundle.arrayBuffer(), "zip", { extractDir: "/app" });
  pyodide.runPython('import sys\nsys.path[:0] = ["/app/web/shims", "/app"]\nfrom web import browser');
  engineLoaded = true;
  return { pyodide, browser: pyodide.globals.get("browser") };
}

function loadedEngine() {
  if (!engine) {
    engine = startEngine().catch((error) => {
      engine = null;
      throw error;
    });
  }
  return engine;
}

function loadedExcelLibrary(checks) {
  if (!excelLibrary) {
    excelLibrary = (async () => {
      const bundle = await fetched(settings.excel);
      checks.pyodide.unpackArchive(await bundle.arrayBuffer(), "zip", { extractDir: "/app/excel" });
      checks.pyodide.runPython('import importlib, sys\nsys.path.append("/app/excel")\nimportlib.invalidate_caches()');
    })().catch((error) => {
      excelLibrary = null;
      throw error;
    });
  }
  return excelLibrary;
}

/* Reply of the catalogue for one dataset, as text. The portal is called directly; when the
   browser is refused, the same question goes through the relay of the site. */
async function portalReply(kind, value) {
  if (directCalls) {
    const query = encodeURIComponent(`${kind}:"${value}"`);
    try {
      const reply = await fetched(`${settings.portal}/api/3/action/package_search?fq=${query}&rows=1`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(PORTAL_TIMEOUT),
      });
      return await reply.text();
    } catch (error) {
      directCalls = !(error instanceof TypeError);
    }
  }
  const reply = await fetched(`${settings.proxy}?${kind}=${encodeURIComponent(value)}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(PORTAL_TIMEOUT + 5000),
  });
  return reply.text();
}

function showResult(html, title) {
  region.innerHTML = html;
  document.title = `${title} | ${pageTitle}`;
  window.scrollTo(0, 0);
  const heading = region.querySelector("h1");
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
}

async function check(text) {
  latestRun += 1;
  const run = latestRun;
  shown = null;
  document.body.dataset.view = "result";
  document.title = pageTitle;
  window.scrollTo(0, 0);
  region.replaceChildren(template(engineLoaded ? "progress-loading" : "progress-preparing"));
  let failure = "error-engine";
  try {
    const checks = await loadedEngine();
    if (run !== latestRun) {
      return;
    }
    const identity = JSON.parse(checks.browser.identify(text, settings.language));
    if (!identity.ok) {
      region.innerHTML = identity.html;
      return;
    }
    region.replaceChildren(template("progress-loading"));
    failure = "error-portal";
    const reply = await portalReply(identity.kind, identity.value);
    if (run !== latestRun) {
      return;
    }
    failure = "error-engine";
    const answer = JSON.parse(checks.browser.assess_reply(reply, identity.value, settings.language, today()));
    if (answer.ok) {
      shown = { example: false, assessed: true };
      showResult(answer.html, answer.title);
    } else {
      region.innerHTML = answer.html;
    }
  } catch (error) {
    if (run === latestRun) {
      region.replaceChildren(template(failure));
    }
  }
}

function showExample() {
  latestRun += 1;
  shown = { example: true, assessed: false };
  document.body.dataset.view = "result";
  field.value = "";
  region.replaceChildren(template("example-result"));
  document.title = `${region.querySelector("h1").textContent} | ${pageTitle}`;
  window.scrollTo(0, 0);
}

function showHome() {
  latestRun += 1;
  shown = null;
  delete document.body.dataset.view;
  region.replaceChildren();
  document.title = pageTitle;
}

/* The links of the language switch keep the dataset that is on the page. */
function carryQuery() {
  for (const link of document.querySelectorAll(".language a")) {
    link.href = new URL(link.href).pathname + location.search;
  }
}

function showAddress() {
  const query = new URLSearchParams(location.search);
  shownSearch = location.search;
  carryQuery();
  if (query.has("example")) {
    showExample();
  } else if (query.has("dataset")) {
    field.value = query.get("dataset");
    check(query.get("dataset"));
  } else {
    showHome();
  }
}

function goTo(search) {
  history.pushState(null, "", search);
  showAddress();
}

function saveFile(blob, name) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 10000);
}

async function reportFile(checks, format) {
  if (format === "xlsx") {
    await loadedExcelLibrary(checks);
    const workbook = checks.browser.report_excel();
    const blob = new Blob([workbook.toJs()], { type: EXCEL_TYPE });
    workbook.destroy();
    return blob;
  }
  return new Blob([checks.browser.report_text(format)], { type: TEXT_TYPES[format] });
}

async function downloadReport(button) {
  const state = shown;
  const buttons = button.closest(".file-buttons");
  const status = buttons.parentElement.querySelector(".file-status");
  button.disabled = true;
  status.classList.remove("is-error");
  status.textContent = buttons.dataset.preparing;
  try {
    const checks = await loadedEngine();
    if (state.example && !state.assessed) {
      const record = await fetched(settings.exampleRecord);
      checks.browser.assess_example(await record.text(), settings.language, settings.exampleDate);
      state.assessed = true;
    }
    if (state !== shown) {
      return;
    }
    const format = button.dataset.format;
    saveFile(await reportFile(checks, format), checks.browser.report_name(format));
    status.textContent = "";
  } catch (error) {
    status.classList.add("is-error");
    status.textContent = buttons.dataset.failed;
  } finally {
    button.disabled = false;
  }
}

if (form && region) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    goTo(`?dataset=${encodeURIComponent(field.value.trim())}`);
  });
  field.addEventListener("focus", () => loadedEngine().catch(() => {}), { once: true });
  document.addEventListener("click", (event) => {
    if (event.target.closest("a[data-example]")) {
      event.preventDefault();
      goTo("?example=1");
      return;
    }
    const button = event.target.closest("button[data-format]");
    if (button && shown) {
      downloadReport(button);
    }
  });
  window.addEventListener("popstate", () => {
    if (location.search !== shownSearch) {
      showAddress();
    }
  });
  showAddress();
}
