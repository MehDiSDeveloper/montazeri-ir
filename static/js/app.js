/* ==========================================================================
   montazeri.ir — progressive enhancement only.

   The server already sent a finished page. Nothing in this file is required
   for the site to be read, navigated or submitted: turn JavaScript off and
   every link, form and page still works. What this adds is the difference
   between "it works" and "it feels considered".

   No framework, no build step, no dependency. One file, one IIFE per concern.
   ========================================================================== */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var STORE_THEME = "montazeri-theme";

  /* ── small helpers ─────────────────────────────────────────────────── */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  var toastTimer = null;
  function toast(text) {
    var old = $(".toast");
    if (old) old.remove();
    var el = document.createElement("div");
    el.className = "toast";
    el.setAttribute("role", "status");
    el.textContent = text;
    document.body.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.remove(); }, 2200);
  }

  /* ══ theme ═════════════════════════════════════════════════════════════
     Three states, not two: system / light / dark. "system" removes the
     attribute so the media query in the stylesheet decides. The same key is
     read by the pre-paint snippet in the <head> of base.html — if you rename
     it here, rename it there, or the page flashes the wrong theme for a frame.
     ══════════════════════════════════════════════════════════════════════ */
  function readTheme() {
    try { return localStorage.getItem(STORE_THEME) || "system"; } catch (e) { return "system"; }
  }
  function applyTheme(value) {
    if (value === "system") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", value);
    try { localStorage.setItem(STORE_THEME, value); } catch (e) { /* private mode */ }
    $$("[data-theme-choice]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.themeChoice === value));
    });
    var meta = $('meta[name="theme-color"]');
    if (meta) {
      var dark = value === "dark" || (value === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
      meta.setAttribute("content", dark ? "#101613" : "#f7f3eb");
    }
  }
  function initTheme() {
    applyTheme(readTheme());
    $$("[data-theme-choice]").forEach(function (btn) {
      btn.addEventListener("click", function () { applyTheme(btn.dataset.themeChoice); });
    });
    // The cycling single button in the header.
    var cycle = $("[data-theme-cycle]");
    if (cycle) {
      cycle.addEventListener("click", function () {
        var order = ["system", "light", "dark"];
        var next = order[(order.indexOf(readTheme()) + 1) % order.length];
        applyTheme(next);
        toast(cycle.dataset["label" + next.charAt(0).toUpperCase() + next.slice(1)] || next);
      });
    }
  }

  /* ══ header ════════════════════════════════════════════════════════════ */
  function initHeader() {
    var hdr = $(".hdr");
    if (!hdr) return;
    var onScroll = function () { hdr.classList.toggle("is-stuck", window.scrollY > 6); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    var burger = $("[data-burger]");
    var mnav = $("[data-mnav]");
    if (burger && mnav) {
      burger.addEventListener("click", function () {
        var open = mnav.hasAttribute("hidden");
        mnav.toggleAttribute("hidden", !open);
        burger.setAttribute("aria-expanded", String(open));
      });
    }
  }

  /* ══ popovers (language menu) ══════════════════════════════════════════ */
  function initPopovers() {
    var open = null;
    function close() {
      if (!open) return;
      open.menu.setAttribute("hidden", "");
      open.btn.setAttribute("aria-expanded", "false");
      open = null;
    }
    $$("[data-popover]").forEach(function (wrap) {
      var btn = $("[data-popover-btn]", wrap);
      var menu = $("[data-popover-menu]", wrap);
      if (!btn || !menu) return;
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var wasOpen = open && open.menu === menu;
        close();
        if (!wasOpen) {
          menu.removeAttribute("hidden");
          btn.setAttribute("aria-expanded", "true");
          open = { btn: btn, menu: menu };
        }
      });
    });
    document.addEventListener("click", close);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  /* ══ reveal on scroll ══════════════════════════════════════════════════
     The resting state in CSS is visible; the hidden state only exists while
     .js is on and the observer is coming. Without IntersectionObserver every
     .reveal is shown immediately, which is the correct failure.
     ══════════════════════════════════════════════════════════════════════ */
  function initReveal() {
    var items = $$(".reveal");
    if (!items.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    items.forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i % 6, 5) * 55 + "ms";
      io.observe(el);
    });
  }

  /* ══ tag filter ════════════════════════════════════════════════════════
     Client-side because the whole list is already on the page. The query
     string is kept in step so a filtered view is still a shareable URL, and
     the server honours ?tag= on a cold load.
     ══════════════════════════════════════════════════════════════════════ */
  function initFilter() {
    var bar = $("[data-filter-bar]");
    var listing = $("[data-filter-list]");
    if (!bar || !listing) return;
    var empty = $("[data-filter-empty]");
    var items = $$("[data-tags]", listing);

    function apply(tag, push) {
      var shown = 0;
      items.forEach(function (el) {
        var match = !tag || (" " + el.dataset.tags + " ").indexOf(" " + tag + " ") > -1;
        el.hidden = !match;
        if (match) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
      $$("[data-tag]", bar).forEach(function (b) {
        b.setAttribute("aria-pressed", String((b.dataset.tag || "") === tag));
      });
      if (push) {
        var url = new URL(window.location.href);
        if (tag) url.searchParams.set("tag", tag); else url.searchParams.delete("tag");
        history.replaceState(null, "", url);
      }
    }

    bar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-tag]");
      if (!btn) return;
      apply(btn.dataset.tag || "", true);
    });

    apply(new URL(window.location.href).searchParams.get("tag") || "", false);
  }

  /* ══ copy to clipboard ═════════════════════════════════════════════════ */
  function initCopy() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-copy]");
      if (!btn) return;
      e.preventDefault();
      var text = btn.dataset.copy;
      var done = function () { toast(btn.dataset.copiedLabel || "Copied"); };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
      } else {
        fallback(text, done);
      }
    });
    function fallback(text, done) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (err) { /* nothing else to try */ }
      ta.remove();
    }
  }

  /* ══ share ═════════════════════════════════════════════════════════════ */
  function initShare() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-share]");
      if (!btn) return;
      e.preventDefault();
      var payload = { title: document.title, url: btn.dataset.share || window.location.href };
      if (navigator.share) {
        navigator.share(payload).catch(function () { /* the reader dismissed it */ });
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(payload.url).then(function () {
          toast(btn.dataset.copiedLabel || "Copied");
        });
      }
    });
  }

  /* ══ command palette ═══════════════════════════════════════════════════
     Ctrl/⌘+K. The index is rendered into the page as JSON by base.html, so it
     costs no request and knows about exactly the pages this reader can see.
     ══════════════════════════════════════════════════════════════════════ */
  function initPalette() {
    var root = $("[data-cmdk]");
    if (!root) return;
    var input = $(".cmdk-input", root);
    var list = $(".cmdk-list", root);
    var emptyText = root.dataset.empty || "No results";
    var data = [];
    try { data = JSON.parse($("#cmdk-data").textContent); } catch (e) { return; }
    var cursor = 0;
    var results = [];

    function render(query) {
      var q = query.trim().toLowerCase();
      results = q
        ? data.filter(function (item) { return (item.t + " " + (item.k || "")).toLowerCase().indexOf(q) > -1; })
        : data.slice();
      cursor = 0;
      if (!results.length) {
        list.innerHTML = '<div class="cmdk-empty"></div>';
        list.firstChild.textContent = emptyText;
        return;
      }
      list.innerHTML = "";
      results.forEach(function (item, i) {
        var a = document.createElement("a");
        a.className = "cmdk-item" + (i === 0 ? " is-on" : "");
        a.href = item.u;
        var label = document.createElement("span");
        label.textContent = item.t;
        var kind = document.createElement("span");
        kind.className = "kind";
        kind.textContent = item.k || "";
        a.appendChild(label);
        a.appendChild(kind);
        list.appendChild(a);
      });
    }

    function move(step) {
      var nodes = $$(".cmdk-item", list);
      if (!nodes.length) return;
      nodes[cursor].classList.remove("is-on");
      cursor = (cursor + step + nodes.length) % nodes.length;
      nodes[cursor].classList.add("is-on");
      nodes[cursor].scrollIntoView({ block: "nearest" });
    }

    function open() {
      root.removeAttribute("hidden");
      input.value = "";
      render("");
      input.focus();
    }
    function close() { root.setAttribute("hidden", ""); }

    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        root.hasAttribute("hidden") ? open() : close();
        return;
      }
      if (root.hasAttribute("hidden")) return;
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        var on = $(".cmdk-item.is-on", list);
        if (on) { e.preventDefault(); window.location.href = on.href; }
      }
    });

    input.addEventListener("input", function () { render(input.value); });
    $(".cmdk-scrim", root).addEventListener("click", close);
    $$("[data-cmdk-open]").forEach(function (b) { b.addEventListener("click", open); });
  }

  /* ══ boot ══════════════════════════════════════════════════════════════ */
  function boot() {
    initTheme();
    initHeader();
    initPopovers();
    initReveal();
    initFilter();
    initCopy();
    initShare();
    initPalette();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
