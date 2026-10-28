#!/usr/bin/env python3
"""Generate an animated contribution snake that covers only the date range in
data/contributions.json (already filtered to start on Feb 1).

Stdlib only. Writes two self-contained SVGs into dist/ so the existing workflow
can publish them to the output branch:

    dist/github-contribution-grid-snake.svg
    dist/github-contribution-grid-snake-dark.svg

The snake follows a serpentine path across the grid; contributed cells flash as
the head passes over them. SMIL/CSS only so it works inside <img> on GitHub.

    python scripts/generate_snake_svg.py [data.json] [out_dir]
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "dist")

CELL = 13
GAP = 4
STEP = CELL + GAP
LEFT = 34
TOP = 22
RAD = 2.5
DUR = 16.0

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PALETTES = {
    "light": {
        "empty": "#ebedf0",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "snake": "#216e39",
        "text": "#57606a",
    },
    "dark": {
        "empty": "#161b22",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "snake": "#39d353",
        "text": "#7d8590",
    },
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_grid(days):
    first = dt.date.fromisoformat(days[0]["date"])
    last = dt.date.fromisoformat(days[-1]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    total = (last - start).days + 1
    ncols = (total + 6) // 7
    by_date = {d["date"]: d for d in days}
    cells = []
    for i in range(total):
        day = start + dt.timedelta(days=i)
        d = by_date.get(day.isoformat())
        cells.append({
            "col": i // 7,
            "row": i % 7,
            "level": min(int(d["level"]), 4) if d else 0,
            "count": int(d["count"]) if d else 0,
            "outside": d is None,
        })
    return start, ncols, cells


def month_labels(start, ncols):
    out, last = [], None
    for col in range(ncols):
        d = start + dt.timedelta(days=col * 7)
        if d.month != last:
            last = d.month
            out.append((col, MONTHS[d.month - 1]))
    return out


def path_points(ncols):
    pts = []
    for col in range(ncols):
        rows = range(7) if col % 2 == 0 else range(6, -1, -1)
        for row in rows:
            pts.append((LEFT + col * STEP + CELL / 2, TOP + row * STEP + CELL / 2))
    return pts


def render(days, palette, out_path):
    start, ncols, cells = build_grid(days)
    W = LEFT + ncols * STEP + CELL + 10
    H = TOP + 7 * STEP + 24
    total = sum(d["count"] for d in days)
    first = days[0]["date"]
    last = days[-1]["date"]
    f = dt.date.fromisoformat(first)
    l = dt.date.fromisoformat(last)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
         '<style>',
         'text.lbl{fill:' + palette["text"] + ';font-size:12px;font-weight:600}',
         'text.foot{fill:' + palette["text"] + ';font-size:11px}',
         f'.eat{{animation:eat {DUR}s linear infinite}}',
         '@keyframes eat{0%{filter:brightness(2.6)}1%{filter:brightness(2.6)}'
         '3%,100%{filter:brightness(1)}}',
         '@media (prefers-reduced-motion:reduce){.eat{animation:none}.snake{display:none}}',
         '</style>']

    for col, mon in month_labels(start, ncols):
        p.append(f'<text class="lbl" x="{LEFT + col * STEP}" y="{TOP - 6}">{mon}</text>')
    for name, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        p.append(f'<text class="lbl" x="4" y="{TOP + row * STEP + CELL - 3}">{name}</text>')

    for c in cells:
        if c["outside"]:
            continue
        x = LEFT + c["col"] * STEP
        y = TOP + c["row"] * STEP
        lvl = c["level"]
        if lvl == 0:
            p.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
                     f'fill="{palette["levels"][0]}"/>')
        else:
            idx = c["col"] * 7 + (c["row"] if c["col"] % 2 == 0 else 6 - c["row"])
            delay = round(idx / (ncols * 7 - 1) * DUR, 3)
            p.append(f'<rect class="eat" style="animation-delay:{delay}s" x="{x}" y="{y}" '
                     f'width="{CELL}" height="{CELL}" rx="{RAD}" fill="{palette["levels"][lvl]}"/>')

    pts = path_points(ncols)
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    for i, off in enumerate([0.48, 0.36, 0.24, 0.12]):
        r = 4.4 - i * 0.4
        op = 0.55 + i * 0.1
        p.append(f'<g class="snake" visibility="hidden">'
                 f'<set attributeName="visibility" to="visible" begin="{off}s"/>'
                 f'<animateMotion dur="{DUR}s" begin="{off}s" repeatCount="indefinite" path="{d}"/>'
                 f'<circle r="{r:.1f}" fill="{palette["snake"]}" opacity="{op:.2f}"/></g>')

    p.append(f'<g class="snake"><animateMotion dur="{DUR}s" repeatCount="indefinite" path="{d}"/>'
             f'<rect x="-5" y="-5" width="10" height="10" rx="3" fill="{palette["snake"]}"/>'
             f'<circle cx="-2" cy="-1.6" r="0.9" fill="#ffffff"/>'
             f'<circle cx="2" cy="-1.6" r="0.9" fill="#ffffff"/></g>')

    foot = f'{f.strftime("%b")} {f.day} – {l.strftime("%b")} {l.day} · {total:,} contributions'
    p.append(f'<text class="foot" x="{LEFT}" y="{H - 6}">{foot}</text>')
    p.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(p))
    print(f"wrote {out_path}: {ncols} weeks, {total:,} contributions")


def main():
    data = load(DATA)
    days = data["days"]
    if not days:
        print("no days in data", file=sys.stderr)
        sys.exit(1)
    render(days, PALETTES["light"], os.path.join(OUTDIR, "github-contribution-grid-snake.svg"))
    render(days, PALETTES["dark"], os.path.join(OUTDIR, "github-contribution-grid-snake-dark.svg"))


if __name__ == "__main__":
    main()
