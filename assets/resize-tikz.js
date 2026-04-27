/* Once TikZJax finishes rendering each <script type="text/tikz"> into an
   SVG, scale the diagram up so it's readable in-page.

   What TikZJax actually emits inside <figure.tikz-figure> is:
       <div style="display:flex; width:Wpt; height:Hpt">  <-- aspect-ratio wrapper
         <div class="page" style="position:relative; width:100%; height:0pt">
           <svg viewBox=... style="position:absolute; top:0; left:0">
             <g>...</g>
           </svg>
         </div>
       </div>
   The visible diagram size is controlled by the OUTER wrapper's inline
   `width` and `height`, both in `pt`. The SVG inside is positioned
   absolute and scales to fill the wrapper via viewBox. So to resize the
   diagram, we patch the wrapper's inline pt values.

   The scale is tied to the root font-size so diagrams grow and shrink
   with the surrounding text — the page keeps its A4-like proportions
   at every viewport. */
(function () {
  var BASE_FONT = 16;            // baseline px; matches the floor of the html font-size clamp
  var STANDALONE_BASE = 2.0;
  var EQ_ROW_BASE = 1.5;

  function currentScale(inEqRow) {
    var root = parseFloat(getComputedStyle(document.documentElement).fontSize) || BASE_FONT;
    var ratio = root / BASE_FONT;
    return (inEqRow ? EQ_ROW_BASE : STANDALONE_BASE) * ratio;
  }

  function resizeOne(figure) {
    var wrapper = figure.querySelector(':scope > div');
    if (!wrapper) return;
    var style = wrapper.getAttribute('style') || '';
    // Cache the original (TikZJax-emitted) pt size on first encounter so
    // viewport resizes don't compound.
    if (!figure.dataset.tikzOrigW) {
      var wMatch = style.match(/width:\s*([\d.]+)pt/);
      var hMatch = style.match(/height:\s*([\d.]+)pt/);
      if (!wMatch || !hMatch) return;
      figure.dataset.tikzOrigW = wMatch[1];
      figure.dataset.tikzOrigH = hMatch[1];
    }
    var w = parseFloat(figure.dataset.tikzOrigW);
    var h = parseFloat(figure.dataset.tikzOrigH);
    if (!isFinite(w) || !isFinite(h) || w <= 0) return;
    var inEqRow = !!figure.closest('.equation-row');
    var scale = currentScale(inEqRow);
    var newW = (w * scale).toFixed(4) + 'pt';
    var newH = (h * scale).toFixed(4) + 'pt';
    var newStyle = style
      .replace(/width:\s*[\d.]+pt/, 'width: ' + newW)
      .replace(/height:\s*[\d.]+pt/, 'height: ' + newH);
    wrapper.setAttribute('style', newStyle);
  }

  function tick() {
    document.querySelectorAll('figure.tikz-figure').forEach(resizeOne);
  }

  // TikZJax renders SVGs progressively; re-tick for ~30s to catch late
  // renders, then stop polling.
  var ticks = 0;
  var iv = setInterval(function () {
    tick();
    if (++ticks > 60) clearInterval(iv);
  }, 500);
  document.addEventListener('DOMContentLoaded', tick);
  window.addEventListener('load', tick);

  // On viewport changes, re-scale (debounced) so diagrams track the
  // root font-size as it shifts under the clamp/vw rules.
  var rt;
  window.addEventListener('resize', function () {
    if (rt) cancelAnimationFrame(rt);
    rt = requestAnimationFrame(tick);
  });
}());
