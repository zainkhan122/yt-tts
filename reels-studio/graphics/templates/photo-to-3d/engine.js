/* photo-to-3d template engine — one tool, one visual language (idol).
 *
 * The whole vocabulary is the tool's own product: a fabricated photo chip on a dark viewer canvas that a
 * scan converts, frame by frame, into a violet Gaussian-splat cloud (orbit rings, density dots). No app
 * windows, no browser chrome, no paper plate — those belong to other tools' templates. Everything on
 * screen is FABRICATED; setTime(t) draws pure-function frames; scenes hard-cut.
 *
 * Data: window.DATA = {width, height, handle, template, brand:{...},
 *                      scenes:[{id, archetype, t0, t1, headline, payload, words, cue, cues, ev}]}
 */
(function () {
  "use strict";
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var INK = "#F2F1EA", MUTED = "#8A8FA8", ACC = "#8B7CFF", ACC2 = "#7CD4FC", WARN = "#FFD60A", DARK = "#0C0E17";

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
  /* deterministic pseudo-random so dots never flicker between frames */
  var PRNG = function (seed) {
    var a = seed >>> 0;
    return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  };

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
    out[0] = Math.min(out[0], s.t0 + 0.12);
    for (var j = 1; j < out.length; j++) if (out[j] <= out[j - 1]) out[j] = out[j - 1] + 0.35;
    return out;
  }

  /* ================= the two artifacts: a photo chip & a splat ================= */
  function photoCard(spec) {
    spec = spec || {};
    var ph = el("div", "ph");
    var bar = el("div", "ph-bar", ph);
    el("i", null, bar); el("i", null, bar); el("i", null, bar);
    el("div", "ph-name", bar, spec.name || "photo.jpg");
    var body = el("div", "ph-body", ph);
    var st = el("div", "ph-stage", body);
    el("div", "tag", st, spec.tag || "INPUT · ONE PICTURE");
    var sub = el("div", "ph-subject", st);
    el("div", "core", sub);
    if (spec.handle !== false) el("div", "wing", sub);
    el("div", "glowring", sub);
    el("div", "ph-cap", body, spec.caption || "one picture · flat 2D");
    return ph;
  }

  function splatCard(spec, seed) {
    spec = spec || {};
    var sp = el("div", "sp");
    var bar = el("div", "sp-bar", sp);
    el("i", null, bar); el("i", null, bar); el("i", null, bar);
    el("div", "sp-name", bar, spec.name || "object.ply");
    el("div", "sp-count", sp, spec.count || "1,048,576 GAUSSIANS");
    var rnd = PRNG(seed || 1);
    var box = { x: 60, y: 130, w: 840, h: 760 };
    sp._dots = [];
    var cx = box.x + box.w / 2, cy = box.y + box.h / 2;
    sp._cx = cx; sp._cy = cy;
    sp._r0 = Math.min(box.w, box.h) * 0.46;
    var rings = [];
    [[1.02, "sp-ring"], [1.14, "sp-ring r2"]].forEach(function (pair) {
      var g = el("div", pair[1], sp);
      var rx = sp._r0 * 1.06 * pair[0], ry = sp._r0 * 0.58 * pair[0];
      g.style.left = fmt(cx - rx) + "px"; g.style.top = fmt(cy - ry) + "px";
      g.style.width = fmt(rx * 2) + "px"; g.style.height = fmt(ry * 2) + "px";
      rings.push(g);
    });
    sp._rings = rings;
    var n = spec.dots || 380;
    for (var i = 0; i < n; i++) {
      var ang = rnd() * 6.2832;
      var mag = Math.abs(rnd() + rnd() - 1);                       // dense core, thin rim
      var wing = rnd() < 0.22;
      var bx = wing ? cx + box.w * 0.20 + Math.cos(ang) * mag * box.w * 0.07
                    : cx + Math.cos(ang) * mag * box.w * 0.17;
      var by = cy + Math.sin(ang) * mag * box.h * 0.21;
      var dsz = 3 + rnd() * 4.4;
      var d = el("div", "sp-dot", sp);
      d.style.width = fmt(dsz) + "px"; d.style.height = fmt(dsz) + "px";
      d.style.background = rnd() < 0.72 ? ACC : (rnd() < 0.5 ? ACC2 : "#DDD6FF");
      var side = Math.sign(rnd() - 0.5) || 1;                       // orbit direction per dot
      var phase = rnd() * 6.2832, w = 0.35 + rnd() * 0.55;          // own orbit speed
      var orbitRx = 8 + rnd() * 26, orbitRy = 5 + rnd() * 16;
      d._b = { x: bx, y: by, rx: orbitRx, ry: orbitRy, phase: phase, w: w, side: side };
      sp._dots.push(d);
    }
    el("div", "sp-cap", sp, spec.caption || "standard 3DGS \u00b7 opens anywhere");
    if (spec.badge) el("div", "sp-badge", sp, spec.badge);
    return sp;
  }

  function driftDots(sp, now) {
    for (var i = 0; i < sp._dots.length; i++) {
      var d = sp._dots[i], b = d._b;
      var th = b.phase + now * b.w * b.side;
      d.style.transform = "translate(" + fmt(b.x + Math.cos(th) * b.rx, 1) + "px," + fmt(b.y + Math.sin(th) * b.ry, 1) + "px)";
      d.style.opacity = fmt(0.55 + 0.45 * Math.sin(th * 1.7 + b.phase), 3);
    }
    for (var k = 0; k < sp._rings.length; k++) {
      sp._rings[k].style.transform = "rotate(" + fmt(Math.sin(now * (0.5 + k * 0.22)) * 4, 2) + "deg)";
    }
  }

  /* ============================ archetypes ============================ */
  var ARCH = {};

  /* photo_splat: photos hard-cut, then the scan line converts the last one into the point cloud. */
  ARCH.photo_splat = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { frames: [], idx: -1 };
      var host = el("div", "pst", root);
      (p.photos || [{}]).forEach(function (spec, i) {
        var f = el("div", "frame", host);
        var ph = photoCard(spec);
        ph.style.position = "absolute"; ph.style.inset = "0 0 90px 0";
        f.appendChild(ph);
        r.frames.push(f);
      });
      var sf = el("div", "frame", host);
      var sp = splatCard(p.splat || {}, (p.splat && p.splat.seed) || 9101);
      sp.style.position = "absolute"; sp.style.inset = "0 0 90px 0";
      sf.appendChild(sp);
      r.splat = sp;
      r.frames.push(sf);
      r.scan = el("div", "scan", host);
      r.scan.style.cssText = "position:absolute;left:24px;right:24px;height:5px;background:" + WHITE() + ";opacity:0;border-radius:3px;box-shadow:0 0 26px " + ACC;
      function WHITE() { return "#DDEBFF"; }
      r.stamp = el("div", "stamp", host, p.label || "");
      r.times = bindTimes(p.cue_phrases, s, r.frames.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0, k = 0;
      for (var i = 0; i < r.times.length; i++) if (now >= r.times[i]) k = i;
      if (k !== r.idx) {
        r.idx = k;
        r.frames.forEach(function (f, i) { f.style.display = i === k ? "block" : "none"; });
      }
      var last = k === r.frames.length - 1;
      if (last) {
        var t = ramp(now, r.times[k], r.times[k] + 0.9);
        r.scan.style.opacity = fmt(t < 1 ? 0.9 : 0);
        r.scan.style.top = fmt(40 + eCubic(t) * 880) + "px";
        driftDots(r.splat, now);
      } else {
        r.scan.style.opacity = "0";
      }
      r.stamp.style.opacity = fmt(ramp(u, 0.1, 0.4));
    }
  };

  /* depth_callouts: one photo, and the findings pinned to it — callout cards with leads and dots. */
  ARCH.depth_callouts = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { marks: [] };
      var ph = photoCard(p.photo || {});
      ph.style.position = "absolute"; ph.style.inset = "0 0 90px 0";
      root.appendChild(ph);
      r.photo = ph;
      (p.marks || []).forEach(function (t, i) {
        var m = el("div", "dc-mark", root, t);
        var dot = el("div", "dc-dot", root);
        var lead = el("div", "dc-lead", root);
        // fixed grid over the photo: 0,1 above the subject, 2,3 beside the glowring
        var grid = [[70, 120], [520, 200], [90, 640], [540, 700]];
        var g2 = grid[i % grid.length];
        m.style.left = g2[0] + "px"; m.style.top = g2[1] + "px";
        dot.style.left = (g2[0] + 120) + "px"; dot.style.top = (g2[1] + 96) + "px";
        lead.style.left = (g2[0] + 128) + "px"; lead.style.width = "4px";
        lead.style.top = (g2[1] + 42) + "px"; lead.style.height = "54px";
        r.marks.push({ m: m, dot: dot, lead: lead });
      });
      r.score = el("div", "dc-score", root, p.score || "FULL 3D REBUILT");
      r.times = bindTimes(p.cue_phrases, s, (p.marks || []).length + 1);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.marks.forEach(function (x, i) {
        var t = now - r.times[i], p = eBack(ramp(t, 0, 0.4));
        x.m.style.opacity = fmt(ramp(t, 0, 0.12));
        x.m.style.transform = "translateY(" + fmt((1 - p) * 18) + "px) scale(" + fmt(0.96 + 0.04 * p, 3) + ")";
        x.dot.style.opacity = fmt(ramp(t, 0, 0.1));
        x.lead.style.opacity = fmt(0.85 * ramp(t, 0.05, 0.3));
      });
      var last = r.times[r.marks.length] || (s.t1 - 0.4);
      r.score.style.opacity = fmt(ramp(now, last - 0.1, last + 0.2));
      r.score.style.transform = "translateX(-50%) scale(" + fmt(0.92 + 0.08 * eBack(ramp(now, last - 0.1, last + 0.35)), 3) + ")";
    }
  };

  /* splat_pipeline: the photo breaks into three stage cards; rail fills on the voice. */
  ARCH.splat_pipeline = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { stages: [] };
      var pl = el("div", "pl", root);
      var row = el("div", "pl-stages", pl);
      (p.stages || []).forEach(function (spec, i) {
        var card = el("div", "pl-stage", row);
        el("div", "num", card, "0" + (i + 1));
        el("div", "ttl", card, spec.title || "");
        el("div", "sub", card, spec.sub || "");
        if (spec.kind === "splat") {
          var mini = splatCard({ name: spec.title || "object.ply", dots: 140, count: "" }, 4000 + i);
          mini.style.position = "absolute"; mini.style.inset = "36% 8% 8% 8%";
          card.appendChild(mini);
          r._mini = mini;
        } else {
          var ph = photoCard({ name: spec.file || "input.jpg", handle: spec.kind !== "cut", caption: spec.kicker || "" });
          ph.style.position = "absolute"; ph.style.inset = "36% 8% 8% 8%";
          card.appendChild(ph);
        }
        r.stages.push(card);
      });
      r.rail = el("i", null, el("div", "pl-rail", pl));
      var steps = el("div", "pl-steps", pl);
      r.names = (p.stages || []).map(function (sp) { return el("span", null, steps, String(sp.title || "").toUpperCase()); });
      r.times = bindTimes(p.cue_phrases, s, r.names.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0, k = -1;
      for (var i = 0; i < r.times.length; i++) if (now >= r.times[i]) k = i;
      r.stages.forEach(function (c, i) { c.className = "pl-stage" + (i <= k ? " lit" : ""); });
      r.names.forEach(function (nm, i) { nm.className = i < k ? "on" : (i === k ? "now" : ""); });
      var fill = k < 0 ? 0.04 : (k + 0.4) / r.names.length;
      r.rail.style.width = fmt(clamp(fill, 0.04, 1) * 100, 2) + "%";
      if (r._mini) driftDots(r._mini, now);
    }
  };

  /* gpu_gauge: the VRAM number with a filling bar, then the speed chip underneath. */
  ARCH.gpu_gauge = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      var gg = el("div", "gg", root);
      var card = el("div", "gg-card", gg);
      el("div", "lbl", card, p.gauze || "VRAM PEAK");
      r.num = el("div", "gg-num", card);
      r.num.innerHTML = "<span></span><em></em>";
      r.numMain = r.num.querySelector("span");
      r.numUnit = r.num.querySelector("em");
      r.numUnit.textContent = " GB";
      var bar = el("div", "gg-bar", card);
      r.barFill = el("i", null, bar);
      r.pct = el("div", "gg-pct", card, "");
      r.vram = parseFloat(p.vram) || 7.2;
      r.cap = parseFloat(p.gauge_cap) || 24;
      r.bench = p.bench || "RTX-class card";
      var chips = el("div", "gg-chips", gg);
      r.chips = [];
      (p.chips || []).forEach(function (t, i) {
        var c = el("div", "gg-chip" + (i === 0 ? " live" : ""), chips);
        var b = el("b", null, c, t);
        var small = el("span", "small", c, (p.chip_subs || [])[i] || "");
        r.chips.push(c);
      });
      r.times = bindTimes(p.cue_phrases, s, 2);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var t = ramp(now, r.times[0], r.times[0] + 1.1);
      var val = r.vram * eCubic(t);
      r.numMain.textContent = Number(val).toFixed(1);
      r.barFill.style.width = fmt((val / r.cap) * 100, 2) + "%";
      r.pct.textContent = fmt((val / r.cap) * 100, 0) + "%";
      var t2 = ramp(now, r.times[1], r.times[1] + 0.35);
      r.chips.forEach(function (c, i) {
        c.style.opacity = fmt(ramp(t2 - i * 0.09, 0, 0.2));
        c.style.transform = "translateY(" + fmt((1 - eCubic(ramp(t2 - i * 0.09, 0, 0.3))) * 22) + "px)";
      });
    }
  };

  /* two_doors: two ways in — the free demo card and the SDK card, lit by the voice. */
  ARCH.two_doors = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { doors: [] };
      var td = el("div", "td", root);
      var row = el("div", "td-doors", td);
      (p.doors || []).forEach(function (spec, i) {
        var door = el("div", "td-door", row);
        el("div", "k", door, String(i + 1));
        el("div", "t", door, spec.title || "");
        el("div", "s", door, spec.sub || "");
        var ln = el("div", "line", door);
        r.doors.push({ door: door, line: ln, text: spec.line || "", caret: null });
      });
      r.times = bindTimes(p.cue_phrases, s, r.doors.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.doors.forEach(function (x, i) {
        var t = now - r.times[i];
        x.door.className = "td-door" + (t >= 0 ? " lit" : "");
        x.door.style.opacity = fmt(t < 0 ? 0.35 : 0.55 + 0.45 * ramp(t, 0, 0.3));
        var cps = 46;
        var n = Math.floor(clamp(t * cps, 0, x.text.length));
        x.line.innerHTML = "";
        var sp = document.createElement("span");
        sp.textContent = x.text.slice(0, n);
        x.line.appendChild(sp);
        var c = el("span", "caret", null, "\u258D");
        if (t >= 0 && n < x.text.length && Math.floor(now * 2.2) % 2 === 0) x.line.appendChild(c);
      });
    }
  };

  /* leaderboard: idol's row wins, the others sit beneath — bars grow on the voice. */
  ARCH.leaderboard = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { rows: [] };
      var lb = el("div", "lb", root);
      if (p.badge) r.badge = el("div", "lb-badge", lb, p.badge);
      var rr = el("div", "lb-rows", lb);
      (p.rows || []).forEach(function (spec, i) {
        var row = el("div", "lb-row" + (spec.win ? " win" : ""), rr);
        el("div", "nm", row, spec.name || "");
        var bw = el("div", "barwrap", row);
        var bar = el("i", null, bw);
        el("div", "val", row, spec.val || "");
        r.rows.push({ row: row, bar: bar, score: spec.score || 0.5 });
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (r.badge) r.badge.style.opacity = fmt(ramp(u, 0, 0.25));
      r.rows.forEach(function (x, i) {
        var t = now - r.times[i];
        var p = eCubic(ramp(t, 0, 0.5));
        x.row.style.opacity = fmt(ramp(t, 0, 0.18));
        x.row.style.transform = "translateX(" + fmt((1 - eCubic(ramp(t, 0, 0.35))) * 40) + "px)";
        x.bar.style.width = fmt(x.score * p * 100, 2) + "%";
      });
    }
  };

  /* expect_rows: the limits as flat, honest cards. */
  ARCH.expect_rows = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { rows: [] };
      var ex = el("div", "ex", root);
      (p.rows || []).forEach(function (spec) {
        var row = el("div", "ex-row" + (spec.kind === "ok" ? " ok" : ""), ex);
        el("div", "ico", row, spec.kind === "ok" ? "\u2713" : "!");
        el("div", "t", row, spec.t || "");
        el("div", "s", row, spec.s || "");
        r.rows.push(row);
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.rows.forEach(function (row, i) {
        var t = now - r.times[i];
        var p = eBack(ramp(t, 0, 0.35));
        row.style.opacity = fmt(ramp(t, 0, 0.16));
        row.style.transform = "translateY(" + fmt((1 - p) * 26) + "px)";
      });
    }
  };

  /* endcard: brand logo, keyword, Follow pressed on the pipeline's press time. */
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
      if (p.keyword_chip !== false && p.keyword) {
        r.kw = el("div", "ec-kw", r.card);
        el("span", "ec-kw-t", r.kw, String(p.keyword).toUpperCase());
      }
      r.btn = el("div", "ec-btn", r.card);
      r.lbl = el("span", "ec-lbl", r.btn, p.follow || b.cta_button || "Follow");
      r.done = el("div", "ec-done", r.btn);
      el("span", "ec-done-t", r.done, "Following");
      r.ring = el("div", "ec-ring", r.btn);
      r.cur = document.createElementNS(NS, "svg");
      r.cur.setAttribute("viewBox", "0 0 24 24");
      r.cur.setAttribute("class", "ec-cursor");
      r.btn.appendChild(r.cur);
      var path = document.createElementNS(NS, "path");
      path.setAttribute("d", "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z");
      path.setAttribute("fill", "#FFFFFF"); path.setAttribute("stroke", DARK); path.setAttribute("stroke-width", "1.2");
      r.cur.appendChild(path);
      return r;
    },
    update: function (r, s, u, d) {
      var ev = s.ev || {};
      var pr = (typeof ev.press === "number" ? ev.press : s.t0 + Math.max(1.1, Math.min(d * 0.6, d - 1.0))) - s.t0;
      var kw = (typeof ev.keyword === "number" ? ev.keyword : s.cue) - s.t0;
      var cin = eBack(ramp(u, 0, 0.5));
      r.card.style.opacity = fmt(ramp(u, 0, 0.2));
      /* keep the CSS centering translate(-50%,-50%) — wiping it slides the card half off-canvas right */
      r.card.style.transform = "translate(-50%,-50%) translateY(" + fmt((1 - cin) * 80) + "px) scale(" + fmt(0.96 + 0.04 * cin, 3) + ")";
      if (r.kw) {
        var kp = eBack(ramp(u, kw, kw + 0.4));
        r.kw.style.opacity = fmt(ramp(u, kw, kw + 0.16));
        r.kw.style.transform = "translateY(" + fmt((1 - kp) * 30) + "px) scale(" + fmt(0.9 + 0.1 * kp, 3) + ")";
      }
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
      el("span", isAcc ? "accent" : null, line, w + (i < words.length - 1 ? " " : ""));
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
    var start = Math.max(0, Math.min(cur, words.length - 3));
    var end = Math.min(words.length, start + 3);
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
    if (s._head) {
      var hp = eCubic(ramp(u, 0, 0.26));
      s._head.style.opacity = "1";
      s._head.style.transform = "translateY(" + fmt((1 - hp) * 26) + "px)";
    }
    if (s._rule) {
      var rp = eCubic(ramp(u, 0, 0.42));
      s._rule.style.transformOrigin = "0 50%";
      s._rule.style.transform = "scaleX(" + fmt(rp, 3) + ")";
    }
    var eb = s._wrap.querySelector(".eyebrow");
    if (eb) eb.style.opacity = fmt(ramp(u, 0, 0.3));
    var cam = (s.payload && s.payload.cam) || [1.0, 1.0];
    var cp = eCubic(ramp(u, 0, d));
    var drift = (s.payload && typeof s.payload.drift === "number") ? s.payload.drift : 14;
    var dx = (cp - 0.35) * drift;
    s._art.style.transform = "translate(" + fmt(dx, 2) + "px, 0px) scale(" +
      fmt(cam[0] + (cam[1] - cam[0]) * cp, 4) + ")";
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
    stageEl.style.backgroundPosition = fmt(t * 5, 2) + "px 0px";
  };

  build();
})();
