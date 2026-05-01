/* Run with: node --test tests/reading-store.test.mjs

   The site has no JS test framework (the existing verification/ folder
   tests LaTeX rendering with Python). node:test is built into modern
   Node and needs zero dependencies, so it fits the "no bundler, no deps"
   project ethos. */

import test from "node:test";
import assert from "node:assert/strict";
import {
  STORAGE_KEY,
  clamp,
  status,
  sortEntries,
  stats,
  makeEntry,
  applyProgress,
  loadItems,
  saveItems,
  serializeForExport,
  isDirty,
  loadPublished,
} from "../assets/reading-store.js";

// ---------- clamp ---------------------------------------------------

test("clamp keeps values inside [lo, hi]", () => {
  assert.equal(clamp(5, 0, 10), 5);
  assert.equal(clamp(-3, 0, 10), 0);
  assert.equal(clamp(99, 0, 10), 10);
  assert.equal(clamp(0, 0, 10), 0);
  assert.equal(clamp(10, 0, 10), 10);
});

test("clamp coerces NaN/Infinity to lower bound", () => {
  assert.equal(clamp(NaN, 0, 100), 0);
  assert.equal(clamp(Infinity, 0, 100), 0);
  assert.equal(clamp(-Infinity, 0, 100), 0);
});

// ---------- status -------------------------------------------------

test("status: queued / reading / finished", () => {
  assert.equal(status({ currentPage: 0,   totalPages: 100 }), "queued");
  assert.equal(status({ currentPage: 1,   totalPages: 100 }), "reading");
  assert.equal(status({ currentPage: 99,  totalPages: 100 }), "reading");
  assert.equal(status({ currentPage: 100, totalPages: 100 }), "finished");
  assert.equal(status({ currentPage: 200, totalPages: 100 }), "finished");
});

// ---------- applyProgress (the clamp the brief specifically calls out) -

test("applyProgress clamps to [0, totalPages]", () => {
  const entry = { id: "a", title: "x", totalPages: 100, currentPage: 50, addedAt: "" };
  assert.equal(applyProgress(entry, 60).currentPage, 60);
  assert.equal(applyProgress(entry, -5).currentPage, 0);
  assert.equal(applyProgress(entry, 9999).currentPage, 100);
});

test("applyProgress rounds and tolerates garbage input", () => {
  const entry = { id: "a", title: "x", totalPages: 100, currentPage: 0, addedAt: "" };
  assert.equal(applyProgress(entry, 12.7).currentPage, 13);
  assert.equal(applyProgress(entry, "42").currentPage, 42);
  assert.equal(applyProgress(entry, "nope").currentPage, 0);
  assert.equal(applyProgress(entry, undefined).currentPage, 0);
});

test("applyProgress does not mutate the input entry", () => {
  const entry = { id: "a", title: "x", totalPages: 100, currentPage: 50, addedAt: "" };
  applyProgress(entry, 9999);
  assert.equal(entry.currentPage, 50);
});

// ---------- makeEntry ----------------------------------------------

test("makeEntry validates title and totalPages", () => {
  assert.throws(() => makeEntry({ title: "",  totalPages: 100 }), /title/);
  assert.throws(() => makeEntry({ title: "ok", totalPages: 0 }), /totalPages/);
  assert.throws(() => makeEntry({ title: "ok", totalPages: -1 }), /totalPages/);
  assert.throws(() => makeEntry({ title: "ok", totalPages: 1.5 }), /totalPages/);
  assert.throws(() => makeEntry({ title: "ok", totalPages: "abc" }), /totalPages/);
});

test("makeEntry trims input and defaults currentPage to 0", () => {
  const e = makeEntry({ title: "  Peskin  ", author: "  M.E.P.  ", totalPages: 842 });
  assert.equal(e.title, "Peskin");
  assert.equal(e.author, "M.E.P.");
  assert.equal(e.currentPage, 0);
  assert.equal(e.totalPages, 842);
  assert.ok(typeof e.id === "string" && e.id.length > 0);
  assert.ok(typeof e.addedAt === "string" && e.addedAt.length > 0);
});

