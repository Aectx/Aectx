#!/usr/bin/env python3
"""Render data/contributions.json as an animated contribution heatmap SVG.

Boxes use GitHub's own level colors, then reveal once on a diagonal and freeze.
"""
import datetime
import json
import os

from matrix_rain import matrix_rain

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

with open(os.path.join(HERE, "profile.json")) as f:
    PROMPT = json.load(f)["prompt"]

PALETTE = ["#140406", "#4a0d12", "#8f1d24", "#e10600", "#ff4d4d"]
CELL = 11
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 32
TOP_LABEL_H = 22
TITLEBAR_H = 30

BG = "#050203"
BG2 = "#120406"
FRAME = "#e10600"
MUTED = "#a34a4a"
ACCENT = "#ff2a2a"
GREEN = "#ff2a2a"
GOLD = "#ffb4b4"

COL_T = 0.016
ROW_T = 0.04
CELL_DUR = 0.4


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    grid = []
    col = [None] * lead
    for day in days:
        date = datetime.date.fromisoformat(day["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        level = max(0, min(len(PALETTE) - 1, int(day.get("level") or 0)))
        col.append((day["date"], day["count"], level))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        col.extend([None] * (7 - len(col)))
        grid.append(col)
    return grid


def render(data):
    grid = build_grid(data["days"])
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + 96 + PAD

    css = (
        "@keyframes cell {"
        "0% { opacity: 0; transform: translateY(-6px); }"
        "100% { opacity: 1; transform: translateY(0); }"
        "}"
        f".c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<style>{css}</style>",
        "<defs>"
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f"</linearGradient></defs>",
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        matrix_rain(canvas_w, canvas_h, spacing=34, opacity=0.16, prefix="heatRain"),
        f'<rect x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}" rx="12" '
        f'fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff2a2a", "#8f1d24", "#4a0d12"]):
        parts.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
    parts.append(
        f'<text x="{canvas_w / 2:.0f}" y="{TITLEBAR_H / 2 + 4}" fill="{ACCENT}" font-size="12" '
        f'text-anchor="middle">{PROMPT}:~/graph --corrupt</text>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W
    for ci, label in month_labels:
        parts.append(
            f'<text x="{grid_left + ci * STEP}" y="{TITLEBAR_H + 15}" fill="{MUTED}" font-size="11">{label}</text>'
        )
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.8
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="10">{wname}</text>')

    for ri in range(7):
        # Two weekday rows sit torn out of line, then jitter.
        torn = ri in (2, 5)
        shift = 8 if ri == 2 else -7
        cells = []
        for ci, column in enumerate(grid):
            cell = column[ri]
            if cell is None:
                continue
            date_s, count, level = cell
            if count == 0 and (ci + ri) % 9 == 0:
                continue
            gx = grid_left + ci * STEP
            gy = grid_top + ri * STEP
            delay = ci * COL_T + ri * ROW_T
            plural = "s" if count != 1 else ""
            cells.append(
                f'<rect class="c" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
                f"<title>{date_s}: {count} contribution{plural}</title></rect>"
            )
        body = "".join(cells)
        if torn:
            parts.append(
                f"<g>{body}"
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0; {shift} 0; 0 0; {-shift // 2} 0; 0 0" '
                f'begin="2.4s" dur="2.2s" repeatCount="indefinite"/>'
                f"</g>"
            )
        else:
            parts.append(body)

    leg_y = grid_top + art_h + 8
    lx = canvas_w - PAD - len(PALETTE) * (CELL + 2)
    parts.append(
        f'<text x="{lx - 8}" y="{leg_y + 9}" fill="{MUTED}" font-size="11" text-anchor="end">Less</text>'
    )
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
        lx += CELL + 3
    parts.append(f'<text x="{lx + 4}" y="{leg_y + 9}" fill="{MUTED}" font-size="11">More</text>')

    sep_y = leg_y + CELL + 16
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}"/>')

    total = data["total_contributions"]
    streak = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    best = data["best_day"]
    rng = data["range"]
    ly = sep_y + 26
    parts.append(
        f'<text x="{PAD}" y="{ly}" font-size="14" fill="{GREEN}">'
        f'<tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_w - PAD}" y="{ly}" font-size="13" fill="{MUTED}" text-anchor="end">'
        f'{rng["start"]} → {rng["end"]}</text>'
    )
    ly += 24
    parts.append(
        f'<text x="{PAD}" y="{ly}" font-size="14" fill="{MUTED}">current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{streak} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   longest </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{longest} days</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_w - PAD}" y="{ly}" font-size="13" fill="{MUTED}" text-anchor="end">'
        f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    with open(IN_PATH) as f:
        data = json.load(f)
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
