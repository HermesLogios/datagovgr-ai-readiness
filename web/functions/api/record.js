/* Relay of the public page to the catalogue of data.gov.gr.
   A browser that is refused a direct call to the portal asks here for the record of one dataset, and the
   search of the page by words always comes here. The relay accepts one dataset name or identifier, or a few
   words with the number of datasets wanted; it builds the address of the portal itself and passes the reply on
   without keeping it. For a search it passes on only the name, the title, the publisher, the day of the last
   change and the number of files of each dataset. */

const PORTAL = "https://data.gov.gr";
const USER_AGENT = "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)";
const NAME = /^[a-z0-9_-]{2,100}$/;
const IDENTIFIER = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SEARCH_SIGNS = /[+!(){}[\]^"~*?:\\/&|]/g;   // signs of the search language of the portal, left out of the words
const MIN_WORDS = 2;           // characters of a search, before and after the signs are left out
const MAX_WORDS = 100;
const MAX_ROWS = 20;           // datasets that one search may ask for
const DEFAULT_ROWS = 8;
const TIMEOUT = 20000;         // milliseconds to wait for the portal
const HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

function answer(body, status) {
  return new Response(body, { status, headers: HEADERS });
}

/* Filter of the catalogue search for a request, or null unless the request names one dataset. */
function catalogueFilter(query) {
  const names = query.getAll("name");
  const identifiers = query.getAll("id");
  if (names.length === 1 && identifiers.length === 0 && NAME.test(names[0])) {
    return `name:"${names[0]}"`;
  }
  if (identifiers.length === 1 && names.length === 0 && IDENTIFIER.test(identifiers[0])) {
    return `id:"${identifiers[0]}"`;
  }
  return null;
}

/* Words and number of datasets of a search, or null unless the request is a search and nothing else. */
function searchRequest(query) {
  const words = query.getAll("q");
  const rows = query.getAll("rows");
  if (words.length !== 1 || rows.length > 1 || query.has("name") || query.has("id") || words[0].length > MAX_WORDS) {
    return null;
  }
  const text = words[0].replace(SEARCH_SIGNS, " ").replace(/\s+/g, " ").trim();
  const count = rows.length ? Number(rows[0]) : DEFAULT_ROWS;
  if (text.length < MIN_WORDS || !Number.isInteger(count) || count < 1 || count > MAX_ROWS) {
    return null;
  }
  return { text, count };
}

/* A title of the portal, which may be given in more than one language. */
function plainTitle(value) {
  if (typeof value === "string") {
    return value;
  }
  if (value && typeof value === "object") {
    const found = [value.el, value.en, ...Object.values(value)].find((text) => typeof text === "string" && text);
    return found || "";
  }
  return "";
}

/* The datasets of a reply of the search, each with the five facts that the list of the page shows. */
function foundDatasets(reply) {
  const result = reply && reply.success === true ? reply.result : null;
  if (!result || !Array.isArray(result.results)) {
    return null;
  }
  const results = result.results
    .filter((item) => item && typeof item.name === "string")
    .map((item) => ({
      name: item.name,
      title: plainTitle(item.title) || item.name,
      organization: item.organization ? plainTitle(item.organization.title) : "",
      modified: typeof item.metadata_modified === "string" ? item.metadata_modified : "",
      resources: Number.isInteger(item.num_resources) ? item.num_resources
        : (Array.isArray(item.resources) ? item.resources.length : 0),
    }));
  return { count: Number.isInteger(result.count) ? result.count : results.length, results };
}

async function portalJson(address) {
  const reply = await fetch(address, {
    headers: { Accept: "application/json", "User-Agent": USER_AGENT },
    signal: AbortSignal.timeout(TIMEOUT),
  });
  if (!reply.ok) {
    throw new Error(`HTTP ${reply.status}`);
  }
  return reply.text();
}

export async function onRequestGet({ request, env }) {
  const query = new URL(request.url).searchParams;
  const portal = ((env && env.DATAGOVGR_BASE_URL) || PORTAL).replace(/\/+$/, "");
  if (query.has("q")) {
    const search = searchRequest(query);
    if (search === null) {
      return answer(JSON.stringify({ error: "request" }), 400);
    }
    try {
      const text = await portalJson(`${portal}/api/3/action/package_search?q=${encodeURIComponent(search.text)}&rows=${search.count}`);
      const found = foundDatasets(JSON.parse(text));
      if (found === null) {
        throw new Error("no search results");
      }
      return answer(JSON.stringify(found), 200);
    } catch (error) {
      return answer(JSON.stringify({ error: "portal" }), 502);
    }
  }
  const wanted = catalogueFilter(query);
  if (wanted === null) {
    return answer(JSON.stringify({ error: "request" }), 400);
  }
  try {
    const text = await portalJson(`${portal}/api/3/action/package_search?fq=${encodeURIComponent(wanted)}&rows=1`);
    JSON.parse(text);
    return answer(text, 200);
  } catch (error) {
    return answer(JSON.stringify({ error: "portal" }), 502);
  }
}
