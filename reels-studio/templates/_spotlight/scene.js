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
          function richText(el, text) {  // *word* = yellow; otherwise caption keywords are yellow
            const explicit = /\*[^*]+\*/.test(text);
            const parts = String(text).split(/\s+/).filter(Boolean);
            const box = A.mk("span", "rt", el);  // single inline flex item: whitespace between words survives
            parts.forEach((w, i) => {
              const m = w.match(/^\*(.+?)\*(\S*)$/);
              const word = m ? m[1] + m[2] : w;
              A.mk("span", (explicit ? !!m : KEYS.has(norm(word))) ? "y" : "", box, word);
              if (i < parts.length - 1) box.appendChild(document.createTextNode(" "));
            });
          }
          function heading(root, text, t, o = {}) {
            if (!text) return null;
            const h = A.mk("div", "sp-heading display", root);
            if (o.top) h.style.top = o.top + "px";
            richText(h, text);
            A.fit(h, { max: o.max || 128, min: 56, maxH: o.maxH || 180 });
            tl.fromTo(h, { opacity: 0, scale: 1.12 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, t);
            return h;
          }
          function credit(root, y, t) {
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
            const bar = A.mk("div", "sp-bar", br);
            dots(bar);
            const url = A.mk("div", "sp-url", bar, String(o.url || "").replace(/^https?:\/\//, ""));
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
            const B = { br, vp, page, img, vpW, vpH, s0, left: 42, top: o.top + 66 };
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
          function statBadge(root, st, t, big) {
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
            tl.fromTo(card, { opacity: 0, y: 40, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: "back.out(1.8)", immediateRender: false }, t);
            A.countText(tl, num, 0, v, t + 0.05, 1.2, fmt);
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
            if (vs) {
              showSet(vs, t0, t1, s.id === FIRST);
              const card = vs.querySelector(".sp-vcard");
              if (s.headline) {
                card.classList.add("bleed");
                Object.assign(card.style, { left: "0px", top: "700px", width: "1080px", height: "608px" });
              }
              tl.fromTo(card, { scale: 1 }, { scale: 1.045, duration: Math.max(0.1, t1 - t0), ease: "none", immediateRender: false }, t0);
            }
            if (s.headline) {
              A.mk("div", "sp-scrim", root);
              const h = A.mk("div", "sp-headline display", root);
              richText(h, s.headline);
              A.fit(h, { max: 200, min: 80, maxH: 380 });  // maxH must equal the box height (scrollHeight >= clientHeight)
              if (s.id === FIRST) tl.fromTo(h, { scale: 1.1 }, { scale: 1, duration: 0.45, ease: "power3.out" }, 0);  // already visible on frame 0 (cover)
              else tl.fromTo(h, { opacity: 0, scale: 1.15 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, t0);
              if (s.sub) {
                const sub = A.mk("div", "sp-sub", root, s.sub);
                if (s.id === FIRST) sub.style.opacity = "1";  // the cover frame shows headline + sub
                else tl.fromTo(sub, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.28, immediateRender: false }, t0 + 0.3);
              }
            }
            credit(root, s.headline ? 1338 : 1118, t0 + 0.4);
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
              chip.style.top = "452px";
              tl.fromTo(chip, { opacity: 0, y: 20, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.22, ease: "back.out(2.5)", immediateRender: false }, a + 0.08);
              if (k + 1 < cuts.length) tl.set(chip, { opacity: 0 }, z);
            });
            credit(root, 1118, t0 + 0.2);
          }
          function sPage(s, root, t0, t1) {
            heading(root, s.heading || prettyName(), t0 + 0.05);
            const B = browser(root, { top: 452, height: 700, url: s.url || X.url, img: s.img });
            const cams = s.camera || [];
            const states = [B.state(null, 1)].concat(cams.map((c) => B.state(c.region, c.zoom || 1.6)));
            const times = [t0].concat(cams.map((c, k) => E(`${s.id}_cam${k}`)));
            const segs = camPlan(B, states, times, t1);
            camApply(B.page, segs);
            (s.cursor || []).forEach((c, k) => cursorClick(root, B, segs, c.region, E(`${s.id}_click${k}`), c.state !== undefined ? c.state : c.region === "star_button" ? "★ Starred" : ""));
            if (s.stat) statBadge(root, s.stat, E(`${s.id}_stat`));
          }
          function sScroll(s, root, t0, t1) {
            if (s.heading) heading(root, s.heading, t0 + 0.05);
            const top = s.heading ? 452 : 300;
            const B = browser(root, { top, height: 1152 - top, url: s.url || X.url, img: s.img });
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
            heading(root, s.heading || "HOW IT *WORKS*", t0 + 0.05);
            const bg = s.background || {};
            if (bg.img) {
              const B = browser(root, { top: 452, height: 430, url: s.url || X.url, img: bg.img });
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
            tl.fromTo(list, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, t0 + 0.1);
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
            heading(root, s.heading || `SETUP: *${lines.length}* COMMANDS`, t0 + 0.05);
            const term = A.mk("div", "sp-term", root);
            term.style.height = Math.min(560, 230 + lines.length * 150) + "px";  // fit the window to the commands
            const bar = A.mk("div", "sp-bar", term);
            dots(bar);
            A.mk("div", "sp-term-title", term, s.title || "Terminal");
            const body = A.mk("div", "sp-term-body", term);
            tl.fromTo(term, { opacity: 0, y: 40, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "power3.out", immediateRender: false }, t0 + 0.08);
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
            heading(root, s.heading || "THE *CATCH*", t0 + 0.05);
            if (s.img && s.region) {
              const B = browser(root, { top: 452, height: 700, url: s.url || X.url, img: s.img });
              const st = B.state(s.region, s.zoom || 1.15);
              tl.fromTo(B.page, st, { ...B.drift(st, 1.04), duration: Math.max(0.1, t1 - t0), ease: "none", immediateRender: false }, t0);
              const dim = A.mk("div", "sp-dim", B.vp);
              tl.fromTo(dim, { opacity: 0 }, { opacity: 1, duration: 0.4, immediateRender: false }, t0 + 0.5);
            }
            let y = 486;
            (s.order || ["cons", "pros"]).forEach((grp) => {
              const items = s[grp] || [];
              if (!items.length) return;
              const card = A.mk("div", "sp-vcardx " + grp, root);
              card.style.top = y + "px";
              A.mk("div", "sp-vt", card, grp === "cons" ? s.cons_title || "⚠ The catch" : s.pros_title || "✓ The good");
              items.forEach((txt, k) => {
                const it = A.mk("div", "sp-vi", card);
                A.mk("span", "ic", it, grp === "cons" ? "⚠️" : "✅");
                A.mk("span", "", it, txt);
                tl.fromTo(it, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.22, ease: "power3.out", immediateRender: false }, E(`${s.id}_${grp}${k}`, t0 + 0.5 + k * 0.6));
              });
              tl.fromTo(card, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.25, ease: "power3.out", immediateRender: false }, E(`${s.id}_${grp}_card`, t0 + 0.3));
              y += card.offsetHeight + 24;
            });
          }
          function sStat(s, root, t0, t1) {
            heading(root, s.heading, t0 + 0.05);
            statBadge(root, s, E(`${s.id}_stat`, t0 + 0.3), true);
          }
          function sImage(s, root, t0, t1) {
            heading(root, s.heading, t0 + 0.05);
            const card = A.mk("div", "sp-imgcard", root);
            const inn = A.mk("div", "in", card);
            const im = A.mk("img", "", inn);
            im.src = "assets/" + s.img.file;
            tl.fromTo(card, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.32, ease: "back.out(1.6)", immediateRender: false }, t0 + 0.05);
            tl.fromTo(inn, { scale: 1 }, { scale: 1.07, duration: Math.max(0.1, t1 - t0), ease: "none", immediateRender: false }, t0);
            (s.chips || []).forEach((txt, k, arr) => {
              const chip = A.mk("div", "sp-chip dark", root, txt);
              chip.style.top = 1128 - (arr.length - k) * 0 + "px";
              const tk = t0 + 0.6 + k * ((t1 - t0 - 1.0) / Math.max(1, arr.length));
              tl.fromTo(chip, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.22, immediateRender: false }, tk);
              if (k + 1 < arr.length) tl.set(chip, { opacity: 0 }, t0 + 0.6 + (k + 1) * ((t1 - t0 - 1.0) / arr.length));
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
                          verdict: sVerdict, stat: sStat, image: sImage, endcard: sEnd };
          for (const s of X.scenes || []) {
            const fn = BUILD[s.type];
            if (!fn) { console.warn("spotlight: unknown scene type " + s.type); continue; }
            const t0 = E(s.id + "_in", 0), t1 = E(s.id + "_out", A.D);
            const root = A.mk("div", "scene sp-scene sc-" + s.type, stage);
            root.id = "s-" + s.id;
            enter(root, t0, t1, s.id === FIRST);
            fn(s, root, t0, t1);
          }
        }