test("makeEntry stores empty author as null", () => {
  const e = makeEntry({ title: "x", totalPages: 1 });
  assert.equal(e.author, null);
});

// ---------- sortEntries --------------------------------------------

test("sortEntries: reading > queued > finished, addedAt desc breaks ties", () => {
  const r1 = { id: "r1", title: "a", totalPages: 10, currentPage: 4,  addedAt: "2026-01-01T00:00:00Z" };
  const r2 = { id: "r2", title: "b", totalPages: 10, currentPage: 7,  addedAt: "2026-02-01T00:00:00Z" };
  const q1 = { id: "q1", title: "c", totalPages: 10, currentPage: 0,  addedAt: "2026-03-01T00:00:00Z" };
  const q2 = { id: "q2", title: "d", totalPages: 10, currentPage: 0,  addedAt: "2026-01-15T00:00:00Z" };
  const f1 = { id: "f1", title: "e", totalPages: 10, currentPage: 10, addedAt: "2026-04-01T00:00:00Z" };

  const sorted = sortEntries([f1, q2, r1, q1, r2]);
  assert.deepEqual(sorted.map(e => e.id), ["r2", "r1", "q1", "q2", "f1"]);
});

test("sortEntries does not mutate input", () => {
  const a = { id: "a", title: "a", totalPages: 10, currentPage: 0, addedAt: "2026-01-01" };
  const b = { id: "b", title: "b", totalPages: 10, currentPage: 5, addedAt: "2026-01-02" };
  const arr = [a, b];
  sortEntries(arr);
  assert.deepEqual(arr.map(e => e.id), ["a", "b"]);
});

// ---------- stats --------------------------------------------------

test("stats counts categories and aggregates pages", () => {
  const items = [
    { id: "1", title: "a", totalPages: 100, currentPage: 0,   addedAt: "" }, // queued
    { id: "2", title: "b", totalPages: 200, currentPage: 50,  addedAt: "" }, // reading
    { id: "3", title: "c", totalPages: 300, currentPage: 300, addedAt: "" }, // finished
    { id: "4", title: "d", totalPages: 50,  currentPage: 999, addedAt: "" }, // finished (over)
  ];
  const s = stats(items);
  assert.equal(s.queued, 1);
  assert.equal(s.reading, 1);
  assert.equal(s.finished, 2);
  // pagesRead clamps each entry's currentPage to its totalPages: 0 + 50 + 300 + 50 = 400
  assert.equal(s.pagesRead, 400);
  assert.equal(s.totalPages, 650);
});

test("stats on empty list is all zeros", () => {
  assert.deepEqual(stats([]), { reading: 0, queued: 0, finished: 0, pagesRead: 0, totalPages: 0 });
});

// ---------- storage adapter (with a fake) --------------------------

function fakeStorage() {
  const map = new Map();
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => { map.set(k, String(v)); },
    removeItem: (k) => { map.delete(k); },
    _raw: map,
  };
}

test("saveItems / loadItems round-trip through storage", () => {
  const s = fakeStorage();
  const e = makeEntry({ title: "Tong", totalPages: 200 });
  saveItems([e], s);
  const out = loadItems(s);
  assert.equal(out.length, 1);
  assert.equal(out[0].title, "Tong");
  assert.equal(out[0].totalPages, 200);
  assert.equal(out[0].currentPage, 0);
});

test("loadItems returns [] when storage is empty or malformed", () => {
  const s = fakeStorage();
  assert.deepEqual(loadItems(s), []);
  s.setItem(STORAGE_KEY, "not json");
  assert.deepEqual(loadItems(s), []);
  s.setItem(STORAGE_KEY, '{"not":"an array"}');
  assert.deepEqual(loadItems(s), []);
});

