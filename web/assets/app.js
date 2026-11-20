/* Script of the public page.
   Reads the address typed in the form, asks the catalogue of data.gov.gr for the metadata of the
   dataset and runs the checks of the study inside the browser, with the Python files of the
   repository. Nothing is stored. Nothing is sent anywhere but to the portal, with one exception:
   when the visitor asks for the second opinion on the description, the texts of the description
   and the key that the visitor typed go to the relay of the site, which passes them to the model.
   A result has three tabs; the address of the page keeps the name of the open tab after the #. */

const settings = document.body.dataset;
const region = document.getElementById("result");
const form = document.getElementById("check-form");
const field = document.getElementById("dataset-address");
const pageTitle = document.title;

const PORTAL_TIMEOUT = 20000;   // milliseconds to wait for the portal, or for the relay of the site
const READING_TIMEOUT = 45000;  // milliseconds to wait for the second reading, longer than the relay waits for the model
const FIELDS_TIMEOUT = 20000;   // milliseconds to wait for the columns of the tables, longer than the relay waits for the portal
const KEY_SHAPE = /^[\x21-\x7e]{8,300}$/;   // a key as the relay of the site accepts it: no space inside, 8 to 300 characters
const EXCEL_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
const TEXT_TYPES = { md: "text/markdown;charset=utf-8", json: "application/json" };
const OPINION_TAB = "second-opinion";
const TAB_KEYS = { ArrowRight: 1, ArrowLeft: -1, Home: "first", End: "last" };

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

/* The checks with the dataset of the page as the last one that was assessed. The example is shown
   from the build, so it is assessed here the first time that a report or a reading asks for it. */
