/* Reading list — DOM wiring.

   Loaded as <script type="module"> from reading.html. Pure data helpers
   live in reading-store.js so they can be unit-tested in Node. This file
   only handles DOM events, rendering, and persistence I/O. */

import {
  loadItems,
  saveItems,
  makeEntry,
  applyProgress,
  sortEntries,
  stats,
  status,
} from "./reading-store.js";

let items = loadItems();
let activeFilter = "all"; // "all" | "reading" | "done"

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function persist() { saveItems(items); }

// ---------- Init ---------------------------------------------------

function init() {
  bindAddForm();
  bindFilters();
  render();
}

function bindAddForm() {
  const form = $("#reading-add");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const title = String(fd.get("title") || "").trim();
    const author = String(fd.get("author") || "").trim();
    const rawPages = String(fd.get("totalPages") || "").trim();
    const totalPages = Number(rawPages);

    if (!title) return flagError(form.elements.title, "Title is required");
    if (!Number.isFinite(totalPages) || !Number.isInteger(totalPages) || totalPages <= 0) {
      return flagError(form.elements.totalPages, "Pages must be a positive integer");
    }

    try {
      items.push(makeEntry({ title, author, totalPages }));
      persist();
      form.reset();
      form.elements.title.focus();
      render();
    } catch (err) {
      flagError(form.elements.title, err.message);
    }
  });
}

function flagError(input, msg) {
  input.setAttribute("aria-invalid", "true");
  input.title = msg;
  input.focus();
  setTimeout(() => {
    input.removeAttribute("aria-invalid");
    input.title = "";
  }, 2400);
}

function bindFilters() {
  $$('[data-filter]').forEach(btn => {
    btn.addEventListener("click", () => {
      activeFilter = btn.dataset.filter;
      $$('[data-filter]').forEach(b =>
        b.classList.toggle("is-active", b === btn)
      );
      render();
    });
  });
}

// ---------- Render -------------------------------------------------

function visibleItems() {
  const sorted = sortEntries(items);
  if (activeFilter === "reading") {
    return sorted.filter(e => status(e) !== "finished");
  }
  if (activeFilter === "done") {
    return sorted.filter(e => status(e) === "finished");
  }
  return sorted;
}

function render() {
  renderStats();
  renderList();
}

function renderStats() {
  const wrap = $("#reading-stats");
  if (!items.length) { wrap.hidden = true; wrap.innerHTML = ""; return; }
  const s = stats(items);
  wrap.hidden = false;
  wrap.innerHTML = `
    <span class="reading-stat"><strong>${s.reading}</strong><span>reading</span></span>
    <span class="reading-stat"><strong>${s.queued}</strong><span>queued</span></span>
    <span class="reading-stat"><strong>${s.finished}</strong><span>finished</span></span>
    <span class="reading-stat reading-stat--pages">
      <strong>${s.pagesRead.toLocaleString()}</strong>
      <span>/ ${s.totalPages.toLocaleString()} pages</span>
    </span>
  `;
}

function renderList() {
  const list = $("#reading-list");
  list.innerHTML = "";

  if (!items.length) {
    list.appendChild(emptyState(
      "Nothing on the pile yet — add a book or paper above to start tracking it."
    ));
    return;
  }

  const vis = visibleItems();
  if (!vis.length) {
    list.appendChild(emptyState("No entries match this filter."));
    return;
  }

  for (const entry of vis) list.appendChild(renderRow(entry));
}

function emptyState(text) {
  const p = document.createElement("p");
  p.className = "reading-empty";
  p.textContent = text;
  return p;
}

