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
    var sub;
    if (spec.shape === "sneaker" && D.vendor_url) {
      var im = el("img", "ph-img", st);
      im.src = D.vendor_url + "/sneaker-photo.jpg";
      sub = el("div", "ph-subject sh-sneaker", st);
      sub.style.display = "none";
    } else {
      sub = el("div", "ph-subject" + (spec.shape ? " sh-" + spec.shape : ""), st);
    }
    if (spec.shape === "sneaker") {
      el("div", "sn-upper", sub);
      el("div", "sn-collar", sub);
      el("div", "sn-ankle", sub);
      el("div", "sn-sole", sub);
      var laces = el("div", "sn-laces", sub);
      el("i", null, laces); el("i", null, laces); el("i", null, laces);
    } else {
      el("div", "core", sub);
      if (spec.handle !== false) el("div", "wing", sub);
    }
    el("div", "glowring", sub);
    el("div", "ph-cap", body, spec.caption || "one picture · flat 2D");
    return ph;
  }

  /* dots that ARE the object: silhouette-shaped Gaussian cloud, shaded like the photo (lit top, dark sole).
     kind: "sneaker" | "mug". Returns [{x,y,f}] with f = 0 (top/lit) .. 1 (bottom/shadow). */
  function shapeDots(kind, rnd, cx, cy, W, H, n) {
    var parts;
    if (kind === "sneaker") {
      parts = [
        { dx: -0.20, dy: 0.09, rx: 0.30 * W, ry: 0.105 * H, w: 0.52 },   /* body   */
        { dx: -0.36, dy: 0.10, rx: 0.055 * W, ry: 0.085 * H, w: 0.12 },  /* toe cap */
        { dx: 0.185, dy: -0.05, rx: 0.078 * W, ry: 0.145 * H, w: 0.14 }, /* collar/heel */
        { dx: 0.245, dy: -0.21, rx: 0.052 * W, ry: 0.075 * H, w: 0.08 }, /* ankle tower */
        { strip: true, w: 0.14 }                                          /* dense sole line */
      ];
    } else {                                                              /* mug */
      parts = [
        { dx: -0.02, dy: 0.02, rx: 0.235 * W, ry: 0.26 * H, w: 0.80 },
        { ring: true, dx: 0.29, dy: 0.02, r: 0.125 * W, w: 0.20 }        /* handle */
      ];
    }
    var tot = 0; parts.forEach(function (p) { tot += p.w; });
    var out = [];
    for (var i = 0; i < n; i++) {
      var pick = rnd() * tot, p = parts[0], a = 0;
      for (var j = 0; j < parts.length; j++) { if (pick < (a += parts[j].w)) { p = parts[j]; break; } }
      var x, y;
      if (p.strip) {
        x = cx + (-0.335 + rnd() * 0.67) * W; y = cy + (0.175 + (rnd() - 0.5) * 0.03) * H;
      } else if (p.ring) {
        var th = (-68 + rnd() * 136) * Math.PI / 180;
        x = cx + p.dx * W + Math.cos(th) * p.r; y = cy + p.dy * H + Math.sin(th) * p.r * 0.92;
      } else {
        var rr = Math.sqrt(rnd()), th2 = rnd() * 6.2832;
        x = cx + p.dx * W + Math.cos(th2) * p.rx * rr; y = cy + p.dy * H + Math.sin(th2) * p.ry * rr;
      }
      out.push({ x: x, y: y, f: clamp((y - (cy - 0.3 * H)) / (0.62 * H), 0, 1) });
    }
    return out;
  }

  var LIT = [239, 233, 220], SHADE = [122, 117, 102];      /* the mug/sneaker's lit→shadow tones */
  function dotColor(f, rnd) {
    if (rnd() < 0.16) return rnd() < 0.5 ? ACC : ACC2;      /* sparse violet/cyan = still a splat */
    var r = Math.round(LIT[0] + (SHADE[0] - LIT[0]) * f),
        g = Math.round(LIT[1] + (SHADE[1] - LIT[1]) * f),
        b = Math.round(LIT[2] + (SHADE[2] - LIT[2]) * f);
    return "rgb(" + r + "," + g + "," + b + ")";
  }

  function splatCard(spec, seed) {
    spec = spec || {};
    var sp = el("div", "sp");
    var bar = el("div", "sp-bar", sp);
    el("i", null, bar); el("i", null, bar); el("i", null, bar);
    el("div", "sp-name", bar, spec.name || "object.ply");
    var cnt = spec.count === undefined ? "1,048,576 GAUSSIANS" : spec.count;
    if (cnt) el("div", "sp-count", sp, cnt);
    var rnd = PRNG(seed || 1);
    var box = spec.compact ? { x: 30, y: 68, w: 396, h: 388 } : { x: 60, y: 130, w: 840, h: 760 };
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
    var n = spec.dots || (spec.shape ? 620 : 380);
    var shaped = spec.shape ? shapeDots(spec.shape, rnd, cx, cy, box.w, box.h, n) : null;
    for (var i = 0; i < n; i++) {
      var bx, by, col, dsz;
      if (shaped) {
        bx = shaped[i].x; by = shaped[i].y;
        col = dotColor(shaped[i].f, rnd);
        dsz = 1.8 + rnd() * 3.4;
      } else {
        var ang = rnd() * 6.2832;
        var mag = Math.abs(rnd() + rnd() - 1);                       // dense core, thin rim
        var wing = rnd() < 0.22;
        bx = wing ? cx + box.w * 0.20 + Math.cos(ang) * mag * box.w * 0.07
                  : cx + Math.cos(ang) * mag * box.w * 0.17;
        by = cy + Math.sin(ang) * mag * box.h * 0.21;
        dsz = 3 + rnd() * 4.4;
        col = rnd() < 0.72 ? ACC : (rnd() < 0.5 ? ACC2 : "#DDD6FF");
      }
      var d = el("div", "sp-dot", sp);
      d.style.width = fmt(dsz) + "px"; d.style.height = fmt(dsz) + "px";
      d.style.background = col;
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

  /* shaped cloud rotating as if held at the cursor: x compresses around the centre of mass, dots keep a
     small live jitter so it stays a splat, not a silhouette. */
  function rotSquash(sp, squish, now) {
    var cx = sp._cx, cy = sp._cy, sx = Math.max(0.12, squish);
    for (var i = 0; i < sp._dots.length; i++) {
      var dt = sp._dots[i], b = dt._b;
      var jx = Math.cos(b.phase + now * b.w * b.side) * 3.2, jy = Math.sin(b.phase * 1.7 + now * b.w) * 2.4;
      var dx = (b.x - cx) * sx, dy = (b.y - cy) * (0.92 + 0.08 * sx);
      dt.style.transform = "translate(" + fmt(cx + dx + jx, 1) + "px," + fmt(cy + dy + jy, 1) + "px)";
      dt.style.opacity = fmt(0.55 + 0.45 * Math.min(1, sx * 1.2));
    }
    for (var k = 0; k < sp._rings.length; k++) {
      sp._rings[k].style.transform = "rotate(" + fmt(Math.sin(now * (0.5 + k * 0.22)) * 5, 2) + "deg) scaleX(" + fmt(0.6 + 0.45 * sx, 3) + ")";
    }
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
  /* ---- real 3D splat view: the Khronos shoe rendered as a splat-like point cloud in WebGL ---- */
  var SplatGL = {
    promise: null, gl: null, scene: null, cam: null, pts: null, fit: null,
    ensure: function () {
      if (this.promise) return this.promise;
      var self = this;
      this.promise = new Promise(function (resolve) {
        var fail = function () { self.ok = false; resolve(false); };
        if (!window.THREE || !THREE.WebGLRenderer || !DATA.vendor_url) { fail(); return; }
        var gl;
        try { gl = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true }); }
        catch (e) { fail(); return; }
        self.gl = gl;
        gl.domElement.className = "sp-gl";
        var xhr = new XMLHttpRequest();
        xhr.open("GET", DATA.vendor_url + "/MaterialsVariantsShoe.glb", true);
        xhr.responseType = "arraybuffer";
        xhr.onerror = fail;
        xhr.onload = function () {
          try {
            new THREE.GLTFLoader().parse(xhr.response, DATA.vendor_url + "/", function (g) {
              /* gather waypoints: subsample mesh vertices to a splat-looking cloud */
              var pos = [], uv = [], vv = 0;
              g.scene.updateMatrixWorld && g.scene.updateMatrixWorld(true);
              g.scene.traverse(function (o) {
                if (o.isMesh && o.geometry && o.geometry.attributes.position) {
                  var a = o.geometry.attributes.position;
                  for (var i = 0; i < a.count; i++) {
                    var v = new THREE.Vector3().fromBufferAttribute(a, i);
                    v.applyMatrix4(o.matrixWorld || o.matrix);
                    pos.push(v.x, v.y, v.z); vv++;
                  }
                }
              });
              if (!vv) { fail(); return; }
              var MAXP = 26000, stride = Math.ceil(vv / MAXP);
              var xs = [], ys = [], zs = [], py = [];
              for (var i = 0; i < vv; i += stride) { xs.push(pos[i * 3]); ys.push(pos[i * 3 + 1]); zs.push(pos[i * 3 + 2]); }
              var mn = new THREE.Vector3(Infinity, Infinity, Infinity), mx = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
              for (i = 0; i < xs.length; i++) { mn.min(new THREE.Vector3(xs[i], ys[i], zs[i])); mx.max(new THREE.Vector3(xs[i], ys[i], zs[i])); }
              var cx = (mn.x + mx.x) / 2, cy = (mn.y + mx.y) / 2, cz = (mn.z + mx.z) / 2;
              var span = Math.max(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z);
              var cols = [];
              var rng = 1234567;
              var rndc = function () { rng = (rng * 16807) % 2147483647; return (rng - 1) / 2147483646; };
              for (i = 0; i < xs.length; i++) {
                var f = (ys[i] - mn.y) / Math.max(1e-6, mx.y - mn.y);          /* lit top, shaded sole */
                var r, gcg, b;
                if (rndc() < 0.14) { var violet = rndc() < 0.6; r = violet ? 139 : 124; gcg = violet ? 124 : 212; b = violet ? 255 : 252; }
                else { r = 239 - 117 * (1 - f); gcg = 233 - 116 * (1 - f); b = 220 - 118 * (1 - f); }
                cols.push(r / 255, gcg / 255, b / 255);
              }
              var geo = new THREE.BufferGeometry();
              var arr = new Float32Array(xs.length * 3);
              for (i = 0; i < xs.length; i++) { arr[i * 3] = (xs[i] - cx) / span * 1.5; arr[i * 3 + 1] = (ys[i] - cy) / span * 1.5; arr[i * 3 + 2] = (zs[i] - cz) / span * 1.5; }
              geo.setAttribute("position", new THREE.BufferAttribute(arr, 3));
              geo.setAttribute("color", new THREE.Float32BufferAttribute(cols, 3));
              /* soft round splat sprite */
              var cv = document.createElement("canvas"); cv.width = cv.height = 64;
              var gc = cv.getContext("2d");
              var grd = gc.createRadialGradient(32, 32, 2, 32, 32, 32);
              grd.addColorStop(0, "rgba(255,255,255,1)"); grd.addColorStop(0.55, "rgba(255,255,255,0.65)"); grd.addColorStop(1, "rgba(255,255,255,0)");
              gc.fillStyle = grd; gc.fillRect(0, 0, 64, 64);
              var tex = new THREE.CanvasTexture(cv);
              var mat = new THREE.PointsMaterial({ size: 0.028, map: tex, vertexColors: true, transparent: true,
                                                   opacity: 0.96, depthWrite: false, sizeAttenuation: true });
              /* points render: the splat-look; gently fake anisotropic spread with a duplicate darker pass */
              var pts = new THREE.Points(geo, mat);
              var sc = new THREE.Scene();
              sc.add(pts);
              var disc = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.052, map: tex, vertexColors: true,
                transparent: true, opacity: 0.18, depthWrite: false, sizeAttenuation: true }));
              sc.add(disc);
              var cam = new THREE.PerspectiveCamera(32, 1, 0.1, 20);
              cam.position.set(0, 0.02, 3.1);
              cam.lookAt(0, 0, 0);
              self.scene = sc; self.cam = cam; self.pts = pts; self.disc = disc;
              self.ok = true;
              resolve(true);
            }, fail);
          } catch (e) { fail(); }
        };
        xhr.send();
      });
      return this.promise;
    },
    mount: function (host, w, h) {
      if (!this.ok) return false;
      if (this._w !== w || this._h !== h) {
        this.gl.setSize(w, h); this._w = w; this._h = h;
        this.cam.aspect = w / h; this.cam.updateProjectionMatrix();
      }
      if (this.gl.domElement.parentNode !== host) host.appendChild(this.gl.domElement);
      return true;
    },
    draw: function (angle, tilt) {
      if (!this.ok) return;
      this.pts.rotation.y = angle; this.disc.rotation.y = angle;
      this.pts.rotation.x = tilt || 0; this.disc.rotation.x = tilt || 0;
      this.gl.render(this.scene, this.cam);
    }
  };

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

  /* split_view: the photo on the left, its live 3D on the right; a cursor drags the splat around as the
     voice says "turn it with your mouse". Both halves are the SAME object: same core shape, same wing. */
  ARCH.split_view = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      var sv = el("div", "sv", root);
      var pk = el("div", "sv-half ph-side", sv);
      var ph = photoCard(p.photo || {});
      ph.style.position = "absolute"; ph.style.inset = "120px 4% 70px 4%";
      pk.appendChild(ph);
      r.photoIn = parseFloat(0);
      var tk = el("div", "sv-half sp-side", sv);
      var sp = splatCard(Object.assign({ compact: true, dots: 220 }, p.splat || {}), (p.splat && p.splat.seed) || 4211);
      sp.style.position = "absolute"; sp.style.inset = "120px 4% 70px 4%";
      tk.appendChild(sp);
      r.splat = sp;
      r.glHost = el("div", "sp-glhost", tk);
      r.glHost.style.inset = "188px 22px 74px 22px";
      r.mid = el("div", "sv-mid", sv, "\u2968");
      var chips = el("div", "sv-chips", sv);
      r.chips = (p.chips || []).map(function (t) { return el("div", "sv-chip", chips, t); });
      /* the drag cursor that turns the splat */
      r.cur = document.createElementNS(NS, "svg");
      r.cur.setAttribute("viewBox", "0 0 24 24");
      r.cur.setAttribute("class", "sv-cursor");
      tk.appendChild(r.cur);
      var path = document.createElementNS(NS, "path");
      path.setAttribute("d", "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z");
      path.setAttribute("fill", "#FFFFFF"); path.setAttribute("stroke", DARK); path.setAttribute("stroke-width", "1.4");
      r.cur.appendChild(path);
      r.times = bindTimes(p.cue_phrases, s, Math.max(4, (p.cue_phrases || []).length || 4));
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var t0 = r.times[0], t1 = r.times[1], t2 = r.times[2], t3 = r.times[3] || (t2 + 1);
      /* halves open on the voice */
      var o = eCubic(ramp(now, t0, t0 + 0.4));
      r.photoIn = o;
      r.cur.style.opacity = fmt(ramp(now, t1 - 0.15, t1 + 0.05));
      /* drag: cursor sweeps, dots & rings swing wider while it drags */
      var drag = ramp(now, t1, t1 + 1.4);
      var wobble = Math.sin(drag * 6.2832);
      var cx = 90 + drag * 230, cy = 300 + wobble * 46;
      r.cur.style.transform = "translate(" + fmt(cx) + "px," + fmt(cy) + "px)";
      /* the REAL 3D object TURNS: idle slow swing; while the cursor drags, it follows the drag */
      if (SplatGL.ok) {
        r.glHost.classList.add("on");
        SplatGL.mount(r.glHost, r.glHost.clientWidth || 440, r.glHost.clientHeight || 560);
        var dragging = ramp(now, t1, t1 + 1.4) * (1 - ramp(now, t1 + 1.4, t1 + 2.2));
        var ang = now * 0.9 + dragging * (drag * 2.6);
        SplatGL.draw(ang, 0.12 + 0.06 * Math.sin(now * 0.7));
      } else {
        var speed = 0.55 + 0.9 * ramp(now, t1, t1 + 1.4) * (1 - ramp(now, t1 + 1.4, t1 + 2.4));
        rotSquash(r.splat, 0.45 + 0.55 * Math.abs(Math.sin(now * speed)), now);
      }
      r.mid.style.opacity = fmt(0.25 + 0.75 * ramp(now, t0 + 0.2, t0 + 0.5));
      var chipOn = [t1, t2, t3];
      r.chips.forEach(function (c, i) {
        c.style.opacity = fmt(ramp(now, chipOn[i] || t1, (chipOn[i] || t1) + 0.25));
        c.style.transform = "translateY(" + fmt((1 - eCubic(ramp(now, chipOn[i] || t1, (chipOn[i] || t1) + 0.4))) * 14) + "px)";
      });
    }
  };

  /* blender_handoff: the same photo, then its background strips off to a checkerboard, then the .ply
     card slides into a drawn Blender viewport window and docks. Three motions, one object. */
  ARCH.blender_handoff = {
    build: function (root, s) {
      var p = s.payload || {};
      var r = {};
      var bh = el("div", "bh", root);
      /* left: the photo with its background (a solid fill that clears to checkers) */
      r.photoWrap = el("div", "bh-photo", bh);
      var ph = photoCard(p.photo || {});
      ph.style.position = "absolute"; ph.style.inset = "26px 18px 66px 18px";
      r.photoWrap.appendChild(ph);
      r.stage = ph.querySelector(".ph-stage");
      /* hoist the subject out of the stage so fading the stage removes ONLY the backdrop */
      var body = ph.querySelector(".ph-body");
      r.subject = ph.querySelector(".ph-img") || ph.querySelector(".ph-subject");
      if (r.subject && body) { r.subject.style.zIndex = "3"; ph.querySelector(".ph-body").appendChild(r.subject); }
      r.checker = el("div", "bh-checker", r.photoWrap);   /* appears behind the subject */
      r.checker.style.zIndex = "2";
      el("div", "bh-tag", r.photoWrap, "background \u00d7");
      /* right: the Blender window */
      r.appWrap = el("div", "bh-app", bh);
      var spec = p.app || {};
      var tb = el("div", "bh-app-bar", r.appWrap);
      el("i", null, tb); el("i", null, tb); el("i", null, tb);
      el("div", "bh-app-name", tb, spec.title || "Blender");
      el("div", "bh-app-grid", r.appWrap);
      var fs = p.file || {};
      var sp = splatCard({ name: fs.name || "model.ply", dots: 220, count: "", compact: true,
                           shape: (p.photo && p.photo.shape) || "mug" }, 6103);
      sp.style.position = "absolute"; sp.style.inset = "22% 8% 12% 8%";
      r.appWrap.appendChild(sp);
      r.appSplat = sp;
      r.glHost = el("div", "sp-glhost", r.appWrap);
      r.glHost.style.inset = "78px 26px 40px 26px";
      /* the file card that flies left -> right */
      r.file = el("div", "bh-file", bh);
      el("div", "bh-file-name", r.file, fs.name || "model.ply");
      el("div", "bh-file-kind", r.file, fs.kind || "3DGS");
      el("span", "bh-file-arrow", r.file, "\u21dd");
      var steps = el("div", "bh-steps", bh);
      r.steps = (p.steps || []).map(function (t) { return el("div", "bh-step", steps, t); });
      r.times = bindTimes(p.cue_phrases, s, Math.max(4, (p.cue_phrases || []).length));
      return r;
    },
    update: function (r, s, u, d) {
      var now = u + s.t0;
      var tCut = r.times[1], tFile = r.times[2], tDock = r.times[3] || (tFile + 1.4);
      /* 1 — background peels: photo stage fades, checker behind slides in */
      var cut = eCubic(ramp(now, tCut, tCut + 0.7));
      if (r.stage) r.stage.style.opacity = fmt(1 - 0.88 * cut, 3);
      r.checker.style.opacity = fmt(cut);
      /* 2 — the .ply card takes off from the cut photo… */
      var fly = eCubic(ramp(now, tFile, tFile + 1.0));
      var x0 = -20, y0 = 400, x1 = 420, y1 = 210;
      r.file.style.opacity = fmt(ramp(now, tFile - 0.2, tFile));
      r.file.style.transform = "translate(" + fmt(x0 + (x1 - x0) * fly) + "px," + fmt(y0 + (y1 - y0) * fly) + "px)"
        + " rotate(" + fmt(-14 + 14 * eCubic(ramp(now, tFile, tFile + 1.2)), 1) + "deg)"
        + " scale(" + fmt(1 - 0.32 * eCubic(ramp(now, tDock - 0.3, tDock)), 3) + ")";
      /* 3 — …and docks: the Blender window fades in, splat blooms inside */
      var dock = eCubic(ramp(now, tDock, tDock + 0.45));
      r.appWrap.style.opacity = fmt(0.25 + 0.75 * ramp(now, tDock - 0.35, tDock));
      r.file.style.opacity = fmt(ramp(now, tFile - 0.2, tFile) * (1 - ramp(now, tDock + 0.15, tDock + 0.5)));
      r.appSplat.style.opacity = fmt(ramp(now, tDock, tDock + 0.3));
      var bloom = eBack(ramp(now, tDock + 0.1, tDock + 0.6));
      if (SplatGL.ok) {
        r.glHost.classList.add("on");
        SplatGL.mount(r.glHost, r.glHost.clientWidth || 380, r.glHost.clientHeight || 560);
        /* dock pop, then a slow show-off turn */
        var pop = 1 + 0.12 * Math.sin(bloom * Math.PI);
        SplatGL.draw(now * 0.85, 0.1);
        r.glHost.style.transform = "scale(" + fmt((0.74 + 0.26 * bloom) * pop, 3) + ")";
        r.appSplat.style.opacity = fmt(ramp(now, tDock, tDock + 0.3) * 0.25);
      } else {
        rotSquash(r.appSplat, 0.5 + 0.5 * Math.abs(Math.sin(now * 0.7)), now);
        r.appSplat.style.transform = "scale(" + fmt(0.74 + 0.26 * bloom, 3) + ")";
      }
      var stepT = [tCut, tDock - 0.3, tDock + 0.6];
      r.steps.forEach(function (st, i) {
        st.style.opacity = fmt(ramp(now, stepT[i], stepT[i] + 0.22));
        st.style.transform = "translateX(" + fmt((1 - eCubic(ramp(now, stepT[i], stepT[i] + 0.3))) * 26) + "px)";
      });
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
    var needsGL = D.scenes.some(function (s) { return s.archetype === "split_view" || s.archetype === "blender_handoff"; });
    if (needsGL && window.THREE) { SplatGL.ensure().then(function () { window.ready = true; }); }
    else { window.ready = true; }
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
