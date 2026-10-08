        // ================= VVS runtime = Reels Studio template API (shared by every template) =================
        // Deterministic helpers: seeded PRNG, frame-exact count-ups, voice-timed karaoke.
        // All timings come from DATA (built by the Python pipeline from the real voice-over).
        const VVS = (() => {
          const HF = window.__hyperframes || {};
          const $ = (s, r) => (r || document).querySelector(s);
          const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
          const mk = (tag, cls, parent, text) => {
            const e = document.createElement(tag);
            if (cls) e.className = cls;
            if (text !== undefined && text !== null) e.textContent = text;
            if (parent) parent.appendChild(e);
            return e;
          };
          const SVGNS = "http://www.w3.org/2000/svg";
          const svg = (tag, attrs, parent) => {
            const e = document.createElementNS(SVGNS, tag);
            for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
            if (parent) parent.appendChild(e);
            return e;
          };
          let _seed = 1;
          const rnd = () => {
            _seed |= 0; _seed = (_seed + 0x6d2b79f5) | 0;
            let t = Math.imul(_seed ^ (_seed >>> 15), 1 | _seed);
            t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
          };
          let D = 10;
          let DATA_ = null;
          const seg = (id) => {
            const s = DATA_.segs[id];
            if (!s) throw new Error("VVS: missing segment " + id);
            return s;
          };
          const ev = (k, dflt) => (DATA_.events && DATA_.events[k] !== undefined ? DATA_.events[k] : dflt);
          const initials = (name) => String(name || "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("") || "★";
          const onColor = (hex) => {
            const h = String(hex || "").replace("#", "");
            if (h.length !== 6) return null;
            const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
            const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
            return lum > 0.55 ? "#0b0b10" : "#ffffff";
          };

          // largest font-size (px) at which el fits its own width and maxH (binary search, deterministic)
          function fit(el, { max = 120, min = 24, maxH = 99999 } = {}) {
            const ok = () => el.scrollHeight <= maxH && el.scrollWidth <= el.clientWidth + 1;
            el.style.fontSize = max + "px";
            if (ok()) return max;
            let lo = min, hi = max;
            while (hi - lo > 1) {
              const mid = (lo + hi) >> 1;
              el.style.fontSize = mid + "px";
              if (ok()) lo = mid; else hi = mid;
            }
            el.style.fontSize = lo + "px";
            return lo;
          }

          // split an element's text into word spans (for read-along highlighting)
          function words(el) {
            const parts = el.textContent.trim().split(/\s+/);
            el.textContent = "";
            el.classList.add("karaoke");
            return parts.map((w, i) => {
              const s = mk("span", "kw", el, w);
              if (i < parts.length - 1) el.appendChild(document.createTextNode(" "));
              return s;
            });
          }
          // light each word as it is spoken; falls back to proportional timing if counts differ
          function karaoke(tl, spans, id, from = 0) {
            const s = seg(id);
            const ws = s.words || [];
            const exact = ws.length - from >= spans.length;
            spans.forEach((sp, i) => {
              const t = exact ? ws[i + from][1] : s.start + ((s.end - s.start) * i) / Math.max(1, spans.length);
              tl.fromTo(sp, { opacity: 0.3 }, { opacity: 1, duration: 0.08, ease: "none", immediateRender: false }, t);
            });
          }

          // frame-exact number roll (one tl.set per frame -> seek-safe)
          function countText(tl, el, from, to, t0, dur, fmt) {
            const n = Math.max(1, Math.round(dur * 30));
            for (let f = 0; f <= n; f++) {
              const p = f / n;
              const e = 1 - Math.pow(1 - p, 3);
              tl.set(el, { textContent: fmt(from + (to - from) * e) }, t0 + f / 30);
            }
          }
          function shake(tl, sel, t, amp = 14, frames = 8) {
            for (let i = 0; i < frames; i++) {
              const k = 1 - i / frames;
              tl.set(sel, { x: (rnd() * 2 - 1) * amp * k, y: (rnd() * 2 - 1) * amp * k }, t + i / 30);
            }
            tl.set(sel, { x: 0, y: 0 }, t + frames / 30);
          }
          function flash(tl, t, o = 0.7, d = 0.25) {
            tl.fromTo("#flash", { opacity: o }, { opacity: 0, duration: d, ease: "power2.out", immediateRender: false }, t);
          }
          // show a .scene between t0 and t1 (explicit fromTo both ways -> deterministic under seeking)
          function show(tl, el, t0, t1, o = {}) {
            const inFrom = o.inFrom || { opacity: 0, y: 50 };
            const outTo = o.outTo || { opacity: 0, y: -40 };
            const inDur = o.inDur || 0.35;
            const outDur = o.outDur || 0.25;
            tl.set(el, { visibility: "visible" }, t0);
            tl.fromTo(el, inFrom, { opacity: 1, x: 0, y: 0, scale: 1, duration: inDur, ease: o.ease || "power3.out", immediateRender: false }, t0);
            if (t1 !== undefined && t1 !== null) {
              tl.fromTo(el, { opacity: 1, x: 0, y: 0, scale: 1 }, { ...outTo, duration: outDur, ease: "power2.in", immediateRender: false }, t1 - outDur);
              tl.set(el, { visibility: "hidden" }, t1);
            }
          }

          function background(tl) {
            tl.fromTo("#glowA", { x: -40, y: -30 }, { x: 220, y: 260, duration: D, ease: "sine.inOut" }, 0);
            tl.fromTo("#glowB", { x: 60, y: 40 }, { x: -240, y: -300, duration: D, ease: "sine.inOut" }, 0);
            tl.fromTo("#bg-grid", { y: 0 }, { y: -270, duration: D, ease: "none" }, 0);
          }
          function hud(tl) {
            tl.fromTo("#prog-fill", { scaleX: 0 }, { scaleX: 1, duration: D, ease: "none" }, 0);
            $("#wm-handle").textContent = (DATA_.brand && DATA_.brand.handle) || "";
            tl.fromTo("#wm", { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.4, ease: "power2.out" }, Math.min(1.0, D * 0.08));
          }

          // karaoke captions for every segment with caption:true (<= maxWords per group, hard cuts)
          function captions(tl) {
            const cfg = DATA_.captions || {};
            if (cfg.enabled === false) return;
            if (cfg.y) $("#root").style.setProperty("--cap-y", cfg.y + "px");
            const zone = $("#cap-zone");
            const all = [];
            DATA_.order.forEach((id) => {
              const s = DATA_.segs[id];
              if (s.caption && s.words) s.words.forEach((w) => all.push({ w: w[0], s: w[1], e: w[2], seg: id }));
            });
            const maxW = cfg.maxWords || 3;
            const nk = (w) => String(w).toLowerCase().replace(/[^a-z0-9]/g, "");
            const keys = new Set((cfg.keywords || []).map(nk));  // caption keywords -> .key (yellow); numbers too
            const isKey = (w) => keys.has(nk(w)) || (cfg.numberKeys !== false && keys.size > 0 && /\d/.test(w));
            const groups = [];
            let cur = [];
            all.forEach((x, i) => {
              cur.push(x);
              const nx = all[i + 1];
              if (!nx || cur.length >= maxW || /[.,!?;:]$/.test(x.w) || nx.seg !== x.seg || nx.s - x.e > 0.35) {
                groups.push(cur);
                cur = [];
              }
            });
            groups.forEach((g, gi) => {
              const div = mk("div", "cg", zone);
              const spans = g.map((x) => {
                const w = mk("span", isKey(x.w) ? "cw key" : "cw", div);
                mk("span", "b", w, x.w);
                const hl = mk("span", "hl", w, x.w);
                hl.setAttribute("data-layout-allow-overlap", "");
                return w;
              });
              const next = groups[gi + 1];
              const on = Math.max(0, g[0].s - 0.04);
              const off = Math.max(on + 0.12, Math.min(next ? next[0].s - 0.04 : D, g[g.length - 1].e + 0.5, D));  // never stuck on
              tl.fromTo(div, { opacity: 0, scale: 0.84, y: 20 }, { opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.2)", immediateRender: false }, on);
              tl.set(div, { opacity: 0 }, off);
              g.forEach((x, k) => {
                const hl = spans[k].querySelector(".hl");
                tl.fromTo(hl, { opacity: 0 }, { opacity: 1, duration: 0.05, immediateRender: false }, x.s);
                tl.fromTo(spans[k], { scale: 1 }, { scale: 1.08, duration: 0.08, immediateRender: false }, x.s);
                tl.fromTo(spans[k], { scale: 1.08 }, { scale: 1, duration: 0.14, immediateRender: false }, x.s + 0.08);
                tl.fromTo(hl, { opacity: 1 }, { opacity: 0, duration: 0.08, immediateRender: false }, Math.max(x.e, x.s + 0.12));
              });
            });
          }

          // follow end-card with a cursor "press" (press time shared with the audio click via DATA.events.press)
          function endCard(tl, t0, t1) {
            const b = DATA_.brand || {};
            const st = $("#stage");
            const card = mk("div", "card", st);
            card.id = "endcard";
            const av = mk("div", "", card);
            av.id = "ec-avatar";
            mk("span", "", av, initials(b.name));
            const nm = mk("div", "", card);
            nm.id = "ec-name";
            const nmt = mk("span", "", nm, b.name || "");
            const badge = mk("span", "", nm);
            badge.id = "ec-badge";
            badge.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
            mk("div", "", card, b.handle || "").id = "ec-handle";
            mk("div", "", card, b.tagline || "").id = "ec-tag";
            const btn = mk("div", "", card);
            btn.id = "ec-btn";
            const lbl = mk("span", "", btn, b.cta_button || "Follow");
            const done = mk("div", "done", btn, "✓ Following");
            done.setAttribute("data-layout-allow-overlap", "");
            if (typeof HF.fitTextFontSize === "function") {
              const f = HF.fitTextFontSize(b.name || "", { baseFontSize: 62, minFontSize: 38, maxWidth: 640, fontFamily: "Inter", fontWeight: 900 });
              nmt.style.fontSize = f.fontSize + "px";
            }
            const cur = svg("svg", { id: "ec-cursor", viewBox: "0 0 24 24" }, st);
            svg("path", { d: "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z", fill: "#fff", stroke: "#111", "stroke-width": "1.2", "stroke-linejoin": "round" }, cur);
            const press = ev("press", t0 + 1.0);
            tl.fromTo(card, { opacity: 0, y: 90, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "back.out(1.6)", immediateRender: false }, t0);
            tl.fromTo(cur, { opacity: 0, x: 220, y: 260 }, { opacity: 1, x: 0, y: 0, duration: 0.45, ease: "power2.out", immediateRender: false }, press - 0.5);
            tl.fromTo(btn, { scale: 1 }, { scale: 0.93, duration: 0.07, immediateRender: false }, press);
            tl.fromTo(btn, { scale: 0.93 }, { scale: 1, duration: 0.2, ease: "back.out(3)", immediateRender: false }, press + 0.07);
            tl.fromTo(done, { opacity: 0 }, { opacity: 1, duration: 0.08, immediateRender: false }, press + 0.04);
            tl.fromTo(lbl, { opacity: 1 }, { opacity: 0, duration: 0.08, immediateRender: false }, press + 0.04);
            tl.fromTo(cur, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, press + 0.7);
            if (t1 !== undefined && t1 !== null) tl.fromTo(card, { opacity: 1 }, { opacity: 0, duration: 0.25, immediateRender: false }, t1 - 0.25);
            return card;
          }

          const API = { $, $$, mk, svg, rnd, seg, ev, fit, words, karaoke, countText, shake, flash, show, endCard, initials, onColor };

          async function boot(DATA, build) {
            DATA_ = DATA;
            D = DATA.duration;
            API.D = D;
            API.DATA = DATA;
            _seed = DATA.seed || 1;
            const root = $("#root");
            const b = DATA.brand || {};
            if (b.accent) root.style.setProperty("--acc", b.accent);
            if (b.accent2) root.style.setProperty("--acc2", b.accent2);
            const on = b.onaccent || onColor(b.accent);
            if (on) root.style.setProperty("--onacc", on);
            const cs = getComputedStyle(root);
            const on2 = onColor(b.accent2 || cs.getPropertyValue("--acc2").trim());
            if (on2) root.style.setProperty("--onacc2", on2);
            const fonts = [
              document.fonts.load('400 100px "Anton"'),
              document.fonts.load('900 100px "Inter"'),
              document.fonts.load('500 30px "JetBrains Mono"'),
            ];
            if (DATA.urdu) fonts.push(document.fonts.load('400 60px "Noto Nastaliq Urdu"'));
            await Promise.all(fonts).catch(() => {});
            const tl = gsap.timeline({ paused: true });
            background(tl);
            hud(tl);
            await build(tl, API);
            captions(tl);
            tl.set({}, {}, D); // pin the timeline length to the composition duration
            window.__timelines["main"] = tl;
            if (typeof window.__hfForceTimelineRebind === "function") window.__hfForceTimelineRebind();
          }
          return { boot, API };
        })();
