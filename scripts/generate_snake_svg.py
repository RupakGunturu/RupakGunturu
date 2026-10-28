#!/usr/bin/env python3
"""Generate a Platane-style contribution snake over the filtered date range.

The visual matches the old output-branch animation:
  * 53-week grid (880x192) with 16px cells / 12px dots
  * a 4-cell purple snake moving through the grid
  * dots disappear as the head reaches them and reset when the loop restarts
  * a thin progress bar fills at the bottom
  * CSS keyframes only, so it animates inside <img> on GitHub

The path is a randomized Hamiltonian path (serpentine base + "backbite" moves),
so the snake wanders instead of sweeping row by row.  Only data already filtered
from Feb 1 in data/contributions.json is drawn.

    python scripts/generate_snake_svg.py [data.json] [out_dir]
"""
import datetime as dt
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "dist")
START_DATE = os.environ.get("GH_PROFILE_START", "2026-02-01")

COLS = 53
ROWS = 7
CELL = 16
DOT = 12
RAD = 2
SNAKE_LEN = 4
STEP_MS = 145
MIX_ITERS = 20000
SEED = 1
MIN_EXIT = 45

PALETTES = {
    "light": {
        "empty": "#ebedf0",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "border": "#1b1f230a",
        "snake": "purple",
    },
    "dark": {
        "empty": "#161b22",
        "levels": ["#161b22", "#01311f", "#034525", "#0f6d31", "#00c647"],
        "border": "#1b1f230a",
        "snake": "purple",
    },
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_grid(days):
    last = max(dt.date.fromisoformat(d["date"]) for d in days)
    end_sunday = last - dt.timedelta(days=(last.weekday() + 1) % 7)
    start = end_sunday - dt.timedelta(weeks=COLS - 1)
    by_date = {d["date"]: d for d in days}
    dots = {}
    for col in range(COLS):
        for row in range(ROWS):
            date = (start + dt.timedelta(days=col * 7 + row)).isoformat()
            d = by_date.get(date)
            if d and d["date"] >= START_DATE and d["count"] > 0:
                dots[(col, row)] = max(1, min(int(d.get("level", 1)), 4))
    return start, last, dots


def neighbors(cell):
    x, y = cell
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            yield (nx, ny)


def base_path():
    path = []
    for row in range(ROWS):
        xs = range(COLS) if row % 2 == 0 else range(COLS - 1, -1, -1)
        path.extend((x, row) for x in xs)
    return path


def mix_path(path, iterations, seed):
    rnd = random.Random(seed)
    pos = {cell: i for i, cell in enumerate(path)}
    for _ in range(iterations):
        end = path[-1]
        choices = [n for n in neighbors(end) if n != path[-2]]
        if not choices:
            continue
        target = rnd.choice(choices)
        i = pos[target]
        segment = path[i + 1:]
        segment.reverse()
        path[i + 1:] = segment
        for k in range(i + 1, len(path)):
            pos[path[k]] = k
    return path


def build_route(path):
    route = [(0, -1)] + path
    x, y = path[-1]
    for yy in range(y - 1, -2, -1):
        route.append((x, yy))
    for xx in range(x - 1, -1, -1):
        route.append((xx, -1))
    while len(route) - 1 - len(path) < MIN_EXIT:
        route.append((0, -1))
    return route


def compress(points):
    out = []
    for i, point in enumerate(points):
        if i == 0 or i == len(points) - 1:
            out.append(point)
            continue
        prev = points[i - 1]
        nxt = points[i + 1]
        if (abs((prev[1] + nxt[1]) / 2 - point[1]) < 0.01
                and abs((prev[2] + nxt[2]) / 2 - point[2]) < 0.01):
            continue
        out.append(point)
    return out


def pct(value):
    return f"{value * 100:.2f}%"


def render(days, palette, out_path):
    start, last, dots = build_grid(days)
    path = mix_path(base_path(), MIX_ITERS, SEED)
    if len(path) != COLS * ROWS or len(set(path)) != len(path):
        raise RuntimeError("path generation did not cover the grid")

    route = build_route(path)
    total = len(route)
    duration = total * STEP_MS

    eat_step = {}
    for i, cell in enumerate(route):
        if cell in dots and cell not in eat_step:
            eat_step[cell] = i
    missing = set(dots) - set(eat_step)
    if missing:
        raise RuntimeError(f"{len(missing)} contribution cells were not reached")

    dot_items = sorted(eat_step.items(), key=lambda item: item[1])
    dot_class = {cell: f"c{k}" for k, (cell, _) in enumerate(dot_items)}

    styles = [
        f".c{{shape-rendering:geometricPrecision;fill:{palette['empty']};"
        f"stroke-width:1px;stroke:{palette['border']};"
        f"animation:none linear {duration}ms infinite;width:{DOT}px;height:{DOT}px}}"
    ]

    for k, (cell, step) in enumerate(dot_items):
        level = dots[cell]
        t = step / total
        styles.append(
            f"@keyframes c{k}{{{pct(t)}{{fill:{palette['levels'][level]}}}"
            f"{pct(min(1.0, t + 0.0002))},100%{{fill:{palette['empty']}}}}}"
        )
        styles.append(
            f".c.c{k}{{fill:{palette['levels'][level]};animation-name:c{k}}}"
        )

    styles.append(
        f".s{{shape-rendering:geometricPrecision;fill:{palette['snake']};"
        f"animation:none linear {duration}ms infinite}}"
    )
    d_min = DOT * 0.8
    d_max = CELL * 0.9
    i_max = min(4, SNAKE_LEN)
    snake_rects = []
    for j in range(SNAKE_LEN):
        u = (1 - min(j, i_max) / i_max) ** 2
        size = (1 - u) * d_min + u * d_max
        margin = (CELL - size) / 2
        radius = min(4.5, 4 * size / DOT)
        snake_rects.append(
            f'<rect class="s s{j}" x="{margin:.1f}" y="{margin:.1f}" '
            f'width="{size:.1f}" height="{size:.1f}" '
            f'rx="{radius:.1f}" ry="{radius:.1f}"/>'
        )

        points = []
        for i in range(total):
            idx = i - j
            if idx >= 0:
                x, y = route[idx]
            else:
                x, y = 0, -1 - (j - i)
            points.append((i / total, x, y))
        frames = compress(points)
        if frames[-1][0] < 1.0:
            frames.append((1.0, frames[-1][1], frames[-1][2]))

        keyframes = "".join(
            f"{pct(t)}{{transform:translate({x * CELL:.0f}px,{y * CELL:.0f}px)}}"
            for t, x, y in frames
        )
        styles.append(f"@keyframes s{j}{{{keyframes}}}")
        styles.append(
            f".s.s{j}{{transform:translate({points[0][1] * CELL:.0f}px,"
            f"{points[0][2] * CELL:.0f}px);animation-name:s{j}}}"
        )

    eaten = [(step, dots[cell]) for cell, step in dot_items]
    blocks = []
    for step, level in eaten:
        if blocks and blocks[-1][0] == level:
            blocks[-1][1].append(step)
        else:
            blocks.append([level, [step]])

    styles.append(
        ".u{transform-origin:0 0;transform:scale(0,1);"
        f"animation:none linear {duration}ms infinite}}"
    )
    bar_width = COLS * CELL
    unit = bar_width / len(eaten)
    bar_y = (ROWS + 2) * CELL
    bar_rects = []
    nx = 0.0
    for k, (level, steps) in enumerate(blocks):
        x = nx * unit
        width = len(steps) * unit + 0.6
        nx += len(steps)

        frames = []
        for i, step in enumerate(steps):
            t = step / total
            frames.append((max(0.0, t - 0.0001), i / len(steps)))
            frames.append((min(1.0, t + 0.0001), (i + 1) / len(steps)))
        frames.append((1.0, 1.0))
        keyframes = "".join(
            f"{pct(t)}{{transform:scale({scale:.5f},1)}}" for t, scale in frames
        )
        styles.append(f"@keyframes u{k}{{{keyframes}}}")
        styles.append(
            f".u.u{k}{{fill:{palette['levels'][level]};animation-name:u{k};"
            f"transform-origin:{x:.1f}px 0}}"
        )
        bar_rects.append(
            f'<rect class="u u{k}" x="{x:.1f}" y="{bar_y}" '
            f'width="{width:.1f}" height="{DOT}"/>'
        )

    styles.append(
        "@media (prefers-reduced-motion:reduce){.c,.s,.u{animation:none}"
        ".s{display:none}}"
    )

    cells = []
    for col in range(COLS):
        for row in range(ROWS):
            cls = "c" + (f" {dot_class[(col, row)]}" if (col, row) in dot_class else "")
            cells.append(
                f'<rect class="{cls}" x="{2 + col * CELL}" y="{2 + row * CELL}" '
                f'rx="{RAD}" ry="{RAD}"/>'
            )

    width = (COLS + 2) * CELL
    height = (ROWS + 5) * CELL
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="-{CELL} -{2 * CELL} {width} {height}">',
        f"<desc>Contribution snake - {start.isoformat()} to {last.isoformat()}, "
        f"{len(dots)} active days</desc>",
        "<style>" + "".join(styles) + "</style>",
        *cells,
        *bar_rects,
        *snake_rects,
        "</svg>",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(svg))
    print(
        f"wrote {out_path}: {COLS} weeks, {len(dots)} dots, "
        f"{total} steps, {duration / 1000:.1f}s"
    )


def main():
    data = load(DATA)
    days = data["days"]
    if not days:
        print("no days in data", file=sys.stderr)
        sys.exit(1)
    end = os.path.join(OUTDIR, "github-contribution-grid-snake.svg")
    dark = os.path.join(OUTDIR, "github-contribution-grid-snake-dark.svg")
    render(days, PALETTES["light"], end)
    render(days, PALETTES["dark"], dark)


if __name__ == "__main__":
    main()
