/* ==========================================================================
   montazeri.ir — progressive enhancement only.

   The server already sent a finished page. Nothing in this file is required
   for the site to be read, navigated or submitted: turn JavaScript off and
   every link, form and page still works. What this adds is the difference
   between "it works" and "it feels considered".

   No framework, no build step, no dependency. One file, one function per
   concern, all started from boot() at the bottom.
   ========================================================================== */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var isPersian = (root.getAttribute("lang") || "").indexOf("fa") === 0;
  var STORE_THEME = "montazeri-theme";
  // The two values of --bg in site.css. The <meta name="theme-color"> tags in
  // base.html carry the same pair; if the tokens change, these change too.
  var THEME_COLOR = { light: "#f4f5f7", dark: "#12141b" };

  /* ── small helpers ─────────────────────────────────────────────────── */
  function $(sel, scope) { return (scope || document).querySelector(sel); }
  function $$(sel, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(sel)); }

  function icon(name, cls) {
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("aria-hidden", "true");
    if (cls) svg.setAttribute("class", cls);
    var use = document.createElementNS(ns, "use");
    use.setAttribute("href", "#i-" + name);
    svg.appendChild(use);
    return svg;
  }

  function digits(n) {
    var s = String(n);
    return isPersian ? s.replace(/\d/g, function (d) { return "۰۱۲۳۴۵۶۷۸۹"[d]; }) : s;
  }

  var toastTimer = null;
  function toast(text, iconName) {
    var old = $(".toast");
    if (old) old.remove();
    var el = document.createElement("div");
    el.className = "toast";
    el.setAttribute("role", "status");
    var ico = document.createElement("span");
    ico.className = "toast-ico";
    ico.appendChild(icon(iconName || "check"));
    var label = document.createElement("span");
    label.textContent = text;
    el.appendChild(ico);
    el.appendChild(label);
    document.body.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.classList.add("is-leaving");
      setTimeout(function () { el.remove(); }, 260);
    }, 2200);
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
    if (value === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", value);
    try { localStorage.setItem(STORE_THEME, value); } catch (e) { /* private mode */ }
    // An explicit choice paints the browser chrome that colour on every
    // device; "system" hands each meta tag back to its own media query.
    $$('meta[name="theme-color"]').forEach(function (meta) {
      var media = meta.getAttribute("media") || "";
      var own = media.indexOf("dark") > -1 ? "dark" : "light";
      meta.setAttribute("content", THEME_COLOR[value === "system" ? own : value]);
    });
  }
  function nextTheme() {
    var order = ["system", "light", "dark"];
    return order[(order.indexOf(readTheme()) + 1) % order.length];
  }
  function cycleTheme() {
    var btn = $("[data-theme-cycle]");
    var next = nextTheme();
    applyTheme(next);
    if (btn) {
      btn.classList.remove("is-turning");
      void btn.offsetWidth;
      btn.classList.add("is-turning");
      toast(btn.dataset["label" + next.charAt(0).toUpperCase() + next.slice(1)] || next, next === "dark" ? "moon" : next === "light" ? "sun" : "monitor");
    }
  }
  function initTheme() {
    applyTheme(readTheme());
    var btn = $("[data-theme-cycle]");
    if (btn) btn.addEventListener("click", cycleTheme);
  }

  /* ══ header: frosting, reading progress, back-to-top, mobile nav ═══════ */
  function initHeader() {
    var hdr = $("[data-hdr]");
    if (!hdr) return;
    var bar = $("[data-progress]");
    var toTop = $("[data-to-top-float]");
    var ring = toTop && $(".bar", toTop);
    var RING = 138.2; // 2πr for r = 22 in the ring's viewBox
    var ticking = false;

    if (toTop) { toTop.hidden = false; toTop.tabIndex = -1; }

    function update() {
      ticking = false;
      var y = window.scrollY;
      var max = root.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, y / max) : 0;
      hdr.classList.toggle("is-stuck", y > 8);
      if (bar) bar.style.transform = "scaleX(" + p.toFixed(4) + ")";
      if (toTop) {
        var on = y > 700;
        if (on !== toTop.classList.contains("is-on")) {
          toTop.classList.toggle("is-on", on);
          toTop.tabIndex = on ? 0 : -1;
          toTop.setAttribute("aria-hidden", String(!on));
        }
        if (ring) ring.style.strokeDashoffset = String(RING * (1 - p));
      }
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();

    $$("[data-to-top], [data-to-top-float]").forEach(function (b) {
      b.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
      });
    });

    var burger = $("[data-burger]");
    var mnav = $("[data-mnav]");
    if (burger && mnav) {
      var setOpen = function (open) {
        mnav.toggleAttribute("hidden", !open);
        burger.setAttribute("aria-expanded", String(open));
        hdr.classList.toggle("is-open", open);
      };
      burger.addEventListener("click", function (e) {
        e.stopPropagation();
        setOpen(mnav.hasAttribute("hidden"));
      });
      document.addEventListener("click", function (e) {
        if (!mnav.hasAttribute("hidden") && !hdr.contains(e.target)) setOpen(false);
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !mnav.hasAttribute("hidden")) { setOpen(false); burger.focus(); }
      });
      window.addEventListener("resize", function () {
        if (window.innerWidth > 960 && !mnav.hasAttribute("hidden")) setOpen(false);
      });
    }
  }

  /* ══ nav indicator ═════════════════════════════════════════════════════
     One soft pill that slides to whichever link the pointer is on and back
     to the current page when it leaves. Without this, .is-active paints its
     own background and nothing moves.
     ══════════════════════════════════════════════════════════════════════ */
  function initNavIndicator() {
    var nav = $("[data-nav]");
    var ind = nav && $(".nav-ind", nav);
    if (!ind) return;
    var active = $("a.is-active", nav);
    nav.classList.add("has-ind");

    function moveTo(a) {
      if (!a || !a.offsetWidth) { ind.style.opacity = "0"; return; }
      ind.style.opacity = "1";
      ind.style.width = a.offsetWidth + "px";
      ind.style.transform = "translateX(" + a.offsetLeft + "px)";
    }
    ind.classList.add("no-anim");
    moveTo(active);
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { ind.classList.remove("no-anim"); });
    });
    $$("a", nav).forEach(function (a) {
      a.addEventListener("pointerenter", function () { moveTo(a); });
      a.addEventListener("focus", function () { moveTo(a); });
    });
    nav.addEventListener("pointerleave", function () { moveTo(active); });
    nav.addEventListener("focusout", function (e) { if (!nav.contains(e.relatedTarget)) moveTo(active); });
    window.addEventListener("resize", function () { moveTo(active); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { moveTo(active); });
  }

  /* ══ popovers (language menu) ══════════════════════════════════════════ */
  function initPopovers() {
    var open = null;
    function close(returnFocus) {
      if (!open) return;
      open.menu.setAttribute("hidden", "");
      open.btn.setAttribute("aria-expanded", "false");
      if (returnFocus) open.btn.focus();
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
          var current = $('[aria-current="true"]', menu) || $("a", menu);
          if (current && e.detail === 0) current.focus(); // keyboard-opened only
        }
      });
      menu.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
        e.preventDefault();
        var items = $$("a", menu);
        var i = items.indexOf(document.activeElement);
        items[(i + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length].focus();
      });
    });
    document.addEventListener("click", function () { close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(true); });
  }

  /* ══ tooltips ══════════════════════════════════════════════════════════
     Any element with data-tip="…" gets one. A single floating element is
     positioned against the viewport, flips below when there is no room
     above and never runs off either edge. Mouse hover and keyboard focus
     only — on touch, the aria-label the element already carries is enough.
     ══════════════════════════════════════════════════════════════════════ */
  var tipApi = { show: function () {}, hide: function () {}, current: null };
  function initTips() {
    var tip = document.createElement("div");
    tip.className = "tip";
    tip.id = "site-tip";
    tip.setAttribute("role", "tooltip");
    document.body.appendChild(tip);
    var timer = null;

    function place(el) {
      var r = el.getBoundingClientRect();
      var tw = tip.offsetWidth, th = tip.offsetHeight, gap = 10;
      var top = r.top - th - gap, where = "top";
      if (top < 8) { top = r.bottom + gap; where = "bottom"; }
      var left = r.left + r.width / 2 - tw / 2;
      left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
      tip.dataset.place = where;
      tip.style.left = left + "px";
      tip.style.top = top + "px";
      tip.style.setProperty("--ax", Math.max(12, Math.min(tw - 12, r.left + r.width / 2 - left)) + "px");
    }
    function show(el) {
      var text = el.getAttribute("data-tip");
      if (!text) return;
      tipApi.current = el;
      tip.textContent = text;
      tip.classList.remove("is-on");
      place(el);
      if (!el.hasAttribute("aria-label")) el.setAttribute("aria-describedby", tip.id);
      window.requestAnimationFrame(function () { tip.classList.add("is-on"); });
    }
    function hide() {
      clearTimeout(timer);
      if (tipApi.current) tipApi.current.removeAttribute("aria-describedby");
      tipApi.current = null;
      tip.classList.remove("is-on");
    }
    tipApi.show = show;
    tipApi.hide = hide;

    document.addEventListener("pointerover", function (e) {
      if (e.pointerType && e.pointerType !== "mouse") return;
      var el = e.target.closest && e.target.closest("[data-tip]");
      if (!el || el === tipApi.current) return;
      clearTimeout(timer);
      timer = setTimeout(function () { show(el); }, tipApi.current ? 0 : 160);
    });
    document.addEventListener("pointerout", function (e) {
      var el = e.target.closest && e.target.closest("[data-tip]");
      if (!el || (e.relatedTarget && el.contains(e.relatedTarget))) return;
      hide();
    });
    document.addEventListener("focusin", function (e) {
      var el = e.target.closest && e.target.closest("[data-tip]");
      if (el && el.matches(":focus-visible")) show(el);
    });
    document.addEventListener("focusout", hide);
    document.addEventListener("pointerdown", hide);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(); });
    window.addEventListener("scroll", hide, { passive: true });
  }

  /* ══ reveal on scroll ══════════════════════════════════════════════════
     The resting state in CSS is visible; the hidden state only exists while
     .js is on and motion is allowed. Without IntersectionObserver every
     .reveal is shown immediately, which is the correct failure. Items that
     arrive together are staggered by --d, which only the arrival animation
     reads — hover transitions stay instant.
     ══════════════════════════════════════════════════════════════════════ */
  function initReveal() {
    var items = $$(".reveal");
    if (!items.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      var n = 0;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.style.setProperty("--d", Math.min(n++, 6) * 80 + "ms");
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ══ pointer effects: spotlight and tilt ═══════════════════════════════
     Fine pointers only, and never under reduced motion. Both write CSS
     custom properties; the stylesheet decides what they look like.
     ══════════════════════════════════════════════════════════════════════ */
  function initPointer() {
    if (!finePointer || reduceMotion) return;
    document.addEventListener("pointermove", function (e) {
      var el = e.target.closest && e.target.closest("[data-spot]");
      if (!el) return;
      var r = el.getBoundingClientRect();
      el.style.setProperty("--mx", (e.clientX - r.left) + "px");
      el.style.setProperty("--my", (e.clientY - r.top) + "px");
    }, { passive: true });

    $$("[data-tilt]").forEach(function (el) {
      var max = parseFloat(el.dataset.tilt) || 6;
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5;
        var y = (e.clientY - r.top) / r.height - 0.5;
        el.classList.add("is-tilting");
        el.style.setProperty("--ry", (x * max * 2).toFixed(2) + "deg");
        el.style.setProperty("--rx", (-y * max * 2).toFixed(2) + "deg");
        el.style.setProperty("--gx", ((x + 0.5) * 100).toFixed(1) + "%");
        el.style.setProperty("--gy", ((y + 0.5) * 100).toFixed(1) + "%");
      });
      el.addEventListener("pointerleave", function () {
        el.classList.remove("is-tilting");
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
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
        if (match) {
          shown++;
          if (el.hidden) {
            el.hidden = false;
            if (push && !reduceMotion) {
              el.classList.remove("is-pop");
              void el.offsetWidth;
              el.classList.add("is-pop");
            }
          }
        } else {
          el.hidden = true;
        }
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
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }
  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (err) { reject(err); }
      ta.remove();
    });
  }
  function flashDone(btn) {
    var use = $("use", btn);
    if (!use || btn.classList.contains("is-done")) return;
    var old = use.getAttribute("href");
    use.setAttribute("href", "#i-check");
    btn.classList.add("is-done");
    setTimeout(function () { use.setAttribute("href", old); btn.classList.remove("is-done"); }, 1600);
  }
  function initCopy() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-copy]");
      if (!btn) return;
      e.preventDefault();
      copyText(btn.dataset.copy).then(function () {
        flashDone(btn);
        toast(btn.dataset.copiedLabel || "Copied");
      }, function () { /* nothing else to try */ });
    });
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
      } else {
        copyText(payload.url).then(function () { toast(btn.dataset.copiedLabel || "Copied", "share"); });
      }
    });
  }

  /* ══ contact form: character count and the sending state ═══════════════ */
  function initForms() {
    $$("[data-form]").forEach(function (form) {
      var area = $("[data-count]", form);
      var counter = $("[data-counter]", form);
      if (area && counter) {
        var max = parseInt(area.getAttribute("maxlength"), 10) || 0;
        var update = function () {
          var n = area.value.length;
          counter.textContent = digits(n) + " / " + digits(max);
          counter.classList.toggle("is-near", max && n > max * 0.9);
        };
        area.addEventListener("input", update);
        update();
      }
      form.addEventListener("submit", function () {
        var btn = $("[data-submit]", form);
        if (!btn) return;
        btn.classList.add("is-loading");
        btn.setAttribute("aria-busy", "true");
        var label = $(".btn-label", btn);
        if (label && btn.dataset.busyLabel) label.textContent = btn.dataset.busyLabel;
      });
    });
    // Coming back through the history cache must not leave a spinner behind.
    window.addEventListener("pageshow", function (e) {
      if (!e.persisted) return;
      $$("[data-submit].is-loading").forEach(function (b) { b.classList.remove("is-loading"); b.removeAttribute("aria-busy"); });
    });
  }

  /* ══ command palette ═══════════════════════════════════════════════════
     Ctrl/⌘+K, or "/". The index is rendered into the page as JSON by
     base.html, so it costs no request and knows about exactly the pages this
     reader can see. The language and theme shortcuts are read from the page
     itself, so they can never disagree with the header.
     ══════════════════════════════════════════════════════════════════════ */
  function initPalette() {
    var box = $("[data-cmdk]");
    if (!box) return;
    var input = $(".cmdk-input", box);
    var list = $(".cmdk-list", box);
    var data = [];
    try { data = JSON.parse($("#cmdk-data").textContent); } catch (e) { return; }

    var groupPages = box.dataset.groupPages || "Pages";
    var groupActions = box.dataset.groupActions || "Actions";
    $$(".lang-menu a").forEach(function (a) {
      if (a.getAttribute("aria-current") === "true") return;
      data.push({ t: a.textContent.replace(/\s+/g, " ").trim(), u: a.getAttribute("href"), k: groupActions, i: "globe" });
    });
    var themeBtn = $("[data-theme-cycle]");
    if (themeBtn) data.push({ t: themeBtn.getAttribute("aria-label"), k: groupActions, i: "sun", run: cycleTheme });

    var cursor = 0, results = [], opener = null;

    function highlight(text, q) {
      var frag = document.createDocumentFragment();
      var i = q ? text.toLowerCase().indexOf(q) : -1;
      if (i < 0) { frag.appendChild(document.createTextNode(text)); return frag; }
      frag.appendChild(document.createTextNode(text.slice(0, i)));
      var m = document.createElement("mark");
      m.textContent = text.slice(i, i + q.length);
      frag.appendChild(m);
      frag.appendChild(document.createTextNode(text.slice(i + q.length)));
      return frag;
    }

    function render(query) {
      var q = query.trim().toLowerCase();
      results = data.filter(function (item) {
        return !q || (item.t + " " + (item.k || "")).toLowerCase().indexOf(q) > -1;
      });
      cursor = 0;
      list.innerHTML = "";
      if (!results.length) {
        var none = document.createElement("div");
        none.className = "cmdk-empty";
        none.textContent = box.dataset.empty || "No results";
        list.appendChild(none);
        return;
      }
      var lastGroup = null;
      results.forEach(function (item, i) {
        var group = item.k || groupPages;
        if (group !== lastGroup) {
          var h = document.createElement("div");
          h.className = "cmdk-group";
          h.setAttribute("role", "presentation");
          h.textContent = group;
          list.appendChild(h);
          lastGroup = group;
        }
        var a = document.createElement(item.run ? "button" : "a");
        a.className = "cmdk-item" + (i === 0 ? " is-on" : "");
        a.setAttribute("role", "option");
        a.dataset.index = String(i);
        if (item.run) { a.type = "button"; a.style.width = "100%"; a.style.border = "0"; a.style.background = "none"; a.style.textAlign = "start"; }
        else a.href = item.u;
        var ci = document.createElement("span");
        ci.className = "ci";
        ci.appendChild(icon(item.i || "arrow"));
        var label = document.createElement("span");
        label.className = "ct";
        label.appendChild(highlight(item.t, q));
        a.appendChild(ci);
        a.appendChild(label);
        a.appendChild(icon("arrow", "go fwd"));
        a.addEventListener("pointermove", function () { setCursor(i); });
        if (item.run) a.addEventListener("click", function () { close(); item.run(); });
        list.appendChild(a);
      });
    }

    function nodes() { return $$(".cmdk-item", list); }
    function setCursor(i) {
      var all = nodes();
      if (!all.length) return;
      if (all[cursor]) all[cursor].classList.remove("is-on");
      cursor = (i + all.length) % all.length;
      all[cursor].classList.add("is-on");
      all[cursor].scrollIntoView({ block: "nearest" });
    }

    function open() {
      opener = document.activeElement;
      box.classList.remove("is-closing");
      box.removeAttribute("hidden");
      root.classList.add("is-locked");
      tipApi.hide();
      input.value = "";
      render("");
      input.focus();
    }
    function close() {
      if (box.hasAttribute("hidden")) return;
      root.classList.remove("is-locked");
      var done = function () { box.setAttribute("hidden", ""); box.classList.remove("is-closing"); };
      if (reduceMotion) done();
      else { box.classList.add("is-closing"); setTimeout(done, 160); }
      if (opener && opener.focus) opener.focus();
    }

    document.addEventListener("keydown", function (e) {
      var typing = /INPUT|TEXTAREA|SELECT/.test((e.target.tagName || "")) || e.target.isContentEditable;
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        box.hasAttribute("hidden") ? open() : close();
        return;
      }
      if (e.key === "/" && !typing && box.hasAttribute("hidden")) { e.preventDefault(); open(); return; }
      if (box.hasAttribute("hidden")) return;
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); setCursor(cursor + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setCursor(cursor - 1); }
      else if (e.key === "Tab") { e.preventDefault(); setCursor(cursor + (e.shiftKey ? -1 : 1)); }
      else if (e.key === "Enter") {
        var item = results[cursor];
        if (!item) return;
        e.preventDefault();
        if (item.run) { close(); item.run(); } else window.location.href = item.u;
      }
    });

    input.addEventListener("input", function () { render(input.value); });
    $$("[data-cmdk-close]", box).forEach(function (el) { el.addEventListener("click", close); });
    $$("[data-cmdk-open]").forEach(function (b) { b.addEventListener("click", open); });
  }

  /* ══ ambient: the running system behind every page ════════════════════
     A fixed canvas under the content: nodes drift and link when near,
     events travel along the links and land with a ripple, and code tokens
     rise and fade. Nodes and tokens scroll at different rates, so the page
     has depth. Colours are read from the --x-rgb tokens (again whenever the
     theme changes), strength is --net in CSS. Paused while the tab is hidden;
     under reduced motion it paints one still frame and stops. */
  function initAmbient() {
    var canvas = $("[data-ambient-net]");
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");
    var HUES = ["mint", "sky", "lilac", "peach"];
    var WORDS = ["{ }", "</>", "=>", "async", "await", "def", "λ", "SELECT", "JOIN", "gRPC",
      "200 OK", "git push", "docker", "0101", "yield", "[ ]", "::", "&&", "fn()", "null",
      "import", "POST", "queue", "try:", "return", "SQL", "event", "{…}", "!=", "01"];
    var LINK = 150, POINTER = 180;
    var w = 0, h = 0, dpr = 1, colors = [], mono = "monospace";
    var nodes = [], glyphs = [], packets = [], ripples = [];
    var pointer = { x: -1e4, y: -1e4 };
    var running = false, last = 0, nextPacket = 0;
    // On a touch device the network runs lighter: fewer nodes, ~30 frames a
    // second, and it rests while the page is being scrolled, so the scroll
    // itself gets the whole frame budget.
    var lite = !finePointer || window.innerWidth < 700;
    var scrolling = false, scrollTimer;

    function rnd(a, b) { return a + Math.random() * (b - a); }
    function rgba(c, a) { return "rgba(" + colors[c] + "," + a.toFixed(3) + ")"; }
    function wrap(v, span) { return ((v % span) + span) % span; }

    function readColors() {
      var cs = getComputedStyle(root);
      colors = HUES.map(function (hue) { return cs.getPropertyValue("--" + hue + "-rgb").trim() || "128,128,128"; });
      mono = cs.getPropertyValue("--mono").trim() || "monospace";
    }
    function makeNode() {
      return { x: rnd(0, w), y: rnd(0, h), vx: rnd(-.22, .22), vy: rnd(-.22, .22),
               r: rnd(1.4, 3.2), c: Math.floor(rnd(0, 4)), sx: 0, sy: 0 };
    }
    function makeGlyph(anywhere) {
      return { x: rnd(0, w), y: anywhere ? rnd(0, h) : h + 20, vy: -rnd(.12, .32),
               t: WORDS[Math.floor(rnd(0, WORDS.length))], c: Math.floor(rnd(0, 4)),
               size: Math.round(rnd(11, 17)), age: anywhere ? rnd(0, 1) : 0, dur: rnd(9000, 16000) };
    }
    function resize() {
      // A tab opened in the background can report a 0×0 viewport; wrapping
      // against 0 would park every node at NaN for good.
      if (!window.innerWidth || !window.innerHeight) return;
      w = window.innerWidth; h = window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      var nodeCount = Math.round(Math.max(22, Math.min(lite ? 30 : 70, w * h / 21000)));
      var glyphCount = w < 700 ? 6 : 14;
      while (nodes.length < nodeCount) nodes.push(makeNode());
      nodes.length = nodeCount;
      while (glyphs.length < glyphCount) glyphs.push(makeGlyph(true));
      glyphs.length = glyphCount;
      nodes.forEach(function (n) {
        n.x = isFinite(n.x) ? wrap(n.x, w) : rnd(0, w);
        n.y = isFinite(n.y) ? wrap(n.y, h) : rnd(0, h);
      });
      glyphs.forEach(function (g, i) { if (!isFinite(g.x) || g.x > w) glyphs[i] = makeGlyph(true); });
    }

    function step(dt, now) {
      nodes.forEach(function (n) {
        var dx = n.sx - pointer.x, dy = n.sy - pointer.y, d2 = dx * dx + dy * dy;
        if (d2 < 14400 && d2 > 1) { var f = (1 - Math.sqrt(d2) / 120) * .6; n.x += dx / Math.sqrt(d2) * f * dt; n.y += dy / Math.sqrt(d2) * f * dt; }
        n.x = wrap(n.x + n.vx * dt, w); n.y = wrap(n.y + n.vy * dt, h);
      });
      glyphs.forEach(function (g, i) {
        g.y += g.vy * dt; g.age += 16.67 * dt / g.dur;
        if (g.age >= 1) glyphs[i] = makeGlyph(true);
      });
      if (now > nextPacket) {
        nextPacket = now + rnd(260, 620);
        var a = nodes[Math.floor(rnd(0, nodes.length))];
        var near = nodes.filter(function (b) {
          var dx = a.sx - b.sx, dy = a.sy - b.sy; return b !== a && dx * dx + dy * dy < LINK * LINK;
        });
        if (near.length) packets.push({ a: a, b: near[Math.floor(rnd(0, near.length))], p: 0, v: rnd(.012, .022), c: a.c });
      }
      packets = packets.filter(function (k) {
        k.p += k.v * dt;
        if (k.p < 1) return true;
        if (k.torn) return false;
        ripples.push({ x: k.b.sx, y: k.b.sy, age: 0, c: k.c });
        return false;
      });
      ripples = ripples.filter(function (r) { r.age += .025 * dt; return r.age < 1; });
    }

    function draw() {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      var scroll = window.scrollY || 0;
      var i, j, n, m, dx, dy, d;
      for (i = 0; i < nodes.length; i++) { n = nodes[i]; n.sx = n.x; n.sy = wrap(n.y - scroll * .12, h); }

      ctx.lineWidth = 1;
      for (i = 0; i < nodes.length; i++) {
        n = nodes[i];
        for (j = i + 1; j < nodes.length; j++) {
          m = nodes[j]; dx = n.sx - m.sx; dy = n.sy - m.sy;
          if (dx * dx + dy * dy > LINK * LINK) continue;
          d = Math.sqrt(dx * dx + dy * dy);
          ctx.strokeStyle = rgba(n.c, (1 - d / LINK) * .45);
          ctx.beginPath(); ctx.moveTo(n.sx, n.sy); ctx.lineTo(m.sx, m.sy); ctx.stroke();
        }
        dx = n.sx - pointer.x; dy = n.sy - pointer.y;
        if (dx * dx + dy * dy < POINTER * POINTER) {
          ctx.strokeStyle = rgba(n.c, (1 - Math.sqrt(dx * dx + dy * dy) / POINTER) * .6);
          ctx.beginPath(); ctx.moveTo(n.sx, n.sy); ctx.lineTo(pointer.x, pointer.y); ctx.stroke();
        }
      }

      nodes.forEach(function (n) {
        if (n.r > 2.4) { ctx.fillStyle = rgba(n.c, .16); ctx.beginPath(); ctx.arc(n.sx, n.sy, n.r * 3.2, 0, 6.283); ctx.fill(); }
        ctx.fillStyle = rgba(n.c, .9); ctx.beginPath(); ctx.arc(n.sx, n.sy, n.r, 0, 6.283); ctx.fill();
      });

      packets.forEach(function (k) {
        dx = k.b.sx - k.a.sx; dy = k.b.sy - k.a.sy;
        if (dx * dx + dy * dy > LINK * LINK * 1.5) { k.p = 2; k.torn = true; return; }   // a scroll wrap tore the link
        var x = k.a.sx + dx * k.p, y = k.a.sy + dy * k.p;
        var t = Math.max(0, k.p - .22);
        ctx.strokeStyle = rgba(k.c, .7); ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.moveTo(k.a.sx + dx * t, k.a.sy + dy * t); ctx.lineTo(x, y); ctx.stroke();
        ctx.fillStyle = rgba(k.c, .22); ctx.beginPath(); ctx.arc(x, y, 6, 0, 6.283); ctx.fill();
        ctx.fillStyle = rgba(k.c, 1); ctx.beginPath(); ctx.arc(x, y, 2.2, 0, 6.283); ctx.fill();
      });
      ctx.lineWidth = 1.2;
      ripples.forEach(function (r) {
        ctx.strokeStyle = rgba(r.c, (1 - r.age) * .7);
        ctx.beginPath(); ctx.arc(r.x, r.y, 3 + r.age * 20, 0, 6.283); ctx.stroke();
      });

      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      if ("direction" in ctx) ctx.direction = "ltr";
      glyphs.forEach(function (g) {
        var a = Math.sin(Math.PI * Math.min(1, g.age)) * .8;
        ctx.font = "500 " + g.size + "px " + mono;
        ctx.fillStyle = rgba(g.c, a);
        ctx.fillText(g.t, g.x, wrap(g.y - scroll * .3 + 30, h + 60) - 30);
      });
    }

    function frame(now) {
      if (!running) return;
      if (lite && (scrolling || (last && now - last < 32))) { requestAnimationFrame(frame); return; }
      var dt = Math.min(48, now - (last || now)) / 16.67;
      last = now;
      step(dt, now);
      draw();
      requestAnimationFrame(frame);
    }
    function start() { if (running || reduceMotion) return; running = true; last = 0; requestAnimationFrame(frame); }
    function stop() { running = false; }

    readColors();
    resize();
    draw();
    draw();   // the first pass only placed the nodes on screen

    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () { resize(); if (!running) draw(); }, 120);
    });
    new MutationObserver(function () { readColors(); if (!running) draw(); })
      .observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    var scheme = window.matchMedia("(prefers-color-scheme: dark)");
    var onScheme = function () { readColors(); if (!running) draw(); };
    if (scheme.addEventListener) scheme.addEventListener("change", onScheme);
    else if (scheme.addListener) scheme.addListener(onScheme);

    if (reduceMotion) return;
    if (finePointer) {
      window.addEventListener("pointermove", function (e) { pointer.x = e.clientX; pointer.y = e.clientY; }, { passive: true });
      document.addEventListener("pointerleave", function () { pointer.x = pointer.y = -1e4; });
    }
    if (lite) {
      window.addEventListener("scroll", function () {
        scrolling = true;
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function () { scrolling = false; last = 0; }, 140);
      }, { passive: true });
    }
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
    start();
  }

  /* ══ boot ══════════════════════════════════════════════════════════════ */
  function boot() {
    initTheme();
    initAmbient();
    initHeader();
    initNavIndicator();
    initPopovers();
    initTips();
    initReveal();
    initPointer();
    initFilter();
    initCopy();
    initShare();
    initForms();
    initPalette();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
