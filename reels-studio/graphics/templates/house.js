/* house.js — the house visual language, used by the HOUSE engine (the default template).
 *
 * The reference reels (v1/v2/v3) do not look like "cards on a dark background". They look like a
 * magazine spread: a paper plate, a hand-drawn illustration built from composed props, a
 * monospace HUD, and sentence-case typography with an italic serif accent. This file is that
 * language, written once, so the house engine draws in it by default.
 *
 * Scope: the house engine only. A per-tool template has its own engine and its own vocabulary,
 * and it gets the shared caption/outro layer instead (shared.js + outro.js). A per-tool engine
 * never reads window.HOUSE — the two stylesheets do not even share variables — so this library is
 * NOT injected into a per-tool template.
 *
 * Contract: window.HOUSE = { ARCH, plate, setPlate, col, ... }
 *   - ARCH  : { archetypeName: { build(root, s), update(r, s, u, d) } }
 *             build() draws the DOM once; update(r, s, u, d) redraws it for frame time u
 *             (u = seconds since the scene started, d = the scene's duration).
 *   - Every archetype is a pure function of t. No timers, no CSS transitions, no randomness that
 *     changes between frames.
 *
 * Loaded by render.build_stage_html for every template, right after gsap and before the
 * template's own engine.js. A template opts in with one line:
 *     Object.keys(window.HOUSE.ARCH).forEach(function (k) { ARCH[k] = window.HOUSE.ARCH[k]; });
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var D = window.DATA || {};

  /* ---------------------------------------------------------------- helpers */
  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 2 : n); };
  var comma = function (n) {
    var s = String(Math.round(n)), out = "", c = 0;
    for (var i = s.length - 1; i >= 0; i--) {
      out = s[i] + out; if (++c % 3 === 0 && i > 0) out = "," + out;
    }
    return out;
  };
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
    s.setAttribute("preserveAspectRatio", "xMidYMid meet");
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
    var t = sEl("text", attrs || {}, parent);
    t.setAttribute("x", x); t.setAttribute("y", y);
    t.textContent = str;
    return t;
  };

  /* Easing: GSAP's curves when the vendored lib is present, hand-rolled fallbacks otherwise. */
  var eCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var eExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var eBack = function (x) {
    x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  };
  var eInOut = eExpo;
  var E = { cubic: eCubic, expo: eExpo, back: eBack, inOut: eInOut, spring: eBack, snappy: eBack };
  if (window.gsap && window.gsap.parseEase) {
    var pe = window.gsap.parseEase;
    E.spring = pe("elastic.out(1, 0.6)");
    E.snappy = pe("back.out(2.2)");
    E.inOut = pe("power4.inOut");
    E.quint = pe("power4.out");
  }
  function ez(name, x) { return (E[name] || eCubic)(x); }

  /* ---------------------------------------------------------------- palette + plates */
  /* A plate is the mood of a scene: the paper it is printed on. The reference reels switch plate
   * mid-video (cream -> ink -> slate -> cream). That rhythm is what makes them feel edited. */
  var PLATES = {
    paper: { bg: "#F7F5EF", ink: "#14161F", mute: "#8A8579", line: "#14161F", accent: "#D93025", accent2: "#1F5F8B", card: "#FFFFFF", soft: "#EDEAE1", grain: 0.05, dots: 0.06, grid: false, glow: false },
    ink:   { bg: "#0B0B0C", ink: "#F5F3ED", mute: "#8B8B88", line: "#3A3A3C", accent: "#FF5B4A", accent2: "#5AC8FA", card: "#17181A", soft: "#222326", grain: 0.10, dots: 0.0, grid: false, glow: false },
    slate: { bg: "#B4B7B2", ink: "#14161F", mute: "#5A5E58", line: "#3A3E38", accent: "#D93025", accent2: "#1F5F8B", card: "#FFFFFF", soft: "#A2A59F", grain: 0.07, dots: 0.0, grid: false, glow: false },
    dots:  { bg: "#E9EAEE", ink: "#14161F", mute: "#878A93", line: "#C3C6CE", accent: "#E0407A", accent2: "#6C4CF1", card: "#FFFFFF", soft: "#DCDEE4", grain: 0.04, dots: 0.55, grid: false, glow: false },
    deep:  { bg: "#0C0E13", ink: "#F5F5F0", mute: "#9AA6B8", line: "#2A3140", accent: "#FFD60A", accent2: "#38BDF8", card: "#141925", soft: "#1A2030", grain: 0.10, dots: 0.0, grid: true, glow: true }
  };
  var currentPlate = "deep";

  function palette() {
    var p = PLATES[currentPlate] || PLATES.deep;
    var over = (D.palette || {});
    var out = {};
    for (var k in p) out[k] = p[k];
    for (var k2 in over) if (over[k2] != null) out[k2] = over[k2];
    return out;
  }
  function col(name) { var p = palette(); return p[name] || p.ink; }

  /* setPlate(name) repaints the stage: CSS variables + the ambient layer's colour. */
  function setPlate(name) {
    if (!PLATES[name]) return;
    currentPlate = name;
    /* The merged palette: the plate's own colours, overridden by the tool's visual language. */
    var p = palette();
    var st = document.getElementById("stage");
    if (st) {
      st.setAttribute("data-plate", name);
      st.style.setProperty("--plate-bg", p.bg);
      st.style.setProperty("--plate-ink", p.ink);
      st.style.setProperty("--plate-mute", p.mute);
      st.style.setProperty("--plate-line", p.line);
      st.style.setProperty("--plate-accent", p.accent);
      st.style.setProperty("--plate-accent2", p.accent2);
      st.style.setProperty("--plate-card", p.card);
      st.style.setProperty("--plate-soft", p.soft);
      st.style.setProperty("--plate-grain", String(p.grain));
      st.style.setProperty("--plate-dots", String(p.dots));
    }
    var raw = PLATES[name];
    var g = document.getElementById("grid");
    if (g) g.style.opacity = raw.grid ? "" : "0";
    var dots = document.getElementById("plate-dots");
    if (dots) dots.style.opacity = raw.dots ? "" : "0";
    var glow = document.getElementById("glow");
    if (glow) glow.style.opacity = raw.glow ? "" : "0";
    /* The travelling sheen is a LIGHT on a dark plate and a soft SHADOW on a paper plate. */
    var dark = raw.bg === PLATES.ink.bg || raw.bg === PLATES.deep.bg || raw.bg === PLATES.slate.bg;
    if (st) st.style.setProperty("--house-sheen", dark ? "rgba(255,255,255,0.115)" : "rgba(28,30,40,0.10)");
  }

  /* ---------------------------------------------------------------- typography helpers */
  /* The house voice: a sentence-case grotesk for the statement, an ITALIC SERIF for the emphasis
   * word, a monospace for the HUD. All caps everywhere is the generic-AI-short look; the reference
   * reels are not that. */
  function richText(node, text, opts) {
    opts = opts || {};
    node.innerHTML = "";
    var parts = String(text || "").split(/\s+/).filter(Boolean);
    var explicit = /[*_][^*_]+[*_]/.test(text || "");
    var inside = false;
    parts.forEach(function (w, i) {
      var word = w, on = inside;
      if (explicit) {
        if (word.charAt(0) === "*" || word.charAt(0) === "_") { word = word.slice(1); on = inside = true; }
        var close = inside ? word.match(/^(.*?)[*_](\W*)$/) : null;
        if (close) { word = close[1] + close[2]; inside = false; }
      }
      /* The space goes INSIDE the span: a whitespace-only text node between flex items is not
       * rendered, which would run every word together. */
      var sp = el("span", on ? "em" : "", node, word + (i < parts.length - 1 ? " " : ""));
      if (opts.accentWords && opts.accentWords[norm(word)]) sp.className = "kw";
    });
    return node;
  }

  /* Shrink a text node until it fits its box. Long tool names must never overflow a card. */
  function fitText(node, maxW, minPx, startPx) {
    var fs = startPx || parseFloat(getComputedStyle(node).fontSize) || 40;
    node.style.fontSize = fs + "px";
    var guard = 0;
    while (fs > (minPx || 14) && node.scrollWidth > maxW && guard++ < 60) {
      fs -= 2; node.style.fontSize = fs + "px";
    }
    return fs;
  }

  /* ---------------------------------------------------------------- HUD chrome */
  /* The persistent frame furniture: a monospace scene label on the left, a live metric on the
   * right. It is what makes a sequence of scenes read as one edited film. */
  function hud(parent, label, metric, value) {
    var h = el("div", "hud", parent);
    var l = el("div", "hud-l", h, label || "");
    var m = el("div", "hud-r", h);
    el("span", "hud-m", m, metric || "");
    el("span", "hud-v", m, value == null ? "" : String(value));
    return h;
  }

  /* ---------------------------------------------------------------- prop drawing (stage_board) */
  /* Each prop is a small illustration. Together they compose a scene the way the reference reels
   * compose theirs: one hero object, a couple of supporting objects, labels and a stamp. */
  var PROPS = {};

  /* hard-shadow card (the reference's offset-print look) */
  PROPS.card = function (g, p, W) {
    var accent = p.accent || col("accent");
    var r = el("div", "p-card", g);
    r.style.setProperty("--pc-accent", accent);
    if (p.title) { var t = el("div", "p-card-t", r, p.title); fitText(t, W * p.w - 44, 16, 34); }
    if (p.value) { var v = el("div", "p-card-v", r, p.value); fitText(v, W * p.w - 44, 16, 40); }
    if (p.note) el("div", "p-card-n", r, p.note);
    return r;
  };

  /* an app / browser window with real chrome */
  PROPS.window = function (g, p, W) {
    var win = el("div", "p-window", g);
    var bar = el("div", "p-titlebar", win);
    ["#ff5f57", "#febc2e", "#28c840"].forEach(function (c) { var d = el("span", "p-tb-dot", bar); d.style.background = c; });
    if (p.title) el("div", "p-titlebar-t", bar, p.title);
    var body = el("div", "p-win-b", win);
    (p.rows || []).forEach(function (row, i) {
      var r = el("div", "p-row", body);
      el("span", "p-row-k", r, row[0] || "");
      el("span", "p-row-v", r, row[1] || "");
      if (i === 0) r.classList.add("on");
    });
    if (p.input) {
      var inp = el("div", "p-input", body);
      el("span", "p-caret-b", inp);
      el("span", "p-input-t", inp, p.input);
    }
    return win;
  };

  /* a console panel with a grid of icon buttons and a count badge (the "CLAUDE PLUGINS 11/11" device) */
  PROPS.panel = function (g, p, W) {
    var pan = el("div", "p-panel", g);
    var head = el("div", "p-panel-h", pan);
    el("span", "p-panel-t", head, p.title || "");
    if (p.value) el("span", "p-panel-v", head, p.value);
    var cam = el("div", "p-panel-cam", pan);
    var grid = el("div", "p-icons", pan);
    var n = Math.max(4, Math.min(18, p.count || 9));
    for (var i = 0; i < n; i++) {
      var b = el("div", "p-icon", grid);
      var r = 5 + (i % 4);
      var rr = el("div", "p-icon-g", b);
      rr.style.borderRadius = r + "px";
      if (p.highlight === i) rr.classList.add("hot");
    }
    return pan;
  };
  /* a dot-matrix (the "295 skills in one repo" grid) */
  PROPS.matrix = function (g, p, W) {
    var m = el("div", "p-matrix", g);
    var cols = p.cols || 18;
    var rows = Math.ceil((p.total || 240) / cols);
    var hot = p.highlight || 12;
    for (var i = 0; i < rows * cols; i++) {
      var d = el("div", "p-dot", m);
      if (i < hot) d.classList.add("hot");
      else if (i % 7 === 3) d.classList.add("warm");
    }
    if (p.label) el("div", "p-matrix-l", m, p.label);
    return m;
  };

  /* a stack of isometric layers (the "10,000 replays" pile) */
  PROPS.stack = function (g, p, W) {
    var s = el("div", "p-stack", g);
    var n = p.layers || 16;
    var cols = p.colors || ["#C0392B", "#2C3E6B", "#3B7A4B"];
    for (var i = 0; i < n; i++) {
      var l = el("div", "p-layer", s);
      l.style.background = cols[i % cols.length];
      l.style.setProperty("--lz", String(i));
    }
    if (p.label) el("div", "p-stack-l", s, p.label);
    return s;
  };

  /* a dial / gauge */
  PROPS.gauge = function (g, p, W) {
    var w = el("div", "p-gauge", g);
    var s = svg(200, 200, w, "p-gauge-s");
    sEl("circle", { cx: 100, cy: 100, r: 86, fill: "none", stroke: col("line"), "stroke-width": 10, opacity: 0.5 }, s);
    sEl("circle", { cx: 100, cy: 100, r: 86, fill: "none", stroke: col("accent"), "stroke-width": 10, "stroke-linecap": "round",
                    "stroke-dasharray": 540, "stroke-dashoffset": 540, transform: "rotate(-90 100 100)" }, s).setAttribute("data-arc", "1");
    for (var i = 0; i <= 10; i++) {
      var a = (-220 + i * 26) * Math.PI / 180;
      sEl("line", { x1: 100 + Math.cos(a) * 70, y1: 100 + Math.sin(a) * 70,
                    x2: 100 + Math.cos(a) * 60, y2: 100 + Math.sin(a) * 60,
                    stroke: col("line"), "stroke-width": 4, "stroke-linecap": "round", opacity: 0.55 }, s);
    }
    sEl("line", { x1: 100, y1: 100, x2: 100, y2: 34, stroke: col("ink"), "stroke-width": 8, "stroke-linecap": "round" }, s).setAttribute("data-needle", "1");
    sEl("circle", { cx: 100, cy: 100, r: 10, fill: col("ink") }, s);
    if (p.value) { var v = el("div", "p-gauge-v", w, p.value); fitText(v, 180, 16, 46); }
    if (p.label) el("div", "p-gauge-l", w, p.label);
    return w;
  };

  /* a sticky / label chip with an optional tick */
  PROPS.note = function (g, p, W) {
    var n = el("div", "p-note", g);
    if (p.check) el("span", "p-note-c", n, "✓");
    var t = el("span", "p-note-t", n, p.label || "");
    fitText(t, W * p.w - 60, 12, 26);
    return n;
  };

  /* a rubber stamp */
  PROPS.stamp = function (g, p, W) {
    var s = el("div", "p-stamp", g);
    var inner = el("div", "p-stamp-in", s);
    el("div", "p-stamp-t", inner, p.label || "");
    if (p.note) el("div", "p-stamp-n", inner, p.note);
    s.style.setProperty("--ps-accent", p.accent || col("accent"));
    return s;
  };

  /* a manila folder */
  PROPS.folder = function (g, p, W) {
    var f = el("div", "p-folder", g);
    el("div", "p-folder-tab", f, p.tab || "");
    var body = el("div", "p-folder-b", f);
    var lab = el("div", "p-folder-l", body, p.label || "");
    fitText(lab, W * p.w - 60, 14, 34);
    if (p.note) el("div", "p-folder-n", body, p.note);
    return f;
  };

  /* a balance scale */
  PROPS.scale = function (g, p, W) {
    var s = el("div", "p-scale", g);
    var sv = svg(240, 220, s, "p-scale-s");
    sEl("path", { d: "M120 40 L120 190", stroke: col("ink"), "stroke-width": 8, "stroke-linecap": "round" }, sv);
    sEl("path", { d: "M50 190 L190 190", stroke: col("ink"), "stroke-width": 10, "stroke-linecap": "round" }, sv);
    sEl("path", { d: "M40 62 L200 62", stroke: col("ink"), "stroke-width": 8, "stroke-linecap": "round" }, sv);
    sEl("path", { d: "M40 62 L20 110 L60 110 Z", fill: "none", stroke: col("ink"), "stroke-width": 6 }, sv);
    sEl("path", { d: "M200 62 L180 110 L220 110 Z", fill: "none", stroke: col("ink"), "stroke-width": 6 }, sv);
    if (p.left) { var L = el("div", "p-scale-l", s, p.left); L.style.left = "0px"; }
    if (p.right) { var R = el("div", "p-scale-r", s, p.right); R.style.right = "0px"; }
    return s;
  };

  /* a small sparkline in a frame */
  PROPS.spark = function (g, p, W) {
    var w = el("div", "p-spark", g);
    var s = svg(320, 120, w, "p-spark-s");
    var n = 14, vals = [], seed = 7;
    for (var i = 0; i < n; i++) { seed = (seed * 9301 + 49297) % 233280; vals.push(20 + (seed / 233280) * 70); }
    if (p.trend === "up") { vals[n - 1] = 8; vals[0] = 92; }
    var d = "M0 120", pts = [];
    for (var k = 0; k < n; k++) {
      var x = (k / (n - 1)) * 320, y = 120 - vals[k];
      d += " L" + fmt(x, 1) + " " + fmt(y, 1);
      pts.push([x, y]);
    }
    sEl("path", { d: d, fill: "none", stroke: col("accent"), "stroke-width": 5, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);
    pts.forEach(function (pt) { sEl("circle", { cx: pt[0], cy: pt[1], r: 5, fill: col("accent") }, s); });
    if (p.label) el("div", "p-spark-l", w, p.label);
    return w;
  };

  /* a horizontal bar (a single ranked value) */
  PROPS.bar = function (g, p, W) {
    var b = el("div", "p-bar", g);
    if (p.label) el("div", "p-bar-l", b, p.label);
    var track = el("div", "p-bar-t", b);
    var fill = el("div", "p-bar-f", track);
    fill.style.setProperty("--pv", String(p.value || 0.6));
    fill.style.background = p.accent || col("accent");
    if (p.note) el("div", "p-bar-n", b, p.note);
    return b;
  };

  /* a 3x3 grid of little cells with avatar glyphs (the "shop window" of v1) */
  PROPS.cells = function (g, p, W) {
    var g2 = el("div", "p-cells", g);
    var cols = p.cols || 4, rows = p.rows || 3;
    for (var i = 0; i < cols * rows; i++) {
      var c = el("div", "p-cell", g2);
      var av = el("div", "p-cell-av", c);
      el("div", "p-cell-h", av);
      el("div", "p-cell-b", av);
      el("div", "p-cell-r", c);
      if (p.marks && p.marks.indexOf(i) >= 0) el("div", "p-cell-m", c, "✓");
    }
    return g2;
  };

  /* an envelope with a wax seal */
  PROPS.envelope = function (g, p, W) {
    var e = el("div", "p-env", g);
    el("div", "p-env-b", e);
    var f = el("div", "p-env-f", e);
    el("div", "p-env-s", f, "✦");
    if (p.label) el("div", "p-env-l", e, p.label);
    return e;
  };

  /* a simple machine / device (the "mail merge sequence" panel) */
  PROPS.machine = function (g, p, W) {
    var m = el("div", "p-machine", g);
    if (p.title) el("div", "p-machine-t", m, p.title);
    var body = el("div", "p-machine-b", m);
    (p.slots || []).forEach(function (sl) {
      var s = el("div", "p-slot", body);
      el("div", "p-slot-l", s, sl);
    });
    if (p.note) el("div", "p-machine-n", m, p.note);
    return m;
  };

  /* ---------------------------------------------------------------- the shared archetypes */
  var ARCH = {};

  /* stage_board: the illustration stage. The agent lays out props in normalised coordinates; each
   * prop springs in on its own spoken word. This is the scene type that makes a short look drawn. */
  ARCH.stage_board = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "board", root), props: [], notes: [], stamp: null };
      var bg = el("div", "board-bg", r.wrap);
      if (p.plate) r.plate = p.plate;
      (p.props || []).forEach(function (prop, i) {
        var holder = el("div", "prop", r.wrap);
        holder.style.left = fmt((prop.x || 0) * 100, 2) + "%";
        holder.style.top = fmt((prop.y || 0) * 100, 2) + "%";
        holder.style.width = fmt((prop.w || 0.3) * 100, 2) + "%";
        holder.style.height = fmt((prop.h || 0.22) * 100, 2) + "%";
        if (prop.z) holder.style.zIndex = String(prop.z);
        var fn = PROPS[prop.kind || "card"];
        var node = fn ? fn(holder, prop, 960) : PROPS.card(holder, prop, 960);
        node.style.width = "100%"; node.style.height = "100%";
        r.props.push({ holder: holder, node: node, prop: prop });
      });
      (p.notes || []).forEach(function (n) {
        var holder = el("div", "prop note-prop", r.wrap);
        holder.style.left = fmt((n.x || 0.5) * 100, 2) + "%";
        holder.style.top = fmt((n.y || 0.1) * 100, 2) + "%";
        holder.style.width = fmt((n.w || 0.22) * 100, 2) + "%";
        var node = PROPS.note(holder, n, 960);
        r.notes.push({ holder: holder, node: node });
      });
      if (p.stamp) {
        var sh = el("div", "prop stamp-prop", r.wrap);
        sh.style.left = fmt((p.stamp.x || 0.62) * 100, 2) + "%";
        sh.style.top = fmt((p.stamp.y || 0.08) * 100, 2) + "%";
        r.stamp = { holder: sh, node: PROPS.stamp(sh, p.stamp, 960) };
      }
      if (p.cable === true) {
        var cab = el("div", "board-cable", r.wrap);
        r.cable = cab;
      }
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload || {};
      if (r.plate) setPlate(r.plate);
      var cues = s.cues || [];
      r.props.forEach(function (x, i) {
        var c = cues[i] !== undefined ? cues[i] : (s.t0 + 0.1 + i * 0.35);
        var t = u + s.t0 - c;
        var k = ez("spring", ramp(t, 0, 0.55));
        x.holder.style.opacity = fmt(ramp(t, -0.1, 0.12));
        x.holder.style.transform = "translateY(" + fmt((1 - k) * 60, 2) + "px) scale(" + fmt(0.86 + 0.14 * k, 3) + ")";
        x.holder.style.transformOrigin = "50% 100%";
      });
      r.notes.forEach(function (x, i) {
        var c = cues[r.props.length + i] !== undefined ? cues[r.props.length + i] : (s.t0 + 0.4 + i * 0.2);
        var t = u + s.t0 - c;
        x.holder.style.opacity = fmt(ramp(t, 0, 0.18));
        x.holder.style.transform = "translateY(" + fmt((1 - ez("back", ramp(t, 0, 0.35))) * 24, 2) + "px)";
      });
      if (r.stamp) {
        var sc = cues.length ? cues[cues.length - 1] : (s.t0 + d * 0.5);
        var st = u + s.t0 - sc;
        var k2 = ez("back", ramp(st, 0, 0.32));
        r.stamp.holder.style.opacity = fmt(ramp(st, 0, 0.1));
        r.stamp.holder.style.transform = "translate(" + fmt((1 - k2) * 220, 1) + "px," + fmt((1 - k2) * -120, 1) + "px) rotate(" + fmt(-16 + k2 * 16, 2) + "deg) scale(" + fmt(1.5 - 0.5 * k2, 3) + ")";
      }
      if (r.cable) {
        var prog = ramp(u + s.t0 - (cues[0] || s.t0), 0, 0.9);
        r.cable.style.opacity = fmt(prog * 0.55);
        r.cable.style.height = fmt(prog * 100, 2) + "%";
      }
    }
  };

  /* chart_bars: a real bar chart with an axis, labels and values. */
  ARCH.chart_bars = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "chart chart-bars", root), bars: [] };
      var labels = p.labels || [], values = p.values || [];
      var max = p.max || Math.max.apply(null, values.map(function (v) { return Number(v); }).concat([1]));
      /* The plot is its own box so the grid lines and the bars share one height: the chart then
       * fills the whole visual band instead of leaving a dead strip under it. */
      var plot = el("div", "ch-plot", r.wrap);
      var grid = el("div", "ch-grid", plot);
      for (var i = 0; i <= 4; i++) { var gl = el("div", "ch-gl", grid); gl.style.bottom = fmt(i * 25, 1) + "%"; }
      var row = el("div", "ch-row", plot);
      labels.forEach(function (lab, i) {
        var b = el("div", "ch-bar-wrap", row);
        var track = el("div", "ch-track", b);
        var pct = clamp(Number(values[i]) / max, 0, 1) * 100;
        var fill = el("div", "ch-fill", track);
        fill.style.height = fmt(pct, 2) + "%";
        fill.style.background = (p.highlight === i) ? col("accent") : col("accent2");
        var v = el("div", "ch-val", track, comma(values[i]) + (p.unit || ""));
        v.style.bottom = fmt(pct, 2) + "%";
        var l = el("div", "ch-lab", b, lab);
        fitText(l, 190, 11, 22);
        r.bars.push({ fill: fill, val: v, lab: l, pct: pct });
      });
      if (p.caption) el("div", "ch-cap", r.wrap, p.caption);
      if (p.source) el("div", "ch-src", r.wrap, p.source);
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      r.bars.forEach(function (b, i) {
        var c = cues[i] !== undefined ? cues[i] : (s.t0 + 0.1 + i * 0.3);
        var t = u + s.t0 - c;
        /* The first bar is the one the scene is about: it rises slowly and linearly, so the chart
         * keeps a big moving mass under the voice instead of waiting for the next cue. */
        var k = i === 0 ? ramp(t, 0, 2.6) : ez("expo", ramp(t, 0, 1.4));
        b.fill.style.transform = "scaleY(" + fmt(k, 4) + ")";
        b.fill.style.transformOrigin = "50% 100%";
        /* The value rides the top of the bar as it grows. */
        b.val.style.bottom = fmt(b.pct * k, 2) + "%";
        b.val.style.opacity = fmt(ramp(t, 0.35, 0.6));
        b.val.style.transform = "translate(-50%, " + fmt((1 - ez("back", ramp(t, 0.35, 0.7))) * 16, 2) + "px)";
        b.lab.style.opacity = fmt(ramp(t, -0.05, 0.15));
      });
    }
  };

  /* chart_line: a real line/area chart with an axis and a highlighted point. */
  ARCH.chart_line = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "chart chart-line", root) };
      var W = 880, H = 460, padL = 70, padB = 62, padT = 40;
      var labels = p.labels || [], values = p.values || [];
      var max = p.max || Math.max.apply(null, values.map(function (v) { return Number(v); }).concat([1]));
      var min = p.min != null ? p.min : 0;
      var plot = el("div", "ch-plot", r.wrap);
      var s2 = svg(W, H, plot, "ch-svg");
      var x = function (i) { return padL + (labels.length > 1 ? (i / (labels.length - 1)) * (W - padL - 26) : 0); };
      var y = function (v) { return H - padB - ((Number(v) - min) / Math.max(1e-6, max - min)) * (H - padB - padT); };
      for (var g = 0; g <= 4; g++) {
        var gy = padT + g * ((H - padB - padT) / 4);
        sEl("line", { x1: padL, y1: gy, x2: W - 20, y2: gy, stroke: col("line"), "stroke-width": 2, opacity: 0.28 }, s2);
      }
      var d = "", ad = "";
      values.forEach(function (v, i) { d += (i ? " L" : "M") + fmt(x(i), 1) + " " + fmt(y(v), 1); });
      ad = d + " L" + fmt(x(values.length - 1), 1) + " " + fmt(H - padB, 1) + " L" + fmt(x(0), 1) + " " + fmt(H - padB, 1) + " Z";
      sEl("path", { d: ad, fill: col("accent"), opacity: 0.16 }, s2);
      var line = sEl("path", { d: d, fill: "none", stroke: col("accent"), "stroke-width": 7, "stroke-linecap": "round", "stroke-linejoin": "round" }, s2);
      var len = 2400; line.setAttribute("stroke-dasharray", len); line.setAttribute("stroke-dashoffset", len);
      r.line = line; r.len = len;
      var dots = [];
      values.forEach(function (v, i) {
        var c = sEl("circle", { cx: x(i), cy: y(v), r: 10, fill: col("bg"), stroke: col("accent"), "stroke-width": 5 }, s2);
        dots.push(c);
      });
      r.dots = dots;
      labels.forEach(function (lab, i) {
        var tx = sText(x(i), H - padB + 40, lab, { fill: col("mute"), "font-size": 24, "font-weight": 700, "text-anchor": "middle" }, s2);
      });
      if (p.caption) el("div", "ch-cap", r.wrap, p.caption);
      if (p.source) el("div", "ch-src", r.wrap, p.source);
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      var c = cues.length ? cues[cues.length - 1] : (s.t0 + 0.4);
      var t = u + s.t0 - c;
      var k = ez("expo", ramp(t, 0, 1.1));
      r.line.setAttribute("stroke-dashoffset", fmt(r.len * (1 - k), 1));
      r.dots.forEach(function (dt, i) {
        var p = ramp(k, i / r.dots.length, i / r.dots.length + 0.06);
        dt.setAttribute("opacity", fmt(p));
        dt.setAttribute("r", fmt(7 + 5 * p, 1));
      });
    }
  };

  /* chart_donut: segments of one whole, each on its own word. */
  ARCH.chart_donut = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "chart chart-donut", root), segs: [] };
      var segs = p.segments || [];
      var total = segs.reduce(function (a, b) { return a + Number(b.value || 0); }, 0) || 1;
      var s2 = svg(440, 440, r.wrap, "ch-donut");
      var cx = 220, cy = 220, rad = 168, sw = 58;
      var acc = -Math.PI / 2;
      segs.forEach(function (sg, i) {
        var frac = Number(sg.value || 0) / total;
        var a0 = acc, a1 = acc + frac * Math.PI * 2;
        acc = a1;
        var g = sEl("g", {}, s2);
        var path = sEl("path", {
          d: "M" + fmt(cx + Math.cos(a0) * rad, 1) + " " + fmt(cy + Math.sin(a0) * rad, 1) +
             " A" + rad + " " + rad + " 0 " + (frac > 0.5 ? 1 : 0) + " 1 " +
             fmt(cx + Math.cos(a1) * rad, 1) + " " + fmt(cy + Math.sin(a1) * rad, 1),
          fill: "none", stroke: sg.color || col("accent"), "stroke-width": sw, "stroke-linecap": "butt", opacity: 0.92
        }, g);
        r.segs.push({ path: path, len: frac * 2 * Math.PI * rad });
      });
      var c = el("div", "ch-donut-c", r.wrap);
      el("div", "ch-donut-v", c, p.center_value || "");
      el("div", "ch-donut-l", c, p.center_label || "");
      var legend = el("div", "ch-legend", r.wrap);
      segs.forEach(function (sg, i) {
        var li = el("div", "ch-leg", legend);
        var sw2 = el("span", "ch-leg-s", li);
        sw2.style.background = sg.color || col("accent");
        el("span", "ch-leg-t", li, sg.label || "");
        el("span", "ch-leg-v", li, comma(sg.value) + (p.unit || ""));
      });
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      r.segs.forEach(function (sg, i) {
        var c = cues[i] !== undefined ? cues[i] : (s.t0 + 0.1 + i * 0.25);
        var t = u + s.t0 - c;
        var k = ez("expo", ramp(t, 0, 0.7));
        sg.path.setAttribute("stroke-dasharray", sg.len);
        sg.path.setAttribute("stroke-dashoffset", fmt(sg.len * (1 - k), 1));
      });
    }
  };

  /* compare_split: two columns, one divider, the honest A/B. */
  ARCH.compare_split = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "compare", root), cols: [] };
      /* The columns sit in their own row: the caption is a sibling of the row, not a third column. */
      var row = el("div", "cmp-row2", r.wrap);
      ["left", "right"].forEach(function (side, i) {
        var data = p[side] || { label: side, items: [] };
        var c = el("div", "cmp-col cmp-" + side, row);
        el("div", "cmp-h", c, data.label || "");
        var list = el("div", "cmp-list", c);
        (data.items || []).forEach(function (it) {
          var r2 = el("div", "cmp-row", list);
          el("span", "cmp-ic", r2, side === "left" ? "✕" : "✓");
          el("span", "cmp-t", r2, it);
        });
        r.cols.push({ node: c, list: list, data: data });
      });
      var div = el("div", "cmp-div", row);
      el("div", "cmp-div-l", div);
      r.div = div;
      if (p.caption) el("div", "cmp-cap", r.wrap, p.caption);
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      var total = cues.length || 2;
      r.cols.forEach(function (c, ci) {
        var rows = c.list.children;
        for (var i = 0; i < rows.length; i++) {
          var idx = ci * rows.length + i;
          var cue = cues[idx] !== undefined ? cues[idx] : (s.t0 + 0.15 + idx * 0.28);
          var t = u + s.t0 - cue;
          rows[i].style.opacity = fmt(ramp(t, 0, 0.2));
          rows[i].style.transform = "translateX(" + fmt((1 - ez("back", ramp(t, 0, 0.4))) * (ci ? 40 : -40), 1) + "px)";
        }
      });
      var k = ez("inOut", ramp(u, 0.1, 0.9));
      r.div.style.transform = "translateX(" + fmt((1 - k) * 120, 1) + "px)";
    }
  };

  /* verdict_pair: the honest catch. Two tones, one scene. */
  ARCH.verdict_pair = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "verdict", root), cards: [] };
      [["pros", p.pros_title || "✓ What works"], ["cons", p.cons_title || "⚠ The catch"]].forEach(function (pair, ci) {
        var key = pair[0], title = pair[1];
        var c = el("div", "vd-card vd-" + key, r.wrap);
        el("div", "vd-h", c, title);
        var list = el("div", "vd-list", c);
        (p[key] || []).forEach(function (it) {
          var row = el("div", "vd-row", list);
          el("span", "vd-ic", row, key === "pros" ? "✓" : "⚠");
          el("span", "vd-t", row, it);
        });
        r.cards.push({ node: c, list: list });
      });
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      var idx = 0;
      r.cards.forEach(function (c, ci) {
        var rows = c.list.children;
        /* Both panels are up from the open so the band is never half empty. A row the voice has not
         * reached yet sits dimmed rather than absent — the list reads as pending, not broken. */
        var ct = u + s.t0 - (s.t0 + 0.12 + ci * 0.16);
        c.node.style.opacity = fmt(ramp(ct, -0.05, 0.25));
        c.node.style.transform = "translateY(" + fmt((1 - ez("snappy", ramp(ct, -0.05, 0.5))) * 34, 1) + "px)";
        for (var i = 0; i < rows.length; i++) {
          var cue = cues[idx] !== undefined ? cues[idx] : (s.t0 + 0.15 + idx * 0.3);
          var t = u + s.t0 - cue;
          var on = ramp(t, 0, 0.2);
          rows[i].style.opacity = fmt(0.3 + 0.7 * on);
          rows[i].style.transform = "translateX(" + fmt((1 - ez("back", ramp(t, 0, 0.4))) * 34, 1) + "px)";
          idx++;
        }
      });
    }
  };

  /* app_mock: a fabricated application window — the tool "being used", never captured. */
  ARCH.app_mock = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "app", root) };
      var win = el("div", "app-win", r.wrap);
      var bar = el("div", "app-bar", win);
      ["#ff5f57", "#febc2e", "#28c840"].forEach(function (c) { var d = el("span", "app-dot", bar); d.style.background = c; });
      var tabs = el("div", "app-tabs", bar);
      (p.tabs || []).forEach(function (t, i) {
        var tb = el("span", "app-tab", tabs, t);
        if (i === (p.active_tab || 0)) tb.classList.add("on");
      });
      var body = el("div", "app-body", win);
      if (p.sidebar) {
        var sb = el("div", "app-side", body);
        el("div", "app-side-h", sb, p.sidebar.title || "");
        (p.sidebar.items || []).forEach(function (it, i) {
          var row = el("div", "app-side-i", sb, it);
          if (i === 0) row.classList.add("on");
        });
      }
      var main = el("div", "app-main", body);
      var cards = el("div", "app-cards", main);
      (p.cards || []).forEach(function (c, i) {
        var cc = el("div", "app-card", cards);
        if (c.glyph) el("div", "app-card-g", cc, c.glyph);
        var t = el("div", "app-card-t", cc, c.label || "");
        fitText(t, 200, 11, 24);
        if (c.value) el("div", "app-card-v", cc, c.value);
      });
      if (p.rows && p.rows.length) {
        var rl = el("div", "app-rows", main);
        p.rows.forEach(function (row) {
          var rw = el("div", "app-row", rl);
          el("span", "app-row-k", rw, row[0] || "");
          el("span", "app-row-v", rw, row[1] || "");
        });
      }
      /* The review itself, posted as a comment bubble: it fills the panel's body the way the
       * reference reels fill theirs, instead of leaving a dead rectangle above the input. */
      if (p.comment) {
        var cm = el("div", "app-comment", main);
        var hd = el("div", "app-comment-h", cm);
        el("div", "app-comment-a", hd);
        el("span", "app-comment-who", hd, p.comment.author || "reviewer");
        if (p.comment.tag) el("span", "app-comment-tag", hd, p.comment.tag);
        var txt = el("div", "app-comment-t", cm);
        var sp = el("span", "app-comment-txt", txt);
        sp.textContent = p.comment.text || "";
        r.commentBody = sp;
        r.commentFull = p.comment.text || "";
        r.caret = el("i", "app-comment-caret", txt);
        r.comment = cm;
        main.classList.add("has-comment");
      }
      if (p.input) {
        var inp = el("div", "app-input", main);
        el("span", "app-input-t", inp, p.input);
        el("span", "app-send", inp);
      }
      if (p.badge) {
        var bg = el("div", "app-badge", r.wrap);
        el("span", "app-badge-t", bg, p.badge);
      }
      return r;
    },
    update: function (r, s, u, d) {
      var t = u + s.t0 - (s.cue || s.t0);
      var k = ez("snappy", ramp(t, 0, 0.5));
      r.wrap.style.opacity = fmt(ramp(t, -0.05, 0.1));
      r.wrap.style.transform = "translateY(" + fmt((1 - k) * 40, 2) + "px) scale(" + fmt(0.97 + 0.03 * k, 4) + ")";
      var cards = r.wrap.querySelectorAll(".app-card");
      for (var i = 0; i < cards.length; i++) {
        var ci = s.cues && s.cues[i] !== undefined ? s.cues[i] : (s.t0 + 0.2 + i * 0.2);
        var ct = u + s.t0 - ci;
        cards[i].style.opacity = fmt(ramp(ct, 0, 0.18));
        cards[i].style.transform = "translateY(" + fmt((1 - ez("back", ramp(ct, 0, 0.4))) * 22, 1) + "px)";
      }
      if (r.comment) {
        /* the comment lands after the last card, with a caret that blinks while it "types" */
        var lastCue = (s.cues && s.cues.length) ? s.cues[s.cues.length - 1] : (s.t0 + 0.6);
        var mt = u + s.t0 - (lastCue + 0.25);
        r.comment.style.opacity = fmt(ramp(mt, 0, 0.3));
        r.comment.style.transform = "translateY(" + fmt((1 - ez("snappy", ramp(mt, 0, 0.45))) * 26, 1) + "px)";
        /* the answer is typed out, not pasted in: the text grows with the voice, so the agent's
         * reply is on screen while it is being written */
        if (r.commentBody) r.commentBody.textContent = r.commentFull.slice(0, Math.max(0, Math.floor(mt * 17)));
        if (r.caret) r.caret.style.opacity = (mt > 0 && mt < 2.6 && (Math.floor(mt / 0.42) % 2 === 0)) ? "1" : "0";
      }
    }
  };

  /* steps_path: a numbered path with a rail that fills on the voice. */
  ARCH.steps_path = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "spath", root), rows: [] };
      var rail = el("div", "spath-rail", r.wrap);
      r.railFill = el("div", "spath-rail-f", rail);
      (p.steps || []).forEach(function (st, i) {
        var row = el("div", "spath-row", r.wrap);
        var num = el("div", "spath-n", row, String(i + 1).padStart(2, "0"));
        var body = el("div", "spath-b", row);
        var t = el("div", "spath-t", body, st.title || st);
        fitText(t, 560, 13, 34);
        if (st.note) el("div", "spath-n2", body, st.note);
        r.rows.push({ row: row, num: num, body: body });
      });
      if (p.caption) el("div", "spath-cap", r.wrap, p.caption);
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      var last = s.t0;
      r.rows.forEach(function (x, i) {
        var c = cues[i] !== undefined ? cues[i] : (s.t0 + 0.15 + i * 0.3);
        last = Math.max(last, c);
        var t = u + s.t0 - c;
        var k = ez("back", ramp(t, 0, 0.45));
        x.row.style.opacity = fmt(ramp(t, 0, 0.16));
        x.row.style.transform = "translateX(" + fmt((1 - k) * 46, 1) + "px)";
        x.num.style.background = ramp(t, 0.1, 0.3) > 0.5 ? col("accent") : col("soft");
        x.num.style.color = ramp(t, 0.1, 0.3) > 0.5 ? col("bg") : col("mute");
      });
      r.railFill.style.transform = "scaleY(" + fmt(ez("expo", ramp(u + s.t0 - s.t0, 0, Math.max(0.2, last - s.t0 + 0.4))), 4) + ")";
    }
  };

  /* stamp_card: the rubber-stamp moment. */
  ARCH.stamp_card = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "stampcard", root) };
      var card = el("div", "sc-card", r.wrap);
      if (p.sub) el("div", "sc-sub", card, p.sub);
      var st = el("div", "sc-stamp", card);
      st.style.setProperty("--ps-accent", p.tone || "red");
      el("div", "sc-stamp-t", st, p.stamp || "");
      if (p.note) el("div", "sc-note", card, p.note);
      r.stamp = st;
      return r;
    },
    update: function (r, s, u, d) {
      var t = u + s.t0 - (s.cue || s.t0);
      var k = ez("back", ramp(t, 0, 0.32));
      r.stamp.style.opacity = fmt(ramp(t, 0, 0.08));
      r.stamp.style.transform = "translate(" + fmt((1 - k) * 260, 1) + "px," + fmt((1 - k) * -140, 1) + "px) rotate(" + fmt(-18 + k * 18, 2) + "deg) scale(" + fmt(1.6 - 0.6 * k, 3) + ")";
    }
  };

  /* spec_strip: a row of metric badges. */
  ARCH.spec_strip = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "specs", root), items: [] };
      (p.items || []).forEach(function (it) {
        var b = el("div", "spec", r.wrap);
        var v = el("div", "spec-v", b, it.value || "");
        var l = el("div", "spec-l", b, it.label || "");
        fitText(v, 250, 16, 46);
        fitText(l, 250, 11, 22);
        r.items.push({ node: b, v: v });
      });
      if (p.caption) r.cap = el("div", "spec-cap", r.wrap, p.caption);
      return r;
    },
    update: function (r, s, u, d) {
      var cues = s.cues || [];
      r.items.forEach(function (x, i) {
        var c = cues[i] !== undefined ? cues[i] : (s.t0 + 0.12 + i * 0.22);
        var t = u + s.t0 - c;
        var k = ez("back", ramp(t, 0, 0.8));
        x.node.style.opacity = fmt(ramp(t, 0, 0.15));
        x.node.style.transform = "translateY(" + fmt((1 - k) * 34, 1) + "px) scale(" + fmt(0.9 + 0.1 * k, 3) + ")";
      });
      /* the caption is the last line of the thought: it comes up with the last item, not with the
       * scene, so the strip reads top to bottom */
      if (r.cap) {
        var lastCue = cues.length ? cues[cues.length - 1] : (s.t0 + 0.8);
        var ct = u + s.t0 - (lastCue + 0.3);
        r.cap.style.opacity = fmt(ramp(ct, 0, 0.4));
        r.cap.style.transform = "translateY(" + fmt((1 - ez("snappy", ramp(ct, 0, 0.5))) * 18, 1) + "px)";
      }
    }
  };

  /* quote_block: a pull-quote with attribution. */
  ARCH.quote_block = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "quoteblock", root) };
      var q = el("div", "qb-mark", r.wrap, "“");
      var body = el("div", "qb-body", r.wrap);
      var t = el("div", "qb-text", body, p.quote || "");
      if (p.attrib) el("div", "qb-attrib", body, p.attrib);
      return r;
    },
    update: function (r, s, u, d) {
      var t = u + s.t0 - (s.cue || s.t0);
      var k = ez("expo", ramp(t, 0, 0.7));
      r.wrap.style.opacity = fmt(ramp(t, 0, 0.2));
      r.wrap.style.transform = "translateY(" + fmt((1 - k) * 40, 1) + "px)";
    }
  };

  /* ---------------------------------------------------------------- ambient life */
  /* A house frame is never still. The reference reels keep something moving in EVERY frame: a
   * travelling light over the printed surface, dust in the beam, the texture breathing under the
   * type. A picture that does not move reads as a slide, not as a film — and the measured QA gate
   * (a visible change in >=75% of the spoken time) says the same thing.
   *
   * HOUSE.ambient(t) is a pure function of the frame time, so the render stays reproducible:
   *   - a wide, soft sheen that travels across the frame,
   *   - a dust field that drifts upward with a slow sway,
   *   - the plate texture drifting under everything.
   * Every template calls it from its own setTime().
   */
  var ambientEls = null;
  function ensureAmbient() {
    if (ambientEls) return ambientEls;
    var st = document.getElementById("stage");
    if (!st) return null;
    var sheen = el("div", "house-sheen", st);
    var dust = el("div", "house-dust", st);
    var motes = [];
    for (var i = 0; i < 80; i++) {
      var m = el("i", "house-mote", dust);
      motes.push({
        el: m,
        x: (i * 397) % 1080,
        y: (i * 613) % 2000,
        s: 3 + (i % 6) * 2.3,
        v: 12 + (i % 7) * 7,
        ph: (i % 11) * 0.73
      });
    }
    ambientEls = { sheen: sheen, dust: dust, motes: motes, scenes: [] };
    return ambientEls;
  }
  function ambient(t) {
    var a = ensureAmbient();
    if (!a) return;
    /* The sheen crosses the frame every 9 s. It is a real light: on a dark plate it lifts the
     * blacks, on a paper plate it lays a soft shadow across the print. */
    var period = 9.0, u = (t % period) / period;
    a.sheen.style.transform = "translate3d(" + fmt(-1000 + u * 3100, 1) + "px,0,0) rotate(-13deg)";
    a.sheen.style.opacity = fmt(0.72 + 0.16 * Math.sin(t * 0.43));
    a.motes.forEach(function (m) {
      var y = ((m.y - t * m.v) % 2000 + 2000) % 2000 - 40;
      var x = m.x + Math.sin(t * 0.47 + m.ph) * 46;
      m.el.style.transform = "translate3d(" + fmt(x, 1) + "px," + fmt(y, 1) + "px)";
      m.el.style.opacity = fmt(0.22 + 0.28 * Math.sin(t * 0.9 + m.ph));
    });
    /* A slow camera breath on the SCENE (headline + picture, not the captions): a push-in and a
     * sway, phase-shifted per scene so a cut does not restart the drift. The reference reels ride a
     * slow zoom on every still subject — a frame that holds perfectly still reads as a slide. */
    if (!a.scenes.length) a.scenes = Array.prototype.slice.call(document.querySelectorAll(".scene"));
    var bx = Math.sin(t * 0.31) * 25 + Math.sin(t * 0.83 + 1.7) * 10;
    var by = Math.cos(t * 0.47) * 30 + Math.sin(t * 0.71 + 0.5) * 13;
    var bs = 1 + 0.028 * Math.sin(t * 0.23) + 0.013 * Math.sin(t * 0.61 + 2.1);
    for (var i = 0; i < a.scenes.length; i++) {
      a.scenes[i].style.transform = "translate3d(" + fmt(bx, 2) + "px," + fmt(by, 2) + "px,0) scale(" + fmt(bs, 5) + ")";
    }
  }

  window.HOUSE = {
    ARCH: ARCH,
    PROPS: PROPS,
    PLATES: PLATES,
    setPlate: setPlate,
    plate: function () { return currentPlate; },
    palette: palette,
    col: col,
    richText: richText,
    fitText: fitText,
    hud: hud,
    ambient: ambient,
    el: el,
    svg: svg,
    sEl: sEl,
    sText: sText,
    fmt: fmt,
    comma: comma,
    norm: norm,
    ramp: ramp,
    clamp: clamp,
    ez: ez
  };
})();
