// Extra captures that `hyperframes capture` doesn't do: a MOBILE full-page shot (fits 9:16 phone mockups)
// and crisp DESKTOP element crops (e.g. GitHub repo header with stars, star-history chart, README image).
// Uses the puppeteer-core + chrome-headless-shell that ship with the HyperFrames CLI (nothing extra to install).
//
//   node tools/capture_extra.cjs <url> <outdir> '{"header":"#repository-container-header","stars":"img[alt*=\"star history\" i]"}'
const fs = require("fs");
const path = require("path");
const HF = "/usr/local/lib/node_modules/hyperframes/node_modules/puppeteer-core";
const puppeteer = require(process.env.PUPPETEER_CORE || HF);

function findChrome() {
  const root = path.join(process.env.HOME, ".cache/hyperframes/chrome/chrome-headless-shell");
  for (const v of fs.readdirSync(root).sort().reverse()) {
    const exe = path.join(root, v, "chrome-headless-shell-linux64/chrome-headless-shell");
    if (fs.existsSync(exe)) return exe;
  }
  throw new Error("chrome-headless-shell not found: run bootstrap.sh");
}

// Cookie/consent banners sit on top of the page and ruin on-camera framing.
// Dismiss them by clicking the most-permissive button with a KNOWN label (exact-ish match only —
// never guess). On by default; set REELS_DISMISS_CONSENT=0 to opt out. Reports what it clicked.
const CONSENT_LABELS = [
  "accept all cookies", "accept all", "accept cookies", "allow all cookies", "allow all",
  "accept & continue", "accept and continue", "i accept", "i agree", "agree and continue",
  "got it", "ok, got it", "okay", "understood", "agree",
  // Site-specific labels only when the caller opts in explicitly, e.g.
  // REELS_DISMISS_CONSENT_LABELS="ok,accept" for sites whose consent button is just "ok".
].concat((process.env.REELS_DISMISS_CONSENT_LABELS || "").split(",").map((s) => s.trim().toLowerCase()).filter(Boolean));
async function dismissConsent(page, log) {
  if (process.env.REELS_DISMISS_CONSENT === "0") return;
  const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();
  const clickIn = async (target) => {  // target: Page or Frame
    const hit = await target.evaluate((labels) => {
      const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 8 && r.height > 8 && r.top < innerHeight + 200; };
      const nodes = [...document.querySelectorAll("button, [role=button], a, input[type=button], input[type=submit]")];
      const scored = nodes
        .map((e) => ({ e, t: (e.innerText || e.value || e.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim().toLowerCase() }))
        .filter(({ e, t }) => vis(e) && t && labels.includes(t))
        .map(({ e, t }) => ({ e, t, i: labels.indexOf(t) }))
        .sort((a, b) => a.i - b.i || b.e.getBoundingClientRect().width - a.e.getBoundingClientRect().width);
      if (!scored.length) return null;
      const { e, t } = scored[0];
      e.scrollIntoView({ block: "center" });
      e.click();
      return t;
    }, CONSENT_LABELS).catch(() => null);
    return hit;
  };
  try {
    let label = await clickIn(page);
    if (!label) {
      for (const f of page.frames().filter((f) => f !== page.mainFrame())) {
        label = await clickIn(f);
        if (label) break;
      }
    }
    if (label) {
      log.push(`consent-dismissed: ${label}`);
      await new Promise((r) => setTimeout(r, 450));  // let the overlay animate away
    }
  } catch { /* dismissal is best-effort; never fail a capture for it */ }
}

