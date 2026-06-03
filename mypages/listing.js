(function () {
  var FOLDER = "mypages";
  var PER_PAGE = parseInt("10", 10) || 10;
  var root = document.getElementById("mypage-list");
  if (!root) return;
  var qEl = root.querySelector("#mp-q");
  var itemsEl = root.querySelector("#mp-items");
  var emptyEl = root.querySelector("#mp-empty");
  var pagerEl = root.querySelector("#mp-pager");
  var countEl = root.querySelector("#mp-count");

  var all = [];
  var filtered = [];
  var page = 1;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function highlight(text, q) {
    text = esc(text);
    if (!q) return text;
    try {
      var re = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      return text.replace(re, "<mark>$1</mark>");
    } catch (e) { return text; }
  }
  function fmtDate(iso) { return iso ? String(iso).slice(0, 10) : ""; }

  function applyFilter() {
    var q = qEl.value.trim().toLowerCase();
    filtered = !q ? all.slice() : all.filter(function (p) {
      return ((p.title || "") + " " + (p.excerpt || "") + " " + (p.text || "")).toLowerCase().indexOf(q) !== -1;
    });
    page = 1;
    render();
  }

  function render() {
    var q = qEl.value.trim();
    var total = filtered.length;
    var pages = Math.max(1, Math.ceil(total / PER_PAGE));
    if (page > pages) page = pages;
    countEl.textContent = total ? (total + (total === 1 ? " post" : " posts")) : "";
    emptyEl.hidden = total !== 0;

    var start = (page - 1) * PER_PAGE;
    var slice = filtered.slice(start, start + PER_PAGE);
    itemsEl.innerHTML = slice.map(function (p) {
      return '<li><a href="' + esc(p.url) + '">' + highlight(p.title || p.slug, q) + "</a>"
        + '<div class="mp-meta">' + fmtDate(p.created)
        + (p.updated && p.updated !== p.created ? " · updated " + fmtDate(p.updated) : "") + "</div>"
        + '<p class="mp-excerpt">' + highlight((p.excerpt || "").slice(0, 180), q) + "</p></li>";
    }).join("");

    pagerEl.innerHTML = "";
    if (pages > 1) {
      var mk = function (label, p, opts) {
        opts = opts || {};
        var b = document.createElement("button");
        b.textContent = label;
        if (opts.active) b.className = "active";
        if (opts.disabled) b.disabled = true;
        else b.onclick = function () { page = p; render(); window.scrollTo({ top: root.offsetTop - 20, behavior: "smooth" }); };
        pagerEl.appendChild(b);
      };
      mk("‹", page - 1, { disabled: page === 1 });
      for (var i = 1; i <= pages; i++) mk(String(i), i, { active: i === page });
      mk("›", page + 1, { disabled: page === pages });
    }
  }

  var url = "/" + FOLDER + "/index.json?v=" + (Date.now());
  fetch(url, { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      all = (data.pages || []).slice().sort(function (a, b) {
        return String(b.created).localeCompare(String(a.created));
      });
      filtered = all.slice();
      render();
    })
    .catch(function (e) {
      emptyEl.hidden = false;
      emptyEl.textContent = "Couldn't load the list (" + e.message + ").";
    });

  qEl.addEventListener("input", applyFilter);
})();