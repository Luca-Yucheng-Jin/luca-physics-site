/* Theme toggle — light / dark.
   Runs synchronously from <head> to set data-theme before paint, then wires
   up any [data-theme-toggle] button after DOM is ready. */
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
  function apply(theme) {
    root.setAttribute("data-theme", theme);
  }

  /* Initial application — runs before <body> renders, so no flash. */
  var initial = getStored() || systemPref();
  apply(initial);

  /* Follow system preference until the user makes an explicit choice. */
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    var listener = function (e) {
      if (!getStored()) apply(e.matches ? "dark" : "light");
    };
    if (mq.addEventListener) mq.addEventListener("change", listener);
    else if (mq.addListener) mq.addListener(listener);
  }

  function bind() {
    var btns = document.querySelectorAll("[data-theme-toggle]");
    btns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var current = root.getAttribute("data-theme") || "light";
        var next = current === "dark" ? "light" : "dark";
        apply(next);
        setStored(next);
        btn.setAttribute(
          "aria-label",
          next === "dark" ? "Switch to light theme" : "Switch to dark theme"
        );
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
