/* Helpers of the search of the catalogue by words: what names one dataset and what is words to search for,
   the question to the relay of the site, and the reading of its reply. Nothing here touches the page. */

const DATASET_NAME = /^[a-z0-9]+(?:[-_][a-z0-9]+)+$/;   // the name of a dataset in the portal, such as troxaia-atyxhmata
const IDENTIFIER = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const LINK = /^(?:https?:\/\/)?(?:[a-z0-9-]+\.)*data\.gov\.gr\//i;

export const SUGGESTIONS = 8;   // datasets proposed under the field while the visitor types
export const RESULTS = 20;      // datasets listed after the visitor sends words
export const MIN_LETTERS = 3;   // characters typed before suggestions are asked for

/* Whether a text names one dataset: a link, the name of a dataset or its identifier. Anything else is words
   to search for in the catalogue. */
export function namesDataset(text) {
  const value = text.trim();
  return /^https?:\/\//i.test(value) || LINK.test(value) || DATASET_NAME.test(value) || IDENTIFIER.test(value);
}

export function wantsSuggestions(text) {
  const value = text.trim();
  return value.length >= MIN_LETTERS && !namesDataset(value);
}

export function searchAddress(relay, words, rows) {
  return `${relay}?q=${encodeURIComponent(words.trim())}&rows=${rows}`;
}

/* Datasets of a reply of the relay, each with its name, title, publisher, day of the last change and number of
   files; null when the text is not such a reply. */
export function foundDatasets(text) {
  let reply;
  try {
    reply = JSON.parse(text);
  } catch (error) {
    return null;
  }
  if (!reply || typeof reply !== "object" || !Number.isInteger(reply.count) || !Array.isArray(reply.results)) {
    return null;
  }
  const results = reply.results
    .filter((item) => item && typeof item.name === "string" && typeof item.title === "string")
    .map((item) => ({
      name: item.name,
      title: item.title,
      organization: typeof item.organization === "string" ? item.organization : "",
      modified: typeof item.modified === "string" ? item.modified : "",
      resources: Number.isInteger(item.resources) ? item.resources : 0,
    }));
  return { count: reply.count, results };
}