test("loadItems drops invalid entries and re-clamps currentPage", () => {
  const s = fakeStorage();
  s.setItem(STORAGE_KEY, JSON.stringify([
    { id: "ok", title: "a", totalPages: 100, currentPage: 999, addedAt: "2026-01-01" }, // clamp to 100
    { id: "bad-no-title", title: "",        totalPages: 100, currentPage: 0, addedAt: "x" },
    { id: "bad-zero",     title: "z",       totalPages: 0,   currentPage: 0, addedAt: "x" },
    null,
    "garbage",
  ]));
  const out = loadItems(s);
  assert.equal(out.length, 1);
  assert.equal(out[0].id, "ok");
  assert.equal(out[0].currentPage, 100);
});

test("loadItems with no storage returns []", () => {
  assert.deepEqual(loadItems(null), []);
});

// ---------- serializeForExport ------------------------------------

test("serializeForExport produces clean, parseable JSON", () => {
  const items = [
    { id: "a", title: "Tong", author: null, totalPages: 200, currentPage: 50, addedAt: "2026-01-01T00:00:00Z" },
  ];
  const out = serializeForExport(items);
  assert.ok(out.endsWith("\n"));
  const parsed = JSON.parse(out);
  assert.equal(parsed.items.length, 1);
  assert.equal(parsed.items[0].title, "Tong");
  assert.ok(typeof parsed.updatedAt === "string");
});

test("serializeForExport drops extraneous fields", () => {
  const items = [{
    id: "a", title: "x", author: "y", totalPages: 10, currentPage: 0, addedAt: "z",
    secret: "leak", _internal: true,
  }];
  const out = JSON.parse(serializeForExport(items));
  assert.deepEqual(Object.keys(out.items[0]).sort(),
    ["addedAt", "author", "currentPage", "id", "title", "totalPages"]);
});

// ---------- isDirty -----------------------------------------------

test("isDirty: identical content is clean", () => {
  const a = [{ id:"1", title:"x", author:null, totalPages:10, currentPage:5, addedAt:"t" }];
  const b = [{ id:"1", title:"x", author:null, totalPages:10, currentPage:5, addedAt:"t" }];
  assert.equal(isDirty(a, b), false);
});

test("isDirty: changed currentPage is dirty", () => {
  const a = [{ id:"1", title:"x", author:null, totalPages:10, currentPage:5, addedAt:"t" }];
  const b = [{ id:"1", title:"x", author:null, totalPages:10, currentPage:6, addedAt:"t" }];
  assert.equal(isDirty(a, b), true);
});

test("isDirty: different array order is clean", () => {
  const a = [
    { id:"1", title:"a", author:null, totalPages:10, currentPage:0, addedAt:"t" },
    { id:"2", title:"b", author:null, totalPages:10, currentPage:0, addedAt:"t" },
  ];
  const b = [a[1], a[0]];
  assert.equal(isDirty(a, b), false);
});

test("isDirty: extra entry is dirty", () => {
  const a = [{ id:"1", title:"x", author:null, totalPages:10, currentPage:0, addedAt:"t" }];
  const b = [];
  assert.equal(isDirty(a, b), true);
});

// ---------- loadPublished (with a stub fetch) ---------------------

function stubFetch(map) {
  return (url) => {
    if (!(url in map)) return Promise.resolve({ ok: false });
    const r = map[url];
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(r),
    });
  };
}

test("loadPublished returns parsed items, dropping invalid ones", async () => {
  const f = stubFetch({
    "x://data": {
      items: [
        { id:"ok", title:"a", author:null, totalPages:100, currentPage:50, addedAt:"t" },
        { id:"clamp", title:"b", author:null, totalPages:100, currentPage:9999, addedAt:"t" },
        { id:"bad", title:"", totalPages:0, currentPage:0, addedAt:"t" },
      ],
    },
  });
  const out = await loadPublished("x://data", f);
  assert.equal(out.length, 2);
  assert.equal(out[0].id, "ok");
  assert.equal(out[1].currentPage, 100);
});

test("loadPublished returns [] on fetch failure", async () => {
  const f = stubFetch({});
  assert.deepEqual(await loadPublished("x://missing", f), []);
});

test("loadPublished returns [] on malformed payload", async () => {
  const f = stubFetch({ "x://data": { items: "not an array" } });
  assert.deepEqual(await loadPublished("x://data", f), []);
});
