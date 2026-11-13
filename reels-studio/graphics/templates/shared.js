/* shared.js — injected into EVERY template by render.build_stage_html, after the template engine.
 *
 * The house caption and the house handle are brand elements, so they live in one file instead of
 * being re-implemented (and drifting) in seven engines. A template draws its own scene; it does
 * not own the caption.
 *
 * Contract: the engine defines `window.setTime(t)`. This file wraps it, so the caption is redrawn
 * on every frame with the same logic for every short.
 */
(function () {
  "use strict";
  var D = window.DATA || {};
  var YELLOW = "#FFD60A";
  var CHUNK = Math.min(3, Math.max(1, parseInt(D.caption_words || 3, 10)));   // owner rule: 2-4 words per chunk

  function norm(w) { return String(w).toLowerCase().replace(/[^a-z0-9]/g, ""); }

  var capEl = null, handleEl = null;

  /* Engines written before the house layer each grew a caption of their own (.caption,
     .pl-caption, .ng-cap, ...). They are all now superseded: two captions on screen is a bug, and
     deleting the code from six engines is a worse bet than suppressing it in one place. */
  var TEMPLATE_CAPTIONS = ".caption,.pl-caption,.ng-cap,.vb-cap,.photo-cap,.dr-cap,.mk-cap,.rl-cap";
  var suppressed = 0;
  function suppressTemplateCaptions() {
    var els = document.querySelectorAll(TEMPLATE_CAPTIONS);
    for (var i = 0; i < els.length; i++) {
      if (els[i] === capEl) continue;
      els[i].setAttribute("data-house-suppressed", "1");
      els[i].style.display = "none";
      suppressed++;
    }
    window.__houseSuppressedCaptions = suppressed;
    return suppressed;
  }

  function mount() {
    var stage = document.getElementById("stage");
    if (!stage) return;
    if (!handleEl && D.handle) {
      handleEl = document.createElement("div");
      handleEl.className = "yt-handle";
      handleEl.textContent = D.handle;
      stage.appendChild(handleEl);
    }
    if (!capEl) {
      capEl = document.createElement("div");
      capEl.className = "yt-cap";
      stage.appendChild(capEl);
    }
  }

  /* The house outro is a SINGLE stage-level element, not something mounted into a template's own
     scene wrapper. Mounting into a wrapper leaked: velocity-black's plain `.scene` class matched a
     `.scene` selector, so the card was attached to scene 1 and appeared under the hook. Appending
     to #stage and showing it only inside the endcard window cannot leak. */
  var OUTRO = {};        // scene id -> refs
  function mountOutro() {
    var stage = document.getElementById("stage");
    if (!stage) return;
    (D.scenes || []).forEach(function (s) {
      if (s.archetype !== "endcard" || OUTRO[s.id]) return;
      var refs = window.buildOutro(stage, s);
      refs.root.style.display = "none";
      refs.root.setAttribute("data-outro-for", s.id);
      OUTRO[s.id] = refs;
      s._outro = refs;
    });
  }

  function updateOutros(t) {
    (D.scenes || []).forEach(function (s) {
      var refs = OUTRO[s.id];
      if (!refs) return;
      var live = t >= s.t0 && t < s.t1;
      refs.root.style.display = live ? "block" : "none";
      if (!live) return;
      // the card stands alone: the template's own scene wrapper is emptied out of the way
      var wrap = document.querySelector('.scene[data-scene="' + s.id + '"]');
      if (wrap) wrap.style.visibility = "hidden";
      window.updateOutro(refs, s, t - s.t0, Math.max(1e-6, s.t1 - s.t0));
    });
  }

  function activeScene(t) {
    var sc = D.scenes || [];
    for (var k = 0; k < sc.length; k++) {
      if (t >= sc[k].t0 && t < sc[k].t1) return sc[k];
    }
    return t < 0 ? sc[0] : sc[sc.length - 1];
  }

  function draw(t) {
    if (!capEl) return;
    var s = activeScene(t);
    if (!s || s.caption === false) { capEl.textContent = ""; return; }
    capEl.classList.toggle("outro-caption", s.archetype === "endcard");
    var ws = s.words || [];
    if (!ws.length) { capEl.textContent = s.text || ""; return; }

    var cur = -1;
    for (var i = 0; i < ws.length; i++) { if (t >= ws[i][1]) cur = i; }
    if (cur < 0) cur = 0;

    // Fixed groups do not reshuffle on every word; all words sit on the same baseline.
    var start = Math.floor(cur / CHUNK) * CHUNK;
    var end = Math.min(ws.length, start + CHUNK);
    // Keep each group on one line. Measure using the real loaded font rather than relying
    // on wrapping, which strands a single word below its neighbours on small screens.
    var canvas = draw._canvas || (draw._canvas = document.createElement("canvas"));
    var ctx = canvas.getContext("2d");
    ctx.font = '88px Anton';
    var measured = 0;
    for (var m = start; m < end; m++) measured += ctx.measureText(String(ws[m][0]).toUpperCase()).width;
    measured += Math.max(0, end - start - 1) * 20 + 16;
    capEl.style.fontSize = Math.min(88, Math.floor(88 * 952 / Math.max(1, measured))) + 'px';
    var html = "";
    for (var j = start; j < end; j++) {
      var w = String(ws[j][0]);
      var isNow = j === cur;
      var elapsed = Math.max(0, t - ws[j][1]);
      var scale = isNow ? 1 + 0.045 * Math.max(0, 1 - elapsed / 0.16) : 1;
      html += '<span class="cw' + (isNow ? ' on hit' : '') + '" style="transform:scale(' + scale.toFixed(3) + ')">' + escapeHtml(w) + '</span>';
    }
    capEl.innerHTML = html;
  }

  /* the accent word: whatever the scene marked as the cue, else the longest content word in the
     chunk. Never a stopword — a highlighted "the" teaches the viewer nothing. */
  var STOP = ("a an the and or of to in on for with is it its be by as at from that this so any " +
              "every each you your we our they them then first before").split(" ");
  function claimWord(w, sceneText) {
    var n = norm(w);
    if (!n || STOP.indexOf(n) >= 0 || n.length < 3) return false;
    if (window.__cueWords && window.__cueWords[n]) return true;
    return false;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* collect every scene's cue words once, so the caption knows which word to light up */
  function cueIndex() {
    var idx = {};
    (D.scenes || []).forEach(function (s) {
      var c = s.cue_word || (s.payload && (s.payload.keyword || s.payload.hit)) || null;
      if (c) idx[norm(c)] = 1;
      if (c) idx[norm(c)] = 1;
      (s.hits || []).forEach(function (h) { idx[norm(h)] = 1; });
      (s.payload && s.payload.accent_words || []).forEach(function (h) { idx[norm(h)] = 1; });
    });
    window.__cueWords = idx;
  }

  function install() {
    mount();
    suppressTemplateCaptions();
    if (typeof window.buildOutro === "function") mountOutro();
    cueIndex();
    var inner = window.setTime;
    if (typeof inner === "function") {
      window.setTime = function (t) {
        inner(t);
        draw(t);
        updateOutros(t);
      };
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
