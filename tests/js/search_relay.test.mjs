/* Checks of the search of the catalogue by words through the relay of the public page, with the calls to the
   portal replaced by prepared replies.

   Usage:
       node --test tests/js/search_relay.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { onRequestGet } from "../../web/functions/api/record.js";

const FOUND = {
  success: true,
  result: {
    count: 134,
    results: [
      {
        name: "troxaia-atyxhmata",
        title: "Τροχαία ατυχήματα",
        notes: "Μεγάλη περιγραφή που δεν χρειάζεται στη λίστα.",
        organization: { name: "elstat", title: "ΕΛΣΤΑΤ" },
        metadata_modified: "2026-03-12T10:20:00.000000",
        num_resources: 4,
        resources: [{ url: "https://example.org/a.csv" }],
      },
      { name: "odiko-diktyo", title: { el: "Οδικό δίκτυο", en: "Road network" }, organization: null, num_resources: 1 },
    ],
  },
};
const realFetch = globalThis.fetch;
let calls;

function portalAnswers(reply) {
  globalThis.fetch = async (address, options) => {
    calls.push({ address, options });
    return reply();
  };
}

async function relay(query) {
  const answer = await onRequestGet({ request: new Request(`https://site.example/api/record?${query}`), env: {} });
  return { status: answer.status, body: await answer.text() };
}

beforeEach(() => {
  calls = [];
  portalAnswers(() => new Response(JSON.stringify(FOUND), { status: 200 }));
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("words are searched in the catalogue for the number of datasets asked", async () => {
  const answer = await relay(`q=${encodeURIComponent("τροχαία ατυχήματα")}&rows=8`);
  assert.equal(answer.status, 200);
  assert.equal(calls[0].address,
    `https://data.gov.gr/api/3/action/package_search?q=${encodeURIComponent("τροχαία ατυχήματα")}&rows=8`);
});

test("only the name, title, publisher, day of the last change and number of files of each dataset come back", async () => {
  const answer = JSON.parse((await relay("q=ατυχήματα&rows=20")).body);
  assert.deepEqual(answer, {
    count: 134,
    results: [
      { name: "troxaia-atyxhmata", title: "Τροχαία ατυχήματα", organization: "ΕΛΣΤΑΤ", modified: "2026-03-12T10:20:00.000000", resources: 4 },
      { name: "odiko-diktyo", title: "Οδικό δίκτυο", organization: "", modified: "", resources: 1 },
    ],
  });
});

test("signs of the search language of the portal are left out of the words", async () => {
  await relay(`q=${encodeURIComponent('ατυχήματα:(2024) "Ρόδος"*')}&rows=8`);
  assert.ok(calls[0].address.includes(`q=${encodeURIComponent("ατυχήματα 2024 Ρόδος")}&`));
});

test("eight datasets are asked when the request names no number", async () => {
  await relay("q=ατυχήματα");
  assert.ok(calls[0].address.endsWith("&rows=8"));
});

test("a search that is too short, too long, asks too many datasets or comes with a name is refused unasked", async () => {
  for (const query of ["q=α", `q=${"α".repeat(101)}`, "q=ατυχήματα&rows=21", "q=ατυχήματα&rows=0", "q=ατυχήματα&rows=δύο",
                       "q=ατυχήματα&name=troxaia-atyxhmata", "q=ατυχήματα&q=δρόμοι", `q=${encodeURIComponent(":()")}`]) {
    assert.equal((await relay(query)).status, 400, query);
  }
  assert.equal(calls.length, 0);
});

test("a failed search of the portal is answered as a failure of the portal", async () => {
  portalAnswers(() => new Response("{}", { status: 500 }));
  const answer = await relay("q=ατυχήματα&rows=8");
  assert.equal(answer.status, 502);
  assert.deepEqual(JSON.parse(answer.body), { error: "portal" });
});
