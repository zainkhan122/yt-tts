/* velocity-black engine: the github.signals/AhSilence grammar on our pipeline.
 * setTime(t) is a pure function of t: no timers, no CSS transitions.
 * Stage is pure #000. One accent: #FE297D. Diagrams are thin white/pink SVG strokes.
 * Captions: bottom band, sentence case, accent words pink.
 * DATA: window.DATA = {width, height, handle, brand?, scenes:[{id, archetype, t0, t1, headline,
 *        payload, words, cue, cues, ev?}]}
 */
(function () {
  "use strict";
  var GRAIN_EL = null;
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var PINK = "#FE297D", WHITE = "#FFFFFF", MUTE = "#8B93A3", CARD = "#0D1117", EDGE = "#30363D",
      TRACK = "#1C2230", GREEN = "#4ADE80";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var easeOutCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var easeOutExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var easeOutBack = function (x) { x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  /* Pro easing (GSAP 3, vendored at graphics/templates/vendor/gsap.min.js). The engine stays a pure
   * function of t: we only borrow GSAP's easing curves, never its ticker. */
  var easeOutSpring = easeOutBack, easeOutSnappy = easeOutBack, easeInOutQuart = easeOutExpo, easeOutQuint = easeOutExpo;
  if (window.gsap && window.gsap.parseEase) {
    var pe = window.gsap.parseEase;
    easeOutSpring = pe("elastic.out(1, 0.55)");
    easeOutSnappy = pe("back.out(2.4)");
    easeInOutQuart = pe("power4.inOut");
    easeOutQuint = pe("power4.out");
  }
  window.EASE = { spring: easeOutSpring, snappy: easeOutSnappy, inOut: easeInOutQuart, quint: easeOutQuint,
                  cubic: easeOutCubic, expo: easeOutExpo, back: easeOutBack };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 2 : n); };
  var comma = function (n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ","); };
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
    var t = sEl("text", attrs || { fill: WHITE }, parent);
    t.setAttribute("x", x); t.setAttribute("y", y);
    t.textContent = str;
    return t;
  };

  var accents = function (s) {
    var a = (s.payload && s.payload.accent_words) || [];
    var m = {};
    a.forEach(function (w) { m[norm(w)] = true; });
    return m;
  };

  /* ================= archetypes ================= */
  var ARCH = {};

  /* hero_hook: the subject made physical (reference: the running generator). Hero image on black,
   * slow push-in, white hum sine growing beneath; flat=true turns the wave into a straight line
   * (the bookend payoff). */
  ARCH.hero_hook = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = { wrap: el("div", "fanwrap", root) };
      r.chaos = p.mode === "chaos";
      var hw = el("div", r.chaos ? "hero-wrap hero-tall" : "hero-wrap", r.wrap);
      r.img = el("img", "heroimg" + (r.chaos ? " heroimg-full" : ""), hw);
      r.img.src = D.vendor_url + "/" + p.hero;
      var g = svg(980, r.chaos ? 560 : 300, r.wrap);
      g.style.position = "absolute"; g.style.left = "0";
      if (r.chaos) { g.style.top = "240px"; g.style.pointerEvents = "none"; }
      else g.style.bottom = "-10px";
      r.g = g;
      if (s.sub) r.chip = el("div", "hero-chip tag", hw, s.sub);
      if (r.chaos) {
        r.noiseA = sEl("path", { fill: "none", stroke: WHITE, "stroke-width": 2.6, opacity: 0.9 }, g);
        r.noiseB = sEl("path", { fill: "none", stroke: PINK, "stroke-width": 2.2, opacity: 0 }, g);
        r.axis = sEl("line", { x1: 0, y1: 280, x2: 980, y2: 280, stroke: TRACK, "stroke-width": 2, opacity: 0.5 }, g);
      } else {
        r.w = stageWave(g, 980, 300, 90, 150);
        r.flatLine = sEl("line", { x1: 0, y1: 150, x2: 980, y2: 150, stroke: "#DADADA", "stroke-width": 2, opacity: 0 }, g);
        r.tagP = sText(100, 0, "PUSH", { fill: MUTE, "font-size": 22, "font-family": "monospace" }, g);
        r.tagL = sText(830, 0, "PULL", { fill: MUTE, "font-size": 22, "font-family": "monospace" }, g);
      }
      return r;
    },
    update: function (r, s, u, d) {
      var push = 1 + 0.05 * easeOutCubic(ramp(u, 0, d));
      if (r.chip) r.chip.style.opacity = fmt(Math.min(1, u * 2.5), 3);
      if (!r.chaos) {
        var breathe = 1 + 0.012 * Math.sin(u * 2.3);
        r.img.style.transform = "scale(" + fmt(push * breathe, 4) + ")";
        var grow = easeOutCubic(ramp(u, 0.2, 1.2));
        var flat0 = s.payload.flat ? ramp(u, d * 0.5, d * 0.85) : 0;
        var amp = 90 * grow * (1 - flat0);
        r.w.path.setAttribute("d", wavePath(980, 150, amp, 4.2, u * 2.4));
        r.flatLine.setAttribute("opacity", fmt(flat0 * 0.85));
        var t0 = s.cue ? (s.cue - s.t0) : d * 0.5;
        var shown = u > t0 - 0.4 && u < d - 0.3 && flat0 < 0.5;
        r.tagP.setAttribute("opacity", shown ? 0.9 : 0); r.tagP.setAttribute("y", 150 - amp - 12);
        r.tagL.setAttribute("opacity", shown ? 0.9 : 0); r.tagL.setAttribute("y", 150 + amp + 26);
        return;
      }
      /* chaos mode: the platform's noise roars past the listener; pink counter-noise arrives on cue */
      r.img.style.transform = "scale(" + fmt(push, 4) + ")";
      var flat = s.payload.flat ? easeOutCubic(ramp(u, d * 0.45, d * 0.8)) : 0;
      var t = s.cue ? (s.cue - s.t0) : d * 0.35;
      var pinkIn = easeOutExpo(ramp(u, t, t + 0.9));
      var ampA = 130 * (1 - flat), ampB = 120 * pinkIn * (1 - flat);
      var segs = 120, dd = "", i, x, y;
      for (i = 0; i <= segs; i++) {
        x = (980 * i) / segs;
        var h1 = Math.sin(i * 11.31 + u * 9.0) * 0.5 + Math.sin(i * 4.1 - u * 6.3) * 0.5;
        y = 280 + h1 * ampA * 0.9;
        dd += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
      }
      r.noiseA.setAttribute("d", dd);
      dd = "";
      for (i = 0; i <= segs; i++) {
        x = (980 * i) / segs;
        var h2 = Math.sin(i * 13.7 - u * 12.0) * 0.5 + Math.sin(i * 5.3 + u * 7.0) * 0.5;
        y = 280 + h2 * ampB * 0.9;
        dd += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
      }
      r.noiseB.setAttribute("d", dd);
      r.noiseB.setAttribute("opacity", fmt(pinkIn * 0.95));
      r.axis.setAttribute("opacity", fmt(0.2 + flat * 0.8));
    }
  };

  /* ---- sine-wave toolkit: the AhSilence grammar lives here ---- */
  var wavePath = function (w, baseY, amp, cycles, phase, dir) {
    var d = "", n = 72;
    for (var i = 0; i <= n; i++) {
      var x = (w * i) / n;
      var y = baseY + (dir || 1) * amp * Math.sin((i / n) * cycles * Math.PI * 2 + phase);
      d += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
    }
    return d;
  };
  var noisePath = function (w, baseY, amp, seed, upto) {
    var d = "", n = 140;
    for (var i = 0; i <= n; i++) {
      var x = (w * i) / n;
      var h = Math.sin(i * 12.9898 + seed * 78.233) * 43758.5453;
      h = h - Math.floor(h);
      var y = baseY + (h - 0.5) * 2 * amp + Math.sin(i * 0.32) * amp * 0.35;
      d += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
    }
    return d;
  };
  var stageWave = function (g, W, Y, amp, cy, col, wdt) {
    return {
      g: g, W: W, Y: Y, amp: amp, cy: cy || Y / 2, col: col || WHITE, wdt: wdt || 3,
      path: sEl("path", { fill: "none", stroke: col || WHITE, "stroke-width": wdt || 3, "stroke-linecap": "round" }, g)
    };
  };

  /* wave_room: the room hum as a living sine; PUSH/PULL tags mark crest and trough. */
  ARCH.wave_room = {
    build: function (root, s) {
      var r = {};
      var g = svg(980, 620, root);
      r.w = stageWave(g, 980, 620, 150);
      if (s.payload.mode === "label") {
        r.tagP = sText(0, 0, "PUSH", { fill: MUTE, "font-size": 26, "font-family": "monospace", "letter-spacing": 3 }, g);
        r.tagL = sText(0, 0, "PULL", { fill: MUTE, "font-size": 26, "font-family": "monospace", "letter-spacing": 3 }, g);
      }
      r.tag = s.payload.label ? sText(490, 70, s.payload.label, { fill: PINK, "font-size": 34, "font-weight": 800, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g) : null;
      return r;
    },
    update: function (r, s, u, d) {
      var grow = easeOutCubic(ramp(u, 0.1, 1.1));
      var ph = u * 2.1;
      r.w.path.setAttribute("d", wavePath(980, 310, 150 * grow, 4, ph));
      if (r.tagP) {
        var up = (ph % (Math.PI * 2)) < Math.PI;
        r.tagP.setAttribute("opacity", up ? 1 : 0); r.tagP.setAttribute("x", 120); r.tagP.setAttribute("y", 310 - 150 * grow - 16);
        r.tagL.setAttribute("opacity", up ? 0 : 1); r.tagL.setAttribute("x", 840); r.tagL.setAttribute("y", 310 + 150 * grow + 34);
      }
      if (r.tag) {
        var t = s.cue ? (s.cue - s.t0) : 1.2;
        r.tag.setAttribute("opacity", fmt(easeOutBack(ramp(u, t, t + 0.4))));
      }
    }
  };

  /* wave_flip: the inverted copy slides in, locks anti-phase, and the pair flattens to silence. */
  ARCH.wave_flip = {
    build: function (root, s) {
      var r = {};
      var g = svg(980, 620, root);
      r.a = stageWave(g, 980, 620, 145);
      r.b = stageWave(g, 980, 620, 145, undefined, PINK, 3.4);
      r.flat = sEl("line", { x1: 0, y1: 310, x2: 980, y2: 310, stroke: MUTE, "stroke-width": 2, opacity: 0 }, g);
      r.tag = sText(490, 84, s.payload.tag, { fill: PINK, "font-size": 44, "font-weight": 900, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      return r;
    },
    update: function (r, s, u, d) {
      var t = s.cue ? (s.cue - s.t0) : d * 0.35;
      var ga = easeOutCubic(ramp(u, 0.1, 0.9));
      var gb = easeOutExpo(ramp(u, t, t + 1.0));
      var lock = ramp(u, t + 1.05, t + 1.8);      /* merge into silence */
      var amp = 145 * ga * (1 - lock);
      r.a.path.setAttribute("d", wavePath(980, 310, amp, 4, u * 2.1));
      r.b.path.setAttribute("d", wavePath(980, 310, amp * gb, 4, u * 2.1, -1));
      r.flat.setAttribute("opacity", fmt(lock * 0.9));
      r.tag.setAttribute("opacity", fmt(easeOutBack(ramp(u, t + 0.1, t + 0.5))));
      r.tag.setAttribute("transform", "translate(0," + fmt((1 - easeOutCubic(ramp(u, t + 0.1, t + 0.5))) * 20, 1) + ")");
    }
  };

  /* scan_tick: the README's 7-second ambient scan — ticker counts, noise traces, the drone pops. */
  ARCH.scan_tick = {
    build: function (root, s) {
      var p = s.payload;
      var r = {};
      r.tick = el("div", "ticker", root);
      var g = svg(980, 560, root);
      g.style.marginTop = "120px";
      r.noise = sEl("path", { fill: "none", stroke: WHITE, "stroke-width": 2.4, opacity: 0.85 }, g);
      r.bin = sEl("rect", { x: 430, width: 60, fill: PINK, opacity: 0 }, g);
      r.binLabel = sText(460, 196, p.found_label || "STRONGEST DRONE", { fill: PINK, "font-size": 30, "font-weight": 800, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      r.axis = sEl("line", { x1: 0, y1: 290, x2: 980, y2: 290, stroke: TRACK, "stroke-width": 2 }, g);
      if (p.label) r.lab = sText(12, 530, p.label, { fill: MUTE, "font-size": 26, "font-family": "monospace" }, g);
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload;
      var done = ramp(u, 0.2, d * 0.78);
      var secs = p.seconds * done;
      r.tick.innerHTML = "";
      el("span", "", r.tick, "LISTENING ");
      el("b", "", r.tick, secs.toFixed(1) + " s");
      el("span", "", r.tick, " / " + p.seconds.toFixed(1) + " s");
      r.noise.setAttribute("d", noisePath(980 * done, 290, 90, 7.3));
      var pop = easeOutBack(ramp(u, d * 0.78, d * 0.78 + 0.5));
      r.bin.setAttribute("opacity", fmt(pop));
      r.bin.setAttribute("y", 205 + (1 - pop) * 30); r.bin.setAttribute("height", 170 * pop);
      r.binLabel.setAttribute("opacity", fmt(pop));
    }
  };

  /* wave_misalign: the exactness beat — half a cycle late, twice as loud. */
  ARCH.wave_misalign = {
    build: function (root, s) {
      var r = {};
      var g = svg(980, 640, root);
      r.a = stageWave(g, 980, 640, 130, 300);
      r.b = stageWave(g, 980, 640, 130, 300, PINK, 3.2);
      r.sum = stageWave(g, 980, 640, 0, 500, WHITE, 4);
      r.axis = sEl("line", { x1: 0, y1: 500, x2: 980, y2: 500, stroke: TRACK, "stroke-width": 2 }, g);
      r.tagS = sText(490, 70, s.payload.shift_tag, { fill: PINK, "font-size": 46, "font-weight": 900, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      var dblW = s.payload.double_word || "double";
      r.tDbl = null;
      (s.words || []).forEach(function (w) { if (r.tDbl === null && norm(w[0]) === norm(dblW)) r.tDbl = w[1] - s.t0; });
      if (r.tDbl === null) r.tDbl = d * 0.62;
      r.tagD = sText(490, 630, "", { fill: PINK, "font-size": 46, "font-weight": 900, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      r.tagD.textContent = s.payload.double_tag;
      return r;
    },
    update: function (r, s, u, d) {
      var t = s.cue ? (s.cue - s.t0) : d * 0.3;
      var off = 0.5 * easeOutCubic(ramp(u, t, t + 0.6)); /* half phase = misaligned */
      r.a.path.setAttribute("d", wavePath(980, 300, 130, 3.4, u * 2.3));
      r.b.path.setAttribute("d", wavePath(980, 300, 130, 3.4, u * 2.3 + Math.PI * (1 - off), -1));
      var dbl = ramp(u, r.tDbl, r.tDbl + 0.6);
      r.sum.path.setAttribute("d", wavePath(980, 500, 240 * dbl, 3.4, u * 2.3));
      r.tagS.setAttribute("opacity", fmt(easeOutBack(ramp(u, t, t + 0.45))));
      r.tagD.setAttribute("opacity", fmt(easeOutBack(ramp(u, r.tDbl, r.tDbl + 0.45))));
    }
  };

  /* wave_select: the steady hum gets erased in place; the voice glitch survives. */
  ARCH.wave_select = {
    build: function (root, s) {
      var p = s.payload;
      var r = {};
      var g = svg(980, 560, root);
      r.hum = stageWave(g, 980, 560, 110, 230);
      r.anti = stageWave(g, 980, 560, 110, 230, PINK, 2.6);
      r.flat = sEl("line", { x1: 0, y1: 230, x2: 980, y2: 230, stroke: MUTE, "stroke-width": 2.4, opacity: 0 }, g);
      r.voice = sEl("path", { fill: "none", stroke: PINK, "stroke-width": 2.8 }, g);
      r.keep = sText(490, 120, p.keep_label, { fill: PINK, "font-size": 32, "font-weight": 800, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      r.drop = sText(490, 400, p.drop_label, { fill: WHITE, "font-size": 30, "font-weight": 700, "text-anchor": "middle", "font-family": "monospace", opacity: 0 }, g);
      return r;
    },
    update: function (r, s, u, d) {
      var erase = ramp(u, 0.6, d * 0.5);
      r.hum.path.setAttribute("d", wavePath(980, 230, 110 * (1 - erase), 3.6, u * 2.0));
      r.anti.path.setAttribute("d", erase < 1 ? wavePath(980, 230, 110 * (1 - erase), 3.6, u * 2.0, -1) : "M0 0");
      r.flat.setAttribute("opacity", fmt(erase * 0.9));
      var vp = easeOutBack(ramp(u, d * 0.45, d * 0.45 + 0.7));
      var vd = "", n = 90;
      for (var i = 0; i <= n; i++) {
        var x = (980 * i) / n;
        var h = Math.sin(i * 9.7) * 43758.5453; h = h - Math.floor(h);
        var y = 460 + (h - 0.5) * 90 * vp;
        vd += (i ? " L " : "M ") + fmt(x, 1) + " " + fmt(y, 1);
      }
      r.voice.setAttribute("d", vd);
      r.keep.setAttribute("opacity", fmt(ramp(u, d * 0.4, d * 0.4 + 0.4)));
      r.drop.setAttribute("opacity", fmt(vp));
      r.drop.setAttribute("y", 540);
    }
  };

  /* gauge_dial: the app's own 360° Phase Calibrator — needle trims the timing by hand. */
  ARCH.gauge_dial = {
    build: function (root, s) {
      var p = s.payload;
      var r = {};
      var g = svg(980, 620, root);
      var cx = 490, cy = 430, R = 260;
      for (var i = 0; i <= 24; i++) {
        var a = (-220 + i * (260 / 24)) * Math.PI / 180;
        var inner = (i % 4 === 0) ? R - 30 : R - 16;
        sEl("line", { x1: cx + Math.cos(a) * inner, y1: cy + Math.sin(a) * inner,
                      x2: cx + Math.cos(a) * R, y2: cy + Math.sin(a) * R,
                      stroke: i % 4 === 0 ? MUTE : TRACK, "stroke-width": 3 }, g);
      }
      r.mark180 = sText(cx - 190, cy - 46, "180°", { fill: MUTE, "font-size": 30, "font-family": "monospace" }, g);
      r.wave = sEl("path", { fill: "none", stroke: PINK, "stroke-width": 4, "stroke-linecap": "round" }, g);
      r.needle = sEl("line", { x1: cx, y1: cy, x2: cx, y2: cy - R + 52, stroke: PINK, "stroke-width": 7, "stroke-linecap": "round" }, g);
      r.hub = sEl("circle", { cx: cx, cy: cy, r: 22, fill: PINK }, g);
      r.deg = sText(cx, cy + 120, "", { fill: WHITE, "font-size": 88, "font-weight": 900, "text-anchor": "middle" }, g);
      r.lab = sText(cx, 72, p.label, { fill: MUTE, "font-size": 30, "font-family": "monospace", "text-anchor": "middle", "letter-spacing": 6 }, g);
      if (p.note) r.note = sText(cx, cy + 180, p.note, { fill: MUTE, "font-size": 28, "font-family": "monospace", "text-anchor": "middle", opacity: 0 }, g);
      r.cx = cx; r.cy = cy; r.R = R;
      return r;
    },
    update: function (r, s, u, d) {
      var from = s.payload.from_deg, to = s.payload.to_deg;
      var span = 260, startA = -220;
      var deg = from + (to - from) * easeOutCubic(ramp(u, 0.3, d * 0.55)) + Math.sin(u * 1.4) * 1.5;
      var a = (startA + (deg / 360) * span) * Math.PI / 180;
      /* map 180° to 12 o'clock */
      a = (deg - 90) * Math.PI / 180;
      var nx = r.cx + Math.cos(a) * (r.R - 52), ny = r.cy + Math.sin(a) * (r.R - 52);
      r.needle.setAttribute("x2", fmt(nx, 1)); r.needle.setAttribute("y2", fmt(ny, 1));
      r.deg.textContent = Math.round(deg) + "°";
      /* a small phase wave riding on the dial, bending until the needle lands near 180+ */
      var bend = Math.sin(a) * 60;
      r.wave.setAttribute("d", wavePath(360, r.cy - r.R - 60, 26 + bend, 3, u * 1.8));
      r.wave.setAttribute("transform", "translate(" + fmt(r.cx - 180, 1) + ",0)");
      if (r.note) r.note.setAttribute("opacity", fmt(ramp(u, d * 0.6, d * 0.6 + 0.5)));
    }
  };



  /* hook_fan: one handle fans out into a field of site lanes with pink pulse packets. */
  ARCH.hook_fan = {
    build: function (root, s) {
      var r = { wrap: el("div", "fanwrap", root) };
      r.hero = el("div", "fan-hero", r.wrap);
      var W = 980, H = 580, N = 30;
      var g = svg(W, H, r.hero);
      r.anchor = sEl("rect", { x: 18, y: H / 2 - 46, width: 128, height: 92, rx: 18, fill: CARD, stroke: EDGE, "stroke-width": 3 }, g);
      sText(80, H / 2 - 8, "@user", { fill: MUTE, "font-size": 26, "text-anchor": "middle", "font-family": "monospace" }, g);
      sText(80, H / 2 + 24, "you", { fill: WHITE, "font-size": 30, "font-weight": 800, "text-anchor": "middle" }, g);
      r.lines = [];
      for (var i = 0; i < N; i++) {
        var y = 24 + (H - 48) * (i / (N - 1));
        var dPath = "M 146 " + (H / 2) + " C 320 " + (H / 2) + " 340 " + y + " 700 " + y + " L 964 " + y;
        var ln = sEl("path", { d: dPath, fill: "none", stroke: WHITE, "stroke-width": 1.6, opacity: 0.5 }, g);
        r.lines.push({ ln: ln, y: y, len: 1200 });
      }
      r.pulses = r.lines.map(function (L, i) {
        return sEl("circle", { r: 8, fill: PINK, opacity: 0 }, g);
      });
      r.counter = el("div", "fan-counter", r.wrap);
      el("div", "n", r.counter, comma(s.payload.sites));
      el("div", "t tag", r.counter, "SITE CHECKS AT ONCE");
      return r;
    },
    update: function (r, s, u, d) {
      var p = easeOutCubic(ramp(u, 0.1, d * 0.62));
      var n = r.lines.length;
      for (var i = 0; i < n; i++) {
        var L = r.lines[i];
        var li = clamp(p * (n + 4) - i, 0, 1); /* staggered draw-in */
        var drawn = easeOutCubic(li);
        L.ln.setAttribute("stroke-dasharray", fmt(drawn * 1200, 1) + " 2000");
        var pulseT = (u * 0.55 + i * 0.31) % 1.0;
        var pu = r.pulses[i];
        if (drawn >= 1) {
          var x = 146 + pulseT * 818, y = L.y;
          if (pulseT < 0.42) { /* project along the curve: first half eases y from center */
            var k = pulseT / 0.42;
            y = (580 / 2) + (L.y - 580 / 2) * easeOutCubic(k);
          }
          pu.setAttribute("cx", fmt(x, 1)); pu.setAttribute("cy", fmt(y, 1));
          pu.setAttribute("opacity", fmt(0.95 * Math.sin(pulseT * Math.PI), 3));
        } else pu.setAttribute("opacity", 0);
      }
      var cp = easeOutBack(ramp(u, d * 0.62, d * 0.62 + 0.45));
      r.counter.style.opacity = fmt(cp);
      r.counter.style.transform = "scale(" + fmt(0.9 + 0.1 * cp, 3) + ")";
    }
  };

  /* lane_counts: three answered-lanes with sweeping tracers; the count pops as its word lands. */
  ARCH.lane_counts = {
    build: function (root, s) {
      var r = { wrap: el("div", "lanes", root), lanes: [] };
      var lanes = s.payload.lanes;
      var max = 0;
      lanes.forEach(function (l) { max = Math.max(max, l.count); });
      lanes.forEach(function (l, i) {
        var row = el("div", "lane", r.wrap);
        row.style.top = (60 + i * 300) + "px";
        el("div", "lab", row, l.label);
        var cnt = el("div", "cnt", row, comma(l.count));
        var track = el("div", "track", row);
        var bar = el("div", "bar", row);
        var tr = el("div", "tracer", row);
        r.lanes.push({ row: row, cnt: cnt, bar: bar, tr: tr, frac: l.count / max });
      });
      /* word-cue per lane: the lane's cue word (spoken) gates its reveal; fallback: even stagger */
      r.reveal = r.lanes.map(function (L, i) {
        var lane = lanes[i], tHit = null;
        var cw = norm(lane.cue || lane.label.split(" ")[0] || "");
        (s.words || []).forEach(function (w) {
          if (tHit === null && norm(w[0]) === cw && w[1] - s.t0 > 0.4) tHit = w[1];
        });
        if (tHit === null) tHit = s.t0 + 0.5 + i * 1.1;
        return tHit;
      });
      return r;
    },
    update: function (r, s, u, d) {
      for (var i = 0; i < r.lanes.length; i++) {
        var L = r.lanes[i];
        var t = r.reveal[i] - s.t0;
        var sweep = easeOutCubic(ramp(u, t, t + 1.3));
        var wpx = 980 * L.frac * sweep;
        L.bar.style.width = fmt(wpx, 1) + "px";
        L.tr.style.left = fmt(wpx - 11, 1) + "px";
        L.tr.style.opacity = fmt(sweep > 0 && sweep < 1 ? 1 : 0);
        var pop = easeOutBack(ramp(u, t + 0.55, t + 0.95));
        L.cnt.style.opacity = fmt(pop);
        L.cnt.style.transform = "scale(" + fmt(0.7 + 0.3 * pop, 3) + ")";
        L.cnt.className = "cnt" + (pop >= 0.99 ? "" : " pk");
      }
    }
  };

  /* repo_card: GitHub dark card + CHECKING ticker that counts in sync with the voice. */
  ARCH.repo_card = {
    build: function (root, s) {
      var p = s.payload;
      var r = {};
      if (p.ticker) r.tick = el("div", "ticker", root);
      var c = el("div", "repocard", root);
      var row = el("div", "pathrow", c);
      el("span", "owner", row, p.owner);
      el("span", "slash", row, "/");
      el("span", "repo", row, p.repo);
      el("div", "ptitle", c, p.repo);
      el("div", "pdesc", c, p.desc);
      var chips = el("div", "chips", c);
      (p.chips || []).forEach(function (t, i) { el("span", i === 0 ? "chip pk" : "chip", chips, t); });
      r.card = c;
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload;
      if (r.tick && p.ticker) {
        var end = ramp(u, 0.4, d * 0.86);
        var n = Math.round(p.ticker.to * easeOutExpo(end));
        r.tick.innerHTML = "";
        el("span", "", r.tick, p.ticker.label + " ");
        el("b", "", r.tick, comma(n));
        el("span", "", r.tick, " / " + comma(p.ticker.to) + " " + (p.ticker.suffix || ""));
      }
      var scan = (u * 220) % 1100;
      r.card.style.boxShadow = "inset 0 0 0 2px rgba(254,41,125," + fmt(0.10 + 0.05 * Math.sin(u * 2.1), 3) + ")";
    }
  };

  /* command_fan: a typed command line, then checks fan out and FOUND hits land row by row. */
  ARCH.command_fan = {
    build: function (root, s) {
      var p = s.payload;
      var r = { wrap: root };
      r.cmd = el("div", "cmdline", root);
      var ds = el("span", "dollar", r.cmd, "$ ");
      r.cmdText = el("span", "", r.cmd, "");
      r.fanSvg = svg(980, 420, root);
      r.fanSvg.style.position = "absolute"; r.fanSvg.style.top = "130px"; r.fanSvg.style.left = "0";
      r.hits = [];
      var H = 420, N = 6;
      for (var i = 0; i < N; i++) {
        var y = 30 + (H - 60) * (i / (N - 1));
        var ln = sEl("path", { d: "M 30 " + (H / 2) + " C 200 " + (H / 2) + " 200 " + y + " 620 " + y, fill: "none", stroke: WHITE, "stroke-width": 1.8, opacity: 0.45 }, r.fanSvg);
        r.hits.push({ ln: ln, y: y });
      }
      r.hitEls = (p.hits || []).map(function (h, i) {
        var row = el("div", "fanhit", root);
        row.style.left = "660px"; row.style.top = (130 + 30 + (H - 60) * (i / (hitsLen(p) - 1)) - 14) + "px";
        el("span", "y", row, "YES  ");
        el("span", "", row, h);
        return row;
      });
      return r;
      function hitsLen(pp) { return Math.max(1, (pp.hits || []).length); }
    },
    update: function (r, s, u, d) {
      var cmd = s.payload.command;
      var typed = Math.floor(clamp(u * 24, 0, cmd.length));
      r.cmdText.textContent = cmd.slice(0, typed) + (typed < cmd.length ? "▉" : "");
      var rows = r.hitEls.length;
      for (var i = 0; i < r.hits.length; i++) {
        var L = r.hits[i];
        var draw = easeOutCubic(ramp(u, 1.0 + i * 0.35, 1.0 + i * 0.35 + 0.9));
        L.ln.setAttribute("stroke-dasharray", fmt(draw * 900, 1) + " 1200");
        if (r.hitEls[i]) {
          var ap = easeOutBack(ramp(u, 1.7 + i * 0.55, 2.05 + i * 0.55));
          r.hitEls[i].style.opacity = fmt(ap);
          r.hitEls[i].style.transform = "translateX(" + fmt((1 - ap) * 40, 1) + "px)";
        }
      }
    }
  };

  /* velocity_curve: lifetime baseline (white) + today's spike (pink), real repo numbers. */
  ARCH.velocity_curve = {
    build: function (root, s) {
      var p = s.payload;
      var r = { wrap: el("div", "vcw", root) };
      var W = 980, H = 500;
      var g = svg(W, H, r.wrap);
      sEl("line", { x1: 40, y1: H - 60, x2: W - 20, y2: H - 60, stroke: TRACK, "stroke-width": 2 }, g);
      var y0 = parseInt(p.start_year || 2019, 10);
      for (var i = 0; i <= 7; i++) {
        var x = 40 + (W - 90) * (i / 7);
        sEl("line", { x1: x, y1: H - 60, x2: x, y2: H - 54, stroke: TRACK, "stroke-width": 2 }, g);
        sText(x, H - 28, String(y0 + i), { fill: MUTE, "font-size": 22, "text-anchor": "middle", "font-family": "monospace" }, g);
      }
      /* baseline: slow steady climb (lifetime average) */
      var pts = [];
      for (var k = 0; k <= 60; k++) {
        var fx = k / 60;
        pts.push([40 + fx * (W - 110), (H - 60) - fx * (H * 0.52) + Math.sin(fx * 9) * 5]);
      }
      r.basePath = sEl("path", { d: "", fill: "none", stroke: WHITE, "stroke-width": 3.4, "stroke-linecap": "round" }, g);
      r.pts = pts;
      /* the spike at TODAY */
      var sx = 40 + (W - 110) * 0.985;
      r.spike = sEl("path", { d: "", fill: "none", stroke: PINK, "stroke-width": 4, "stroke-linecap": "round" }, g);
      r.sx = sx;
      r.todayTick = sEl("line", { x1: sx - 8, y1: 60, x2: sx - 8, y2: H - 60, stroke: MUTE, "stroke-width": 2, "stroke-dasharray": "2 10", opacity: 0 }, g);
      r.todayTag = sText(sx - 24, 46, "TODAY", { fill: MUTE, "font-size": 24, "text-anchor": "end", "font-family": "monospace", opacity: 0 }, g);
      r.tag = sText(60, 52, p.tag || "", { fill: PINK, "font-size": 30, "font-weight": 800, "font-family": "monospace", opacity: 0 }, g);
      r.dot = sEl("circle", { r: 13, fill: PINK, opacity: 0 }, g);
      r.bignum = el("div", "vc-bignum", r.wrap, "");
      r.sub = el("div", "vc-sub tag", r.wrap, p.base_note || "");
      return r;
    },
    update: function (r, s, u, d) {
      var build = easeOutCubic(ramp(u, 0.2, d * 0.5));
      var upto = Math.floor(build * (r.pts.length - 1));
      var dp = "";
      for (var i = 0; i <= upto; i++) dp += (i ? " L " : "M ") + fmt(r.pts[i][0], 1) + " " + fmt(r.pts[i][1], 1);
      r.basePath.setAttribute("d", dp);
      var sp = easeOutExpo(ramp(u, d * 0.52, d * 0.52 + 0.7));
      var sx = r.sx, by = (500 - 60) - (500 * 0.52) * 0.985;
      var spikeH = 150 * sp;
      var sPath = "M " + fmt(40 + (980 - 110) * 0.80, 1) + " " + fmt((500 - 60) - (500 * 0.52) * 0.80, 1) +
                  " C " + fmt(sx - 130, 1) + " " + fmt(by, 1) + " " + fmt(sx - 60, 1) + " " + fmt(by, 1) +
                  " " + fmt(sx - 8, 1) + " " + fmt(by - spikeH, 1);
      r.spike.setAttribute("d", sp > 0 ? sPath : "M 0 0");
      r.todayTick.setAttribute("opacity", fmt(ramp(u, d * 0.5, d * 0.56)));
      r.todayTag.setAttribute("opacity", fmt(ramp(u, d * 0.5, d * 0.56)));
      r.tag.setAttribute("opacity", fmt(ramp(u, d * 0.62, d * 0.72)));
      r.dot.setAttribute("cx", fmt(sx - 8, 1)); r.dot.setAttribute("cy", fmt(by - spikeH, 1));
      r.dot.setAttribute("opacity", fmt(sp > 0.5 ? 1 : 0));
      /* big number counts up as the spike peaks */
      var t = s.cue ? (s.cue - s.t0) : d * 0.6;
      var cnt = easeOutExpo(ramp(u, t, t + 0.9));
      r.bignum.textContent = cnt > 0.001 ? comma(s.payload.stars * cnt) : "";
      r.bignum.style.color = cnt >= 0.999 ? WHITE : PINK;
      r.sub.style.opacity = fmt(ramp(u, d * 0.66, d * 0.76));
    }
  };

  /* name_collision: two ghosts overlap; the pink "not equal" verdict separates name from person. */
  ARCH.name_collision = {
    build: function (root, s) {
      var p = s.payload;
      var r = { wrap: el("div", "collw", root) };
      var W = 980, H = 420;
      var g = svg(W, H, r.wrap);
      r.a = sEl("circle", { r: 150, fill: "rgba(255,255,255,0.10)", stroke: WHITE, "stroke-width": 3 }, g);
      r.b = sEl("circle", { r: 150, fill: "rgba(254,41,125,0.07)", stroke: PINK, "stroke-width": 3 }, g);
      /* a single "?" face inside each ghost while the circles are separate */
      r.qa = sText(0, 0, "@", { fill: WHITE, "font-size": 120, "font-weight": 900, "text-anchor": "middle", opacity: 0.85 }, g);
      r.qb = sText(0, 0, "@", { fill: PINK, "font-size": 120, "font-weight": 900, "text-anchor": "middle", opacity: 0.85 }, g);
      r.neq = sText(W / 2, H / 2 + 96, "≠", { fill: PINK, "font-size": 260, "font-weight": 900, "text-anchor": "middle", opacity: 0 }, g);
      var labels = el("div", "coll-labels", r.wrap);
      var la = el("div", "cl", labels); el("div", "t1", la, p.label_a); el("div", "t2 dim mono", la, (p.verdicts && p.verdicts[0]) || "SITE SAYS YES");
      var lb = el("div", "cl", labels); el("div", "t1", lb, p.label_b); el("div", "t2 mono", lb, (p.verdicts && p.verdicts[1]) || "PERSON UNKNOWN");
      lb.querySelector(".t2").style.color = PINK;
      return r;
    },
    update: function (r, s, u, d) {
      var W = 980, H = 420;
      var ap = easeOutCubic(ramp(u, 0.1, 1.4));
      var wob = Math.sin(u * 1.6) * 8;
      r.a.setAttribute("cx", fmt(W * 0.36 + (1 - ap) * -260 + wob, 1));
      r.a.setAttribute("cy", fmt(H / 2, 1));
      r.b.setAttribute("cx", fmt(W * 0.64 + (1 - ap) * 260 - wob, 1));
      r.b.setAttribute("cy", fmt(H / 2, 1));
      r.qa.setAttribute("x", fmt(W * 0.36 + (1 - ap) * -260, 1)); r.qa.setAttribute("y", fmt(H / 2 + 42, 1));
      r.qb.setAttribute("x", fmt(W * 0.64 + (1 - ap) * 260, 1)); r.qb.setAttribute("y", fmt(H / 2 + 42, 1));
      var t = s.cue ? (s.cue - s.t0) : d * 0.45;
      var np = easeOutBack(ramp(u, t, t + 0.5));
      r.neq.setAttribute("opacity", fmt(np));
      r.neq.setAttribute("y", fmt(H / 2 + 96 - (1 - np) * 30, 1));
    }
  };

  /* quote_card: the honesty beat — docs/help text quoted verbatim in pink italic. */
  ARCH.quote_card = {
    build: function (root, s) {
      var p = s.payload;
      var r = { wrap: el("div", "quotew", root) };
      var panel = el("div", "quote-panel", r.wrap);
      if (p.context) el("div", "mono", panel, p.context).style.cssText = "color:#8B93A3;font-size:28px;letter-spacing:0.14em;margin-bottom:30px;";
      r.q = el("div", "quote-text", panel, p.quote);
      r.src = el("div", "quote-src", panel, p.source);
      return r;
    },
    update: function (r, s, u, d) {
      var p = easeOutCubic(ramp(u, 0.1, 0.7));
      r.q.style.opacity = fmt(p);
      r.q.style.transform = "translateY(" + fmt((1 - p) * 26, 1) + "px)";
      r.src.style.opacity = fmt(ramp(u, 0.6, 1.0));
    }
  };

  /* fan_collapse: the bookend — the fan closes back into one line, then the takeaway line lands. */
  ARCH.fan_collapse = {
    build: function (root, s) {
      var r = { wrap: el("div", "fanwrap", root) };
      var W = 980, H = 560, N = 16;
      var g = svg(W, H, el("div", "fan-hero", r.wrap));
      r.lines = [];
      for (var i = 0; i < N; i++) {
        var y = 40 + (H - 80) * (i / (N - 1));
        var ln = sEl("path", { d: "M 30 " + y + " L 950 " + y, fill: "none", stroke: WHITE, "stroke-width": 1.5, opacity: 0.32 }, g);
        r.lines.push({ ln: ln, y: y, dly: (i % 5) * 0.09 });
      }
      r.final = sEl("path", { d: "M 30 " + H / 2 + " L 950 " + H / 2, fill: "none", stroke: PINK, "stroke-width": 4, "stroke-linecap": "round", opacity: 0 }, g);
      r.line = el("div", "collapse-line", r.wrap, s.payload.line);
      return r;
    },
    update: function (r, s, u, d) {
      var H = 560, i, L;
      for (i = 0; i < r.lines.length; i++) {
        L = r.lines[i];
        var c = easeOutCubic(ramp(u, 0.1 + L.dly, d * 0.42 + L.dly));
        var y = L.y + (H / 2 - L.y) * c;
        L.ln.setAttribute("d", "M 30 " + fmt(y, 1) + " L 950 " + fmt(y, 1));
        L.ln.setAttribute("opacity", fmt(0.32 * (1 - c), 3));
      }
      var f = easeOutExpo(ramp(u, d * 0.44, d * 0.44 + 0.8));
      r.final.setAttribute("opacity", fmt(f > 0 ? 1 : 0, 2));
      r.final.setAttribute("stroke-dasharray", fmt(f * 940, 1) + " 2000");
      var lp = easeOutCubic(ramp(u, d * 0.58, d * 0.58 + 0.6));
      r.line.style.opacity = fmt(lp);
      r.line.style.transform = "translateY(" + fmt((1 - lp) * 24, 1) + "px)";
    }
  };

  /* endcard: real brand logo, follow press locked to the click cue, keyword chip on the word. */
  ARCH.endcard = {
    build: function (root, s) {
      var b = D.brand || {};
      var p = s.payload;
      var r = { wrap: el("div", "endcard", root) };
      if (b.logo) r.logo = el("img", "ec-logo", r.wrap), r.logo.src = b.logo;
      el("div", "ec-name", r.wrap, b.name || "");
      el("div", "ec-handle", r.wrap, b.handle || "");
      r.follow = el("div", "ec-follow", r.wrap, b.cta_button || "Follow");
      r.chip = el("div", "ec-chip", r.wrap);
      el("span", "", r.chip, "COMMENT " + String(p.keyword).toUpperCase());
      el("div", "ec-prompt", r.wrap, p.prompt || "for the repo link");
      var cur = el("div", "ec-cursor", r.wrap);
      cur.innerHTML = "<svg width='70' height='70' viewBox='0 0 24 24'><path d='M4 2 L20 12 L13 13.5 L16.5 21 L13.5 22.5 L10 14.5 L4 19 Z' fill='#ffffff' stroke='#000000' stroke-width='1'/></svg>";
      r.cursor = cur;
      r.cursor.style.left = "880px"; r.cursor.style.top = "1500px";
      return r;
    },
    update: function (r, s, u, d) {
      var ev = s.ev || {};
      var pressT = (ev.press != null ? ev.press - s.t0 : d * 0.55);
      var kwT = (ev.keyword != null ? ev.keyword - s.t0 : d * 0.3);
      var kp = easeOutBack(ramp(u, kwT, kwT + 0.4));
      r.chip.style.opacity = fmt(kp);
      r.chip.style.transform = "scale(" + fmt(0.8 + 0.2 * kp, 3) + ")";
      var a = easeOutCubic(ramp(u, pressT - 0.7, pressT));
      var bx = 880 - a * 340, by = 1500 - a * 560;
      var press = ramp(u, pressT, pressT + 0.12) - ramp(u, pressT + 0.3, pressT + 0.45);
      r.cursor.style.transform = "translate(" + fmt(bx - 880, 1) + "px," + fmt(by - 1500, 1) + "px)";
      r.cursor.style.opacity = a > 0.02 ? 1 : 0;
      r.follow.style.transform = "scale(" + fmt(1 - 0.12 * press, 3) + ")";
    }
  };

  /* ================= stage, captions, clock ================= */
  var stageEl = document.getElementById("stage");
  var capEl;

  function build() {
    el("div", "handle", stageEl, D.handle || "");
    D.scenes.forEach(function (s) {
      var wrap = el("div", "scene", stageEl);
      wrap.style.display = "none";
      var head = el("div", "headline", wrap, s.headline || "");
      var visual = el("div", "visual arch-" + s.archetype, wrap);
      s._wrap = wrap; s._head = head; s._visual = visual;
      s._refs = ARCH[s.archetype].build(visual, s);
      s._acc = accents(s);
    });
    capEl = el("div", "caption", stageEl);
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
      var on = j === cur;
      var pk = s._acc[norm(words[j][0])] === true;
      var w = el("span", "cw" + (pk ? " pk" : ""), capEl, words[j][0]);
      if (on) {
        var k = easeOutBack(ramp(t - words[j][1], 0, 0.16));
        w.style.transform = "scale(" + fmt(1.16 - 0.16 * k, 3) + ")";
      }
    }
  }

  window.setTime = function (t) {
    /* film grain: jitter the noise layer once per frame — a pure function of the frame index */
    var g = GRAIN_EL || (GRAIN_EL = document.querySelector("#postfx .grain"));
    if (g) { var fi = Math.round(t * 30); g.style.backgroundPosition = ((fi * 41) % 211) + "px " + ((fi * 97) % 173) + "px"; }
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    var u = t - s.t0, d = Math.max(1e-6, s.t1 - s.t0);
    var fade = Math.min(ramp(u, 0, 0.18), ramp(d - u, 0, 0.16));
    s._head.style.opacity = fmt(fade);
    s._head.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(u, 0, 0.3))) * 26, 1) + "px)";
    s._visual.style.opacity = fmt(fade);
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
  };

  build();
})();
