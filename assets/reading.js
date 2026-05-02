/* Reading list — DOM wiring.

   Two display modes:
     - Read mode (default): renders assets/reading-data.json, no edit UI.
       Anyone visiting the site sees this.
     - Edit mode: unlocked with a passphrase (hash in reading-config.js).
       Edits go to localStorage as a working copy. A Download button
       exports the working copy as reading-data.json so the owner can
       commit it back to the repo. */

import {
  loadItems,
  saveItems,
  loadPublished,
  makeEntry,
  applyProgress,
  sortEntries,
  stats,
  status,
  sha256Hex,
  serializeForExport,
  isDirty,
  publishToGitHub,
} from "./reading-store.js";
import {
  PASSPHRASE_HASH,
  DEFAULT_PASSPHRASE_HASH,
  GITHUB_REPO,
  GITHUB_BRANCH,
  PUBLISHED_PATH,
} from "./reading-config.js";

const SESSION_KEY = "reading-list:unlocked";
const TOKEN_KEY   = "reading-list:gh-token";

let publishedItems = [];
let workingItems = [];
let unlocked = false;
let activeFilter = "all";

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* Console helper: lets the owner generate a fresh passphrase hash
   without needing to know how SubtleCrypto works. Available always,
   not just in edit mode. */
if (typeof window !== "undefined") {
  window.ReadingDigest = sha256Hex;
}

// ---------- Init ---------------------------------------------------

async function init() {
  unlocked = sessionStorage.getItem(SESSION_KEY) === "true";

  publishedItems = await loadPublished();
  workingItems = unlocked ? loadItems() : [];
  if (unlocked && workingItems.length === 0 && publishedItems.length > 0) {
    workingItems = publishedItems.map(e => ({ ...e }));
    saveItems(workingItems);
  }

  bindAddForm();
  bindFilters();
  bindToolbar();

  if (new URL(location.href).searchParams.has("edit") && !unlocked) {
    promptUnlock();
  }

  render();
}

function activeItems() { return unlocked ? workingItems : publishedItems; }

function persist() {
  if (!unlocked) return;
  saveItems(workingItems);
}

// ---------- Toolbar (lock / download) ------------------------------

function bindToolbar() {
  $("#reading-lock").addEventListener("click", () => {
    if (unlocked) lock();
    else promptUnlock();
  });
  $("#reading-publish").addEventListener("click", publish);
  $("#reading-download").addEventListener("click", downloadPublished);
  $("#reading-forget-token").addEventListener("click", forgetToken);
}

async function promptUnlock() {
  if (!PASSPHRASE_HASH || PASSPHRASE_HASH.length !== 64) {
    alert(
      "Edit gate not configured.\n\n" +
      "Open the developer console and run:\n\n" +
      "    await window.ReadingDigest(\"your-passphrase\")\n\n" +
      "Paste the 64-char result into PASSPHRASE_HASH in " +
      "assets/reading-config.js, then redeploy."
    );
    return;
  }
  // Trim leading/trailing whitespace and zero-width characters —
  // autocorrect, mobile keyboards, and clipboard managers love to sneak
  // these in, and SHA-256 is unforgiving about them.
  const raw = window.prompt("Passphrase to unlock edit mode:");
  if (raw == null) return;
  // \s plus the common zero-width sneak-ins (ZWSP, ZWNJ, ZWJ, BOM).
  // Trimmed from both ends only — interior whitespace is preserved in
  // case the passphrase legitimately contains a space.
  const TRIM_RE = new RegExp(
    "^[\\s\u200B\u200C\u200D\uFEFF]+|[\\s\u200B\u200C\u200D\uFEFF]+$",
    "g"
  );
  const phrase = raw.replace(TRIM_RE, "");
  if (!phrase) return;
  const hash = await sha256Hex(phrase);
  if (hash !== PASSPHRASE_HASH) {
    alert("Incorrect passphrase.");
    return;
  }
  unlocked = true;
  sessionStorage.setItem(SESSION_KEY, "true");
  workingItems = loadItems();
  if (workingItems.length === 0 && publishedItems.length > 0) {
    workingItems = publishedItems.map(e => ({ ...e }));
    saveItems(workingItems);
  }
  render();
}

