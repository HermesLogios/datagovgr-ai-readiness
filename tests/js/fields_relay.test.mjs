/* Checks of the relay of the public page to the DataStore of the portal, with the calls to the portal replaced
   by prepared replies.

   Usage:
       node --test tests/js/fields_relay.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { onRequestGet } from "../../web/functions/api/fields.js";

const FIRST = "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a11";
const SECOND = "7d1e2a3b-4c5d-4e6f-8a9b-0c1d2e3f4a5b";
const TABLE = {
  success: true,
  result: {
    fields: [
      { id: "_id", type: "int" },
      { id: "Δήμος", type: "text", info: { label: "Δήμος", notes: "Ο δήμος του ατυχήματος" } },
      { id: "Πλήθος", type: "numeric" },
    ],
    records: [{ _id: 1, "Δήμος": "Ρόδου", "Πλήθος": 3 }],
    total: 120,
  },
};
const realFetch = globalThis.fetch;
let calls;

function portalAnswers(reply) {
  globalThis.fetch = async (address, options) => {
    calls.push({ address, options });
    return reply(address);
  };
}

async function relay(query, env = {}) {
  const answer = await onRequestGet({ request: new Request(`https://site.example/api/fields?${query}`), env });
  return { status: answer.status, body: await answer.text(), headers: answer.headers };
}

beforeEach(() => {
  calls = [];
  portalAnswers(() => new Response(JSON.stringify(TABLE), { status: 200 }));
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("each table is asked from the DataStore for its structure only, with no rows", async () => {
  const answer = await relay(`resource=${FIRST}&resource=${SECOND}`);
  assert.equal(answer.status, 200);
  assert.deepEqual(calls.map((call) => call.address), [
    `https://data.gov.gr/api/3/action/datastore_search?resource_id=${FIRST}&limit=0`,
    `https://data.gov.gr/api/3/action/datastore_search?resource_id=${SECOND}&limit=0`,
  ]);
});

test("only names, types and the data dictionary are passed on, without the internal column and the rows", async () => {
  const answer = await relay(`resource=${FIRST}`);
  assert.deepEqual(JSON.parse(answer.body), {
    columns: {
      [FIRST]: [
        { id: "Δήμος", type: "text", label: "Δήμος", notes: "Ο δήμος του ατυχήματος" },
        { id: "Πλήθος", type: "numeric", label: "", notes: "" },
      ],
    },
  });
  assert.ok(!answer.body.includes("Ρόδου"));
  assert.equal(answer.headers.get("Cache-Control"), "no-store");
});

test("a table that the portal does not give is passed on without columns", async () => {
  portalAnswers((address) => (address.includes(FIRST)
    ? new Response("{}", { status: 404 })
    : new Response(JSON.stringify(TABLE), { status: 200 })));
  const columns = JSON.parse((await relay(`resource=${FIRST}&resource=${SECOND}`)).body).columns;
  assert.deepEqual(columns[FIRST], []);
  assert.equal(columns[SECOND].length, 2);
});

test("a request without tables, with more than three, with repeats or with other names is refused unasked", async () => {
  const four = [FIRST, SECOND, FIRST.replace("0c", "1c"), SECOND.replace("7d", "8d")].map((id) => `resource=${id}`).join("&");
  for (const query of ["", four, `resource=${FIRST}&resource=${FIRST}`, "resource=not-an-identifier", `id=${FIRST}`]) {
    assert.equal((await relay(query)).status, 400, query);
  }
  assert.equal(calls.length, 0);
});

test("the address of the portal comes from the settings of the Worker when it is set", async () => {
  await relay(`resource=${FIRST}`, { DATAGOVGR_BASE_URL: "https://trial.example/" });
  assert.ok(calls[0].address.startsWith("https://trial.example/api/3/action/datastore_search?"));
});
