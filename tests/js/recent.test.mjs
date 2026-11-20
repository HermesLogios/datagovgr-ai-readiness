/* Checks of the recent checks that the public page keeps in the storage of the browser, with the storage
   replaced by a stand-in that can be filled up.

   Usage:
       node --test tests/js/recent.test.mjs
*/

import assert from "node:assert/strict";
import { test } from "node:test";

import { MAX_CHECKS, STORAGE_KEY, changedCheck, readChecks, withCheck, withoutCheck, writeChecks } from "../../web/assets/recent.js";

function storage(limit = Infinity) {
  const items = new Map();
  return {
    items,
    getItem: (key) => (items.has(key) ? items.get(key) : null),
    setItem: (key, value) => {
      if (value.length > limit) {
        throw new Error("QuotaExceededError");
      }
      items.set(key, value);
    },
    removeItem: (key) => items.delete(key),
  };
}

function check(name, size = 10) {
  return { name, title: `Σύνολο ${name}`, language: "el", value: name, day: "2026-11-20", time: "2026-11-20T23:40:00",
           version: "1.6", counts: { met: 5, total: 9 }, reply: "{}", html: "x".repeat(size), reading: null, ticks: {} };
}

test("a new check comes first and the list keeps the ten latest", () => {
  let checks = [];
  for (let number = 1; number <= 12; number += 1) {
    checks = withCheck(checks, check(`s${number}`));
  }
  assert.equal(checks.length, MAX_CHECKS);
  assert.deepEqual(checks.slice(0, 2).map((kept) => kept.name), ["s12", "s11"]);
  assert.ok(!checks.some((kept) => kept.name === "s1" || kept.name === "s2"));
});

test("a new check of a dataset already in the list takes the place of the old one", () => {
  const checks = withCheck(withCheck(withCheck([], check("a")), check("b")), { ...check("a"), time: "later" });
  assert.deepEqual(checks.map((kept) => [kept.name, kept.time]), [["a", "later"], ["b", "2026-11-20T23:40:00"]]);
});

test("one check is removed by its dataset, and a change touches only its own check", () => {
  const checks = [check("a"), check("b")];
  assert.deepEqual(withoutCheck(checks, "a").map((kept) => kept.name), ["b"]);
  const changed = changedCheck(checks, "b", { ticks: { Q2: true } });
  assert.deepEqual(changed[1].ticks, { Q2: true });
  assert.deepEqual(changed[0].ticks, {});
  assert.deepEqual(checks[1].ticks, {});
});

test("the checks are written under one key and read back, and what is not a check is left out", () => {
  const kept = storage();
  writeChecks(kept, [check("a"), check("b")]);
  assert.deepEqual(readChecks(kept).map((found) => found.name), ["a", "b"]);
  kept.items.set(STORAGE_KEY, JSON.stringify([check("a"), { name: "b" }, "text", null]));
  assert.deepEqual(readChecks(kept).map((found) => found.name), ["a"]);
  kept.items.set(STORAGE_KEY, "not json");
  assert.deepEqual(readChecks(kept), []);
});

test("when the storage is full the oldest checks are left out until the rest fit", () => {
  const full = storage(JSON.stringify([check("a", 400), check("b", 400)]).length);
  const written = writeChecks(full, [check("a", 400), check("b", 400), check("c", 400)]);
  assert.deepEqual(written.map((found) => found.name), ["a", "b"]);
  assert.deepEqual(readChecks(full).map((found) => found.name), ["a", "b"]);
});

test("an empty list removes the key, and a storage that refuses everything gives nothing back", () => {
  const kept = storage();
  writeChecks(kept, [check("a")]);
  assert.deepEqual(writeChecks(kept, []), []);
  assert.equal(kept.items.has(STORAGE_KEY), false);
  const refusing = { getItem: () => { throw new Error("SecurityError"); }, setItem: () => { throw new Error("SecurityError"); },
                     removeItem: () => { throw new Error("SecurityError"); } };
  assert.deepEqual(readChecks(refusing), []);
  assert.equal(writeChecks(refusing, [check("a")]), null);
});