function lock() {
  unlocked = false;
  sessionStorage.removeItem(SESSION_KEY);
  render();
}

// ---------- GitHub publish flow ------------------------------------

function getToken()  { try { return localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; } }
function setToken(t) { try { localStorage.setItem(TOKEN_KEY, t); } catch {} }
function clearToken(){ try { localStorage.removeItem(TOKEN_KEY); } catch {} }

function forgetToken() {
  if (!getToken()) { setStatus("No token stored.", "info"); return; }
  if (!confirm("Forget the saved GitHub token from this browser?")) return;
  clearToken();
  setStatus("Token forgotten. You'll be asked for it the next time you publish.", "info");
  render();
}

async function publish() {
  if (!unlocked) return;
  let token = getToken();
  if (!token) {
    const raw = window.prompt(
      "Paste a GitHub fine-grained personal access token.\n\n" +
      "Scope: Contents (Read and write) on this repo only.\n" +
      "It will be stored unencrypted in this browser's localStorage.\n" +
      "Click 'Forget token' in the toolbar to clear it."
    );
    if (raw == null) return;
    const TRIM_RE = new RegExp(
      "^[\\s\u200B\u200C\u200D\uFEFF]+|[\\s\u200B\u200C\u200D\uFEFF]+$",
      "g"
    );
    token = raw.replace(TRIM_RE, "");
    if (!token) return;
    setToken(token);
  }

  setStatus("Publishing to GitHub…", "info");
  setPublishBusy(true);

  const result = await publishToGitHub({
    items: workingItems,
    token,
    repo:   GITHUB_REPO,
    branch: GITHUB_BRANCH,
    path:   PUBLISHED_PATH,
  });

  setPublishBusy(false);

  if (!result.ok) {
    if (result.status === 401 || result.status === 403) {
      clearToken();
      setStatus(
        `${result.message || "Token rejected"} — token cleared. Click Publish again to paste a new one.`,
        "error"
      );
    } else if (result.status === 409) {
      setStatus(
        "Conflict: someone else updated the file. Reload the page so the published view catches up, then publish again.",
        "error"
      );
    } else {
      setStatus(`Publish failed: ${result.message}`, "error");
    }
    render();
    return;
  }

  // Success — published view now matches working copy.
  publishedItems = workingItems.map(e => ({ ...e }));
  const shortSha = result.commitSha ? ` (${result.commitSha.slice(0, 7)})` : "";
  setStatus(
    `Published${shortSha}. GitHub Pages will redeploy in ~30 seconds.`,
    "success"
  );
  render();
}

function setStatus(msg, kind = "info") {
  const el = $("#reading-status");
  if (!el) return;
  el.textContent = msg;
  el.dataset.kind = kind;
  el.hidden = false;
  if (kind === "info") {
    // Auto-clear info messages after a few seconds.
    clearTimeout(setStatus._t);
    setStatus._t = setTimeout(() => {
      if (el.textContent === msg) { el.hidden = true; el.textContent = ""; }
    }, 4500);
  }
  if (kind === "success") {
    clearTimeout(setStatus._t);
    setStatus._t = setTimeout(() => {
      if (el.textContent === msg) { el.hidden = true; el.textContent = ""; }
    }, 6500);
  }
}

function setPublishBusy(busy) {
  const btn = $("#reading-publish");
  btn.disabled = busy;
  btn.classList.toggle("is-busy", busy);
}

