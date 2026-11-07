/* design-review template engine — one tool, one visual language (unslop).
 *
 * setTime(t) draws one frame as a pure function of t: no timers, no CSS transitions, no randomness.
 * Everything on screen is a FABRICATED product surface (owner correction D2: the reference accounts draw
 * their UI, they do not capture it). Each scene is an artifact; scenes hard-cut (no cross-fade), and the
 * artifact gets a camera (punch-in) so a single drawing never sits still.
 *
 * Data: window.DATA = {width, height, handle, template, brand:{...},
 *                      scenes:[{id, archetype, t0, t1, headline, payload, words, cue, cues, ev}]}
 */
(function () {
  "use strict";
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var PAPER = "#F4F0E8", INK = "#14161F", MUTED = "#6E6A63", HAIR = "#DED6C6", ACC = "#6C4CF1", RED = "#E4572E";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var eCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var eExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var eBack = function (x) { x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 2 : n); };
  var el = function (tag, cls, parent, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  var svg = function (w, h, parent, cls) {
    var s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 " + w + " " + h);
    if (cls) s.setAttribute("class", cls);
    if (parent) parent.appendChild(s);
    return s;
  };
  var norm = function (w) { return String(w).toLowerCase().replace(/[^a-z0-9]/g, ""); };
  var STOP = "a an the and or of to in on for with is it its be by as at from that this so any every each you your we our they them then first before can not no do does one two".split(" ");
  var toks = function (s) {
    var out = [], p = String(s).split(/\s+/);
    for (var i = 0; i < p.length; i++) {
      var n = norm(p[i]);
      if (n.length > 2 && STOP.indexOf(n) < 0) out.push(n);
    }
    return out;
  };

  /* Cut times inside a scene: bind each cue phrase to the first spoken word that matches, then fill the
   * rest by an even spread. Same rule cues.py uses for the default template, so the picture stays on the word. */
  function bindTimes(phrases, s, n) {
    var want = phrases && phrases.length ? phrases : null;
    var out = [], used = -1;
    for (var i = 0; i < n; i++) {
      var t = null;
      if (want && want[i]) {
        var to = toks(want[i]);
        for (var k = 0; k < (s.words || []).length; k++) {
          var w = s.words[k];
          if (w[1] <= used) continue;
          if (to.indexOf(norm(w[0])) >= 0) { t = w[1]; used = w[1]; break; }
        }
      }
      if (t === null) t = s.t0 + (s.t1 - s.t0) * (i / Math.max(1, n)) + 0.12;
      out.push(t);
    }
    out[0] = Math.min(out[0], s.t0 + 0.12);  // never open on an empty stage
    for (var j = 1; j < out.length; j++) if (out[j] <= out[j - 1]) out[j] = out[j - 1] + 0.35;
    return out;
  }

  /* ============================ fabricated app screens ============================ */
  var SLOP = null;
  function screen(spec) {
    spec = spec || {};
    var pg = el("div", "pg pg-" + (spec.variant || "slop"));
    var brand = el("div", "brand", pg);
    el("i", null, brand);
    el("b", null, brand, spec.brand || "Nimbus");
    if (spec.variant === "clean") {
      el("div", "nav", pg, spec.nav || "PRODUCT   PRICING   DOCS");
      var hero = el("div", "hero", pg);
      el("div", "kicker", hero, spec.kicker || "Invoice tooling");
      el("h1", null, hero, spec.title || "Send invoices that get paid");
      el("p", null, hero, spec.sub || "One screen, your numbers, nothing in the way.");
      el("div", "cta", hero, spec.cta || "Start with one invoice \u2192");
      var rows = el("div", "rows", pg);
      (spec.sections || ["Invoices", "Clients", "Payments"]).forEach(function (t, i) {
        var r = el("div", "row", rows);
        el("em", null, r, "0" + (i + 1));
        el("b", null, r, t);
        el("s", null, r, spec.rowMeta || "\u2014");
      });
    } else if (spec.variant === "mid") {
      var hero2 = el("div", "hero", pg);
      el("h1", null, hero2, spec.title || "Send invoices that get paid");
      el("p", null, hero2, spec.sub || "One screen, your numbers, nothing in the way.");
      el("div", "cta", hero2, spec.cta || "Start with one invoice \u2192");
      var cards2 = el("div", "cards", pg);
      (spec.sections || ["Invoices", "Clients", "Payments"]).forEach(function (t) {
        var c = el("div", "card", cards2);
        el("b", null, c, t);
        el("u", null, c);
        el("u", "short", c);
      });
    } else {
      if (spec.badge !== false) {
        var bd = el("div", "badges", pg);
        ["\u2726 AI", "\u25B2 Fast", "\u2605 Pro"].forEach(function (t) {
          var b = el("div", "badge", bd);
          var s = el("s", null, b, t.slice(0, 1));
          el("span", null, b, t.slice(2));
        });
      }
      var glow = el("div", "glow", pg);
      var hero3 = el("div", "hero", pg);
      el("h1", null, hero3, spec.title || "Send invoices that get paid");
      el("p", null, hero3, spec.sub || "AI-powered invoicing. Ship faster. Scale effortlessly.");
      el("div", "cta", hero3, spec.cta || "Get started free");
      var cards3 = el("div", "cards", pg);
      (spec.sections || ["Invoices", "Clients", "Payments"]).forEach(function (t) {
        var c = el("div", "card", cards3);
        el("b", null, c, t);
        el("u", null, c);
        el("u", "short", c);
      });
      pg._glow = glow;
    }
    return pg;
  }

  function windowWith(pageSpec, opts) {
    opts = opts || {};
    var win = el("div", "win");
    var bar = el("div", "win-bar", win);
    el("i", null, bar); el("i", null, bar); el("i", null, bar);
    el("div", "win-url", bar, opts.url || "nimbus.app/dashboard");
    var body = el("div", "win-body", win);
    var pg = screen(pageSpec);
    body.appendChild(pg);
    return { win: win, body: body, page: pg };
  }

  /* ============================ archetypes ============================ */
  var ARCH = {};

  /* ui_screen: one artifact, and it hard-cuts between pages on the words — the "same screen, again" beat. */
  ARCH.ui_screen = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { pages: [], idx: -1 };
      var host = el("div", null, root);
      (p.pages || [{ variant: "slop" }]).forEach(function (spec, i) {
        var w = windowWith(spec, { url: spec.url });
        host.appendChild(w.win);
        w.win.style.height = "92%";
        w.win.style.display = "none";
        r.pages.push(w);
      });
      host.className = "artifact-host";
      var lab = el("div", "ps");
      r.stamp = el("div", "stamp", lab, p.label || "");
      r.stamp.style.top = "auto";
      r.stamp.style.bottom = "26px";
      root.appendChild(lab);
      r.times = bindTimes(p.cue_phrases, s, r.pages.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0, k = 0;
      for (var i = 0; i < r.times.length; i++) if (now >= r.times[i]) k = i;
      if (k !== r.idx) {
        r.idx = k;                                     // hard cut, no fade: the page is simply replaced
        r.pages.forEach(function (w, i) { w.win.style.display = i === k ? "block" : "none"; });
      }
      var cur = r.pages[k];
      if (cur && cur.page._glow) {                      // the slop screens glow and breathe; the clean one holds still
        cur.page._glow.style.opacity = fmt(0.55 + 0.45 * Math.sin(now * 1.7));
        cur.page._glow.style.transform = "scale(" + fmt(1 + 0.03 * Math.sin(now * 1.1), 3) + ")";
      }
      if (r.stamp.textContent) r.stamp.style.opacity = fmt(ramp(u, 0.1, 0.4));
    }
  };

  /* audit_marks: the same screen, annotated — a red callout per finding, each hung off the element that
   * commits it, plus the verdict band under the screen. Labels flip side so they never cover their target. */
  ARCH.audit_marks = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { marks: [] };
      var w = windowWith(p.page || { variant: "slop" }, { url: (p.page || {}).url });
      w.win.style.height = "1090px";
      root.appendChild(w.win);
      var layer = el("div", "am", root);
      (p.marks || []).forEach(function (spec) {
        var obj = (spec && typeof spec === "object") ? spec : { t: String(spec) };
        var m = el("div", "mark", layer, obj.t);
        var dot = el("div", "dot", layer);
        var lead = el("div", "lead", layer);
        r.marks.push({ m: m, dot: dot, lead: lead, sel: obj.sel || null, at: obj.at || null, side: obj.side || null });
      });
      r.score = el("div", "score", root, "SLOP FOUND \u00d7" + (p.marks || []).length);
      r.times = bindTimes(p.cue_phrases, s, (p.marks || []).length + 1);
      return r;
    },
    place: function (r, host) {
      // measured once, the first time the scene is really on screen: every label sits just outside the
      // element that commits the slop, with a short leader down to a dot on that element's edge
      var hb = host.getBoundingClientRect();
      r.marks.forEach(function (x, i) {
        var tr = null;
        if (x.sel) { try { var t = host.querySelector(x.sel); if (t) tr = t.getBoundingClientRect(); } catch (e) { tr = null; } }
        var top = tr ? tr.top - hb.top : 68 + (x.at ? x.at[1] : 260 + 150 * i);
        var left = tr ? tr.left - hb.left : (x.at ? x.at[0] : 300);
        var w = tr ? tr.width : 320, h = tr ? tr.height : 60;
        var mw = x.m.offsetWidth || 220, mh = x.m.offsetHeight || 56;
        var below = (x.side !== "above") && (top + h / 2 < 600);
        var ly = below ? top + h + 16 : top - mh - 16;
        var lx = Math.max(12, Math.min(946 - mw, left + Math.min(w * 0.5, 120) - mw * 0.4));
        var dotx = Math.max(16, Math.min(944, lx + mw * 0.35));
        var doty = below ? top + h - 8 : top + 8;
        x.m.style.left = fmt(lx) + "px";
        x.m.style.top = fmt(Math.max(6, Math.min(1082 - mh, ly))) + "px";
        x.dot.style.left = fmt(dotx - 10) + "px";
        x.dot.style.top = fmt(doty - 10) + "px";
        x.lead.style.left = fmt(dotx) + "px";
        x.lead.style.width = "3px";
        x.lead.style.top = fmt(below ? doty : doty) + "px";
        x.lead.style.height = fmt(Math.max(10, Math.abs((ly + (below ? 0 : mh)) - doty))) + "px";
      });
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (!r.placed) { r.placed = true; ARCH.audit_marks.place(r, s._art); }
      r.marks.forEach(function (x, i) {
        var t = now - r.times[i], p = eBack(ramp(t, 0, 0.4));
        x.m.style.opacity = fmt(ramp(t, 0, 0.12));
        x.m.style.transform = "translateY(" + fmt((1 - p) * 18) + "px)";
        x.dot.style.opacity = fmt(ramp(t, 0, 0.1));
        x.dot.style.transform = "scale(" + fmt(0.6 + 0.4 * p + 0.06 * Math.sin(now * 5 + i), 3) + ")";
        x.lead.style.opacity = fmt(0.85 * ramp(t, 0.05, 0.3));
      });
      var last = r.times[r.marks.length] || (s.t1 - 0.4);
      r.score.style.opacity = fmt(ramp(now, last - 0.1, last + 0.2));
      r.score.style.transform = "scale(" + fmt(0.92 + 0.08 * eBack(ramp(now, last - 0.1, last + 0.35)), 3) + ")";
    }
  };

  /* direction_card: the answer you give becomes the direction — typed, line by line, on the voice. */
  ARCH.direction_card = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { lines: [] };
      var card = el("div", "dc", root);
      var inner = el("div", "card", card);
      var top = el("div", "top", inner);
      el("i", null, top);
      el("span", null, top, p.label || "direction");
      (p.lines || []).forEach(function (text) {
        var ln = el("div", "ln", inner);
        var idx = el("i", null, ln, "");
        var body = el("span", null, ln, "");
        var caret = el("span", "caret", ln);
        r.lines.push({ ln: ln, idx: idx, body: body, caret: caret, text: text, node: inner });
      });
      r.card = inner;
      r.times = bindTimes(p.cue_phrases, s, r.lines.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.card.style.opacity = fmt(ramp(u, 0, 0.18));
      r.card.style.transform = "translateY(" + fmt((1 - eCubic(ramp(u, 0, 0.42))) * 26) + "px)";
      var active = -1;
      r.lines.forEach(function (x, i) {
        var t = now - r.times[i];
        if (t >= 0) active = i;
      });
      r.lines.forEach(function (x, i) {
        var t = now - r.times[i];
        var cps = 46;
        var n = Math.floor(clamp(t * cps, 0, x.text.length));
        if (t < 0) { x.ln.style.opacity = "0"; x.body.textContent = ""; x.idx.textContent = ""; x.caret.style.opacity = "0"; return; }
        x.ln.style.opacity = fmt(ramp(t, 0, 0.14));
        x.idx.textContent = "0" + (i + 1);
        x.body.textContent = x.text.slice(0, n);
        x.caret.style.opacity = (i === active && (Math.floor(now * 2.2) % 2 === 0)) ? "1" : "0";
      });
    }
  };

  /* pass_stack: the same screen, redrawn in nine passes — three hard cuts, three visible changes. */
  ARCH.pass_stack = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { pages: [], idx: -1 };
      var box = el("div", "ps", root);
      var stagebox = el("div", "stagebox", box);
      (p.pages || [{ variant: "slop" }, { variant: "mid" }, { variant: "clean" }]).forEach(function (spec) {
        var w = windowWith(spec, { url: spec.url });
        w.win.style.transformOrigin = "50% 0";
        w.win.style.height = "960px";
        w.win.style.position = "absolute";
        stagebox.appendChild(w.win);
        w.win.style.display = "none";
        r.pages.push(w);
      });
      r.label = el("div", "passlabel", box, "");
      var pips = el("div", "passpips", box);
      r.pips = (p.passes || []).map(function () { return el("i", null, pips); });
      var names = el("div", "passnames", box);
      r.names = (p.passes || []).map(function (t) { return el("span", null, names, String(t).toUpperCase()); });
      var n = r.pages.length;
      r.times = bindTimes(p.cue_phrases, s, n);
      r.per = Math.ceil(r.names.length / n);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0, k = 0;
      for (var i = 0; i < r.times.length; i++) if (now >= r.times[i]) k = i;
      if (k !== r.idx) {
        r.idx = k;
        r.pages.forEach(function (w, i) { w.win.style.display = i === k ? "block" : "none"; });
      }
      var done = Math.min(r.names.length, (k + 1) * r.per);
      r.pips.forEach(function (pi, i) { pi.className = i < done ? (i === done - 1 ? "now" : "on") : ""; });
      r.names.forEach(function (nm, i) { nm.className = i < done - 1 ? "on" : (i === done - 1 ? "now" : ""); });
      var cur = r.names[Math.max(0, done - 1)];
      r.label.textContent = (done < 10 ? "0" + done : done) + " \u00b7 " + (cur ? cur.textContent : "");
      var cut = ramp(now - r.times[k], 0, 0.22);
      r.pages.forEach(function (w, i) {
        if (i !== k) return;
        w.win.style.transform = "scale(" + fmt(0.985 + 0.015 * eCubic(cut), 4) + ")";
      });
      if (r.pages[k].page._glow) r.pages[k].page._glow.style.opacity = fmt(0.6 + 0.4 * Math.sin(now * 1.7));
    }
  };

  /* stack_chips: the exact thing to type, then the stacks it runs in. */
  ARCH.stack_chips = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { chips: [] };
      var wrap = el("div", "sc", root);
      var term = el("div", "term", wrap);
      var bar = el("div", "bar", term);
      el("i", null, bar); el("i", null, bar); el("i", null, bar);
      var line = el("div", "line", term);
      var pspan = el("span", "p", line, "$ ");
      r.cmd = el("span", "c", line, "");
      r.full = p.command || "/unslop this dashboard";
      var chips = el("div", "chips", wrap);
      (p.chips || []).forEach(function (t, i) {
        var c = el("div", "chip" + (i === (p.chips || []).length - 1 ? " live" : ""), chips, t);
        r.chips.push(c);
      });
      r.times = bindTimes(p.cue_phrases, s, r.chips.length + 1);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var cps = 30, t0 = r.times[0];
      var n = Math.floor(clamp((now - t0) * cps, 0, r.full.length));
      r.cmd.textContent = r.full.slice(0, n);
      if (n < r.full.length && Math.floor(now * 2.5) % 2 === 0) r.cmd.textContent += "\u258d";
      r.chips.forEach(function (c, i) {
        var t = now - (r.times[i + 1] || t0 + 0.5 + i * 0.4);
        var p = eBack(ramp(t, 0, 0.34));
        c.style.opacity = fmt(0.16 + 0.84 * ramp(t, 0, 0.2));
        c.style.transform = "translateY(" + fmt((1 - p) * 22) + "px)";
      });
    }
  };

  /* boundary_rows: what you can expect. Concessions sit inside the pitch, never as a warning card. */
  ARCH.boundary_rows = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { rows: [] };
      var wrap = el("div", "br", root);
      (p.rows || []).forEach(function (text, ri) {
        var row = el("div", "row", wrap);
        el("div", "bar", row);
        var obj = (text && typeof text === "object") ? text : { t: String(text) };
        var kind = obj.kind || (ri === 0 ? "ok" : "tag");
        var ic = el("div", "ic " + kind, row);
        var sv = svg(24, 24, ic);
        var path = document.createElementNS(NS, "path");
        path.setAttribute("d", kind === "ok" ? "M4 12.5l5.5 5.5L20 6" : "M12 4v10M12 18v2");
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", kind === "ok" ? "#2F9E63" : ACC);
        path.setAttribute("stroke-width", "3.4");
        path.setAttribute("stroke-linecap", "round");
        sv.appendChild(path);
        var t = el("div", "t", row);
        el("span", null, t, obj.t);
        if (obj.s) el("small", null, t, obj.s);
        r.rows.push({ row: row, bar: row.querySelector(".bar") });
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.rows.forEach(function (x, i) {
        var t = now - r.times[i];
        var p = eCubic(ramp(t, 0, 0.4));
        x.row.style.opacity = fmt(ramp(t, 0, 0.22));
        x.row.style.transform = "translateY(" + fmt((1 - p) * 24) + "px)";
        x.bar.style.width = fmt(100 * eCubic(ramp(t, 0.05, 0.55)), 2) + "%";   // the rule draws itself
      });
    }
  };

  /* split_compare: same layout, same words, different product. The divider is dragged across. */
  ARCH.split_compare = {
    build: function (root, s) {
      var p = s.payload || {};
      var wrap = el("div", "sp", root);
      var before = el("div", "half before", wrap);
      var after = el("div", "half after", wrap);
      var b = windowWith(p.before || { variant: "slop" }, { url: (p.before || {}).url });
      var a = windowWith(p.after || { variant: "clean" }, { url: (p.after || {}).url });
      b.win.style.position = "absolute"; a.win.style.position = "absolute";
      b.win.style.height = "100%"; a.win.style.height = "100%";
      before.appendChild(b.win); after.appendChild(a.win);
      var labels = p.labels || ["BEFORE", "AFTER"];
      var lb = el("div", "label before", wrap, labels[0]);
      var la = el("div", "label after", wrap, labels[1]);
      var div = el("div", "divider", wrap);
      var knob = el("div", "knob", wrap);
      var r = { div: div, knob: knob, after: after, b: b, a: a, labels: [lb, la] };
      r.times = bindTimes(p.cue_phrases, s, 2);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var t = ramp(now, r.times[0] + 0.25, r.times[0] + 1.5);
      var x = 100 - 94 * eCubic(t);                       // 100% -> 6%: the clean screen wipes across
      r.div.style.left = fmt(x * 9.6 - 3) + "px";
      r.knob.style.left = fmt(x * 9.6) + "px";
      r.after.style.clipPath = "inset(0 0 0 " + fmt(x, 2) + "%)";
      r.labels[0].style.opacity = fmt(ramp(now, r.times[0], r.times[0] + 0.3) * ramp(x, 50, 70));
      r.labels[1].style.opacity = fmt(1 - ramp(x, 50, 70));
      if (r.b.page._glow) r.b.page._glow.style.opacity = fmt(0.6 + 0.4 * Math.sin(now * 1.6));
    }
  };

  /* endcard: real brand logo, handle, the keyword, a Follow button and a cursor that presses it on the
   * pipeline's own press time (the same number the click SFX uses). */
  ARCH.endcard = {
    build: function (root, s) {
      var b = (D && D.brand) || {};
      var p = s.payload || {};
      var r = { wrap: el("div", "ec", root) };
      r.card = el("div", "ec-card", r.wrap);
      var av = el("div", "ec-av", r.card);
      if (b.logo) { var img = document.createElement("img"); img.src = b.logo; img.alt = b.name || ""; av.appendChild(img); }
      else { el("span", "ec-initial", av, String(b.name || "H").slice(0, 1)); }
      el("div", "ec-name", r.card, b.name || "");
      el("div", "ec-handle", r.card, b.handle || D.handle || "");
      if (b.tagline) el("div", "ec-tag", r.card, b.tagline);
      r.kw = el("div", "ec-kw", r.card);
      el("span", "ec-kw-t", r.kw, p.keyword ? String(p.keyword).toUpperCase() : "");
      r.btn = el("div", "ec-btn", r.card);
      r.lbl = el("span", "ec-lbl", r.btn, p.follow || b.cta_button || "Follow");
      r.done = el("div", "ec-done", r.btn);
      el("span", "ec-done-t", r.done, "Following");
      r.ring = el("div", "ec-ring", r.btn);
      r.cur = svg(24, 24, r.btn, "ec-cursor");
      var path = document.createElementNS(NS, "path");
      path.setAttribute("d", "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z");
      path.setAttribute("fill", "#FFFFFF"); path.setAttribute("stroke", INK); path.setAttribute("stroke-width", "1.2");
      r.cur.appendChild(path);
      return r;
    },
    update: function (r, s, u, d) {
      var ev = s.ev || {};
      var pr = (typeof ev.press === "number" ? ev.press : s.t0 + Math.max(1.1, Math.min(d * 0.6, d - 1.0))) - s.t0;
      var kw = (typeof ev.keyword === "number" ? ev.keyword : s.cue) - s.t0;
      var cin = eBack(ramp(u, 0, 0.5));
      r.card.style.opacity = fmt(ramp(u, 0, 0.2));
      r.card.style.transform = "translateY(" + fmt((1 - cin) * 80) + "px) scale(" + fmt(0.96 + 0.04 * cin, 3) + ")";
      var kp = eBack(ramp(u, kw, kw + 0.4));
      r.kw.style.opacity = fmt(ramp(u, kw, kw + 0.16));
      r.kw.style.transform = "translateY(" + fmt((1 - kp) * 30) + "px) scale(" + fmt(0.9 + 0.1 * kp, 3) + ")";
      var arrive = eCubic(ramp(u, pr - 0.55, pr));
      var leave = ramp(u, pr + 0.5, pr + 0.8);
      r.cur.style.opacity = fmt(ramp(u, pr - 0.58, pr - 0.4) * (1 - leave));
      r.cur.style.transform = "translate(" + fmt((1 - arrive) * 150) + "px," + fmt((1 - arrive) * 170) + "px)";
      var down = ramp(u, pr - 0.12, pr - 0.02) * (1 - ramp(u, pr + 0.02, pr + 0.2));
      r.btn.style.transform = "scale(" + fmt((1 - 0.06 * down) * (0.97 + 0.03 * eBack(ramp(u, 0.16, 0.5))), 3) + ")";
      r.lbl.style.opacity = fmt(1 - ramp(u, pr + 0.02, pr + 0.1));
      r.done.style.opacity = fmt(ramp(u, pr + 0.03, pr + 0.14));
      r.ring.style.opacity = fmt(ramp(u, pr, pr + 0.03) * (1 - ramp(u, pr + 0.26, pr + 0.56)));
      r.ring.style.transform = "scale(" + fmt(0.7 + 1.4 * eCubic(ramp(u, pr, pr + 0.5)), 3) + ")";
    }
  };

  /* ============================ stage ============================ */
  var stageEl, capEl;

  function headlineNode(parent, text, accentWord) {
    var h = el("div", "headline", parent);
    var words = String(text || "").split(" ");
    var line = el("span", "ln", h);
    var acc = accentWord ? String(accentWord).toLowerCase() : null;
    var chars = 0;
    words.forEach(function (w, i) {
      var isAcc = acc && norm(w) === norm(acc);
      var span = el("span", isAcc ? "accent" : null, line, w + (i < words.length - 1 ? " " : ""));
      chars += w.length + 1;
      if (chars > 22 && i < words.length - 1) { line = el("span", "ln", h); chars = 0; }
    });
    return h;
  }

  function build() {
    stageEl = document.getElementById("stage");
    el("div", "paper", stageEl);
    el("div", "handle", stageEl, D.handle || "");
    D.scenes.forEach(function (s) {
      var wrap = el("div", "scene", stageEl);
      wrap.style.display = "none";
      var p = s.payload || {};
      if (p.eyebrow) el("div", "eyebrow", wrap, String(p.eyebrow));
      if (s.headline) s._head = headlineNode(wrap, s.headline, p.accent_word);
      var art = el("div", "artifact", wrap);
      s._art = art;
      s._wrap = wrap;
      s._refs = ARCH[s.archetype].build(art, s);
    });
    fitScenes();
    capEl = el("div", "caption", stageEl);
    window.ready = true;
  }

  /* One layout pass after the DOM exists: shrink a long headline until it holds in three lines, then hang
   * the artifact and its hairline off the real bottom of the type. No scene is allowed to leave a void. */
  function fitScenes() {
    D.scenes.forEach(function (s) {
      var wrap = s._wrap;
      wrap.style.display = "block";
      if (s._head) {
        var len = String(s.headline || "").length;
        var size = len <= 14 ? 104 : len <= 22 ? 92 : len <= 32 ? 78 : 66;
        s._head.style.fontSize = size + "px";
        var guard = 0;
        while (s._head.offsetHeight > 250 && size > 42 && guard++ < 30) {
          size -= 4;
          s._head.style.fontSize = size + "px";
        }
      }
      var top = s._head ? Math.max(292, 196 + s._head.offsetHeight + 34) : 292;
      s._art.style.top = top + "px";
      s._art.style.height = (1584 - top) + "px";
      s._rule = el("div", "rule", wrap);
      s._rule.style.top = (top - 26) + "px";
      wrap.style.display = "none";
    });
  }

  function activeIndex(t) {
    var sc = D.scenes;
    for (var k = 0; k < sc.length; k++) if (t >= sc[k].t0 && t < sc[k].t1) return k;
    return t < 0 ? 0 : sc.length - 1;
  }

  function drawCaption(s, t) {
    var words = s.words || [], cur = -1;
    for (var i = 0; i < words.length; i++) if (t >= words[i][1]) cur = i;
    var start = Math.max(0, Math.min(cur, words.length - 4));
    var end = Math.min(words.length, start + 4);
    capEl.innerHTML = "";
    for (var j = start; j < end; j++) {
      el("span", j === cur ? "cw cw-on" : "cw", capEl, words[j][0]);
    }
  }

  window.setTime = function (t) {
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    var u = t - s.t0, d = Math.max(1e-6, s.t1 - s.t0);
    // hard cut: the scene is simply present from its first frame (no cross-fade anywhere in this template)
    if (s._head) {
      var hp = eCubic(ramp(u, 0, 0.26));
      s._head.style.opacity = "1";
      s._head.style.transform = "translateY(" + fmt((1 - hp) * 26) + "px)";
    }
    if (s._rule) {                                   // the hairline draws in on the cut
      var rp = eCubic(ramp(u, 0, 0.42));
      s._rule.style.transformOrigin = "0 50%";
      s._rule.style.transform = "scaleX(" + fmt(rp, 3) + ")";
    }
    var eb = s._wrap.querySelector(".eyebrow");
    if (eb) eb.style.opacity = fmt(ramp(u, 0, 0.3));
    // camera: a slow punch-in keeps a single artifact from sitting still
    var cam = (s.payload && s.payload.cam) || [1.0, 1.085];
    var cp = eCubic(ramp(u, 0, d));
    var drift = (s.payload && typeof s.payload.drift === "number") ? s.payload.drift : 9;
    var dx = (cp - 0.35) * drift;
    s._art.style.transform = "translate(" + fmt(dx, 2) + "px, 0px) scale(" +
      fmt(cam[0] + (cam[1] - cam[0]) * cp, 4) + ")";
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
    // a one-pixel paper breath so nothing is ever bit-identical between frames
    stageEl.style.backgroundPosition = fmt(t * 7, 2) + "px 0px";
  };

  build();
})();
