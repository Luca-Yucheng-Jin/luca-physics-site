/* Once TikZJax finishes rendering each <script type="text/tikz"> into an
   SVG, scale the SVG up by editing its width/height attributes so the
   diagram is readable in-page. We avoid CSS `zoom` because that
   inflates the surrounding empty space; doubling the SVG's pt
   attributes scales the diagram while keeping TikZJax's
   aspect-ratio wrapper intact. */
(function () {
  var STANDALONE_SCALE = 2.0;
  var EQ_ROW_SCALE = 1.5;

  function resizeOne(figure) {
    if (figure.dataset.tikzResized) return;
    var svg = figure.querySelector('svg');
    if (!svg) return;
    var wAttr = svg.getAttribute('width');
    var hAttr = svg.getAttribute('height');
    if (!wAttr || !hAttr) return;
    var w = parseFloat(wAttr);
    var h = parseFloat(hAttr);
    if (!isFinite(w) || !isFinite(h) || w <= 0) return;

    var inEqRow = !!figure.closest('.equation-row');
    var scale = inEqRow ? EQ_ROW_SCALE : STANDALONE_SCALE;
    svg.setAttribute('width',  (w * scale).toFixed(4) + 'pt');
    svg.setAttribute('height', (h * scale).toFixed(4) + 'pt');
    figure.dataset.tikzResized = '1';
  }

  function tick() {
    var figs = document.querySelectorAll('figure.tikz-figure');
    figs.forEach(resizeOne);
  }

  // TikZJax renders SVGs progressively, so we re-tick for ~30s to catch
  // any late renders, then stop.
  var ticks = 0;
  var iv = setInterval(function () {
    tick();
    if (++ticks > 60) clearInterval(iv);
  }, 500);
  document.addEventListener('DOMContentLoaded', tick);
  window.addEventListener('load', tick);
}());
