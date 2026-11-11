"""Smoke test of the pipeline adapter with synthetic word timings (no voice). Usage: python3 -m graphics.smoke_brief <out.mp4> <vo.wav>"""
import json
import sys
from pathlib import Path

from graphics.stage import render_for_pipeline
from graphics.tests.test_brief_plan import _timing  # same scene text as the brief


def main(out, vo):
    timing, order, dur = _timing(True)
    gdir = Path(__file__).resolve().parent / "fixtures" / "craft-anything"
    info = render_for_pipeline(gdir, timing, order, Path(vo), Path(out), Path(out).parent / "smoke-work", round(dur, 2))
    print(json.dumps(info, indent=1, default=str)[:1200])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
