/* Relay of the public page to the DataStore of data.gov.gr, for the second reading.
   The page asks for the columns of at most three tables of one dataset. For each table the relay asks the
   portal for its structure only (datastore_search with limit=0, as scripts/08_documentation_checks.py does)
   and passes on the names, the types and the data dictionary of the columns, never a row of the data. */

const PORTAL = "https://data.gov.gr";
const USER_AGENT = "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)";
const IDENTIFIER = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const MAX_TABLES = 3;
const MAX_COLUMNS = 100;   // columns passed on for one table
const MAX_TEXT = 300;      // characters of a name, a type, a label or a note
const TIMEOUT = 15000;     // milliseconds to wait for the portal
const HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

function answer(body, status) {
  return new Response(JSON.stringify(body), { status, headers: HEADERS });
}

function shortText(value) {
  return typeof value === "string" ? value.slice(0, MAX_TEXT) : "";
}

/* Name, type, label and notes of each column of a reply of the DataStore, without its internal column _id. */
function columnsOf(reply) {
  const fields = reply && reply.success === true && reply.result && Array.isArray(reply.result.fields)
    ? reply.result.fields
    : [];
  return fields
    .filter((field) => field && typeof field.id === "string" && field.id !== "_id")
    .slice(0, MAX_COLUMNS)
    .map((field) => {
      const info = field.info && typeof field.info === "object" ? field.info : {};
      return { id: shortText(field.id), type: shortText(field.type), label: shortText(info.label), notes: shortText(info.notes) };
    });
}

/* Columns of one table; none when the portal does not give the table. */
async function tableColumns(portal, identifier) {
  const address = `${portal}/api/3/action/datastore_search?resource_id=${identifier}&limit=0`;
  try {
    const reply = await fetch(address, {
      headers: { Accept: "application/json", "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(TIMEOUT),
    });
    return reply.ok ? columnsOf(JSON.parse(await reply.text())) : [];
  } catch (error) {
    return [];
  }
}

export async function onRequestGet({ request, env }) {
  const identifiers = new URL(request.url).searchParams.getAll("resource");
  if (identifiers.length < 1 || identifiers.length > MAX_TABLES || new Set(identifiers).size !== identifiers.length
      || !identifiers.every((identifier) => IDENTIFIER.test(identifier))) {
    return answer({ error: "request" }, 400);
  }
  const portal = ((env && env.DATAGOVGR_BASE_URL) || PORTAL).replace(/\/+$/, "");
  const tables = await Promise.all(identifiers.map((identifier) => tableColumns(portal, identifier)));
  return answer({ columns: Object.fromEntries(identifiers.map((identifier, index) => [identifier, tables[index]])) }, 200);
}
