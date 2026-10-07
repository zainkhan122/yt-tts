#!/usr/bin/env python3
"""
Fetch a World Bank indicator for several countries and print (1) a data block you can paste
into a data-race / ranked-list brief and (2) an editor's fact sheet (values at key years,
leader per year, lead changes) so the narration you write uses REAL numbers.

World Bank Open Data: free, no API key, licensed CC BY 4.0 -> credit "Source: World Bank".

  python3 tools/fetch_worldbank.py NY.GDP.PCAP.CD PAK,IND,BGD 1990 2025
  python3 tools/fetch_worldbank.py SP.POP.TOTL WLD 1960 2025 --json > pop.json

Popular indicators: NY.GDP.PCAP.CD (GDP per person, US$), NY.GDP.MKTP.CD (GDP), SP.POP.TOTL
(population), IT.NET.USER.ZS (% using internet), SP.DYN.LE00.IN (life expectancy),
EN.GHG.CO2.PC.CE.AR5 (CO2 per person), SL.UEM.TOTL.ZS (unemployment %).
"""
import argparse
import json
import sys
import urllib.request

FLAGS = {"PAK": "🇵🇰", "IND": "🇮🇳", "BGD": "🇧🇩", "CHN": "🇨🇳", "USA": "🇺🇸", "GBR": "🇬🇧", "IDN": "🇮🇩", "NGA": "🇳🇬",
         "BRA": "🇧🇷", "TUR": "🇹🇷", "SAU": "🇸🇦", "ARE": "🇦🇪", "EGY": "🇪🇬", "IRN": "🇮🇷", "AFG": "🇦🇫", "LKA": "🇱🇰",
         "NPL": "🇳🇵", "VNM": "🇻🇳", "PHL": "🇵🇭", "MYS": "🇲🇾", "JPN": "🇯🇵", "KOR": "🇰🇷", "DEU": "🇩🇪", "FRA": "🇫🇷"}
COLORS = ["#22c55e", "#f97316", "#38bdf8", "#e879f9", "#facc15", "#f43f5e"]


def fetch(indicator, countries, y0, y1):
    url = (f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
           f"?format=json&date={y0}:{y1}&per_page=2000")
    with urllib.request.urlopen(url, timeout=40) as r:
        payload = json.load(r)
    if len(payload) < 2 or payload[1] is None:
        raise SystemExit(f"no data: {payload}")
    meta, rows = payload
    series, label = {}, rows[0]["indicator"]["value"]
    for row in rows:
        if row["value"] is None:
            continue
        iso = row["countryiso3code"] or row["country"]["id"]
        s = series.setdefault(iso, {"iso": iso, "name": row["country"]["value"], "values": {}})
        s["values"][int(row["date"])] = round(float(row["value"]), 2)
    return label, meta, series


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indicator")
    ap.add_argument("countries", help="comma-separated ISO3 codes, e.g. PAK,IND,BGD")
    ap.add_argument("y0", type=int)
    ap.add_argument("y1", type=int)
    ap.add_argument("--json", action="store_true", help="print only the brief data block")
    a = ap.parse_args()
    isos = [c.strip().upper() for c in a.countries.split(",")]
    label, meta, series = fetch(a.indicator, isos, a.y0, a.y1)
    common = sorted(set.intersection(*(set(s["values"]) for s in series.values())))
    block = {"indicator": a.indicator, "label": label, "source": "World Bank Open Data (CC BY 4.0)",
             "source_url": f"https://data.worldbank.org/indicator/{a.indicator}",
             "series": [{"name": series[i]["name"], "iso": i, "flag": FLAGS.get(i, ""), "color": COLORS[k % len(COLORS)],
                         "values": {str(y): series[i]["values"][y] for y in common}} for k, i in enumerate(isos) if i in series]}
    if a.json:
        print(json.dumps(block, ensure_ascii=False, indent=1))
        return
    print(f"# {label}  ({a.indicator}); years with data for all: {common[0]}-{common[-1]} ({len(common)} points)")
    print(f"# last updated by World Bank: {meta.get('lastupdated')}")
    marks = sorted({common[0], common[-1], *[y for y in common if y % 5 == 0]})
    print("year  " + "  ".join(f"{series[i]['name'][:12]:>12}" for i in isos if i in series) + "   leader")
    prev = None
    for y in common:
        vals = {i: series[i]["values"][y] for i in isos if i in series}
        lead = max(vals, key=vals.get)
        change = prev is not None and lead != prev
        if y in marks or change:
            print(f"{y}  " + "  ".join(f"{vals[i]:>12,.0f}" for i in vals) + f"   {series[lead]['name']}{'  <- lead change' if change else ''}")
        prev = lead
    first, last = common[0], common[-1]
    for i in isos:
        if i in series:
            v0, v1 = series[i]["values"][first], series[i]["values"][last]
            print(f"# {series[i]['name']}: {v0:,.0f} -> {v1:,.0f}  (x{v1 / v0:.1f})")
    print("\n# data block for the brief (content.series):", file=sys.stderr)


if __name__ == "__main__":
    main()
