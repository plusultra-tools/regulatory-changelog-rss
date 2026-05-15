// Vanilla JS keyword + source filter for the EU Regulatory Changelog static site.
// Reads data-keywords and data-source attributes set by aggregator.py's emit_html().
(function () {
  "use strict";
  var kwSel = document.getElementById("kw");
  var srcSel = document.getElementById("src");
  var countEl = document.getElementById("count");
  var items = Array.prototype.slice.call(document.querySelectorAll("#items .item"));

  function matches(item, kw, src) {
    if (src && item.getAttribute("data-source") !== src) return false;
    if (!kw) return true;
    var kws = (item.getAttribute("data-keywords") || "").split(/\s+/);
    return kws.indexOf(kw) !== -1;
  }

  function apply() {
    var kw = kwSel ? kwSel.value : "";
    var src = srcSel ? srcSel.value : "";
    var visible = 0;
    items.forEach(function (it) {
      if (matches(it, kw, src)) {
        it.style.display = "";
        visible += 1;
      } else {
        it.style.display = "none";
      }
    });
    if (countEl) countEl.textContent = visible + " / " + items.length + " shown";
  }

  if (kwSel) kwSel.addEventListener("change", apply);
  if (srcSel) srcSel.addEventListener("change", apply);
  apply();
})();
