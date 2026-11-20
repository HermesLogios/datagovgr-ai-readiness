/* Script of the public page.
   Reads what is typed in the form. An address or the name of a dataset is checked: the script asks the
   catalogue of data.gov.gr for the metadata of the dataset and runs the checks of the study inside the
   browser, with the Python files of the repository. Words are searched for in the catalogue, through the
   relay of the site, which returns only the title, publisher, day of the last change and number of files
   of each dataset found. The ten latest checks are kept in the storage of this browser and nowhere else,
   so that they open again as they were, without the contact details that the metadata name; the key of
   the model is never kept. Nothing is sent anywhere but to the portal and the relay of the site, and the
   texts of the description and the key go to the model only when the visitor asks for the second opinion.
   A result has three tabs; the address of the page keeps the name of the open tab after the #. */

import { STORAGE_KEY, changedCheck, readChecks, withCheck, withoutCheck, writeChecks } from "./recent.js";
import { RESULTS, SUGGESTIONS, foundDatasets, namesDataset, searchAddress, wantsSuggestions } from "./search.js";

const settings = document.body.dataset;
const region = document.getElementById("result");
const form = document.getElementById("check-form");
const field = document.getElementById("dataset-address");
const suggestionList = document.getElementById("search-suggestions");
const searchStatus = document.getElementById("search-status");
const recentSection = document.getElementById("recent");
const examplePreview = document.querySelector(".hero-side .preview");
const exampleLink = document.querySelector(".example-prompt a[data-example]");
const pageTitle = document.title;

const PORTAL_TIMEOUT = 20000;   // milliseconds to wait for the portal, or for the relay of the site
const READING_TIMEOUT = 45000;  // milliseconds to wait for the second reading, longer than the relay waits for the model
const FIELDS_TIMEOUT = 20000;   // milliseconds to wait for the columns of the tables, longer than the relay waits for the portal
const KEY_SHAPE = /^[\x21-\x7e]{8,300}$/;   // a key as the relay of the site accepts it: no space inside, 8 to 300 characters
const EXCEL_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
const TEXT_TYPES = { md: "text/markdown;charset=utf-8", json: "application/json" };
const OPINION_TAB = "second-opinion";
const TAB_KEYS = { ArrowRight: 1, ArrowLeft: -1, Home: "first", End: "last" };
const SUGGESTION_DELAY = 300;   // milliseconds of quiet typing before the catalogue is asked for suggestions
const HOME_PATHS = { el: "/", en: "/en/" };
const DATE_STYLES = { el: { day: "numeric", month: "numeric", year: "numeric" }, en: { day: "numeric", month: "long", year: "numeric" } };
const TICKS = 'input[type="checkbox"][id^="tick-"]';

let engine = null;         // promise of the Python runtime with the checks loaded
let engineLoaded = false;
let excelLibrary = null;   // promise of the library of the Excel report
let directCalls = true;    // false once the browser was refused a direct call to the portal
let latestRun = 0;         // number of the latest check, so that a late answer never replaces a newer one
let shown = null;          // the result on the page: { example, assessed, name, stored }, or null when there is none
let shownSearch = null;    // query of the address that the page shows
let suggestionTimer = 0;
let suggestionRun = 0;     // number of the latest question for suggestions, so that a late answer is left unshown
let activeSuggestion = -1; // place of the suggestion chosen with the arrow keys, -1 for none
const suggestionReplies = new Map();   // suggestions already found, by the words typed

/* Storage of the browser for the recent checks; null when the browser refuses it, and then nothing is kept. */
const storage = (() => {
  try {
    const kept = window.localStorage;
    kept.getItem(STORAGE_KEY);
    return kept;
  } catch (error) {
    return null;
  }
})();

function template(name) {
  return document.getElementById(name).content.cloneNode(true);
}

