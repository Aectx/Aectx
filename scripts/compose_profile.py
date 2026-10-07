#!/usr/bin/env python3
"""Stack the profile panels on one canvas so the matrix rain is the full background.

GitHub won't layer separate images, so the rain has to be behind every panel
inside a single SVG.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matrix_rain import matrix_rain

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "profile.svg")

CANVAS_W = 900
PAD = 18
GAP = 16


def load(name):
    text = open(os.path.join(ROOT, name)).read()
    text = re.sub(r"<!--BG-->.*?<!--/BG-->", "", text, flags=re.S)
    text = re.sub(r"<!--RAIN-->.*?<!--/RAIN-->", "", text, flags=re.S)
    match = re.search(r"<svg\b([^>]*)>(.*)</svg>\s*$", text, re.S)
    if not match:
        raise SystemExit(f"could not read {name}")
    attrs, body = match.group(1), match.group(2)
    width = float(re.search(r'\bwidth="([\d.]+)"', attrs).group(1))
    height = float(re.search(r'\bheight="([\d.]+)"', attrs).group(1))
    return width, height, body


def place(body, x, y, src_w, src_h, dst_w, dst_h):
    return (
        f'<svg x="{x:.1f}" y="{y:.1f}" width="{dst_w:.1f}" height="{dst_h:.1f}" '
        f'viewBox="0 0 {src_w:.2f} {src_h:.2f}">{body}</svg>'
    )


def main():
    banner = load("override.svg")
    heat = load("contrib-heatmap.svg")
    ascii_art = load("ascii.svg")
    card = load("info-card.svg")

    inner_w = CANVAS_W - PAD * 2
    y = PAD
    nodes = []

    def add(item, dst_w):
        nonlocal y
        src_w, src_h, body = item
        dst_h = src_h * (dst_w / src_w)
        nodes.append(place(body, PAD, y, src_w, src_h, dst_w, dst_h))
        y += dst_h + GAP
        return dst_h

    add(banner, inner_w)
    add(heat, inner_w)

    col_w = (inner_w - GAP) / 2
    a_w, a_h, a_body = ascii_art
    c_w, c_h, c_body = card
    a_dh = a_h * (col_w / a_w)
    c_dh = c_h * (col_w / c_w)
    row_h = max(a_dh, c_dh)
    nodes.append(place(a_body, PAD, y, a_w, a_h, col_w, a_dh))
    nodes.append(place(c_body, PAD + col_w + GAP, y, c_w, c_h, col_w, c_dh))
    y += row_h + PAD

    rain = matrix_rain(CANVAS_W, y, spacing=18, opacity=0.34, prefix="fullRain", length=26)
    rain_slow = matrix_rain(CANVAS_W, y, spacing=27, opacity=0.16, prefix="fullRainSlow", length=18)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{y:.0f}" '
        f'viewBox="0 0 {CANVAS_W} {y:.0f}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
        f'<rect width="{CANVAS_W}" height="{y:.0f}" fill="#050203"/>'
        f"{rain}{rain_slow}"
        f'{"".join(nodes)}'
        f"</svg>"
    )
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes, {CANVAS_W}x{y:.0f})")


if __name__ == "__main__":
    main()
