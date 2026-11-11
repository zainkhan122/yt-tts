        // ================= quiz scene =================
        async function buildScene(tl, V) {
          const { $, $$, mk, seg, ev, fit, words, karaoke, show, flash, shake, endCard, DATA } = V;
          const C = DATA.content;
          const X = DATA.extra;
          const N = C.questions.length;

          // ---- hook: slam + read-along
          $("#hook-kicker").textContent = C.kicker || "QUIZ TIME";
          const ht = $("#hook-text");
          ht.textContent = C.hook_display || C.hook;
          fit(ht, { max: 170, min: 70, maxH: 620 });
          const hw = words(ht);
          $("#hook-sub").textContent = C.sub || `${N} QUESTIONS · ${X.think} SECONDS EACH`;
          const hs = seg("hook");
          show(tl, "#hook", 0, ev("q0_in"), { inFrom: { opacity: 0, scale: 1.18 }, inDur: 0.18 });
          tl.fromTo("#hook-kicker", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, 0.12);
          karaoke(tl, hw, "hook");
          tl.fromTo("#hook-sub", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, Math.max(0.5, hs.end - 0.5));
          shake(tl, "#hook-box", 0.06, 18, 8);
          flash(tl, 0.04, 0.55, 0.3);

          // ---- questions
          const host = $("#qs");
          const CIRC = 2 * Math.PI * 74;
          C.questions.forEach((q, i) => {
            const g = mk("section", "scene qgroup", host);
            g.id = "qg" + i;
            const head = mk("div", "qhead", g);
            mk("span", "chip", head, `QUESTION ${i + 1}/${N}`);
            const dots = mk("div", "dots", head);
            for (let k = 0; k < N; k++) mk("i", k < i ? "done" : k === i ? "on" : "", dots);
            const card = mk("div", "card qcard", g);
            const qt = mk("div", "qtext", card, q.q);
            fit(qt, { max: 80, min: 40, maxH: 310 });
            const qw = words(qt);
            const opts = mk("div", "opts", g);
            const optEls = q.options.map((o, k) => {
              const el = mk("div", "card opt", opts);
              const okl = mk("div", "okl", el);
              okl.setAttribute("data-layout-allow-overlap", "");
              mk("span", "badge", el, "ABCD"[k]);
              const tx = mk("span", "otext", el, o);
              fit(tx, { max: 54, min: 30, maxH: 80 });
              mk("span", "mark", el, k === q.answer ? "✓" : "✕");
              return el;
            });
            const timer = mk("div", "timer", g);
            timer.innerHTML = `<svg viewBox="0 0 190 190"><circle class="tr-bg" cx="95" cy="95" r="74"/><circle class="tr-fg" cx="95" cy="95" r="74" transform="rotate(-90 95 95)"/></svg><span class="tnum">${X.think}</span>`;
            const fact = mk("div", "fact", g, q.fact);
            fact.setAttribute("data-layout-allow-overlap", "");
            fit(fact, { max: 52, min: 30, maxH: 280 });
            const fw = words(fact);

            const tin = ev(`q${i}_in`);
            const tout = ev(`q${i}_out`);
            show(tl, g, tin, tout, { inFrom: { opacity: 0, x: 140 }, outTo: { opacity: 0, x: -140 }, inDur: 0.32 });
            tl.fromTo(card, { scale: 0.9 }, { scale: 1, duration: 0.4, ease: "back.out(1.8)", immediateRender: false }, tin + 0.04);
            karaoke(tl, qw, `q${i}`);
            optEls.forEach((el, k) => {
              tl.fromTo(el, { opacity: 0, x: k % 2 ? 90 : -90, scale: 0.9 }, { opacity: 1, x: 0, scale: 1, duration: 0.3, ease: "back.out(2)", immediateRender: false }, ev(`q${i}_opt${k}`));
            });

            // countdown ring + digits (ticks are in the audio at the same event times)
            const ts = ev(`t${i}_start`);
            tl.fromTo(timer, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.25, ease: "back.out(2.2)", immediateRender: false }, ts - 0.08);
            const fg = timer.querySelector(".tr-fg");
            fg.style.strokeDasharray = String(CIRC);
            tl.fromTo(fg, { strokeDashoffset: 0 }, { strokeDashoffset: CIRC, duration: X.think, ease: "none", immediateRender: false }, ts);
            const num = timer.querySelector(".tnum");
            for (let s = 0; s < X.think; s++) {
              const t = ev(`t${i}_tick${s}`);
              tl.set(num, { textContent: String(X.think - s) }, t);
              tl.fromTo(num, { scale: 1.4 }, { scale: 1, duration: 0.28, ease: "power2.out", immediateRender: false }, t);
            }

            // reveal
            const tr = ev(`r${i}`);
            tl.fromTo(timer, { opacity: 1, scale: 1 }, { opacity: 0, scale: 0.7, duration: 0.18, immediateRender: false }, tr);
            optEls.forEach((el, k) => {
              const mark = el.querySelector(".mark");
              if (k === q.answer) {
                tl.fromTo(el.querySelector(".okl"), { opacity: 0 }, { opacity: 1, duration: 0.12, immediateRender: false }, tr);
                tl.fromTo(mark, { opacity: 0, scale: 2 }, { opacity: 1, scale: 1, duration: 0.25, ease: "back.out(3)", immediateRender: false }, tr + 0.05);
                tl.fromTo(el, { scale: 1 }, { scale: 1.06, duration: 0.12, immediateRender: false }, tr);
                tl.fromTo(el, { scale: 1.06 }, { scale: 1, duration: 0.3, ease: "back.out(3)", immediateRender: false }, tr + 0.12);
              } else {
                tl.fromTo(el, { opacity: 1 }, { opacity: 0.34, duration: 0.2, immediateRender: false }, tr);
                tl.fromTo(mark, { opacity: 0 }, { opacity: 0.9, duration: 0.2, immediateRender: false }, tr + 0.05);
              }
            });
            tl.fromTo(fact, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out", immediateRender: false }, tr + 0.12);
            karaoke(tl, fw, `a${i}`, X.ans_words[i]);
            flash(tl, tr, 0.22, 0.2);
          });

          // ---- CTA: score prompt + follow card
          const ct = $("#cta-title");
          ct.textContent = C.cta_title || "HOW MANY DID YOU GET?";
          fit(ct, { max: 130, min: 60, maxH: 260 });
          const sc = $("#cta-scores");
          for (let k = 0; k <= N; k++) mk("span", "chip ghost", sc, `${k}/${N}`);
          const tc = ev("cta_in");
          show(tl, "#cta", tc, null, { inFrom: { opacity: 0, y: 70 } });
          $$("#cta-scores .chip").forEach((el, k) => {
            tl.fromTo(el, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.25, ease: "back.out(2)", immediateRender: false }, tc + 0.15 + k * 0.08);
          });
          endCard(tl, tc + 0.35, null);
        }
