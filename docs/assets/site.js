/* Ingredient Lens documentation — behaviour. No dependencies; works from file:// and from a web server. */
(function () {
  "use strict";
  var root = document.documentElement;
  var body = document.body;

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  /* ---------------------------------------------------------------- theme */
  var themeButton = document.querySelector("[data-theme-toggle]");
  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t === "light" || t === "dark") return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function labelTheme() {
    if (!themeButton) return;
    var dark = currentTheme() === "dark";
    themeButton.setAttribute("aria-pressed", String(dark));
    themeButton.querySelector("[data-theme-label]").textContent = dark ? "Light mode" : "Dark mode";
  }
  if (themeButton) {
    themeButton.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      store("il-theme", next);
      labelTheme();
      renderDiagrams(true);
    });
    labelTheme();
  }

  /* ---------------------------------------------------------------- header shadow + reading progress */
  var header = document.querySelector(".site-header");
  var bar = document.querySelector(".progress span");
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    if (header) header.classList.toggle("is-scrolled", y > 8);
    if (bar) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (max > 0 ? Math.min(100, (y / max) * 100) : 0) + "%";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------------------------------------------------------------- mobile drawer */
  var menuButton = document.querySelector(".menu-button");
  var backdrop = document.querySelector(".drawer-backdrop");
  var sidebar = document.getElementById("sidebar");
  function setDrawer(open) {
    body.classList.toggle("drawer-open", open);
    if (menuButton) menuButton.setAttribute("aria-expanded", String(open));
    if (open && sidebar) { var first = sidebar.querySelector("a"); if (first) first.focus(); }
    if (!open && menuButton && document.activeElement && sidebar && sidebar.contains(document.activeElement)) menuButton.focus();
  }
  if (menuButton) menuButton.addEventListener("click", function () { setDrawer(!body.classList.contains("drawer-open")); });
  if (backdrop) backdrop.addEventListener("click", function () { setDrawer(false); });

  /* ---------------------------------------------------------------- table of contents scroll-spy */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var targets = tocLinks.map(function (a) { return document.getElementById(decodeURIComponent(a.hash.slice(1))); });
    var visible = {};
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
      var active = null;
      for (var i = 0; i < targets.length; i++) {
        var t = targets[i];
        if (!t) continue;
        if (t.getBoundingClientRect().top < window.innerHeight * 0.35) active = t.id;
      }
      tocLinks.forEach(function (a) {
        var on = active && decodeURIComponent(a.hash.slice(1)) === active;
        a.classList.toggle("is-active", !!on);
        if (on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
      });
    }, { rootMargin: "0px 0px -55% 0px", threshold: [0, 1] });
    targets.forEach(function (t) { if (t) observer.observe(t); });
  }

  /* ---------------------------------------------------------------- heading anchors: copy link */
  var toast = document.querySelector(".toast");
  function showToast(text) {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add("is-visible");
    clearTimeout(showToast.t);
    showToast.t = setTimeout(function () { toast.classList.remove("is-visible"); }, 1600);
  }
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a.anchor");
    if (!a) return;
    var url = location.href.split("#")[0] + a.getAttribute("href");
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(function () { showToast("Link copied"); }, function () {});
    }
  });

  /* ---------------------------------------------------------------- search */
  var dialog = document.querySelector(".search");
  var input = dialog && dialog.querySelector("input");
  var list = dialog && dialog.querySelector(".search-results");
  var openers = document.querySelectorAll("[data-search-open]");
  var lastFocus = null;
  var selected = -1;
  var base = body.getAttribute("data-base") || "";

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function norm(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function highlight(text, terms) {
    var out = escapeHtml(text);
    terms.forEach(function (t) {
      if (t.length < 2) return;
      var re = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }
  function snippet(text, terms) {
    var n = norm(text);
    var at = terms.length ? n.indexOf(terms[0]) : -1;
    var start = Math.max(0, at - 60);
    var s = text.slice(start, start + 170);
    return (start > 0 ? "… " : "") + s + (start + 170 < text.length ? " …" : "");
  }
  function runSearch(q) {
    var data = window.__SEARCH__ || [];
    var terms = norm(q).split(/\s+/).filter(Boolean);
    list.innerHTML = "";
    selected = -1;
    if (!terms.length) { list.innerHTML = '<li class="search-empty">Type to search the documentation.</li>'; return; }
    var scored = [];
    data.forEach(function (d) {
      var t = norm(d.s || ""), p = norm(d.p || ""), x = norm(d.x || "");
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var term = terms[i], hit = 0;
        if (t.indexOf(term) > -1) hit += 8;
        if (p.indexOf(term) > -1) hit += 3;
        if (x.indexOf(term) > -1) hit += 1;
        if (!hit) return;
        score += hit;
      }
      scored.push({ d: d, score: score });
    });
    scored.sort(function (a, b) { return b.score - a.score; });
    if (!scored.length) { list.innerHTML = '<li class="search-empty">No results for “' + escapeHtml(q) + '”.</li>'; return; }
    scored.slice(0, 12).forEach(function (r, i) {
      var li = document.createElement("li");
      li.setAttribute("role", "presentation");
      li.innerHTML = '<a role="option" id="sr-' + i + '" href="' + base + r.d.u + '">' +
        '<span class="r-page">' + escapeHtml(r.d.p) + '</span>' +
        '<span class="r-title">' + highlight(r.d.s || r.d.p, terms) + '</span>' +
        '<span class="r-text">' + highlight(snippet(r.d.x || "", terms), terms) + '</span></a>';
      list.appendChild(li);
    });
  }
  function select(i) {
    var items = list.querySelectorAll("a");
    if (!items.length) return;
    selected = (i + items.length) % items.length;
    items.forEach(function (a, k) { a.setAttribute("aria-selected", String(k === selected)); });
    items[selected].scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", items[selected].id);
  }
  function openSearch() {
    if (!dialog) return;
    lastFocus = document.activeElement;
    dialog.hidden = false;
    body.style.overflow = "hidden";
    input.value = "";
    runSearch("");
    setTimeout(function () { input.focus(); }, 10);
  }
  function closeSearch() {
    if (!dialog || dialog.hidden) return;
    dialog.hidden = true;
    body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }
  Array.prototype.forEach.call(openers, function (b) { b.addEventListener("click", openSearch); });
  if (dialog) {
    dialog.addEventListener("click", function (ev) { if (ev.target === dialog) closeSearch(); });
    input.addEventListener("input", function () { runSearch(input.value); });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown") { ev.preventDefault(); select(selected + 1); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); select(selected - 1); }
      else if (ev.key === "Enter") {
        var items = list.querySelectorAll("a");
        if (items.length) { ev.preventDefault(); (items[selected >= 0 ? selected : 0]).click(); }
      }
    });
  }
  document.addEventListener("keydown", function (ev) {
    var typing = /^(input|textarea|select)$/i.test((ev.target.tagName || "")) || ev.target.isContentEditable;
    if ((ev.key === "k" || ev.key === "K") && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); openSearch(); }
    else if (ev.key === "/" && !typing) { ev.preventDefault(); openSearch(); }
    else if (ev.key === "Escape") { closeSearch(); setDrawer(false); }
  });

  /* ---------------------------------------------------------------- diagrams (Mermaid, loaded only where used) */
  var sources = [];
  document.querySelectorAll("pre.mermaid").forEach(function (el) { sources.push(el.textContent); });
  // Mermaid renders on window load with its default theme unless told not to; stop that before it happens.
  if (window.mermaid) window.mermaid.initialize({ startOnLoad: false });
  function renderDiagrams(rerender) {
    if (!sources.length || !window.mermaid) return;
    var dark = currentTheme() === "dark";
    var vars = dark ? {
      background: "#0E262C", primaryColor: "#12424B", primaryTextColor: "#E8F6F7", primaryBorderColor: "#38B6CC",
      lineColor: "#7FD3E2", secondaryColor: "#3D3810", secondaryTextColor: "#FFF7B3", tertiaryColor: "#10282E",
      edgeLabelBackground: "#0E262C", textColor: "#D6E4E6", fontFamily: "Signika, Segoe UI, sans-serif", fontSize: "15px"
    } : {
      background: "#F1F6F6", primaryColor: "#D5FAFE", primaryTextColor: "#00596B", primaryBorderColor: "#27787F",
      lineColor: "#27787F", secondaryColor: "#FFF7B3", secondaryTextColor: "#3B3B3B", tertiaryColor: "#FFFFFF",
      edgeLabelBackground: "#F1F6F6", textColor: "#3B3B3B", fontFamily: "Signika, Segoe UI, sans-serif", fontSize: "15px"
    };
    window.mermaid.initialize({ startOnLoad: false, theme: "base", themeVariables: vars, securityLevel: "strict",
      flowchart: { curve: "basis", padding: 14 } });
    var nodes = document.querySelectorAll("pre.mermaid");
    nodes.forEach(function (el, i) {
      if (rerender) { el.removeAttribute("data-processed"); el.textContent = sources[i]; }
    });
    try { window.mermaid.run({ nodes: nodes }); } catch (e) { /* diagrams stay as text */ }
  }
  window.addEventListener("load", function () { renderDiagrams(false); });
})();