async function assessedChecks(state) {
  const checks = await loadedEngine();
  if (state.example && !state.assessed) {
    const record = await fetched(settings.exampleRecord);
    checks.browser.assess_example(await record.text(), settings.language, settings.exampleDate);
    state.assessed = true;
  }
  return checks;
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

function tabs() {
  return [...region.querySelectorAll('.tab[role="tab"]')];
}

function tabName(tab) {
  return tab.getAttribute("href").slice(1);
}

function panelOf(tab) {
  return document.getElementById(tab.getAttribute("aria-controls"));
}

/* Distance of an element from the top of the page, as the page is laid out. The position that the browser
   reports for an element moves with the animation of a result that has just arrived; this one does not. */
function pageTop(element) {
  let top = 0;
  for (let node = element; node; node = node.offsetParent) {
    top += node.offsetTop;
  }
  return top;
}

/* Scrolls the page to the start of the open panel: the bar of the tabs at the top of the window and the
   panel right under it. Without this, a tab opened from far down a long panel would show the middle of
   the new panel, and a tab opened from the top of the page would show nothing of it. */
function revealPanel() {
  const bar = region.querySelector(".result-bar");
  const panel = region.querySelector('[role="tabpanel"]:not([hidden])');
  if (!bar || !panel) {
    return;
  }
  const gap = parseFloat(getComputedStyle(panel).marginTop) || 0;
  window.scrollTo({ top: Math.max(0, Math.round(pageTop(panel) - gap - bar.offsetHeight)) });
}

/* Opens a tab and hides the panels of the others. */
function openTab(chosen) {
  for (const tab of tabs()) {
    const selected = tab === chosen;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    panelOf(tab).hidden = !selected;
  }
}

/* Opens the tab with the name, moves the focus to it and shows the start of its panel. Unless the address
   of the page already names the tab, the name is written in the address without a new entry in the
   history. Returns false when no tab has the name. */
function chooseTab(name, writeAddress = true) {
  const chosen = tabs().find((tab) => tabName(tab) === name);
  if (!chosen) {
    return false;
  }
  openTab(chosen);
  if (writeAddress) {
    history.replaceState(null, "", `${location.pathname}${location.search}#${name}`);
  }
  carryQuery();
  chosen.focus({ preventScroll: true });
  revealPanel();
  return true;
}

/* Follows the part of the address after the #: the name of a tab, or a place inside the panel of a tab. */
function showHash() {
  if (!shown) {
    return;
  }
  let name = "";
  try {
    name = decodeURIComponent(location.hash.slice(1));
  } catch (error) {
    name = "";
  }
  const all = tabs();
  carryQuery();
  if (!name) {
    if (all.length) {
      openTab(all[0]);
    }
    return;
  }
  if (chooseTab(name, false)) {
    return;
  }
  const target = document.getElementById(name);
  if (!target || !region.contains(target)) {
    return;
  }
  const hiddenIn = all.find((tab) => panelOf(tab).hidden && panelOf(tab).contains(target));
  if (hiddenIn) {
    openTab(hiddenIn);
  }
  target.scrollIntoView();
}

/* The region of the result announces what arrives in it, which suits the progress of a check and its
   failures. Once a result stands in it the announcements stop: the focus goes to the name of the dataset
   instead, and a screen reader is not read a whole panel every time a tab opens. */
function announceArrivals(announced) {
  region.setAttribute("aria-live", announced ? "polite" : "off");
}

/* Common end of showing a result: the top of the page, the focus on the name of the dataset, and the tab
   that the address of the page names. */
function settleResult(title) {
  document.title = `${title} | ${pageTitle}`;
  window.scrollTo(0, 0);
  const heading = region.querySelector("h1");
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
  showHash();
}

function showResult(html, title) {
  announceArrivals(false);
  region.innerHTML = html;
  settleResult(title);
}

async function check(text) {
  latestRun += 1;
  const run = latestRun;
  shown = null;
  document.body.dataset.view = "result";
  document.title = pageTitle;
  window.scrollTo(0, 0);
  announceArrivals(true);
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
  announceArrivals(false);
  region.replaceChildren(template("example-result"));
  settleResult(region.querySelector("h1").textContent);
}

function showHome() {
  latestRun += 1;
  shown = null;
  delete document.body.dataset.view;
  announceArrivals(true);
  region.replaceChildren();
  document.title = pageTitle;
}

/* The links of the language switch keep the dataset that is on the page and the tab that is open. */
function carryQuery() {
  for (const link of document.querySelectorAll(".language a")) {
    link.href = new URL(link.href).pathname + location.search + location.hash;
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
    const checks = await assessedChecks(state);
    if (state !== shown) {
      return;
    }
    const format = button.dataset.format;
    const file = await reportFile(checks, format);
    status.textContent = "";
    closeReportMenu(true);
    saveFile(file, checks.browser.report_name(format));
  } catch (error) {
    status.classList.add("is-error");
    status.textContent = buttons.dataset.failed;
  } finally {
    button.disabled = false;
  }
}

/* Puts the reading in the place of the offer, marks its tab as answered and moves the focus to its heading. */
function showReading(offer, html) {
  const holder = document.createElement("template");
  holder.innerHTML = html;
  const reading = holder.content.firstElementChild;
  offer.replaceWith(reading);
  const tab = tabs().find((candidate) => tabName(candidate) === OPINION_TAB);
  if (tab) {
    tab.dataset.answered = "";
  }
  reading.querySelector("h3").focus();
}

function closeReportMenu(focusBack) {
  const menu = region.querySelector(".report-menu[open]");
  if (menu) {
    menu.open = false;
    if (focusBack) {
      menu.querySelector("summary").focus();
    }
  }
}

/* Names of the columns of up to three tables of the dataset in the DataStore of the portal, as the relay of
   the site returns them, or an empty text when the dataset has no such table or the relay does not answer.
   Only the structure of the tables comes back, never a row. */
async function tableColumns(checks) {
  const tables = JSON.parse(checks.browser.field_request());
  if (!tables.length) {
    return "";
  }
  const query = tables.map((table) => `resource=${encodeURIComponent(table)}`).join("&");
  try {
    const reply = await fetch(`${settings.fields}?${query}`, { cache: "no-store", signal: AbortSignal.timeout(FIELDS_TIMEOUT) });
    return reply.ok ? await reply.text() : "";
  } catch (error) {
    return "";
  }
}

/* Second reading of the description of the dataset on the page. The key that the visitor typed is
   sent once, in the body of the request to the relay of the site, and is stored nowhere. The
   messages of the form are data attributes written by the build. */
async function readDescription(readingForm) {
  const state = shown;
  const offer = readingForm.closest(".reading");
  const status = offer.querySelector(".reading-status");
  const button = readingForm.querySelector("button");
  const keyField = readingForm.elements.key;
  const key = keyField.value.trim();
  const report = (message, failed) => {
    status.classList.toggle("is-error", failed);
    status.textContent = message;
  };
  const refuseKey = (message) => {
    report(message, true);
    keyField.setAttribute("aria-invalid", "true");
    keyField.focus();
    keyField.select();
  };
  keyField.removeAttribute("aria-invalid");
  if (!KEY_SHAPE.test(key)) {
    refuseKey(readingForm.dataset[key ? "key" : "keyMissing"]);
    return;
  }
  button.disabled = true;
  report(readingForm.dataset.waiting, false);
  let failure = "engine";
  try {
    const checks = await assessedChecks(state);
    if (state !== shown) {
      return;
    }
    const columns = await tableColumns(checks);
    if (state !== shown) {
      return;
    }
    const request = JSON.parse(checks.browser.reading_request(columns));
    failure = "service";
    const reply = await fetch(settings.reading, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, request }),
      cache: "no-store",
      signal: AbortSignal.timeout(READING_TIMEOUT),
    });
    if (state !== shown) {
      return;
    }
    if (reply.status === 401) {
      refuseKey(readingForm.dataset.key);
      return;
    }
    if (reply.status === 429) {
      report(readingForm.dataset.limit, true);
      return;
    }
    if (!reply.ok) {
      throw new Error(`HTTP ${reply.status}`);
    }
    const text = await reply.text();
    if (state !== shown) {
      return;
    }
    const answer = JSON.parse(checks.browser.reading_result(text, settings.language, today()));
    if (!answer.ok) {
      throw new Error(answer.code);
    }
    showReading(offer, answer.html);
  } catch (error) {
    if (state === shown) {
      report(readingForm.dataset[failure], true);
    }
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
    if (!event.target.closest(".report-menu")) {
      closeReportMenu(false);
    }
    if (event.target.closest("a[data-example]")) {
      event.preventDefault();
      goTo("?example=1");
      return;
    }
    const link = event.target.closest('a[href^="#"]');
    if (link && shown && region.contains(link) && chooseTab(link.getAttribute("href").slice(1))) {
      event.preventDefault();
      return;
    }
    if (event.target.closest("a[data-opinion-link]") && shown && chooseTab(OPINION_TAB)) {
      event.preventDefault();
      return;
    }
    const button = event.target.closest("button[data-format]");
    if (button && shown) {
      downloadReport(button);
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeReportMenu(true);
    }
  });
  region.addEventListener("keydown", (event) => {
    const tab = event.target.closest('.tab[role="tab"]');
    if (!tab) {
      return;
    }
    if (event.key === " ") {
      event.preventDefault();
      chooseTab(tabName(tab));
      return;
    }
    const move = TAB_KEYS[event.key];
    if (move === undefined) {
      return;
    }
    event.preventDefault();
    const all = tabs();
    const places = { first: 0, last: all.length - 1 };
    const place = move in places ? places[move] : (all.indexOf(tab) + move + all.length) % all.length;
    chooseTab(tabName(all[place]));
  });
  window.addEventListener("hashchange", showHash);
  /* The menu of the report opens under its button, which may stand at the bottom of the window. */
  region.addEventListener("toggle", (event) => {
    if (event.target.matches(".report-menu") && event.target.open) {
      event.target.querySelector(".report-menu-box").scrollIntoView({ block: "nearest" });
    }
  }, true);
  region.addEventListener("submit", (event) => {
    const readingForm = event.target.closest("#reading-form");
    if (readingForm) {
      event.preventDefault();
      if (shown) {
        readDescription(readingForm);
      }
    }
  });
  window.addEventListener("popstate", () => {
    if (location.search !== shownSearch) {
      showAddress();
    }
  });
  showAddress();
}

