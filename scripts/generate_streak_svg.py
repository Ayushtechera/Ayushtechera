"""
Render an animated GitHub-style contribution heatmap SVG from
data/contributions.json (produced by fetch_contributions.py).

Usage:
    python scripts/generate_streak_svg.py <github_username> <output.svg>

This reads data/contributions.json (relative to repo root) and draws a
GitHub-calendar-style grid of squares, colored by contribution count, plus a
small stats line (current streak / longest streak / total).
"""
import datetime
import json
import os
import sys

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "Ayushtechera"
OUT = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "data", "contributions.json")

CELL = 11
GAP = 3
PAD = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"

# GitHub-ish green scale, level 0..4
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def level_for(count, max_count):
    if count == 0:
        return 0
    if max_count <= 0:
        return 1
    frac = count / max_count
    if frac > 0.75:
        return 4
    if frac > 0.5:
        return 3
    if frac > 0.25:
        return 2
    return 1


def main():
    with open(DATA_PATH) as f:
        data = json.load(f)

    days = data["days"]
    max_count = max((d["count"] for d in days), default=0)

    # bucket into weeks (columns), Sunday-start, like GitHub's calendar
    first_date = datetime.date.fromisoformat(days[0]["date"])
    start_offset = (first_date.weekday() + 1) % 7  # days before first Sunday
    weeks = []
    week = [None] * start_offset
    for d in days:
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    cols = len(weeks)
    grid_w = cols * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    canvas_w = grid_w + PAD * 2
    canvas_h = TITLEBAR_H + grid_h + PAD * 2 + 24  # extra for stats line

    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">'
    )
    p.append('<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
              f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
              '</linearGradient></defs>')
    p.append(f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>')
    p.append(f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')
    p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="11.5" '
              f'text-anchor="middle">{USERNAME}@github: ~$ ./contributions.sh</text>')

    grid_top = TITLEBAR_H + PAD * 0.6
    for wi, wk in enumerate(weeks):
        x = PAD + wi * (CELL + GAP)
        for di, d in enumerate(wk):
            y = grid_top + di * (CELL + GAP)
            if d is None:
                continue
            lvl = level_for(d["count"], max_count)
            delay = wi * 0.012 + di * 0.006
            p.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{LEVELS[lvl]}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{delay:.3f}s"/></rect>'
            )

    stats_y = grid_top + grid_h + 20
    cur = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    total = data["total_contributions"]
    p.append(f'<text x="{PAD}" y="{stats_y:.1f}" fill="{TITLE_TEXT}" font-size="12">'
              f'total <tspan fill="{INK}">{total}</tspan> &#183; '
              f'current streak <tspan fill="{INK}">{cur}</tspan> &#183; '
              f'longest <tspan fill="{INK}">{longest}</tspan></text>')

    p.append("</svg>")
    svg = "".join(p)
    out_path = OUT if os.path.isabs(OUT) else os.path.join(HERE, "..", OUT)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path}  {len(svg)/1024:.1f} KB  {cols} weeks")


if __name__ == "__main__":
    main()
