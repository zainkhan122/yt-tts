        // ================= Spotlight scene engine (repo-spotlight + tool-spotlight) =================
        // Scenes: DATA.extra.scenes. Times: DATA.events (anchored to the real voice-over by spotcore.py).
        // Seek-safe: explicit fromTo states everywhere, per-frame tl.set for typing / counting.
        async function buildScene(tl, A) {
          const X = A.DATA.extra || {};
          const E = (k, d) => A.ev(k, d);
          const stage = A.$("#stage");
          const R = X.regions || {};
          const F = X.facts || {};
          const norm = (w) => String(w).toLowerCase().replace(/[^a-z0-9]/g, "");
          const KEYS = new Set(((A.DATA.captions || {}).keywords || []).map(norm));
          const FIRST = ((X.scenes || [])[0] || {}).id;
          const L = X.layout || {};
          const STAGE_BOTTOM = L.stage_bottom || 1128;        // every card ends here, above captions
          const COVER_STAGE_TOP = L.cover_top || 640;
          const COVER_STAGE_HEIGHT = STAGE_BOTTOM - COVER_STAGE_TOP;
          const STAGE_TOP = L.stage_top || 452;
          const WHIP = X.cut === "whip";

          // ---------------------------------------------------------------- helpers
          const fmtFull = (v) => Math.round(v).toLocaleString("en-US");
          const fmtCompact = (v) => (v >= 1e6 ? (v / 1e6).toFixed(1) + "M" : v >= 1e3 ? (v / 1e3).toFixed(1) + "K" : String(Math.round(v)));
          const getPath = (p) => String(p || "").split(".").reduce((o, k) => (o == null ? o : o[k]), { facts: F });
          const prettyName = () => String(F.repo || F.name || "").split("/").pop().split(/[-_]+/).filter(Boolean).join(" ").toUpperCase();
          const firstQuestion = (say) => {
            const t = String(say || "").replace(/\{([^{}|]+)\|[^{}]+\}/g, "$1");
            const i = t.indexOf("?");
            return i > 0 ? t.slice(0, i + 1) : "";
          };

          function enter(el, t0, t1, first) {
            if (first) {
              el.style.visibility = "visible";
              el.style.opacity = "1";
            } else {
              tl.set(el, { visibility: "visible" }, t0);
              if (WHIP) tl.fromTo(el, { opacity: 0, x: 90 }, { opacity: 1, x: 0, duration: 0.2, ease: "power3.out", immediateRender: false }, t0);
              else tl.fromTo(el, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.32, ease: "power2.out", immediateRender: false }, t0);
            }
            if (t1 < A.D - 0.01) {
              const d = WHIP ? 0.16 : 0.26;
              if (WHIP) tl.fromTo(el, { opacity: 1, x: 0 }, { opacity: 0, x: -90, duration: d, ease: "power2.in", immediateRender: false }, t1 - d);
              else tl.fromTo(el, { opacity: 1, y: 0 }, { opacity: 0, y: 0, duration: d, ease: "none", immediateRender: false }, t1 - d);
              tl.set(el, { visibility: "hidden" }, t1);
            }
          }
          function showSet(vs, a, z, first) {  // static <video> wrapper: plain cut in/out (the clip itself is timed by the renderer)
            if (first) { vs.style.visibility = "visible"; vs.style.opacity = "1"; }
            else tl.set(vs, { visibility: "visible", opacity: 1 }, a);
            if (z < A.D - 0.01) tl.set(vs, { visibility: "hidden", opacity: 0 }, z);
          }
          function richText(el, text) {  // *word* or *several words* = yellow; otherwise caption keywords are yellow
            const explicit = /\*[^*]+\*/.test(text);
            const parts = String(text).split(/\s+/).filter(Boolean);
            const box = A.mk("span", "rt", el);  // single inline flex item: whitespace between words survives
            let inside = false;  // a highlight span may cover several words: "*FIND IT.*"
            parts.forEach((w, i) => {
              let word = w, on = inside;
              if (explicit) {
                if (word.startsWith("*")) { word = word.slice(1); on = inside = true; }
                const close = inside ? word.match(/^(.*?)\*(\W*)$/) : null;  // "IT.*", "AI*", "WORKS*,"
                if (close) { word = close[1] + close[2]; inside = false; }
              }
              A.mk("span", (explicit ? on : KEYS.has(norm(word))) ? "y" : "", box, word);
              if (i < parts.length - 1) box.appendChild(document.createTextNode(" "));
            });
          }
          function heading(root, text, t, o = {}) {
            if (!text) return null;
            const cover = !!o.instant;
            const h = A.mk("div", "sp-heading display" + (cover ? " cover-heading" : ""), root);
            if (o.top) h.style.top = o.top + "px";
            richText(h, text);
            // Cover title uses the same large, bold range as the original clip-hook covers.
            // Keep at least 80 px and give it the full 380 px title band instead of shrinking
            // long image-hook titles into the old 56 px one-line style.
            A.fit(h, cover
              ? { max: o.max || 200, min: o.min || 80, maxH: o.maxH || 380 }
              : { max: o.max || 128, min: 56, maxH: o.maxH || 180 });
            if (o.instant) {  // hook scene: visible on frame 0 (the cover frame every platform grabs)
              h.style.opacity = "1";
              tl.fromTo(h, { scale: 1.1 }, { scale: 1, duration: 0.4, ease: "power3.out" }, 0);
            } else {
              tl.fromTo(h, { opacity: 0, scale: 1.12 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, t);
            }
            return h;
          }
          function credit(root, y, t) {
            return;  // owner rule 2026-10-09: no credit captions on screen; credits go in the post text + descriptions
            if (!X.credits) return;
            const c = A.mk("div", "sp-credit", root, X.credits);
            c.style.top = y + "px";
            tl.fromTo(c, { opacity: 0 }, { opacity: 1, duration: 0.3, immediateRender: false }, t);
          }
          function dots(parent) {
            const d = A.mk("div", "sp-dots", parent);
            ["#ff5f57", "#febc2e", "#28c840"].forEach((c) => { A.mk("span", "", d).style.background = c; });
          }

          // ---------------------------------------------------------------- browser + camera
          function browser(root, o) {
            const br = A.mk("div", "sp-browser", root);
            br.style.top = o.top + "px";
            br.style.height = o.height + "px";
            if (o.instant) br.style.opacity = "1";  // hook scene: the frame belongs to the cover frame
            const bar = A.mk("div", "sp-bar", br);
            dots(bar);
            const url = A.mk("div", "sp-url", bar, String(o.display_url || o.url || "").replace(/^https?:\/\//, ""));
            url.setAttribute("data-layout-allow-occlusion", "");
            const lock = A.svg("svg", { class: "sp-lock", viewBox: "0 0 24 24" }, url);
            A.svg("path", { d: "M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V11a1 1 0 0 1 1-1h1zm2 0h6V7a3 3 0 0 0-6 0v3z", fill: "#3fb950" }, lock);
            const vp = A.mk("div", "sp-vp", br);
            vp.setAttribute("data-layout-allow-overflow", "");
            const img = o.img;
            const page = A.mk("div", "sp-page", vp);
            page.setAttribute("data-layout-allow-overflow", "");
            page.style.width = img.w + "px";
            page.style.height = img.h + "px";
            const im = A.mk("img", "", page);
            im.src = "assets/" + img.file;
            im.alt = "";
            const vpW = 996, vpH = o.height - 68;
            const s0 = vpW / img.w;
            const B = { br, vp, page, img, vpW, vpH, s0, left: 42, top: o.top + 66, regions: R };
            const clamp = (x, y, S) => ({
              x: Math.min(0, Math.max(Math.min(0, vpW - img.w * S), x)),
              y: Math.min(0, Math.max(Math.min(0, vpH - img.h * S), y)), scale: S,
            });
            B.state = (region, zoom = 1, frac = 0) => {
              const S = s0 * zoom;
              const r = typeof region === "string" ? R[region] : region;
              if (!r) return clamp(0, -Math.max(0, img.h * S - vpH) * frac, S);
              return clamp(vpW / 2 - (r.x + r.w / 2) * S, vpH / 2 - (r.y + r.h / 2) * S, S);
            };
            B.drift = (st, z) => {  // zoom around the viewport centre
              const S = st.scale * z;
              const cx = (vpW / 2 - st.x) / st.scale, cy = (vpH / 2 - st.y) / st.scale;
              return clamp(vpW / 2 - cx * S, vpH / 2 - cy * S, S);
            };
            B.toScreen = (region, st) => {
              const r = typeof region === "string" ? R[region] : region;
              return { x: B.left + st.x + (r.x + r.w / 2) * st.scale, y: B.top + st.y + (r.y + r.h / 2) * st.scale };
            };
            return B;
          }
          // camera plan: [initial drift] + per keyframe (eased move, then slow drift until the next move)
          function camPlan(B, states, times, t1) {
            const segs = [];
            let cur = states[0];
            const firstEnd = states.length > 1 ? times[1] : t1;
            const d0 = B.drift(cur, 1.035);
            segs.push({ a: times[0], z: Math.max(times[0] + 0.05, firstEnd), from: cur, to: d0, ease: "none" });
            cur = d0;
            for (let k = 1; k < states.length; k++) {
              const a = times[k], next = k + 1 < states.length ? times[k + 1] : t1;
              const dur = Math.min(0.8, Math.max(0.3, (next - a) * 0.6));
              segs.push({ a, z: a + dur, from: cur, to: states[k], ease: "power3.inOut" });
              cur = states[k];
              if (next - (a + dur) > 0.12) {
                const dk = B.drift(states[k], 1.03);
                segs.push({ a: a + dur, z: next, from: states[k], to: dk, ease: "none" });
                cur = dk;
              }
            }
            return segs;
          }
          function camApply(page, segs) {
            segs.forEach((g) => tl.fromTo(page, { ...g.from }, { ...g.to, duration: Math.max(0.01, g.z - g.a), ease: g.ease, immediateRender: false }, g.a));
          }
          function camAt(segs, t) {
            let g = segs[0];
            for (const s of segs) if (s.a <= t) g = s;
            const p = Math.min(1, Math.max(0, (t - g.a) / Math.max(0.001, g.z - g.a)));
            const e = gsap.parseEase(g.ease)(p);
            return { x: g.from.x + (g.to.x - g.from.x) * e, y: g.from.y + (g.to.y - g.from.y) * e, scale: g.from.scale + (g.to.scale - g.from.scale) * e };
          }
          function cursorClick(root, B, segs, region, tc, stateText) {
            const r = R[region];
            if (!r) return;
            const p = B.toScreen(r, camAt(segs, tc));
            const cur = A.svg("svg", { class: "sp-cursor", viewBox: "0 0 24 24" }, root);
            A.svg("path", { d: "M4 2l15 9.2-6.6 1.3 3.9 7.4-2.8 1.5-3.9-7.5L4 18.8z", fill: "#fff", stroke: "#111", "stroke-width": "1.2", "stroke-linejoin": "round" }, cur);
            gsap.set(cur, { transformOrigin: "17% 8%" });
            const ox = p.x - 12, oy = p.y - 6;  // arrow tip at the target
            tl.fromTo(cur, { opacity: 0, x: ox + 250, y: oy + 300 }, { opacity: 1, x: ox, y: oy, duration: 0.6, ease: "power2.inOut", immediateRender: false }, tc - 0.62);
            tl.fromTo(cur, { scale: 1 }, { scale: 0.82, duration: 0.07, immediateRender: false }, tc);
            tl.fromTo(cur, { scale: 0.82 }, { scale: 1, duration: 0.18, immediateRender: false }, tc + 0.07);
            tl.fromTo(cur, { opacity: 1 }, { opacity: 0, duration: 0.25, immediateRender: false }, tc + 0.8);
            const rip = A.mk("div", "sp-ripple", root);
            rip.style.left = p.x + "px";
            rip.style.top = p.y + "px";
            tl.fromTo(rip, { opacity: 0.95, scale: 0.2 }, { opacity: 0, scale: 1.7, duration: 0.55, ease: "power2.out", immediateRender: false }, tc);
            if (stateText) {  // button state change, inside the page so it rides the camera
              const b = A.mk("div", "sp-starred", B.page, stateText);
              Object.assign(b.style, { left: r.x + "px", top: r.y + "px", width: r.w + "px", height: r.h + "px" });
              tl.fromTo(b, { opacity: 0 }, { opacity: 1, duration: 0.08, immediateRender: false }, tc + 0.03);
            }
          }
          function statBadge(root, st, t, big, instant) {
            const v = typeof st.value === "number" ? st.value : Number(getPath(st.from)) || 0;
            const base = st.format === "compact" ? fmtCompact : st.decimals ? (v) => Number(v).toFixed(st.decimals) : fmtFull;
            const fmt = (v) => (st.prefix || "") + base(v) + (st.suffix || "");  // e.g. decimals:1 + suffix " GB" -> "12.2 GB"
            const card = A.mk("div", "sp-stat" + (big ? " sp-bigstat" : ""), root);
            if (st.top) card.style.top = st.top + "px";
            const n = A.mk("div", "n", card);
            if (st.icon !== false) {
              const ic = A.svg("svg", { viewBox: "0 0 24 24" }, n);
              A.svg("path", { d: "M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6L2.5 9.4l6.6-.8z", fill: "#ffd60a" }, ic);
            }
            const num = A.mk("span", "", n, fmt(0));
            A.mk("div", "l", card, st.label || "");
            // Auto-fit: measure the FINAL string and shrink the number until number + label
            // fit inside the card. A long suffix ("49.4 pages/s") must never overflow the box.
            num.textContent = fmt(v);
            let statFs = big ? 220 : 140;
            n.style.fontSize = statFs + "px";
            while (statFs > 56 && (card.scrollHeight > card.clientHeight || n.scrollWidth > card.clientWidth + 4)) {
              statFs -= 8;
              n.style.fontSize = statFs + "px";
            }
            num.textContent = fmt(0);
            if (instant) {  // hook scene: the stat is part of the cover frame
              card.style.opacity = "1";
              tl.fromTo(card, { scale: 0.94 }, { scale: 1, duration: 0.36, ease: "power3.out" }, 0);
            } else {
              tl.fromTo(card, { opacity: 0, y: 40, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: "back.out(1.8)", immediateRender: false }, t);
            }
            A.countText(tl, num, instant ? v : 0, v, instant ? 0.25 : t + 0.05, 1.2, fmt);
            return card;
          }
          function boxAt(parent, r, pad, cls) {
            const b = A.mk("div", cls, parent);
            Object.assign(b.style, { left: r.x - pad + "px", top: r.y - pad + "px", width: r.w + 2 * pad + "px", height: r.h + 2 * pad + "px" });
            b.setAttribute("data-layout-allow-overlap", "");
            return b;
          }
          function typeText(el, text, a, z) {
            const n = Math.max(1, Math.round((z - a) * 30));
            for (let f = 0; f <= n; f++) tl.set(el, { textContent: text.slice(0, Math.round((text.length * f) / n)) }, a + f / 30);
          }

          // ---------------------------------------------------------------- scenes
          function sClip(s, root, t0, t1) {
            const vs = A.$("#vs-" + s.id);
            const card = vs ? vs.querySelector(".sp-vcard") : null;
            let cardTop = COVER_STAGE_TOP;  // hook layout: headline box 236-616, sub from 616, card below it
            if (s.headline) {
              A.mk("div", "sp-scrim", root);
              const h = A.mk("div", "sp-headline display", root);
              richText(h, s.headline);
              A.fit(h, { max: 200, min: 80, maxH: 380 });  // maxH must equal the box height (scrollHeight >= clientHeight)
              if (s.id === FIRST) tl.fromTo(h, { scale: 1.1 }, { scale: 1, duration: 0.45, ease: "power3.out" }, 0);  // already visible on frame 0 (cover)
              else tl.fromTo(h, { opacity: 0, scale: 1.15 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, t0);
              if (s.sub) {
                const sub = A.mk("div", "sp-sub", root, s.sub);
                A.fit(sub, { max: 54, min: 42, maxH: 66 });                                   // one line if it fits at >= 42 px
                if (sub.scrollHeight > 66) A.fit(sub, { max: 54, min: 40, maxH: 124 });      // else two lines
                cardTop = Math.max(700, Math.ceil(616 + sub.scrollHeight + 26));
                if (s.id === FIRST) sub.style.opacity = "1";  // the cover frame shows headline + sub
                else tl.fromTo(sub, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.28, immediateRender: false }, t0 + 0.3);
              }
            }
            if (vs) {
              showSet(vs, t0, t1, s.id === FIRST);
              if (s.headline) {
                card.classList.add("bleed");
                // The card zooms to 1.045 while it is on screen (see the tween below). Reserving
                // that growth keeps the scaled box on the stage floor instead of 10-18 px past it
                // into the caption band (audit, 2026-10-20).
                Object.assign(card.style, { left: "0px", top: cardTop + "px", width: "1080px",
                                            height: Math.min(608, Math.floor((STAGE_BOTTOM - cardTop) / 1.045)) + "px",
                                            transformOrigin: "center top" });
              } else {
                const ar = parseFloat(card.getAttribute("data-ar") || "0.5625");
                if (ar > 0.62) {  // tall / phone footage: card follows the source aspect inside 180-1220 (captions at 1330), no crop
                  let W = 960, H = W * ar;
                  if (H > 1040) { H = 1040; W = H / ar; }
                  Object.assign(card.style, { left: Math.round((1080 - W) / 2) + "px", top: Math.round(180 + (1040 - H) / 2) + "px",
                                              width: Math.round(W) + "px", height: Math.round(H) + "px" });
                }
              }
              tl.fromTo(card, { scale: 1 }, { scale: 1.045, duration: Math.max(0.1, t1 - t0), ease: "none", immediateRender: false }, t0);
            }
            credit(root, s.headline ? cardTop + 638 : 1118, t0 + 0.4);
          }
          function sMontage(s, root, t0, t1) {
            const cuts = s.cuts || [];
            cuts.forEach((c, k) => {
              const a = E(`${s.id}_cut${k}`), z = k + 1 < cuts.length ? E(`${s.id}_cut${k + 1}`) : t1;
              const vs = A.$(`#vs-${s.id}-${k}`);
              if (vs) {
                showSet(vs, a, z, false);
                const card = vs.querySelector(".sp-vcard");
                if (k > 0) tl.fromTo(card, { x: 1100, filter: "blur(12px)" }, { x: 0, filter: "blur(0px)", duration: 0.24, ease: "power4.out", immediateRender: false }, a);
                tl.fromTo(card, { scale: 1 }, { scale: 1.05, duration: Math.max(0.1, z - a), ease: "none", immediateRender: false }, a);
              }
              const chip = A.mk("div", "sp-chip", root, c.label || "");
              chip.style.top = "430px";
              tl.fromTo(chip, { opacity: 0, y: 20, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.22, ease: "back.out(2.5)", immediateRender: false }, a + 0.08);
              if (k + 1 < cuts.length) tl.set(chip, { opacity: 0 }, z);
            });
            credit(root, 1118, t0 + 0.2);
          }
          function sPage(s, root, t0, t1) {
            const cover = s.id === FIRST;
            heading(root, s.heading || prettyName(), t0 + 0.05, { instant: cover });
            const B = browser(root, { top: cover ? COVER_STAGE_TOP : STAGE_TOP,
                                     height: cover ? COVER_STAGE_HEIGHT : STAGE_BOTTOM - STAGE_TOP,
                                     url: s.display_url || s.url || X.display_url || X.url, img: s.img, instant: cover });
            const cams = s.camera || [];
            const states = [B.state(null, 1)].concat(cams.map((c) => B.state(c.region, c.zoom || 1.6)));
            const times = [t0].concat(cams.map((c, k) => E(`${s.id}_cam${k}`)));
            const segs = camPlan(B, states, times, t1);
            camApply(B.page, segs);
            (s.cursor || []).forEach((c, k) => cursorClick(root, B, segs, c.region, E(`${s.id}_click${k}`), c.state !== undefined ? c.state : c.region === "star_button" ? "★ Starred" : ""));
            if (s.stat) statBadge(root, s.stat, E(`${s.id}_stat`));
          }
          function sScroll(s, root, t0, t1) {
            const cover = s.id === FIRST;
            const title = s.heading || (cover ? prettyName() : "");
            if (title) heading(root, title, t0 + 0.05, { instant: cover });
            const top = title ? (cover ? COVER_STAGE_TOP : STAGE_TOP) : 300;
            const height = title ? (cover ? COVER_STAGE_HEIGHT : STAGE_BOTTOM - STAGE_TOP) : STAGE_BOTTOM - 300;
            const B = browser(root, { top, height, url: s.display_url || s.url || X.display_url || X.url, img: s.img, instant: cover });
            const stops = s.stops || [];
            const states = [B.state(s.start_region || null, s.start_zoom || 1)].concat(stops.map((st) => B.state(st.region, st.zoom || 1.3)));
            const times = [t0].concat(stops.map((st, k) => E(`${s.id}_stop${k}`)));
            const segs = camPlan(B, states, times, t1);
            camApply(B.page, segs);
            stops.forEach((st, k) => {
              const r = R[st.region];
              if (!r) return;
              const tk = times[k + 1] + 0.55, next = k + 1 < stops.length ? times[k + 2] : t1;
              const box = boxAt(B.page, r, 10, "sp-hlbox");
              tl.fromTo(box, { opacity: 0 }, { opacity: 1, duration: 0.22, immediateRender: false }, tk);
              if (next < t1 - 0.01) tl.fromTo(box, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, next - 0.05);
              if (st.label) {
                const chip = A.mk("div", "sp-chip", root, st.label);
                chip.style.top = B.top + 26 + "px";
                tl.fromTo(chip, { opacity: 0, y: -16, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.25, ease: "back.out(2.4)", immediateRender: false }, tk);
                if (next < t1 - 0.01) tl.set(chip, { opacity: 0 }, next);
              }
            });
          }
          function sSteps(s, root, t0, t1) {
            heading(root, s.heading || "HOW IT *WORKS*", t0 + 0.05, { instant: s.id === FIRST });
            const bg = s.background || {};
            if (bg.img) {
              const cover = s.id === FIRST;
              // Keep an optional screenshot below the large hook title and above the steps card.
              const B = browser(root, { top: cover ? COVER_STAGE_TOP : 452,
                                       height: cover ? 180 : 430, url: s.display_url || s.url || X.display_url || X.url, img: bg.img });
              const regs = bg.scroll_regions || [];
              const z = bg.zoom || 1.0;
              const a0 = B.state(regs[0] || null, z), a1 = regs[1] ? B.state(regs[1], z) : B.state(null, z, 0.25);
              tl.fromTo(B.page, a0, { ...a1, duration: Math.max(0.1, t1 - t0), ease: "sine.inOut", immediateRender: false }, t0);
              if (s.fig) {
                const fig = A.mk("div", "sp-fig", B.vp);
                const im = A.mk("img", "", fig);
                im.src = "assets/" + s.fig.file;
                tl.fromTo(fig, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 0.35, ease: "power2.out", immediateRender: false }, E(`${s.id}_figure`, t0 + 1));
              }
            }
            const list = A.mk("div", "sp-steps", root);
            if (s.id === FIRST) {
              list.style.top = Math.max(COVER_STAGE_TOP, STAGE_BOTTOM - 356) + "px";  // sits below the cover headline
              list.style.opacity = "1";  // hook scene: steps visible on frame 0
            }
            else tl.fromTo(list, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, t0 + 0.1);
            const steps = s.steps || [];
            steps.forEach((txt, k) => {
              const row = A.mk("div", "sp-step", list);
              const on = A.mk("div", "on", row);
              on.setAttribute("data-layout-allow-overlap", "");
              A.mk("span", "num", row, String(k + 1));
              A.mk("span", "tx", row, txt);
              const tk = E(`${s.id}_step${k}`), tn = k + 1 < steps.length ? E(`${s.id}_step${k + 1}`) : t1;
              tl.fromTo(row, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: 0.25, ease: "power3.out", immediateRender: false }, tk);
              tl.fromTo(on, { opacity: 0 }, { opacity: 1, duration: 0.12, immediateRender: false }, tk);
              if (tn < t1 - 0.01) tl.fromTo(on, { opacity: 1 }, { opacity: 0, duration: 0.15, immediateRender: false }, Math.max(tk + 0.2, tn - 0.05));
            });
          }
          function sTerminal(s, root, t0, t1) {
            const lines = s.lines || [];
            heading(root, s.heading || `SETUP: *${lines.length}* COMMANDS`, t0 + 0.05, { instant: s.id === FIRST });
            const term = A.mk("div", "sp-term", root);
            if (s.id === FIRST) term.style.top = COVER_STAGE_TOP + "px";  // title band is 236-616
            const termTop = s.id === FIRST ? COVER_STAGE_TOP : 480;
            term.style.height = Math.max(240, Math.min(560, STAGE_BOTTOM - termTop, 230 + lines.length * 150)) + "px";
            const bar = A.mk("div", "sp-bar", term);
            dots(bar);
            A.mk("div", "sp-term-title", term, s.title || "Terminal");
            const body = A.mk("div", "sp-term-body", term);
            if (s.id === FIRST) {  // hook scene: the window is on frame 0
              term.style.opacity = "1";
              tl.fromTo(term, { scale: 0.97 }, { scale: 1, duration: 0.32, ease: "power3.out" }, 0);
            } else {
              tl.fromTo(term, { opacity: 0, y: 40, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "power3.out", immediateRender: false }, t0 + 0.08);
            }
            lines.forEach((line, k) => {
              const a = E(`${s.id}_type${k}`), z = E(`${s.id}_type${k}_end`);
              const row = A.mk("div", "sp-tl", body);
              row.style.opacity = "0";
              A.mk("span", "p", row, (s.prompt || "❯") + " ");
              const tx = A.mk("span", "", row, "");
              const caret = A.mk("span", "sp-caret", row);
              tl.set(row, { opacity: 1 }, a - 0.05);
              typeText(tx, line, a, z);
              tl.set(caret, { opacity: 0 }, z + 0.12);
              const out = A.mk("div", "sp-out", body, "✓ " + ((s.outputs || [])[k] || "done"));
              tl.fromTo(out, { opacity: 0 }, { opacity: 1, duration: 0.15, immediateRender: false }, z + 0.15);
            });
          }
          function sVerdict(s, root, t0, t1) {
            const cover = s.id === FIRST;
            heading(root, s.heading || "THE *CATCH*", t0 + 0.05, { instant: cover });
            // An `evidence` list means the camera has to walk between proofs, so the page keeps the
            // upper stage and the cards sit below it instead of covering the evidence.
            const evList = Array.isArray(s.evidence) ? s.evidence : null;
            const hasEv = Boolean(evList && evList.some((e) => e && e.region));
            const bTop = cover ? COVER_STAGE_TOP : 452;
            const bH = cover ? COVER_STAGE_HEIGHT : (hasEv ? 420 : STAGE_BOTTOM - STAGE_TOP);
            if (s.img && s.region) {
              const B = browser(root, { top: bTop, height: bH,
                                       url: s.display_url || s.url || X.display_url || X.url, img: s.img, instant: cover });
              // 2026-10-20: the dim used to fade in 0.5 s late, so every catch scene opened on a
              // full-stage sheet of white in the middle of a dark film. It is on from frame one now.
              const dim = A.mk("div", "sp-dim", B.vp);
              tl.set(dim, { opacity: 0.35 }, t0);
              // Evidence callout: the region the line is talking about stays bright while the rest
              // of the page falls away, so the proof reads instead of a grey slab.
              const ring = A.mk("div", "sp-ring", B.page);
              ring.style.opacity = "0";  // shown only when a real evidence region is on the page
              const itemTimes = [];
              (s.order || ["cons", "pros"]).forEach((grp) => (s[grp] || []).forEach((_, k) => itemTimes.push(E(`${s.id}_${grp}${k}`, t0 + 0.5))));
              const ringTo = (r) => ({ left: (r.x - 12) + "px", top: (r.y - 12) + "px",
                                       width: (r.w + 24) + "px", height: (r.h + 24) + "px" });
              const first = (evList && evList.find((e) => e && e.region && B.regions[e.region])) ||
                            { region: s.region, zoom: s.zoom };
              let cur = B.state(first.region, first.zoom || 1.6);
              tl.set(B.page, { ...cur }, t0);
              const r0 = B.regions[first.region];
              if (r0 && r0.w > 0) {
                Object.assign(ring.style, ringTo(r0));
                // on screen at the first frame of the scene: a callout that fades in leaves the
                // full-brightness page behind it for half a second, which is the white flash.
                tl.set(ring, { opacity: 1 }, t0);
                tl.fromTo(ring, { scale: 1.05 }, { scale: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, t0);
              }
              const moves = (evList || []).map((e, k) => ({ e, k }))
                .filter(({ e, k }) => k > 0 && e && e.region && B.regions[e.region] && B.regions[e.region].w > 0);
              moves.forEach(({ e, k }, n) => {
                const at = Math.max(t0 + 0.5, itemTimes[k] !== undefined ? itemTimes[k] : t0 + 0.9 * k);
                const nxt = B.state(e.region, e.zoom || 1.6);
                tl.to(B.page, { ...nxt, duration: 0.55, ease: "power2.inOut", immediateRender: false }, at - 0.1);
                tl.to(ring, { ...ringTo(B.regions[e.region]), duration: 0.55, ease: "power2.inOut", immediateRender: false }, at - 0.1);
                if (n === moves.length - 1) {  // a slow drift keeps the frame alive until the next scene
                  tl.to(B.page, { ...B.drift(nxt, 1.03), duration: Math.max(0.2, t1 - (at + 0.45)), ease: "none",
                                  immediateRender: false }, at + 0.45);
                }
                cur = nxt;
              });
              if (!moves.length) {
                tl.to(B.page, { ...B.drift(cur, 1.03), duration: Math.max(0.1, t1 - t0), ease: "none",
                                immediateRender: false }, t0 + 0.02);
              }
            }
            // Evidence mode keeps the page on screen, so only ONE card may be up at a time: two
            // stacked cards ran 898→1372 and crossed into the caption zone (2026-10-20). The catch
            // card swaps to the good card exactly when the script starts listing the upside.
            const groups = (s.order || ["cons", "pros"]).filter((g) => (s[g] || []).length);
            let y = cover ? COVER_STAGE_TOP : (hasEv ? bTop + bH + 26 : 486);
            groups.forEach((grp, gi) => {
              const items = s[grp] || [];
              const card = A.mk("div", "sp-vcardx " + grp, root);
              card.style.top = y + "px";
              A.mk("div", "sp-vt", card, grp === "cons" ? s.cons_title || "⚠ The catch" : s.pros_title || "✓ The good");
              items.forEach((txt, k) => {
                const it = A.mk("div", "sp-vi", card);
                A.mk("span", "ic", it, grp === "cons" ? "⚠️" : "✅");
                A.mk("span", "", it, txt);
                tl.fromTo(it, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.22, ease: "power3.out", immediateRender: false }, E(`${s.id}_${grp}${k}`, t0 + 0.5 + k * 0.6));
              });
              const cardAt = E(`${s.id}_${grp}_card`, t0 + 0.3);
              tl.fromTo(card, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.25, ease: "power3.out", immediateRender: false }, cardAt);
              if (hasEv && gi + 1 < groups.length) {
                // hide just before the upside card arrives, so the two never share a frame
                const nextAt = E(`${s.id}_${groups[gi + 1]}_card`, E(`${s.id}_${groups[gi + 1]}0`, t0 + 1.1)) - 0.3;
                tl.to(card, { opacity: 0, y: -26, duration: 0.2, ease: "power2.in", immediateRender: false }, Math.max(cardAt + 0.3, nextAt));
              }
              if (!hasEv) y += card.offsetHeight + 24;
            });
          }
          function sStat(s, root, t0, t1) {
            const cover = s.id === FIRST;
            heading(root, s.heading, t0 + 0.05, { instant: cover });
            const card = statBadge(root, s, E(`${s.id}_stat`, t0 + 0.3), true, cover);
            if (cover && !s.top) card.style.top = COVER_STAGE_TOP + "px";
          }
          function sImageStill(s, root, t0, t1) {
            const cover = s.id === FIRST;
            heading(root, s.heading, t0 + 0.05, { instant: cover });
            let cardTop = cover ? COVER_STAGE_TOP : 470;  // 470 = .sp-imgcard default top
            if (s.sub) {  // static cover line under the heading (karaoke captions hold until the first sentence ends)
              const sub = A.mk("div", "sp-sub", root, s.sub);
              sub.style.top = cover ? "616px" : "436px";
              A.fit(sub, { max: 54, min: 42, maxH: 66 });
              if (sub.scrollHeight > 66) A.fit(sub, { max: 54, min: 40, maxH: 124 });
              if (cover) {
                cardTop = Math.max(COVER_STAGE_TOP, Math.ceil(616 + sub.scrollHeight + 26));
                sub.style.opacity = "1";  // cover frame: sub is part of the design, no fade
              } else {
                // Non-cover: the card must start BELOW the sub. The fixed 470px card top
                // overlapped any sub taller than ~8px (sub at 436 + up to 124px tall).
                cardTop = Math.max(470, Math.ceil(436 + sub.scrollHeight + 26));
                tl.fromTo(sub, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.28, immediateRender: false }, t0 + 0.3);
              }
            }
            const card = A.mk("div", "sp-imgcard", root);
            if (cover || s.sub) card.style.top = cardTop + "px";
            // The image card must end above the caption zone in every case; a fixed 640px
            // height pushed it to 1164 once the sub line moved it down.
            Object.assign(card.style, { top: cardTop + "px",
                                        height: Math.max(300, Math.min(640, STAGE_BOTTOM - cardTop)) + "px" });
            const inn = A.mk("div", "in", card);
            const im = A.mk("img", "", inn);
            im.src = "assets/" + s.img.file;
            if (cover) {  // frame 0 = the cover: card present below the large title + sub
              card.style.opacity = "1";
              tl.fromTo(card, { scale: 0.94 }, { scale: 1, duration: 0.36, ease: "power3.out" }, 0);
            } else {
              tl.fromTo(card, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.32, ease: "back.out(1.6)", immediateRender: false }, t0 + 0.05);
            }
            tl.fromTo(inn, { scale: 1 }, { scale: 1.07, duration: Math.max(0.1, t1 - t0), ease: "none", immediateRender: false }, t0);
            (s.chips || []).forEach((txt, k, arr) => {
              const chip = A.mk("div", "sp-chip dark", root, txt);
              chip.style.top = 1128 - (arr.length - k) * 0 + "px";
              const tk = t0 + 0.6 + k * ((t1 - t0 - 1.0) / Math.max(1, arr.length));
              tl.fromTo(chip, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.22, immediateRender: false }, tk);
              if (k + 1 < arr.length) tl.set(chip, { opacity: 0 }, t0 + 0.6 + (k + 1) * ((t1 - t0 - 1.0) / arr.length));
            });
          }
          // Crop-zoom on a still from the tool's OWN media. `focus` is a list of
          // {box:[x,y,w,h] as fractions of the image, at: seconds from scene start, pad}.
          // Each keyframe glides the image so that box fills the panel (the rest of
          // the screenshot is cut away). Nothing is drawn: it only moves real pixels.
          function focusMotion(im, PW, PH, iw, ih, focus, t0, t1) {
            const k = PW / iw, DH = ih * k, oy = (PH - DH) / 2;
            Object.assign(im.style, { position: "absolute", left: "0px", top: oy + "px",
                                      width: PW + "px", height: DH + "px", maxWidth: "none",
                                      maxHeight: "none", transformOrigin: "0 0" });
            focus.forEach((f, i) => {
              const [bx, by, bw, bh] = f.box;
              const cx = (bx + bw / 2) * iw * k, cy = (by + bh / 2) * ih * k;
              const z = Math.min(PW / (bw * iw * k), PH / (bh * ih * k)) * (f.pad || 0.9);
              const x = PW / 2 - cx * z, y = PH / 2 - oy - cy * z;
              const at = t0 + (f.at != null ? f.at : (i / focus.length) * (t1 - t0));
              tl.to(im, { x: x, y: y, scale: z, duration: 0.7, ease: "power2.inOut",
                          immediateRender: false }, at);
            });
          }
          function sImage(s, root, t0, t1) {
            if (s.focus && s.img) return sFocus(s, root, t0, t1);
            return sImageStill(s, root, t0, t1);
          }
          function sFocus(s, root, t0, t1) {
            const cover = s.id === FIRST;
            heading(root, s.heading, t0 + 0.05, { instant: cover });
            const cardTop = 470;
            const card = A.mk("div", "sp-imgcard", root);
            Object.assign(card.style, { top: cardTop + "px", height: "640px" });
            const inn = A.mk("div", "in", card);
            inn.style.overflow = "hidden";
            const im = A.mk("img", "", inn);
            im.src = "assets/" + s.img.file;
            focusMotion(im, 960, 640, s.img.w, s.img.h, s.focus, t0, t1);
            tl.fromTo(card, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.32,
                      ease: "back.out(1.6)", immediateRender: false }, t0 + 0.05);
            if (s.sub) {
              const sub = A.mk("div", "sp-sub", root, s.sub);
              sub.style.top = "436px";
              A.fit(sub, { max: 54, min: 42, maxH: 66 });
              tl.fromTo(sub, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.28, immediateRender: false }, t0 + 0.3);
            }
          }
          // Side-by-side panels. Each panel: a crop-zoom of the tool's own UI (left/right
          // {image, img, focus, label, levels}) and an animated level bar drawn from the
          // real audio envelope (levels = 15 Hz RMS of the reference or the cloned voice).
          function sSplit(s, root, t0, t1) {
            heading(root, s.heading, t0 + 0.05);
            const top = 470, PH = 380, PW = 460, BAR_BASE = 1100, BAR_MAX = 170, N = 36;
            [s.left, s.right].forEach((p, pi) => {
              if (!p) return;
              const x = pi === 0 ? 60 : 560;
              const card = A.mk("div", "sp-imgcard", root);
              Object.assign(card.style, { left: x + "px", width: PW + "px", top: top + "px", height: PH + "px" });
              const inn = A.mk("div", "in", card);
              inn.style.overflow = "hidden";
              const im = A.mk("img", "", inn);
              im.src = "assets/" + p.img.file;
              focusMotion(im, PW, PH, p.img.w, p.img.h, p.focus || [{ box: [0, 0, 1, 1] }], t0, t1);
              tl.fromTo(card, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.32,
                        ease: "back.out(1.6)", immediateRender: false }, t0 + 0.05 + 0.1 * pi);
              const lab = A.mk("div", "sp-chip dark", root, p.label || "");
              lab.style.top = (BAR_BASE - BAR_MAX - 60) + "px";
              lab.style.left = (x + 10) + "px";
              lab.style.transform = "none";
              const bars = [];
              for (let j = 0; j < N; j++) {
                const b = A.mk("div", "sp-bar", root);
                b.style.left = (x + 10 + j * ((PW - 20) / N)) + "px";
                b.style.width = ((PW - 20) / N - 5) + "px";
                b.style.top = BAR_BASE + "px";
                bars.push(b);
              }
              const lv = p.levels || [];
              if (lv.length) {
                const step = 1 / 12;
                for (let st = 0; t0 + st * step < t1 - 0.05; st++) {
                  const tt = t0 + st * step;
                  bars.forEach((b, j) => {
                    const v = lv[(st + j * 2) % lv.length];
                    const h = 8 + v * BAR_MAX;
                    tl.set(b, { height: h, top: BAR_BASE - h }, tt);
                  });
                }
              }
            });
          }
          function sEnd(s, root, t0, t1) {
            const q = s.question || firstQuestion(s.say);
            if (q) {
              const qe = A.mk("div", "sp-question display", root);
              richText(qe, q);
              A.fit(qe, { max: 120, min: 56, maxH: 330 });
              tl.fromTo(qe, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, t0 + 0.05);
            }
            if (s.keyword) {
              const kw = A.mk("div", "sp-chip sp-kw", root, `COMMENT “${s.keyword}” 👇`);
              tl.fromTo(kw, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2.6)", immediateRender: false }, E(`${s.id}_keyword`, t0 + 1));
            }
            A.endCard(tl, E("follow_in", t0 + 1.2), null);
          }

          const BUILD = { clip: sClip, "clip-montage": sMontage, page: sPage, scroll: sScroll, steps: sSteps, terminal: sTerminal,
                          verdict: sVerdict, stat: sStat, image: sImage, split: sSplit, endcard: sEnd };
          for (const s of X.scenes || []) {
            const fn = BUILD[s.type];
            if (!fn) { console.warn("spotlight: unknown scene type " + s.type); continue; }
            const t0 = E(s.id + "_in", 0), t1 = E(s.id + "_out", A.D);
            const root = A.mk("div", "scene sp-scene sc-" + s.type, stage);
            root.id = "s-" + s.id;
            enter(root, t0, t1, s.id === FIRST);
            fn(s, root, t0, t1);
          }
          if (typeof archetypeChrome === "function") archetypeChrome(tl, A, X);
        }