/* Page of the criteria. Every criterion is a card whose rules open under it: a click anywhere on the card opens
   or closes it, the button above the cards opens or closes them all, an address with the code of a criterion
   after the # opens its card, and on paper every card is printed open. Without this script the cards still open
   from the line of their rules, and the button stays hidden. */

const criterionCards = Array.from(document.querySelectorAll(".criterion-more"));
const toggleAll = document.querySelector("[data-toggle-all]");

function showToggleState() {
  const allOpen = criterionCards.every((card) => card.open);
  toggleAll.setAttribute("aria-expanded", String(allOpen));
  toggleAll.querySelector("span").textContent = allOpen ? toggleAll.dataset.closeLabel : toggleAll.dataset.openLabel;
}

function openCriterionOfAddress() {
  let name = "";
  try {
    name = decodeURIComponent(location.hash.slice(1));
  } catch (error) {
    return;
  }
  const section = name ? document.getElementById(name) : null;
  if (section && section.classList.contains("criterion")) {
    section.querySelector(".criterion-more").open = true;
    section.scrollIntoView({ block: "start" });
  }
}

if (criterionCards.length && toggleAll) {
  let closedBeforePrint = [];
  toggleAll.hidden = false;
  toggleAll.addEventListener("click", () => {
    const openThem = !criterionCards.every((card) => card.open);
    criterionCards.forEach((card) => { card.open = openThem; });
    showToggleState();
  });
  document.addEventListener("toggle", (event) => {
    if (event.target.matches(".criterion-more")) {
      showToggleState();
    }
  }, true);
  document.addEventListener("click", (event) => {
    const section = event.target.closest(".criterion");
    if (!section || event.target.closest("a, button, summary, .criterion-body") || String(window.getSelection())) {
      return;
    }
    const card = section.querySelector(".criterion-more");
    card.open = !card.open;
  });
  window.addEventListener("hashchange", openCriterionOfAddress);
  window.addEventListener("beforeprint", () => {
    closedBeforePrint = criterionCards.filter((card) => !card.open);
    closedBeforePrint.forEach((card) => { card.open = true; });
  });
  window.addEventListener("afterprint", () => {
    closedBeforePrint.forEach((card) => { card.open = false; });
    closedBeforePrint = [];
  });
  openCriterionOfAddress();
  showToggleState();
}
