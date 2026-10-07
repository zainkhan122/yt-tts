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

(async () => {
  const [url, out, selJson] = process.argv.slice(2);
  const selectors = selJson ? JSON.parse(selJson) : {};
  fs.mkdirSync(out, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: findChrome(), headless: "shell",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars", "--force-color-profile=srgb"],
  });
  const result = { url, files: {}, missing: [] };
  try {
    const page = await browser.newPage();
    // ---- mobile (phone mockup material)
    await page.setUserAgent("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1");
    await page.setViewport({ width: 430, height: 932, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true });
    await page.goto(url, { waitUntil: "networkidle2", timeout: 90000 });
    await new Promise((r) => setTimeout(r, 1500));
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
  fs.writeFileSync(path.join(out, "extra.json"), JSON.stringify(result, null, 1));
  console.log(JSON.stringify(result));
})().catch((e) => { console.error(e); process.exit(1); });