function downloadPublished() {
  const blob = new Blob([serializeForExport(workingItems)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "reading-data.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------- Add form ----------------------------------------------

function bindAddForm() {
  const form = $("#reading-add");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!unlocked) return;
    const fd = new FormData(form);
    const title = String(fd.get("title") || "").trim();
    const author = String(fd.get("author") || "").trim();
    const totalPages = Number(String(fd.get("totalPages") || "").trim());

    if (!title) return flagError(form.elements.title, "Title is required");
    if (!Number.isFinite(totalPages) || !Number.isInteger(totalPages) || totalPages <= 0) {
      return flagError(form.elements.totalPages, "Pages must be a positive integer");
    }

    try {
      workingItems.push(makeEntry({ title, author, totalPages }));
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

// ---------- Filter -------------------------------------------------

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

function visibleItems() {
  const sorted = sortEntries(activeItems());
  if (activeFilter === "reading") return sorted.filter(e => status(e) !== "finished");
  if (activeFilter === "done")    return sorted.filter(e => status(e) === "finished");
  return sorted;
}

// ---------- Render -------------------------------------------------

function render() {
  document.body.classList.toggle("reading-locked",   !unlocked);
  document.body.classList.toggle("reading-unlocked",  unlocked);

  const lockBtn = $("#reading-lock");
  lockBtn.setAttribute("aria-pressed", unlocked ? "true" : "false");
  lockBtn.title = unlocked
    ? "Lock — return to read-only view"
    : "Edit — enter passphrase to unlock";
  $("#reading-lock-label").textContent = unlocked ? "Lock" : "Edit";

  const dirty = unlocked && isDirty(workingItems, publishedItems);

  const pub = $("#reading-publish");
  pub.hidden = !unlocked;
  pub.classList.toggle("is-dirty", dirty);
  $("#reading-publish-label").textContent = dirty ? "Publish ●" : "Publish";

  const dl = $("#reading-download");
  dl.hidden = !unlocked;

  const forget = $("#reading-forget-token");
  forget.hidden = !(unlocked && getToken());

  const warn = $("#reading-default-warn");
  warn.hidden = !(unlocked && PASSPHRASE_HASH === DEFAULT_PASSPHRASE_HASH);

  $("#reading-add").hidden = !unlocked;

  renderStats();
  renderList();
}

function renderStats() {
  const wrap = $("#reading-stats");
  const items = activeItems();
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

  const items = activeItems();
  if (!items.length) {
    list.appendChild(emptyState(
      unlocked
        ? "Nothing on the pile yet — add a book or paper above to start tracking it."
        : "No published entries yet."
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

  const ctrl = document.createElement("div");
  ctrl.className = "reading-row__ctrl";

  const pages = document.createElement("button");
  pages.type = "button";
  pages.className = "reading-row__pages";
  pages.setAttribute("aria-label", "Edit current page");
  pages.title = "Click to edit current page";
  pages.textContent = entry.currentPage + " / " + entry.totalPages;
  if (unlocked) {
    pages.addEventListener("click", () => editProgress(entry, pages));
  } else {
    pages.disabled = true;
  }
  ctrl.appendChild(pages);

  if (unlocked) {
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
  }

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
  const e = workingItems.find(x => x.id === id);
  if (!e) return;
  setProgress(id, e.currentPage + delta);
}

function setProgress(id, value) {
  const idx = workingItems.findIndex(x => x.id === id);
  if (idx < 0) return;
  workingItems[idx] = applyProgress(workingItems[idx], value);
  persist();
  render();
}

function removeEntry(id) {
  const reduced = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const row = document.querySelector('.reading-row[data-id="' + cssEscape(id) + '"]');

  let done = false;
  function finalize() {
    if (done) return;
    done = true;
    workingItems = workingItems.filter(e => e.id !== id);
    persist();
    render();
  }

  if (!reduced && row) {
    row.classList.add("is-leaving");
    row.addEventListener("animationend", finalize, { once: true });
    // Fallback in case the animationend event doesn't fire (e.g. the
    // tab is backgrounded mid-animation).
    setTimeout(finalize, 320);
    return;
  }
  finalize();
}

function cssEscape(s) {
  if (window.CSS && CSS.escape) return CSS.escape(s);
  return String(s).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

// ---------- Boot ---------------------------------------------------

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
