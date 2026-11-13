/* Shared deterministic narration cues for template item builds.
 * Loaded before engines: engines build their scenes immediately. No timers or random state.
 */
(function () {
  "use strict";
  function norm(w) { return String(w || "").toLowerCase().replace(/[^a-z0-9]/g, ""); }
  function cueTimes(phrases, scene, n, options) {
    options = options || {};
    var words = scene.words || [], out = [], report = [], last = -Infinity;
    var start = Number(scene.t0), end = Number(scene.t1), duration = Math.max(0.001, end-start);
    for (var i = 0; i < n; i++) {
      var phrase = String((phrases || [])[i] || "");
      var target = phrase.toLowerCase().match(/[a-z0-9]+/g) || [], hit = null;
      // Exact contiguous phrases, in spoken order. Never bind to a stray word from a phrase.
      for (var j = 0; target.length && j <= words.length-target.length; j++) {
        if (Number(words[j][1]) < last) continue;
        if (target.every(function (word,k) { return norm(words[j+k][0]) === word; })) {
          hit = Number(words[j][1]); break;
        }
      }
      var matched = hit !== null;
      if (!matched) {
        if (options.fallback === "spread") hit = start + duration * (i / Math.max(1,n)) + 0.12;
        else if (options.fallback === "redline") hit = start + 0.35 + i * Math.min(1.1, Math.max(0.5, duration/(n+1.6)));
        else hit = start + 0.3 + i * Math.max(0.45, Math.min(1.2, duration/(n+1.5)));
      }
      if (i === 0 && options.lead) hit = Math.min(hit, start + 0.12);
      // Maintain ordering without pushing visual events beyond a short scene's end.
      hit = Math.max(start, Math.min(end - 0.001, Math.max(hit, last)));
      out.push(hit); report.push({phrase:phrase, time:hit, matched:matched}); last = hit;
    }
    window.__motionCueReports = window.__motionCueReports || {};
    window.__motionCueReports[scene.id] = report;
    return out;
  }
  window.HouseMotion = {cueTimes:cueTimes};
})();