(async () => {
  const [url, out, selJson] = process.argv.slice(2);
  const selectors = selJson ? JSON.parse(selJson) : {};
  fs.mkdirSync(out, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: findChrome(), headless: "shell",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars", "--force-color-profile=srgb"],
  });
  const result = { url, files: {}, missing: [] };
  const consentLog = [];
  try {
    const page = await browser.newPage();
    // ---- mobile (phone mockup material)
    await page.setUserAgent("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1");
    await page.setViewport({ width: 430, height: 932, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true });
    await page.goto(url, { waitUntil: "networkidle2", timeout: 90000 });
    await new Promise((r) => setTimeout(r, 1500));
    await dismissConsent(page, consentLog);
    await page.screenshot({ path: path.join(out, "mobile-viewport.png") });
    const h = await page.evaluate(() => document.documentElement.scrollHeight);
    const clipH = Math.min(h, 6000); // 6000 css px x 2.5 = 15000 px, under Chrome's 16384 limit
    await page.screenshot({ path: path.join(out, "mobile-full.png"), clip: { x: 0, y: 0, width: 430, height: clipH }, captureBeyondViewport: true });
    result.files.mobile_full = { file: "mobile-full.png", css_height: clipH, page_height: h };
    // ---- desktop element crops (crisp @2x)
    await page.setUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36");
    await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 2, isMobile: false, hasTouch: false });
    await page.goto(url, { waitUntil: "networkidle2", timeout: 90000 });
    await new Promise((r) => setTimeout(r, 1500));
    await dismissConsent(page, consentLog);
    await page.screenshot({ path: path.join(out, "desktop-viewport.png") });
    const dh = await page.evaluate(() => document.documentElement.scrollHeight);
    const dClip = Math.min(dh, 7000); // @2x = 14000 px tall, under Chrome's 16384 limit
    await page.screenshot({ path: path.join(out, "desktop-full.png"), clip: { x: 0, y: 0, width: 1280, height: dClip }, captureBeyondViewport: true });
    result.files.desktop_full = { file: "desktop-full.png", css_width: 1280, css_height: dClip, dpr: 2 };
    // REGION MAP (page CSS px): lets the video camera zoom to / the cursor click on REAL elements of the page
    result.regions = await page.evaluate(() => {
      const out = {};
      const vis = (e) => e && e.getBoundingClientRect().width > 4 && e.getBoundingClientRect().height > 4;
      const R = (e) => { const r = e.getBoundingClientRect(); return { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; };
      const put = (name, e) => { if (vis(e) && !out[name]) out[name] = R(e); };
      const slug = (s) => (s || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 32);
      [...document.querySelectorAll('a[href$="/stargazers"]')].filter(vis).forEach((e, i) => put("stars_" + i, e));
      [...document.querySelectorAll('a[href$="/forks"]')].filter(vis).forEach((e, i) => put("forks_" + i, e));
      // header buttons by visible text (logged-out GitHub renders Star as a login link, so hrefs are unreliable)
      const area = (e) => { const r = e.getBoundingClientRect(); return r.width * r.height; };
      const txt = (e) => (e.innerText || "").trim().replace(/\s+/g, " ");  // rendered text only (GitHub hides tooltips in the DOM)
      const byText = (re, maxY) => [...document.querySelectorAll("a, button, summary")].filter((e) => vis(e) && re.test(txt(e)) && R(e).y < maxY).sort((a, b) => area(a) - area(b));
      put("star_button", byText(/^Star\s*[\d.,]+\s*k?/i, 420)[0]);  // renders as "Star4.9k (4.9k)"
      put("fork_button", byText(/^Fork\s*[\d.,]+/i, 420)[0]);
      const title = [...document.querySelectorAll("a, strong")].filter((e) => vis(e) && R(e).y < 420 && /^[\w.-]+$/.test(e.textContent.trim()) && location.pathname.endsWith("/" + e.textContent.trim())).sort((a, b) => parseFloat(getComputedStyle(b).fontSize) - parseFloat(getComputedStyle(a).fontSize))[0];  // header title, not the breadcrumb
      put("repo_title", title);
      // About box: smallest sidebar-sized block whose rendered text starts with "About"
      const aboutBox = [...document.querySelectorAll("div, section, aside")].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 150 && r.width <= 420 && r.height >= 150 && /^About\b/.test(txt(e));
      }).sort((a, b) => area(a) - area(b))[0];
      put("about", aboutBox);
      const art = document.querySelector("article.markdown-body") || document.querySelector("article");
      put("readme", art);
      if (art) {
        [...art.querySelectorAll("img")].filter(vis).slice(0, 16).forEach((im, i) => put("img_" + i + (im.alt ? "_" + slug(im.alt) : ""), im));
        [...art.querySelectorAll("h1, h2, h3")].filter(vis).forEach((h) => put("h_" + slug(h.textContent), h));
        [...art.querySelectorAll("pre")].filter(vis).slice(0, 8).forEach((pre, i) => put("code_" + i, pre));
      }
      // Generic (non-GitHub) harvest for changelogs/news pages: dated entry labels + short bold titles.
      // Named `date_oct-8-2026` / `title_katana` so briefs can zoom to real entries; capped to stay sane.
      if (!document.querySelector('a[href$="/stargazers"]')) {
        const root = art || document.querySelector("main") || document.body;
        const dateRe = /^[A-Z][a-z]{2,8}\s+\d{1,2},\s+20\d\d$/;
        const seenY = new Set();
        let n = 0;
        [...root.querySelectorAll("time, span, p, div, strong")].filter((e) => vis(e) && e.children.length === 0).forEach((e) => {
          const t = txt(e);
          if (!dateRe.test(t) || n >= 20) return;
          const r = R(e);
          const key = Math.round(r.y / 8);  // dedupe stacked nodes with the same date
          if (seenY.has(key)) return;
          seenY.add(key);
          const name = "date_" + slug(t);
          if (!out[name]) { out[name] = r; n += 1; }
        });
        let m = 0;
        [...root.querySelectorAll("h1, h2, h3, h4, h5, h6, strong, b")].filter(vis).forEach((e) => {
          const t = txt(e);
          if (!t || t.length > 60 || m >= 25) return;
          const name = "title_" + slug(t);
          if (!out[name]) { out[name] = R(e); m += 1; }
        });
        // Docs/app pages often style headings and buttons with plain divs/spans: fall back to
        // font-size (title-ish text) and short interactive labels so the camera still has anchors.
        const seenY2 = new Set();
        [...root.querySelectorAll("div, span, p, section, header, li")].filter(vis).forEach((e) => {
          const t = txt(e);
          if (!t || t.length < 3 || t.length > 60 || e.children.length > 3 || n + m >= 40) return;
          const fs = parseFloat(getComputedStyle(e).fontSize) || 0;
          if (fs < 22) return;
          const r = R(e);
          if (r.h > 90) return;
          const key = Math.round(r.y / 6);
          if (seenY2.has(key)) return;
          seenY2.add(key);
          const name = "t_" + slug(t);
          if (!out[name]) { out[name] = r; m += 1; }
        });
        [...root.querySelectorAll("button, a[role=button], a[class*=btn i], a[class*=button i]")].filter(vis).forEach((e) => {
          const t = txt(e);
          if (!t || t.length > 32 || m >= 45) return;
          const name = "btn_" + slug(t);
          if (!out[name]) { out[name] = R(e); m += 1; }
        });
      }
      return out;
    });
    for (const [name, sel] of Object.entries(selectors)) {
      const el = await page.$(sel);
      if (!el) { result.missing.push(name); continue; }
      await el.scrollIntoView();
      await new Promise((r) => setTimeout(r, 600));
      await el.screenshot({ path: path.join(out, `crop-${name}.png`) });
      result.files[name] = { file: `crop-${name}.png`, selector: sel };
    }
  } finally {
    await browser.close();
  }
  if (consentLog.length) result.consent = consentLog;
  fs.writeFileSync(path.join(out, "extra.json"), JSON.stringify(result, null, 1));
  console.log(JSON.stringify(result));
})().catch((e) => { console.error(e); process.exit(1); });
