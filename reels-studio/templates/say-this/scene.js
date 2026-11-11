        // ================= say-this scene =================
        async function buildScene(tl, V) {
          const { $, mk, seg, ev, fit, words, karaoke, show, flash, shake, endCard, DATA } = V;
          const C = DATA.content;
          const X = DATA.extra;
          const N = C.pairs.length;

          // ---- hook
          $("#hook-kicker").textContent = C.kicker || "SPOKEN ENGLISH";
          const ht = $("#hook-text");
          ht.textContent = C.hook_display || C.hook;
          fit(ht, { max: 160, min: 70, maxH: 580 });
          const hw = words(ht);
          const hu = $("#hook-ur");
          hu.textContent = C.hook_ur || "";
          if (C.hook_ur) fit(hu, { max: 66, min: 36, maxH: 200 });
          show(tl, "#hook", 0, ev("p0_in"), { inFrom: { opacity: 0, scale: 1.15 }, inDur: 0.2 });
          tl.fromTo("#hook-kicker", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, 0.1);
          karaoke(tl, hw, "hook");
          if (C.hook_ur) tl.fromTo(hu, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.35, immediateRender: false }, Math.max(0.7, seg("hook").end - 0.9));
          shake(tl, "#hook-box", 0.05, 14, 7);
          flash(tl, 0.04, 0.4, 0.3);

          // ---- pairs
          const host = $("#pairs");
          C.pairs.forEach((p, i) => {
            const sc = mk("section", "scene pair", host);
            const head = mk("div", "phead", sc);
            mk("span", "chip", head, `${i + 1}/${N}`);
            mk("span", "chip ghost", head, C.series_label || "DAILY ENGLISH");
            const bad = mk("div", "card pcard bad", sc);
            mk("div", "ico", bad, "✕");
            mk("div", "lab", bad, "DON'T SAY");
            const bt = mk("div", "txt", bad, p.wrong);
            bt.setAttribute("data-layout-allow-occlusion", ""); // audit checks the occluded text's ancestors
            fit(bt, { max: 68, min: 36, maxH: 90 });
            const bw = words(bt);
            bw.forEach((w) => w.setAttribute("data-layout-allow-occlusion", "")); // flag is read per text element (no ancestor walk)
            const strike = mk("div", "strike", bad);
            strike.setAttribute("data-layout-allow-overlap", "");
            strike.setAttribute("data-layout-allow-occlusion", ""); // the strike-through is meant to cross the words
            const good = mk("div", "card pcard good", sc);
            mk("div", "ico", good, "✓");
            mk("div", "lab", good, "SAY");
            const gt = mk("div", "txt", good, p.right);
            fit(gt, { max: 68, min: 36, maxH: 90 });
            const gw = words(gt);
            const uc = mk("div", "card ucard", sc);
            mk("div", "ulab", uc, C.ur_label || "اردو میں · IN URDU");
            const ut = mk("div", "utext urdu", uc, p.ur);
            fit(ut, { max: 54, min: 32, maxH: 230 });
            const uw = X.urdu_voice ? words(ut) : null; // read-along on the Urdu card when it is spoken

            const tin = ev(`p${i}_in`), tout = ev(`p${i}_out`);
            show(tl, sc, tin, tout, { inFrom: { opacity: 0, y: 80 }, outTo: { opacity: 0, y: -80 } });
            tl.fromTo(bad, { scale: 0.92 }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, tin + 0.05);
            karaoke(tl, bw, `w${i}`, X.wrong_from[i]);
            const ts = ev(`w${i}_strike`);
            tl.fromTo(strike, { scaleX: 0 }, { scaleX: 1, duration: 0.28, ease: "power2.inOut", immediateRender: false }, ts);
            tl.fromTo(bad, { opacity: 1 }, { opacity: 0.72, duration: 0.3, immediateRender: false }, ts + 0.25);
            shake(tl, bad, ts, 10, 6);
            const tr = ev(`r${i}_in`);
            tl.fromTo(good, { opacity: 0, y: 50, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, tr);
            karaoke(tl, gw, `r${i}`, X.right_from[i]);
            tl.fromTo(uc, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", immediateRender: false }, ev(`e${i}_in`));
            if (uw) karaoke(tl, uw, `e${i}`);
          });

          // ---- CTA (Urdu line + follow card)
          const cu = $("#cta-ur");
          cu.textContent = C.cta_ur || "";
          if (C.cta_ur) fit(cu, { max: 62, min: 34, maxH: 220 });
          const tc = ev("cta_in");
          show(tl, "#cta", tc, null, { inFrom: { opacity: 0, y: 60 } });
          endCard(tl, tc + 0.3, null);
        }
