/* Generated-graphics engine v2.
 * setTime(t) draws one frame as a pure function of t: no timers, no CSS transitions.
 * Every element is bound to the spoken word timings (scene.cue / scene.cues, computed in cues.py),
 * so the picture lands on the word it depicts. Scenes never hold still: idle motion, drifting
 * particles and the moving grid run on the clock.
 * Data: window.DATA = {width, height, handle, scenes:[{id, archetype, t0, t1, headline, payload,
 *        words, cue, cues, icons}]}
 */
(function () {
  "use strict";
  var GRAIN_EL = null;
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var Y = "#FFD60A", BLUE = "#38BDF8", GREEN = "#4ADE80", INK = "#0C0E13", CARD = "#141925", EDGE = "#2A3140";

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

  /* ---------- icons: 48x48 stroke glyphs, drawn at any size ---------- */
  var ICON_PATHS = {
    code: "M16 14 L6 24 L16 34 M32 14 L42 24 L32 34 M27 10 L21 38",
    files: "M10 6 H28 L38 16 V42 H10 Z M28 6 V16 H38",
    page: "M5 10 H43 V38 H5 Z M5 17 H43 M11 13.5 H13.5 M16.5 13.5 H19",
    play: "M16 11 L38 24 L16 37 Z",
    wrench: "M30 8 C24 8 20 12 20 18 C20 20 21 22 22 23 L8 37 L11 40 L25 26 C26 27 28 28 30 28 C36 28 40 24 40 18 L35 21 L30 18 L27 13 L30 8 Z",
    terminal: "M5 9 H43 V39 H5 Z M11 17 L18 24 L11 31 M22 32 H34",
    plug: "M18 6 V16 M30 6 V16 M11 16 H37 V26 C37 34 31 40 24 40 C17 40 11 34 11 26 Z M24 40 V46",
    agent: "M10 16 H38 V40 H10 Z M24 6 V16 M18 26 H18.5 M30 26 H30.5 M18 34 H30 M4 26 H10 M38 26 H44",
    layers: "M24 6 L42 16 L24 26 L6 16 Z M6 26 L24 36 L42 26 M6 34 L24 44 L42 34",
    check: "M8 25 L19 36 L40 13",
    eye: "M3 24 C11 11 37 11 45 24 C37 37 11 37 3 24 Z",
    bolt: "M29 4 L11 28 H23 L19 44 L37 20 H25 Z",
    star: "M24 5 L29.5 18.5 L44 19.5 L32.8 28.8 L36.5 43 L24 35.2 L11.5 43 L15.2 28.8 L4 19.5 L18.5 18.5 Z",
    shield: "M24 5 L41 11 V24 C41 34 33 40 24 43 C15 40 7 34 7 24 V11 Z M17 24 L22 29 L31 19",
    bookmark: "M13 6 H35 V42 L24 34 L13 42 Z",
    chat: "M7 10 H41 V32 H22 L14 40 V32 H7 Z",
    plus: "M24 8 V40 M8 24 H40",
    arrow: "M8 24 H38 M28 14 L38 24 L28 34",
    dot: "M24 19 A5 5 0 1 0 24.01 19"
  };
  function icon(name, parent, color) {
    var s = svg(48, 48, parent, "ico");
    var p = document.createElementNS(NS, "path");
    p.setAttribute("d", ICON_PATHS[name] || ICON_PATHS.dot);
    p.setAttribute("fill", "none");
    p.setAttribute("stroke", color || Y);
    p.setAttribute("stroke-width", "3.2");
    p.setAttribute("stroke-linecap", "round");
    p.setAttribute("stroke-linejoin", "round");
    s.appendChild(p);
    return s;
  }

  /* ---------- per-archetype builders and updaters ---------- */
  var ARCH = {};

  /* concept_card: letters rise one by one on the spoken word, a ripple fires, the underline draws. */
  ARCH.concept_card = {
    build: function (root, s) {
      var r = { wrap: el("div", "cc", root) };
      r.ripple = el("div", "ripple", r.wrap);
      r.big = el("div", "big", r.wrap);
      if (String(s.payload.big).length > 24) { r.big.className += " big-long"; }
      r.letters = [];
      String(s.payload.big).split(" ").forEach(function (word) {
        var ws = el("span", "wd", r.big);
        word.split("").forEach(function (ch) { r.letters.push(el("span", "lt", ws, ch)); });
      });
      r.line = el("div", "uline", r.wrap);
      r.sub = el("div", "sub", r.wrap, s.payload.sub || "");
      return r;
    },
    update: function (r, s, u, d) {
      var c = u - (s.cue - s.t0);
      r.wrap.style.transform = "translateY(" + fmt(Math.sin(u * 2.1) * 8) + "px)";
      // The whole title is up inside ~0.34 s of the spoken cue however long it is: a fixed per-letter
      // stagger made long titles finish a second after the word, which reads as lagging kinetic text.
      var gap = Math.min(0.022, 0.16 / Math.max(1, r.letters.length));
      r.letters.forEach(function (sp, i) {
        var p = ramp(c, i * gap, i * gap + 0.3);
        sp.style.opacity = fmt(p);
        sp.style.transform = "translateY(" + fmt((1 - easeOutBack(p)) * 70) + "px)";
      });
      var rp = ramp(c, 0, 0.9);
      r.ripple.style.opacity = fmt((1 - rp) * 0.5 * ramp(c, 0, 0.05));
      r.ripple.style.transform = "scale(" + fmt(0.4 + 1.5 * easeOutCubic(rp), 3) + ")";
      r.line.style.transform = "scaleX(" + fmt(easeOutExpo(ramp(c, 0.2, 0.75))) + ")";
      r.sub.style.opacity = fmt(ramp(c, 0.45, 0.85));
      r.sub.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(c, 0.45, 0.85))) * 28) + "px)";
    }
  };

  /* stat_pop: a ring fills and its ticks light in turn; the number counts up to the spoken value. */
  ARCH.stat_pop = {
    build: function (root, s) {
      var r = { wrap: el("div", "stat-wrap", root), ticks: [] };
      r.box = el("div", "ring-box", r.wrap);
      r.svg = svg(620, 620, r.box, "ring");
      var track = document.createElementNS(NS, "circle");
      track.setAttribute("cx", "310"); track.setAttribute("cy", "310"); track.setAttribute("r", "276");
      track.setAttribute("fill", "rgba(20,25,37,0.9)"); track.setAttribute("stroke", EDGE); track.setAttribute("stroke-width", "12");
      r.svg.appendChild(track);
      r.arc = document.createElementNS(NS, "circle");
      r.arc.setAttribute("cx", "310"); r.arc.setAttribute("cy", "310"); r.arc.setAttribute("r", "276");
      r.arc.setAttribute("fill", "none"); r.arc.setAttribute("stroke", Y); r.arc.setAttribute("stroke-width", "16");
      r.arc.setAttribute("stroke-linecap", "round"); r.arc.setAttribute("transform", "rotate(-90 310 310)");
      r.circ = 2 * Math.PI * 276;
      r.arc.setAttribute("stroke-dasharray", String(r.circ));
      r.svg.appendChild(r.arc);
      for (var k = 0; k < 24; k++) {
        var a = (k / 24) * Math.PI * 2;
        var tk = document.createElementNS(NS, "line");
        tk.setAttribute("x1", fmt(310 + Math.cos(a) * 304)); tk.setAttribute("y1", fmt(310 + Math.sin(a) * 304));
        tk.setAttribute("x2", fmt(310 + Math.cos(a) * 292)); tk.setAttribute("y2", fmt(310 + Math.sin(a) * 292));
        tk.setAttribute("stroke", EDGE); tk.setAttribute("stroke-width", "6"); tk.setAttribute("stroke-linecap", "round");
        r.svg.appendChild(tk);
        r.ticks.push(tk);
      }
      var c = el("div", "stat-c", r.box);
      r.num = el("div", "stat", c);
      r.unit = el("div", "stat-unit", r.wrap, s.payload.unit || "");
      r.sub = el("div", "sub", r.wrap, s.payload.sub || "");
      return r;
    },
    update: function (r, s, u, d) {
      var c = u - (s.cue - s.t0);
      var target = Number(s.payload.value);
      var v = Math.round(target * easeOutExpo(ramp(c, 0, 1.1)));
      r.num.textContent = String(v) + (s.payload.suffix || "");
      r.num.style.transform = "scale(" + fmt(0.8 + 0.2 * easeOutBack(ramp(c, 0, 0.45)), 3) + ")";
      r.num.style.textShadow = "0 0 " + fmt(20 + 30 * (0.5 + 0.5 * Math.sin(u * 3.2)) * ramp(c, 0, 0.3), 1) + "px rgba(255,214,10,0.6)";
      r.arc.setAttribute("stroke-dashoffset", fmt(r.circ * (1 - easeOutCubic(ramp(c, 0, 1.2))), 2));
      r.ticks.forEach(function (tk, i) { tk.setAttribute("stroke", c > i * 0.03 ? Y : EDGE); });
      r.svg.style.transform = "rotate(" + fmt(u * 9, 2) + "deg)";
      r.unit.style.opacity = fmt(ramp(c, 0.4, 0.8));
      r.sub.style.opacity = fmt(ramp(c, 0.5, 0.9));
      r.sub.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(c, 0.5, 0.9))) * 24) + "px)";
    }
  };

  /* chip_grid: cards slide in on their own word; a rail draws down the grid; the highlight pulses. */
  ARCH.chip_grid = {
    build: function (root, s) {
      var r = { wrap: el("div", "chips", root), chips: [] };
      r.rail = el("div", "rail", r.wrap);
      s.payload.chips.forEach(function (text, i) {
        var c = el("div", "chip", r.wrap);
        c.style.height = Math.min(176, Math.floor(860 / s.payload.chips.length) - 18) + "px";
        var ic = el("div", "chip-ic", c);
        icon(s.icons[i] || "dot", ic, i === s.payload.highlight ? INK : BLUE);
        el("div", "chip-t", c, text);
        el("div", "chip-n", c, String(i + 1).padStart(2, "0"));
        el("div", "shine", c);
        r.chips.push(c);
      });
      return r;
    },
    update: function (r, s, u, d) {
      var n = r.chips.length, hi = s.payload.highlight;
      var first = s.cues[0], last = s.cues[n - 1];
      var rail = ramp(u + s.t0, first, last + 0.3);
      r.rail.style.transform = "scaleY(" + fmt(rail, 3) + ")";
      r.chips.forEach(function (c, i) {
        var t = u + s.t0 - s.cues[i];
        var p = easeOutExpo(ramp(t, 0, 0.5));
        c.style.opacity = fmt(ramp(t, 0, 0.2));
        c.style.transform = "translateX(" + fmt((1 - p) * 120) + "px) translateY(" + fmt(p > 0.99 ? 4 * Math.sin(u * 2 + i * 1.3) : 0) + "px)";
        var sh = c.querySelector(".shine");
        sh.style.opacity = fmt(ramp(t, 0.1, 0.25) * (1 - ramp(t, 0.5, 0.9)));
        sh.style.transform = "translateX(" + fmt(-100 + 200 * ramp(t, 0.1, 0.9)) + "%)";
        if (i === hi) {
          var on = ramp(t, 0.3, 0.6);
          var pulse = 0.5 + 0.5 * Math.sin(u * 4.2);
          c.style.background = "linear-gradient(90deg," + Y + " 0%, #FFB800 100%)";
          c.style.color = INK;
          c.style.opacity = fmt(ramp(t, 0, 0.2));
          c.style.boxShadow = "0 0 " + fmt(10 + 34 * pulse * on, 1) + "px rgba(255,214,10," + fmt(0.25 + 0.6 * pulse * on, 2) + ")";
        }
      });
    }
  };

  /* flow_link: nodes pop in on their words; connectors draw between them; packets travel. */
  /* Shrink a node label until it fits its box, so a long single word never spills past the border. */
  function fitNodeText(t, box) {
    var fs = parseFloat(getComputedStyle(t).fontSize);
    var max = box.clientWidth - 40;
    var guard = 0;
    while (t.scrollWidth > max && fs > 24 && guard++ < 40) { fs -= 2; t.style.fontSize = fs + "px"; }
  }

  ARCH.flow_link = {
    build: function (root, s) {
      var r = { wrap: el("div", "flow", root), nodes: [], conns: [] };
      r.label = el("div", "edge-label", r.wrap, s.payload.edge_label || "");
      r.row = el("div", "flow-row", r.wrap);
      if (s.payload.nodes.length >= 3) { r.row.className += " flow-3"; }
      s.payload.nodes.forEach(function (text, i) {
        var n = el("div", "node", r.row);
        icon(s.icons[i] || "dot", el("div", "node-ic", n), i === 0 ? Y : BLUE);
        fitNodeText(el("div", "node-t", n, text), n);
        r.nodes.push(n);
        if (i < s.payload.nodes.length - 1) {
          var cs = el("div", "conn", r.row);
          var sv = svg(150, 40, cs, "conn-svg");
          var ln = document.createElementNS(NS, "line");
          ln.setAttribute("x1", "4"); ln.setAttribute("y1", "20"); ln.setAttribute("x2", "104"); ln.setAttribute("y2", "20");
          ln.setAttribute("stroke", Y); ln.setAttribute("stroke-width", "5"); ln.setAttribute("stroke-linecap", "round");
          ln.setAttribute("stroke-dasharray", "100"); sv.appendChild(ln);
          var head = document.createElementNS(NS, "path");
          head.setAttribute("d", "M96 10 L114 20 L96 30 Z"); head.setAttribute("fill", Y); sv.appendChild(head);
          var pk = [el("div", "packet", cs), el("div", "packet p2", cs)];
          r.conns.push({ ln: ln, head: head, pk: pk });
        }
      });
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.nodes.forEach(function (n, i) {
        var t = now - s.cues[i];
        var p = easeOutBack(ramp(t, 0, 0.45));
        n.style.opacity = fmt(ramp(t, 0, 0.2));
        n.style.transform = "scale(" + fmt(0.7 + 0.3 * p, 3) + ") translateY(" + fmt(Math.sin(u * 1.7 + i * 2) * 5) + "px)";
        n.style.borderColor = i === 0 ? Y : BLUE;
      });
      r.conns.forEach(function (c, i) {
        var start = s.cues[i + 1] !== undefined ? s.cues[i + 1] : s.cues[i];
        var p = easeOutCubic(ramp(now, start - 0.1, start + 0.35));
        c.ln.setAttribute("stroke-dashoffset", fmt(100 * (1 - p), 2));
        c.head.style.opacity = fmt(ramp(now, start + 0.3, start + 0.45));
        var ph = (u * 0.8 + i * 0.37) % 1;
        var on = ramp(now, start + 0.35, start + 0.5);
        c.pk[0].style.opacity = fmt(on);
        c.pk[0].style.left = fmt(6 + ph * 88, 2) + "%";
        c.pk[1].style.opacity = fmt(on * 0.6);
        c.pk[1].style.left = fmt(6 + ((ph + 0.5) % 1) * 88, 2) + "%";
      });
      r.label.style.opacity = fmt(ramp(now, s.cues[0] - 0.1, s.cues[0] + 0.3));
    }
  };

  /* terminal_type: typed on the spoken words, syntax-coloured, with a live status line. */
  ARCH.terminal_type = {
    build: function (root, s) {
      var r = { wrap: el("div", "term", root), lines: [] };
      var bar = el("div", "term-bar", r.wrap);
      el("span", "tl r", bar); el("span", "tl y", bar); el("span", "tl g", bar);
      el("span", "term-title", bar, (s.payload && s.payload.title) || "craft-anything");
      var body = el("div", "term-body", r.wrap);
      s.payload.lines.forEach(function (text) {
        var node = el("div", "term-line", body);
        r.lines.push({ node: node, text: text });
      });
      r.caret = el("span", "caret", null, "\u258d");
      r.status = el("div", "term-status", r.wrap);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var cps = 30, typedEnd = s.t0;
      var active = null, firstIdle = null;
      r.lines.forEach(function (ln, i) {
        var t0 = s.cues[i] !== undefined ? s.cues[i] : s.cue;
        var n = Math.floor(clamp((now - t0) * cps, 0, ln.text.length));
        // The shell prompt is on screen from the scene's first frame, so the window reads as "ready",
        // never as an empty box waiting for the voice.
        if (i === 0 && ln.text.charAt(0) === "$") n = Math.max(n, 2);
        if (n === 0 && !firstIdle) firstIdle = ln.node;
        var shown = ln.text.slice(0, n);
        ln.node.innerHTML = "";
        colourise(ln.node, shown, ln.text.charAt(0) === "$");
        if (n > 0 && n < ln.text.length) active = ln.node;
        if (n >= ln.text.length) typedEnd = Math.max(typedEnd, t0 + ln.text.length / cps);
      });
      // The prompt is alive from the scene's first frame: the caret waits on the next empty line, so the
      // window is never a blank box before the first command is spoken.
      if (!active) active = firstIdle || r.lines[r.lines.length - 1].node;
      active.appendChild(r.caret);
      r.caret.style.opacity = (Math.floor(now * 2.5) % 2 === 0) ? "1" : "0";
      var allTyped = r.lines.every(function (ln, i) {
        var t0 = s.cues[i] !== undefined ? s.cues[i] : s.cue;
        return now >= t0 + ln.text.length / cps;
      });
      var started = r.lines.some(function (ln, i) {
        var t0 = s.cues[i] !== undefined ? s.cues[i] : s.cue;
        return now >= t0;
      });
      r.status.textContent = allTyped && now > typedEnd + 0.15 ? "\u2713 done" : (started ? "\u25cf running" : "\u25cf waiting");
      r.status.style.color = allTyped && now > typedEnd + 0.15 ? GREEN : BLUE;
    }
  };
  function colourise(node, text, isCmd) {
    if (!isCmd) {
      el("span", "t-out", node, text);
      return;
    }
    var m = text.match(/^(\$\s*)(\S+)?(\s+)?(\S+)?(.*)$/);
    if (!m) { el("span", "t-p", node, text); return; }
    if (m[1]) el("span", "t-p", node, m[1]);
    if (m[2]) el("span", "t-cmd", node, m[2]);
    if (m[3]) node.appendChild(document.createTextNode(m[3]));
    if (m[4]) el("span", "t-sub", node, m[4]);
    if (m[5]) el("span", "t-arg", node, m[5]);
  }

  /* toggle_steps: each step ticks on its word, a row wash sweeps in, a progress bar fills. */
  ARCH.toggle_steps = {
    build: function (root, s) {
      var r = { wrap: el("div", "steps", root), rows: [] };
      s.payload.steps.forEach(function (text, i) {
        var row = el("div", "step", r.wrap);
        row.style.height = Math.min(158, Math.floor(860 / s.payload.steps.length) - 18) + "px";
        var box = el("div", "tick", row);
        var sv = svg(48, 48, box, "tick-svg");
        var p = document.createElementNS(NS, "path");
        p.setAttribute("d", ICON_PATHS.check); p.setAttribute("fill", "none"); p.setAttribute("stroke", INK);
        p.setAttribute("stroke-width", "6"); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
        p.setAttribute("stroke-dasharray", "50"); sv.appendChild(p);
        el("div", "step-t", row, text);
        el("div", "wash", row);
        r.rows.push({ row: row, box: box, p: p, wash: row.querySelector(".wash") });
      });
      r.bar = el("div", "prog", r.wrap);
      r.barFill = el("div", "prog-fill", r.bar);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.rows.forEach(function (x, i) {
        var t = now - s.cues[i];
        var on = ramp(t, 0, 0.12);
        x.row.style.opacity = fmt(0.35 + 0.65 * ramp(t, -0.35, 0));
        x.row.style.transform = "translateX(" + fmt((1 - easeOutCubic(ramp(t, -0.35, 0.1))) * -60) + "px)";
        x.row.style.borderColor = on > 0 ? Y : EDGE;
        x.box.style.background = on > 0 ? Y : "transparent";
        x.box.style.borderColor = on > 0 ? Y : BLUE;
        x.p.setAttribute("stroke-dashoffset", fmt(50 * (1 - ramp(t, 0.08, 0.3)), 2));
        x.wash.style.transform = "scaleX(" + fmt(easeOutCubic(ramp(t, 0, 0.45)), 3) + ")";
      });
      var last = s.cues[s.cues.length - 1];
      r.barFill.style.transform = "scaleX(" + fmt(easeOutCubic(ramp(now, s.cues[0], last + 0.4)), 3) + ")";
    }
  };

  /* cta_stack: three pills rise in on their words; the primary pill breathes; a shine sweeps across. */
  ARCH.cta_stack = {
    build: function (root, s) {
      var r = { wrap: el("div", "cta", root), pills: [] };
      var glyphs = ["bookmark", "chat", "plus"];
      s.payload.lines.forEach(function (text, i) {
        var p = el("div", "pill" + (i === 0 ? " pill-hi" : ""), r.wrap);
        icon(glyphs[i] || "arrow", el("div", "pill-ic", p), i === 0 ? INK : Y);
        el("div", "pill-t", p, text);
        el("div", "shine", p);
        r.pills.push(p);
      });
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      r.pills.forEach(function (p, i) {
        var t = now - s.cues[i];
        var k = easeOutBack(ramp(t, 0, 0.5));
        p.style.opacity = fmt(ramp(t, 0, 0.2));
        p.style.transform = "translateY(" + fmt((1 - k) * 200 + (i === 0 ? 0 : Math.sin(u * 2.2 + i) * 4)) + "px) scale(" + fmt(i === 0 ? 1 + 0.02 * Math.sin(u * 3.4) : 1, 3) + ")";
        var sh = p.querySelector(".shine");
        sh.style.transform = "translateX(" + fmt(-110 + 220 * ramp(t, 0.3, 0.9)) + "%)";
        sh.style.opacity = fmt(ramp(t, 0.3, 0.4) * (1 - ramp(t, 0.6, 0.95)));
      });
    }
  };

  /* endcard: the brand end-card. Real logo (never a text initial), handle, the CTA keyword, a Follow
   button, and a cursor that presses it. The press fires on the pipeline's own `press` time, the same
   number the click SFX uses, so what you hear and what you see are one event. */
  ARCH.endcard = {
    build: function (root, s) {
      var b = (D && D.brand) || {};
      var p = s.payload || {};
      var r = { wrap: el("div", "ec", root) };
      r.card = el("div", "ec-card", r.wrap);
      var av = el("div", "ec-av", r.card);
      if (b.logo) {
        var img = document.createElement("img");
        img.src = b.logo; img.alt = b.name || "";
        av.appendChild(img);
      } else {
        el("span", "ec-initial", av, String(b.name || "H").slice(0, 1));
      }
      r.name = el("div", "ec-name", r.card, b.name || "");
      var badge = el("span", "ec-badge", r.name);
      badge.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="#0C0E13" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      el("div", "ec-handle", r.card, b.handle || D.handle || "");
      if (b.tagline) el("div", "ec-tag", r.card, b.tagline);
      r.kw = el("div", "ec-kw", r.card);
      el("span", "ec-kw-ic", r.kw, "comment");
      el("span", "ec-kw-t", r.kw, p.keyword ? String(p.keyword).toUpperCase() : "");
      r.btn = el("div", "ec-btn", r.card);
      r.lbl = el("span", "ec-lbl", r.btn, p.follow || b.cta_button || "Follow");
      r.done = el("div", "ec-done", r.btn);
      el("span", "ec-done-t", r.done, "Following");
      r.ring = el("div", "ec-ring", r.btn);
      r.cur = svg(24, 24, r.btn, "ec-cursor");  // parented to the button so it always lands on it
      var path = document.createElementNS(NS, "path");
      path.setAttribute("d", "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z");
      path.setAttribute("fill", "#FFFFFF");
      path.setAttribute("stroke", "#0C0E13");
      path.setAttribute("stroke-width", "1.2");
      path.setAttribute("stroke-linejoin", "round");
      r.cur.appendChild(path);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var ev = s.ev || {};
      var pr = (typeof ev.press === "number" ? ev.press : s.t0 + Math.max(1.2, Math.min(d * 0.62, d - 1.1))) - s.t0;
      var kw = (typeof ev.keyword === "number" ? ev.keyword : s.cue) - s.t0;

      // the card lands on the first word of the CTA
      var cin = easeOutBack(ramp(u, 0, 0.5));
      r.card.style.opacity = fmt(ramp(u, 0, 0.2));
      r.card.style.transform = "translateY(" + fmt((1 - cin) * 110) + "px) scale(" + fmt(0.94 + 0.06 * cin, 3) + ")";

      // keyword chip pops on the spoken keyword, then keeps breathing
      var kp = easeOutBack(ramp(u, kw, kw + 0.42));
      r.kw.style.opacity = fmt(ramp(u, kw, kw + 0.16));
      r.kw.style.transform = "translateY(" + fmt((1 - kp) * 44) + "px) scale(" + fmt(0.86 + 0.14 * kp + 0.012 * Math.sin(u * 3.1), 3) + ")";

      // cursor: arrives, presses, leaves
      var arrive = easeOutCubic(ramp(u, pr - 0.6, pr));
      var leave = ramp(u, pr + 0.55, pr + 0.85);
      r.cur.style.opacity = fmt(ramp(u, pr - 0.62, pr - 0.42) * (1 - leave));
      r.cur.style.transform = "translate(" + fmt((1 - arrive) * 210) + "px," + fmt((1 - arrive) * 250) + "px) scale(1)";

      var down = ramp(u, pr - 0.12, pr - 0.02) * (1 - ramp(u, pr + 0.02, pr + 0.2));
      var back = easeOutBack(ramp(u, pr + 0.04, pr + 0.26));
      var bscale = 1 - 0.09 * down + 0.012 * (u > pr + 0.04 ? 0 : Math.sin(u * 3.2));
      r.btn.style.transform = "scale(" + fmt(bscale * (0.96 + 0.04 * easeOutBack(ramp(u, 0.16, 0.52))), 3) + ")";
      r.btn.style.boxShadow = "0 0 " + fmt(18 + 26 * (0.5 + 0.5 * Math.sin(u * 3.2))) + "px rgba(255,214,10," + fmt(0.35 + 0.1 * Math.sin(u * 3.2)) + ")";
      r.lbl.style.opacity = fmt(1 - ramp(u, pr + 0.02, pr + 0.1));
      r.done.style.opacity = fmt(ramp(u, pr + 0.03, pr + 0.12));
      r.done.style.transform = "scale(" + fmt(0.9 + 0.1 * back) + ")";
      r.ring.style.opacity = fmt(ramp(u, pr, pr + 0.03) * (1 - ramp(u, pr + 0.3, pr + 0.62)));
      r.ring.style.transform = "scale(" + fmt(0.7 + 1.5 * easeOutCubic(ramp(u, pr, pr + 0.55)), 3) + ")";

      // idle life so the last frame is never frozen
      r.wrap.style.transform = "translateY(" + fmt(Math.sin(u * 1.6) * 5) + "px)";
    }
  };

  /* ---------- stage ---------- */
  var stageEl, gridEl, glowEl, capEl, handleEl, particles = [];

  function build() {
    stageEl = document.getElementById("stage");
    gridEl = el("div", "grid", stageEl); gridEl.id = "grid";
    glowEl = el("div", "glow", stageEl);
    for (var p = 0; p < 26; p++) {
      var dot = el("div", "dot", stageEl);
      var seed = (p * 9301 + 49297) % 233280 / 233280;
      particles.push({ el: dot, x: seed * 1080, y: ((p * 7919) % 1920), v: 18 + (p % 7) * 9, s: 2 + (p % 3) * 2 });
    }
    handleEl = el("div", "handle", stageEl, D.handle || "");
    D.scenes.forEach(function (s) {
      var wrap = el("div", "scene", stageEl);
      wrap.style.display = "none";
      var head = el("div", "headline", wrap, s.headline || "");
      var visual = el("div", "visual arch-" + s.archetype, wrap);
      s._wrap = wrap; s._head = head; s._visual = visual;
      s._refs = ARCH[s.archetype].build(visual, s);
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
    // The word being said is the FIRST word on screen (owner, 6 Nov 2026: kinetic text read one word
    // behind because the line led with the previous word). Three words of look-ahead follow it.
    var start = Math.max(0, Math.min(cur, words.length - 4));
    var end = Math.min(words.length, start + 4);
    capEl.innerHTML = "";
    for (var j = start; j < end; j++) {
      var on = j === cur;
      var w = el("span", on ? "cw cw-on" : "cw", capEl, words[j][0]);
      if (on) {
        var k = easeOutBack(ramp(t - words[j][1], 0, 0.16));
        w.style.transform = "scale(" + fmt(1.14 - 0.14 * k, 3) + ")";
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
    // The shared house card owns the complete endcard scene.
    if (s.archetype === "endcard") { D.scenes.forEach(function (x) { x._wrap.style.display = "none"; }); return; }
    var u = t - s.t0, d = Math.max(1e-6, s.t1 - s.t0);
    var fade = 0.7 + 0.3 * Math.min(ramp(u, 0, 0.18), ramp(d - u, 0, 0.16));
    s._head.style.opacity = fmt(fade);
    s._head.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(u, 0, 0.3))) * 30) + "px)";
    s._visual.style.opacity = fmt(fade);
    s._visual.style.transform = "scale(" + fmt(0.96 + 0.04 * easeOutCubic(ramp(u, 0, 0.3)) + 0.03 * (u / d), 4) + ")";
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);

    // Ambient layer: grid drifts, glow wanders on a slow Lissajous path, particles rise.
    gridEl.style.backgroundPosition = fmt(t * 90, 2) + "px " + fmt(t * 90, 2) + "px";
    glowEl.style.transform = "translate(" + fmt(Math.sin(t * 0.21) * 160, 1) + "px," + fmt(Math.cos(t * 0.17) * 220, 1) + "px)";
    particles.forEach(function (p) {
      var y = ((p.y - t * p.v) % 1920 + 1920) % 1920;
      p.el.style.transform = "translate(" + fmt(p.x + Math.sin(t * 0.8 + p.x) * 14, 1) + "px," + fmt(y, 1) + "px)";
      p.el.style.width = p.el.style.height = p.s + "px";
      p.el.style.opacity = fmt(0.25 + 0.2 * Math.sin(t * 1.3 + p.y));
    });
  };

  build();
})();
