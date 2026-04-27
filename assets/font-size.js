/* Font-size control — multiplies the root font-size via the
   `--font-scale` CSS custom property, persisted in localStorage so it
   survives navigation. Mirrors theme.js: applies the stored value
   synchronously from <head> to avoid a flash, then wires up A−/A+
   buttons after DOM is ready. */
(function () {
  var STORAGE_KEY = "luca-font-scale";
  var STEP = 0.1;
  var MIN = 0.7;
  var MAX = 1.5;
  var root = document.documentElement;

  function getStored() {
    try {
      var v = parseFloat(localStorage.getItem(STORAGE_KEY));
      return isFinite(v) ? v : null;
    } catch (e) { return null; }
  }
  function setStored(v) {
    try { localStorage.setItem(STORAGE_KEY, String(v)); } catch (e) {}
  }
  function clampScale(v) { return Math.max(MIN, Math.min(MAX, v)); }
  function round(v) { return Math.round(v * 100) / 100; }
  function apply(scale) {
    root.style.setProperty("--font-scale", String(scale));
  }

  /* Initial application before <body> renders. */
  var current = getStored();
  if (current === null) current = 1;
  current = clampScale(current);
  apply(current);

  function bind() {
    var btns = document.querySelectorAll("[data-font-size]");
    btns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var action = btn.getAttribute("data-font-size");
        if (action === "inc") current = clampScale(round(current + STEP));
        else if (action === "dec") current = clampScale(round(current - STEP));
        else if (action === "reset") current = 1;
        apply(current);
        setStored(current);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
}());
