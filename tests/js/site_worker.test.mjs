/* Checks of the entry of the site on Cloudflare Workers: which requests reach the relay and
   which are answered with the files of the build.

   Usage:
       node --test tests/js/site_worker.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import worker from "../../web/worker.js";

const REPLY = JSON.stringify({ success: true, result: { count: 1, results: [{ name: "troxaia-atyxhmata" }] } });
const realFetch = globalThis.fetch;
let portalCalls;
let fileRequests;

const env = {
  ASSETS: {
    fetch: async (request) => {
      fileRequests.push(new URL(request.url).pathname);
      return new Response("file of the site");
    },
  },
};

function request(path, method = "GET") {
  return new Request(`https://site.example${path}`, { method });
}

beforeEach(() => {
  portalCalls = [];
  fileRequests = [];
  globalThis.fetch = async (address) => {
    portalCalls.push(String(address));
    return new Response(REPLY, { status: 200 });
  };
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("a request for the relay is answered with the reply of the portal", async () => {
  const answer = await worker.fetch(request("/api/record?name=troxaia-atyxhmata"), env);
  assert.equal(answer.status, 200);
  assert.equal(await answer.text(), REPLY);
  assert.equal(portalCalls.length, 1);
  assert.deepEqual(fileRequests, []);
});

test("the relay answers only to GET", async () => {
  const answer = await worker.fetch(request("/api/record?name=troxaia-atyxhmata", "POST"), env);
  assert.equal(answer.status, 405);
  assert.equal(answer.headers.get("Allow"), "GET");
  assert.equal(portalCalls.length, 0);
});

test("every other address is answered with the files of the site", async () => {
  const paths = ["/", "/en/guide/", "/api/other", "/api/record/more"];
  for (const path of paths) {
    const answer = await worker.fetch(request(path), env);
    assert.equal(await answer.text(), "file of the site");
  }
  assert.deepEqual(fileRequests, paths);
  assert.equal(portalCalls.length, 0);
});

test("the address of the portal comes from the settings of the Worker when it is set", async () => {
  await worker.fetch(request("/api/record?name=troxaia-atyxhmata"), { ...env, DATAGOVGR_BASE_URL: "http://127.0.0.1:9" });
  assert.ok(portalCalls[0].startsWith("http://127.0.0.1:9/api/3/action/package_search?"));
});
