#!/usr/bin/env python3
"""Turn a prepped grayscale portrait into a monochrome ASCII SVG that types itself.

GitHub strips <script> from READMEs, but an <img> SVG still runs SMIL. Each row
is revealed with a left-to-right clip wipe and a block cursor, staggered from
top to bottom, then the portrait holds. One ink color keeps it from looking noisy.

    python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, no animation
"""
import html
import json
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "ascii.svg")

with open(os.path.join(HERE, "profile.json")) as f:
    PROFILE = json.load(f)

PROMPT = PROFILE["prompt"]
NAME = PROFILE["name"]

COLS = int(os.environ.get("COLS", 140))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"

CONTRAST = 1.15
BRIGHTNESS = 1.02
GAMMA = 1.05
WHITE_FLOOR = 0.86

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

ROW_DUR = 5.8 / ROWS
STAGGER = ROW_DUR
STATIC = bool(os.environ.get("STATIC"))


def sample_rows():
    im = Image.open(SRC).convert("L")
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = im.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    px = im.load()
    rows = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = pow(px[x, y] / 255.0, GAMMA)
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            chars.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
        rows.append("".join(chars))
    return rows


def build(rows_txt):
    art_top = TITLEBAR_H + PAD * 0.35
    font_size = CELL_H * 0.86
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W:.0f}" height="{CANVAS_H:.0f}" '
        f'viewBox="0 0 {CANVAS_W:.0f} {CANVAS_H:.0f}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<defs>"
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f"</linearGradient></defs>",
        f'<rect width="{CANVAS_W:.0f}" height="{CANVAS_H:.0f}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1:.0f}" height="{CANVAS_H - 1:.0f}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dotcol}"/>')
    parts.append(
        f'<text x="{CANVAS_W / 2:.0f}" y="{TITLEBAR_H / 2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
        f'text-anchor="middle">{PROMPT}: ~$ ./portrait.sh</text>'
    )

    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (
            f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.2f}" textLength="{ART_W:.1f}" lengthAdjust="spacing">{safe}</text>'
        )
        if STATIC:
            parts.append(text)
            continue
        parts.append(
            f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        parts.append(
            f'<rect y="{row_y + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + ROW_DUR:.3f}s"/></rect>'
        )

    status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
    status_y = status_line_y + 19
    status = f"{PROMPT}:~$ whoami {NAME} "
    parts.append(
        f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W:.0f}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>'
    )
    parts.append(
        f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
        f'{PROMPT}:~$ whoami <tspan fill="{INK}">{html.escape(NAME)}</tspan></text>'
    )
    parts.append(
        f'<rect x="{PAD + len(status) * 13 * 0.60:.1f}" y="{status_y - 12:.1f}" width="8" height="14" fill="{INK}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1s" repeatCount="indefinite"/></rect>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main():
    rows_txt = sample_rows()
    svg = build(rows_txt)
    with open(OUT, "w") as f:
        f.write(svg)
    print("wrote", OUT, len(svg), "bytes;", f"{CANVAS_W:.0f}x{CANVAS_H:.0f}")


if __name__ == "__main__":
    main()
