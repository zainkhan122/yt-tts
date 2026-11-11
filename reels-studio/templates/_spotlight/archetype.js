        // ============ Archetype chrome ============
        // Runs after every scene is built. The treatment's archetype decides the on-screen
        // grammar: a mission rail (quest), a claim/reality stamp (myth-bust), and so on.
        // Seek-safe: only opacity/scale tweens with immediateRender:false, never callbacks.
        function archetypeChrome(tl, A, X) {
          X = X || {};
          const root = A.$("#root");
          const ARCH = String(X.archetype || (root && root.dataset.archetype) || "spotlight");
          const scenes = (X.scenes || []).filter((s) => s && s.id);
          const L = X.layout || {};
          const STAGE_BOTTOM = L.stage_bottom || 1128;
          const BEATS = X.beats || {};
          const fmt2 = (n) => String(n).padStart(2, "0");
          const ev = (k, d) => A.ev(k, d);
          if (!scenes.length) return;

          // ---- scene at a given type / role
          const byType = (t) => scenes.find((s) => s.type === t);
          const byId = (id) => scenes.find((s) => s.id === id);
          const first = scenes[0];
          const proof = byId(BEATS.proof_scene) || byType("steps") || byType("page");
          const payoff = byId(BEATS.payoff_scene) || byType("verdict") || scenes[scenes.length - 1];

          // ---- HUD: always on screen (also on the cover frame)
          const hud = A.mk("div", "arch-hud", root);
          hud.setAttribute("data-layout-allow-overlap", "");
          const label = { quest: "MISSION", "myth-bust": "CLAIM vs REALITY", "demo-first": "DEMO",
                          workflow: "PIPELINE", warning: "WATCH OUT", duel: "HEAD TO HEAD", spotlight: "" }[ARCH] || "";
          if (label) A.mk("span", "arch-tag", hud, label);
          const counts = scenes.map((s, i) => {
            const c = A.mk("span", "arch-count", hud, `${fmt2(i + 1)}/${fmt2(scenes.length)}`);
            c.style.display = "none";
            return c;
          });
          hud.style.opacity = label ? "1" : "0";
          scenes.forEach((s, i) => {
            const a = ev(s.id + "_in", 0), z = ev(s.id + "_out", A.D);
            if (i === 0) { counts[i].style.display = ""; }
            else tl.set(counts[i], { display: "" }, a);
            if (i + 1 < scenes.length) tl.set(counts[i], { display: "none" }, ev(scenes[i + 1].id + "_in", z));
          });

          // ---- QUEST: mission rail with one node per scene + objective kickers + proof stamps
          if (ARCH === "quest") {
            const rail = A.mk("div", "arch-rail", root);
            rail.setAttribute("data-layout-allow-overlap", "");
            const fill = A.mk("div", "arch-rail-fill", rail);
            const H = 872;
            const nodes = scenes.map((s, i) => {
              const n = A.mk("div", "arch-node", rail);
              n.style.top = Math.round((H - 24) * (i / Math.max(1, scenes.length - 1))) + "px";
              n.setAttribute("data-layout-allow-overlap", "");
              return n;
            });
            const span = ev(first.id + "_in", 0) === 0 ? A.D : A.D;
            tl.fromTo(fill, { scaleY: 0 }, { scaleY: 1, duration: span, ease: "none", immediateRender: false }, 0);
            nodes.forEach((n, i) => {
              const a = ev(scenes[i].id + "_in", 0);
              tl.fromTo(n, { opacity: 0.35, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.2, immediateRender: false }, a);
            });

            scenes.forEach((s, i) => {
              const host = A.$("#s-" + s.id);
              if (!host) return;
              const a = ev(s.id + "_in", 0), z = ev(s.id + "_out", A.D);
              if (s.heading || s.headline) {
                const k = A.mk("div", "arch-kicker", host, `OBJECTIVE ${fmt2(i + 1)}`);
                k.setAttribute("data-layout-allow-overlap", "");
                if (i === 0) k.style.opacity = "1";
                else tl.fromTo(k, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.25, immediateRender: false }, a + 0.05);
                if (z < A.D - 0.01) tl.fromTo(k, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, z - 0.2);
              }
              const stampText = s.id === (proof || {}).id ? "PROOF"
                : s.id === (payoff || {}).id ? "FIELD NOTES"
                : i === 0 ? "BRIEFING" : "";
              if (!stampText) return;
              const st = A.mk("div", "arch-stamp", host, stampText);
              st.setAttribute("data-layout-allow-overlap", "");
              Object.assign(st.style, { left: "84px", top: (STAGE_BOTTOM - 196) + "px", color: "#fbbf24",
                                        background: "rgba(4,8,16,0.55)", transform: "rotate(-4deg)" });
              if (i === 0) st.style.opacity = "1";
              else tl.fromTo(st, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.26, ease: "back.out(2)", immediateRender: false }, a + 0.35);
              if (z < A.D - 0.01) tl.fromTo(st, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, z - 0.22);
            });
          }

          // ---- MYTH-BUST: claim/reality stamp over the proof and the verdict
          if (ARCH === "myth-bust") {
            scenes.forEach((s, i) => {
              const host = A.$("#s-" + s.id);
              if (!host) return;
              const a = ev(s.id + "_in", 0), z = ev(s.id + "_out", A.D);
              const stampText = i === 0 ? "CLAIM"
                : s.id === (payoff || {}).id ? "REALITY"
                : (proof && s.id === proof.id) ? "PROOF" : "";
              if (!stampText) return;
              const colour = stampText === "REALITY" ? "#4ade80" : stampText === "CLAIM" ? "#f87171" : "#c084fc";
              const st = A.mk("div", "arch-stamp", host, stampText === "REALITY" ? "REALITY ✓" : stampText);
              st.setAttribute("data-layout-allow-overlap", "");
              Object.assign(st.style, { left: "84px", top: (STAGE_BOTTOM - 200) + "px", color: colour,
                                        background: "rgba(6,4,16,0.55)", transform: "rotate(-6deg)" });
              if (i === 0) st.style.opacity = "1";
              else tl.fromTo(st, { opacity: 0, scale: 1.7, rotation: -18 }, { opacity: 1, scale: 1, rotation: -6, duration: 0.28, ease: "back.out(2.2)", immediateRender: false }, a + 0.4);
              if (z < A.D - 0.01) tl.fromTo(st, { opacity: 1 }, { opacity: 0, duration: 0.18, immediateRender: false }, z - 0.2);
            });
          }

          // ---- other archetypes: one scene-level device each (never colour alone)
          if (ARCH === "warning" || ARCH === "workflow" || ARCH === "demo-first" || ARCH === "duel") {
            const tag = { warning: "THE CATCH", workflow: "STEP BY STEP", "demo-first": "LIVE DEMO", duel: "SIDE BY SIDE" }[ARCH];
            const host = A.$("#s-" + (proof || first).id);
            if (host && tag) {
              const k = A.mk("div", "arch-kicker", host, tag);
              k.setAttribute("data-layout-allow-overlap", "");
              k.style.opacity = "1";
            }
          }
        }