function renderRow(entry) {
  const s = status(entry);
  const li = document.createElement("li");
  li.className = "reading-row reading-row--" + s;
  li.dataset.id = entry.id;

  // ----- Heading row: title + author ------------------------------
  const head = document.createElement("div");
  head.className = "reading-row__head";

  const titleEl = document.createElement("span");
  titleEl.className = "reading-row__title";
  titleEl.textContent = entry.title;
  head.appendChild(titleEl);

  if (entry.author) {
    const authorEl = document.createElement("span");
    authorEl.className = "reading-row__author";
    authorEl.textContent = entry.author;
    head.appendChild(authorEl);
  }
  li.appendChild(head);

  // ----- Progress bar ---------------------------------------------
  const bar = document.createElement("div");
  bar.className = "reading-row__bar";
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-valuemin", "0");
  bar.setAttribute("aria-valuemax", String(entry.totalPages));
  bar.setAttribute("aria-valuenow", String(entry.currentPage));
  const fill = document.createElement("div");
  fill.className = "reading-row__bar-fill";
  const pct = entry.totalPages
    ? Math.min(100, (entry.currentPage / entry.totalPages) * 100)
    : 0;
  fill.style.width = pct + "%";
  bar.appendChild(fill);
  li.appendChild(bar);

  // ----- Controls --------------------------------------------------
  const ctrl = document.createElement("div");
  ctrl.className = "reading-row__ctrl";

  const pages = document.createElement("button");
  pages.type = "button";
  pages.className = "reading-row__pages";
  pages.setAttribute("aria-label", "Edit current page");
  pages.title = "Click to edit current page";
  pages.textContent = entry.currentPage + " / " + entry.totalPages;
  pages.addEventListener("click", () => editProgress(entry, pages));
  ctrl.appendChild(pages);

  const dec  = makeBtn("−10", "Subtract 10 pages", () => bumpProgress(entry.id, -10));
  const inc  = makeBtn("+10", "Add 10 pages",      () => bumpProgress(entry.id, +10));
  if (s === "finished") { dec.disabled = true; inc.disabled = true; }
  ctrl.appendChild(dec); ctrl.appendChild(inc);

  const done = makeBtn("✓", "Mark finished",
    () => setProgress(entry.id, entry.totalPages));
  done.classList.add("reading-row__btn--done");
  if (s === "finished") done.disabled = true;
  ctrl.appendChild(done);

  const del = makeBtn("×", "Delete", () => removeEntry(entry.id));
  del.classList.add("reading-row__btn--del");
  ctrl.appendChild(del);

  li.appendChild(ctrl);
  return li;
}

function makeBtn(label, ariaLabel, onClick) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "reading-row__btn";
  b.textContent = label;
  b.setAttribute("aria-label", ariaLabel);
  b.title = ariaLabel;
  b.addEventListener("click", onClick);
  return b;
}

// ---------- Inline page editor -------------------------------------

function editProgress(entry, button) {
  const input = document.createElement("input");
  input.type = "number";
  input.min = "0";
  input.max = String(entry.totalPages);
  input.step = "1";
  input.value = String(entry.currentPage);
  input.className = "reading-row__page-input";
  input.setAttribute("aria-label", "Current page (Enter to save, Esc to cancel)");
  button.replaceWith(input);
  input.focus();
  input.select();

  let settled = false;
  const commit = () => {
    if (settled) return;
    settled = true;
    setProgress(entry.id, Number(input.value));
  };
  const cancel = () => {
    if (settled) return;
    settled = true;
    render();
  };

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); commit(); }
    else if (e.key === "Escape") { e.preventDefault(); cancel(); }
  });
  input.addEventListener("blur", commit);
}

// ---------- Mutations ---------------------------------------------

function bumpProgress(id, delta) {
  const e = items.find(x => x.id === id);
  if (!e) return;
  setProgress(id, e.currentPage + delta);
}

function setProgress(id, value) {
  const idx = items.findIndex(x => x.id === id);
  if (idx < 0) return;
  items[idx] = applyProgress(items[idx], value);
  persist();
  render();
}

function removeEntry(id) {
  items = items.filter(e => e.id !== id);
  persist();
  render();
}

// ---------- Boot ---------------------------------------------------

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