function today() {
  const now = new Date();
  const two = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())}`;
}

function shownNumber(value) {
  return new Intl.NumberFormat(settings.locale).format(value);
}

function shownDate(moment) {
  return new Intl.DateTimeFormat(settings.locale, DATE_STYLES[settings.language] || DATE_STYLES.en).format(moment);
}

function shownTime(moment) {
  return new Intl.DateTimeFormat(settings.locale, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(moment);
}

/* The day of a date of the catalogue, such as 2026-11-03T10:22:31.123456, as the page writes days; empty when
   the text holds no such day. Only the day is read, so the hours and the time zone never move it. */
function catalogueDay(text) {
  const parts = /^(\d{4})-(\d{2})-(\d{2})/.exec(text || "");
  return parts ? shownDate(new Date(Number(parts[1]), Number(parts[2]) - 1, Number(parts[3]))) : "";
}

/* Publisher, day of the last change and number of files of a dataset found in the catalogue, in one line. */
function datasetFacts(item, texts) {
  const facts = [];
  if (item.organization) {
    facts.push(item.organization);
  }
  const day = catalogueDay(item.modified);
  if (day) {
    facts.push(texts.modified.replace("{date}", day));
  }
  facts.push(item.resources === 1 ? texts.filesOne : texts.filesMany.replace("{count}", shownNumber(item.resources)));
  return facts.join(" · ");
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

/* The checks with the dataset of the page as the last one that was assessed. The example is shown from the
   build and a kept check from the storage, so each is assessed here the first time that a report or a
   reading asks for it: a kept check with the reply of the catalogue and the day of its first assessment. */
async function assessedChecks(state) {
  const checks = await loadedEngine();
  if (state.example && !state.assessed) {
    const record = await fetched(settings.exampleRecord);
    checks.browser.assess_example(await record.text(), settings.language, settings.exampleDate);
    state.assessed = true;
  }
  if (state.stored && !state.assessed) {
    const kept = state.stored;
    const answer = JSON.parse(checks.browser.assess_reply(kept.reply, kept.value || kept.name, kept.language, kept.day || today()));
    if (!answer.ok) {
      throw new Error("kept check");
    }
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

/* Recent checks */

function keptChecks() {
  return storage ? readChecks(storage) : [];
}

/* Writes the recent checks and shows them; false when the storage refused them. */
function keepChecks(checks) {
  if (!storage || writeChecks(storage, checks) === null) {
    return false;
  }
  showRecent();
  return true;
}

function keptCheck(name) {
  return keptChecks().find((kept) => kept.name === name || kept.value === name) || null;
}

/* Changes a kept check, when the dataset of the page is one. */
function changeKeptCheck(name, changes) {
  const checks = keptChecks();
  if (checks.some((kept) => kept.name === name)) {
    keepChecks(changedCheck(checks, name, changes));
  }
}

/* The list of the recent checks next to the example, which steps aside once there is a check. Each check opens
   in the language in which it was made. */
function showRecent() {
  if (!recentSection) {
    return;
  }
  const checks = keptChecks();
  const list = recentSection.querySelector(".recent-list");
  const texts = list.dataset;
  list.replaceChildren(...checks.map((kept) => {
    const item = template("recent-item").firstElementChild;
    const link = item.querySelector(".recent-open");
    const query = `?dataset=${encodeURIComponent(kept.name)}&saved=1`;
    const language = HOME_PATHS[kept.language] ? kept.language : settings.language;
    link.href = language === settings.language ? query : `${HOME_PATHS[language]}${query}`;
    link.hreflang = language;
    item.querySelector(".recent-title").textContent = kept.title;
    const facts = [];
    const made = new Date(kept.time);
    if (!Number.isNaN(made.getTime())) {
      facts.push(`${shownDate(made)}, ${shownTime(made)}`);
    }
    const counts = kept.counts || {};
    if (Number.isInteger(counts.met) && Number.isInteger(counts.total)) {
      facts.push(texts.summary.replace("{met}", shownNumber(counts.met)).replace("{total}", shownNumber(counts.total)));
    }
    item.querySelector(".recent-meta").textContent = facts.join(" · ");
    item.querySelector(".recent-badge").hidden = !(kept.reading && typeof kept.reading.html === "string");
    const remove = item.querySelector(".recent-remove");
    remove.dataset.recentRemove = kept.name;
    remove.setAttribute("aria-label", texts.remove.replace("{title}", kept.title));
    return item;
  }));
  recentSection.hidden = checks.length === 0;
  if (examplePreview) {
    examplePreview.hidden = checks.length > 0;
  }
}

/* Removes one check and moves the focus to the next one, or to the example when none is left. */
function removeKeptCheck(button) {
  const before = [...recentSection.querySelectorAll("button[data-recent-remove]")];
  const place = before.indexOf(button);
  if (!keepChecks(withoutCheck(keptChecks(), button.dataset.recentRemove))) {
    return;
  }
  const after = [...recentSection.querySelectorAll("button[data-recent-remove]")];
  if (after.length) {
    after[Math.min(Math.max(place, 0), after.length - 1)].focus();
  } else {
    (exampleLink || field).focus();
  }
}

function clearKeptChecks(button) {
  if (window.confirm(button.dataset.confirm) && keepChecks([])) {
    (exampleLink || field).focus();
  }
}

function keepTicks() {
  if (shown && shown.name) {
    const ticks = {};
    region.querySelectorAll(TICKS).forEach((box) => {
      if (box.checked) {
        ticks[box.id] = true;
      }
    });
    changeKeptCheck(shown.name, { ticks });
  }
}

/* A kept check as it was first shown: the result, the second reading when there was one and the ticks of the
   checklist, under a bar with the time of the check and the way to check the dataset again now. */
function showStored(kept) {
  latestRun += 1;
  shown = { example: false, assessed: false, name: kept.name, stored: kept };
  document.body.dataset.view = "result";
  announceArrivals(false);
  region.innerHTML = kept.html;
  const bar = template("stored-bar").firstElementChild;
  const made = new Date(kept.time);
  const text = bar.querySelector(".stored-text");
  text.textContent = text.dataset.text.replace("{date}", shownDate(made)).replace("{time}", shownTime(made));
  bar.querySelector(".stored-again").href = `?dataset=${encodeURIComponent(kept.name)}`;
  region.prepend(bar);
  const offer = region.querySelector(".reading");
  if (offer && kept.reading && typeof kept.reading.html === "string") {
    placeReading(offer, kept.reading.html);
  }
  for (const [id, ticked] of Object.entries(kept.ticks || {})) {
    const box = document.getElementById(id);
    if (box && region.contains(box) && box.matches(TICKS)) {
      box.checked = Boolean(ticked);
    }
  }
  settleResult(kept.title);
}

/* Search of the catalogue by words */

function suggestionOptions() {
  return suggestionList ? [...suggestionList.querySelectorAll('[role="option"]')] : [];
}

function markSuggestion(place) {
  const options = suggestionOptions();
  activeSuggestion = place;
  options.forEach((option, index) => option.setAttribute("aria-selected", String(index === place)));
  if (place >= 0) {
    field.setAttribute("aria-activedescendant", options[place].id);
    options[place].scrollIntoView({ block: "nearest" });
  } else {
    field.removeAttribute("aria-activedescendant");
  }
}

function closeSuggestions() {
  if (!suggestionList) {
    return;
  }
  suggestionRun += 1;
  clearTimeout(suggestionTimer);
  suggestionList.hidden = true;
  suggestionList.replaceChildren();
  field.setAttribute("aria-expanded", "false");
  markSuggestion(-1);
}

/* Shows the datasets found for the words under the field, while the field still holds those words and the focus. */
function showSuggestions(words, found) {
  if (field.value.trim() !== words || document.activeElement !== field) {
    return;
  }
  const texts = suggestionList.dataset;
  suggestionList.replaceChildren(...found.results.map((item, index) => {
    const option = template("suggestion-item").firstElementChild;
    option.id = `suggestion-${index}`;
    option.dataset.name = item.name;
    option.querySelector(".suggestion-title").textContent = item.title;
    option.querySelector(".suggestion-meta").textContent = datasetFacts(item, texts);
    return option;
  }));
  const count = found.results.length;
  searchStatus.textContent = count === 0 ? texts.statusNone
    : count === 1 ? texts.statusOne : texts.statusMany.replace("{count}", shownNumber(count));
  suggestionList.hidden = count === 0;
  field.setAttribute("aria-expanded", String(count > 0));
  markSuggestion(-1);
}

/* Asks the catalogue for the datasets that match the words. A failure stays silent: the visitor can still send
   the words and see the full list, or its failure, on the page. */
async function suggest(words) {
  suggestionRun += 1;
  const run = suggestionRun;
  let found = suggestionReplies.get(words);
  if (!found) {
    try {
      const reply = await fetched(searchAddress(settings.proxy, words, SUGGESTIONS), { signal: AbortSignal.timeout(PORTAL_TIMEOUT) });
      found = foundDatasets(await reply.text());
    } catch (error) {
      found = null;
    }
    if (!found) {
      return;
    }
    suggestionReplies.set(words, found);
  }
  if (run === suggestionRun) {
    showSuggestions(words, found);
  }
}

function chooseSuggestion(option) {
  const name = option.dataset.name;
  closeSuggestions();
  goTo(`?dataset=${encodeURIComponent(name)}`);
}

/* The datasets of the catalogue that match the words, as a list of links that check each one. */
async function showSearch(words) {
  latestRun += 1;
  const run = latestRun;
  shown = null;
  document.body.dataset.view = "result";
  document.title = pageTitle;
  window.scrollTo(0, 0);
  announceArrivals(true);
  region.replaceChildren(template("search-loading"));
  let found = null;
  try {
    const reply = await fetch(searchAddress(settings.proxy, words, RESULTS), {
      signal: AbortSignal.timeout(PORTAL_TIMEOUT + 5000),
    });
    if (reply.status === 400) {
      found = { count: 0, results: [] };
    } else if (reply.ok) {
      found = foundDatasets(await reply.text());
    }
  } catch (error) {
    found = null;
  }
  if (run !== latestRun) {
    return;
  }
  const listing = template("search-list").firstElementChild;
  const texts = listing.dataset;
  const title = texts.title.replace("{query}", words);
  const heading = listing.querySelector("h2");
  const summary = listing.querySelector(".search-count");
  const list = listing.querySelector(".search-list");
  heading.textContent = title;
  document.title = `${title} | ${pageTitle}`;
  if (!found) {
    summary.textContent = texts.error;
    summary.classList.add("is-error");
    list.remove();
    region.replaceChildren(listing);
    return;
  }
  if (found.count === 0 || !found.results.length) {
    summary.textContent = texts.none.replace("{query}", words);
  } else if (found.count === 1) {
    summary.textContent = texts.countOne;
  } else if (found.count <= found.results.length) {
    summary.textContent = texts.countAll.replace("{count}", shownNumber(found.count));
  } else {
    summary.textContent = texts.countSome.replace("{count}", shownNumber(found.count)).replace("{shown}", shownNumber(found.results.length));
  }
  list.replaceChildren(...found.results.map((item) => {
    const entry = template("search-item").firstElementChild;
    const link = entry.querySelector(".search-link");
    link.href = `?dataset=${encodeURIComponent(item.name)}${location.hash}`;
    link.textContent = item.title;
    entry.querySelector(".search-meta").textContent = datasetFacts(item, texts);
    return entry;
  }));
  if (!found.results.length) {
    list.remove();
  }
  announceArrivals(false);
  region.replaceChildren(listing);
  heading.focus({ preventScroll: true });
}

/* Checks */

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
    const day = today();
    const answer = JSON.parse(checks.browser.assess_reply(reply, identity.value, settings.language, day));
    if (answer.ok) {
      shown = { example: false, assessed: true, name: answer.name };
      showResult(answer.html, answer.title);
      keepChecks(withCheck(keptChecks(), {
        name: answer.name, title: answer.title, language: settings.language, value: identity.value, day,
        time: new Date().toISOString(), version: settings.version, counts: answer.counts, reply: answer.kept, html: answer.html,
        reading: null, ticks: {},
      }));
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

/* Shows what the address of the page asks for: the example, words to search for, a dataset to check, or a kept
   check. Words that arrive as a dataset, from the form of another page, become a search; the tab named after
   the # stays in the address, and the datasets found open at that tab. */
function showAddress() {
  const query = new URLSearchParams(location.search);
  closeSuggestions();
  if (query.has("dataset")) {
    const words = query.get("dataset").trim();
    if (words && !namesDataset(words)) {
      history.replaceState(null, "", `?search=${encodeURIComponent(words)}${location.hash}`);
      query.set("search", words);
      query.delete("dataset");
    }
  }
  shownSearch = location.search;
  carryQuery();
  if (query.has("example")) {
    showExample();
  } else if (query.has("search")) {
    field.value = query.get("search");
    showSearch(query.get("search").trim());
  } else if (query.has("dataset")) {
    const value = query.get("dataset");
    const kept = query.has("saved") ? keptCheck(value.trim()) : null;
    field.value = value;
    if (kept && kept.language === settings.language) {
      showStored(kept);
    } else {
      check(value);
    }
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

/* Puts the reading in the place of the offer and marks its tab as answered. */
function placeReading(offer, html) {
  const holder = document.createElement("template");
  holder.innerHTML = html;
  const reading = holder.content.firstElementChild;
  offer.replaceWith(reading);
  const tab = tabs().find((candidate) => tabName(candidate) === OPINION_TAB);
  if (tab) {
    tab.dataset.answered = "";
  }
  return reading;
}

function showReading(offer, html) {
  placeReading(offer, html).querySelector("h3").focus();
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
    if (state.name) {
      changeKeptCheck(state.name, { reading: { html: answer.html } });
    }
  } catch (error) {
    if (state === shown) {
      report(readingForm.dataset[failure], true);
    }
  } finally {
    button.disabled = false;
  }
}

/* Whether a click on a link is a plain one, which the page may follow itself; a click with a key held or with
   another button opens the link as the browser does. */
function plainClick(event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
}

if (form && region) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = field.value.trim();
    closeSuggestions();
    goTo(text && !namesDataset(text) ? `?search=${encodeURIComponent(text)}` : `?dataset=${encodeURIComponent(text)}`);
  });
  field.addEventListener("focus", () => loadedEngine().catch(() => {}), { once: true });
  if (suggestionList) {
    field.addEventListener("input", () => {
      clearTimeout(suggestionTimer);
      const words = field.value.trim();
      if (!wantsSuggestions(words)) {
        closeSuggestions();
        return;
      }
      suggestionTimer = setTimeout(() => suggest(words), SUGGESTION_DELAY);
    });
    field.addEventListener("keydown", (event) => {
      const options = suggestionOptions();
      if (suggestionList.hidden || !options.length) {
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        let place = activeSuggestion + (event.key === "ArrowDown" ? 1 : -1);
        if (place < -1) {
          place = options.length - 1;
        } else if (place >= options.length) {
          place = -1;
        }
        markSuggestion(place);
      } else if (event.key === "Enter" && activeSuggestion >= 0) {
        event.preventDefault();
        chooseSuggestion(options[activeSuggestion]);
      } else if (event.key === "Escape") {
        event.preventDefault();
        closeSuggestions();
      }
    });
    /* A press on a suggestion keeps the focus in the field, so that the list is still there when the click lands. */
    suggestionList.addEventListener("mousedown", (event) => event.preventDefault());
    suggestionList.addEventListener("click", (event) => {
      const option = event.target.closest('[role="option"]');
      if (option) {
        chooseSuggestion(option);
      }
    });
    field.addEventListener("blur", () => setTimeout(() => {
      if (document.activeElement !== field) {
        closeSuggestions();
      }
    }, 150));
    /* A press anywhere outside the form closes the suggestions, also on phones, where the field may keep the focus. */
    document.addEventListener("pointerdown", (event) => {
      if (!suggestionList.hidden && !form.contains(event.target)) {
        closeSuggestions();
      }
    });
  }
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".report-menu")) {
      closeReportMenu(false);
    }
    if (event.target.closest("a[data-example]")) {
      event.preventDefault();
      goTo("?example=1");
      return;
    }
    const remove = event.target.closest("button[data-recent-remove]");
    if (remove) {
      removeKeptCheck(remove);
      return;
    }
    const clear = event.target.closest("button[data-recent-clear]");
    if (clear) {
      clearKeptChecks(clear);
      return;
    }
    const pageLink = event.target.closest("a[data-goto]");
    if (pageLink && plainClick(event)) {
      const target = new URL(pageLink.href);
      if (target.origin === location.origin && target.pathname === location.pathname) {
        event.preventDefault();
        goTo(target.search + target.hash);
        return;
      }
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
  region.addEventListener("change", (event) => {
    if (event.target.matches(TICKS)) {
      keepTicks();
    }
  });
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY || event.key === null) {
      showRecent();
    }
  });
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
  showRecent();
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
