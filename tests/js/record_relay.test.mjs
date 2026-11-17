/* Checks of the relay of the public page, with the calls to the portal replaced by prepared replies.

   Usage:
       node --test tests/js/record_relay.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { onRequestGet } from "../../web/functions/api/record.js";

const REPLY = JSON.stringify({ success: true, result: { count: 1, results: [{ name: "troxaia-atyxhmata" }] } });
const realFetch = globalThis.fetch;
let calls;

function portalAnswers(reply) {
  globalThis.fetch = async (address, options) => {
    calls.push({ address, options });
    return reply();
  };
}

async function relay(query, env = {}) {
  const answer = await onRequestGet({ request: new Request(`https://site.example/api/record?${query}`), env });
  return { status: answer.status, body: await answer.text(), headers: answer.headers };
}

beforeEach(() => {
  calls = [];
  portalAnswers(() => new Response(REPLY, { status: 200 }));
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("a dataset name is asked from the portal once and the reply is passed on", async () => {
  const answer = await relay("name=troxaia-atyxhmata");
  assert.equal(answer.status, 200);
  assert.equal(answer.body, REPLY);
  assert.equal(answer.headers.get("Cache-Control"), "no-store");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].address, "https://data.gov.gr/api/3/action/package_search?fq=name%3A%22troxaia-atyxhmata%22&rows=1");
  assert.match(calls[0].options.headers["User-Agent"], /^datagovgr-ai-readiness\//);
});

test("a dataset identifier is asked by the field id", async () => {
  await relay("id=0f0f0f0f-0f0f-0f0f-0f0f-0f0f0f0f0f0f");
  assert.ok(calls[0].address.endsWith("fq=id%3A%220f0f0f0f-0f0f-0f0f-0f0f-0f0f0f0f0f0f%22&rows=1"));
});

test("anything but one name or identifier is refused without a call to the portal", async () => {
  const queries = ["", "name=Two%20Words", "name=a%22%20OR%20name:b", "id=not-an-identifier", "name=a",
    "name=troxaia-atyxhmata&name=other-name", "name=troxaia-atyxhmata&id=0f0f0f0f-0f0f-0f0f-0f0f-0f0f0f0f0f0f"];
  for (const query of queries) {
    assert.equal((await relay(query)).status, 400, query);
  }
  assert.equal(calls.length, 0);
});

test("trouble at the portal is reported as a bad gateway", async () => {
  portalAnswers(() => new Response("busy", { status: 503 }));
  assert.deepEqual([(await relay("name=troxaia-atyxhmata")).status, calls.length], [502, 1]);
  portalAnswers(() => new Response("<html>not json</html>", { status: 200 }));
  assert.equal((await relay("name=troxaia-atyxhmata")).body, '{"error":"portal"}');
  portalAnswers(() => { throw new TypeError("network"); });
  assert.equal((await relay("name=troxaia-atyxhmata")).status, 502);
});

test("the address of the portal can be set for a trial", async () => {
  await relay("name=troxaia-atyxhmata", { DATAGOVGR_BASE_URL: "http://127.0.0.1:9/" });
  assert.ok(calls[0].address.startsWith("http://127.0.0.1:9/api/3/action/package_search?"));
});
