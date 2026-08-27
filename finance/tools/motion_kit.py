#!/usr/bin/env python3
"""motion_kit.py — F1 chart/diagram renderer. No Pexels.
Usage:
  python3 tools/motion_kit.py sample
  python3 tools/motion_kit.py bars OUT.png --title "..." --labels a,b,c --values 1,2,3 --source "Fed SCF 2022"
  python3 tools/motion_kit.py stat OUT.png --value "$20,000" --label "THE FIRST THRESHOLD" --source "..."
  python3 tools/motion_kit.py line OUT.png --title "..." --ys 1,1.08,1.16 --source "..."
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOK = json.loads((ROOT / "brand/tokens.json").read_text())
C = TOK["colors"]
CH = TOK["chart"]
FONT = TOK["type"]["thumb"]
OUTDIR = ROOT / "output"
OUTDIR.mkdir(exist_ok=True)

def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fp = font_manager.FontProperties(fname=FONT)
    plt.rcParams.update({
        "figure.facecolor": CH["facecolor"],
        "axes.facecolor": CH["facecolor"],
        "axes.edgecolor": C["grid"],
        "axes.labelcolor": C["paper"],
        "text.color": C["paper"],
        "xtick.color": C["paper"],
        "ytick.color": C["muted"],
        "grid.color": C["grid"],
        "savefig.facecolor": CH["facecolor"],
        "savefig.dpi": 160,
    })
    return plt, fp

def _source(ax, plt, text, fp):
    ax.text(0.0, -0.14, text, transform=ax.transAxes, fontsize=8,
            color=C["muted"], fontproperties=fp, ha="left")

def bars(out, title, labels, values, source):
    plt, fp = _mpl()
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    ax.bar(labels, values, color=CH["bar"], width=0.62)
    ax.set_title(title, fontproperties=fp, fontsize=22, color=C["paper"], pad=16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C["grid"])
    ax.spines["bottom"].set_color(C["grid"])
    ax.yaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    for i, v in enumerate(values):
        ax.text(i, v, f"  {v:,.0f}" if v >= 10 else f"  {v:g}",
                ha="center", va="bottom", fontsize=12, color=C["gold"], fontproperties=fp)
    _source(ax, plt, source, fp)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", pad_inches=0.35)
    plt.close()
    print("WROTE", out)

def stat(out, value, label, source):
    plt, fp = _mpl()
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.58, value, ha="center", va="center", fontsize=72,
            color=C["gold"], fontproperties=fp)
    ax.text(0.5, 0.32, label, ha="center", va="center", fontsize=22,
            color=C["paper"], fontproperties=fp)
    ax.text(0.5, 0.12, source, ha="center", va="center", fontsize=10, color=C["muted"])
    fig.savefig(out, bbox_inches="tight", pad_inches=0.2)
    plt.close()
    print("WROTE", out)

def line(out, title, ys, source, xlabel="year"):
    plt, fp = _mpl()
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    xs = list(range(len(ys)))
    ax.plot(xs, ys, color=CH["bar"], linewidth=3.5)
    ax.fill_between(xs, ys, color=CH["bar"], alpha=0.15)
    ax.set_title(title, fontproperties=fp, fontsize=22, pad=16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    _source(ax, plt, source, fp)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", pad_inches=0.35)
    plt.close()
    print("WROTE", out)

def sample():
    bars(OUTDIR / "sample_20k.png",
         "Why $20,000 is the first threshold",
         ["$0", "$5k", "$20k", "$100k"],
         [0, 5, 20, 100],
         "Source: illustrative thresholds, not a recommendation. Fed SCF for US medians.")
    stat(OUTDIR / "sample_stat.png",
         "$20,000", "THE FIRST THRESHOLD",
         "Education only. Not financial advice.")
    line(OUTDIR / "sample_compound.png",
         "8% returns on $0 is still $0",
         [0, 0, 0, 0.2, 0.5, 1.2, 2.5],
         "Source: illustration of contribution vs rate. Not a projected return.")

def _csv(s):
    out = []
    for x in s.split(","):
        x = x.strip()
        try: out.append(float(x))
        except ValueError: out.append(x)
    return out

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if cmd == "sample":
        sample()
    elif cmd == "bars":
        kw = dict(zip([a.lstrip("-") for a in sys.argv[3::2]], sys.argv[4::2]))
        bars(sys.argv[2], kw["title"], kw["labels"].split(","),
             [float(x) for x in kw["values"].split(",")], kw.get("source", ""))
    elif cmd == "stat":
        kw = dict(zip([a.lstrip("-") for a in sys.argv[3::2]], sys.argv[4::2]))
        stat(sys.argv[2], kw["value"], kw["label"], kw.get("source", ""))
    elif cmd == "line":
        kw = dict(zip([a.lstrip("-") for a in sys.argv[3::2]], sys.argv[4::2]))
        line(sys.argv[2], kw["title"], [float(x) for x in kw["ys"].split(",")],
             kw.get("source", ""))
    else:
        sys.exit("unknown command")
