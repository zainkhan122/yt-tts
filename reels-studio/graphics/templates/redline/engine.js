/* redline: a paper report being marked up in red pen.
 * Pure function of setTime(t) — no timers, no transitions.
 * Grammar: warm paper, black ink, ONE red accent. Ruled lines draw on. Rows get struck out.
 * Captions are set as a footnote band in the same mono as the document.
 */
(function () {
  "use strict";
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var PAPER = "#F2EEE6", INK = "#16150F", MUTED = "#6E6A5E", RULE = "#CFC8B8",
      RED = "#D8341C", GREEN = "#2E6B4F", CARD = "#FBF8F2";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var eCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var eExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var eBack = function (x) { x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 2 : n); };
  var norm = function (w) { return String(w).toLowerCase().replace(/[^a-z0-9]/g, ""); };

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
    s.setAttribute("width", w); s.setAttribute("height", h);
    if (cls) s.setAttribute("class", cls);
    if (parent) parent.appendChild(s);
    return s;
  };
  var sEl = function (tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  var sText = function (x, y, str, attrs, parent) {
    var t = sEl("text", attrs || { fill: INK }, parent);
    t.setAttribute("x", x); t.setAttribute("y", y);
    t.textContent = String(str === undefined || str === null ? "" : str);
    return t;
  };

  /* moment a spoken phrase lands, else an even stagger inside the scene */
  function bindTimes(phrases, s, n) {
    return window.HouseMotion.cueTimes(phrases, s, n, {fallback:"redline"});
  }

  /* ruled paper background: horizontal hairlines + a red margin rule */
  function paperRules(root) {
    var g = svg(1080, 1920, root, "rl-rules");
    for (var y = 150; y < 1880; y += 62) {
      sEl("line", { x1: 0, y1: y, x2: 1080, y2: y, stroke: RULE, "stroke-width": 1, opacity: 0.55 }, g);
    }
    sEl("line", { x1: 96, y1: 120, x2: 96, y2: 1860, stroke: RED, "stroke-width": 2, opacity: 0.5 }, g);
    return g;
  }

  function pad2(n) { n = Number(n || 0) + 1; return (n < 10 ? "0" : "") + n; }
  /* every sheet carries a page number, so each scene reads as a page of one report */
  function pageNum(root, s) { el("div", "rl-pnum", root, "PAGE " + pad2(s.idx)); }

  var ARCH = {};

  /* doc_title: the cover of the report. Kicker, big title, then the rule lines draw in. */
  ARCH.doc_title = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      pageNum(root, s);
      var sheet = el("div", "rl-sheet", root);
      el("div", "rl-kicker", sheet, p.kicker || "REPORT");
      r.title = el("div", "rl-title", sheet);
      r.title.textContent = s.headline || p.title || "";
      r.rule = el("i", "rl-rule", sheet);
      r.lines = (p.lines || []).map(function (t) {
        var row = el("div", "rl-line", sheet);
        el("em", null, row, t);
        return { row: row, t: t };
      });
      r.times = bindTimes(p.cue_phrases, s, r.lines.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      r.title.style.opacity = fmt(ramp(u, 0.05, 0.35));
      r.title.style.transform = "translateY(" + fmt((1 - eCubic(ramp(u, 0.05, 0.45))) * 24, 1) + "px)";
      r.rule.style.width = fmt(eExpo(ramp(u, 0.2, 0.8)) * 100, 1) + "%";
      r.lines.forEach(function (x, i) {
        var p = eCubic(ramp(now - r.times[i], 0, 0.4));
        x.row.style.opacity = fmt(p);
        x.row.style.transform = "translateX(" + fmt((1 - p) * -26, 1) + "px)";
      });
    }
  };

  /* strike_list: the four plugins, each struck through in red as it is spoken. */
  ARCH.strike_list = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      pageNum(root, s);
      var sheet = el("div", "rl-sheet", root);
      if (p.note) el("div", "rl-kicker", sheet, p.note);
      r.rows = (p.rows || []).map(function (spec) {
        var row = el("div", "rl-strike", sheet);
        el("span", "no", row, spec.no || "");
        var body = el("div", "body", row);
        el("b", null, body, spec.name || "");
        el("s", null, body, spec.what || "");
        var bar = el("i", "bar", row);
        return { row: row, bar: bar };
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      r.rows.forEach(function (x, i) {
        var inP = eCubic(ramp(now - r.times[i], 0, 0.35));
        x.row.style.opacity = fmt(inP);
        x.row.style.transform = "translateY(" + fmt((1 - inP) * 18, 1) + "px)";
        /* the strike lands a beat after the row appears */
        var st = eExpo(ramp(now - r.times[i] - 0.45, 0, 0.42));
        x.bar.style.width = fmt(st * 100, 1) + "%";
      });
    }
  };

  /* number_stamp: one measured number, stamped like a figure in a printed report. */
  ARCH.number_stamp = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      var sheet = el("div", "rl-sheet rl-figure", root);
      el("div", "rl-kicker", sheet, p.caption || "MEASURED");
      r.box = el("div", "rl-stamp", sheet);
      r.num = el("div", "n", r.box);
      if (p.sub) r.sub = el("div", "s", r.box, p.sub);
      r.foot = el("div", "rl-foot", sheet, p.note || "");
      r.when = bindTimes(p.cue_phrases, s, 1)[0];
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload || {}, since = s.t0 + u - r.when;
      var val = parseFloat(p.value) || 0;
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      var k = eExpo(ramp(since, 0, 0.7));
      r.num.textContent = since < 0 ? "—" : Math.round(val * k) + (p.suffix || "");
      var pop = eBack(ramp(since, 0, 0.35));
      r.box.style.transform = "scale(" + fmt(0.9 + 0.1 * pop, 3) + ") rotate(-1.4deg)";
      r.box.style.opacity = fmt(0.35 + 0.65 * ramp(since, 0, 0.2));
      r.foot.style.opacity = fmt(ramp(since, 0.25, 0.55));
    }
  };

  /* score_rules: a scored table — the claim, a red score, and a hairline that fills. */
  ARCH.score_rules = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      pageNum(root, s);
      var sheet = el("div", "rl-sheet", root);
      el("div", "rl-kicker", sheet, p.title || "FIELD NOTES");
      r.rows = (p.rows || []).map(function (spec) {
        var row = el("div", "rl-score" + (spec.score === undefined ? " no-bar" : ""), sheet);
        el("b", null, row, spec.t || "");
        var track = el("i", "track", row);
        var fill = el("u", null, track);
        el("em", null, row, spec.val || "");
        return { row: row, fill: fill, score: spec.score === undefined ? 0 : spec.score };
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      r.rows.forEach(function (x, i) {
        var p = eCubic(ramp(now - r.times[i], 0, 0.4));
        x.row.style.opacity = fmt(p);
        x.fill.style.width = fmt(x.score * eExpo(ramp(now - r.times[i], 0.1, 0.65)) * 100, 1) + "%";
      });
    }
  };

  /* margin_note: the honest catch, written in the margin and underlined by hand. */
  ARCH.margin_note = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      var sheet = el("div", "rl-sheet rl-margin", root);
      r.card = el("div", "rl-note", sheet);
      el("div", "rl-kicker", r.card, "MARGIN NOTE");
      r.quote = el("blockquote", null, r.card, "\u201C" + (p.note || "") + "\u201D");
      r.attrib = el("div", "attrib", r.card, "\u2014 " + (p.attrib || ""));
      r.underline = el("i", "ul", r.card);
      return r;
    },
    update: function (r, s, u, d) {
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      r.card.style.opacity = fmt(ramp(u, 0.08, 0.32));
      r.card.style.transform = "translateY(" + fmt((1 - eCubic(ramp(u, 0.08, 0.5))) * 30, 1) + "px)";
      r.quote.style.opacity = fmt(ramp(u, 0.2, 0.45));
      r.attrib.style.opacity = fmt(ramp(u, 0.5, 0.8));
      r.underline.style.width = fmt(eExpo(ramp(u, 0.55, 0.95)) * 100, 1) + "%";
    }
  };

  /* endcard: the last page, signed off. */
  /* endcard: BYPASSED — graphics/outro.js draws the single house brand card for every short.
     Kept as a stub so the beat planner can still name the archetype. */
  ARCH.endcard = {
    build: function (root, s) {
      var host = el("div", "house-endcard-host", root);
      host.style.cssText = "position:absolute;inset:0;";
      return { house: true, host: host };
    },
    update: function () { /* the house layer owns this scene */ }
  };

  /* ================= stage + captions ================= */
  var stageEl = document.getElementById("stage");
  var capEl;

  function build() {
    el("div", "rl-head", stageEl, D.handle || "");
    D.scenes.forEach(function (s, si) {
      s.idx = si;
      var wrap = el("div", "scene", stageEl);
      wrap.setAttribute("data-scene", s.id);   // house layer mounts the house outro here
      wrap.style.display = "none";
      var head = el("div", "rl-overline", wrap, s.headline || "");
      head.className = "rl-overline";
      head.style.display = "none";           /* the archetype owns the type; headline is spoken */
      var visual = el("div", "visual", wrap);
      s._wrap = wrap; s._visual = visual;
      s._refs = ARCH[s.archetype].build(visual, s);
    });
    capEl = el("div", "rl-foot-band", stageEl);
    window.ready = true;
  }

  function activeIndex(t) {
    var sc = D.scenes;
    for (var k = 0; k < sc.length; k++) if (t >= sc[k].t0 && t < sc[k].t1) return k;
    return t < 0 ? 0 : sc.length - 1;
  }

  function drawCaption(s, t) {
    var words = s.words || [];
    var cur = -1;
    for (var i = 0; i < words.length; i++) if (t >= words[i][1]) cur = i;
    var start = Math.max(0, Math.min(cur, words.length - 4));
    var end = Math.min(words.length, start + 4);
    capEl.innerHTML = "";
    for (var j = start; j < end; j++) {
      var w = el("span", "cw" + (j === cur ? " on" : ""), capEl, words[j][0]);
      if (j === cur) w.style.transform = "scale(" + fmt(1.1 - 0.1 * eCubic(ramp(t - words[j][1], 0, 0.16)), 3) + ")";
    }
  }

  window.setTime = function (t) {
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    // House layer owns the outro; hide the entire template scene.
    if (s.archetype === "endcard") { D.scenes.forEach(function (x) { x._wrap.style.display = "none"; }); return; }
    var u = t - s.t0, d = Math.max(1e-6, s.t1 - s.t0);
    var enter = eCubic(ramp(u, 0, 0.28));
    s._visual.style.opacity = fmt(0.7 + 0.3 * enter);
    s._visual.style.transform = "translateY(" + fmt((1 - enter) * 12, 1) + "px)";
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
  };

  build();
})();
