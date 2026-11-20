/* Checks of the helpers of the search by words on the public page.

   Usage:
       node --test tests/js/search.test.mjs
*/

import assert from "node:assert/strict";
import { test } from "node:test";

import { RESULTS, SUGGESTIONS, foundDatasets, namesDataset, searchAddress, wantsSuggestions } from "../../web/assets/search.js";

test("a link, the name of a dataset or its identifier names one dataset, and anything else is words", () => {
  for (const text of ["https://data.gov.gr/dataset/troxaia-atyxhmata", "data.gov.gr/dataset/troxaia-atyxhmata",
                      " troxaia-atyxhmata ", "odiko_diktyo", "0c5a6f2e-1b7d-4c1e-9a43-2f6b8d0e9a11"]) {
    assert.equal(namesDataset(text), true, text);
  }
  for (const text of ["τροχαία ατυχήματα", "Τροχαία", "covid", "air quality", "ΕΛΣΤΑΤ 2024"]) {
    assert.equal(namesDataset(text), false, text);
  }
});

test("suggestions are asked for words of three characters or more", () => {
  assert.equal(wantsSuggestions("τρ"), false);
  assert.equal(wantsSuggestions("τρο"), true);
  assert.equal(wantsSuggestions("  τρ  "), false);
  assert.equal(wantsSuggestions("troxaia-atyxhmata"), false);
});

test("the question to the relay carries the words and the number of datasets", () => {
  assert.equal(searchAddress("/api/record", " τροχαία ατυχήματα ", SUGGESTIONS), `/api/record?q=${encodeURIComponent("τροχαία ατυχήματα")}&rows=8`);
  assert.equal(RESULTS, 20);
});

test("the reply of the relay is read into datasets, and what is not a reply gives null", () => {
  const reply = JSON.stringify({ count: 2, results: [
    { name: "a", title: "Α", organization: "ΕΛΣΤΑΤ", modified: "2026-03-12T10:20:00", resources: 4 },
    { name: "b", title: "Β" },
    { title: "χωρίς όνομα" },
  ] });
  assert.deepEqual(foundDatasets(reply), { count: 2, results: [
    { name: "a", title: "Α", organization: "ΕΛΣΤΑΤ", modified: "2026-03-12T10:20:00", resources: 4 },
    { name: "b", title: "Β", organization: "", modified: "", resources: 0 },
  ] });
  for (const text of ["", "not json", "[]", '{"count": "2", "results": []}', '{"error": "portal"}']) {
    assert.equal(foundDatasets(text), null, text);
  }
});
