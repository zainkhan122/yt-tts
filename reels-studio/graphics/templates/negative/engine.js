/* negative: a black void, a hairline instrument, and constant motion.
 *
 * Pure function of setTime(t) — no timers, no CSS transitions, no Math.random.
 *
 * Built after the owner's verdict on v1 (2026-11-13): "will a user even watch 3 sec?" The answer
 * was no. v1 was six static slides with a fade; frames at 0.8s and 3.2s were pixel-identical.
 * A reference style is a LAYOUT system, and layout is not motion. This version adds a motion
 * grammar that runs on EVERY frame of EVERY beat:
 *
 *   1. camera   — the whole beat scales/parallaxes every frame (never static, never more than 4%)
 *   2. ambient  — a hairline grid drifts behind the content at all times; it never stops
 *   3. trace    — instruments travel: the phase scrolls, the needle sweeps, counters never freeze
 *   4. stagger  — type lands word by word on the beat of speech, never as a block
 *   5. impact   — the hook punches in oversized and settles; the first frame is already full
 *
 * The brand layer is the house one and is not negotiable: Anton for headlines, Inter for body,
 * JetBrains Mono for telemetry (all three now actually load — see graphics/render.py).
 */
(function () {
  "use strict";
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var INK = "#FFFFFF", LIVE = "#F05080", GHOST = "#8A8A93", TRACE = "#E8E8EC", HAIR = "#22222A";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var eOut = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var eExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var eBack = function (x) { x = clamp(x, 0, 1); var c1 = 2.2, c3 = c1 + 1;
                             return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 3 : n); };
  var norm = function (w) { return String(w).toLowerCase().replace(/[^a-z0-9]/g, ""); };
  var lerp = function (a, b, k) { return a + (b - a) * k; };

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
    s.style.position = "absolute";
    if (parent) parent.appendChild(s);
    return s;
  };
  var sEl = function (tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };

  /* the scene's own cue time (from the word timings), scene-relative; fallback when unspoken */
  function cue(u, s, fallback) {
    var c = s.cue;
    if (typeof c !== "number" || !isFinite(c)) return fallback;
    var rel = c - s.t0;
    return rel >= 0 && rel <= (s.t1 - s.t0) + 0.5 ? rel : fallback;
  }

  /* deterministic value noise, seeded per scene — never Math.random */
  function noise(seed, n, smooth) {
    var pts = [], v = 0, h = seed * 9301 + 49297;
    for (var i = 0; i < n; i++) {
      h = (h * 9301 + 49297) % 233280;
      v = v * (smooth || 0.55) + (h / 233280 - 0.5) * 1.15;
      pts.push(clamp(v, -1, 1));
    }
    return pts;
  }

  /* split a string into word spans so it can be staggered instead of dropped in as a block */
  function words(parent, str, cls, hitList) {
  var out = [];
    String(str || "").split(" ").forEach(function (w, i) {
      var hit = (hitList || []).map(norm).indexOf(norm(w.replace(/[^a-zA-Z0-9]/g, ""))) >= 0;
      var n = el("span", (cls || "w") + (hit ? " hit" : ""), parent, w);
      n.style.display = "inline-block";
      n.style.marginRight = "0.26em";
      out.push(n);
    });
    return out;
  }

  /* stagger a group of word nodes in, from a start time, with a per-word step */
  function stagger(nodes, u, start, step, dist, dir) {
    for (var i = 0; i < nodes.length; i++) {
      var k = eOut(ramp(u, start + i * step, start + i * step + 0.34));
      nodes[i].style.opacity = fmt(k);
      var d = (1 - k) * (dist || 40);
      nodes[i].style.transform = dir === "x"
        ? "translateX(" + fmt(-d, 1) + "px)"
        : "translateY(" + fmt(d, 1) + "px)";
    }
  }

  /* ---------------- shared furniture ---------------- */

  /* the ambient layer: a hairline grid that drifts forever. This is the thing that makes every
   * frame of the short different from the frame before it, even when the content holds. */
  function ambient(parent) {
    var g = svg(1080, 1920, parent, "ng-grid");
    var v = [], h = [];
    for (var i = -1; i <= 7; i++) v.push(sEl("line", { x1: 0, y1: 0, x2: 0, y2: 1920,
                                                      stroke: HAIR, "stroke-width": 1 }, g));
    for (var j = -1; j <= 13; j++) h.push(sEl("line", { x1: 0, y1: 0, x2: 1080, y2: 0,
                                                        stroke: HAIR, "stroke-width": 1 }, g));
    return { g: g, v: v, h: h };
  }

  function ambientTick(a, t) {
    var sp = 120, ox = (t * 14) % sp, oy = (t * 26) % sp;
    for (var i = 0; i < a.v.length; i++) {
      var x = -sp + i * sp + ox;
      a.v[i].setAttribute("x1", fmt(x, 1)); a.v[i].setAttribute("x2", fmt(x, 1));
      // the grid brightens toward the top so the void has depth without a gradient band
      a.v[i].setAttribute("opacity", fmt(0.10 + 0.5 * Math.max(0, 1 - Math.abs(x - 540) / 900), 3));
    }
    for (var j = 0; j < a.h.length; j++) {
      var y = -sp + j * sp + oy;
      a.h[j].setAttribute("y1", fmt(y, 1)); a.h[j].setAttribute("y2", fmt(y, 1));
      a.h[j].setAttribute("opacity", fmt(0.07 + 0.45 * Math.max(0, 1 - Math.abs(y - 700) / 1400), 3));
    }
  }

  /* the camera: one continuous move across the beat. Small enough to feel expensive. */
  function camera(wrap, u, d, cfg) {
    var k = clamp(u / Math.max(0.001, d), 0, 1);
    var s = (cfg.from === undefined ? 1.035 : cfg.from) + (cfg.to - (cfg.from === undefined ? 1.035 : cfg.from)) * eOut(k);
    var pan = (cfg.pan || 0) * (k - 0.5);
    wrap.style.transform = "scale(" + fmt(s, 4) + ") translate(" + fmt(pan, 2) + "px," +
                           fmt((cfg.rise || 0) * (k - 0.5), 2) + "px)";
  }

  /* the hairline instrument: grid + baseline + a travelling trace. The trace SCROLLS, so no two
   * frames are the same even when the beat is holding. */
  function field(parent, s, opts) {
    opts = opts || {};
    var w = 984, h = opts.height || 400, mid = h / 2;
    var box = el("div", "ng-field", parent);
    box.style.top = (opts.top || 760) + "px";
    box.style.height = h + "px";

    var g = svg(w, h, box);
    var grid = [];
    for (var i = 0; i <= 12; i++) {
      grid.push(sEl("line", { x1: (i / 12) * w, y1: 0, x2: (i / 12) * w, y2: h,
                              stroke: HAIR, "stroke-width": 1, opacity: 0.5 }, g));
    }
    sEl("line", { x1: 0, y1: mid, x2: w, y2: mid, stroke: "#33333C", "stroke-width": 1 }, g);

    var path = sEl("path", { fill: "none", stroke: TRACE, "stroke-width": 3.4,
                             "stroke-linejoin": "round", "stroke-linecap": "round" }, g);
    var live = el("div", "live", box);
    if (opts.labelBelow) live.style.top = (h + 18) + "px";
    var lab = el("span", null, live, (opts.label || "READING") + "  ");
    lab.style.color = GHOST;
    var val = el("b", null, live, "");
    var of = el("span", null, live, opts.total ? "  /  " + opts.total : "");
    of.style.color = GHOST;

    var tick = sEl("line", { x1: 0, y1: 0, x2: 0, y2: h, stroke: LIVE,
                             "stroke-width": 1.6, opacity: 0.9 }, g);
    var dot = sEl("circle", { r: 5, fill: LIVE }, g);
    var cap = el("div", "ng-note", box, opts.annotation || "");
    cap.style.top = (h + 66) + "px";

    var pts = noise(s.idx + 3, 220, 0.5);
    return { box: box, g: g, grid: grid, path: path, pts: pts, w: w, mid: mid, h: h,
             live: live, val: val, tick: tick, dot: dot, cap: cap, labelEl: lab };
  }

  /* redraw the trace at a scrolled phase so it never freezes mid-beat */
  function fieldTick(f, u, d, drawK) {
    var pts = f.pts, n = pts.length, span = 58;         // visible samples
    var off = Math.floor(u * 26) % (n - span - 1);      // scroll speed in samples/frame
    var drawn = Math.round(span * clamp(drawK, 0, 1));
    var dd = "";
    for (var i = 0; i <= drawn; i++) {
      var x = (i / span) * f.w * 0.96;
      var y = f.mid - pts[off + i] * (f.h * 0.40);
      dd += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
    }
    f.path.setAttribute("d", dd);
    var lx = (drawn / span) * f.w * 0.96;
    f.tick.setAttribute("x1", fmt(lx, 1)); f.tick.setAttribute("x2", fmt(lx, 1));
    f.dot.setAttribute("cx", fmt(lx, 1));
    f.dot.setAttribute("cy", fmt(f.mid - pts[off + drawn] * (f.h * 0.40), 1));
  }

  var ARCH = {

    /* ================= HOOK: oversized type punched in, settling, never still ================= */
    impact_hook: {
      build: function (parent, s) {
        var p = s.payload || {};
        var amb = ambient(parent);
        var kick = el("div", "ng-tkick", parent, p.kicker || "");
        kick.style.top = "240px";
        var big = el("div", "ng-impact", parent);
        big.style.top = "336px";
        var ws = words(big, p.title || s.headline || "", "w", p.accent_words);
        var bar = el("div", "ng-slab", parent);
        bar.style.top = "660px";
        var foot = el("div", "ng-telemetry", parent, p.foot || "");
        foot.style.top = "730px";
        // a live micro-instrument under the hook: the void is never empty, even at 0.2s
        var f = field(parent, s, { top: 840, height: 200, labelBelow: true, label: p.label || "STREAM",
                                   annotation: "" });
        f.cap.style.display = "none";
        return { amb: amb, kick: kick, big: big, ws: ws, bar: bar, foot: foot, f: f };
      },
      update: function (r, s, u, d) {
        ambientTick(r.amb, s.t0 + u);
        camera(r.big, u, d, { from: 1.10, to: 1.0, rise: -30 });
        r.kick.style.opacity = "1";
        r.kick.style.letterSpacing = fmt(0.42 - 0.16 * eOut(ramp(u, 0, 0.7)), 3) + "em";
        // words slam in one at a time, the first frame already carries the claim
        stagger(r.ws, u, -0.26, 0.085, 90);
        var bk = eExpo(ramp(u, 0.34, 0.92));
        r.bar.style.width = fmt(bk * 760, 1) + "px";
        r.bar.style.opacity = fmt(ramp(u, 0.3, 0.45));
        r.foot.style.opacity = fmt(ramp(u, 0.5, 0.85));
        r.f.live.style.opacity = fmt(ramp(u, 0.55, 0.9) * 0.9);
        fieldTick(r.f, u, d, eOut(ramp(u, 0.4, 1.3)));
        r.f.val.textContent = fmt(0.6 + u * 1.7, 1) + "s";
        r.f.val.style.color = LIVE;
        // the label glitches to a new reading every ~0.45s: motion even where nothing is "content"
        var labels = ["STREAM", "PARSED", "TRIMMED", "QUEUED"];
        var li = Math.floor((s.t0 + u) / 0.45) % labels.length;
        r.f.labelEl.textContent = labels[li] + "  ";
        r.f.labelEl.style.color = GHOST;
      }
    },

    /* ================= the reference's own grammar, now with a scrolling trace ================= */
    trace_field: {
      build: function (parent, s) {
        var p = s.payload || {};
        var amb = ambient(parent);
        var f = field(parent, s, { top: p.top || 600, label: p.label || "LISTENING",
                                   total: p.total, annotation: p.annotation });
        var head = el("div", "ng-headword", parent);
        head.style.top = "330px";
        var hw = words(head, s.headline || "", "w", p.accent_words);
        return { amb: amb, f: f, head: head, hw: hw,
          at: window.HouseMotion.cueTimes(p.cue_phrases, s, 1, {})[0] - s.t0 };
      },
      update: function (r, s, u, d) {
        var p = s.payload || {};
        ambientTick(r.amb, s.t0 + u);
        camera(r.f.box, u, d, { from: 1.04, to: 1.0, rise: 18 });
        stagger(r.hw, u, 0.02, 0.09, 34);
        var draw = eOut(ramp(u, r.at, r.at + 0.85));
        fieldTick(r.f, u, d, draw);
        r.f.live.style.opacity = fmt(ramp(u, 0.08, 0.3));
        var target = p.value !== undefined && p.value !== null ? Number(p.value) : null;
        r.f.val.textContent = target === null ? "" : (Math.abs(target) >= 10 ? String(Math.round(target * draw))
                                                      : fmt(target * draw, 1)) + (p.unit || "");
        r.f.val.style.color = LIVE;
        r.f.cap.style.opacity = fmt(ramp(u, 0.42, 0.75));
        r.f.cap.style.transform = "translateY(" + fmt((1 - eOut(ramp(u, 0.42, 0.75))) * 16, 1) + "px)";
      }
    },

    /* ================= rows that arrive on the count, with a live bar ================= */
    marker_list: {
      build: function (parent, s) {
        var p = s.payload || {};
        var amb = ambient(parent);
        if (p.label) {
          var lb = el("div", "ng-telemetry", parent, p.label);
          lb.style.top = "400px";
        }
        var wrap = el("div", "ng-rows", parent);
        wrap.style.top = "520px";
        var rows = (p.rows || []).map(function (row) {
          var rr = el("div", "ng-row" + (row.on ? " on" : ""), wrap);
          el("u", null, rr);
          el("div", "n", rr, row.n !== undefined ? String(row.n) : "");
          el("div", "t", rr, row.t || "");
          var barw = el("div", "bar", rr);
          var fill = el("i", null, barw);
          if (row.m !== undefined) el("div", "m", rr, String(row.m));
          return { row: rr, fill: fill };
        });
        var note = el("div", "ng-note", parent, p.annotation || "");
        note.style.top = "930px";
        return { amb: amb, rows: rows, note: note,
          times: window.HouseMotion.cueTimes(p.cue_phrases, s, rows.length, {}) };
      },
      update: function (r, s, u, d) {
        ambientTick(r.amb, s.t0 + u);
        for (var i = 0; i < r.rows.length; i++) {
          var at = r.times[i] - s.t0;
          var k = eOut(ramp(u, at, at + 0.36));
          r.rows[i].row.style.opacity = fmt(k);
          r.rows[i].row.style.transform = "translateX(" + fmt((1 - k) * -46, 1) + "px)";
          // All rows receive the same underline: these are categories, not quantified bars.
          var bf = eExpo(ramp(u, at, at + 0.55));
          r.rows[i].fill.style.width = fmt(bf * 100, 1) + "%";
        }
        r.note.style.opacity = fmt(ramp(u, 0.7, 1.05));
        r.note.style.transform = "translateY(" + fmt((1 - eOut(ramp(u, 0.7, 1.05))) * 14, 1) + "px)";
      }
    },

    /* ================= plates that flip in and a live tick that keeps counting ================= */
    phantom_frame: {
      build: function (parent, s) {
        var p = s.payload || {};
        var amb = ambient(parent);
        var fr = el("div", "ng-frame", parent);
        var bar = el("div", "bar", fr);
        el("s", null, bar); el("s", null, bar); el("s", null, bar);
        el("span", null, bar, p.label || "LOCAL RUN");
        var plates = el("div", "ng-plates", fr);
        var rows = (p.plates || []).map(function (pl) {
          var row = el("div", "ng-plate" + (pl.on ? " on" : ""), plates);
          el("div", "k", row, pl.k || "");
          var v = words(el("div", "v", row), pl.v || "", "w", pl.on ? p.accent_words : []);
          return { row: row, v: v };
        });
        var note = el("div", "ng-note", parent, p.annotation || "");
        note.style.top = "1080px"; note.style.textAlign = "center";
        return { amb: amb, fr: fr, rows: rows, note: note, bar: bar,
          times: window.HouseMotion.cueTimes(p.cue_phrases, s, rows.length, {}) };
      },
      update: function (r, s, u, d) {
        ambientTick(r.amb, s.t0 + u);
        camera(r.fr, u, d, { from: 1.06, to: 1.0, rise: -22 });
        r.fr.style.opacity = fmt(eOut(ramp(u, 0.02, 0.3)));
        for (var i = 0; i < r.rows.length; i++) {
          var at = r.times[i] - s.t0;
          var k = eBack(ramp(u, at, at + 0.41));
          r.rows[i].row.style.opacity = fmt(clamp(k, 0, 1));
          r.rows[i].row.style.transform = "rotateX(" + fmt((1 - clamp(k, 0, 1)) * -70, 1) + "deg)";
          stagger(r.rows[i].v, u, at + 0.1, 0.05, 18);
        }
        // the window chrome line keeps sweeping: constant motion on the frame itself
        r.bar.style.backgroundPosition = fmt(-(s.t0 + u) * 260, 1) + "px 0";
        r.note.style.opacity = fmt(ramp(u, 0.8, 1.15));
      }
    },

    /* ================= a statement, its words landing on the beat ================= */
    readout: {
      build: function (parent, s) {
        var p = s.payload || {};
        var amb = ambient(parent);
        var lb = el("div", "ng-telemetry", parent, p.label || "");
        lb.style.top = "560px";
        var st = el("div", "ng-stmt", parent);
        st.style.top = "680px";
        var stw = words(st, p.statement || "", "w", p.accent_words);
        var note = el("div", "ng-note", parent, p.annotation || "");
        note.style.top = "1010px"; note.style.textAlign = "center";
        var rule = el("div", "ng-rule", parent);
        rule.style.top = "1090px"; rule.style.width = "0px";
        return { amb: amb, lb: lb, st: st, stw: stw, note: note, rule: rule,
          at: window.HouseMotion.cueTimes(p.cue_phrases, s, 1, {})[0] - s.t0 };
      },
      update: function (r, s, u, d) {
        ambientTick(r.amb, s.t0 + u);
        camera(r.st, u, d, { from: 1.0, to: 1.04, rise: -18 });
        r.lb.style.opacity = fmt(ramp(u, 0.02, 0.26));
        stagger(r.stw, u, 0.10, 0.13, 52);
        var c = r.at;
        // the accent word turns on its spoken cue, which is the only colour event in the beat
        for (var i = 0; i < r.stw.length; i++) {
          if (r.stw[i].classList.contains("hit")) {
            var on = u >= c;
            r.stw[i].style.color = on ? LIVE : INK;
            if (on) r.stw[i].style.transform = "translateY(" + fmt(-6 * eBack(ramp(u, c, c + 0.3)), 1) + "px)";
          }
        }
        r.note.style.opacity = fmt(ramp(u, c + 0.35, c + 0.75));
        r.rule.style.width = fmt(eExpo(ramp(u, c, c + 0.7)) * 520, 1) + "px";
        r.rule.style.marginLeft = fmt((1080 - eExpo(ramp(u, c, c + 0.7)) * 520) / 2, 1) + "px";
      }
    },

    /* ================= outro: the house endcard, brand layer untouched ================= */
    endcard: {
      build: function (parent, s) {
        // drawn by the house outro layer (templates/shared.js + graphics/outro.js); the engine
        // returns inert refs so setTime stays a pure function and nothing throws
        return { house: true };
        var p = s.payload || {};
        var amb = ambient(parent);
        var br = window.DATA.brand || {};
        var brandEl = el("img", "ng-brand", parent);
        brandEl.src = br.logo || "";                 // the real brand logo, never a text initial
        var handle = el("div", "ng-handle2", parent, br.handle || D.handle || "");
        handle.style.top = "900px";
        var kw = el("div", "ng-kw", parent);
        var kww = words(kw, p.keyword || "", "w", [p.keyword]);
        var prompt = el("div", "ng-telemetry", parent, p.prompt || "FOR THE REPOS");
        prompt.style.top = "1210px";
        var follow = el("div", "ng-follow", parent, p.follow || "FOLLOW FOR MORE");
        return { amb: amb, brand: brandEl, kw: kw, kww: kww, prompt: prompt, follow: follow,
                 handle: handle };
      },
      update: function (r, s, u, d) {
        if (r.house) return;
        ambientTick(r.amb, s.t0 + u);
        var bk = eBack(ramp(u, 0.02, 0.45));
        r.brand.style.opacity = fmt(ramp(u, 0.02, 0.3));
        r.brand.style.transform = "scale(" + fmt(0.86 + 0.14 * bk, 3) + ")";
        r.handle.style.opacity = fmt(ramp(u, 0.30, 0.55));
        stagger(r.kww, u, 0.18, 0.12, 46);
        var kk = eBack(ramp(u, 0.42, 0.8));
        r.kw.style.transform = "scale(" + fmt(0.92 + 0.08 * clamp(kk, 0, 1), 3) + ")";
        r.prompt.style.opacity = fmt(ramp(u, 0.6, 0.9));
        r.follow.style.opacity = fmt(ramp(u, 0.75, 1.05));
        r.follow.style.letterSpacing = fmt(0.34 - 0.06 * ramp(u, 0.75, 1.4), 3) + "em";
      }
    }
  };

  /* ================= stage + kinetic caption ================= */
  var stageEl = document.getElementById("stage");
  var capEl;

  function build() {
    el("div", "ng-handle", stageEl, D.handle || "");
    D.scenes.forEach(function (s, si) {
      s.idx = si;
      var wrap = el("div", "scene", stageEl);
      wrap.setAttribute("data-scene", s.id);
      wrap.style.display = "none";
      var inner = el("div", "visual", wrap);
      s._wrap = wrap; s._visual = inner;
      var spec = ARCH[s.archetype];
      if (!spec) throw new Error("negative: unknown archetype " + s.archetype);
      s._refs = spec.build(inner, s);
    });
    window.ready = true;
  }

  function activeIndex(t) {
    var sc = D.scenes;
    for (var k = 0; k < sc.length; k++) if (t >= sc[k].t0 && t < sc[k].t1) return k;
    return t < 0 ? 0 : sc.length - 1;
  }

  function drawCaption_unused(s, t) {
    // the outro card is its own call to action; a scrolling caption over it is clutter
    capEl.className = "ng-cap" + (s.archetype === "endcard" ? " hide" : "");
    var ws = s.words || [];
    var cur = -1;
    for (var i = 0; i < ws.length; i++) if (t >= ws[i][1]) cur = i;
    var start = Math.max(0, Math.min(cur, ws.length - 4));
    var end = Math.min(ws.length, start + 4);
    var hits = s.hits || [];
    capEl.innerHTML = "";
    for (var j = start; j < end; j++) {
      var cls = "cw" + (j === cur ? " on" : "");
      if (hits.indexOf(norm(ws[j][0])) >= 0) cls += " hit";
      var w = el("span", cls, capEl, ws[j][0]);
      if (j === cur) {
        var k = eOut(ramp(t - ws[j][1], 0, 0.16));
        w.style.transform = "translateY(" + fmt((1 - k) * 10, 1) + "px) scale(" + fmt(1 + 0.04 * k, 3) + ")";
      }
    }
  }

  window.setTime = function (t) {
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    // The shared house card owns the complete endcard scene.
    if (s.archetype === "endcard") { D.scenes.forEach(function (x) { x._wrap.style.display = "none"; }); return; }
    s._visual.style.transformOrigin = "50% 46%";
    ARCH[s.archetype].update(s._refs, s, t - s.t0, Math.max(1e-6, s.t1 - s.t0));
  };

  build();
})();
