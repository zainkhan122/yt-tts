/* redline: a paper report being marked up in red pen.
 * Pure function of setTime(t) â€” no timers, no transitions.
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
  /* How fast the report page scrolls while it is read, in px per second. It has to be fast
   * enough that the picture changes in every quarter second (the Short QA measures the frame
   * difference over 0.25 s bins), and slow enough that the type stays readable. */
  var SCROLL_PX_PER_S = 26;
  /* The camera's breath: a slow push in and back, so the frame is never frozen. It is a
   * triangle wave with eased corners â€” a constant rate, so every quarter second moves the
   * picture, and a bounded amplitude, so the page never grows out of the frame. */
  var PULSE_AMP = 0.16;
  var PULSE_PERIOD = 2.2;
  function pulse(u) {
    var ph = (u % PULSE_PERIOD) / PULSE_PERIOD;
    var tri = ph < 0.5 ? ph * 2 : 2 - ph * 2;
    return eCubic(tri);
  }
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
  /* every sheet carries a page number, so each scene reads as a page of one report. It is pinned
   * to the frame (not to the page), because the page scrolls while it is read. */
  var FIXED_EL = null;
  function pageNum(root, s) { el("div", "rl-pnum", FIXED_EL || root, "PAGE " + pad2(s.idx)); }

  /* ---------- the exhibit: the tool's own page, pasted into the report ----------
   * A report about a tool that shows no tool is a text card. The capture packs hold real screen
   * recordings of the product; graphics/stage.py cuts them into frames and hands them over as
   * `evidence_frames`. The page here PLAYS those frames, so the viewer watches the product load
   * instead of reading about it (the owner's bar: no full static screenshot held over a second),
   * and the house type sits over the top of it.
   */
  function exhibit(root, s) {
    var frames = s.evidence_frames || [];
    if (!frames.length) return null;
    var ex = el("div", "rl-exhibit", root);
    var shot = el("div", "rl-exhibit-shot", ex);
    var zoom = el("div", "rl-exhibit-zoom", shot);
    var imgs = frames.map(function (src) {
      var im = el("img", null, zoom);
      im.src = src;
      im.alt = "Captured product page";
      im.style.opacity = "0";
      return im;
    });
    if (s.evidence_label) el("div", "rl-exhibit-tab", ex, s.evidence_label);
    if (s.evidence_credit) el("div", "rl-exhibit-credit", ex, s.evidence_credit);
    return { node: ex, imgs: imgs, count: frames.length };
  }

  function exhibitUpdate(refs, s, u) {
    if (!refs) return;
    /* the exhibit arrives with the page, not before it: the shot fades up with the sheet */
    refs.node.style.opacity = fmt(ramp(u, 0.05, 0.4), 3);
    var span = Math.max(0.001, s.t1 - s.t0);
    /* the recording plays at its own speed: the whole clip fits the scene, whatever the voice does */
    var fps = s.evidence_fps || 0;
    var dur = s.evidence_duration || 0;
    var clipT = fps > 0 ? (u / span) * dur : (u / span) * refs.count;
    var slot = clipT * fps;
    var i0 = Math.floor(slot) % refs.count;
    var i1 = (i0 + 1) % refs.count;
    var f = slot - Math.floor(slot);
    /* a short dissolve forward reads as the page filling up, not as a slideshow */
    var blend = Math.max(0, (f - 0.7) / 0.3);
    refs.imgs.forEach(function (im, i) {
      var o = i === i0 ? 1 - blend : (i === i1 ? blend : 0);
      im.style.opacity = fmt(o, 3);
    });
  }

  var ARCH = {};

  /* doc_title: the cover of the report. Kicker, big title, then the rule lines draw in. */
  ARCH.doc_title = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.paper = paperRules(root);
      pageNum(root, s);
      var sheet = el("div", "rl-sheet rl-sheet--title", root);
      el("div", "rl-kicker", sheet, p.kicker || "REPORT");
      r.title = el("div", "rl-title", sheet);
      r.title.textContent = s.headline || p.title || "";
      r.rule = el("i", "rl-rule", sheet);
      r.lines = (p.lines || []).map(function (t) {
        var row = el("div", "rl-line", sheet);
        el("em", null, row, t);
        return { row: row, t: t };
      });
      r.ex = exhibit(sheet, s);
      if (r.ex) sheet.classList.add("rl-sheet--exhibit");
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
      exhibitUpdate(r.ex, s, u);
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
      r.ex = exhibit(sheet, s);
      if (r.ex) sheet.classList.add("rl-sheet--exhibit");
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
      exhibitUpdate(r.ex, s, u);
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
      r.ex = exhibit(sheet, s);
      if (r.ex) sheet.classList.add("rl-sheet--exhibit");
      r.when = bindTimes(p.cue_phrases, s, 1)[0];
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload || {}, since = s.t0 + u - r.when;
      var val = parseFloat(p.value) || 0;
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      var k = eExpo(ramp(since, 0, 0.7));
      r.num.textContent = since < 0 ? "â€”" : Math.round(val * k) + (p.suffix || "");
      var pop = eBack(ramp(since, 0, 0.35));
      r.box.style.transform = "scale(" + fmt(0.9 + 0.1 * pop, 3) + ") rotate(-1.4deg)";
      r.box.style.opacity = fmt(0.35 + 0.65 * ramp(since, 0, 0.2));
      r.foot.style.opacity = fmt(ramp(since, 0.25, 0.55));
      exhibitUpdate(r.ex, s, u);
    }
  };

  /* score_rules: a scored table â€” the claim, a red score, and a hairline that fills. */
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
      r.ex = exhibit(sheet, s);
      if (r.ex) sheet.classList.add("rl-sheet--exhibit");
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
      exhibitUpdate(r.ex, s, u);
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
      r.ex = exhibit(sheet, s);
      if (r.ex) sheet.classList.add("rl-sheet--exhibit");
      return r;
    },
    update: function (r, s, u, d) {
      r.paper.style.opacity = fmt(ramp(u, 0, 0.3));
      r.card.style.opacity = fmt(ramp(u, 0.08, 0.32));
      r.card.style.transform = "translateY(" + fmt((1 - eCubic(ramp(u, 0.08, 0.5))) * 30, 1) + "px)";
      r.quote.style.opacity = fmt(ramp(u, 0.2, 0.45));
      r.attrib.style.opacity = fmt(ramp(u, 0.5, 0.8));
      r.underline.style.width = fmt(eExpo(ramp(u, 0.55, 0.95)) * 100, 1) + "%";
      exhibitUpdate(r.ex, s, u);
    }
  };

  /* endcard: the last page, signed off. */
  /* endcard: BYPASSED â€” graphics/outro.js draws the single house brand card for every short.
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
      /* The camera. The report is READ on a camera that scrolls and breathes, so the frame is
       * never a still card. The camera has three layers:
       *   .rl-rules-layer  the paper's ruling — it moves with the page (the ruling IS the page)
       *   .rl-clip         the page itself; the content slides up and out of the frame
       *   .rl-sticky       the section label, pinned, so the page slides under it
       * The clip hides what has scrolled past, so the page is read, not clipped by accident. */
      var cam = el("div", "rl-camera", visual);
      cam.setAttribute("data-house-camera", "1");
      var rules = el("div", "rl-rules-layer", cam);
      var sticky = el("div", "rl-sticky", cam);
      var clip = el("div", "rl-clip", cam);
      if (s.archetype !== "doc_title") clip.classList.add("rl-clip--scroll");
      var move = el("div", "rl-camera-move", clip);
      move.setAttribute("data-house-camera", "1");
      var fixed = el("div", "rl-fixed", cam);
      fixed.setAttribute("data-house-camera", "1");
      FIXED_EL = fixed;
      s._wrap = wrap; s._visual = visual; s._cam = move; s._rules = rules; s._sticky = sticky;
      s._refs = ARCH[s.archetype].build(move, s);
      /* the section label is pinned; the ruling moves with the page */
      var sheet = move.querySelector(".rl-sheet");
      var kicker = sheet ? sheet.querySelector(".rl-kicker") : null;
      if (kicker) sticky.appendChild(kicker);
      var ruling = move.querySelector(".rl-rules");
      if (ruling) rules.appendChild(ruling);
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
    /* The report is READ, not held: the page scrolls up while the line is spoken, at a fixed
     * 30 px/second, so the picture is never a still card (the owner's bar: a visible change
     * every few seconds). The camera also breathes â€” a slow push and settle â€” so even the
     * quietest passage keeps moving. The caption band does not move with the page. */
    var breath = 1 + PULSE_AMP * pulse(u);
    /* The cover page is the cover page: it does not scroll (the title has to stay readable for
     * the whole hook). Every other page is read on a moving camera. */
    var scroll = s.archetype === "doc_title" ? 0 : SCROLL_PX_PER_S;
    var cam = "translateY(" + fmt((1 - enter) * 12 - scroll * u, 1) + "px) scale(" + fmt(breath, 4) + ")";
    s._cam.style.transform = cam;
    s._rules.style.transform = cam;
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
  };

  build();
})();


