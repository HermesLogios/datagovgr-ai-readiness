/* Relay of the public page to the catalogue of data.gov.gr.
   A browser that is refused a direct call to the portal asks here for the record of one dataset.
   The relay accepts only one dataset name or identifier, builds the address of the portal
   itself and passes the reply on without keeping it. */

const PORTAL = "https://data.gov.gr";
const USER_AGENT = "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)";
const NAME = /^[a-z0-9_-]{2,100}$/;
const IDENTIFIER = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const TIMEOUT = 20000;   // milliseconds to wait for the portal
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

export async function onRequestGet({ request, env }) {
  const wanted = catalogueFilter(new URL(request.url).searchParams);
  if (wanted === null) {
    return answer(JSON.stringify({ error: "request" }), 400);
  }
  const portal = ((env && env.DATAGOVGR_BASE_URL) || PORTAL).replace(/\/+$/, "");
  const address = `${portal}/api/3/action/package_search?fq=${encodeURIComponent(wanted)}&rows=1`;
  try {
    const reply = await fetch(address, {
      headers: { Accept: "application/json", "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(TIMEOUT),
    });
    if (!reply.ok) {
      throw new Error(`HTTP ${reply.status}`);
    }
    const text = await reply.text();
    JSON.parse(text);
    return answer(text, 200);
  } catch (error) {
    return answer(JSON.stringify({ error: "portal" }), 502);
  }
}
