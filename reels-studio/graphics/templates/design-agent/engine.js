/* pulse: a measurement scope on a scrolling perspective grid.
 * Pure function of setTime(t). No timers, no CSS transitions.
 * Two accents only: cyan for the winner, magenta for the challenger.
 */
(function () {
  "use strict";
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var GROUND = "#0A0B12", DEEP = "#12141F", PANEL = "#171A28", EDGE = "#2B3050",
      INK = "#EDF0FF", MUTED = "#7D86AE", CYAN = "#35E7F2", MAGENTA = "#FF3D8A", AMBER = "#FFC24B";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var eCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var eExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var eBack = function (x) { x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
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

  // Resolve multi-word narration cues against contiguous aligned tokens. A missing cue falls
  // back to an explicit stagger; it must never match an unrelated concatenated word.
  function bindTimes(phrases, s, n) {
    return window.HouseMotion.cueTimes(phrases, s, n, {});
  }

  /* the ground: scrolling perspective grid + a soft horizon glow */
  function ground(root, phase) {
    var g = svg(1080, 1920, root, "pl-ground");
    g.setAttribute("viewBox", "-40 -40 1160 2000");   // overscan for the camera drift
    g.setAttribute("preserveAspectRatio", "none");
    g.style.width = "1080px"; g.style.height = "1920px";
    g.style.overflow = "hidden";
    var horizon = 1180;
    for (var i = 0; i < 26; i++) {           /* vertical stays converge on the vanishing point */
      var x = -540 + i * 84;
      sEl("line", { x1: 540 + (x - 540) * 0.12, y1: horizon, x2: x, y2: 1920,
                    stroke: EDGE, "stroke-width": 1.4, opacity: 0.55 }, g);
    }
    var horizonLines = [];
    for (var k = 0; k < 22; k++) {           /* horizontals creep toward the viewer */
      var f = ((k / 22) + phase) % 1;
      var y = horizon + Math.pow(f, 2.4) * (1920 - horizon);
      horizonLines.push(sEl("line", { x1: 0, y1: y, x2: 1080, y2: y, stroke: EDGE,
                    "stroke-width": 1 + f * 1.6, opacity: 0.14 + f * 0.5 }, g));
    }
    var hz = sEl("line", { x1: 0, y1: horizon, x2: 1080, y2: horizon, stroke: CYAN,
                           "stroke-width": 2, opacity: 0.35 }, g);
    /* motion contract: a beat never sits still. The camera drifts and the horizon breathes, so
       even a beat whose content has finished settling still moves on every frame. */
    g._hz = hz;
    g._tick = function (t) {
      var ph = t * 0.11;
      horizonLines.forEach(function (line, i) {
        var f = ((i / horizonLines.length) + phase + t * .055) % 1;
        var y = horizon + Math.pow(f, 2.4) * (1920 - horizon);
        line.setAttribute("y1", y.toFixed(1)); line.setAttribute("y2", y.toFixed(1));
      });
      var sink = 2.5 + 2.5 * Math.sin(t * 0.7);      // slow push-in, never a still frame
      g.setAttribute("transform", "translate(540,1180) scale(" +
        (1.0015 + 0.0015 * Math.sin(t * 0.7)).toFixed(5) + ") translate(-540,-1180) translate(0," +
        (Math.sin(ph) * 4 + sink).toFixed(2) + ")");
      hz.setAttribute("y1", (1180 + Math.sin(ph * 1.3) * 26).toFixed(1));
      hz.setAttribute("y2", hz.getAttribute("y1"));
    };
    return g;
  }

  var ARCH = {};

  /* title_burst: the hook. Kicker, a title that unclips, chips that snap in. */
  ARCH.title_burst = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.0);
      var wrap = el("div", "pl-titlewrap", root);
      el("div", "pl-kicker", wrap, p.kicker || "");
      r.title = el("div", "pl-title", wrap);
      r.titleWords = String(s.headline || p.title || "").split(/\s+/).map(function (word) {
        var part = el("span", "pl-title-word", r.title, word);
        r.title.appendChild(document.createTextNode(" "));
        return part;
      });
      r.chips = (p.chips || []).map(function (t) {
        return el("div", "pl-chip", wrap, t);
      });
      var mock=el("div","da-hook-mock",wrap);el("div","da-hook-kicker",mock,"A REQUEST · ILLUSTRATION");el("div","da-hook-prompt",mock,"Make a launch video\nin our brand.");
      return r;
    },
    update: function (r, s, u, d) {
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.5)));
      r.title.style.opacity = fmt(ramp(u, 0.06, 0.3));
      /* a clip-path style wipe: scale + blur-free slide */
      r.title.style.transform = "translateY(" + fmt((1 - eExpo(ramp(u, 0.06, 0.55))) * 40, 1) + "px)";
      r.titleWords.forEach(function (word, i) {
        var k = eExpo(ramp(u, 0.02 + i * 0.09, 0.38 + i * 0.09));
        word.style.opacity = fmt(0.45 + 0.55 * k);
        word.style.transform = "translateY(" + fmt((1-k)*22,1) + "px)";
      });
      r.chips.forEach(function (c, i) {
        var k = eBack(ramp(u - 0.45 - i * 0.16, 0, 0.45));
        c.style.opacity = fmt(ramp(u - 0.45 - i * 0.16, 0, 0.2));
        c.style.transform = "translateY(" + fmt((1 - k) * 26, 1) + "px) scale(" + fmt(0.9 + 0.1 * k, 3) + ")";
      });
    }
  };

  /* Brand inputs lead to the three named output types; each fires on speech. */
  ARCH.brand_inputs = {
    build:function(root,s){var p=s.payload||{},r={ground:ground(root,.12)},wrap=el("div","da-brand",root);
      r.inputs=(p.items||[]).map(function(x,i){var card=el("div","da-brand-row",wrap);el("span","da-swatch s"+i,card);el("b",null,card,x);return card;});
      var out=el("div","da-output",wrap);el("div","da-output-label",out,"OUTPUTS · ILLUSTRATION");var rail=el("div","da-output-rail",out);
      r.outputs=(p.outputs||[]).map(function(x){return el("div","da-output-item",rail,x);});
      r.times=bindTimes(p.cue_phrases,s,r.inputs.length+r.outputs.length);return r;},
    update:function(r,s,u,d){r.ground._tick(u+s.t0);r.ground.setAttribute("opacity",fmt(ramp(u,0,.3)));
      r.inputs.concat(r.outputs).forEach(function(node,i){var k=eCubic(ramp(s.t0+u-r.times[i],0,.35));node.style.opacity=fmt(k);node.style.transform="translateY("+fmt((1-k)*18)+"px)";});}
  };
  /* Zero-based chart: only vendor-reported, same unit and same measure. */
  ARCH.proof_chart={
    build:function(root,s){var p=s.payload||{},r={ground:ground(root,.26)},wrap=el("div","da-chart",root);
      r.total=el("div","da-total",wrap,comma(Number(p.assets))+"+ ASSETS");el("div","da-chart-caption",wrap,"MEDIAN MODEL SPEND / REQUEST · USD");
      var before=Number(p.before),after=Number(p.after),max=Math.max(before,after,0.001);
      r.rows=[{label:"MID-SEPTEMBER",value:"$"+before.toFixed(2),frac:before/max},{label:"REPORTED LATER",value:"$"+after.toFixed(2),frac:after/max}].map(function(x){
        var row=el("div","da-chart-row",wrap);el("div","da-chart-name",row,x.label);var tr=el("div","da-chart-track",row),bar=el("div","da-chart-fill",tr);var val=el("div","da-chart-value",row,x.value);return {row:row,bar:bar,frac:x.frac,val:val};});
      el("div","da-source",wrap,"LANGCHAIN'S OWN REPORT · NOT INDEPENDENT");r.times=bindTimes(p.cue_phrases,s,3);return r;},
    update:function(r,s,u,d){var now=s.t0+u;r.ground._tick(now);r.ground.setAttribute("opacity",fmt(ramp(u,0,.3)));
      var n=eCubic(ramp(now-r.times[0],0,.35));r.total.style.opacity=fmt(n);r.total.style.transform="translateY("+fmt((1-n)*15)+"px)";
      r.rows.forEach(function(x,i){var k=eCubic(ramp(now-r.times[i+1],0,.55));x.row.style.opacity=fmt(k);x.bar.style.width=fmt(100*x.frac*k,2)+"%";});}
  };

  /* Three steps are a process diagram, never quantitative bars. */
  ARCH.design_process = {
    build: function(root,s) {
      var p=s.payload||{},r={ground:ground(root,.18)}, wrap=el("div","da-process",root);
      r.items=(p.items||[]).map(function(item,i){
        var row=el("div","da-step",wrap); el("div","da-index",row,"0"+(i+1));
        var txt=el("div","da-step-text",row); el("b",null,txt,item.title); el("span",null,txt,item.sub);
        var line=el("div","da-rule",row); return {row:row,line:line};
      });
      r.times=bindTimes(p.cue_phrases,s,r.items.length);return r;
    },
    update:function(r,s,u,d){
      r.ground._tick(u+s.t0);r.ground.setAttribute("opacity",fmt(ramp(u,0,.3)));
      r.items.forEach(function(item,i){var k=eCubic(ramp(s.t0+u-r.times[i],0,.45));
        item.row.style.opacity=fmt(k); item.row.style.transform="translateX("+fmt((1-k)*38)+"px)";
        item.line.style.transform="scaleX("+fmt(k)+")";
      });
    }
  };
  /* One attributed vendor count. No made-up comparison or scale. */
  ARCH.proof_counter = {
    build:function(root,s){var p=s.payload||{},r={ground:ground(root,.26)},wrap=el("div","da-proof",root);
      el("div","da-proof-label",wrap,p.label);r.num=el("div","da-number",wrap,"—");
      r.note=el("div","da-proof-note",wrap,p.note);r.time=bindTimes(p.cue_phrases,s,1)[0];return r;},
    update:function(r,s,u,d){var q=s.t0+u-r.time,p=s.payload||{},k=eExpo(ramp(q,0,.75));
      r.ground._tick(u+s.t0);r.ground.setAttribute("opacity",fmt(ramp(u,0,.3)));
      r.num.textContent=q<0?"—":comma(Number(p.value||0)*k)+(p.suffix||"");
      r.num.style.transform="translateY("+fmt((1-eCubic(ramp(q,0,.4)))*18)+"px)";
      r.note.style.opacity=fmt(.6+.4*ramp(q,0,.4));
    }
  };

  /* rank_ladder: the blind leaderboard. Bars climb, the winner glows cyan. */
  ARCH.rank_ladder = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.08);
      var wrap = el("div", "pl-ladder", root);
      if (p.badge) el("div", "pl-badge", wrap, p.badge);
      el("div", "pl-chart-label", wrap, "ELO SNAPSHOT · ARTIFICIAL ANALYSIS");
      r.rows = (p.rows || []).map(function (spec) {
        var row = el("div", "pl-rank" + (spec.win ? " win" : ""), wrap);
        el("div", "pos", row, String(spec.pos || ""));
        var mid = el("div", "mid", row);
        el("b", null, mid, spec.name || "");
        var track = el("i", "track", mid);
        var fill = el("u", null, track);
        var value = el("em", null, row, spec.val || "");
        return { row: row, fill: fill, value: value, label: spec.val || "", score: spec.score === undefined ? 0 : spec.score };
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.4)));
      r.rows.forEach(function (x, i) {
        var p = eCubic(ramp(now - r.times[i], 0, 0.45));
        x.row.style.opacity = fmt(0.28 + 0.72 * p);
        x.row.style.transform = "translateX(" + fmt((1 - p) * 46, 1) + "px)";
        x.fill.style.width = fmt(x.score * eExpo(ramp(now - r.times[i], 0.05, 0.7)) * 100, 1) + "%";
        x.value.textContent = x.label;
      });
    }
  };

  /* versus_split: two panels, vendor claim against the independent measurement. */
  ARCH.versus_split = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.16);
      var wrap = el("div", "pl-vs", root);
      if (p.tag) el("div", "pl-vstag", wrap, p.tag);
      var row = el("div", "pl-vsrow", wrap);
      function panel(side, cls) {
        var box = el("div", "pl-vspanel " + cls, row);
        el("div", "who", box, side.who || "");
        el("div", "big", box, side.big || "");
        if (side.sub) el("div", "sub", box, side.sub);
        return box;
      }
      r.left = panel(p.left || {}, "l");
      r.right = panel(p.right || {}, "r");
      r.mid = el("div", "pl-vsmid", row, "OR");
      row.insertBefore(r.mid, r.right); // the connector belongs BETWEEN the two choices
      r.times = bindTimes(p.cue_phrases, s, 2);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.4)));
      [[r.left, 0], [r.right, 1]].forEach(function (pair) {
        var box = pair[0];
        var k = eCubic(ramp(now - r.times[pair[1]], 0, 0.45));
        box.style.opacity = fmt(k);
        box.style.transform = "translateY(" + fmt((1 - k) * 30, 1) + "px)";
      });
      var mk = eBack(ramp(u - 0.8, 0, 0.4));
      r.mid.style.opacity = fmt(ramp(u - 0.8, 0, 0.2));
      r.mid.style.transform = "scale(" + fmt(0.7 + 0.3 * mk, 3) + ")";
    }
  };

  /* spec_plates: what you actually get, as instrument readouts. */
  ARCH.spec_plates = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.24);
      var wrap = el("div", "pl-plates", root);
      r.plates = (p.plates || []).map(function (spec, i) {
        var card = el("div", "pl-plate" + (i === 0 ? " lead" : ""), wrap);
        el("div", "k", card, spec.k || "");
        el("div", "v", card, spec.v || "");
        if (spec.s) el("div", "s", card, spec.s || "");
        return card;
      });
      r.times = bindTimes(p.cue_phrases, s, r.plates.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.4)));
      r.plates.forEach(function (card, i) {
        var k = eBack(ramp(now - r.times[i], 0, 0.5));
        card.style.opacity = fmt(ramp(now - r.times[i], 0, 0.22));
        card.style.transform = "translateY(" + fmt((1 - k) * 34, 1) + "px)";
      });
    }
  };

  /* sonar_scan: the arena measured. A sweep runs, then the Elo lands. */
  ARCH.sonar_scan = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.32);
      var wrap = el("div", "pl-sonar", root);
      var g = svg(880, 880, wrap, "pl-scope");
      r.rings = [];
      for (var i = 1; i <= 5; i++) {
        r.rings.push(sEl("circle", { cx: 440, cy: 440, r: i * 82, fill: "none",
                                     stroke: EDGE, "stroke-width": 2 }, g));
      }
      r.arc = sEl("path", { fill: "none", stroke: CYAN, "stroke-width": 6, "stroke-linecap": "round" }, g);
      r.sweep = sEl("line", { x1:440, y1:440, x2:440, y2:30, stroke:CYAN, "stroke-width":4, opacity:0.8 }, g);
      r.dot = sEl("circle", { cx: 440, cy: 440, r: 12, fill: MAGENTA, opacity: 0 }, g);
      r.value = el("div", "pl-sonarval", wrap);
      if (p.found) r.found = el("div", "pl-sonarfound", wrap, p.found);
      r.tick = el("div", "pl-sonartick", wrap);
      return r;
    },
    update: function (r, s, u, d) {
      var p = s.payload || {};
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.4)));
      var theta = u * 1.45 - Math.PI / 2;
      r.sweep.setAttribute("x2", fmt(440 + Math.cos(theta)*410,1));
      r.sweep.setAttribute("y2", fmt(440 + Math.sin(theta)*410,1));
      var done = ramp(u, 0.15, d * 0.8);
      var a0 = -Math.PI / 2, a1 = a0 + done * Math.PI * 2;
      var large = done > 0.5 ? 1 : 0;
      r.arc.setAttribute("d", "M 440 440 L " + fmt(440 + Math.cos(a0) * 410, 1) + " " + fmt(440 + Math.sin(a0) * 410, 1) +
                              " A 410 410 0 " + large + " 1 " + fmt(440 + Math.cos(a1) * 410, 1) + " " +
                              fmt(440 + Math.sin(a1) * 410, 1) + " Z");
      r.arc.setAttribute("opacity", fmt(0.5 * (1 - done * 0.7)));
      var secl = eExpo(ramp(u, 0.15, d * 0.8)) * (p.seconds || 4);
      r.tick.textContent = "SCANNING " + secl.toFixed(1) + " s";
      var pop = eBack(ramp(u, d * 0.55, d * 0.85));
      if (r.found) r.found.style.opacity = fmt(ramp(u, d * 0.5, d * 0.7));
      r.dot.setAttribute("opacity", fmt(ramp(u, d * 0.5, d * 0.65)));
      r.value.style.opacity = fmt(ramp(u, d * 0.5, d * 0.72));
      r.value.style.transform = "scale(" + fmt(0.86 + 0.14 * pop, 3) + ")";
      r.value.textContent = p.value || "";
    }
  };

  /* verdict_stack: a narrow check-list verdict. Deliberately not a split panel, so the
     honesty beat reads as a different instrument from the pricing beat. */
  ARCH.verdict_stack = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      r.ground = ground(root, 0.36);
      var wrap = el("div", "pl-verdict", root);
      if (p.tag) el("div", "pl-vtag", wrap, p.tag);
      r.rows = (p.rows || []).map(function (spec) {
        var row = el("div", "pl-vrow " + (spec.kind || "ok"), wrap);
        el("div", "mark", row, spec.kind === "warn" ? "!" : "\u2713");
        var mid = el("div", "mid", row);
        el("b", null, mid, spec.t || "");
        el("s", null, mid, spec.sub || "");
        el("em", null, row, spec.v || "");
        return row;
      });
      r.times = bindTimes(p.cue_phrases, s, r.rows.length);
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      if (r.ground && r.ground._tick) r.ground._tick(u + s.t0);
      r.ground.setAttribute("opacity", fmt(ramp(u, 0, 0.4)));
      r.rows.forEach(function (row, i) {
        var k = eCubic(ramp(now - r.times[i], 0, 0.4));
        row.style.opacity = fmt(k);
        row.style.transform = "translateY(" + fmt((1 - k) * 26, 1) + "px)";
      });
    }
  };

  /* endcard */
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
    el("div", "pl-head", stageEl, D.handle || "");
    D.scenes.forEach(function (s, si) {
      s.idx = si;
      var wrap = el("div", "scene", stageEl);
      wrap.setAttribute("data-scene", s.id);   // house layer mounts the house outro here
      wrap.style.display = "none";
      var visual = el("div", "visual", wrap);
      if (s.archetype !== "endcard" && s.archetype !== "title_burst") el("div", "pl-scene-heading", visual, s.headline || "");
      s._wrap = wrap; s._visual = visual;
      s._refs = ARCH[s.archetype].build(visual, s);
    });
    capEl = el("div", "pl-caption", stageEl);
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
      if (j === cur) {
        var k = eCubic(ramp(t - words[j][1], 0, 0.16));
        w.style.transform = "translateY(" + fmt((1 - k) * 8, 1) + "px)";
      }
    }
  }

  window.setTime = function (t) {
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    // House layer owns the outro; hide the entire template scene.
    if (s.archetype === "endcard") { D.scenes.forEach(function (x) { x._wrap.style.display = "none"; }); return; }
    // A short, deterministic entrance gives a scene change direction without a blank frame.
    var local = Math.max(0, t - s.t0), enter = eCubic(ramp(local, 0, 0.28));
    s._visual.style.opacity = fmt(0.7 + 0.3 * enter);
    s._visual.style.transform = "translateY(" + fmt((1 - enter) * 16, 1) + "px)";
    ARCH[s.archetype].update(s._refs, s, local, Math.max(1e-6, s.t1 - s.t0));
    drawCaption(s, t);
  };

  build();
})();
