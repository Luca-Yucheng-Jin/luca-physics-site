/* Reading-list store: pure helpers + a thin localStorage adapter.

   Kept DOM-free so it can be imported by a Node test runner. Functions
   that touch storage take an optional `storage` argument (any object
   shaped like the Web Storage API), which the tests use to inject a
   fake. In the browser it defaults to `localStorage`.

   Schema (one entry):
     { id, title, author?, totalPages, currentPage, addedAt }
   `userId` is intentionally omitted — this site has no auth. */

export const STORAGE_KEY = "reading-list:items";

export function clamp(n, lo, hi) {
  if (!Number.isFinite(n)) return lo;
  if (n < lo) return lo;
  if (n > hi) return hi;
  return n;
}

export function status(entry) {
  if (entry.currentPage >= entry.totalPages) return "finished";
  if (entry.currentPage <= 0) return "queued";
  return "reading";
}

const STATUS_ORDER = { reading: 0, queued: 1, finished: 2 };

export function sortEntries(items) {
  return items.slice().sort((a, b) => {
    const sa = STATUS_ORDER[status(a)];
    const sb = STATUS_ORDER[status(b)];
    if (sa !== sb) return sa - sb;
    // tie-break: addedAt descending (newest first)
    const aa = a.addedAt || "";
    const bb = b.addedAt || "";
    if (aa === bb) return 0;
    return aa < bb ? 1 : -1;
  });
}

export function stats(items) {
  let reading = 0, queued = 0, finished = 0, pagesRead = 0, totalPages = 0;
  for (const e of items) {
    const s = status(e);
    if (s === "reading") reading++;
    else if (s === "queued") queued++;
    else finished++;
    pagesRead  += clamp(e.currentPage, 0, e.totalPages);
    totalPages += e.totalPages;
  }
  return { reading, queued, finished, pagesRead, totalPages };
}

export function newId() {
  // Short, sortable-ish, no deps. The randomness only needs to be enough
  // to avoid collisions within a single user's list.
  const r = Math.random().toString(36).slice(2, 9);
  const t = Date.now().toString(36);
  return "r_" + t + "_" + r;
}

export function makeEntry(input, opts = {}) {
  const title = String(input?.title ?? "").trim();
  const author = String(input?.author ?? "").trim();
  const totalPages = Number(input?.totalPages);
  if (!title) throw new Error("title is required");
  if (!Number.isFinite(totalPages) || !Number.isInteger(totalPages) || totalPages <= 0) {
    throw new Error("totalPages must be a positive integer");
  }
  return {
    id: opts.id || newId(),
    title,
    author: author || null,
    totalPages,
    currentPage: 0,
    addedAt: opts.addedAt || new Date().toISOString(),
  };
}

export function applyProgress(entry, currentPage) {
  const raw = Number(currentPage);
  const next = clamp(Number.isFinite(raw) ? Math.round(raw) : 0, 0, entry.totalPages);
  return { ...entry, currentPage: next };
}

function isValidEntry(e) {
  return !!e
    && typeof e.id === "string"
    && typeof e.title === "string" && e.title.length > 0
    && Number.isInteger(e.totalPages) && e.totalPages > 0
    && Number.isInteger(e.currentPage) && e.currentPage >= 0
    && typeof e.addedAt === "string";
}

function defaultStorage() {
  return (typeof globalThis !== "undefined" && globalThis.localStorage) || null;
}

export function loadItems(storage = defaultStorage()) {
  if (!storage) return [];
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(isValidEntry)
      .map(e => ({ ...e, currentPage: clamp(e.currentPage, 0, e.totalPages) }));
  } catch {
    return [];
  }
}

export function saveItems(items, storage = defaultStorage()) {
  if (!storage) return;
  try { storage.setItem(STORAGE_KEY, JSON.stringify(items)); } catch {}
}
