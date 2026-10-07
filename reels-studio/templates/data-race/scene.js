        // ================= data-race scene =================
        async function buildScene(tl, V) {
          const { $, $$, mk, svg, seg, ev, fit, words, karaoke, show, flash, shake, countText, endCard, DATA } = V;
          const C = DATA.content;
          const S = C.series;
          const YEARS = DATA.extra.years;
          const pre = C.unit_prefix === undefined ? "$" : C.unit_prefix;
          const suf = C.unit_suffix || "";
          const fmt = (v) => pre + Math.round(v).toLocaleString("en-US") + suf;
          const A = ev("anchors");
          const tOf = (y) => {
            if (y <= A[0][1]) return A[0][0];
            for (let k = 0; k < A.length - 1; k++) {
              const [t0, y0] = A[k], [t1, y1] = A[k + 1];
              if (y0 <= y && y <= y1 && y1 > y0) return t0 + ((t1 - t0) * (y - y0)) / (y1 - y0);
            }
            return A[A.length - 1][0];
          };

          // ---- hook
          $("#hook-kicker").textContent = C.kicker || "DATA STORY";
          const ht = $("#hook-text");
          ht.textContent = C.hook_display || C.hook;
          fit(ht, { max: 150, min: 64, maxH: 500 });
          const hw = words(ht);
          const flags = $("#hook-flags");
          const hf = S.map((s) => {
            const c = mk("div", "card hflag", flags);
            mk("div", "f", c, s.flag || "●");
            const n = mk("div", "n", c, s.name);
            fit(n, { max: 38, min: 24, maxH: 60 });
            return c;
          });
          $("#hook-sub").textContent = C.hook_sub || `${DATA.extra.first} → ${DATA.extra.last}`;
          const tChart = ev("chart_in");
          show(tl, "#hook", 0, tChart, { inFrom: { opacity: 0, scale: 1.12 }, inDur: 0.2 });
          tl.fromTo("#hook-kicker", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, 0.1);
          karaoke(tl, hw, "hook");
          hf.forEach((c, k) => tl.fromTo(c, { opacity: 0, y: 80, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, 0.5 + k * 0.18));
          tl.fromTo("#hook-sub", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, Math.max(1.0, seg("hook").end - 0.6));
          flash(tl, 0.04, 0.45, 0.3);

          // ---- chart geometry
          const PX0 = 150, PX1 = 760, PY0 = 660, PY1 = 1300;
          const vmax = Math.max(...S.flatMap((s) => YEARS.map((y) => s.values[String(y)])));
          const step = [1, 2, 2.5, 5, 10].map((m) => m * Math.pow(10, Math.floor(Math.log10(vmax / 4)))).find((st) => vmax / st <= 5);
          const top = Math.ceil((vmax * 1.04) / step) * step;
          const X = (y) => PX0 + ((y - YEARS[0]) / (YEARS[YEARS.length - 1] - YEARS[0])) * (PX1 - PX0);
          const Y = (v) => PY1 - (v / top) * (PY1 - PY0);
          const short = (v) => (v >= 1e9 ? pre + (v / 1e9).toFixed(v % 1e9 ? 1 : 0) + "B" : v >= 1e6 ? pre + (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + "M" : v >= 1e3 ? pre + (v / 1e3).toFixed(v % 1e3 ? 1 : 0) + "k" : pre + v) + suf;
          const g = $("#chart");
          for (let v = 0; v <= top + 1e-9; v += step) {
            svg("line", { x1: PX0, x2: PX1 + 20, y1: Y(v), y2: Y(v), class: "gridline" }, g);
            const t = svg("text", { x: PX0 - 18, y: Y(v) + 10, "text-anchor": "end", class: "axis-label" }, g);
            t.textContent = short(v);
          }
          const midYear = YEARS[Math.floor(YEARS.length / 2)];
          [YEARS[0], midYear, YEARS[YEARS.length - 1]].forEach((y, k) => {
            const t = svg("text", { x: X(y), y: PY1 + 52, "text-anchor": k === 0 ? "start" : k === 2 ? "end" : "middle", class: "axis-label" }, g);
            t.textContent = String(y);
          });
          $("#chart-title").textContent = C.title || "";
          fit($("#chart-title"), { max: 64, min: 36, maxH: 80 });
          $("#chart-sub").textContent = C.subtitle || "";
          $("#chart-source").textContent = C.source_note || "Source: World Bank Open Data (CC BY 4.0)";

          // ---- show chart scene
          const tRank = ev("rank_in");
          show(tl, "#chart-scene", tChart, tRank, { inFrom: { opacity: 0, y: 60 } });
          const yearEl = $("#chart-year");
          yearEl.textContent = String(YEARS[0]);
          YEARS.forEach((y) => tl.set(yearEl, { textContent: String(y) }, Math.max(tChart + 0.01, tOf(y))));

          // ---- live leaderboard: one pill per series, moves between rank slots when the order changes
          const NS = S.length, GAP = 20, PW = (900 - GAP * (NS - 1)) / NS;
          const slotX = (r) => r * (PW + GAP);
          const board = $("#board");
          const ORD = ["1ST", "2ND", "3RD", "4TH", "5TH", "6TH"];
          for (let r = 0; r < NS; r++) {
            const l = mk("div", "slot-lab", board, r === 0 ? "👑 " + ORD[r] : ORD[r]);
            l.style.left = slotX(r) + "px";
            l.style.width = PW + "px";
          }
          const rankAt = YEARS.map((y) => {
            const order = S.map((s, k) => k).sort((p, q) => S[q].values[String(y)] - S[p].values[String(y)]);
            const r = [];
            order.forEach((k, i) => (r[k] = i));
            return r;
          });
          const flagHost = $("#chart-flags");
          S.forEach((s, k) => {
            const pts = YEARS.map((y) => [X(y), Y(s.values[String(y)])]);
            const cum = [0];
            for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
            const L = cum[cum.length - 1] + 1;
            const path = svg("path", { d: "M" + pts.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" L"), class: "line", stroke: s.color }, g);
            path.style.strokeDasharray = `${L} ${L}`;
            path.style.strokeDashoffset = String(L);
            const head = svg("circle", { cx: 0, cy: 0, r: 15, class: "head", fill: s.color }, g);
            const fl = mk("div", "hflag-sm", flagHost, s.flag || "");
            fl.setAttribute("data-layout-allow-overlap", "");
            const pill = mk("div", "card pill", board);
            pill.setAttribute("data-layout-allow-overlap", "");
            pill.style.width = PW + "px";
            pill.style.borderColor = s.color;
            mk("span", "f", pill, s.flag || "");
            const val = mk("span", "v", pill, fmt(s.values[String(YEARS[0])]));
            val.style.color = s.color;
            fit(val, { max: 46, min: 28, maxH: 70 });

            const t0 = tChart + 0.2 + k * 0.1;
            tl.fromTo(head, { x: pts[0][0], y: pts[0][1], scale: 0, opacity: 0 }, { x: pts[0][0], y: pts[0][1], scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)", immediateRender: false }, t0);
            tl.fromTo(fl, { x: pts[0][0] + 22, y: pts[0][1] - 62, opacity: 0 }, { x: pts[0][0] + 22, y: pts[0][1] - 62, opacity: 1, duration: 0.3, immediateRender: false }, t0);
            tl.fromTo(pill, { x: slotX(rankAt[0][k]), y: 24, opacity: 0 }, { x: slotX(rankAt[0][k]), y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, t0);
            for (let i = 1; i < pts.length; i++) {
              const ta = Math.max(tChart + 0.5, tOf(YEARS[i - 1]));
              const tb = Math.max(ta + 1 / 30, tOf(YEARS[i]));
              const d = tb - ta;
              tl.fromTo(path, { strokeDashoffset: L - cum[i - 1] }, { strokeDashoffset: L - cum[i], duration: d, ease: "none", immediateRender: false }, ta);
              tl.fromTo(head, { x: pts[i - 1][0], y: pts[i - 1][1] }, { x: pts[i][0], y: pts[i][1], duration: d, ease: "none", immediateRender: false }, ta);
              tl.fromTo(fl, { x: pts[i - 1][0] + 22, y: pts[i - 1][1] - 62 }, { x: pts[i][0] + 22, y: pts[i][1] - 62, duration: d, ease: "none", immediateRender: false }, ta);
              tl.set(val, { textContent: fmt(s.values[String(YEARS[i])]) }, tb);
              if (rankAt[i][k] !== rankAt[i - 1][k]) {
                const nxt = i + 1 < YEARS.length ? Math.max(tb + 0.05, tOf(YEARS[i + 1])) : tb + 0.4;
                tl.fromTo(pill, { x: slotX(rankAt[i - 1][k]) }, { x: slotX(rankAt[i][k]), duration: Math.min(0.35, Math.max(0.1, nxt - tb)), ease: "power2.inOut", immediateRender: false }, tb);
              }
            }
          });
          ev("lead_changes").forEach(([, t]) => tl.fromTo("#chart-year", { opacity: 0.32 }, { opacity: 0.16, duration: 0.4, immediateRender: false }, t));

          // ---- final ranking
          const last = String(DATA.extra.last), first = String(DATA.extra.first);
          $("#rank-title").textContent = C.rank_title || `${last} RANKING`;
          const rows = $("#rank-rows");
          const sorted = S.map((s) => s).sort((a, b) => b.values[last] - a.values[last]);
          const vtop = sorted[0].values[last];
          const tCta = ev("cta_in");
          show(tl, "#rank", tRank, tCta, { inFrom: { opacity: 0, y: 70 } });
          sorted.forEach((s, k) => {
            const r = mk("div", "card rrow", rows);
            mk("div", "pos", r, String(k + 1));
            mk("div", "f", r, s.flag || "");
            const nm = mk("div", "name", r, s.name);
            const v = mk("div", "val", r, fmt(0));
            const bar = mk("div", "bar", r);
            const fill = mk("i", "", bar);
            fill.style.background = s.color;
            fill.style.width = ((100 * s.values[last]) / vtop).toFixed(1) + "%";
            const growth = s.values[last] / s.values[first];
            mk("div", "grow", r, `×${growth.toFixed(1)} since ${first}`);
            const t = tRank + 0.25 + k * 0.32;
            tl.fromTo(r, { opacity: 0, x: 120 }, { opacity: 1, x: 0, duration: 0.35, ease: "back.out(1.8)", immediateRender: false }, t);
            tl.fromTo(fill, { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: "power3.out", immediateRender: false }, t + 0.15);
            countText(tl, v, 0, s.values[last], t + 0.15, 0.8, fmt);
          });
          $("#rank-source").textContent = C.source_note || "Source: World Bank Open Data (CC BY 4.0)";
          endCard(tl, tCta + 0.3, null);
        }
