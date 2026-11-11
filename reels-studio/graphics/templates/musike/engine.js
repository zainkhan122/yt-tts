/* musike engine v2 — the player never leaves the frame (owner verdict: scenes without the
 * interface around them read as text cards). Pure function of t; GSAP vendored = easing curves only.
 * window.DATA = {width, height, handle, scenes:[{archetype, t0, t1, headline, payload, words}]}
 */
(function () {
  "use strict";
  var GRAIN_EL = null;
  var D = window.DATA;
  var NS = "http://www.w3.org/2000/svg";
  var GREEN = "#34C759", AMBER = "#FFD60A", MUTE = "#8E96A0", TXT = "#F5F6F7";

  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ramp = function (u, a, b) { return clamp((u - a) / Math.max(1e-6, b - a), 0, 1); };
  var fmt = function (x, n) { return Number(x).toFixed(n === undefined ? 2 : n); };
  var easeOutCubic = function (x) { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  var easeOutExpo = function (x) { x = clamp(x, 0, 1); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
  var easeOutBack = function (x) { x = clamp(x, 0, 1); var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  var easeSpring = easeOutBack, easeSnappy = easeOutBack, easeInOut = easeOutExpo;
  if (window.gsap && window.gsap.parseEase) {
    easeSpring = window.gsap.parseEase("elastic.out(1, 0.55)");
    easeSnappy = window.gsap.parseEase("back.out(2.4)");
    easeInOut = window.gsap.parseEase("power4.inOut");
  }
  var el = function (tag, cls, parent, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  var iconSvg = function (w, h, parent, path, color) {
    var s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 48 48");
    s.setAttribute("width", w); s.setAttribute("height", h);
    var p = document.createElementNS(NS, "path");
    p.setAttribute("d", path); p.setAttribute("fill", "none");
    p.setAttribute("stroke", color || GREEN); p.setAttribute("stroke-width", "3.2");
    p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
    s.appendChild(p); if (parent) parent.appendChild(s);
    return s;
  };
  var ICONS = {
    home: "M8 24 L24 9 L40 24 V40 H28 V30 H20 V40 H8 Z",
    library: "M10 8 H16 V40 H10 Z M22 8 H28 V40 H22 Z M34 8 H40 V40 H34 Z M13 20 H25",
    heart: "M24 41 C12 33 6 26 6 18 C6 11 11 7 16 7 C20 7 23 10 24 13 C25 10 28 7 32 7 C37 7 42 11 42 18 C42 26 36 33 24 41 Z",
    play: "M16 11 L38 24 L16 37 Z",
    monitor: "M6 10 H42 V32 H6 Z M18 38 H30 M24 32 V38",
    phone: "M17 5 H31 V43 H17 Z M21 38.5 H27",
    tv: "M6 12 H42 V34 H6 Z M15 40 H33",
    globe: "M24 5 A19 19 0 1 0 24.01 5 M5 24 H43 M24 5 C15 16 15 32 24 43 C33 32 33 16 24 5",
    docker: "M8 24 H40 V34 C40 38 37 41 33 41 H15 C11 41 8 38 8 34 Z M12 18 H18 V24 H12 Z M20 18 H26 V24 H20 Z M28 18 H34 V24 H28 Z M20 11 H26 V18 H20 Z",
    folder: "M5 12 H19 L23 17 H43 V38 H5 Z",
    download: "M24 8 V30 M15 23 L24 32 L33 23 M10 39 H38",
    file: "M12 6 H30 L38 14 V42 H12 Z M30 6 V14 H38",
    warn: "M24 6 L44 40 H4 Z M24 18 V28 M24 33 V34.5"
  };

  var COVERS = [["#3D5AFE", "#00B8D4"], ["#8E24AA", "#FF5252"], ["#00897B", "#AEEA00"],
                ["#F4511E", "#FFB300"], ["#3949AB", "#40C4FF"], ["#C0CA33", "#00BFA5"]];
  function art(parent, i, cls) {
    var dmix = el("div", "mk-art " + (cls || ""), parent);
    var c = COVERS[i % COVERS.length];
    dmix.style.background = "linear-gradient(135deg, " + c[0] + ", " + c[1] + ")";
    el("div", "vinyl", dmix); el("div", "hole", dmix);
    return dmix;
  }
  function eq(parent, n) {
    var w = el("div", "mk-eq", parent), bars = [];
    for (var i = 0; i < n; i++) bars.push(el("b", "", w));
    return bars;
  }
  function eqDrive(bars, u, speed) {
    for (var i = 0; i < bars.length; i++) {
      var h = 8 + 34 * (0.5 + 0.5 * Math.sin(u * (speed || 7) + i * 1.9)) * (0.6 + 0.4 * Math.sin(u * 2.3 + i));
      bars[i].style.height = fmt(h) + "px";
    }
  }
  function seekBuild(parent, knob) {
    var s = el("div", "mk-seek", parent);
    var f = el("div", "mk-seek-fill", s);
    var k = knob ? el("div", "mk-seek-knob", s) : null;
    return { bar: s, fill: f, knob: k };
  }
  function seekSet(r, p) {
    r.fill.style.width = fmt(p * 100) + "%";
    if (r.knob) r.knob.style.left = fmt(p * 100) + "%";
  }

  /* Musike window: titlebar (+optional status/toggle slot) + sidebar + content pane + now-playing bar.
   * Every scene lives INSIDE this window — the app is always the stage. */
  function playerWindow(parent, opts) {
    opts = opts || {};
    var w = el("div", "mk-win" + (opts.ghosted ? " ghosted" : "") + (opts.slim ? " slim" : ""), parent);
    var bar = el("div", "mk-bar", w);
    el("i", "mk-dot r", bar); el("i", "mk-dot y", bar); el("i", "mk-dot g", bar);
    el("div", "mk-title", bar, "musike");
    var status = null;
    if (opts.status) status = el("div", "mk-status", bar, opts.status);
    var body = el("div", "mk-body", w);
    var side = el("div", "mk-side", body);
    var navs = [];
    [["home", "Home"], ["library", "Library"], ["heart", "Favourites"]].forEach(function (nv, i) {
      var n = el("div", "mk-nav" + (i === 0 ? " on" : ""), side);
      el("i", "pill", n); iconSvg(30, 30, n, ICONS[nv[0]], i === 0 ? GREEN : MUTE);
      n.appendChild(document.createTextNode(nv[1]));
      navs.push(n);
    });
    var pane = el("div", "mk-pane", body);
    if (!opts.empty) {
      pane.className = "mk-pane mk-grid";
      for (var i = 0; i < 6; i++) art(pane, i);
    }
    var np = el("div", "mk-np", w);
    var npArt = el("div", "mk-np-art", np);
    npArt.style.background = "linear-gradient(135deg, #3D5AFE, #00B8D4)";
    var mid = el("div", "mk-np-mid", np);
    var tw = el("div", "mk-np-titlewrap", mid);
    var title = el("div", "mk-np-title", tw, opts.title || "Night Drive — Afterglow Session");
    el("div", "mk-np-sub", mid, opts.sub || "the library · flac");
    var sk = seekBuild(mid, true);
    var bars = eq(np, 5);
    iconSvg(40, 40, el("span", "mk-transport", np), ICONS.play, TXT);
    return { win: w, bar: bar, navs: navs, pane: pane, np: np, npArt: npArt,
             title: title, seek: sk, eq: bars, status: status };
  }

  var ARCH = {};

  /* ---- hook: the player IS the frame; title scrolls; seek, EQ and chips move ---- */
  ARCH.player_hook = {
    build: function (root, s) {
      var r = playerWindow(root, { title: (s.payload && s.payload.track) || "Night Drive — Afterglow Session", status: "LIVE" });
      r.chips = el("div", "", root);
      r.chips.innerHTML = "<span class='mk-chip'>NO ADS</span> <span class='mk-chip'>NO ACCOUNT</span> <span class='mk-chip amber'>FREE + MIT</span>";
      r.chips.style.cssText = "display:flex;gap:18px;margin-top:38px;";
      return r;
    },
    update: function (r, s, u, d) {
      seekSet(r.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.eq, u, 8);
      r.title.style.transform = "translateX(" + fmt(-((u * 70) % 520)) + "px)";
      var pop = easeSpring(ramp(u, 0, 0.5));
      r.win.style.transform = "translateY(" + fmt((1 - pop) * 40) + "px) scale(" + fmt(0.97 + 0.03 * pop) + ")";
      r.win.style.boxShadow = "0 30px 80px rgba(0,0,0,0.55), 0 0 " + fmt(40 + 30 * (0.5 + 0.5 * Math.sin(u * 2.1))) + "px rgba(52,199,89," + fmt(0.10 + 0.07 * ramp(u, 1.2, 2.2)) + ")";
      r.navs[0].querySelector(".pill").style.opacity = fmt(easeSnappy(ramp(u, 0.7, 1.1)));
      r.chips.style.opacity = fmt(ramp(u, 1.1, 1.7));
      r.chips.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(u, 1.1, 1.7))) * 26) + "px)";
      if (r.status) r.status.style.opacity = fmt(0.55 + 0.45 * (0.5 + 0.5 * Math.sin(u * 3.2)));
    }
  };

  /* ---- point 1: the flow runs INSIDE the app; packets feed the now-playing tile ---- */
  ARCH.server_stream = {
    build: function (root, s) {
      var r = playerWindow(root, { empty: true, status: "fetching…", sub: "yt-dlp · your server" });
      var pane = r.pane;
      pane.style.position = "relative";
      var f = el("div", "mk-flow-pane", pane);
      var mk = function (x, y, lab, tiny, ic, col) {
        var n = el("div", "mk-node sm", f);
        n.style.left = x + "px"; n.style.top = y + "px";
        iconSvg(64, 64, n, ic, col || GREEN);
        el("div", "lab", n, lab); el("div", "tiny", n, tiny);
        return n;
      };
      r.src = mk(36, 120, "SOURCE", "streams online", ICONS.globe, MUTE);
      r.srv = mk(268, 30, "YOUR SERVER", "yt-dlp fetches", ICONS.download, AMBER);
      r.tgt = mk(494, 120, "THIS WINDOW", "plays them", ICONS.play, GREEN);
      var edge = function (x0, y0, x1, y1) {
        var e = el("div", "mk-edge", f);
        var dx = x1 - x0, dy = y1 - y0;
        e.style.left = x0 + "px"; e.style.top = y0 + "px";
        e.style.width = fmt(Math.sqrt(dx * dx + dy * dy)) + "px";
        e.style.transform = "rotate(" + fmt(Math.atan2(dy, dx) * 180 / Math.PI) + "deg)";
        e.style.transformOrigin = "0 50%";
        return { x0: x0, y0: y0, x1: x1, y1: y1 };
      };
      r.edges = [edge(196, 200, 244, 152), edge(428, 152, 470, 200)];
      r.packets = [];
      for (var i = 0; i < 6; i++) r.packets.push(el("div", "mk-packet" + (i % 2 ? " b" : ""), f));
      r.arts = [];
      for (var g = 0; g < 3; g++) { var a = art(r.pane, g + 3); a.style.width = "130px"; a.style.marginTop = "8px"; r.arts.push(a); }
      return r;
    },
    update: function (r, s, u, d) {
      seekSet(r.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.eq, u, 8);
      r.title.style.transform = "translateX(" + fmt(-((u * 55) % 520)) + "px)";
      [r.src, r.srv, r.tgt].forEach(function (n, i) {
        var k = easeSnappy(ramp(u, 0.12 * i, 0.12 * i + 0.45));
        n.style.opacity = fmt(k);
        n.style.transform = "scale(" + fmt(0.85 + 0.15 * k) + ")";
      });
      r.srv.style.borderColor = "rgba(255,214,10," + fmt(0.35 + 0.45 * (0.5 + 0.5 * Math.sin(u * 3))) + ")";
      if (r.status) r.status.style.opacity = fmt(0.45 + 0.55 * (0.5 + 0.5 * Math.sin(u * 4.4)));
      for (var i = 0; i < r.packets.length; i++) {
        var e = r.edges[i % 2], ph = (u * 0.6 + (i * 0.31)) % 1, vis = ramp(u, 0.55, 0.95);
        r.packets[i].style.transform = "translate(" + fmt(e.x0 + (e.x1 - e.x0) * ph) + "px," + fmt(e.y0 + (e.y1 - e.y0) * ph) + "px)";
        r.packets[i].style.opacity = fmt(vis);
      }
      r.arts.forEach(function (a, i) {
        var k = ramp(u, 1.0 + i * 0.35, 1.4 + i * 0.35);   // art tiles "arrive" as packets land
        a.style.opacity = fmt(k);
        a.style.transform = "scale(" + fmt(0.9 + 0.1 * easeSnappy(k)) + ")";
      });
    }
  };

  /* ---- point 2: audio flips to video INSIDE the player; the seek never restarts ---- */
  ARCH.av_toggle = {
    build: function (root, s) {
      var r = playerWindow(root, { empty: true, slim: true, sub: "one clock, both modes" });
      r.toggle = el("div", "mk-toggle sm", r.bar);
      r.thumb = el("div", "mk-thumb sm", r.toggle);
      r.optA = el("div", "mk-topt", r.toggle, "AUDIO");
      r.optV = el("div", "mk-topt", r.toggle, "VIDEO");
      r.stage = el("div", "mk-stage sm", r.pane);
      r.waves = el("div", "mk-waves", r.stage);
      r.bars = [];
      for (var i = 0; i < 34; i++) r.bars.push(el("b", "", r.waves));
      r.video = el("div", "mk-video", r.stage);
      el("div", "playglyph", r.video);
      r.shim = el("div", "shimmer", r.video);
      r.bigArt = el("div", "mk-bigart", r.stage);
      r.bigArt.style.background = "linear-gradient(135deg, #3D5AFE, #00B8D4)";
      return r;
    },
    update: function (r, s, u, d) {
      var flipAt = clamp(1.3, d * 0.15, d * 0.4);
      var f = easeSpring(ramp(u, flipAt, flipAt + 0.7));
      r.thumb.style.left = fmt(6 + f * (360 - 172 - 12)) + "px";
      r.optA.style.color = f < 0.5 ? "#F5F6F7" : MUTE;
      r.optV.style.color = f >= 0.5 ? "#F5F6F7" : MUTE;
      r.waves.style.opacity = fmt(1 - ramp(f, 0.25, 0.65));
      r.bigArt.style.opacity = fmt(0.5 * (1 - ramp(f, 0.2, 0.6)));
      r.video.style.opacity = fmt(ramp(f, 0.35, 0.8));
      for (var i = 0; i < r.bars.length; i++) {
        var h = 18 + 96 * Math.abs(Math.sin(i * 0.55 + u * 5.2)) * (0.5 + 0.5 * Math.sin(i * 1.3 + 2));
        r.bars[i].style.height = fmt(h) + "px";
      }
      r.shim.style.transform = "translateX(" + fmt(((u * 340) % 950) - 140) + "px)";
      seekSet(r.seek, clamp(u / Math.max(1, d), 0, 1));   // same clock, both ways
      eqDrive(r.eq, u, 8);
      r.title.style.transform = "translateX(" + fmt(-((u * 55) % 520)) + "px)";
      r.np.style.boxShadow = "0 0 " + fmt(24 + 26 * f) + "px rgba(52,199,89," + fmt(0.10 + 0.12 * f) + ")";
    }
  };

  /* ---- point 3: one player, six screens — the player stays on top, tiles spring in ---- */
  ARCH.platform_grid = {
    build: function (root, s) {
      var r = {};
      r.mini = playerWindow(root, { empty: true, slim: true, sub: "the same build everywhere" });
      r.mini.win.className += " strip";
      r.pane = r.mini.pane;
      var strip = el("div", "mk-now-strip", r.pane);
      strip.innerHTML = "";
      var sa = el("div", "mk-np-art", strip); sa.style.background = "linear-gradient(135deg, #F4511E, #FFB300)";
      el("div", "strip-title", strip, "Night Drive — Afterglow Session");
      r.stripSeek = seekBuild(strip, false);
      r.stripEq = eq(strip, 4);
      r.grid = el("div", "mk-plats six", r.pane);
      r.tiles = [];
      [["monitor", "DESKTOP"], ["globe", "BROWSER PWA"], ["phone", "ANDROID + iPHONE"],
       ["tv", "ANDROID TV"], ["docker", "DOCKER"], ["file", "WIN · MAC · LINUX"]].forEach(function (pv) {
        var t = el("div", "mk-plat", r.grid);
        el("div", "gl", t).appendChild(iconSvg(84, 84, null, ICONS[pv[0]], pv[0] === "docker" ? AMBER : GREEN));
        el("div", "nm", t, pv[1]);
        var ms = el("div", "miniseek", t); el("i", "", ms);
        r.tiles.push(t);
      });
      return r;
    },
    update: function (r, s, u, d) {
      var head = easeSpring(ramp(u, 0, 0.45));
      r.mini.win.style.opacity = fmt(head);
      r.mini.win.style.transform = "translateY(" + fmt((1 - head) * 30) + "px)";
      seekSet(r.mini.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.mini.eq, u, 8);
      seekSet(r.stripSeek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.stripEq, u, 8);
      r.tiles.forEach(function (t, i) {
        var k = easeSnappy(ramp(u, 0.5 + 0.16 * i, 1.0 + 0.16 * i));
        t.style.opacity = fmt(k);
        t.style.transform = "translateY(" + fmt((1 - k) * 46) + "px) scale(" + fmt(0.9 + 0.1 * k) + ")";
        t.querySelector(".miniseek i").style.width = fmt(30 + 40 * (0.5 + 0.5 * Math.sin(u * 2 + i))) + "%";
      });
    }
  };

  /* ---- point 4: the JSON floats over YOUR player — the file belongs to the app ---- */
  ARCH.library_file = {
    build: function (root, s) {
      var r = { ghost: playerWindow(root, { ghosted: true }) };
      r.file = el("div", "mk-file", root);
      var bar = el("div", "mk-bar", r.file);
      el("i", "mk-dot r", bar); el("i", "mk-dot y", bar); el("i", "mk-dot g", bar);
      el("div", "mk-title", bar, "library.json");
      r.lines = el("div", "mk-flines", r.file);
      r.spanEls = [];
      ["<span class='k'>\"favourites\"</span>: [",
       "  <span class='s'>\"Afterglow — Night Drive\"</span>,",
       "  <span class='s'>\"Lo-Fi Study Mix, Vol. 4\"</span>,",
       "  <span class='s'>\"Live at Red Rocks, 2003\"</span>",
       "]",
       "<span class='d'>// yours. copy it anywhere.</span>"].forEach(function (html) {
        var sp = el("div", "", r.lines); sp.innerHTML = html;
        r.spanEls.push(sp);
      });
      r.caret = el("span", "mk-caret", r.lines);
      r.exportChip = el("div", "mk-export", root);
      r.exportChip.innerHTML = "<span class='mk-chip'>⇩ export · move to any musike</span>";
      return r;
    },
    update: function (r, s, u, d) {
      seekSet(r.ghost.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.ghost.eq, u, 6);
      r.spanEls.forEach(function (sp, i) {
        var k = ramp(u, 0.2 + i * 0.5, 0.4 + i * 0.5);
        sp.style.opacity = fmt(k);
        sp.style.transform = "translateX(" + fmt((1 - easeOutCubic(k)) * 30) + "px)";
      });
      r.caret.style.opacity = fmt(0.4 + 0.6 * (0.5 + 0.5 * Math.sin(u * 6)));
      var e = easeSnappy(ramp(u, d * 0.72, d * 0.72 + 0.5));
      r.exportChip.style.opacity = fmt(e);
      r.exportChip.style.transform = "translateY(" + fmt((1 - e) * 30) + "px)";
    }
  };

  /* ---- the catch: README card over the running player ---- */
  ARCH.honesty_card = {
    build: function (root, s) {
      var r = { ghost: playerWindow(root, { ghosted: true }) };
      r.doc = el("div", "mk-doc", root);
      var bar = el("div", "mk-bar", r.doc);
      el("i", "mk-dot r", bar); el("i", "mk-dot y", bar); el("i", "mk-dot g", bar);
      el("div", "mk-title", bar, "README.md");
      r.warn = el("div", "mk-warn", r.doc);
      iconSvg(44, 44, r.warn, ICONS.warn, AMBER);
      r.warn.appendChild(document.createTextNode("Personal and educational use only."));
      r.bullets = el("div", "mk-bullets", r.doc);
      r.rowEls = [];
      (s.payload && s.payload.bullets || [
        "YouTube's terms forbid ad-free streams like this",
        "Public bots Groovy and Rythm were shut down",
        "Run your own — quietly, for yourself"
      ]).forEach(function (b) {
        var row = el("div", "mk-bullet", r.bullets);
        el("i", "sq", row); row.appendChild(document.createTextNode(b));
        r.rowEls.push(row);
      });
      return r;
    },
    update: function (r, s, u, d) {
      seekSet(r.ghost.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.ghost.eq, u, 6);
      var w = easeSnappy(ramp(u, 0, 0.5));
      r.warn.style.opacity = fmt(w);
      r.warn.style.transform = "scale(" + fmt(0.94 + 0.06 * w) + ")";
      r.warn.style.boxShadow = "0 0 " + fmt(18 + 14 * (0.5 + 0.5 * Math.sin(u * 2.4))) + "px rgba(255,214,10,0.12)";
      r.rowEls.forEach(function (row, i) {
        var k = ramp(u, 0.5 + i * 0.55, 0.9 + i * 0.55);
        row.style.opacity = fmt(k);
        row.style.transform = "translateX(" + fmt((1 - easeOutCubic(k)) * 34) + "px)";
      });
    }
  };

  /* ---- endcard: the player stays on screen; CTA breathes ---- */
  ARCH.endcard = {
    build: function (root, s) {
      var r = { ghost: playerWindow(root, { ghosted: true, title: "…and nothing left to sell you." }) };
      r.end = el("div", "mk-end", root);
      r.ring = el("div", "mk-ring", r.end);
      r.cta = el("div", "mk-cta", r.end, "COMMENT “MUSIKE”");
      r.repo = el("div", "mk-repochip", r.end);
      r.repo.innerHTML = "<span class='mk-chip amber'>github · musike · MIT</span>";
      r.sub = el("div", "end-sub", r.end, "run your own music player — link pinned");
      return r;
    },
    update: function (r, s, u, d) {
      seekSet(r.ghost.seek, clamp(u / Math.max(1, d), 0, 1));
      eqDrive(r.ghost.eq, u, 6);
      var k = easeSpring(ramp(u, 0, 0.6));
      r.cta.style.opacity = fmt(k);
      r.cta.style.transform = "scale(" + fmt(0.9 + 0.1 * k) + ")";
      var pulse = 0.5 + 0.5 * Math.sin(u * 2.6);
      r.cta.style.boxShadow = "0 16px 44px rgba(52,199,89," + fmt(0.30 + 0.18 * pulse) + ")";
      var rr = ramp(u, 0.3, 1.1) * (1 - ramp(u, 1.4, 2.0));
      r.ring.style.opacity = fmt(rr);
      r.ring.style.transform = "scale(" + fmt(0.85 + 0.35 * easeOutCubic(ramp(u, 0.3, 1.2)), 3) + ")";
      r.repo.style.opacity = fmt(ramp(u, 0.8, 1.3));
      r.sub.style.opacity = fmt(ramp(u, 1.1, 1.7));
    }
  };

  /* ---------- stage ---------- */
  var stageEl, glowEl, capEl, handleEl;
  function build() {
    stageEl = document.getElementById("stage");
    glowEl = el("div", "", stageEl); glowEl.id = "ambglow";
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
    var start = Math.max(0, Math.min(cur, words.length - 4));
    var end = Math.min(words.length, start + 4);
    capEl.innerHTML = "";
    for (var j = start; j < end; j++) {
      var on = j === cur;
      var w = el("span", on ? "cw cw-on" : "cw", capEl, words[j][0]);
      if (on) {
        var k = easeSnappy(ramp(t - words[j][1], 0, 0.16));
        w.style.transform = "scale(" + fmt(1.14 - 0.14 * k, 3) + ")";
      }
    }
  }
  window.setTime = function (t) {
    var g = GRAIN_EL || (GRAIN_EL = document.querySelector("#postfx .grain"));
    if (g) { var fi = Math.round(t * 30); g.style.backgroundPosition = ((fi * 41) % 211) + "px " + ((fi * 97) % 173) + "px"; }
    var k = activeIndex(t);
    D.scenes.forEach(function (s, i) { s._wrap.style.display = i === k ? "block" : "none"; });
    var s = D.scenes[k];
    var u = t - s.t0, d = Math.max(1e-6, s.t1 - s.t0);
    var fade = Math.min(ramp(u, 0, 0.18), ramp(d - u, 0, 0.16));
    s._head.style.opacity = fmt(fade);
    s._head.style.transform = "translateY(" + fmt((1 - easeOutCubic(ramp(u, 0, 0.3))) * 30) + "px)";
    s._visual.style.opacity = fmt(fade);
    s._visual.style.transform = "scale(" + fmt(0.965 + 0.035 * easeOutCubic(ramp(u, 0, 0.3)), 4) + ")";
    ARCH[s.archetype].update(s._refs, s, u, d);
    drawCaption(s, t);
    glowEl.style.transform = "translate(" + fmt(Math.sin(t * 0.19) * 150, 1) + "px," + fmt(Math.cos(t * 0.16) * 200, 1) + "px)";
  };
  build();
})();
