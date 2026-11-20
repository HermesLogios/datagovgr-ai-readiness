/* The recent checks of the visitor, kept only in the storage of the browser (localStorage), under one key.
   Each check holds what the page needs to show it again as it was: the reply of the catalogue, the result as
   it was shown, the second reading when there was one, and the ticks of the checklist. The key of the model
   is never part of it. Nothing here touches the page; the storage is given to every function. */

export const STORAGE_KEY = "datagovgr-ai-readiness.recent";
export const MAX_CHECKS = 10;

function isCheck(value) {
  return Boolean(value) && typeof value === "object" && typeof value.name === "string" && typeof value.title === "string"
    && typeof value.reply === "string" && typeof value.html === "string" && typeof value.time === "string";
}

/* The kept checks, newest first; none when the storage is empty, refused or holds something else. */
export function readChecks(storage) {
  try {
    const kept = JSON.parse(storage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(kept) ? kept.filter(isCheck).slice(0, MAX_CHECKS) : [];
  } catch (error) {
    return [];
  }
}

/* The list with a new check first; an older check of the same dataset makes way for it. */
export function withCheck(checks, check) {
  return [check, ...checks.filter((kept) => kept.name !== check.name)].slice(0, MAX_CHECKS);
}

export function withoutCheck(checks, name) {
  return checks.filter((kept) => kept.name !== name);
}

export function changedCheck(checks, name, changes) {
  return checks.map((kept) => (kept.name === name ? { ...kept, ...changes } : kept));
}

/* Writes the checks; an empty list removes the key. When the storage is full, the oldest are left out until the
   rest fit. Returns the checks that were written, or null when nothing could be written, in which case what was
   kept before stays as it was. */
export function writeChecks(storage, checks) {
  if (!checks.length) {
    try {
      storage.removeItem(STORAGE_KEY);
      return [];
    } catch (error) {
      return null;
    }
  }
  for (let count = checks.length; count > 0; count -= 1) {
    try {
      storage.setItem(STORAGE_KEY, JSON.stringify(checks.slice(0, count)));
      return checks.slice(0, count);
    } catch (error) {
      continue;
    }
  }
  return null;
}
