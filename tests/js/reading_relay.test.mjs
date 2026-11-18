/* Checks of the relay of the public page to Jev, with the calls to the model replaced by prepared replies.

   Usage:
       node --test tests/js/reading_relay.test.mjs
*/

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { onRequestPost } from "../../web/functions/api/reading.js";

const KEY = "ts-trial-key-0123456789";
const REPLY = JSON.stringify({ model: "jev-1.14.0", answers: { contents: { type: "noul", noul: 0.9 } }, usage: { input_tokens: 700 } });
const realFetch = globalThis.fetch;
let calls;

function modelRequest() {
  return {
    model: "jev-1.14.0",
    state: { title: "Στάσεις", description: "Οι στάσεις του δήμου.", resource_descriptions: ["Οι στάσεις ανά γραμμή."] },
    questions: {
      contents: {
        type: "noul",
        instructions: "The description of the dataset tells a reader what the data contain.",
        criteria: { true: "The description names what is recorded.", false: "The description repeats the title." },
      },
    },
  };
}

function modelAnswers(reply) {
  globalThis.fetch = async (address, options) => {
    calls.push({ address, options });
    return reply();
  };
}

async function relay(sent, env = {}, type = "application/json") {
  const body = typeof sent === "string" ? sent : JSON.stringify(sent);
  const request = new Request("https://site.example/api/reading", { method: "POST", body, headers: { "Content-Type": type } });
  const answer = await onRequestPost({ request, env });
  return { status: answer.status, body: await answer.text(), headers: answer.headers };
}

beforeEach(() => {
  calls = [];
  modelAnswers(() => new Response(REPLY, { status: 200 }));
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("a request of the page is passed to the model with the key and the reply is passed back", async () => {
  const answer = await relay({ key: KEY, request: modelRequest() });
  assert.equal(answer.status, 200);
  assert.equal(answer.body, REPLY);
  assert.equal(answer.headers.get("Cache-Control"), "no-store");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].address, "https://api.typesafe.ai/v1/systemone");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers.Authorization, `Bearer ${KEY}`);
  assert.deepEqual(JSON.parse(calls[0].options.body), modelRequest());
});

test("only the fields that the page sends reach the model", async () => {
  const request = modelRequest();
  request.assets = { photo: "https://example.org/a.png" };
  request.state.maintainer = "someone@example.org";
  request.questions.contents.examples = ["extra"];
  await relay({ key: KEY, request, note: "extra" });
  assert.deepEqual(JSON.parse(calls[0].options.body), modelRequest());
});

test("a statement without criteria is passed on without them", async () => {
  const request = modelRequest();
  delete request.questions.contents.criteria;
  await relay({ key: KEY, request });
  assert.deepEqual(JSON.parse(calls[0].options.body).questions.contents, { type: "noul", instructions: request.questions.contents.instructions });
});

test("anything but a request of the page is refused without a call to the model", async () => {
  const changed = (change) => {
    const request = modelRequest();
    change(request);
    return { key: KEY, request };
  };
  const refused = [
    "not json",
    "[]",
    { request: modelRequest() },
    { key: "short", request: modelRequest() },
    { key: "a key with spaces 0123456789", request: modelRequest() },
    { key: KEY },
    changed((request) => { request.model = "other-model"; }),
    changed((request) => { request.state = "text"; }),
    changed((request) => { request.state.title = 7; }),
    changed((request) => { request.state.resource_descriptions = "text"; }),
    changed((request) => { request.state.resource_descriptions = Array(21).fill("text"); }),
    changed((request) => { request.state.description = "α".repeat(8001); }),
    changed((request) => { request.questions = {}; }),
    changed((request) => { request.questions.contents.type = "choice"; }),
    changed((request) => { request.questions.contents.instructions = ""; }),
    changed((request) => { request.questions.contents.criteria = { true: "only one side" }; }),
    changed((request) => { request.questions["Bad Name"] = request.questions.contents; }),
    changed((request) => { request.questions = JSON.parse('{"__proto__": {"type": "noul", "instructions": "A statement."}}'); }),
    changed((request) => {
      for (let number = 0; number < 10; number += 1) {
        request.questions[`statement_${"abcdefghij"[number]}`] = request.questions.contents;
      }
    }),
    { key: KEY, request: modelRequest(), padding: "x".repeat(60000) },
  ];
  for (const sent of refused) {
    const answer = await relay(sent);
    assert.equal(answer.status, 400, JSON.stringify(sent).slice(0, 80));
    assert.equal(answer.body, '{"error":"request"}');
  }
  assert.equal(calls.length, 0);
});

test("a body that is not declared as JSON is refused without a call to the model", async () => {
  for (const type of ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data"]) {
    const answer = await relay({ key: KEY, request: modelRequest() }, {}, type);
    assert.equal(answer.status, 400, type);
    assert.equal(answer.body, '{"error":"request"}');
  }
  assert.equal(calls.length, 0);
  assert.equal((await relay({ key: KEY, request: modelRequest() }, {}, "application/json; charset=utf-8")).status, 200);
});

test("a refused key and a limit of requests are told apart from other trouble", async () => {
  modelAnswers(() => new Response('{"detail":"invalid key"}', { status: 401 }));
  assert.deepEqual([(await relay({ key: KEY, request: modelRequest() })).status, calls.length], [401, 1]);
  modelAnswers(() => new Response("forbidden", { status: 403 }));
  assert.equal((await relay({ key: KEY, request: modelRequest() })).body, '{"error":"key"}');
  modelAnswers(() => new Response("slow down", { status: 429 }));
  const limited = await relay({ key: KEY, request: modelRequest() });
  assert.deepEqual([limited.status, limited.body], [429, '{"error":"limit"}']);
});

test("trouble at the model is reported as a bad gateway", async () => {
  modelAnswers(() => new Response("busy", { status: 503 }));
  assert.equal((await relay({ key: KEY, request: modelRequest() })).status, 502);
  modelAnswers(() => new Response("<html>not json</html>", { status: 200 }));
  assert.equal((await relay({ key: KEY, request: modelRequest() })).body, '{"error":"service"}');
  modelAnswers(() => new Response('{"detail":"bad request"}', { status: 422 }));
  assert.equal((await relay({ key: KEY, request: modelRequest() })).status, 502);
  modelAnswers(() => { throw new TypeError("network"); });
  assert.equal((await relay({ key: KEY, request: modelRequest() })).status, 502);
});

test("no answer of the relay repeats the key", async () => {
  const replies = [() => new Response(REPLY, { status: 200 }), () => new Response("no", { status: 401 }),
    () => new Response("no", { status: 429 }), () => new Response("no", { status: 500 })];
  for (const reply of replies) {
    modelAnswers(reply);
    const answer = await relay({ key: KEY, request: modelRequest() });
    assert.ok(!answer.body.includes(KEY));
    assert.ok(![...answer.headers.values()].some((value) => value.includes(KEY)));
  }
  assert.ok(!(await relay({ key: KEY, request: { model: "other-model" } })).body.includes(KEY));
});

test("the address of the model can be set for a trial", async () => {
  await relay({ key: KEY, request: modelRequest() }, { TYPESAFE_API_URL: "http://127.0.0.1:9/v1/systemone" });
  assert.equal(calls[0].address, "http://127.0.0.1:9/v1/systemone");
});
