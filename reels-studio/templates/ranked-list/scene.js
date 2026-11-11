        // ================= ranked-list scene =================
        async function buildScene(tl, V) {
          const { $, $$, mk, seg, ev, fit, words, karaoke, show, flash, shake, countText, endCard, rnd, DATA } = V;
          const C = DATA.content;
          const ITEMS = DATA.extra.items;
          const N = ITEMS.length;
          const icon = C.metric_icon || "⭐";
          const k = (v) => (v >= 1e6 ? (v / 1e6).toFixed(1) + "M" : v >= 1e3 ? (v / 1e3).toFixed(1) + "k" : String(Math.round(v)));
          const full = (v) => Math.round(v).toLocaleString("en-US");
          const vmax = Math.max(...ITEMS.map((it) => it.value));
          const PALETTE = ["#a78bfa", "#f472b6", "#38bdf8", "#facc15", "#34d399", "#fb923c"];

          // ---- hook
          $("#hook-kicker").textContent = C.kicker || "TOP " + N;
          const ht = $("#hook-text");
          ht.textContent = C.hook_display || C.hook;
          fit(ht, { max: 160, min: 70, maxH: 600 });
          const hw = words(ht);
          $("#hook-sub").textContent = C.sub || "";
          show(tl, "#hook", 0, ev("i0_in"), { inFrom: { opacity: 0, scale: 1.15 }, inDur: 0.2 });
          tl.fromTo("#hook-kicker", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, 0.1);
          karaoke(tl, hw, "hook");
          if (C.sub) tl.fromTo("#hook-sub", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, Math.max(0.8, seg("hook").end - 0.6));
          shake(tl, "#hook-box", 0.05, 16, 7);
          flash(tl, 0.04, 0.5, 0.3);

          // ---- items (countdown) + mini leaderboard
          const host = $("#items");
          const board = $("#board");
          ITEMS.forEach((it, i) => {
            const color = it.color || PALETTE[i % PALETTE.length];
            const isOne = i === N - 1;
            const sc = mk("section", "scene item", host);
            const rk = mk("div", "rank", sc);
            rk.innerHTML = `#<b>${it.rank}</b>`;
            const mono = mk("div", "mono", sc, it.mono || it.name.slice(0, 2));
            mono.style.background = `linear-gradient(145deg, ${color}, #1b1030)`;
            const nm = mk("div", "name", sc, it.name);
            fit(nm, { max: 112, min: 56, maxH: 140 });
            const ln = mk("div", "line", sc, it.line);
            fit(ln, { max: 50, min: 32, maxH: 180 });
            const lw = words(ln);
            const st = mk("div", "card stat", sc);
            mk("div", "lab", st, `${icon} ${C.metric_label || ""}`);
            const num = mk("div", "num", st, "0");
            const bar = mk("div", "bar", st);
            const fill = mk("i", "", bar);
            fill.style.background = `linear-gradient(90deg, ${color}, var(--acc))`;
            fill.style.width = ((100 * it.value) / vmax).toFixed(1) + "%";
            if (it.tag) mk("div", "chip ghost tag", sc, it.tag);

            const tin = ev(`i${i}_in`), tout = ev(`i${i}_out`), tname = ev(`i${i}_name`), tstat = ev(`i${i}_stat`);
            show(tl, sc, tin, tout, { inFrom: { opacity: 0, x: 160 }, outTo: { opacity: 0, x: -160 }, inDur: 0.3 });
            tl.fromTo(rk, { scale: 2.2, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.24, ease: "power4.in", immediateRender: false }, tin + 0.06);
            shake(tl, sc, tin + 0.3, isOne ? 26 : 12, isOne ? 10 : 6);
            tl.fromTo(mono, { scale: 0, rotation: -25, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: 0.45, ease: "back.out(2.2)", immediateRender: false }, tin + 0.2);
            tl.fromTo(nm, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, tname - 0.05);
            karaoke(tl, lw, `item${i}`, ev(`i${i}_line_from`));
            tl.fromTo(st, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, tstat - 0.1);
            tl.fromTo(fill, { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "power3.out", immediateRender: false }, tstat);
            countText(tl, num, 0, it.value, tstat, 0.9, full);
            if (it.tag) tl.fromTo(sc.querySelector(".tag"), { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.25, immediateRender: false }, tstat + 0.5);
            if (isOne) {
              flash(tl, ev("one_hit"), 0.8, 0.35);
              const cf = $("#confetti");
              for (let p = 0; p < 26; p++) {
                const e = mk("i", "conf", cf);
                e.style.background = PALETTE[p % PALETTE.length];
                const a = rnd() * Math.PI * 2, dist = 260 + rnd() * 420;
                tl.fromTo(e, { x: 0, y: 0, rotation: 0, opacity: 1 },
                  { x: Math.cos(a) * dist, y: Math.sin(a) * dist + 260, rotation: rnd() * 540 - 270, opacity: 0, duration: 1.3, ease: "power2.out", immediateRender: false }, ev("one_hit") + 0.05 + p * 0.008);
              }
            } else {
              // row joins the leaderboard (rank N at the bottom, filling upwards)
              const row = mk("div", "card brow", board);
              row.style.top = (N - 2 - i) * 78 + "px";
              mk("span", "r", row, "#" + it.rank);
              mk("span", "n", row, it.name);
              mk("span", "v", row, `${icon} ${k(it.value)}`);
              tl.fromTo(row, { opacity: 0, x: -80, scale: 0.9 }, { opacity: 1, x: 0, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, ev(`i${i}_board`));
            }
          });

          // ---- CTA
          const tc = ev("cta_in");
          tl.fromTo("#board", { opacity: 1 }, { opacity: 0, duration: 0.25, immediateRender: false }, tc - 0.25);
          endCard(tl, tc + 0.1, null);
        }
