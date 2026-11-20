/* Checks of the entry of the site on Cloudflare Workers: which requests reach the two relays and
   which are answered with the files of the build.

   Usage:
       node --test tests/js/site_worker.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import worker from "../../web/worker.js";

const REPLY = JSON.stringify({ success: true, result: { count: 1, results: [{ name: "troxaia-atyxhmata" }] } });
const READING = JSON.stringify({ model: "jev-1.14.0", answers: { contents: { type: "noul", noul: 0.9 } } });
const KEY = "ts-trial-key-0123456789";
const SENT = JSON.stringify({
  key: KEY,
  request: {
    model: "jev-1.14.0",
    state: { title: "Στάσεις", description: "Οι στάσεις του δήμου.", resource_descriptions: [] },
    questions: { contents: { type: "noul", instructions: "The description tells a reader what the data contain." } },
  },
});
const realFetch = globalThis.fetch;
let outsideCalls;
let fileRequests;

const env = {
  ASSETS: {
    fetch: async (request) => {
      fileRequests.push(new URL(request.url).pathname);
      return new Response("file of the site");
    },
  },
};

function request(path, method = "GET", body = undefined) {
  const headers = body === undefined ? {} : { "Content-Type": "application/json" };
  return new Request(`https://site.example${path}`, { method, body, headers });
}

beforeEach(() => {
  outsideCalls = [];
  fileRequests = [];
  globalThis.fetch = async (address, options = {}) => {
    outsideCalls.push({ address: String(address), options });
    return new Response(String(address).includes("systemone") ? READING : REPLY, { status: 200 });
  };
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("a request for the relay of the catalogue is answered with the reply of the portal", async () => {
  const answer = await worker.fetch(request("/api/record?name=troxaia-atyxhmata"), env);
  assert.equal(answer.status, 200);
  assert.equal(await answer.text(), REPLY);
  assert.equal(outsideCalls.length, 1);
  assert.deepEqual(fileRequests, []);
});

test("a request for the relay of the columns is answered with the structure of the tables", async () => {
  const answer = await worker.fetch(request("/api/fields?resource=0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a11"), env);
  assert.equal(answer.status, 200);
  assert.ok(outsideCalls[0].address.includes("datastore_search?resource_id=0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a11&limit=0"));
  assert.deepEqual(fileRequests, []);
});

test("the relay of the catalogue answers only to GET", async () => {
  const answer = await worker.fetch(request("/api/record?name=troxaia-atyxhmata", "POST", "{}"), env);
  assert.equal(answer.status, 405);
  assert.equal(answer.headers.get("Allow"), "GET");
  assert.equal(outsideCalls.length, 0);
});

test("a request for the relay of the model is answered with the reply of the model", async () => {
  const answer = await worker.fetch(request("/api/reading", "POST", SENT), env);
  assert.equal(answer.status, 200);
  assert.equal(await answer.text(), READING);
  assert.equal(outsideCalls.length, 1);
  assert.equal(outsideCalls[0].address, "https://api.typesafe.ai/v1/systemone");
  assert.equal(outsideCalls[0].options.headers.Authorization, `Bearer ${KEY}`);
  assert.deepEqual(fileRequests, []);
});

test("the relay of the model answers only to POST", async () => {
  const answer = await worker.fetch(request("/api/reading"), env);
  assert.equal(answer.status, 405);
  assert.equal(answer.headers.get("Allow"), "POST");
  assert.equal(outsideCalls.length, 0);
});

test("every other address is answered with the files of the site", async () => {
  const paths = ["/", "/en/guide/", "/api/other", "/api/record/more", "/api/reading/more"];
  for (const path of paths) {
    const answer = await worker.fetch(request(path), env);
    assert.equal(await answer.text(), "file of the site");
  }
  assert.deepEqual(fileRequests, paths);
  assert.equal(outsideCalls.length, 0);
});

test("the addresses of the portal and of the model come from the settings of the Worker when they are set", async () => {
  const trial = { ...env, DATAGOVGR_BASE_URL: "http://127.0.0.1:9", TYPESAFE_API_URL: "http://127.0.0.1:8/v1/systemone" };
  await worker.fetch(request("/api/record?name=troxaia-atyxhmata"), trial);
  await worker.fetch(request("/api/reading", "POST", SENT), trial);
  assert.ok(outsideCalls[0].address.startsWith("http://127.0.0.1:9/api/3/action/package_search?"));
  assert.equal(outsideCalls[1].address, "http://127.0.0.1:8/v1/systemone");
});
