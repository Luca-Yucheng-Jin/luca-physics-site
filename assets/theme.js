/* Page chrome: theme toggle, back-to-top button, and per-note sidebar.
   Theme application runs synchronously from <head> to set data-theme before
   paint. Other features attach on DOMContentLoaded. */
(function () {
  var STORAGE_KEY = "luca-theme";
  var root = document.documentElement;

  function getStored() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }
  function setStored(v) {
    try { localStorage.setItem(STORAGE_KEY, v); } catch (e) {}
  }
  function systemPref() {
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark" : "light";
  }
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
  }

  /* Initial application — runs before <body> renders, so no flash. */
  applyTheme(getStored() || systemPref());

  /* Follow system preference until the user makes an explicit choice. */
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    var listener = function (e) {
      if (!getStored()) applyTheme(e.matches ? "dark" : "light");
    };
    if (mq.addEventListener) mq.addEventListener("change", listener);
    else if (mq.addListener) mq.addListener(listener);
  }

  function bindThemeToggles() {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var current = root.getAttribute("data-theme") || "light";
        var next = current === "dark" ? "light" : "dark";
        applyTheme(next);
        setStored(next);
        btn.setAttribute(
          "aria-label",
          next === "dark" ? "Switch to light theme" : "Switch to dark theme"
        );
      });
    });
  }

  /* ---------- Back-to-top ----------
     Visible once the user has scrolled past ~one viewport. Uses an
     IntersectionObserver on a sentinel pinned to the top of the document
     rather than scroll events — fires reliably across browsers. */
  function buildBackToTop() {
    var btn = document.createElement("button");
    btn.className = "back-to-top";
    btn.type = "button";
    btn.setAttribute("aria-label", "Back to top");
    btn.title = "Back to top";
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true">' +
        '<path d="M12 19V5M5 12l7-7 7 7"/>' +
      '</svg>';
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    document.body.appendChild(btn);

    var sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText =
      "position:absolute;top:0;left:0;width:1px;height:400px;" +
      "pointer-events:none;visibility:hidden;";
    document.body.insertBefore(sentinel, document.body.firstChild);

    if (!("IntersectionObserver" in window)) {
      btn.classList.add("is-visible");
      return;
    }
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        btn.classList.toggle("is-visible", !e.isIntersecting);
      });
    }, { threshold: 0 });
    obs.observe(sentinel);
  }

  /* ---------- Note sidebar ---------- */
  function buildSidebar() {
    var note = document.querySelector("main.note");
    if (!note) return;
    var headings = note.querySelectorAll("h2[id], h3[id]");
    if (headings.length < 2) return;

    var aside = document.createElement("aside");
    aside.className = "note__sidebar";
    aside.setAttribute("aria-label", "Page contents");

    var label = document.createElement("div");
    label.className = "note__sidebar-label";
    label.textContent = "On this page";
    aside.appendChild(label);

    var list = document.createElement("ol");
    list.className = "note__sidebar-list";

    var links = [];
    headings.forEach(function (h) {
      var li = document.createElement("li");
      li.className = "sidebar-" + h.tagName.toLowerCase();
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent.replace(/^§\s*/, "").trim();
      a.dataset.target = h.id;
      li.appendChild(a);
      list.appendChild(li);
      links.push(a);
    });

    aside.appendChild(list);
    document.body.appendChild(aside);

    /* Highlight whichever heading is closest to the top of the viewport. */
    if (!("IntersectionObserver" in window)) return;
    var visible = new Set();
    var headingOrder = Array.prototype.slice.call(headings);

    function setActive() {
      var current = null;
      for (var i = 0; i < headingOrder.length; i++) {
        if (visible.has(headingOrder[i].id)) { current = headingOrder[i].id; break; }
      }
      links.forEach(function (a) {
        a.classList.toggle("is-active", a.dataset.target === current);
      });
    }

    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) visible.add(e.target.id);
        else visible.delete(e.target.id);
      });
      setActive();
    }, { rootMargin: "-80px 0px -60% 0px", threshold: 0 });
    headingOrder.forEach(function (h) { obs.observe(h); });
  }

  function bind() {
    bindThemeToggles();
    buildBackToTop();
    buildSidebar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
