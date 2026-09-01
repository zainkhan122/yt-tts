#!/usr/bin/env python3
"""Real artifacts: Wikimedia photos + sourced filing/headline cards (verbatim public-record text)."""
import json, ssl, textwrap, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CTX = ssl.create_default_context()
UA = "ThePublicRecord/1.0 (educational documentary; research@localhost)"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1280, 720


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=CTX, timeout=45) as r:
        return r.read()


def wiki_image(title, dest):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    data = json.loads(get(url).decode("utf-8"))
    src = (data.get("originalimage") or data.get("thumbnail") or {}).get("source")
    if not src:
        raise RuntimeError(f"no image for {title}")
    dest = Path(dest)
    dest.write_bytes(get(src))
    print("IMG", dest, dest.stat().st_size, src)
    return data


def card(path, kicker, title, body, source):
    im = Image.new("RGB", (W, H), (18, 18, 20))
    d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(FONTB, 22)
    ft = ImageFont.truetype(FONTB, 36)
    fbod = ImageFont.truetype(FONT, 22)
    fs = ImageFont.truetype(FONT, 16)
    d.rectangle((0, 0, 14, H), fill=(196, 30, 58))
    d.text((48, 36), kicker.upper(), font=fb, fill=(196, 30, 58))
    # wrap title
    y = 80
    for line in textwrap.wrap(title, 42):
        d.text((48, y), line, font=ft, fill=(237, 230, 217))
        y += 46
    y += 16
    d.line((48, y, 1230, y), fill=(80, 70, 60), width=1)
    y += 24
    for line in textwrap.wrap(body, 78):
        if y > 620:
            break
        d.text((48, y), line, font=fbod, fill=(210, 205, 195))
        y += 30
    d.text((48, 670), source[:110], font=fs, fill=(140, 130, 120))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=92)
    print("CARD", path)


def main():
    e01 = Path("/home/user/the-public-record/episodes/Why MoviePass Died With 3 Million Members/artifacts")
    e02 = Path("/home/user/the-public-record/episodes/Quibi Raised $1.75 Billion. It Lasted Six Months/artifacts")
    e01.mkdir(parents=True, exist_ok=True)
    e02.mkdir(parents=True, exist_ok=True)

    card(
        e01 / "01_hmny_8k_moviepass_stake.png",
        "SEC EDGAR  ·  Form 8-K/A  ·  30 Nov 2017",
        "Helios and Matheson Analytics Inc. agreed to acquire a majority stake in MoviePass.",
        "On August 15, 2017, Helios and Matheson Analytics Inc. filed a Form 8-K which disclosed its agreement to acquire a majority stake in MoviePass Inc. pursuant to a Securities Purchase Agreement entered into on the same date. On October 11, 2017 the companies entered Amendment No. 1. Headquarters listed: Empire State Building, 350 5th Avenue.",
        "Source: SEC EDGAR accession 0001213900-18-001535  (CIK 0001040792)",
    )
    card(
        e01 / "02_hmny_600k_subscribers_oct2017.png",
        "COMPANY PRESS  ·  Exhibit 99  ·  24 Oct 2017",
        "MoviePass surpasses 600,000 paying monthly subscribers.",
        "Helios and Matheson Analytics Inc. announced that MoviePass Inc. had surpassed over 600,000 paying monthly subscribers as of October 18, 2017, up from approximately 20,000 as of August 14, 2017 — the day before MoviePass announced its new $9.95 per month subscription price.",
        "Source: SEC EDGAR Exhibit 99, 24 Oct 2017  accession 0001213900-17-010855",
    )
    try:
        wiki_image("Empire State Building", e01 / "03_empire_state_hmny_hq.jpg")
    except Exception as e:
        print("wiki ESB failed", e)
        card(
            e01 / "03_empire_state_hmny_hq.png",
            "HEADQUARTERS",
            "Empire State Building, New York — address on the Helios 8-K.",
            "The November 2017 Helios and Matheson 8-K lists the Empire State Building, 350 5th Avenue, New York, as the company address during the MoviePass transaction.",
            "Source: SEC EDGAR 8-K/A 30 Nov 2017",
        )

    try:
        wiki_image("Jeffrey Katzenberg", e02 / "01_jeffrey_katzenberg.jpg")
    except Exception as e:
        print("wiki katzenberg failed", e)
    try:
        wiki_image("Meg Whitman", e02 / "02_meg_whitman.jpg")
    except Exception as e:
        print("wiki whitman failed", e)
    card(
        e02 / "03_techcrunch_quibi_launch_headline.png",
        "HEADLINE  ·  TechCrunch  ·  6 Mar 2020",
        "Quibi will launch with 50 shows on April 6.",
        "The short-form streaming service from Jeffrey Katzenberg and Meg Whitman priced at $4.99 a month with ads or $7.99 without, with a 90-day free trial around launch. TechCrunch published the slate and the prices before the 6 April 2020 doors opened.",
        "Source: TechCrunch, 6 Mar 2020, 'Quibi will launch with 50 shows on April 6'",
    )
    print("DONE artifacts")


if __name__ == "__main__":
    main()
